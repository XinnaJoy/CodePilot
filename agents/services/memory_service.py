#!/usr/bin/env python3
"""Memory subsystem service facade."""

from pathlib import Path

from core.memory_models import WorkingMemory
from infra.memory_file_store import MemoryFileStore
from infra.session_store import SessionDB


class MemoryService:
    """Facade over working memory and session persistence."""

    def __init__(self, working_memory: WorkingMemory, session_db: SessionDB, file_store: MemoryFileStore):
        self.working_memory = working_memory
        self.session_db = session_db
        self.file_store = file_store

    @classmethod
    def from_workdir(cls, workdir: Path):
        memory_dir = workdir / ".runtime" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            WorkingMemory(),
            SessionDB(memory_dir / "sessions.db"),
            MemoryFileStore(memory_dir),
        )

    def set(self, key: str, value: str) -> str:
        return self.working_memory.set(key, value)

    def get(self, key: str) -> str:
        return self.working_memory.get(key)

    def push_goal(self, goal: str) -> str:
        return self.working_memory.push_goal(goal)

    def pop_goal(self) -> str:
        return self.working_memory.pop_goal()

    def render(self) -> str:
        return self.working_memory.render()

    def clear(self):
        self.working_memory.clear()

    def to_dict(self) -> dict:
        return self.working_memory.to_dict()

    def from_dict(self, data: dict):
        self.working_memory.from_dict(data)

    def save_snapshot(
        self,
        session_id: str,
        messages: list[dict],
        working_memory: dict | None = None,
        snapshot_type: str = "auto_compact",
    ) -> int:
        payload = working_memory if working_memory is not None else self.working_memory.to_dict()
        return self.session_db.save_snapshot(session_id, messages, payload, snapshot_type)

    def get_latest_snapshot(self, session_id: str):
        return self.session_db.get_latest_snapshot(session_id)

    def list_snapshots(self, session_id: str, limit: int = 10):
        return self.session_db.list_snapshots(session_id, limit)

    def list_all_snapshots(self, limit: int = 10):
        return self.session_db.list_all_snapshots(limit)

    def cleanup_old_snapshots(self, session_id: str, keep_last: int = 5):
        return self.session_db.cleanup_old_snapshots(session_id, keep_last)

    def get_stats(self) -> dict:
        return self.session_db.get_stats()

    def upsert_note(
        self,
        memory_type: str,
        title: str,
        content: str,
        slug: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        return self.file_store.upsert_note(memory_type, title, content, slug, metadata)

    def get_note(self, memory_type: str, slug: str) -> dict | None:
        return self.file_store.get_note(memory_type, slug)

    def list_notes(self, memory_type: str | None = None) -> list[dict]:
        return self.file_store.list_notes(memory_type)

    def render_index(self) -> str:
        return self.file_store.render_index()

    def save_session_summary(
        self,
        session_id: str,
        summary: str,
        transcript_path: Path,
        snapshot_id: int | None = None,
    ) -> Path:
        return self.file_store.save_session_summary(session_id, summary, transcript_path, snapshot_id)

    def get_session_summary(self, session_id: str) -> str | None:
        return self.file_store.get_session_summary(session_id)

    def capture_compaction(
        self,
        session_id: str,
        summary: str,
        transcript_path: Path,
        snapshot_id: int | None = None,
    ) -> dict:
        session_path = self.save_session_summary(session_id, summary, transcript_path, snapshot_id)
        note = self.upsert_note(
            "project",
            f"Session {session_id} Continuity",
            summary,
            slug=f"session-{session_id}-continuity",
            metadata={
                "source": "auto_compact",
                "transcript": str(transcript_path),
                "snapshot_id": snapshot_id if snapshot_id is not None else "",
            },
        )
        return {
            "session_summary_path": str(session_path),
            "continuity_note": note,
        }

    def close(self):
        self.session_db.close()


def create_memory_system(workdir: Path) -> tuple[WorkingMemory, SessionDB]:
    """Backward-compatible helper for current agent wiring."""
    service = MemoryService.from_workdir(workdir)
    return service.working_memory, service.session_db
