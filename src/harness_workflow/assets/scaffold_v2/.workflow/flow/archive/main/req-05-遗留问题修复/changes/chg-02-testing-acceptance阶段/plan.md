# Plan: WORKFLOW_SEQUENCE 增加 testing/acceptance 阶段

## 执行步骤

### Step 1: 修改 WORKFLOW_SEQUENCE

文件：`src/harness_workflow/core.py`，约第 75-82 行

将：
```python
WORKFLOW_SEQUENCE = [
    "requirement_review",
    "changes_review",
    "plan_review",
    "ready_for_execution",
    "executing",
    "done",
]
```

改为：
```python
WORKFLOW_SEQUENCE = [
    "requirement_review",
    "changes_review",
    "plan_review",
    "ready_for_execution",
    "executing",
    "testing",
    "acceptance",
    "done",
]
```

### Step 2: 检查 workflow_next() 逻辑

文件：`src/harness_workflow/core.py`，约第 3287-3337 行

`workflow_next()` 使用 `WORKFLOW_SEQUENCE.index()` + 1 推进，新增阶段会自动被包含在流转路径中。需检查：
- `ready_for_execution` 的 `--execute` 特殊逻辑不受影响（保持不变）
- `done` 的终止判断不受影响（保持不变）
- 无其他硬编码跳过 testing/acceptance 的逻辑

### Step 3: 检查其他引用 WORKFLOW_SEQUENCE 的代码

搜索 `core.py` 中所有引用 `WORKFLOW_SEQUENCE` 的位置，确认无硬编码 `executing` -> `done` 的跳转。

### Step 4: 验证

- `harness next`（executing 状态）→ 进入 testing
- `harness next`（testing 状态）→ 进入 acceptance
- `harness next`（acceptance 状态）→ 进入 done

## 产物

- `src/harness_workflow/core.py`（修改）

## 风险评估

中风险：影响核心流转逻辑，但变更范围可控（1 个常量修改），有明确验证路径
