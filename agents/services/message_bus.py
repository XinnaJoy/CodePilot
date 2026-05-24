#!/usr/bin/env python3
"""Filesystem-backed inbox messaging."""

import json
import time
from pathlib import Path


class MessageBus:
    def __init__(self, inbox_dir: Path):
        self.inbox_dir = inbox_dir
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

    def send(
        self,
        sender: str,
        to: str,
        content: str,
        msg_type: str = "message",
        extra: dict | None = None,
    ) -> str:
        message = {
            "type": msg_type,
            "from": sender,
            "content": content,
            "timestamp": time.time(),
        }
        if extra:
            message.update(extra)
        with open(self.inbox_dir / f"{to}.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps(message) + "\n")
        return f"Sent {msg_type} to {to}"

    def read_inbox(self, name: str) -> list:
        path = self.inbox_dir / f"{name}.jsonl"
        if not path.exists():
            return []
        messages = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").strip().splitlines()
            if line
        ]
        path.write_text("", encoding="utf-8")
        return messages

    def broadcast(self, sender: str, content: str, names: list) -> str:
        count = 0
        for name in names:
            if name != sender:
                self.send(sender, name, content, "broadcast")
                count += 1
        return f"Broadcast to {count} teammates"
