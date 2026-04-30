# Plan — chg-01（trivial 通道命令骨架）

## 1. Steps（按硬序排列）

### Step 1：常量与枚举扩展（helper 层）
- 在 `src/harness_workflow/workflow_helpers.py` 新增常量 `TRIVIAL_SEQUENCE = ["trivial_define", "executing", "done"]`；
- 扩 task_type 枚举校验：`VALID_TASK_TYPES = {"req", "bugfix", "sug", "regression", "trivial"}`；
- 新增 helper `get_sequence_for_task_type(task_type) -> list[str]`，返回对应 SEQUENCE 常量；
- 单测 `tests/test_trivial_sequence_helper.py`：覆盖 5 类 task_type 各正例 + 1 反例（unknown task_type → ValueError）。

### Step 2：runtime state machine 扩展
- 扩 `validate_stage(task_type, stage)` 支持 trivial 分支；
- 扩 `get_next_stage(task_type, stage) -> str|None`：`trivial_define → executing → done → None`；
- 扩 `is_terminal_stage(task_type, stage)`：trivial 模式下 `done` 为 terminal；
- 单测 `tests/test_trivial_state_machine.py`：覆盖 3 stage 流转 + 反例（trivial 模式下出现 testing/acceptance stage → ValueError）。

### Step 3：create_trivial helper
- 新增 `create_trivial(title: str, root: Path) -> dict`：
  - 分配 task_id（沿用 `_next_req_id` 但 prefix 用 `trivial-`，或复用 req-id 编号空间——default-pick D-12 = A 复用 req-id 编号空间，避免 id 命名分裂）；
  - 生成 slug；
  - 创建目录 `.workflow/flow/requirements/{req-id}-{slug}/`；
  - 写空骨架 `requirement.md`（含 trivial 标记 frontmatter）；
  - 更新 `runtime.yaml`：task_type=trivial / current_requirement={req-id} / stage=trivial_define；
- 单测 `tests/test_create_trivial.py`：覆盖目录创建 + frontmatter 正确 + runtime.yaml 字段。

### Step 4：CLI 入口注册
- 在 `src/harness_workflow/cli.py` 注册 `trivial` 子命令：
  - argparse subparser `trivial`；
  - 位置参数 `title`；
  - choices 注册 `trivial`；
  - 调用 `create_trivial(title, root)` + stdout 输出 `已创建 trivial 任务 trivial-{id}（{title}）。stage = trivial_define。`；
- 单测 `tests/test_cli_trivial.py`：子进程调用 `harness trivial "test"` 断言 stdout 含 id+title 且 runtime.yaml 字段正确。

### Step 5：harness-manager 路由表扩展
- 编辑 `.workflow/context/roles/harness-manager.md` §3.6 路由表：
  - 加一行 `harness trivial` → analyst（trivial_define）→ executing → done 派发链；
  - 加 §3.6.X trivial 路由特殊段（briefing 注入 task_type=trivial / TRIVIAL_SEQUENCE 提示 / 跳过 testing/acceptance/planning 派发）；
- grep 自检：`grep "harness trivial" .workflow/context/roles/harness-manager.md` 命中。

### Step 6：`harness suggest --apply --trivial` flag
- 在 `cli.py` 的 `suggest --apply` 子命令加 `--trivial` flag；
- 在 `apply_suggestion(sug_id, trivial=False)` helper 加分支：trivial=True 时调 `create_trivial(sug.title)` 而非 `create_requirement`；
- 单测 `tests/test_suggest_apply_trivial.py`：覆盖 sug-NN apply --trivial 后 runtime task_type=trivial。

### Step 7：硬门禁六 / 七 / 契约 7 自检
- 所有新增 stdout / harness-manager briefing / commit message：grep `(req|chg|sug|bugfix|reg|trivial)-[0-9]+` 命中行核对 ≤ 15 字描述；
- 自我介绍模板复用既有，无需新增。

## 2. 验证

### Unit 测试
- `tests/test_trivial_sequence_helper.py`：5 用例（4 正例 task_type + 1 反例）；
- `tests/test_trivial_state_machine.py`：6 用例（3 流转 + 3 反例）；
- `tests/test_create_trivial.py`：4 用例（目录 / frontmatter / runtime / 重复 id 边界）；
- `tests/test_cli_trivial.py`：3 用例（子进程 + stdout + runtime）；
- `tests/test_suggest_apply_trivial.py`：3 用例。

### Manual 测试
- `harness trivial "test typo"` → 检查 runtime.yaml + 目录结构；
- `harness next` → 流转到 executing → done。

### AC mapping
- AC-01 → Step 4 + tests/test_cli_trivial.py；
- AC-02 → Step 1 + Step 2 + tests/test_trivial_sequence_helper.py + test_trivial_state_machine.py；
- AC-06 → Step 6 + tests/test_suggest_apply_trivial.py；
- AC-09 → Step 7 grep 自检。

## 3. 硬序约束

- Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7（线性硬序，前置失败禁止后续）；
- 本 chg 完成后才允许进入 chg-02；
- chg-02 / chg-03 / chg-04 / chg-05 全部依赖本 chg 的 TRIVIAL_SEQUENCE 常量与 task_type 枚举。

## 4. 测试用例设计

> regression_scope: full  # 改动跨核心 helper（workflow_helpers.py / cli.py 入口分发逻辑）+ runtime schema 扩展，触发 full 回归
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - src/harness_workflow/workflow_helpers.py（新增 TRIVIAL_SEQUENCE / VALID_TASK_TYPES / get_sequence_for_task_type / create_trivial / validate_stage / get_next_stage / is_terminal_stage 改写）
> - src/harness_workflow/cli.py（新增 trivial subparser + suggest --trivial flag）
> - .workflow/state/runtime.yaml（task_type 字段扩枚举）
> - .workflow/context/roles/harness-manager.md（路由表新增条目）
> - 间接波及：archive_requirement / validate_human_docs / get_artifact_dir 等所有按 task_type 分支的下游 helper

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | `get_sequence_for_task_type("trivial")` | 返回 `["trivial_define", "executing", "done"]` | AC-02 | P0 |
| TC-02 | `get_sequence_for_task_type("unknown")` | 抛 ValueError | AC-02 | P0 |
| TC-03 | `validate_stage("trivial", "trivial_define")` | True | AC-02 | P0 |
| TC-04 | `validate_stage("trivial", "testing")` | False（trivial 无 testing stage） | AC-02 | P0 |
| TC-05 | `get_next_stage("trivial", "trivial_define")` | `"executing"` | AC-02 | P0 |
| TC-06 | `get_next_stage("trivial", "done")` | None（terminal） | AC-02 | P0 |
| TC-07 | `create_trivial("修typo", tmpdir)` | 目录创建 + requirement.md frontmatter trivial=true + runtime.yaml task_type=trivial | AC-01 | P0 |
| TC-Dogfood-01 | tmpdir 子进程 `harness trivial "test"` | stdout 含 `trivial-{id}（test）` + runtime stage=trivial_define + feedback.jsonl 事件 ≥ 1 | AC-01 | P0 |
| TC-Dogfood-02 | tmpdir 子进程 `harness trivial "test" && harness next` | runtime stage 流转到 executing | AC-02 | P0 |
| TC-08 | `apply_suggestion(sug_id, trivial=True)` | runtime task_type=trivial（非 req） | AC-06 | P0 |
| TC-Dogfood-03 | tmpdir 子进程 `harness suggest --apply <sug-id> --trivial` | runtime task_type=trivial + stage=trivial_define | AC-06 | P0 |
| TC-09 | grep harness-manager.md 含 `harness trivial` 路由条目 | 命中 ≥ 1 | AC-02 | P1 |
| TC-10 | grep CLI stdout 含 `trivial-{id}（{title}）` 格式 | 不出现裸 `trivial-{id}` 形态 | AC-09 | P1 |
| TC-11（反例） | runtime.yaml task_type=trivial + stage=acceptance | validate_stage 返回 False（trivial 无 acceptance） | AC-02 | P1 |
| TC-12（反例） | `harness trivial` 不传 title | argparse 报错 + exit 2 | AC-01 | P2 |

---

## 实施结果 ✅

- ✅ Step 1：TRIVIAL_SEQUENCE + VALID_TASK_TYPES + get_sequence_for_task_type + validate_stage + get_next_stage + is_terminal_stage
- ✅ Step 2：workflow_next 新增 trivial 分支 + _FALLBACK_STAGES 加 trivial_define + _REGRESSION_ROUTE_VALID_STAGES 扩 TRIVIAL_SEQUENCE
- ✅ Step 3：create_trivial helper + apply_suggestion_as_trivial helper
- ✅ Step 4：cli.py 注册 trivial 子命令 + suggest --trivial flag
- ✅ Step 5：harness-manager.md §3.4 路由表 + §3.4.1 trivial 路由特殊段 + scaffold_v2 mirror 同步
- ✅ Step 6：suggest --apply --trivial → apply_suggestion_as_trivial（AC-06）
- ✅ Step 7：硬门禁六 / 七 自检通过
- ✅ 单测：38 tests passed（test_trivial_sequence_helper / test_trivial_state_machine / test_create_trivial / test_cli_trivial / test_suggest_apply_trivial）
