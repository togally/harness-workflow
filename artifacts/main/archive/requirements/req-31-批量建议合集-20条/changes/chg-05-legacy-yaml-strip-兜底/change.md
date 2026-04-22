# Change

## 1. Title

chg-05（legacy yaml strip 兜底，optional）：`render_work_item_id` 读 state yaml title 时 strip 掉 legacy 非标准空串字符（`'` `"` 前后空格）

> 父需求：req-31（批量建议合集（20条））
>
> **optional 标注**：本 change 修改面极小（1 个 helper 函数 `.strip(...)`），可选地并入 chg-03（CLI / helper 剩余修复）。保持独立时便于回溯 sug-23；合并入 chg-03 则减少 1 次 review。决策见 §11。

## 2. Background

源自 req-31（批量建议合集（20条））§5 Split Rules 的 **chg-05 分组**（G 组杂项，1 条 sug），以及 §4 的 **AC-12**：

- **现状**：`render_work_item_id`（`workflow_helpers.py:461`）读 state yaml 的 `title` 字段时未对 legacy 非标准空串字符做兜底——历史脏数据形如 `title: "'批量建议合集'"`（yaml 字符串内层再套引号）或 `title: " 批量建议合集 "`（前后空格）会被渲染成带引号 / 空格的 title，影响对人文档可读性。
- req-30（slug 沟通可读性增强：全链路透出 title）chg-02 落地 `render_work_item_id` 时未处理此边界（因当时无脏数据样本），sug-23 由 req-30 归档阶段 2026-04-21 登记。

## 3. Goal

- `render_work_item_id` 读 title 时 strip 掉 legacy yaml 脏数据的 `'` / `"` / 前后空格；即使 state yaml 历史脏数据形如 `title: "'foo'"`、`title: " foo "`、`title: '"foo"'` 等，也能渲染出干净 title。
- 不改 state yaml 数据本身（`render_work_item_id` 是渲染层兜底，源数据另由 chg-04 `_write_archive_meta` 等入口统一清洗）。

## 4. Requirement

- req-31（批量建议合集（20条））

## 5. Scope

### 5.1 In scope

- **`src/harness_workflow/workflow_helpers.py::render_work_item_id`**（461）：
  - 在 helper 读取 title 后、返回前，对 title 做 strip：
    ```python
    title = raw_title.strip().strip("'\"").strip()
    ```
    （先去前后空格 → 去引号 → 再去可能的内部前后空格，覆盖 `" foo "` / `"'foo'"` / `' "foo" '` 等组合）
- **单元测试**：
  - `tests/test_render_work_item_id_strip.py`（新增；或合并到现有 `tests/test_render_work_item_id.py`，**优先合并**减少测试文件数）：
    - `test_render_strips_single_quotes`：state yaml `title: "'批量建议合集'"` → 渲染 `req-31（批量建议合集）`（去单引号）。
    - `test_render_strips_double_quotes`：state yaml 实际内容含 `"foo"` → 渲染 `req-XX（foo）`。
    - `test_render_strips_leading_trailing_whitespace`：state yaml `title: "  foo  "` → 渲染 `req-XX（foo）`。
    - `test_render_handles_nested_quotes_and_spaces`：state yaml `title: ' "批量建议合集" '` → 渲染 `req-XX（批量建议合集）`。
    - `test_render_preserves_internal_quotes`：state yaml `title: "foo's bar"` → 渲染 `req-XX（foo's bar）`（不去内部单引号）。

### 5.2 Out of scope

- 不改 state yaml 源数据（只在渲染层兜底）。
- 不扩展其他 helper（如 `_resolve_title_for_id`）的 strip 逻辑——只 `render_work_item_id` 作为**对人输出**的统一渲染层兜底一次。
- 不处理 yaml 反序列化的引号转义问题（`load_simple_yaml` 负责）。
- 不处理其他 render helper（如 contract 7 lint 的 title 提取）——本 change 仅 `render_work_item_id`。

## 6. 覆盖的 sug 清单（契约 7，id + title）

| sug id | title | 合入方式 |
|--------|-------|---------|
| sug-23（AC-04 legacy yaml 非标准空串 title 的 strip 兜底） | `render_work_item_id` 读 title 后 `.strip().strip("'\"").strip()` 链式清洗 |

## 7. 覆盖的 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-12 | `render_work_item_id` strip 掉 legacy yaml 脏数据的 `'` `"` 空格 + 至少 1 单测覆盖 | Step 1 + 5 条单测 |

## 8. DoD

1. **DoD-1**：`render_work_item_id` 对 legacy 脏数据（`'foo'` / `"foo"` / `" foo "` / `' "foo" '`）统一渲染出干净 title；`tests/test_render_work_item_id.py`（或新增文件）5 条新增用例全绿。
2. **DoD-2**：现有 `tests/test_render_work_item_id.py` 零回归。
3. **DoD-3**：本 change 产出文档过 `harness status --lint` 得绿（依赖 chg-01）。

## 9. 依赖 / 顺序

- **前置**：chg-01（契约自动化）——本 change 对人文档自检依赖 `harness status --lint`。
- **后置**：无。
- **内部 Step 顺序**：单 Step，直接改 + 测。

## 10. 风险与缓解

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `.strip("'\"")` 可能误去内部紧邻的引号（虽然 strip 只去首尾字符，但复杂嵌套场景需验证） | 单测用例覆盖典型 case + 边界 case；保留 `test_render_preserves_internal_quotes` 防止误去内部引号 |
| R2 | legacy yaml 脏数据可能还有其他字符（如全角引号 `""` / 中文括号 `（）`） | 本 change 只处理 ASCII `'` / `"` / 空格（AC-12 明确范围）；其他字符另登 sug |
| R3 | body 丢失：sug-23 title 明确范围（`'` `"` 空格），推断风险低 | title 已自说明；参考 req-31 §4 AC-12 原文确认 |

## 11. 合并建议（是否合并入 chg-03）

**推荐：保持独立，不合并入 chg-03**。理由：

1. **回溯清晰**：chg-05 独立存在便于 grep 追溯 sug-23 的单一改造；合并入 chg-03 后会与 hash_guard / auto-locate / id allocator 等混在一起。
2. **修改面差异**：chg-03 改 4 个文件 + 4 组测试；chg-05 只改 1 个 helper + 1 个测试文件——性质差异大，独立 commit 更清洗。
3. **风险隔离**：chg-05 仅影响渲染层（低风险），chg-03 涉及 update_repo / CLI 入口（中风险）；分开便于独立 revert。
4. **执行成本增量小**：chg-05 独立 commit 最多多 1 次 review，但可读性显著提升。

若 executing 阶段人力紧张 / 批量 commit 便利性优先，可合并；合并时：
- chg-05 Step 1 并入 chg-03 Step 5（或新 Step 5）。
- chg-05 单测并入 `tests/test_render_work_item_id.py`（本就是合并方向）。
- chg-04 的归档迁移不受影响。
- 本 change.md / plan.md 标注"已并入 chg-03"的 optional 状态，保留作为 AC-12 的追溯证据。
