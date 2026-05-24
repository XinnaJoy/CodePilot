#!/usr/bin/env python3
"""Tool handler bindings."""
#实际执行逻辑，通过 lambda 函数绑定到具体实现

import json
import uuid

from services.subagent_service import run_subagent


def build_system_prompt(config, context) -> str:
    return f"""You are CodePilot, a local coding agent running in the workspace {config.workdir}.
If the user asks who you are or what you are, identify yourself as CodePilot.
Use tools to solve tasks.
Prefer task_create/task_update/task_list for multi-step work. Use TodoWrite for short checklists.
Use task for subagent delegation. Use load_skill for specialized knowledge.
Skills: {context.skills.descriptions()}"""


def build_tool_handlers(get_context, shutdown_requests: dict, plan_requests: dict) -> dict:
    def shutdown_request(teammate: str) -> str:
        context = get_context()
        request_id = str(uuid.uuid4())[:8]
        shutdown_requests[request_id] = {"target": teammate, "status": "pending"}
        context.bus.send(
            "lead",
            teammate,
            "Please shut down.",
            "shutdown_request",
            {"request_id": request_id},
        )
        return f"Shutdown request {request_id} sent to '{teammate}'"

    def plan_approval(request_id: str, approve: bool, feedback: str = "") -> str:
        context = get_context()
        request = plan_requests.get(request_id)
        if not request:
            return f"Error: Unknown plan request_id '{request_id}'"
        request["status"] = "approved" if approve else "rejected"
        context.bus.send(
            "lead",
            request["from"],
            feedback,
            "plan_approval_response",
            {"request_id": request_id, "approve": approve, "feedback": feedback},
        )
        return f"Plan {request['status']} for '{request['from']}'"

    return {
        "bash": lambda **kwargs: get_context().shell_runner.run(kwargs["command"]),
        "read_file": lambda **kwargs: get_context().file_store.read(kwargs["path"], kwargs.get("limit")),
        "write_file": lambda **kwargs: get_context().file_store.write(kwargs["path"], kwargs["content"]),
        "edit_file": lambda **kwargs: get_context().file_store.edit(
            kwargs["path"], kwargs["old_text"], kwargs["new_text"]
        ),
        "TodoWrite": lambda **kwargs: get_context().todo.update(kwargs["items"]),
        "task": lambda **kwargs: run_subagent(
            kwargs["prompt"],
            kwargs.get("agent_type", "Explore"),
            get_context().client,
            get_context().config.model,
            get_context().shell_runner,
            get_context().file_store,
        ),
        "load_skill": lambda **kwargs: get_context().skills.load(kwargs["name"]),
        "compress": lambda **kwargs: "Compressing...",
        "background_run": lambda **kwargs: get_context().background.run(
            kwargs["command"], kwargs.get("timeout", 120)
        ),
        "check_background": lambda **kwargs: get_context().background.check(kwargs.get("task_id")),
        "task_create": lambda **kwargs: get_context().tasks.create(
            kwargs["subject"], kwargs.get("description", "")
        ),
        "task_get": lambda **kwargs: get_context().tasks.get(kwargs["task_id"]),
        "task_update": lambda **kwargs: get_context().tasks.update(
            kwargs["task_id"],
            kwargs.get("status"),
            kwargs.get("add_blocked_by"),
            kwargs.get("remove_blocked_by"),
        ),
        "task_list": lambda **kwargs: get_context().tasks.list_all(),
        "spawn_teammate": lambda **kwargs: get_context().team.spawn(
            kwargs["name"], kwargs["role"], kwargs["prompt"]
        ),
        "list_teammates": lambda **kwargs: get_context().team.list_all(),
        "send_message": lambda **kwargs: get_context().bus.send(
            "lead", kwargs["to"], kwargs["content"], kwargs.get("msg_type", "message")
        ),
        "read_inbox": lambda **kwargs: json.dumps(get_context().bus.read_inbox("lead"), indent=2),
        "broadcast": lambda **kwargs: get_context().bus.broadcast(
            "lead", kwargs["content"], get_context().team.member_names()
        ),
        "shutdown_request": lambda **kwargs: shutdown_request(kwargs["teammate"]),
        "plan_approval": lambda **kwargs: plan_approval(
            kwargs["request_id"], kwargs["approve"], kwargs.get("feedback", "")
        ),
        "idle": lambda **kwargs: "Lead does not idle.",
        "claim_task": lambda **kwargs: get_context().tasks.claim(kwargs["task_id"], "lead"),
        "mem_set": lambda **kwargs: get_context().memory.set(kwargs["key"], kwargs["value"]),
        "mem_get": lambda **kwargs: get_context().memory.get(kwargs["key"]),
        "save_session": lambda **kwargs: (
            "Snapshot ID: "
            f"{get_context().memory.save_snapshot(kwargs['session_id'], kwargs['messages'])}"
        ),
        "list_sessions": lambda **kwargs: json.dumps(
            get_context().memory.list_all_snapshots(kwargs.get("limit", 10))
            if not kwargs.get("session_id")
            else get_context().memory.list_snapshots(
                kwargs["session_id"], kwargs.get("limit", 10)
            ),
            indent=2,
        ),
        "get_session": lambda **kwargs: json.dumps(
            get_context().memory.get_latest_snapshot(kwargs["session_id"]),
            indent=2,
            default=str,
        ),
        "memory_note_write": lambda **kwargs: json.dumps(
            get_context().memory.upsert_note(
                kwargs["memory_type"],
                kwargs["title"],
                kwargs["content"],
                kwargs.get("slug"),
            ),
            indent=2,
        ),
        "memory_note_get": lambda **kwargs: json.dumps(
            get_context().memory.get_note(kwargs["memory_type"], kwargs["slug"]),
            indent=2,
        ),
        "memory_list": lambda **kwargs: json.dumps(
            get_context().memory.list_notes(kwargs.get("memory_type")),
            indent=2,
        ),
        "memory_index": lambda **kwargs: get_context().memory.render_index(),
    }
