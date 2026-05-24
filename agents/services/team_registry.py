#!/usr/bin/env python3
"""Teammate member registry persistence."""

import json
from pathlib import Path


class TeamRegistry:
    def __init__(self, team_dir: Path):
        self.team_dir = team_dir
        self.team_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.team_dir / "config.json"
        self.config = self._load()

    def _load(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        return {"team_name": "default", "members": []}

    def _save(self):
        self.config_path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")

    @property
    def team_name(self) -> str:
        return self.config["team_name"]

    def find(self, name: str) -> dict | None:
        for member in self.config["members"]:
            if member["name"] == name:
                return member
        return None

    def ensure_working_member(self, name: str, role: str) -> tuple[bool, str | None]:
        member = self.find(name)
        if member:
            if member["status"] not in ("idle", "shutdown"):
                return False, f"Error: '{name}' is currently {member['status']}"
            member["status"] = "working"
            member["role"] = role
        else:
            self.config["members"].append({"name": name, "role": role, "status": "working"})
        self._save()
        return True, None

    def set_status(self, name: str, status: str):
        member = self.find(name)
        if member:
            member["status"] = status
            self._save()

    def list_all(self) -> str:
        if not self.config["members"]:
            return "No teammates."
        lines = [f"Team: {self.config['team_name']}"]
        for member in self.config["members"]:
            lines.append(f"  {member['name']} ({member['role']}): {member['status']}")
        return "\n".join(lines)

    def member_names(self) -> list[str]:
        return [member["name"] for member in self.config["members"]]
