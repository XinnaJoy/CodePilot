import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "agents"))

from memory import MemoryService


class TestLongTermMemory(unittest.TestCase):
    def test_upsert_note_creates_typed_file_and_index_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = MemoryService.from_workdir(Path(tmp))
            try:
                item = service.upsert_note(
                    "project",
                    "Runtime Layout",
                    "Store runtime artifacts under .runtime only.",
                )
                note = service.get_note("project", item["slug"])
                index = service.render_index()
            finally:
                service.close()

        self.assertEqual(note["title"], "Runtime Layout")
        self.assertIn("[project]", index)
        self.assertIn("Runtime Layout", index)

    def test_memory_index_is_truncated_when_entries_get_too_large(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = MemoryService.from_workdir(Path(tmp))
            try:
                for idx in range(260):
                    service.upsert_note(
                        "reference",
                        f"Note {idx}",
                        "x" * 300,
                    )
                index = service.render_index()
            finally:
                service.close()

        self.assertLessEqual(len(index.splitlines()), 202)
        self.assertIn("memory index truncated", index)

    def test_large_note_content_is_truncated_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = MemoryService.from_workdir(Path(tmp))
            try:
                item = service.upsert_note(
                    "reference",
                    "Huge Note",
                    "y" * 20_000,
                )
                note = service.get_note("reference", item["slug"])
            finally:
                service.close()

        self.assertIn("memory note truncated", note["content"])


if __name__ == "__main__":
    unittest.main()
