#!/usr/bin/env python3
"""Workspace file access helpers."""

from pathlib import Path


class WorkspaceFileStore:
    def __init__(self, workdir: Path):
        self.workdir = workdir

    def safe_path(self, path: str) -> Path:
        resolved = (self.workdir / path).resolve()
        if not resolved.is_relative_to(self.workdir):
            raise ValueError(f"Path escapes workspace: {path}")
        return resolved

    def read(self, path: str, limit: int | None = None) -> str:
        try:
            lines = self.safe_path(path).read_text(encoding="utf-8").splitlines()
            if limit and limit < len(lines):
                lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
            return "\n".join(lines)[:50000]
        except Exception as exc:
            return f"Error: {exc}"

    def write(self, path: str, content: str) -> str:
        try:
            file_path = self.safe_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} bytes to {path}"
        except Exception as exc:
            return f"Error: {exc}"

    def edit(self, path: str, old_text: str, new_text: str) -> str:
        try:
            file_path = self.safe_path(path)
            current = file_path.read_text(encoding="utf-8")
            if old_text not in current:
                return f"Error: Text not found in {path}"
            file_path.write_text(current.replace(old_text, new_text, 1), encoding="utf-8")
            return f"Edited {path}"
        except Exception as exc:
            return f"Error: {exc}"
