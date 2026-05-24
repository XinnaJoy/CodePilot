#!/usr/bin/env python3
"""Filesystem-backed long-term and session memory storage."""

from __future__ import annotations

import re
import time
from pathlib import Path


MEMORY_TYPES = ("user", "feedback", "project", "reference")
MAX_ENTRYPOINT_LINES = 200
MAX_ENTRYPOINT_BYTES = 25_000
MAX_NOTE_BYTES = 12_000
MAX_SESSION_SUMMARY_BYTES = 20_000


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"note-{int(time.time())}"


def truncate_entrypoint_content(raw: str) -> str:
    lines = raw.splitlines()
    truncated = lines[:MAX_ENTRYPOINT_LINES]
    text = "\n".join(truncated)

    while len(text.encode("utf-8")) > MAX_ENTRYPOINT_BYTES and truncated:
        truncated = truncated[:-1]
        text = "\n".join(truncated)

    if len(truncated) == len(lines) and len(text.encode("utf-8")) <= MAX_ENTRYPOINT_BYTES:
        return text

    warning = [
        "",
        "<!-- memory index truncated: open note files directly for full content -->",
    ]
    truncated_text = "\n".join(truncated + warning)
    while len(truncated_text.encode("utf-8")) > MAX_ENTRYPOINT_BYTES and truncated:
        truncated = truncated[:-1]
        truncated_text = "\n".join(truncated + warning)
    return truncated_text


def truncate_body_content(raw: str, max_bytes: int, warning: str) -> str:
    text = raw.strip()
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text

    warning_block = f"\n\n{warning}"
    limit = max_bytes - len(warning_block.encode("utf-8"))
    trimmed = text
    while len(trimmed.encode("utf-8")) > limit and trimmed:
        trimmed = trimmed[:-1]
    return trimmed.rstrip() + warning_block


class MemoryFileStore:
    """File storage for long-term notes and session summaries."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.longterm_dir = memory_dir / "longterm"
        self.session_memory_dir = memory_dir / "session_memory"
        self.index_path = self.longterm_dir / "MEMORY.md"
        self._ensure_layout()

    def _ensure_layout(self):
        self.longterm_dir.mkdir(parents=True, exist_ok=True)
        self.session_memory_dir.mkdir(parents=True, exist_ok=True)
        for memory_type in MEMORY_TYPES:
            (self.longterm_dir / memory_type).mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text("# Memory Index\n\n", encoding="utf-8")

    def _note_dir(self, memory_type: str) -> Path:
        if memory_type not in MEMORY_TYPES:
            raise ValueError(f"Unsupported memory type: {memory_type}")
        return self.longterm_dir / memory_type

    def _note_path(self, memory_type: str, slug: str) -> Path:
        return self._note_dir(memory_type) / f"{slug}.md"

    def upsert_note(
        self,
        memory_type: str,
        title: str,
        content: str,
        slug: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        note_slug = slugify(slug or title)
        path = self._note_path(memory_type, note_slug)
        normalized_content = truncate_body_content(
            content,
            MAX_NOTE_BYTES,
            "<!-- memory note truncated to protect runtime footprint -->",
        )
        hook = self._build_hook(normalized_content)
        frontmatter = [
            "---",
            f"title: {title}",
            f"type: {memory_type}",
            f"slug: {note_slug}",
            f"updated_at: {int(time.time())}",
        ]
        for key, value in sorted((metadata or {}).items()):
            frontmatter.append(f"{key}: {value}")
        frontmatter.extend(["---", "", normalized_content, ""])
        payload = "\n".join(frontmatter)
        path.write_text(payload, encoding="utf-8")
        self._write_index()
        return {
            "type": memory_type,
            "title": title,
            "slug": note_slug,
            "path": str(path),
            "hook": hook,
        }

    def get_note(self, memory_type: str, slug: str) -> dict | None:
        path = self._note_path(memory_type, slug)
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        return {
            "type": memory_type,
            "title": self._read_title(text, slug),
            "slug": slug,
            "path": str(path),
            "content": text,
        }

    def list_notes(self, memory_type: str | None = None) -> list[dict]:
        note_types = [memory_type] if memory_type else list(MEMORY_TYPES)
        items = []
        for current_type in note_types:
            note_dir = self._note_dir(current_type)
            for path in sorted(note_dir.glob("*.md")):
                content = path.read_text(encoding="utf-8")
                items.append(
                    {
                        "type": current_type,
                        "slug": path.stem,
                        "title": self._read_title(content, path.stem),
                        "path": str(path),
                        "hook": self._build_hook(content),
                    }
                )
        return items

    def render_index(self) -> str:
        self._write_index()
        return self.index_path.read_text(encoding="utf-8")

    def save_session_summary(
        self,
        session_id: str,
        summary: str,
        transcript_path: Path,
        snapshot_id: int | None = None,
    ) -> Path:
        path = self.session_memory_dir / f"{session_id}.md"
        normalized_summary = truncate_body_content(
            summary,
            MAX_SESSION_SUMMARY_BYTES,
            "<!-- session summary truncated to protect runtime footprint -->",
        )
        lines = [
            "---",
            f"session_id: {session_id}",
            f"updated_at: {int(time.time())}",
            f"transcript: {transcript_path}",
        ]
        if snapshot_id is not None:
            lines.append(f"snapshot_id: {snapshot_id}")
        lines.extend(
            [
                "---",
                "",
                "# Session Memory",
                "",
                normalized_summary,
                "",
            ]
        )
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def get_session_summary(self, session_id: str) -> str | None:
        path = self.session_memory_dir / f"{session_id}.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def _build_hook(self, content: str) -> str:
        body = self._strip_frontmatter(content)
        first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
        return first_line[:120]

    def _read_title(self, content: str, fallback: str) -> str:
        for line in content.splitlines():
            if line.startswith("title: "):
                return line.split(":", 1)[1].strip()
        return fallback

    def _strip_frontmatter(self, content: str) -> str:
        if not content.startswith("---\n"):
            return content
        parts = content.split("\n---\n", 1)
        if len(parts) == 2:
            return parts[1]
        return content

    def _write_index(self):
        lines = ["# Memory Index", ""]
        for item in self.list_notes():
            relative = Path(item["path"]).relative_to(self.longterm_dir).as_posix()
            lines.append(f"- [{item['title']}]({relative}) [{item['type']}] - {item['hook']}")
        rendered = "\n".join(lines).rstrip() + "\n"
        self.index_path.write_text(truncate_entrypoint_content(rendered), encoding="utf-8")
