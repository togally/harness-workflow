# Test Evidence — bugfix-4

## 测试环境

- 空仓：`/tmp/harness-bugfix4-20260419-120634/`
- `git init` 后执行 `harness install --agent claude`
- harness 二进制：`/Users/jiazhiwei/.local/bin/harness`（editable install → `/Users/jiazhiwei/IdeaProjects/harness-workflow/src`）
- 主仓：`/Users/jiazhiwei/IdeaProjects/harness-workflow/`
- 日期：2026-04-19

## 场景矩阵

| # | 场景 | 期望 | 实际 | 结果 |
|---|------|------|------|------|
| 1 | `runtime.yaml` 内容 | 所有字段初始值，无 `req-25` | `current_requirement: ""`, `stage: ""`, `active_requirements: []`, `ff_mode: false` | PASS |
| 2 | `.workflow/state/sessions/` | 空目录 | 空目录（仅 `.` / `..`） | PASS |
| 3 | `.workflow/flow/archive/` | 不存在（legacy 未被创建） | 目录不存在（`ls` 返回 No such file or directory） | PASS |
| 4 | `.workflow/flow/suggestions/` | 不存在或空 | 目录不存在 | PASS |
| 5 | `.workflow/state/requirements/` | 空目录 | 空目录 | PASS |
| 6 | `.workflow/flow/requirements/` | 空目录 | 空目录 | PASS |
| 7 | `.workflow/archive/` | 不存在 | 不存在 | PASS |
| 8 | `harness requirement "smoke"` → 成功创建 req-01 | runtime 更新为 req-01 / requirement_review；`req-01-smoke.yaml` 创建 | runtime `current_requirement: req-01`, `stage: requirement_review`, `active_requirements: [req-01]`；创建 `artifacts/main/requirements/req-01-smoke/requirement.md` | PASS |
| 9 | 主仓 `harness status` 仍正常 | 主仓 runtime 读出 bugfix-4/regression | `current_requirement: bugfix-4`, `stage: regression`, `active_requirements: req-27, req-25, bugfix-3, bugfix-4` | PASS |

**7/7 核心场景 + 2 补充场景全部 PASS。**

## 关键输出日志

### Test 1：runtime.yaml 内容

```yaml
current_requirement: ""
stage: ""
conversation_mode: "open"
locked_requirement: ""
locked_stage: ""
current_regression: ""
ff_mode: false
ff_stage_history: []
active_requirements: []
```

### Test 1 对比：清洗前 scaffold_v2/.workflow/state/runtime.yaml（污染）

```yaml
current_requirement: "req-25"
stage: "done"
conversation_mode: "open"
locked_requirement: ""
locked_stage: ""
current_regression: ""
ff_mode: true
ff_stage_history: []
active_requirements:
  - req-25
```

### Test 8：harness requirement "smoke" 输出

```
Requirement workspace: /private/tmp/harness-bugfix4-20260419-120634/artifacts/main/requirements/req-01-smoke
- created /private/tmp/harness-bugfix4-20260419-120634/artifacts/main/requirements/req-01-smoke/requirement.md
- created .workflow/state/requirements/req-01-smoke.yaml
```

执行后 runtime.yaml：
```yaml
current_requirement: "req-01"
stage: "requirement_review"
conversation_mode: "open"
locked_requirement: ""
locked_stage: ""
current_regression: ""
ff_mode: false
ff_stage_history: []
active_requirements:
  - req-01
```

### Test 9：主仓 harness status

```
current_requirement: bugfix-4
stage: regression
conversation_mode: open
locked_requirement: (none)
locked_stage: (none)
current_regression: (none)
active_requirements: req-27, req-25, bugfix-3, bugfix-4
```

## 补充验证

- `py_compile src/harness_workflow/workflow_helpers.py`：OK
- `pytest src/harness_workflow/assets/skill/tests/`：1 passed, 14 skipped（无回归）
- `_scaffold_v2_file_contents()` 直接调用：返回 72 个文件键；无 `req-25` 泄漏；runtime 字段/action-log 内容干净

## 清洗统计对比

| 位置 | 清洗前 | 清洗后 |
|------|--------|--------|
| `scaffold_v2/` 总计 | 903 files | 72 files |
| `scaffold_v2/.workflow/flow/archive/` | 383 files | 目录已删 |
| `scaffold_v2/.workflow/archive/` | 275 files | 空目录 |
| `scaffold_v2/.workflow/state/sessions/` | 60 files | 空目录 |
| `scaffold_v2/.workflow/context/backup/` | 57 files | 空目录 |
| `scaffold_v2/.workflow/flow/requirements/` | 29 files | 空目录 |
| `scaffold_v2/.workflow/state/requirements/` | 20 files | 空目录 |
| `scaffold_v2/.workflow/flow/suggestions/archive/` | 7 files | 空目录 |

## 运行时代码是否被修改

未修改任何 Python 代码。仅静态清洗 `src/harness_workflow/assets/scaffold_v2/` 下污染文件/目录，重置 `runtime.yaml`，清空 `action-log.md`。`OPTIONAL_EMPTY_DIRS` 保持原样（保留对老仓 legacy archive 的剪空能力）。
