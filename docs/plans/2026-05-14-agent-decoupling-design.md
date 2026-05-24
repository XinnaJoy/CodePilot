# Agent 项目解耦重构设计文档

## 1. 背景

当前项目已经具备一个可运行的 Agent 原型，核心能力包括：

- 主 Agent 对话循环
- 文件与命令工具调用
- Todo 管理
- 任务持久化
- 子 Agent / Teammate 协作
- 后台任务执行
- 技能加载
- 会话压缩
- 工作记忆与会话快照

但这些能力当前大部分都集中在 [agents/MyAgent.py](/D:/Code/Demo/CodePilot/agents/MyAgent.py:1) 中，导致以下问题：

- 单文件职责过多，阅读和修改成本高
- 全局状态较多，模块边界不清晰
- 工具定义、业务逻辑、基础设施调用混在一起
- 某些能力很难单独测试或复用
- 后续继续增加功能时，耦合度会继续上升

本次重构的目标不是重写功能，而是在**尽量不改变现有行为**的前提下，完成结构降耦，为后续迭代留出空间。

## 2. 当前主要耦合点

### 2.1 主文件承担了过多职责

[agents/MyAgent.py](/D:/Code/Demo/CodePilot/agents/MyAgent.py:1) 当前同时承担了：

- 配置加载
- LLM 客户端初始化
- 文件系统安全控制
- Shell 执行
- Todo 管理
- 子 Agent 运行
- 技能扫描与加载
- 上下文压缩
- 任务持久化
- 后台任务管理
- 团队协作消息总线
- Teammate 生命周期管理
- Tool schema 定义
- Tool handler 分发
- 主 Agent loop
- REPL 入口

这意味着任何新功能都容易继续往一个文件堆积。

### 2.2 全局实例过多

当前模块级全局对象包括但不限于：

- `TODO`
- `SKILLS`
- `TASK_MGR`
- `BG`
- `BUS`
- `TEAM`
- `WORKING_MEM`
- `SESSION_DB`

这些对象让代码运行简单，但会带来：

- 测试隔离困难
- 生命周期不明确
- 依赖关系隐式化
- 后续支持多 session / 多 runtime 时扩展困难

### 2.3 Tool 层与业务实现耦合

当前 `TOOLS` 与 `TOOL_HANDLERS` 和具体实现强绑定，导致：

- 新增一个能力需要同时改 schema、handler、具体逻辑
- 工具注册逻辑和业务对象没有清晰分层
- 难以在不同 runtime 下复用同一组服务

### 2.4 团队协作模块职责过重

`TeammateManager` 同时处理：

- 团队成员注册
- 线程管理
- 消息处理
- 任务认领
- LLM 调用
- idle / shutdown 生命周期

这是当前最重的“复合职责模块”，后续应重点拆分。

### 2.5 记忆系统边界不完整

[agents/memory.py](/D:/Code/Demo/CodePilot/agents/memory.py:1) 当前实现的是：

- `WorkingMemory`
- `SessionDB`

但测试 [tests/test_memory_system.py](/D:/Code/Demo/CodePilot/tests/test_memory_system.py:1) 预期存在更完整的 `MemoryDB`，包括：

- 知识库存储
- 经验库存储
- 检索统计
- 长期记忆查询

这说明“记忆子系统”的设计意图与当前落地实现之间存在偏差。

## 3. 重构目标

本次重构目标分为 5 个层面。

### 3.1 结构目标

将当前“单文件总控”拆成“入口层 + runtime 层 + service 层 + infra 层”。

### 3.2 工程目标

- 让每个模块职责更单一
- 让依赖关系显式化
- 让测试可以按模块单独验证
- 让新增功能不必继续修改核心总控文件

### 3.3 行为目标

在第一阶段重构中，不主动改变用户可见功能，不重写对话逻辑，不改变工具协议。

### 3.4 测试目标

重构过程中保证：

- 核心导入路径清晰
- 现有测试可以逐步迁移
- 关键服务可单测

### 3.5 后续演进目标

为未来这些能力预留结构空间：

- 更完整的 memory system
- 多个不同类型的 subagent
- 更灵活的 tool registry
- Web / CLI / API 多入口

## 4. 目标架构

建议拆成以下结构：

```text
agents/
  main.py
  config.py
  agent_loop.py
  tool_registry.py

  core/
    models.py
    interfaces.py
    context.py

  infra/
    llm_client.py
    shell_runner.py
    file_store.py
    sqlite_store.py

  services/
    todo_service.py
    task_service.py
    skill_service.py
    compression_service.py
    background_service.py
    message_bus.py
    teammate_service.py
    subagent_service.py
    memory_service.py

  repl/
    commands.py
    console.py
```

说明如下。

### 4.1 入口层

`main.py`

- 负责启动程序
- 加载配置
- 组装依赖
- 启动 REPL

`config.py`

- 负责环境变量
- 负责工作目录、常量、阈值配置
- 集中管理 Anthropic 配置与路径配置

### 4.2 runtime 层

`agent_loop.py`

- 负责一轮轮调用模型
- 处理消息追加
- 调用压缩策略
- 注入 inbox / background 结果
- 不直接实现业务能力

`tool_registry.py`

- 负责 Tool schema
- 负责 tool name 到 handler 的注册
- 负责把服务方法暴露给 agent

### 4.3 core 层

`context.py`

- 定义 `AgentContext`
- 集中挂载 todo、tasks、bus、team、memory 等服务实例
- 用显式依赖代替模块级全局变量

`models.py`

- 放数据结构
- 如 task、message、snapshot、tool result 等

`interfaces.py`

- 放协议或抽象约定
- 例如 runner / store / bus 的接口定义

### 4.4 infra 层

`shell_runner.py`

- 负责安全执行 shell 命令
- 处理超时、编码、输出截断

`file_store.py`

- 负责安全路径校验
- 负责文件读写编辑

`llm_client.py`

- 负责 Anthropic 客户端封装
- 统一模型调用入口

`sqlite_store.py`

- 负责 SQLite 通用连接和基础存储支持

### 4.5 services 层

`todo_service.py`

- 管理对话期 todo 列表

`task_service.py`

- 管理 `.runtime/tasks/` 中的任务文件

`skill_service.py`

- 扫描 `skills/`
- 解析 `SKILL.md`
- 提供加载与描述能力

`compression_service.py`

- 负责 token 估算
- 微压缩
- 自动压缩

`background_service.py`

- 负责后台命令执行与通知

`message_bus.py`

- 负责 inbox 文件通信

`teammate_service.py`

- 负责 team member 生命周期管理
- 后续可以继续再拆

`subagent_service.py`

- 负责一次性子 Agent 执行

`memory_service.py`

- 统一暴露 working memory / session snapshot / 后续长期记忆

### 4.6 repl 层

`commands.py`

- 负责 `/compact`、`/tasks`、`/team`、`/memory`、`/inbox`

`console.py`

- 负责命令行循环和 I/O

## 5. 迁移映射

当前 [agents/MyAgent.py](/D:/Code/Demo/CodePilot/agents/MyAgent.py:1) 中的代码建议按下表迁移：

| 当前内容 | 目标文件 |
|---|---|
| `safe_path` `run_read` `run_write` `run_edit` | `infra/file_store.py` |
| `run_bash` | `infra/shell_runner.py` |
| `TodoManager` | `services/todo_service.py` |
| `run_subagent` | `services/subagent_service.py` |
| `SkillLoader` | `services/skill_service.py` |
| `estimate_tokens` `microcompact` `auto_compact` | `services/compression_service.py` |
| `TaskManager` | `services/task_service.py` |
| `BackgroundManager` | `services/background_service.py` |
| `MessageBus` | `services/message_bus.py` |
| `TeammateManager` | `services/teammate_service.py` |
| `SYSTEM` 相关拼装 | `config.py` 或 `tool_registry.py` |
| `TOOL_HANDLERS` `TOOLS` | `tool_registry.py` |
| `agent_loop` | `agent_loop.py` |
| `if __name__ == "__main__"` | `main.py` + `repl/console.py` |

当前 [agents/memory.py](/D:/Code/Demo/CodePilot/agents/memory.py:1) 中：

| 当前内容 | 目标文件 |
|---|---|
| `WorkingMemory` | `services/memory_service.py` 或 `core/models.py` |
| `SessionDB` | `services/memory_service.py` + `infra/sqlite_store.py` |
| `create_memory_system` | `services/memory_service.py` |

## 6. 推荐实施阶段

为了控制风险，建议按三阶段推进。

### 阶段一：低风险物理拆分

目标：

- 减少单文件体积
- 不改业务行为
- 不立刻重写依赖注入

本阶段拆出：

- `config.py`
- `infra/file_store.py`
- `infra/shell_runner.py`
- `services/todo_service.py`
- `services/task_service.py`
- `services/skill_service.py`
- `services/compression_service.py`

阶段一完成标准：

- `MyAgent.py` 
- 主逻辑仍可运行
- 导入路径稳定

### 阶段二：上下文容器化

目标：

- 移除模块级全局实例
- 引入显式依赖管理

本阶段新增：

- `core/context.py`
- `AgentContext`

把以下全局实例收拢到 context：

- `TODO`
- `SKILLS`
- `TASK_MGR`
- `BG`
- `BUS`
- `TEAM`
- `WORKING_MEM`
- `SESSION_DB`

阶段二完成标准：

- `agent_loop` 接收 context
- 服务之间依赖通过构造传入
- 测试可以构造独立 context

### 阶段三：工具层和协作层解耦

目标：

- 重构 tool 注册方式
- 继续拆解 teammate 子系统
- 明确 memory 子系统边界

本阶段重点：

- `tool_registry.py` 改为注册式组织
- `TeammateManager` 拆出内部职责
- `memory_service` 重新定义长期记忆方案

阶段三完成标准：

- 新增工具不需要修改巨型字典
- team 逻辑更可测
- memory 设计与测试预期开始对齐

## 7. Teammate 模块专项拆分建议

`TeammateManager` 不建议在第一阶段大拆，否则回归风险较高。建议在第二或第三阶段处理。

可拆成：

- `team_registry`
  - 管理成员配置
  - 负责成员列表和状态存储

- `teammate_runner`
  - 管理单个 teammate 的执行循环
  - 处理 inbox、idle、shutdown

- `team_coordinator`
  - 负责 spawn、claim、broadcast 等高层协调

这样拆的好处是：

- 生命周期逻辑和配置逻辑分开
- 更容易单测某个 teammate 行为
- 未来支持不同 teammate 类型更自然

## 8. Memory 模块专项建议

当前建议先明确 memory 的三个层次。

### 8.1 Working Memory

短期、会话内、临时状态：

- 当前目标
- 当前上下文键值
- 临时中间结论

### 8.2 Session Snapshot

用于压缩前恢复：

- messages snapshot
- working memory snapshot
- session id

### 8.3 Long-term Memory

如果后续要和测试对齐，应补充：

- `KnowledgeStore`
- `ExperienceStore`

如果暂时不做长期记忆，则建议：

- 修改测试范围
- 或调整文档，明确当前版本只支持 working/session memory

换句话说，这里需要先做“产品边界决策”，再改代码。

## 9. 风险与注意事项

### 9.1 最大风险

重构不是新功能开发，最容易出现的是“结构变好了，但行为悄悄变了”。

重点风险点：

- tool schema 与 handler 对不上
- 路径与工作目录行为变化
- 编码处理在 Windows 下退化
- 背景任务通知漏注入
- teammate idle / auto-claim 行为改变
- REPL 命令兼容性下降

### 9.2 风险控制手段

建议每个阶段都做最小回归验证：

- 能启动主 REPL
- 能执行 `read_file` / `bash`
- 能创建和列出 task
- 能加载 skill
- 能查看 memory
- 能运行至少一个基本测试

## 10. 验收标准

本次解耦重构完成后，应该满足：

### 10.1 结构验收

- `MyAgent.py` 不再承载全部实现
- 目录结构能表达职责划分
- 服务边界清晰

### 10.2 可维护性验收

- 新增一个工具时，只需改动有限文件
- 修改一个 service 时，不必理解全部 agent loop
- 新同学可以快速定位某个功能在哪个模块

### 10.3 可测试性验收

- 关键 service 可单独初始化
- 不依赖全局单例
- memory / task / skill 等可以单测

### 10.4 兼容性验收

- 主功能行为不显著变化
- 现有命令入口保留
- 后续可以继续分阶段补齐 memory 与 team 设计

## 11. 建议的下一步

建议下一轮讨论只聚焦三个决策，不要同时展开所有细节：

1. 是否接受“分三阶段重构”的节奏
2. 是否接受 `AgentContext` 作为统一依赖容器
3. `memory` 是要补成长期记忆系统，还是先把测试和产品边界对齐

这三个问题定下来之后，就可以进入第一阶段代码修改。

## 12. 本文档结论

当前项目的核心问题不是功能不足，而是结构已经接近“单体膨胀”的临界点。最合适的路径不是重写，而是：

- 先拆文件
- 再收依赖
- 最后拆工具层和重模块

这是一个风险最低、也最适合当前项目状态的解耦方案。
