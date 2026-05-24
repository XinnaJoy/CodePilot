#!/usr/bin/env python3
"""Runtime configuration helpers for the agent."""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

TOKEN_THRESHOLD = 100000
POLL_INTERVAL = 5
IDLE_TIMEOUT = 60
VALID_MSG_TYPES = {
    "message",
    "broadcast",
    "shutdown_request",
    "shutdown_response",
    "plan_approval_response",
}


@dataclass
class RuntimeConfig:
    workdir: Path
    runtime_dir: Path
    team_dir: Path
    inbox_dir: Path
    tasks_dir: Path
    skills_dir: Path
    transcript_dir: Path
    memory_dir: Path
    model: str
    anthropic_base_url: str | None


def resolve_workdir() -> Path:
    override = os.getenv("CODEPILOT_WORKDIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def configure_console_encoding():
    """Best-effort UTF-8 console configuration for Windows."""
    if sys.platform != "win32":
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "replace")


def load_runtime_config() -> RuntimeConfig:
    load_dotenv(override=True)
    if os.getenv("ANTHROPIC_BASE_URL"):
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

    workdir = resolve_workdir()
    runtime_dir = workdir / ".runtime"
    team_dir = runtime_dir / "team"

    return RuntimeConfig(
        workdir=workdir,
        runtime_dir=runtime_dir,
        team_dir=team_dir,
        inbox_dir=team_dir / "inbox",
        tasks_dir=runtime_dir / "tasks",
        skills_dir=workdir / "skills",
        transcript_dir=runtime_dir / "transcripts",
        memory_dir=runtime_dir / "memory",
        model=os.environ["MODEL_ID"],
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )


def create_client(base_url: str | None) -> Anthropic:
    return Anthropic(base_url=base_url)
