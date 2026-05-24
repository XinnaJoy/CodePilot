import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "agents"))

from memory import MemoryService


class TestMemoryService(unittest.TestCase):
    def test_service_wraps_working_memory_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = MemoryService.from_workdir(Path(tmp))
            try:
                set_result = service.set("current_task", "ship memory refactor")
                get_result = service.get("current_task")
            finally:
                service.close()

        self.assertIn("Set current_task", set_result)
        self.assertEqual(get_result, "ship memory refactor")

    def test_service_saves_snapshot_using_current_working_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = MemoryService.from_workdir(Path(tmp))
            try:
                service.set("focus", "session summary")
                snapshot_id = service.save_snapshot(
                    "session_001",
                    [{"role": "user", "content": "hello"}],
                )
                snapshot = service.get_latest_snapshot("session_001")
            finally:
                service.close()

        self.assertIsInstance(snapshot_id, int)
        self.assertEqual(snapshot["working_memory"]["context"]["focus"], "session summary")


if __name__ == "__main__":
    unittest.main()
