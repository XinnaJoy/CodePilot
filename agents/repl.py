#!/usr/bin/env python3
"""Interactive REPL entrypoint."""

import datetime as dt
import json
import shutil
import subprocess
import sys
import uuid

from services.compression_service import auto_compact


RESET = "\033[0m"
BOLD = "\033[1m"
GOLD = "\033[38;5;220m"
BLUE = "\033[38;5;111m"
CYAN = "\033[38;5;81m"
PURPLE = "\033[38;5;177m"
GREEN = "\033[38;5;77m"
WHITE = "\033[38;5;255m"
GRAY = "\033[38;5;248m"


def _current_branch(workdir) -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workdir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        branch = result.stdout.strip()
        return branch or "detached"
    except Exception:
        return "unknown"


def _build_session_id() -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    return f"{timestamp}-{short_id}"


def _visible_len(text: str) -> int:
    length = 0
    in_escape = False
    for char in text:
        if char == "\033":
            in_escape = True
            continue
        if in_escape:
            if char == "m":
                in_escape = False
            continue
        length += 1
    return length


def _pad(text: str, width: int) -> str:
    visible = _visible_len(text)
    if visible >= width:
        return text
    return text + (" " * (width - visible))


def _frame_line(content: str, inner_width: int) -> str:
    return f"| {_pad(content, inner_width)} |"


def _divider(inner_width: int) -> str:
    return "|" + "-" * (inner_width + 2) + "|"


def _ensure_utf8_console():
    if sys.platform != "win32":
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def print_startup_banner(context):
    _ensure_utf8_console()
    width = min(max(shutil.get_terminal_size((120, 30)).columns, 96), 140)
    inner_width = max(92, width - 4)
    branch = _current_branch(context.config.workdir)
    session_id = getattr(context, "session_id", _build_session_id())

    cat_art = [
        r"      /\_/\\",
        r"     ( •.• )",
        r"      > ^ <",
    ]

    title_lines = [
        f"{GOLD}{BOLD}CodePilot{RESET}",
        f"{GRAY}local coding agent{RESET}",
        f"{GRAY}structured, tool-ready, built for your workflow{RESET}",
    ]

    lines = []
    border = "+" + "=" * (inner_width + 2) + "+"
    lines.append(border)

    art_width = 18
    for index in range(max(len(cat_art), len(title_lines))):
        left = cat_art[index] if index < len(cat_art) else ""
        right = title_lines[index] if index < len(title_lines) else ""
        content = f"{left.ljust(art_width)}  {right}"
        lines.append(_frame_line(content, inner_width))

    lines.append(_frame_line("", inner_width))
    lines.append(_divider(inner_width))

    left_col_width = (inner_width - 4) // 2
    right_col_width = inner_width - left_col_width - 4
    info_pairs = [
        (
            f"{BLUE}WORKSPACE{RESET} : {WHITE}{context.config.workdir}{RESET}",
            f"{BLUE}BRANCH{RESET}    : {WHITE}{branch}{RESET}",
        ),
        (
            f"{BLUE}MODEL{RESET}     : {WHITE}{context.config.model}{RESET}",
            f"{BLUE}SESSION{RESET}   : {WHITE}{session_id}{RESET}",
        ),
        (
            f"{BLUE}RUNTIME{RESET}   : {WHITE}local python agent{RESET}",
            f"{BLUE}STATUS{RESET}    : {GREEN}ready{RESET}",
        ),
    ]
    for left, right in info_pairs:
        content = f"{_pad(left, left_col_width)}  {_pad(right, right_col_width)}"
        lines.append(_frame_line(content, inner_width))

    lines.append(_frame_line("", inner_width))
    lines.append(_divider(inner_width))

    features = [
        (f"{PURPLE}{BOLD}TOOLS{RESET}", f"{WHITE}bash  file  task  agent{RESET}"),
        (f"{PURPLE}{BOLD}MEMORY{RESET}", f"{WHITE}working + snapshot{RESET}"),
        (f"{PURPLE}{BOLD}TASKS{RESET}", f"{WHITE}.runtime/tasks managed{RESET}"),
        (f"{PURPLE}{BOLD}TEAM{RESET}", f"{WHITE}collaboration ready{RESET}"),
    ]
    quarter = (inner_width - 9) // 4
    header = " | ".join(_pad(title, quarter) for title, _ in features)
    detail = " | ".join(_pad(body, quarter) for _, body in features)
    lines.append(_frame_line(header, inner_width))
    lines.append(_frame_line(detail, inner_width))

    lines.append(_frame_line("", inner_width))
    lines.append(_divider(inner_width))

    commands = (
        f"{WHITE}Type {CYAN}/help{RESET} {WHITE}to see all commands  |  "
        f"{CYAN}/tasks{RESET}  |  {CYAN}/memory{RESET}  |  "
        f"{CYAN}/team{RESET}  |  {CYAN}/inbox{RESET}  |  {CYAN}/compact{RESET}"
    )
    lines.append(_frame_line(commands, inner_width))
    lines.append(border)

    print("\n".join(lines))
    context._startup_prompt = f"{GREEN}CodePilot{RESET} > "


def run_repl(context, agent_loop_runner):
    print_startup_banner(context)
    history = []
    while True:
        try:
            query = input(getattr(context, "_startup_prompt", "\033[36ms_full >> \033[0m"))
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        if query.strip() == "/compact":
            if history:
                print("[manual compact via /compact]")
                history[:] = auto_compact(
                    history,
                    context.client,
                    context.config.model,
                    context.config.transcript_dir,
                    memory=context.memory,
                    session_id=context.session_id,
                )
            continue
        if query.strip() == "/tasks":
            print(context.tasks.list_all())
            continue
        if query.strip() == "/team":
            print(context.team.list_all())
            continue
        if query.strip() == "/memory":
            print("=== Memory Statistics ===")
            print(json.dumps(context.memory.get_stats(), indent=2))
            print("\n=== Working Memory ===")
            print(context.memory.render())
            print("\n=== Long-term Memory Index ===")
            print(context.memory.render_index())
            continue
        if query.strip() == "/inbox":
            print(json.dumps(context.bus.read_inbox("lead"), indent=2))
            continue
        history.append({"role": "user", "content": query})
        agent_loop_runner(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()
