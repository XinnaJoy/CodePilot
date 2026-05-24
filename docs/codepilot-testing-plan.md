# CodePilot Testing Plan

## Goal

先把 `CodePilot` 的测试体系做稳，再补真实任务评测。

优先级：

1. Runtime 稳定
2. 安全边界稳定
3. 行为可复现
4. Benchmark 可回归
5. 指标可量化

## Testing Model

参考 `pico`，测试分 6 层：

### 1. Unit Tests

覆盖纯逻辑模块：

- state
- memory
- context builder
- tool validation
- artifact writer

目标：

- 快
- 易定位
- 不依赖真实模型

### 2. Agent Behavior Tests

用脚本化 `FakeModelClient` 驱动多轮 agent loop。

覆盖：

- tool -> final
- retry
- malformed tool output recovery
- session resume
- delegate
- trace/report 落盘

目标：

- 稳定复现 agent 行为
- 测控制循环，不测模型能力

### 3. Safety Invariant Tests

覆盖高风险边界：

- path escape
- symlink escape
- approval deny
- read-only mode
- secret redaction
- shell env allowlist

目标：

- 安全规则单独成套
- 不和功能测试混在一起

### 4. Harness Regression Tests

做固定 benchmark harness。

每个任务包含：

- `prompt`
- `fixture_repo`
- `allowed_tools`
- `step_budget`
- `verifier`
- `category`

目标：

- fresh fixture copy
- fresh run directory
- deterministic outputs
- verifier 作为最终判定

### 5. Recovery Tests

覆盖恢复链路：

- checkpoint create
- checkpoint resume
- stale summary invalidation
- workspace mismatch
- runtime identity mismatch
- partial success recovery

目标：

- 证明 agent 能恢复
- 不是只会从头再跑

### 6. Metrics / Ablation Tests

最后补收益验证：

- context ablation
- memory ablation
- recovery ablation

目标：

- 量化模块收益
- 形成可复用报告

## Proposed Layout

```text
tests/
  test_state.py
  test_memory.py
  test_context_manager.py
  test_tools.py
  test_run_store.py
  test_agent_runtime.py
  test_safety_invariants.py
  test_evaluator.py
  test_metrics.py
  fixtures/
    bench_repo_readme/
    bench_repo_patch/

benchmarks/
  coding_tasks.json

artifacts/
  harness-regression-v1.json
  context-ablation-v1.json
  memory-ablation-v1.json
  recovery-ablation-v1.json

docs/
  codepilot-testing-plan.md
  metrics/
    codepilot-benchmark-core-report.md
```

## Execution Order

### Phase 1. Test Harness Base

先补最小测试基础设施：

- `FakeModelClient`
- 临时 workspace builder
- session/run artifact helper
- fixture copy helper

完成标准：

- 不接真实模型也能跑 agent loop

### Phase 2. Core Unit + Behavior

先写最关键的本地回归测试：

- state
- memory
- context
- run artifacts
- tool loop
- retry/recovery 基础行为

完成标准：

- 核心 runtime 每次改动都能快速回归

### Phase 3. Safety Suite

独立补安全测试：

- 路径逃逸
- 权限拒绝
- secret masking
- shell 环境隔离

完成标准：

- 风险动作可验证
- 错误路径有固定断言

### Phase 4. Fixed Benchmark Harness

建立固定任务集和 verifier。

要求：

- 每次运行复制 fixture
- 每个任务独立 run dir
- 结果写 artifact

完成标准：

- 能产出稳定 benchmark JSON

### Phase 5. Recovery Coverage

补 checkpoint / resume / stale memory 相关测试和 benchmark 任务。

完成标准：

- 恢复能力进入回归体系

### Phase 6. Metrics Report

最后补 ablation 和汇总报告。

完成标准：

- 能输出核心指标
- 能区分“可写进简历”和“仅内部分析”指标

## Rules

- 先测 runtime 合同，再测真实任务效果
- 先 deterministic，再引入真实模型评测
- 失败优先能定位到模块，不接受“大而全但难排查”的测试
- benchmark 结果必须可复现
- trace/report/checkpoint 都算可测试产物

## Immediate Next Steps

后续按这个顺序执行：

1. 建 `FakeModelClient` 和测试 helper
2. 建 `test_state.py / test_run_store.py / test_agent_runtime.py`
3. 建 `test_safety_invariants.py`
4. 建 `benchmarks/coding_tasks.json` 和 `test_evaluator.py`
5. 建 recovery 和 metrics

## Done Criteria

满足以下条件后，测试体系算第一阶段完成：

- 本地单测可稳定跑通
- agent 行为测试可复现
- 安全边界有独立测试
- benchmark harness 可重复执行
- 至少有一份核心指标报告
