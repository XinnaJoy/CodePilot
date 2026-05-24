# Claude Code 源码分析报告

## 概述

本文档分析了 Claude Code 的核心架构和设计模式,重点关注值得 CodePilot 学习的模块和机制。

## 一、核心模块结构

### 1.1 主要模块分类

Claude Code 采用了清晰的模块化架构:

```
src/
├── assistant/          # 会话历史管理
├── bridge/            # 远程连接和会话桥接
├── coordinator/       # 协调器模式(多 Agent 协同)
├── memdir/            # 记忆系统
├── services/          # 核心服务
│   ├── compact/       # 上下文压缩
│   ├── SessionMemory/ # 会话记忆
│   ├── api/           # API 调用
│   └── analytics/     # 分析和遥测
├── tasks/             # 任务管理
├── tools/             # 工具实现
├── state/             # 状态管理
└── utils/             # 工具函数
```

## 二、记忆系统 (Memory System)

### 2.1 设计理念

Claude Code 实现了**分层记忆系统**:

1. **MEMORY.md 索引文件** - 作为记忆入口点
2. **主题文件** - 每个记忆主题独立文件
3. **类型化记忆** - 四种记忆类型:
   - `user` - 用户信息和偏好
   - `feedback` - 用户反馈和纠正
   - `project` - 项目上下文
   - `reference` - 外部引用

### 2.2 关键特性

#### 索引 + 内容分离
```typescript
// MEMORY.md 只存储索引(每行 ~150 字符)
- [Title](file.md) — one-line hook

// 详细内容存储在独立文件中
// 文件包含 frontmatter 元数据
---
name: User Role
type: user
description: User's professional role and context
---
```

#### 自动记忆 (Auto Memory)
- 路径: `~/.claude/projects/<slug>/memory/`
- 自动创建目录,无需用户手动管理
- 支持日志模式(KAIROS 特性):
  - 按日期组织: `logs/YYYY/MM/YYYY-MM-DD.md`
  - 追加式写入,避免重写
  - 夜间自动提炼到主题文件

#### 记忆截断保护
```typescript
export const MAX_ENTRYPOINT_LINES = 200
export const MAX_ENTRYPOINT_BYTES = 25_000

function truncateEntrypointContent(raw: string): EntrypointTruncation {
  // 先按行数截断
  // 再按字节数截断(在最后一个换行符处)
  // 添加警告信息
}
```

### 2.3 值得学习的点

✅ **索引分离设计** - 避免加载大量不相关内容
✅ **类型化记忆** - 明确记忆的用途和范围
✅ **自动截断** - 防止记忆文件过大影响性能
✅ **日志模式** - 适合长期运行的 Assistant 模式

## 三、上下文压缩 (Context Compaction)

### 3.1 多层压缩策略

Claude Code 实现了**三层压缩机制**:

#### 1. Microcompact (微压缩)
- **目标**: 清理工具调用结果,不破坏缓存
- **触发**: 自动,每次请求前
- **方法**: 
  - 时间触发: 距离上次 assistant 消息超过阈值
  - 计数触发: 工具结果数量超过阈值
  - 缓存编辑: 使用 `cache_edits` API 删除旧工具结果

```typescript
// 可压缩的工具类型
const COMPACTABLE_TOOLS = new Set([
  FILE_READ_TOOL_NAME,
  BASH_TOOL_NAME,
  GREP_TOOL_NAME,
  GLOB_TOOL_NAME,
  WEB_SEARCH_TOOL_NAME,
  WEB_FETCH_TOOL_NAME,
  FILE_EDIT_TOOL_NAME,
  FILE_WRITE_TOOL_NAME,
])

// 时间触发配置
type TimeBasedMCConfig = {
  enabled: boolean
  gapThresholdMinutes: number  // 默认 5 分钟
  keepRecent: number            // 保留最近 N 个工具结果
}
```

#### 2. Session Memory Compaction (会话记忆压缩)
- **目标**: 提取关键信息到会话记忆文件
- **触发**: 
  - 初始化阈值: 10,000 tokens
  - 更新阈值: 增长 5,000 tokens
  - 工具调用间隔: 每 3 次工具调用
- **方法**: 
  - 使用子 Agent 提取记忆
  - 保存到 `session_memory.md`
  - 删除已提取的消息

```typescript
export type SessionMemoryConfig = {
  minimumMessageTokensToInit: number      // 10,000
  minimumTokensBetweenUpdate: number      // 5,000
  toolCallsBetweenUpdates: number         // 3
}
```

#### 3. Full Compaction (完整压缩)
- **目标**: 总结整个对话历史
- **触发**: 
  - 自动: 上下文窗口使用率 > 阈值
  - 手动: `/compact` 命令
- **方法**:
  - 使用 forked agent 生成摘要
  - 创建 compact boundary marker
  - 重新注入关键文件和技能

```typescript
// 自动压缩阈值计算
export function getAutoCompactThreshold(model: string): number {
  const effectiveContextWindow = getEffectiveContextWindowSize(model)
  return effectiveContextWindow - AUTOCOMPACT_BUFFER_TOKENS  // 13,000
}

// 压缩后重新注入
const POST_COMPACT_MAX_FILES_TO_RESTORE = 5
const POST_COMPACT_TOKEN_BUDGET = 50_000
const POST_COMPACT_MAX_TOKENS_PER_FILE = 5_000
const POST_COMPACT_MAX_TOKENS_PER_SKILL = 5_000
const POST_COMPACT_SKILLS_TOKEN_BUDGET = 25_000
```

### 3.2 压缩流程

```
1. Pre-Compact Hooks
   ↓
2. 生成摘要 (使用 forked agent)
   ↓
3. 清理状态 (readFileState, loadedNestedMemoryPaths)
   ↓
4. 创建 Compact Boundary Marker
   ↓
5. 重新注入:
   - 最近读取的文件 (最多 5 个)
   - 已调用的技能
   - 计划文件 (如果存在)
   - Delta attachments (工具/Agent/MCP 变更)
   ↓
6. Session Start Hooks
   ↓
7. Post-Compact Hooks
```

### 3.3 值得学习的点

✅ **分层压缩** - 不同粒度的压缩策略
✅ **缓存感知** - 使用 cache_edits 避免破坏缓存
✅ **智能重注入** - 压缩后恢复关键上下文
✅ **熔断机制** - 连续失败后停止自动压缩
✅ **时间触发** - 基于时间间隔的压缩策略

## 四、任务管理 (Task Management)

### 4.1 任务类型

```typescript
export type TaskType =
  | 'local_bash'           // 本地 Shell 命令
  | 'local_agent'          // 本地 Agent
  | 'remote_agent'         // 远程 Agent
  | 'in_process_teammate'  // 进程内队友
  | 'local_workflow'       // 本地工作流
  | 'monitor_mcp'          // MCP 监控
  | 'dream'                // Dream 任务

export type TaskStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'killed'
```

### 4.2 任务状态管理

```typescript
export type TaskStateBase = {
  id: string                // 任务 ID (带类型前缀)
  type: TaskType
  status: TaskStatus
  description: string
  toolUseId?: string        // 关联的工具调用 ID
  startTime: number
  endTime?: number
  totalPausedMs?: number
  outputFile: string        // 输出文件路径
  outputOffset: number      // 输出偏移量
  notified: boolean         // 是否已通知
}

// 任务 ID 生成 (带类型前缀)
const TASK_ID_PREFIXES: Record<string, string> = {
  local_bash: 'b',
  local_agent: 'a',
  remote_agent: 'r',
  in_process_teammate: 't',
  local_workflow: 'w',
  monitor_mcp: 'm',
  dream: 'd',
}

function generateTaskId(type: TaskType): string {
  const prefix = getTaskIdPrefix(type)
  const bytes = randomBytes(8)
  // 36^8 ≈ 2.8 trillion combinations
  return prefix + randomString(bytes, TASK_ID_ALPHABET)
}
```

### 4.3 值得学习的点

✅ **类型化任务** - 清晰的任务分类
✅ **状态机** - 明确的状态转换
✅ **输出管理** - 任务输出持久化到文件
✅ **ID 设计** - 带类型前缀的 ID,易于识别

## 五、协调器模式 (Coordinator Mode)

### 5.1 设计理念

Claude Code 实现了**协调器-工作者**模式:

- **协调器 (Coordinator)**: 主 Agent,负责:
  - 与用户交互
  - 分解任务
  - 调度工作者
  - 综合结果

- **工作者 (Worker)**: 子 Agent,负责:
  - 执行具体任务
  - 研究、实现、验证
  - 报告结果

### 5.2 工作流程

```
用户请求
   ↓
协调器分析
   ↓
生成工作者提示 (synthesize)
   ↓
并行启动多个工作者
   ↓
工作者执行任务
   ↓
工作者报告结果 (<task-notification>)
   ↓
协调器综合结果
   ↓
向用户报告
```

### 5.3 关键设计

#### 工作者通知格式
```xml
<task-notification>
<task-id>{agentId}</task-id>
<status>completed|failed|killed</status>
<summary>{human-readable status summary}</summary>
<result>{agent's final text response}</result>
<usage>
  <total_tokens>N</total_tokens>
  <tool_uses>N</tool_uses>
  <duration_ms>N</duration_ms>
</usage>
</task-notification>
```

#### 工作者工具限制
```typescript
const ASYNC_AGENT_ALLOWED_TOOLS = [
  BASH_TOOL_NAME,
  FILE_READ_TOOL_NAME,
  FILE_EDIT_TOOL_NAME,
  GREP_TOOL_NAME,
  GLOB_TOOL_NAME,
  // ... 标准工具
]

// 内部工具(协调器专用)
const INTERNAL_WORKER_TOOLS = new Set([
  TEAM_CREATE_TOOL_NAME,
  TEAM_DELETE_TOOL_NAME,
  SEND_MESSAGE_TOOL_NAME,
  SYNTHETIC_OUTPUT_TOOL_NAME,
])
```

#### 任务阶段
```
1. Research (研究) - 并行工作者
   ↓
2. Synthesis (综合) - 协调器
   ↓
3. Implementation (实现) - 工作者
   ↓
4. Verification (验证) - 工作者
```

### 5.4 值得学习的点

✅ **职责分离** - 协调器不执行具体任务
✅ **并行执行** - 充分利用多 Agent 并发
✅ **上下文隔离** - 工作者看不到协调器对话
✅ **结果综合** - 协调器负责理解和综合结果
✅ **继续 vs 新建** - 根据上下文重叠度选择

## 六、历史记录系统 (History System)

### 6.1 设计特点

#### 全局历史文件
```typescript
// 所有项目共享一个历史文件
const historyPath = join(getClaudeConfigHomeDir(), 'history.jsonl')

type LogEntry = {
  display: string
  pastedContents: Record<number, StoredPastedContent>
  timestamp: number
  project: string
  sessionId?: string
}
```

#### 粘贴内容管理
```typescript
// 小内容内联存储
const MAX_PASTED_CONTENT_LENGTH = 1024

// 大内容外部存储(使用哈希引用)
type StoredPastedContent = {
  id: number
  type: 'text' | 'image'
  content?: string        // 内联内容
  contentHash?: string    // 哈希引用
  mediaType?: string
  filename?: string
}
```

#### 会话优先排序
```typescript
// 当前会话的历史优先显示
async function* getHistory(): AsyncGenerator<HistoryEntry> {
  const currentSession = getSessionId()
  const otherSessionEntries: LogEntry[] = []
  
  for await (const entry of makeLogEntryReader()) {
    if (entry.sessionId === currentSession) {
      yield await logEntryToHistoryEntry(entry)  // 立即返回
    } else {
      otherSessionEntries.push(entry)  // 缓存其他会话
    }
  }
  
  // 然后返回其他会话的历史
  for (const entry of otherSessionEntries) {
    yield await logEntryToHistoryEntry(entry)
  }
}
```

### 6.2 值得学习的点

✅ **全局历史** - 跨项目共享历史记录
✅ **会话隔离** - 当前会话历史优先
✅ **内容分离** - 大内容外部存储
✅ **异步刷新** - 不阻塞主流程
✅ **撤销支持** - `removeLastFromHistory()` 支持中断恢复

## 七、Checkpoint 和恢复机制

### 7.1 会话存储

Claude Code 使用 **JSONL 格式**存储会话:

```typescript
// 会话文件路径
const transcriptPath = getTranscriptPath()
// ~/.claude/projects/<slug>/sessions/<session-id>.jsonl

// 每条消息一行 JSON
{
  "type": "user" | "assistant" | "system",
  "uuid": "...",
  "timestamp": "...",
  "message": { ... },
  "parentUuid": "..."
}
```

### 7.2 恢复流程

```typescript
// 1. 读取会话元数据
const metadata = readLiteMetadata(transcriptPath)

// 2. 加载消息历史
const messages = await loadSessionMessages(sessionId)

// 3. 恢复状态
- readFileState (文件读取缓存)
- loadedNestedMemoryPaths (记忆路径)
- sentSkillNames (已发送的技能)
- discoveredToolNames (已发现的工具)

// 4. 重新注入上下文
- System prompt
- User context
- Memory files
- Skills
```

### 7.3 Compact Boundary

```typescript
type SystemCompactBoundaryMessage = {
  type: 'system'
  compactMetadata: {
    trigger: 'auto' | 'manual'
    preCompactTokenCount: number
    lastPreCompactMessageUuid?: string
    preCompactDiscoveredTools?: string[]
    preservedSegment?: {
      headUuid: string
      anchorUuid: string
      tailUuid: string
    }
  }
}
```

### 7.4 值得学习的点

✅ **JSONL 格式** - 易于追加和解析
✅ **元数据分离** - 快速读取会话信息
✅ **状态恢复** - 完整恢复运行时状态
✅ **Boundary 标记** - 清晰标记压缩点

## 八、对 CodePilot 的建议

### 8.1 立即可以借鉴的设计

1. **分层记忆系统**
   - 实现 `MEMORY.md` 索引 + 主题文件
   - 添加记忆类型分类
   - 实现自动截断保护

2. **微压缩机制**
   - 实现时间触发的工具结果清理
   - 保留最近 N 个工具结果
   - 添加压缩警告抑制

3. **任务 ID 设计**
   - 使用类型前缀 (b/a/r/t)
   - 生成足够长的随机 ID

4. **会话历史优化**
   - 当前会话历史优先
   - 大内容外部存储
   - 异步刷新机制

### 8.2 中期可以实现的功能

1. **会话记忆压缩**
   - 实现增量记忆提取
   - 设置合理的触发阈值
   - 保存到独立的记忆文件

2. **完整压缩系统**
   - 实现自动压缩触发
   - 添加熔断机制
   - 实现智能重注入

3. **Checkpoint 系统**
   - 使用 JSONL 格式存储
   - 实现状态恢复
   - 添加 Boundary 标记

### 8.3 长期可以探索的方向

1. **协调器模式**
   - 实现主 Agent + 子 Agent 架构
   - 支持并行任务执行
   - 实现结果综合机制

2. **缓存感知压缩**
   - 使用 cache_edits API
   - 避免破坏 prompt cache
   - 实现缓存删除通知

3. **远程会话**
   - 实现 Bridge 机制
   - 支持远程 Agent 执行
   - 实现会话同步

## 九、总结

Claude Code 的架构设计体现了以下核心原则:

1. **模块化** - 清晰的职责分离
2. **可扩展** - 插件化的工具和服务
3. **性能优化** - 多层缓存和压缩
4. **用户体验** - 自动化的记忆和压缩
5. **可靠性** - 完善的错误处理和恢复

CodePilot 可以从以下方面优先学习:

1. ✅ **记忆系统** - 索引分离、类型化、自动截断
2. ✅ **微压缩** - 时间触发、工具结果清理
3. ✅ **任务管理** - 类型化任务、状态机
4. ✅ **历史记录** - 会话优先、内容分离
5. 🔄 **会话记忆** - 增量提取、独立存储
6. 🔄 **完整压缩** - 自动触发、智能重注入
7. 🔄 **Checkpoint** - JSONL 存储、状态恢复
8. 🚀 **协调器模式** - 多 Agent 协同、并行执行

通过逐步实现这些功能,CodePilot 可以构建一个更加强大和用户友好的 Agent 系统。
