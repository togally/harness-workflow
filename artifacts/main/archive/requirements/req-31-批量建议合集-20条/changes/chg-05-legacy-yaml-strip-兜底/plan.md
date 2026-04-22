# Change Plan

> 父 change：chg-05（legacy yaml strip 兜底，optional）/ req-31（批量建议合集（20条））

## 1. Development Steps

### Step 1：`render_work_item_id` title 清洗（sug-23）

- **操作意图**：对 legacy yaml 脏数据的 title 字段做渲染层 strip 兜底。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::render_work_item_id`（461）。
- **关键代码思路**（伪代码）：
  ```python
  def render_work_item_id(
      work_item_id: str,
      runtime: dict | None = None,
      root: Path | None = None,
  ) -> str:
      raw_title = _lookup_title(...)  # 既有实现
      # sug-23 新增：legacy yaml strip 兜底
      if raw_title:
          title = raw_title.strip().strip("'\"").strip()
      else:
          title = ""
      if not title:
          return f"{work_item_id}（no title）"  # 或当前 fallback 行为
      return f"{work_item_id}（{title}）"
  ```
  - **注意**：`.strip("'\"")` 会去首尾的 `'` 或 `"`；外层再加 `.strip()` 是防止 `"'foo '"` 这种组合场景（引号去掉后内部仍有空格）。
  - **保留内部引号**：因 `.strip(...)` 只作用于字符串首尾，`foo's bar` 不会被误改（`'` 不在首尾）。
- **body 丢失补位**：sug-23 title "AC-04 legacy yaml 非标准空串 title 的 strip 兜底" 推断来源 = req-31 §4 AC-12 明确字符范围（`'` / `"` / 前后空格）+ req-30 chg-02 `render_work_item_id` 实现（`workflow_helpers.py:461`）+ commit `2dd9db5`（slug 清洗与截断 sug 归档）前后 state yaml 脏数据样本。
- **验证方式**：
  - 单测 5 条（见 change.md §5.1）。
  - `pytest tests/test_render_work_item_id.py -v` 全绿。
  - 手工验证：fixture state yaml `title: "'批量建议合集'"` → CLI `harness status` 输出不含外层单引号。

### Step 2：回归 + 自证

- **操作意图**：全量测试绿 + 契约 7 自证。
- **验证方式**：
  - `pytest` 全量绿（≥ 183 passed 基线不下降）。
  - 本 change 产出文档过 `harness status --lint` 得绿（依赖 chg-01）。

## 2. Verification Steps

### 2.1 单测 / 集成测清单

| 测试文件 / 用例 | 意图 | 关键断言 |
|----------------|------|---------|
| `tests/test_render_work_item_id.py::test_render_strips_single_quotes` | 单引号脏数据 | `title: "'foo'"` → render `req-XX（foo）` |
| `tests/test_render_work_item_id.py::test_render_strips_double_quotes` | 双引号脏数据 | `"foo"` → `（foo）` |
| `tests/test_render_work_item_id.py::test_render_strips_leading_trailing_whitespace` | 前后空格 | `"  foo  "` → `（foo）` |
| `tests/test_render_work_item_id.py::test_render_handles_nested_quotes_and_spaces` | 嵌套组合 | `' "foo" '` → `（foo）` |
| `tests/test_render_work_item_id.py::test_render_preserves_internal_quotes` | 内部引号保留 | `"foo's bar"` → `（foo's bar）` |

### 2.2 Manual smoke verification

- fixture `state/requirements/req-99-x.yaml` 写入 `title: "'测试脏数据'"` → `harness status` 输出的 `current_requirement` 行不含外层单引号。

### 2.3 AC Mapping

- AC-12 → Step 1 + 5 条单测。

## 3. body 丢失补位专段

| sug id | title | 推断来源 |
|--------|-------|---------|
| sug-23（AC-04 legacy yaml 非标准空串 title 的 strip 兜底） | req-31 §4 AC-12 明确字符范围 + req-30 chg-02 `render_work_item_id`（`workflow_helpers.py:461`）+ commit `2dd9db5` |

## 4. 回滚策略

- **粒度**：单 Step 一个 commit。
- **回滚触发**：
  - 若 `.strip("'\"")` 误改某个现有测试 fixture（历史上用 `"foo"` 做 title → render 结果现在变了），导致 `tests/test_render_work_item_id.py` 已有用例回归 → 分析回归用例：如果本就应该清洗（脏数据），更新断言；如果断言是故意保留引号，改实现为更保守（仅 strip 首尾空格，不 strip 引号）。
- **兜底**：修改集中在 1 个 helper + 1 个测试文件；`git revert` 单次撤销。

## 5. 执行依赖顺序

1. Step 1（实现 + 测试）。
2. Step 2（回归 + 自证）。

**前置依赖**：chg-01（契约自动化）。chg-02 / chg-03 / chg-04 无代码耦合，仅顺序依赖。

## 6. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `.strip("'\"")` 误去内部紧邻引号 | 实际 Python `.strip(chars)` 只处理首尾字符，内部不受影响；`test_render_preserves_internal_quotes` 防御 |
| R2 | 现有 `tests/test_render_work_item_id.py` fixture 中的 title 如果本就含引号（作为合法字符）→ 回归 | grep 现有测试的 fixture title 值，逐一核对是否 legacy 脏数据 vs 故意保留 |
| R3 | legacy 脏数据的其他字符（如全角引号 `""`）未覆盖 | AC-12 明确范围只含 ASCII `'` `"` 空格；其他字符另登 sug |
| R4 | 合并入 chg-03 的决策反复 | 见 change.md §11；planning 阶段建议保持独立，executing 阶段可视工作量合并 |
