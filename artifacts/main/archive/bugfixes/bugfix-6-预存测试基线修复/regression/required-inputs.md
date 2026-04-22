# Regression Required Inputs

When compilation fails, startup fails, or user-supplied data is required before the investigation can continue, the AI must fill out this file first and only then ask the human to complete it.
If startup logs, compile output, test failures, or stack traces are already available locally, the AI should collect and analyze them first instead of asking the human for those local artifacts.

## 1. Current Problem

- Issue summary: bugfix-6 预存测试基线（3 fail + 3 error）全为测试漂移，生产代码无需改动。
- Related regression: bugfix-6 内联 regression（无独立 reg-id）。
- Linked change: 无；后续 executing 仅改 `tests/test_cli.py` 与 `tests/test_cycle_detection.py`。

## 2. Required Human Inputs

| Item | Required | Notes |
| --- | --- | --- |
| Configuration | no | 所有失败均来自本地 `unittest discover`，无外部配置。 |
| Test data | no | 无测试数据依赖，全部基于内置模板与 tmpdir。 |
| Account details | no | 不涉及账号 / 权限 / scope。 |
| External dependency details | no | 不涉及第三方依赖或回调。 |

## 3. Human Response Section

- Configuration: n/a
- Test data: n/a
- Account details: n/a
- External dependency details: n/a

## 4. Next Step

- 诊断阶段已完成，路由建议 `harness regression --confirm`（主 agent 执行）。
- 进入 planning/executing 后按 R1/R2/R3 三类修测试断言与 import。
