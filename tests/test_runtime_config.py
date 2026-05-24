import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "agents"))

from config import load_runtime_config


class TestRuntimeConfig(unittest.TestCase):
    def test_runtime_dirs_always_resolve_from_project_root(self):
        project_root = PROJECT_ROOT
        agents_dir = project_root / "agents"

        with patch.dict(os.environ, {"MODEL_ID": "test-model"}, clear=False):
            original_cwd = Path.cwd()
            try:
                os.chdir(agents_dir)
                config = load_runtime_config()
            finally:
                os.chdir(original_cwd)

        self.assertEqual(config.workdir, project_root)
        self.assertEqual(config.runtime_dir, project_root / ".runtime")
        self.assertEqual(config.memory_dir, project_root / ".runtime" / "memory")
        self.assertEqual(config.tasks_dir, project_root / ".runtime" / "tasks")
        self.assertEqual(config.team_dir, project_root / ".runtime" / "team")
        self.assertEqual(config.transcript_dir, project_root / ".runtime" / "transcripts")

    def test_runtime_root_can_be_overridden_for_tests(self):
        project_root = PROJECT_ROOT
        override = project_root / "tests" / "tmp-workdir"

        with patch.dict(
            os.environ,
            {"MODEL_ID": "test-model", "CODEPILOT_WORKDIR": str(override)},
            clear=False,
        ):
            config = load_runtime_config()

        self.assertEqual(config.workdir, override.resolve())
        self.assertEqual(config.runtime_dir, override.resolve() / ".runtime")


if __name__ == "__main__":
    unittest.main()
