#!/usr/bin/env python3
"""One-shot subagent execution."""


def run_subagent(prompt: str, agent_type: str, client, model: str, shell_runner, file_store) -> str:
    tools = [
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
    ]
    if agent_type != "Explore":
        tools += [
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
        ]
    handlers = {
        "bash": lambda **kwargs: shell_runner.run(kwargs["command"]),
        "read_file": lambda **kwargs: file_store.read(kwargs["path"]),
        "write_file": lambda **kwargs: file_store.write(kwargs["path"], kwargs["content"]),
        "edit_file": lambda **kwargs: file_store.edit(
            kwargs["path"], kwargs["old_text"], kwargs["new_text"]
        ),
    }
    messages = [{"role": "user", "content": prompt}]
    response = None
    for _ in range(30):
        response = client.messages.create(
            model=model,
            messages=messages,
            tools=tools,
            max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = handlers.get(block.name, lambda **kwargs: "Unknown tool")
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(handler(**block.input))[:50000],
                    }
                )
        messages.append({"role": "user", "content": results})
    if response:
        return "".join(block.text for block in response.content if hasattr(block, "text")) or "(no summary)"
    return "(subagent failed)"
