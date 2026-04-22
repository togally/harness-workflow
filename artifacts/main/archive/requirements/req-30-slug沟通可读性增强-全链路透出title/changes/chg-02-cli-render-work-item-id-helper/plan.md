# Change Plan

## 1. Development Steps

### Step 1: 新增 `render_work_item_id` helper

- **操作意图**：把"id → 显示字符串"的转换集中到单一 helper，所有命令走同一入口。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（建议放在 `load_requirement_runtime` / `_resolve_title_for_id` 附近，便于模块内引用）。
- **关键代码思路**：
  - 签名：`def render_work_item_id(work_item_id: str, *, runtime: dict | None = None, root: Path | None = None) -> str:`
  - 空值：`work_item_id.strip() == ""` → 返回 `"(none)"`（保持和现有 `workflow_status` 的行为一致）。
  - 标准化 id（去前后空白）。
  - 查 title 的优先级：
    1. **runtime 缓存**：按 id 前缀匹配 runtime 对应 `*_title` 字段（`req-*` → `current_requirement_title` / `locked_requirement_title`；`reg-*` → `current_regression_title`；`bugfix-*` → 若 runtime 已扩展 `current_bugfix_title` 则读，否则跳过；`sug-*` → 无 runtime 缓存）。
    2. **state fallback**：调 `_resolve_title_for_id(root, work_item_id)`（chg-01 提供；本 change 只消费）。
    3. **sug 特殊 fallback**：对 `sug-*` 前缀，读 `.workflow/flow/suggestions/sug-NN-*.md` 或 `archive/` 下对应文件，解析 frontmatter `title:`；解析不到则截取 body 首行前 40 字符。
  - 拼接：`f"{id}（{title}）"`；title 最终为空则 `f"{id} (no title)"`。
- **验证方式**：单测 Step 6 覆盖。

### Step 2: 改造 `workflow_status`

- **操作意图**：让 `harness status` 的输出 id 行带 title，且保留原有 `requirement_title` 独立行（用户读单行即可知全貌）。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py:5060-5096`。
- **关键代码思路**：
  - `print(f"current_requirement: {render_work_item_id(current_requirement, runtime=runtime, root=root)}")`。
  - 同理改造 `locked_requirement` / `current_regression` 行。
  - `active_requirements` 行：用 `_render_id_list(active_requirements, runtime, root)` 辅助 helper 逐项渲染，输出 `req-28（...）, req-29（...）, req-30（...）`。
  - 空值保持显示 `(none)`。
- **验证方式**：
  - smoke `test_workflow_status_prints_title`：fixture 仓库 → `capsys` 捕获 stdout → 断言含 `req-30（slug` 子串。
  - 手工 `harness status` 输出肉眼验证。

### Step 3: 改造 `workflow_next`

- **操作意图**：stage 推进输出与 feedback event 保持一致；日志式输出带 title。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py:5099-5161`。
- **关键代码思路**：
  - `print(f"Workflow advanced to {next_stage}")` 后如果有 "for req-30" 子句，走 helper；若无则保持。
  - `record_feedback_event` 的 payload 仍只记 id（后端机器消费），不改。
  - done 阶段的 `Review context/experience/stage/...` 提示保持不变（不涉及 id）。
- **验证方式**：
  - 现有 `tests/test_next_writeback.py` 零回归。
  - 新增集成级 `test_workflow_next_preserves_title_in_runtime`（保险丝，确认 stage 推进后 runtime.yaml 的 `*_title` 仍在——这个主要是 chg-01 的保证，这里作为 chg-02 与 chg-01 的集成 smoke）。

### Step 4: 改造 `workflow_fast_forward`（ff 命令）

- **操作意图**：ff 自动推进链路打印的 stage / id 都带 title。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py:5164+`（`workflow_fast_forward` 函数）。
- **关键代码思路**：
  - 定位 ff 循环中所有 `print(f"... {operation_target} ...")` 或 `print(f"... {req_id} ...")` 的行，用 `render_work_item_id` 包装。
  - `ff --auto` 的决策汇总输出由 req-29 / chg-03 产出的 `render_decision_summary` 负责；本 change 只负责 ff 主循环的 id 打印。
- **验证方式**：
  - 现有 `tests/test_ff_auto.py` / `test_smoke_req29.py` 零回归。
  - 手工 `harness ff` smoke：stdout 多处 id 带 title。

### Step 5: 改造 `list_suggestions`

- **操作意图**：`harness suggest --list` 输出每行 sug-NN 带 title。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py:3240-3261`。
- **关键代码思路**：
  - 改 `print(f"  {sid} [{status}] ({created}) {summary}")`，其中 `sid` 用 `render_work_item_id(sid, runtime=None, root=root)` 渲染；或直接在 summary 之前插入 helper 的输出。
  - 为了不改变现有列宽感观：建议格式 `render_work_item_id(...)` → `sug-01（title）[pending] (2026-04-21) body summary`；把原来的 `sid` 位置扩展为"id+title"，其余字段不变。
- **验证方式**：
  - 现有 `tests/test_suggest_cli.py` 部分用例涉及 stdout，需同步更新断言（断言包含 `sug-01（` 而非裸 `sug-01`）。
  - 新增用例 `test_list_suggestions_prints_title_fallback`：legacy sug 无 title → 输出 `sug-XX (no title)`。

### Step 6: 编写单元测试

- **操作意图**：把 render helper 的 5 种分支和 4 条命令的渲染行为固化为回归。
- **涉及文件**：`tests/test_render_work_item_id.py`（新增）。
- **关键代码思路**：
  - `test_render_with_runtime_cache`：构造 runtime dict → 断言输出 `req-30（...）`。
  - `test_render_with_state_fallback`：构造 fixture `state/requirements/req-99-x.yaml` 有 title → 断言输出带 title。
  - `test_render_missing_title_fallback`：runtime 空 + state 不存在 → 断言输出 `req-404 (no title)`。
  - `test_render_empty_id_returns_none_placeholder`：断言返回 `"(none)"`。
  - `test_render_suggestion_reads_frontmatter_title`：fixture `sug-99-x.md` frontmatter 含 `title:` → 断言输出带 title。
  - `test_workflow_status_prints_title`：fixture 仓库 → capsys 断言 stdout 含 `current_requirement: req-30（`。
- **验证方式**：`pytest tests/test_render_work_item_id.py -v` 全绿。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_render_work_item_id.py -v`：6 条新用例全绿。
- `pytest tests/test_suggest_cli.py -v`：原有用例更新断言后仍绿。
- `pytest` 全量：180+ 测试零回归。
- `grep -n "print.*req-\|print.*bugfix-\|print.*sug-\|print.*reg-" src/harness_workflow/workflow_helpers.py`：列出所有 id 打印点，对照改造清单逐行检查。

### 2.2 Manual smoke verification

- `harness status` → stdout 含 `current_requirement: req-30（slug 沟通可读性增强：全链路透出 title）`；`active_requirements:` 行每项都有 title。
- `harness next` → 现有行为不变，无副作用。
- `harness ff` → 循环打印的 stage + id 带 title。
- `harness suggest --list` → 每行 sug-NN 带 title 或 `(no title)`。
- 异常路径：`harness status` 在 runtime.yaml `current_requirement_title` 被手动清空时，能 fallback 到 state yaml 读 title（验证 R1 缓存漂移）。

### 2.3 AC Mapping

- AC-03 → Step 2 + Step 3 + Step 4 + Step 5 + Step 6 的 `test_workflow_status_prints_title`。
- AC-04 → Step 1 的降级分支 + Step 6 的 `test_render_missing_title_fallback`。
- AC-06（部分）→ Step 1 的 "runtime 优先 + state fallback" 读取策略（写入统一由 chg-01 保证）。
- AC-09 → Step 6 的 6 条单测（含 1 条 smoke）。

## 3. 执行依赖顺序

1. **前置**：chg-01 必须已落地（runtime 有 `*_title` 字段 + `_resolve_title_for_id` helper 可用）。
2. Step 1（helper）先落地；后续 Step 2-5 的任何改造都 import 这个 helper。
3. Step 2 / 3 / 4 / 5 可并行（不同命令函数），各自独立提交。
4. Step 6 的单测在 Step 1 落地后即可开始编写，其他 Step 跟进补充断言。

## 4. 回滚策略

- **粒度**：每个 Step 一个 commit；Step 2-5 各命令的改造可单独 revert 而不影响其他命令。
- **回滚触发**：
  - `pytest` 回归（特别是 `test_suggest_cli.py`）：若是断言不兼容，更新断言；若是行为回归，revert Step 5。
  - 用户反馈 stdout 过长 / 换行异常：将 `render_work_item_id` 的 title 部分加 30 字符截断（而不是完全 revert）。
  - ff 循环性能异常（R3 变种）：在 `render_work_item_id` 内增加 per-call LRU cache；极端情况下 revert Step 4。
- **兜底**：所有修改都在 `workflow_helpers.py` + 新 test 文件；不改任何外部依赖；`git revert` 可完整回滚。

## 5. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | CLI 散点 print 遗漏（covered id 行未走 helper） | grep 清单 + smoke 断言 + 允许后续 sug 补充 |
| R2 | sug 文件无 `title` frontmatter，全部显示 `(no title)` | helper 多级 fallback（frontmatter.title → body 首行 → `(no title)`） |
| R3 | 频繁 state yaml 读取性能下降 | runtime 缓存优先；文件数 <30 实测可接受；不引入全局 cache（避免陈旧数据） |
| R4 | `reg-*` 无独立 title 源 | 本 change 渲染 `reg-NN (regression)` 兜底；真正 title 渲染作为后续 sug 登记 |
| R5 | 现有 `test_suggest_cli.py` 断言硬编码 `sug-01`，改造后断言失败 | Step 5 同步更新断言；在 PR description 列出更新的断言行数 |
