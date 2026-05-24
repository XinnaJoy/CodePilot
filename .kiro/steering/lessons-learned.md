---
inclusion: auto
description: Project-specific patterns, preferences, and lessons learned over time (user-editable)
---

# Lessons Learned

This file captures project-specific patterns, coding preferences, common pitfalls, and architectural decisions that emerge during development. It serves as a workaround for continuous learning by allowing you to document patterns manually.

**How to use this file:**
1. The `extract-patterns` hook will suggest patterns after agent sessions
2. Review suggestions and add genuinely useful patterns below
3. Edit this file directly to capture team conventions
4. Keep it focused on project-specific insights, not general best practices

---

## Project-Specific Patterns

*Document patterns unique to this project that the team should follow.*

### Example: API Error Handling
```typescript
// Always use our custom ApiError class for consistent error responses
throw new ApiError(404, 'Resource not found', { resourceId });
```

---

## Code Style Preferences

*Document team preferences that go beyond standard linting rules.*

### Example: Import Organization
```typescript
// Group imports: external, internal, types
import { useState } from 'react';
import { Button } from '@/components/ui';
import type { User } from '@/types';
```

---

## Kiro Hooks

### `install.sh` is additive-only — it won't update existing installations
The installer skips any file that already exists in the target (`if [ ! -f ... ]`). Running it against a folder that already has `.kiro/` will not overwrite or update hooks, agents, or steering files. To push updates to an existing project, manually copy the changed files or remove the target files first before re-running the installer.

### README.md mirrors hook configurations — keep them in sync
The hooks table and Example 5 in README.md document the action type (`runCommand` vs `askAgent`) and behavior of each hook. When changing a hook's `then.type` or behavior, update both the hook file and the corresponding README entries to avoid misleading documentation.

### Prefer `askAgent` over `runCommand` for file-event hooks
`runCommand` hooks on `fileEdited` or `fileCreated` events spawn a new terminal session every time they fire, creating friction. Use `askAgent` instead so the agent handles the task inline. Reserve `runCommand` for `userTriggered` hooks where a manual, isolated terminal run is intentional (e.g., `quality-gate`).

---

## Common Pitfalls

*Document mistakes that have been made and how to avoid them.*

### Example: Database Transactions
- Always wrap multiple database operations in a transaction
- Remember to handle rollback on errors
- Don't forget to close connections in finally blocks

### Session Snapshot Data Loss Risk
- **Problem**: Current implementation only saves SQLite snapshots during auto_compact (tokens > 80k) or manual compress, creating data loss risk for: (1) short conversations that never reach threshold, (2) program crashes before compression, (3) user interruptions (Ctrl+C)
- **Impact**: All conversation history lost if session ends before compression trigger
- **Solution**: Implement hybrid persistence strategy:
  - **Periodic saves**: Save snapshot every N rounds (e.g., 10) with snapshot_type="periodic" to limit data loss window
  - **Exit handlers**: Register signal handlers (SIGINT, SIGTERM) and atexit to save on graceful shutdown
  - **Keep compression triggers**: Retain existing auto_compact and manual compress for continuity summaries
- **Performance**: SQLite snapshot write takes ~1-2ms, negligible impact when done every 10 rounds
- **Implementation note**: Wrap snapshot saves in try/except to prevent save failures from crashing the agent loop

---

## Architecture Decisions

*Document key architectural decisions and their rationale.*

### Example: State Management
- **Decision**: Use Zustand for global state, React Context for component trees
- **Rationale**: Zustand provides better performance and simpler API than Redux
- **Trade-offs**: Less ecosystem tooling than Redux, but sufficient for our needs

### Dual-Layer Task Management: TodoWrite vs task_create
- **Decision**: Use TodoWrite for single-session execution steps, task_create for multi-session project tasks
- **Decision Tree**:
  - **Use TodoWrite when**: Task completes in < 1 hour, single conversation, no dependencies, operation-level steps (e.g., "create file X", "run test Y")
  - **Use task_create when**: Task spans multiple sessions, needs persistence, has dependencies (blockedBy), feature-level work (e.g., "implement auth module")
  - **Hybrid approach**: Create task_create for project milestones, then use TodoWrite within each task execution to track granular steps
- **Rationale**: TodoWrite is in-memory and lightweight for immediate execution tracking; task_create provides persistent DAG-based dependency management for complex projects
- **System prompt guidance**: "Prefer task_create/task_update/task_list for multi-step work. Use TodoWrite for short checklists."
- **Example**: User says "build e-commerce frontend" → create task_create for each page (list, detail, cart) with dependencies → when executing task #1, create TodoWrite for steps (create component, add styles, write tests)

### Three-Stage Progressive Compression for Context Management
- **Decision**: Use microcompact → auto_compact → manual compress progression for managing conversation context
- **Stage 1 - Microcompact**: Runs every loop iteration before API call; clears old tool_result content (keeps last 3); no LLM call; ~2:1 compression
- **Stage 2 - Auto_compact**: Triggers when tokens > threshold (80k); saves full history to SQLite + JSONL transcript; calls Claude to generate continuity summary; replaces messages with summary; ~50:1 compression
- **Stage 3 - Manual compress**: Agent explicitly calls compress tool; immediately triggers auto_compact and exits loop; gives agent control over compression timing
- **Rationale**: Progressive approach balances performance (microcompact is cheap), effectiveness (auto_compact is powerful), and control (manual gives agent autonomy)
- **Critical implementation detail**: Always save snapshot to SQLite + transcript file BEFORE replacing messages, enabling full history recovery via get_session tool
- **Continuity preservation**: Auto_compact prompt is "Summarize for continuity" (not just "summarize") to ensure summary includes: completed tasks, current state, next steps

### Dual-Layer Memory Architecture: WorkingMemory + SQLite + Filesystem
- **Decision**: Use three-tier memory system for different persistence needs
- **Tier 1 - WorkingMemory (in-memory)**: Python dict/list for current session state (context variables, goal stack); fast O(1) access; volatile (cleared on restart)
- **Tier 2 - SessionDB (SQLite)**: Persistent snapshots of full conversation history + working memory state; enables session recovery after compression; indexed by session_id + timestamp
- **Tier 3 - MemoryFileStore (filesystem)**: Long-term knowledge organized by type (user/, feedback/, project/, reference/); human-readable markdown; auto-indexed to MEMORY.md
- **Rationale**: In-memory for speed, SQLite for reliable persistence, filesystem for human editability and cross-session knowledge
- **Snapshot strategy**: Save snapshot BEFORE every auto_compact with snapshot_type="auto_compact"; include both messages and working_memory.to_dict() for full state recovery
- **Recovery workflow**: get_latest_snapshot(session_id) → restore messages + working_memory.from_dict() → agent continues from exact pre-compression state

### Multi-Agent Collaboration: JSONL Message Bus + State Machine + Auto-Claim
- **Decision**: Use JSONL file-based message bus for inter-agent communication with state machine-driven autonomous task allocation
- **Message Bus (JSONL)**: Each agent has inbox file (e.g., worker.jsonl); messages appended atomically; read_inbox() consumes and clears file
  - **Why JSONL over database**: Simplicity (no dependencies), observability (cat worker.jsonl), atomicity (append is atomic), sufficient performance for <10 agents
- **State Machine**: working → idle → shutdown
  - **working**: Executing task; transitions to idle when agent calls idle tool
  - **idle**: Polling mode; checks inbox (priority 1) and unclaimed tasks (priority 2) every poll_interval seconds
  - **shutdown**: Terminal state; triggered by idle_timeout or shutdown_request message
- **Auto-Claim Mechanism**: In idle state, agent queries iter_unclaimed() which returns tasks matching: status="pending" AND owner=null AND blockedBy=[]
  - Agent automatically claims first unclaimed task and transitions back to working
  - Task completion triggers automatic dependency resolution (removes task_id from other tasks' blockedBy arrays)
- **Critical implementation details**:
  - Use daemon threads for teammates to prevent blocking main process
  - Wrap teammate loop in try/except to handle API failures gracefully (set status to shutdown on exception)
  - Poll inbox BEFORE checking unclaimed tasks (messages have higher priority than autonomous work)
  - Inject identity reminder if message history is short (<3 messages) to maintain agent context after long idle periods
- **Scalability consideration**: For >10 agents or high message frequency, migrate to Redis pub/sub or RabbitMQ; JSONL sufficient for current scale

### Background Command Execution: Threading + Queue + Auto-Notification
- **Decision**: Use Threading with Queue for non-blocking execution of long-running shell commands with automatic result notification
- **Architecture**: BackgroundManager spawns daemon threads for each background_run call; results pushed to thread-safe Queue; agent_loop.drain() consumes queue and injects results into conversation
- **Why Threading over asyncio**: 
  - subprocess.run is blocking; asyncio.create_subprocess_shell has Windows compatibility issues
  - Threading API simpler (no async/await, no event loop management)
  - Task isolation: thread crash doesn't affect other tasks or main loop
  - GIL impact minimal for I/O-bound subprocess tasks
- **Execution flow**:
  1. Agent calls background_run(command, timeout) → generates task_id, spawns daemon thread, returns immediately
  2. Worker thread executes shell_runner.run(command, timeout) in isolation
  3. On completion/error, worker thread puts notification in Queue: {"task_id", "status", "result"}
  4. Agent loop calls drain() every iteration BEFORE API call → consumes all notifications
  5. Notifications injected as `<background-results>` user message → agent sees results automatically
- **Critical implementation details**:
  - Use Queue (thread-safe) not list for notifications to avoid race conditions
  - Use daemon=True for worker threads so main process exit terminates background tasks
  - Wrap _exec in try/except to catch all exceptions (timeout, command not found, etc.) and update task status to "error"
  - Truncate result to 500 chars in notification to prevent context bloat
  - Use get_nowait() not get() to avoid blocking main thread
- **Performance benefit**: Parallel execution of long tasks (e.g., npm test 5min + npm build 3min = 5min total vs 8min serial)
- **Scalability consideration**: For >20 concurrent background tasks, consider ProcessPoolExecutor or asyncio; Threading sufficient for current scale

---

## Open Source Security

### Always verify .gitignore before first push
When preparing a project for open source release, explicitly verify that sensitive files (.env, API keys, database files) are properly ignored by running `git status --ignored` before the first push. The `.env` file containing API keys should appear in the "Ignored files" section, not in staged changes.

### Network issues require fallback upload strategies
GitHub push failures due to network connectivity are common in certain regions. Always provide users with alternative upload methods (GitHub web interface, GitHub Desktop) when `git push` fails, especially for initial repository setup.

---

## Notes

- Keep entries concise and actionable
- Remove patterns that are no longer relevant
- Update patterns as the project evolves
- Focus on what's unique to this project
