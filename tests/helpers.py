import time
from pathlib import Path
from types import SimpleNamespace


class FakeResponse:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class FakeModelClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("No fake responses left")
        return self._responses.pop(0)


def text_block(text: str):
    return SimpleNamespace(type="text", text=text)


def tool_use_block(tool_id: str, name: str, **tool_input):
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)


class StubTodo:
    def __init__(self, has_open=False):
        self._has_open = has_open

    def has_open_items(self):
        return self._has_open


class StubBackground:
    def __init__(self, items=None):
        self._items = list(items or [])

    def drain(self):
        items = self._items
        self._items = []
        return items


class StubBus:
    def __init__(self, inbox=None):
        self._inbox = list(inbox or [])

    def read_inbox(self, _name):
        inbox = self._inbox
        self._inbox = []
        return inbox


class StubMemory:
    def __init__(self):
        self._context = {}
        self.notes = []
        self.summary_by_session = {}

    def set(self, key: str, value: str):
        self._context[key] = value
        return f"Set {key} = {value[:100]}"

    def get(self, key: str):
        if key in self._context:
            return self._context[key]
        return f"Key '{key}' not found"

    def to_dict(self):
        return {"context": self._context.copy(), "goals": []}

    def render(self):
        if not self._context:
            return "Empty"
        return "\n".join(["=== Working Memory ==="] + [f"  {k}: {v}" for k, v in self._context.items()])

    def get_stats(self):
        return {"total_snapshots": 0, "unique_sessions": 0, "db_size_kb": 0}

    def list_all_snapshots(self, _limit=10):
        return []

    def list_snapshots(self, _session_id, _limit=10):
        return []

    def get_latest_snapshot(self, _session_id):
        return None

    def save_snapshot(self, _session_id, _messages, working_memory=None, snapshot_type="auto_compact"):
        return 1

    def upsert_note(self, memory_type: str, title: str, content: str, slug: str | None = None):
        item = {
            "type": memory_type,
            "title": title,
            "slug": slug or title.lower().replace(" ", "-"),
            "content": content,
        }
        self.notes.append(item)
        return item

    def get_note(self, memory_type: str, slug: str):
        for item in self.notes:
            if item["type"] == memory_type and item["slug"] == slug:
                return item
        return None

    def list_notes(self, memory_type: str | None = None):
        if memory_type is None:
            return list(self.notes)
        return [item for item in self.notes if item["type"] == memory_type]

    def render_index(self):
        lines = ["# Memory Index", ""]
        for item in self.notes:
            lines.append(f"- [{item['title']}]({item['slug']}.md) [{item['type']}] - {item['content'][:40]}")
        return "\n".join(lines).rstrip() + "\n"

    def save_session_summary(
        self,
        session_id: str,
        summary: str,
        transcript_path: Path,
        snapshot_id: int | None = None,
    ):
        path = transcript_path.parent.parent / "memory" / "session_memory" / f"{session_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "---",
                    f"session_id: {session_id}",
                    f"updated_at: {int(time.time())}",
                    f"transcript: {transcript_path}",
                    f"snapshot_id: {snapshot_id or 1}",
                    "---",
                    "",
                    summary,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.summary_by_session[session_id] = path
        return path

    def get_session_summary(self, session_id: str):
        path = self.summary_by_session.get(session_id)
        if not path or not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def capture_compaction(
        self,
        session_id: str,
        summary: str,
        transcript_path: Path,
        snapshot_id: int | None = None,
    ):
        summary_path = self.save_session_summary(session_id, summary, transcript_path, snapshot_id)
        note = self.upsert_note(
            "project",
            f"Session {session_id} Continuity",
            summary,
            slug=f"session-{session_id}-continuity",
        )
        return {
            "session_summary_path": str(summary_path),
            "continuity_note": note,
        }


def make_context(client, workdir: Path, todo=None, background=None, bus=None):
    runtime_dir = workdir / ".runtime"
    memory = StubMemory()
    return SimpleNamespace(
        client=client,
        session_id="test-session",
        config=SimpleNamespace(
            workdir=workdir,
            model="fake-model",
            runtime_dir=runtime_dir,
            memory_dir=runtime_dir / "memory",
            tasks_dir=runtime_dir / "tasks",
            team_dir=runtime_dir / "team",
            transcript_dir=runtime_dir / "transcripts",
        ),
        todo=todo or StubTodo(),
        background=background or StubBackground(),
        bus=bus or StubBus(),
        memory=memory,
        working_memory=memory,
        session_db=SimpleNamespace(),
    )
