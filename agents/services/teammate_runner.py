#!/usr/bin/env python3
"""Execution loop for a single teammate."""

import json
import time


class TeammateRunner:
    def __init__(self, context, registry, idle_timeout: int, poll_interval: int):
        self.context = context
        self.registry = registry
        self.idle_timeout = idle_timeout
        self.poll_interval = poll_interval

    def _dispatch_tool(self, block, name: str) -> str:
        if block.name == "idle":
            return "Entering idle phase."
        if block.name == "claim_task":
            return self.context.tasks.claim(block.input["task_id"], name)
        if block.name == "send_message":
            return self.context.bus.send(name, block.input["to"], block.input["content"])
        handlers = {
            "bash": lambda **kwargs: self.context.shell_runner.run(kwargs["command"]),
            "read_file": lambda **kwargs: self.context.file_store.read(kwargs["path"]),
            "write_file": lambda **kwargs: self.context.file_store.write(
                kwargs["path"], kwargs["content"]
            ),
            "edit_file": lambda **kwargs: self.context.file_store.edit(
                kwargs["path"], kwargs["old_text"], kwargs["new_text"]
            ),
        }
        return handlers.get(block.name, lambda **kwargs: "Unknown")(**block.input)

    def _tools(self) -> list[dict]:
        return [
            {
                "name": "bash",
                "description": "Run command.",
                "input_schema": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
            {
                "name": "read_file",
                "description": "Read file.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
            {
                "name": "edit_file",
                "description": "Edit file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"},
                    },
                    "required": ["path", "old_text", "new_text"],
                },
            },
            {
                "name": "send_message",
                "description": "Send message.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["to", "content"],
                },
            },
            {
                "name": "idle",
                "description": "Signal no more work.",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "claim_task",
                "description": "Claim task by ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {"task_id": {"type": "integer"}},
                    "required": ["task_id"],
                },
            },
        ]

    def run(self, name: str, role: str, prompt: str):
        team_name = self.registry.team_name
        system_prompt = (
            f"You are '{name}', role: {role}, team: {team_name}, at {self.context.config.workdir}. "
            "Use idle when done with current work. You may auto-claim tasks."
        )
        messages = [{"role": "user", "content": prompt}]
        tools = self._tools()
        while True:
            for _ in range(50):
                inbox = self.context.bus.read_inbox(name)
                for message in inbox:
                    if message.get("type") == "shutdown_request":
                        self.registry.set_status(name, "shutdown")
                        return
                    messages.append({"role": "user", "content": json.dumps(message)})
                try:
                    response = self.context.client.messages.create(
                        model=self.context.config.model,
                        system=system_prompt,
                        messages=messages,
                        tools=tools,
                        max_tokens=8000,
                    )
                except Exception:
                    self.registry.set_status(name, "shutdown")
                    return
                messages.append({"role": "assistant", "content": response.content})
                if response.stop_reason != "tool_use":
                    break
                results = []
                idle_requested = False
                for block in response.content:
                    if block.type == "tool_use":
                        idle_requested = block.name == "idle"
                        output = self._dispatch_tool(block, name)
                        print(f"  [{name}] {block.name}: {str(output)[:120]}")
                        results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(output),
                            }
                        )
                messages.append({"role": "user", "content": results})
                if idle_requested:
                    break
            self.registry.set_status(name, "idle")
            if not self._idle_wait(name, role, team_name, messages):
                self.registry.set_status(name, "shutdown")
                return
            self.registry.set_status(name, "working")

    def _idle_wait(self, name: str, role: str, team_name: str, messages: list) -> bool:
        for _ in range(self.idle_timeout // max(self.poll_interval, 1)):
            time.sleep(self.poll_interval)
            inbox = self.context.bus.read_inbox(name)
            if inbox:
                for message in inbox:
                    if message.get("type") == "shutdown_request":
                        self.registry.set_status(name, "shutdown")
                        return False
                    messages.append({"role": "user", "content": json.dumps(message)})
                return True
            unclaimed = self.context.tasks.iter_unclaimed()
            if unclaimed:
                task = unclaimed[0]
                self.context.tasks.claim(task["id"], name)
                if len(messages) <= 3:
                    messages.insert(
                        0,
                        {
                            "role": "user",
                            "content": f"<identity>You are '{name}', role: {role}, team: {team_name}.</identity>",
                        },
                    )
                    messages.insert(
                        1,
                        {"role": "assistant", "content": f"I am {name}. Continuing."},
                    )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"<auto-claimed>Task #{task['id']}: {task['subject']}\n"
                            f"{task.get('description', '')}</auto-claimed>"
                        ),
                    }
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Claimed task #{task['id']}. Working on it.",
                    }
                )
                return True
        return False
