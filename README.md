# CodePilot

一个基于 Anthropic / Claude API 的本地 Agent 项目，支持工具调用、任务管理、多智能体协作、技能加载，以及工作记忆与会话恢复。

当前版本已经完成一轮较完整的解耦重构，代码结构从“单文件大总控”调整为“入口层 + runtime 层 + service 层 + infra 层”，更适合后续继续迭代。

## 功能概览

- Agent 主循环与工具调用
- 安全的文件读写与 shell 执行
- 对话期 Todo 管理
- 持久化任务板
- 子 Agent 执行
- 多 teammate 协作
- 技能系统 `skills/*/SKILL.md`
- 工作记忆与会话快照恢复
- 后台任务执行与消息总线

## 快速开始

### 环境要求

- Python 3.10+
- 可用的 Anthropic 兼容 API Key

### 安装

```bash
pip install -r requirements.txt
```

复制环境变量模板：

```bash
cp .env.example .env
```

最少需要配置：

```env
ANTHROPIC_API_KEY=your-key
MODEL_ID=claude-sonnet-4-6
```

如果你使用兼容 Anthropic 协议的第三方服务，也可以设置：

```env
ANTHROPIC_BASE_URL=https://your-provider.example.com/anthropic
```

### 运行

```bash
python agents/MyAgent.py
```

## REPL 命令

- `/compact` 手动压缩上下文
- `/tasks` 查看任务板
- `/team` 查看 teammate 状态
- `/memory` 查看记忆统计与 working memory
- `/inbox` 查看 lead inbox

## 当前项目架构

### 入口层

- [agents/MyAgent.py](/D:/Code/Demo/CodePilot/agents/MyAgent.py:1)
  负责启动、装配 `AgentContext`、注册工具、接入 REPL

### Runtime 层

- [agents/agent_loop.py](/D:/Code/Demo/CodePilot/agents/agent_loop.py:1)
  Agent 主循环，负责模型调用、工具结果回注、压缩与消息注入
- [agents/repl.py](/D:/Code/Demo/CodePilot/agents/repl.py:1)
  交互式命令行入口
- [agents/tool_registry.py](/D:/Code/Demo/CodePilot/agents/tool_registry.py:1)
  工具注册 facade
- [agents/tool_schemas.py](/D:/Code/Demo/CodePilot/agents/tool_schemas.py:1)
  工具 schema 定义
- [agents/tool_handlers.py](/D:/Code/Demo/CodePilot/agents/tool_handlers.py:1)
  工具 handler 绑定

### Core 层

- [agents/core/context.py](/D:/Code/Demo/CodePilot/agents/core/context.py:1)
  统一依赖容器 `AgentContext`

### Infra 层

- [agents/config.py](/D:/Code/Demo/CodePilot/agents/config.py:1)
  运行时配置与常量
- [agents/infra/file_store.py](/D:/Code/Demo/CodePilot/agents/infra/file_store.py:1)
  安全文件访问
- [agents/infra/shell_runner.py](/D:/Code/Demo/CodePilot/agents/infra/shell_runner.py:1)
  Shell 执行封装

### Service 层

- [agents/services/todo_service.py](/D:/Code/Demo/CodePilot/agents/services/todo_service.py:1)
- [agents/services/task_service.py](/D:/Code/Demo/CodePilot/agents/services/task_service.py:1)
- [agents/services/skill_service.py](/D:/Code/Demo/CodePilot/agents/services/skill_service.py:1)
- [agents/services/background_service.py](/D:/Code/Demo/CodePilot/agents/services/background_service.py:1)
- [agents/services/message_bus.py](/D:/Code/Demo/CodePilot/agents/services/message_bus.py:1)
- [agents/services/subagent_service.py](/D:/Code/Demo/CodePilot/agents/services/subagent_service.py:1)
- [agents/services/teammate_service.py](/D:/Code/Demo/CodePilot/agents/services/teammate_service.py:1)
- [agents/services/team_registry.py](/D:/Code/Demo/CodePilot/agents/services/team_registry.py:1)
- [agents/services/teammate_runner.py](/D:/Code/Demo/CodePilot/agents/services/teammate_runner.py:1)

### Memory

- [agents/memory.py](/D:/Code/Demo/CodePilot/agents/memory.py:1)
  当前只保留：
  - `WorkingMemory`
  - `SessionDB`

说明：当前版本**不再把长期知识库记忆作为已实现能力**，测试边界已经收缩到当前真实能力。

## 目录结构

```text
CodePilot/
├─ agents/
│  ├─ MyAgent.py
│  ├─ agent_loop.py
│  ├─ repl.py
│  ├─ config.py
│  ├─ tool_registry.py
│  ├─ tool_schemas.py
│  ├─ tool_handlers.py
│  ├─ memory.py
│  ├─ core/
│  ├─ infra/
│  └─ services/
├─ docs/
│  ├─ plans/
│  ├─ architecture.md
│  └─ development.md
├─ skills/
├─ tests/
└─ README.md
```

## 技能系统

技能目录位于 `skills/`，每个技能一个子目录，最少包含一个 `SKILL.md`：

```text
skills/
  my-skill/
    SKILL.md
```

Agent 会在运行时扫描这些技能，并通过 `load_skill` 工具进行按需加载。

## 测试

运行全部测试：

```bash
pytest tests/
```

运行当前最核心的记忆系统测试：

```bash
pytest tests/test_memory_system.py
```

## 开发文档

- [docs/architecture.md](/D:/Code/Demo/CodePilot/docs/architecture.md:1)
  当前架构分层、依赖方向、运行时目录说明
- [docs/development.md](/D:/Code/Demo/CodePilot/docs/development.md:1)
  日常开发、扩展模块、增加工具、重构约束
- [docs/plans/2026-05-14-agent-decoupling-design.md](/D:/Code/Demo/CodePilot/docs/plans/2026-05-14-agent-decoupling-design.md:1)
  本轮解耦重构设计记录

## 运行时目录说明

下面这些目录属于运行时产物，不应该作为项目源码的一部分：

- `.runtime/memory/`
- `.runtime/tasks/`
- `.runtime/team/`
- `.runtime/transcripts/`
- `.pytest_cache/`
- `__pycache__/`

另外，旧结构中遗留在 `agents/` 下的：

- `agents/.memory/`
- `agents/.tasks/`
- `agents/.team/`

也属于历史运行产物，建议逐步移除，不再保留。

## 许可证

MIT，见 [LICENSE](/D:/Code/Demo/CodePilot/LICENSE:1)。
