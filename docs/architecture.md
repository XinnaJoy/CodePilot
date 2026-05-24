# CodePilot Architecture

## Overview

CodePilot 当前采用分层结构：

- Entry
- Runtime
- Core
- Infra
- Services
- Skills
- Tests

目标是让入口负责装配，让 runtime 负责调度，让 service 负责业务，让 infra 负责外部依赖。

## Layers

### Entry

入口文件是 [agents/MyAgent.py](/D:/Code/Demo/CodePilot/agents/MyAgent.py:1)。

职责：

- 初始化配置
- 构建 `AgentContext`
- 创建 `ToolRegistry`
- 启动 REPL

### Runtime

Runtime 负责控制执行流程：

- [agents/agent_loop.py](/D:/Code/Demo/CodePilot/agents/agent_loop.py:1)
- [agents/repl.py](/D:/Code/Demo/CodePilot/agents/repl.py:1)
- [agents/tool_registry.py](/D:/Code/Demo/CodePilot/agents/tool_registry.py:1)
- [agents/tool_schemas.py](/D:/Code/Demo/CodePilot/agents/tool_schemas.py:1)
- [agents/tool_handlers.py](/D:/Code/Demo/CodePilot/agents/tool_handlers.py:1)

其中：

- `tool_schemas` 定义模型可见工具
- `tool_handlers` 绑定工具到具体服务
- `tool_registry` 统一对外暴露

### Core

- [agents/core/context.py](/D:/Code/Demo/CodePilot/agents/core/context.py:1)

这里定义 `AgentContext`，用于承载所有共享依赖。

### Infra

Infra 只关心“怎么接外部世界”：

- 配置
- 文件系统
- Shell

文件：

- [agents/config.py](/D:/Code/Demo/CodePilot/agents/config.py:1)
- [agents/infra/file_store.py](/D:/Code/Demo/CodePilot/agents/infra/file_store.py:1)
- [agents/infra/shell_runner.py](/D:/Code/Demo/CodePilot/agents/infra/shell_runner.py:1)

### Services

Services 只表达业务能力：

- todo
- task
- skill
- background
- message bus
- subagent
- teammate

teammate 又继续拆成：

- [team_registry.py](/D:/Code/Demo/CodePilot/agents/services/team_registry.py:1)
- [teammate_runner.py](/D:/Code/Demo/CodePilot/agents/services/teammate_runner.py:1)
- [teammate_service.py](/D:/Code/Demo/CodePilot/agents/services/teammate_service.py:1)

### Memory

当前 memory 边界是：

- `WorkingMemory`
- `SessionDB`

不把长期 knowledge / experience DB 视为当前版本已实现能力。

## Dependency Direction

推荐依赖方向：

```text
Entry -> Runtime -> Services -> Infra
                -> Core
```

约束：

- `infra` 不依赖 `runtime`
- `services` 不直接依赖 REPL
- `runtime` 不直接操作底层文件细节
- `MyAgent.py` 不再承载业务实现

## Runtime Directories

以下目录是运行时目录，不属于源码：

- `.runtime/memory/`
- `.runtime/tasks/`
- `.runtime/team/`
- `.runtime/transcripts/`
- `.pytest_cache/`
- `__pycache__/`

历史遗留目录：

- `agents/.memory/`
- `agents/.tasks/`
- `agents/.team/`

建议持续清理，不再继续使用。
