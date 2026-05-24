#!/usr/bin/env python3
"""Conversation compaction helpers."""

import json
import time
from pathlib import Path


def estimate_tokens(messages: list) -> int:
    return len(json.dumps(messages, default=str)) // 4


def microcompact(messages: list):
    tool_results = []
    for message in messages:
        if message["role"] == "user" and isinstance(message.get("content"), list):
            for part in message["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    tool_results.append(part)
    if len(tool_results) <= 3:
        return
    for part in tool_results[:-3]:
        if isinstance(part.get("content"), str) and len(part["content"]) > 100:
            part["content"] = "[cleared]"


def auto_compact(
    messages: list,
    client,
    model: str,
    transcript_dir: Path,
    memory=None,
    session_id: str | None = None,
) -> list:
    transcript_dir.mkdir(parents=True, exist_ok=True)
    path = transcript_dir / f"transcript_{int(time.time())}.jsonl"
    with open(path, "w", encoding="utf-8") as handle:
        for message in messages:
            handle.write(json.dumps(message, default=str) + "\n")
    conversation_text = json.dumps(messages, default=str)[-80000:]
    response = client.messages.create(
        model=model,
        messages=[{"role": "user", "content": f"Summarize for continuity:\n{conversation_text}"}],
        max_tokens=2000,
    )
    summary = response.content[0].text
    if memory and session_id:
        snapshot_id = memory.save_snapshot(session_id, messages, snapshot_type="auto_compact")
        if hasattr(memory, "capture_compaction"):
            memory.capture_compaction(session_id, summary, path, snapshot_id=snapshot_id)
        else:
            memory.save_session_summary(session_id, summary, path, snapshot_id=snapshot_id)
    return [{"role": "user", "content": f"[Compressed. Transcript: {path}]\n{summary}"}]
