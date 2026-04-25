# Change Plan — chg-05（done 交付总结扩 §效率与成本 + Step 6 聚合）

## 1. Development Steps

### Step 1: 读取 done.md + `record_subagent_usage` 实际 yaml 格式

- 读取 `.workflow/context/roles/done.md` 全文，定位 "交付总结最小字段模板" 与 "SOP Step 6" 两段；
- 读取 `src/harness_workflow/workflow_helpers.py` 中 `record_subagent_usage` 函数体，记录写入 yaml 的字段（预期：`role` / `model` / `input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens` / `total_tokens` / `tool_uses` / `duration_ms` / `req_id` / `stage` / `chg_id` / `reg_id` / `timestamp`）；
- 读取 `.workflow/state/requirements/req-40/...` 或其他既有 req yaml 样本，确认 `stage_timestamps` 字段结构（预期：list of `{stage, entered_at}` 或 dict）；
- 产出字段清单到 chg-05 session-memory.md。

### Step 2: 在 done.md 交付总结模板新增 §效率与成本段

- 定位现有最小字段模板（如 `## 目标 / 验证 / 风险` 等段结构）；
- 在模板末尾紧贴添加：

```markdown
## 效率与成本

### 总耗时

- `{duration_s} s`（约 `{human_readable}`，如 20 分钟）

### 总 token

| input | output | cache_read | cache_creation | total |
|-------|--------|------------|----------------|-------|
| ...   | ...    | ...        | ...            | ...   |

### 各阶段耗时分布

| stage | entered_at | duration_s |
|-------|-----------|-----------|
| ...   | ...       | ...       |

### 各阶段 token 分布

| role | model | total_tokens | tool_uses |
|------|-------|-------------|-----------|
| ...  | ...   | ...         | ...       |
```

- 段头注释："禁止编造；若 usage-log 为空则标 `⚠️ 无数据`，不得回填虚构值"；
- 字段顺序固定：总耗时 → 总 token → 各阶段耗时 → 各阶段 token；注释锁死顺序（"字段顺序不得变更，变更须走新 req"）。

### Step 3: 在 done.md SOP Step 6 加聚合逻辑陈述

- 定位现有 SOP Step 6（done 角色六层回顾 / 交付总结产出步骤）；
- 新增子步骤："6.x 聚合效率与成本数据：
  1. 读取 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml`（含若干 subagent_usage entries）；
  2. 读取 req yaml `stage_timestamps`；
  3. 按 stage 时序聚合耗时（duration_s = next_stage.entered_at - this_stage.entered_at）；
  4. 按 role × model 聚合 token（sum input/output/cache_read/total + count tool_uses）；
  5. 写入交付总结 §效率与成本四子字段；
  6. 若任一数据源缺失（usage-log.yaml 不存在或 entries 为空），对应子字段标 `⚠️ 无数据`，禁止编造。"；
- 删除原 `召唤 usage-reporter` / `生成耗时与用量报告` 残留陈述（若存在）。

### Step 4: 去路径化 `→ artifacts/`（与 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）配合，本 chg 只改 §效率与成本 + Step 6 相关路径）

- 若 done.md 现有路径引用 `→ artifacts/{branch}/...交付总结.md` 已由 chg-04 处理，本 chg 跳过；
- 若有新引用 `usage-log.yaml` 路径，统一写作 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml`（符合 chg-01（repository-layout 契约底座）契约）；
- 不产出独立"对人 brief"（本 req 已废）。

### Step 5: 同步 scaffold_v2 mirror

- `cp .workflow/context/roles/done.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`；
- `diff -q` 零输出验证。

### Step 6: 新增 pytest 用例

- 新增 `tests/test_done_subagent.py`（或扩既有）：
  - `test_done_delivery_summary_efficiency_section`：
    1. tempdir fixture 建 `.workflow/flow/requirements/req-99-smoke/usage-log.yaml`，含 ≥ 2 条 subagent_usage entries（不同 role + model + stage），用 `record_subagent_usage` 真实写入避免手写格式漂移；
    2. req yaml 含 ≥ 3 stage_timestamps；
    3. 调 done 聚合函数（或模拟 done subagent 执行路径；若 done.md 逻辑仅为文档，用"主 agent 代跑聚合"函数 stub）；
    4. 断言产出的 `交付总结.md` 内 §效率与成本 四子字段齐全、表格行数与 mock 源一致、总 token 数值 = entries 求和；
  - `test_done_delivery_summary_empty_usage_log`：usage-log.yaml 为空 → 四子字段标 `⚠️ 无数据`；
  - `test_done_delivery_summary_field_order_fixed`：解析产出文档字段顺序，断言 `总耗时 → 总 token → 各阶段耗时 → 各阶段 token` 顺序稳定；
- pytest helper：若 done.md 仅作为 agent 文档使用，新增一个轻量 Python 聚合 helper（如 `done_efficiency_aggregate(root, req_id) -> dict`）给测试直接调，避免依赖 LLM 触发。

### Step 7: 自检 + 交接

- `grep -q "效率与成本" .workflow/context/roles/done.md` PASS；
- `grep -q "usage-log.yaml" .workflow/context/roles/done.md` PASS；
- `grep -cE "总耗时|总 token|各阶段耗时分布|各阶段 token 分布" .workflow/context/roles/done.md` ≥ 4；
- `diff -q .workflow/context/roles/done.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` 无输出；
- `pytest tests/ -k "test_done_delivery_summary" -v` 三用例全 PASS；
- `pytest tests/` 全量绿；
- 更新 chg-05 session-memory.md。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -q "## 效率与成本" .workflow/context/roles/done.md`
- `grep -q "usage-log.yaml" .workflow/context/roles/done.md`
- `[ $(grep -cE "^### (总耗时|总 token|各阶段耗时分布|各阶段 token 分布)" .workflow/context/roles/done.md) -ge 4 ]`
- `diff -q .workflow/context/roles/done.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`（零输出）
- `pytest tests/ -k "test_done_delivery_summary_efficiency_section" -v`（PASS）
- `pytest tests/ -k "test_done_delivery_summary_empty_usage_log" -v`（PASS）
- `pytest tests/ -k "test_done_delivery_summary_field_order_fixed" -v`（PASS）
- `pytest tests/`（全量绿）

### 2.2 Manual smoke / integration verification

- 人工抽读 done.md §效率与成本段，确认四子字段 + 表头 + "禁止编造"注释齐全；
- 人工抽读 done.md SOP Step 6 子步骤，确认聚合逻辑陈述清晰（读源 → 聚合 → 写入 → 缺数据降级）；
- 人工跑 `awk '/^### (总耗时|总 token|各阶段耗时分布|各阶段 token 分布)/{print NR,$0}' .workflow/context/roles/done.md` 输出四行，顺序锁定；
- dogfood 验证由 chg-07（dogfood 活证 + scaffold_v2 mirror 收口）端到端跑。

### 2.3 AC Mapping

- AC-10（done.md Step 6 聚合陈述） → Step 3 + 2.1 grep；
- AC-11（模板扩展四子字段顺序） → Step 2 + 2.1 grep + 字段顺序 pytest；
- AC-13 (d) 起点 → Step 6 pytest + chg-07 dogfood 端到端；
- AC-15（mirror diff 归零） → Step 5 + 2.1 diff；
- AC-06（回归不破坏） → 2.1 pytest 全量绿。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（repository-layout 契约底座）+ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）；chg-04 先行确保"召唤 usage-reporter"残留已清；
- **可并行邻居**：chg-06（harness-manager Step 4 派发硬门禁）可与本 chg 并行（都依赖 chg-04 完成）；
- **后置依赖**：chg-07（dogfood + scaffold_v2 mirror 收口）跑 dogfood §效率与成本段从真实 usage-log 聚合；
- **本 chg 内部顺序**：Step 1 读取 → Step 2 模板扩段 → Step 3 SOP Step 6 陈述 → Step 4 路径复查 → Step 5 mirror → Step 6 pytest → Step 7 自检；强制串行。
