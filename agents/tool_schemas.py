#!/usr/bin/env python3
"""Tool schema definitions."""
#定义 30+ 工具的 JSON Schema
from config import VALID_MSG_TYPES


def build_tools() -> list[dict]:
    return [
        {
            "name": "bash",
            "description": "Run a shell command.",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
        {
            "name": "read_file",
            "description": "Read file contents.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write content to file.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            },
        },
        {
            "name": "edit_file",
            "description": "Replace exact text in file.",
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
            "name": "TodoWrite",
            "description": "Update task tracking list.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                },
                                "activeForm": {"type": "string"},
                            },
                            "required": ["content", "status", "activeForm"],
                        },
                    }
                },
                "required": ["items"],
            },
        },
        {
            "name": "task",
            "description": "Spawn a subagent for isolated exploration or work.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "agent_type": {"type": "string", "enum": ["Explore", "general-purpose"]},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "load_skill",
            "description": "Load specialized knowledge by name.",
            "input_schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        {
            "name": "compress",
            "description": "Manually compress conversation context.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "background_run",
            "description": "Run command in background thread.",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}},
                "required": ["command"],
            },
        },
        {
            "name": "check_background",
            "description": "Check background task status.",
            "input_schema": {"type": "object", "properties": {"task_id": {"type": "string"}}},
        },
        {
            "name": "task_create",
            "description": "Create a persistent file task.",
            "input_schema": {
                "type": "object",
                "properties": {"subject": {"type": "string"}, "description": {"type": "string"}},
                "required": ["subject"],
            },
        },
        {
            "name": "task_get",
            "description": "Get task details by ID.",
            "input_schema": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
        {
            "name": "task_update",
            "description": "Update task status or dependencies.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "deleted"],
                    },
                    "add_blocked_by": {"type": "array", "items": {"type": "integer"}},
                    "remove_blocked_by": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["task_id"],
            },
        },
        {
            "name": "task_list",
            "description": "List all tasks.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "spawn_teammate",
            "description": "Spawn a persistent autonomous teammate.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "prompt": {"type": "string"},
                },
                "required": ["name", "role", "prompt"],
            },
        },
        {
            "name": "list_teammates",
            "description": "List all teammates.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "send_message",
            "description": "Send a message to a teammate.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "content": {"type": "string"},
                    "msg_type": {"type": "string", "enum": list(VALID_MSG_TYPES)},
                },
                "required": ["to", "content"],
            },
        },
        {
            "name": "read_inbox",
            "description": "Read and drain the lead's inbox.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "broadcast",
            "description": "Send message to all teammates.",
            "input_schema": {
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
        },
        {
            "name": "shutdown_request",
            "description": "Request a teammate to shut down.",
            "input_schema": {
                "type": "object",
                "properties": {"teammate": {"type": "string"}},
                "required": ["teammate"],
            },
        },
        {
            "name": "plan_approval",
            "description": "Approve or reject a teammate's plan.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "approve": {"type": "boolean"},
                    "feedback": {"type": "string"},
                },
                "required": ["request_id", "approve"],
            },
        },
        {
            "name": "idle",
            "description": "Enter idle state.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "claim_task",
            "description": "Claim a task from the board.",
            "input_schema": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
        {
            "name": "mem_set",
            "description": "Set working memory variable",
            "input_schema": {
                "type": "object",
                "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
                "required": ["key", "value"],
            },
        },
        {
            "name": "mem_get",
            "description": "Get working memory variable",
            "input_schema": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        },
        {
            "name": "save_session",
            "description": "Save conversation snapshot for recovery",
            "input_schema": {
                "type": "object",
                "properties": {"session_id": {"type": "string"}, "messages": {"type": "array"}},
                "required": ["session_id", "messages"],
            },
        },
        {
            "name": "list_sessions",
            "description": "List saved session snapshots",
            "input_schema": {
                "type": "object",
                "properties": {"session_id": {"type": "string"}, "limit": {"type": "integer"}},
            },
        },
        {
            "name": "get_session",
            "description": "Get latest session snapshot",
            "input_schema": {
                "type": "object",
                "properties": {"session_id": {"type": "string"}},
                "required": ["session_id"],
            },
        },
        {
            "name": "memory_note_write",
            "description": "Create or update a typed long-term memory note.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "memory_type": {
                        "type": "string",
                        "enum": ["user", "feedback", "project", "reference"],
                    },
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "slug": {"type": "string"},
                },
                "required": ["memory_type", "title", "content"],
            },
        },
        {
            "name": "memory_note_get",
            "description": "Read a typed long-term memory note.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "memory_type": {
                        "type": "string",
                        "enum": ["user", "feedback", "project", "reference"],
                    },
                    "slug": {"type": "string"},
                },
                "required": ["memory_type", "slug"],
            },
        },
        {
            "name": "memory_list",
            "description": "List typed long-term memory notes.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "memory_type": {
                        "type": "string",
                        "enum": ["user", "feedback", "project", "reference"],
                    }
                },
            },
        },
        {
            "name": "memory_index",
            "description": "Render the long-term memory index entrypoint.",
            "input_schema": {"type": "object", "properties": {}},
        },
    ]
