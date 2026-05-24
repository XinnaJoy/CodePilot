#!/usr/bin/env python3
"""Main agent loop orchestration."""

import json

from services.compression_service import auto_compact, estimate_tokens, microcompact


def run_agent_loop(messages: list, context, tools: list, tool_handlers: dict, system_prompt: str, token_threshold: int):
    rounds_without_todo = 0
    while True:
        microcompact(messages)
        if estimate_tokens(messages) > token_threshold:
            print("[auto-compact triggered]")
            messages[:] = auto_compact(
                messages,
                context.client,
                context.config.model,
                context.config.transcript_dir,
                memory=context.memory,
                session_id=context.session_id,
            )
        notifications = context.background.drain()
        if notifications:
            text = "\n".join(
                f"[bg:{item['task_id']}] {item['status']}: {item['result']}"
                for item in notifications
            )
            messages.append(
                {"role": "user", "content": f"<background-results>\n{text}\n</background-results>"}
            )
        inbox = context.bus.read_inbox("lead")
        if inbox:
            messages.append({"role": "user", "content": f"<inbox>{json.dumps(inbox, indent=2)}</inbox>"})
        # 传入工具定义
        response = context.client.messages.create(
            model=context.config.model,
            system=system_prompt,
            messages=messages,
            tools=tools,    # 工具的 JSON Schema
            max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return
        results = []
        used_todo = False
        manual_compress = False
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "compress":
                    manual_compress = True
                handler = tool_handlers.get(block.name)
                try:
                    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                except Exception as exc:
                    output = f"Error: {exc}"
                print(f"> {block.name}:")
                print(str(output)[:200])
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
                if block.name == "TodoWrite":
                    used_todo = True
        rounds_without_todo = 0 if used_todo else rounds_without_todo + 1
        if context.todo.has_open_items() and rounds_without_todo >= 3:
            results.append({"type": "text", "text": "<reminder>Update your todos.</reminder>"})
        messages.append({"role": "user", "content": results})
        if manual_compress:
            print("[manual compact]")
            messages[:] = auto_compact(
                messages,
                context.client,
                context.config.model,
                context.config.transcript_dir,
                memory=context.memory,
                session_id=context.session_id,
            )
            return
