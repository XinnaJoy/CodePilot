import uuid

from agent_loop import run_agent_loop
from config import (
    IDLE_TIMEOUT,
    POLL_INTERVAL,
    TOKEN_THRESHOLD,
    configure_console_encoding,
    create_client,
    load_runtime_config,
)
from core.context import AgentContext
from infra.file_store import WorkspaceFileStore
from infra.shell_runner import ShellRunner
from memory import MemoryService
from repl import run_repl
from services.background_service import BackgroundManager
from services.message_bus import MessageBus
from services.skill_service import SkillLoader
from services.task_service import TaskManager
from services.teammate_service import TeammateManager
from services.todo_service import TodoManager
from tool_registry import ToolRegistry

configure_console_encoding()
CONFIG = load_runtime_config()
CLIENT = create_client(CONFIG.anthropic_base_url)
_CTX = None

shutdown_requests = {}
plan_requests = {}


def _build_session_id() -> str:
    return uuid.uuid4().hex[:12]


def build_context() -> AgentContext:
    file_store = WorkspaceFileStore(CONFIG.workdir)
    shell_runner = ShellRunner(CONFIG.workdir)
    todo = TodoManager()
    skills = SkillLoader(CONFIG.skills_dir)
    tasks = TaskManager(CONFIG.tasks_dir)
    background = BackgroundManager(shell_runner)
    bus = MessageBus(CONFIG.inbox_dir)
    memory = MemoryService.from_workdir(CONFIG.workdir)

    context = AgentContext(
        session_id=_build_session_id(),
        config=CONFIG,
        client=CLIENT,
        file_store=file_store,
        shell_runner=shell_runner,
        todo=todo,
        skills=skills,
        tasks=tasks,
        background=background,
        bus=bus,
        memory=memory,
        team=None,
        working_memory=memory.working_memory,
        session_db=memory.session_db,
    )
    context.team = TeammateManager(context, idle_timeout=IDLE_TIMEOUT, poll_interval=POLL_INTERVAL)
    return context


def get_context() -> AgentContext:
    global _CTX
    if _CTX is None:
        _CTX = build_context()
    return _CTX


TOOL_REGISTRY = ToolRegistry(get_context, shutdown_requests, plan_requests)


def agent_loop(messages: list):
    context = get_context()
    system_prompt = TOOL_REGISTRY.system_prompt(CONFIG)
    return run_agent_loop(
        messages,
        context,
        TOOL_REGISTRY.tools,
        TOOL_REGISTRY.handlers,
        system_prompt,
        TOKEN_THRESHOLD,
    )


if __name__ == "__main__":
    run_repl(get_context(), agent_loop)
