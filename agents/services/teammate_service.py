#!/usr/bin/env python3
"""Persistent teammate orchestration."""

import threading

from services.team_registry import TeamRegistry
from services.teammate_runner import TeammateRunner


class TeammateManager:
    def __init__(self, context, idle_timeout: int, poll_interval: int):
        self.context = context
        self.registry = TeamRegistry(self.context.config.team_dir)
        self.runner = TeammateRunner(context, self.registry, idle_timeout, poll_interval)
        self.threads = {}

    def spawn(self, name: str, role: str, prompt: str) -> str:
        ok, error = self.registry.ensure_working_member(name, role)
        if not ok:
            return error
        worker = threading.Thread(target=self.runner.run, args=(name, role, prompt), daemon=True)
        worker.start()
        self.threads[name] = worker
        return f"Spawned '{name}' (role: {role})"

    def list_all(self) -> str:
        return self.registry.list_all()

    def member_names(self) -> list:
        return self.registry.member_names()
