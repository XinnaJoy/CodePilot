#!/usr/bin/env python3
"""Safe shell execution helpers."""

import subprocess
import sys
from pathlib import Path


class ShellRunner:
    def __init__(self, workdir: Path, default_timeout: int = 120):
        self.workdir = workdir
        self.default_timeout = default_timeout

    def run(self, command: str, timeout: int | None = None) -> str:
        dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
        if any(pattern in command for pattern in dangerous):
            return "Error: Dangerous command blocked"

        try:
            if sys.platform == "win32":
                completed = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.workdir,
                    capture_output=True,
                    timeout=timeout or self.default_timeout,
                )
                try:
                    stdout = completed.stdout.decode("gbk", errors="replace")
                    stderr = completed.stderr.decode("gbk", errors="replace")
                except (UnicodeDecodeError, AttributeError):
                    stdout = completed.stdout.decode("utf-8", errors="replace")
                    stderr = completed.stderr.decode("utf-8", errors="replace")
                output = (stdout + stderr).strip()
            else:
                completed = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.workdir,
                    capture_output=True,
                    text=True,
                    timeout=timeout or self.default_timeout,
                    encoding="utf-8",
                    errors="replace",
                )
                output = (completed.stdout + completed.stderr).strip()
            return output[:50000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: Timeout ({timeout or self.default_timeout}s)"
