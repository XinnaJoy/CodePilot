import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "agents"))
sys.path.insert(0, str(PROJECT_ROOT))

from memory import MemoryService
from services.compression_service import auto_compact
from tests.helpers import FakeModelClient, FakeResponse, text_block


class TestSessionMemory(unittest.TestCase):
    def test_auto_compact_writes_session_memory_summary_file(self):
        responses = [FakeResponse([text_block("Keep the runtime layout stable.")], "end_turn")]
        client = FakeModelClient(responses)

        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            memory = MemoryService.from_workdir(workdir)
            try:
                messages = [{"role": "user", "content": "Summarize this session."}]
                transcript_dir = workdir / ".runtime" / "transcripts"

                compacted = auto_compact(
                    messages,
                    client,
                    "fake-model",
                    transcript_dir,
                    memory=memory,
                    session_id="session-123",
                )
                summary_text = memory.get_session_summary("session-123")
                continuity_note = memory.get_note("project", "session-session-123-continuity")
            finally:
                memory.close()

        self.assertIn("Compressed. Transcript:", compacted[0]["content"])
        self.assertIsNotNone(summary_text)
        self.assertIn("session_id: session-123", summary_text)
        self.assertIn("Keep the runtime layout stable.", summary_text)
        self.assertIsNotNone(continuity_note)
        self.assertEqual(continuity_note["title"], "Session session-123 Continuity")

    def test_auto_compact_truncates_large_session_summary(self):
        responses = [FakeResponse([text_block("z" * 25_000)], "end_turn")]
        client = FakeModelClient(responses)

        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            memory = MemoryService.from_workdir(workdir)
            try:
                messages = [{"role": "user", "content": "Summarize this long session."}]
                transcript_dir = workdir / ".runtime" / "transcripts"

                auto_compact(
                    messages,
                    client,
                    "fake-model",
                    transcript_dir,
                    memory=memory,
                    session_id="session-big",
                )
                summary_text = memory.get_session_summary("session-big")
            finally:
                memory.close()

        self.assertIsNotNone(summary_text)
        self.assertIn("session summary truncated", summary_text)


if __name__ == "__main__":
    unittest.main()
