import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "agents"))

from infra.file_store import WorkspaceFileStore
from infra.shell_runner import ShellRunner


class TestSafetyInvariants(unittest.TestCase):
    def test_workspace_file_store_blocks_parent_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = WorkspaceFileStore(Path(tmp))
            with self.assertRaises(ValueError):
                store.safe_path("../outside.txt")

    def test_workspace_file_store_blocks_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            outside = workspace.parent / f"{workspace.name}-outside.txt"
            outside.write_text("secret", encoding="utf-8")
            link = workspace / "escape.txt"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable on this machine")

            store = WorkspaceFileStore(workspace)
            with self.assertRaises(ValueError):
                store.safe_path("escape.txt")

    def test_shell_runner_blocks_dangerous_command_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = ShellRunner(Path(tmp))
            result = runner.run("sudo reboot")
        self.assertEqual(result, "Error: Dangerous command blocked")

    def test_workspace_write_stays_inside_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            store = WorkspaceFileStore(workspace)
            result = store.write("notes/output.txt", "hello")
            self.assertIn("Wrote", result)
            self.assertTrue((workspace / "notes" / "output.txt").exists())


if __name__ == "__main__":
    unittest.main()
