#!/usr/bin/env python3
"""Persistent task board stored on disk."""

import json
from pathlib import Path


class TaskManager:
    def __init__(self, tasks_dir: Path):
        self.tasks_dir = tasks_dir
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _next_id(self) -> int:
        ids = [int(file.stem.split("_")[1]) for file in self.tasks_dir.glob("task_*.json")]
        return max(ids, default=0) + 1

    def _load(self, task_id: int) -> dict:
        path = self.tasks_dir / f"task_{task_id}.json"
        if not path.exists():
            raise ValueError(f"Task {task_id} not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, task: dict):
        path = self.tasks_dir / f"task_{task['id']}.json"
        path.write_text(json.dumps(task, indent=2), encoding="utf-8")

    def create(self, subject: str, description: str = "") -> str:
        task = {
            "id": self._next_id(),
            "subject": subject,
            "description": description,
            "status": "pending",
            "owner": None,
            "blockedBy": [],
        }
        self._save(task)
        return json.dumps(task, indent=2)

    def get(self, task_id: int) -> str:
        return json.dumps(self._load(task_id), indent=2)

    def update(
        self,
        task_id: int,
        status: str | None = None,
        add_blocked_by: list | None = None,
        remove_blocked_by: list | None = None,
    ) -> str:
        task = self._load(task_id)
        if status:
            task["status"] = status
            if status == "completed":
                for file in self.tasks_dir.glob("task_*.json"):
                    item = json.loads(file.read_text(encoding="utf-8"))
                    if task_id in item.get("blockedBy", []):
                        item["blockedBy"].remove(task_id)
                        self._save(item)
            if status == "deleted":
                (self.tasks_dir / f"task_{task_id}.json").unlink(missing_ok=True)
                return f"Task {task_id} deleted"
        if add_blocked_by:
            task["blockedBy"] = list(set(task["blockedBy"] + add_blocked_by))
        if remove_blocked_by:
            task["blockedBy"] = [
                blocked for blocked in task["blockedBy"] if blocked not in remove_blocked_by
            ]
        self._save(task)
        return json.dumps(task, indent=2)

    def list_all(self) -> str:
        tasks = [
            json.loads(file.read_text(encoding="utf-8"))
            for file in sorted(self.tasks_dir.glob("task_*.json"))
        ]
        if not tasks:
            return "No tasks."
        lines = []
        for task in tasks:
            marker = {
                "pending": "[ ]",
                "in_progress": "[>]",
                "completed": "[x]",
            }.get(task["status"], "[?]")
            owner = f" @{task['owner']}" if task.get("owner") else ""
            blocked = f" (blocked by: {task['blockedBy']})" if task.get("blockedBy") else ""
            lines.append(f"{marker} #{task['id']}: {task['subject']}{owner}{blocked}")
        return "\n".join(lines)

    def claim(self, task_id: int, owner: str) -> str:
        task = self._load(task_id)
        task["owner"] = owner
        task["status"] = "in_progress"
        self._save(task)
        return f"Claimed task #{task_id} for {owner}"

    def iter_unclaimed(self) -> list[dict]:
        tasks = []
        for file in sorted(self.tasks_dir.glob("task_*.json")):
            task = json.loads(file.read_text(encoding="utf-8"))
            if task.get("status") == "pending" and not task.get("owner") and not task.get("blockedBy"):
                tasks.append(task)
        return tasks
