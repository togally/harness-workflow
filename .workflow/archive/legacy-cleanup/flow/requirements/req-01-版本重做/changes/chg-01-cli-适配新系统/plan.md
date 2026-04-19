# Plan: chg-01 CLI 适配新系统

## 决策前置

- **格式**：CLI 写出的所有 state 文件统一用 JSON 格式（JSON 是合法 YAML，`json.loads()` 不变）
- **version 命令**：保留为 `requirement` 的别名，降低测试迁移成本
- **regression 目录**：维持旧版独立 workspace（挂在 requirement 下而非 version 下），即 `flow/requirements/{req_id}/regressions/{reg_id}/`

## 变更文件清单

| 路径 | 变更类型 | 说明 |
|------|----------|------|
| `.claude/skills/harness/scripts/harness.py` | 重构 | 路径常量、数据模型、全部命令函数适配新系统 |
| `.claude/skills/harness/tests/test_harness_cli.py` | 重构 | 断言路径、字段名、命令序列对齐新系统 |
| `.claude/skills/harness/assets/templates/` | 新建（恢复目录） | 恢复被删除的模板目录，内容适配新路径 |

## 执行步骤

### Step 1 — 修改 harness.py 常量和数据结构

```python
# 旧
WORKFLOW_RUNTIME_PATH = Path("workflow") / "context" / "rules" / "workflow-runtime.yaml"
DEFAULT_CONFIG = {"language": DEFAULT_LANGUAGE, "current_version": ""}

# 新
WORKFLOW_RUNTIME_PATH = Path("workflow") / "state" / "runtime.yaml"
DEFAULT_CONFIG = {"language": DEFAULT_LANGUAGE}  # current_requirement 只存 runtime
```

新 DEFAULT_RUNTIME：
```python
DEFAULT_RUNTIME = {
    "current_requirement": "",
    "stage": "",
    "conversation_mode": "open",
    "locked_requirement": "",
    "locked_stage": "",
    "current_regression": "",
    "active_requirements": [],
}
```

删除 `DEFAULT_VERSION_META`，引入：
```python
DEFAULT_REQUIREMENT_STATE = {
    "req_id": "",
    "title": "",
    "stage": "requirement_review",
    "status": "in_progress",
    "created": "",
    "description": "",
}
```

新 stage 序列：
```python
WORKFLOW_SEQUENCE = [
    "requirement_review",
    "planning",
    "executing",
    "testing",
    "acceptance",
    "done",
]
```

### Step 2 — 更新路径解析和 IO 函数

- `WORKFLOW_RUNTIME_PATH` 已改，`load_runtime()` / `save_runtime()` 使用新字段
- `load_version_meta()` → `load_requirement_state()`：读 `workflow/state/requirements/` 下匹配文件
- `save_version_meta()` → `save_requirement_state()`：写同目录
- `_required_dirs()`：新增 `workflow/flow/requirements`、`workflow/flow/archive`、`workflow/state/requirements`、`workflow/state/sessions`；删除 `workflow/versions/active`
- `list_existing_versions()` → `list_active_requirements()`：扫描 `flow/requirements/` 目录
- `resolve_requirement_layout()`：返回 `{requirement_dir, changes_dir}`（不再有 version 层）

### Step 3 — 重构命令函数

| 命令 | 改动要点 |
|------|---------|
| `init` | 使用新 `_required_dirs()`，runtime 写新 DEFAULT_RUNTIME |
| `version` | 别名 → 内部调用 `create_requirement()` |
| `requirement` | 路径改为 `flow/requirements/{req_id}/`，state 写 `state/requirements/{req_id}.json`，req_id 自动递增 `req-{nn}-{slug}` |
| `change` | 路径改为 `flow/requirements/{req_id}/changes/{chg_id}/`，chg_id 自动递增 `chg-{nn}-{slug}` |
| `plan` | 路径跟随 change 目录 |
| `next` | 使用新 WORKFLOW_SEQUENCE；读/写 runtime `stage` 字段 |
| `ff` | 快进目标改为 `executing` |
| `enter`/`exit` | `locked_version` → `locked_requirement`；删除 `locked_artifact_kind`/`locked_artifact_id` |
| `status` | 输出新字段名；删除旧版 version 相关字段 |
| `use`/`active` | 写 `current_requirement` |
| `archive` | 路径：`flow/requirements/` → `flow/archive/[version]/` |
| `regression` | workspace 路径：`flow/requirements/{req_id}/regressions/{reg_id}/` |
| `rename` | 路径跟随新目录规范 |
| `update` | 扫描 `state/requirements/` 和 `flow/requirements/` 修复漂移 |

关键：`apply_stage_transition()` 完全重写，使用新 6-stage 序列，更新所有 `suggested_skill`、`assistant_prompt`、`next_action` 文案。

### Step 4 — 恢复 assets/templates/

参照 `_managed_file_contents()` 函数中 `render_template()` 调用清单，逐一创建或更新 .tmpl 文件：
- 路径引用：`workflow/context/rules/workflow-runtime.yaml` → `workflow/state/runtime.yaml`
- 路径引用：`workflow/versions/active/{version}/` → `workflow/flow/requirements/`
- 字段引用：`current_version` → `current_requirement`
- 命令引用：`harness active` → `harness use`

### Step 5 — 重构 test_harness_cli.py

辅助方法：
- `read_runtime()`：路径改为 `workflow/state/runtime.yaml`
- `read_version_meta()` → `read_requirement_state()`：路径改为 `state/requirements/`

各测试更新方向（保留全部 15 个用例，均修改断言）：
- 路径：`workflow/versions/active/{v}/` → `workflow/flow/requirements/{req_id}/`
- 字段：`current_version` → `current_requirement`；`locked_version` → `locked_requirement`
- Stage 名：`changes_review`/`plan_review`/`ready_for_execution` → `planning`/`executing`
- `version` 命令调用保留（别名），但断言改为检查 requirement 路径

### Step 6 — 全量测试验证

```bash
python3 tests/test_harness_cli.py -v
```
15 个用例全部通过为完成标准。

## 风险点

1. `apply_stage_transition()` 全量重写，文案 + 逻辑都变，需逐 stage 对照 roles/*.md 核对
2. `render_agent_command()` 内约 200 行硬编码旧路径字符串，遗漏替换测试不会报错
3. `repair_identifier_drift()` 约 170 行，三层结构变两层，边界条件多
4. regression workspace 路径需在 create_regression() 和测试中保持一致
