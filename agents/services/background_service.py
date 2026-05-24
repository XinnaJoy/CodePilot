#!/usr/bin/env python3
"""Background shell execution service."""

import threading
import uuid
from queue import Queue


class BackgroundManager:
    def __init__(self, shell_runner):
        self.shell_runner = shell_runner
        self.tasks = {}
        self.notifications = Queue()

    def run(self, command: str, timeout: int = 120) -> str:
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {"status": "running", "command": command, "result": None}
        worker = threading.Thread(
            target=self._exec, args=(task_id, command, timeout), daemon=True
        )
        worker.start()
        return f"Background task {task_id} started: {command[:80]}"

    def _exec(self, task_id: str, command: str, timeout: int):
        try:
            output = self.shell_runner.run(command, timeout=timeout)
            self.tasks[task_id].update({"status": "completed", "result": output})
        except Exception as exc:
            self.tasks[task_id].update({"status": "error", "result": str(exc)})
        self.notifications.put(
            {
                "task_id": task_id,
                "status": self.tasks[task_id]["status"],
                "result": self.tasks[task_id]["result"][:500],
            }
        )

    def check(self, task_id: str | None = None) -> str:
        if task_id:
            task = self.tasks.get(task_id)
            if not task:
                return f"Unknown: {task_id}"
            return f"[{task['status']}] {task.get('result') or '(running)'}"
        return (
            "\n".join(
                f"{key}: [{value['status']}] {value['command'][:60]}"
                for key, value in self.tasks.items()
            )
            or "No bg tasks."
        )

    def drain(self) -> list:
        notifications = []
        while not self.notifications.empty():
            notifications.append(self.notifications.get_nowait())
        return notifications
