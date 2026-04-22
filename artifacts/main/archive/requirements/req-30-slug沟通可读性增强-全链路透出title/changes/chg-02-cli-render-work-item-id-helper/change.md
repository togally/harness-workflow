# Change

## 1. Title

chg-02（CLI 渲染 — render_work_item_id helper）：统一 CLI stdout 打印工作项时"id + title"双字段渲染

## 2. Background

源自 req-30 方案 B 的 **L2 层目标**（Harness CLI stdout 渲染）与 **AC-03 / AC-04**：

- 现状：`workflow_status`（`src/harness_workflow/workflow_helpers.py:5060`）只在检测到匹配 state yaml 时才在独立行打印 `requirement_title`，且其他命令（`workflow_next` / `workflow_fast_forward` / `list_suggestions`）在打印 id（如 `current_requirement: req-30`、`Workflow advanced to executing`、`sug-05 [pending]`）时完全不带 title。
- 对人读者看到 `current_requirement: req-30` 只能反查目录或 yaml 才能知道 req-30 到底是什么需求。方案 B 要求 CLI 主动在**同行**上附带 title，格式如 `current_requirement: req-30（slug 沟通可读性增强：全链路透出 title）`。
- 缺少统一渲染入口：每个命令自己拼接会漂移；需要一个单点 helper `render_work_item_id` 兜住所有格式、降级策略。

## 3. Goal

为 CLI 打印层提供**唯一的 id→显示字符串转换 helper**，覆盖主流命令输出，实现"一次改对、处处一致"：

- 新增 `render_work_item_id(work_item_id, runtime, root) -> str` helper（放在 `workflow_helpers.py`），输出 `{id}（{title}）`；title 缺失时降级为 `{id} (no title)`，绝不抛错。
- 覆盖改造至少 4 条命令：`harness status` / `harness next` / `harness ff` / `harness suggest --list`（以及上述命令内部所有渲染 id 的 print 点）。
- 至少 2 条单元测试：正常 title 路径 + 缺失 title 降级路径。

## 4. Requirement

- `req-30`

## 5. Scope

### 5.1 In scope

- **`src/harness_workflow/workflow_helpers.py`**：
  - 新增 `def render_work_item_id(work_item_id: str, *, runtime: dict | None = None, root: Path | None = None) -> str:`
    - 优先用 `runtime` 的 `*_title` 缓存（chg-01 落地的字段）；
    - 若 runtime 缓存为空或未传入，fallback 到 `_resolve_title_for_id(root, work_item_id)`（chg-01 新增的 helper）；
    - 都拿不到 → 返回 `f"{id} (no title)"` 格式；
    - `work_item_id` 本身为空 → 返回 `"(none)"`（保持与现有 `workflow_status` 空值渲染一致）。
  - 改造 `workflow_status`（约第 5060-5096 行）：
    - `current_requirement` / `locked_requirement` / `current_regression` 的 print 行改为 `print(f"current_requirement: {render_work_item_id(...)}")`。
    - `active_requirements` 的 `rendered_active` 每项走 `render_work_item_id`。
    - 原有的 `requirement_title` 独立行保留（人类可读性加分），但 id 行也带 title（同行冗余不会误导）。
  - 改造 `workflow_next`（约 5099-5161 行）：
    - `print(f"Workflow advanced to {next_stage}")` 保持不变；但如果有"涉及 id"的输出（如未来扩展），走 helper。
    - 以及 `extract_suggestions_from_done_report` 附近若打印 id 同步改造。
  - 改造 `workflow_fast_forward`（`ff` 命令主循环）：打印当前 `operation_target` / 推进前后 stage 时，走 helper。
  - 改造 `list_suggestions`（约 3240-3261 行）：每条 `  {sid} [{status}] (...) {summary}` 的 `sid` 用 helper 渲染（sug-NN 无 state/requirements/*.yaml，读 sug 文件 frontmatter 的 `title`；本 change 扩展 `_resolve_title_for_id` 支持 `sug-*` 前缀回退到 sug 文件）。
  - 辅助：`_render_id_list(ids, runtime, root) -> str`：批量版本，接收 ids list，返回逗号分隔的带 title 渲染字符串（`workflow_status` 的 `active_requirements` 会用）。
- **单元测试**：新增 `tests/test_render_work_item_id.py`：
  - `test_render_with_runtime_cache`：`runtime["current_requirement_title"] = "slug 沟通可读性"` 时，返回 `req-30（slug 沟通可读性）`。
  - `test_render_with_state_fallback`：runtime 缓存为空，state/requirements/*.yaml 有 title → 返回带 title 的格式。
  - `test_render_missing_title_fallback`：runtime + state 都拿不到 → 返回 `req-404 (no title)`，不抛错。
  - `test_render_empty_id_returns_none_placeholder`：`work_item_id=""` → 返回 `"(none)"`。
  - `test_render_suggestion_reads_frontmatter_title`：sug-01 frontmatter 有 `title:` → 返回 `sug-01（...）`。
  - `test_workflow_status_prints_title`：集成级，fixture 仓库 → `workflow_status` 的 stdout 包含 `current_requirement: req-30（...）`。

### 5.2 Out of scope

- state schema（`*_title` 字段）由 chg-01 提供，本 change 只**读**这些字段。
- 角色文件 / `stage-role.md` 契约更新由 chg-03 负责。
- 归档 `_meta.yaml` 由 chg-04 可选负责。
- 不改 CLI 命令行参数结构；不新增命令；不支持用 title 做反向查 id（req-30 §4.2 明确排除方案 C）。
- 不改 `print` 的 locale / i18n（req-30 §4.2 排除 i18n）。
- 不改 action-log.md 的写入格式（由 chg-03 的角色契约在写入侧约束）。

## 6. Definition of Done（≥3 条）

1. **DoD-1**：`harness status` 的 stdout 第一行形如 `current_requirement: req-30（slug 沟通可读性增强：全链路透出 title）`，且 `active_requirements:` 行每个 id 带 title。
2. **DoD-2**：`render_work_item_id` 在 runtime + state 均无 title 时不抛错，返回 `{id} (no title)` 或 `(none)`。
3. **DoD-3**：新增 6 条单元测试（见 Scope）全部通过；现有 180+ 测试零回归。
4. **DoD-4**：`harness suggest --list` 的输出每行 `sid` 带 title（读自 sug 文件 frontmatter 的 `title` 字段；对无 frontmatter 的 legacy sug 显式降级为 `(no title)`，不阻断命令）。

## 7. 关联 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-03 | CLI 默认带 title（status / next / ff / suggest --list） | Step 2-5 改造 4 条命令 + 单测 `test_workflow_status_prints_title` |
| AC-04 | title 缺失降级 `(no title)` 不报错 | Step 1 helper 设计 + 单测 `test_render_missing_title_fallback` |
| AC-06（部分） | 写入路径统一（此处是读取路径统一的对称） | Step 1 的"runtime 缓存优先、state fallback"读取策略 |
| AC-09 | 至少 2 单测 + 1 smoke | Step 6 的 6 条单测（含 smoke 级 `test_workflow_status_prints_title`） |

## 8. 依赖 / 顺序

- **前置**：chg-01（state schema）。本 change 的 `render_work_item_id` 优先读 `runtime["current_requirement_title"]`，该字段由 chg-01 提供；chg-01 未落地时，本 change 的 helper 仍可工作（fallback 到 state yaml 或 `(no title)`），但覆盖率会退化——**强烈建议 chg-01 先落地再做 chg-02**。
- **本 change 不依赖 chg-03 / chg-04**。
- 执行顺序：chg-01 → **chg-02** → chg-03 → chg-04（可选）。

## 9. 风险与缓解

- **R1 覆盖遗漏**：`workflow_helpers.py` 中有大量 `print(f"... {some_id} ...")` 散点（grep `print.*req-\|print.*bugfix-\|print.*chg-\|print.*sug-` 可定位），批量改造可能遗漏。
  - **缓解**：executing 阶段用 grep 列清单，逐点改造；在 `test_workflow_status_prints_title` 等 smoke 测试覆盖关键命令的 stdout；非关键散点（如内部 debug 打印）允许延后处理。
- **R2 sug-* 无 state yaml，读 frontmatter 可能失败**：sug 文件 frontmatter 当前 (req-28 / chg-01 约定) 含 `id` / `created_at` / `status`，但**不一定有 `title`**；render 时拿不到 title → 走降级但显示 `(no title)` 可能对 `harness suggest --list` 输出造成"大部分都是 (no title)"的观感劣化。
  - **缓解**：本 change 中 `render_work_item_id` 对 sug 的 fallback 顺序为：frontmatter.title → 首行 body（前 40 字符截断） → `(no title)`；这样对已有 sug 文件也能渲染出可读标题，不需要回填 frontmatter。
- **R3 性能**：每次 `workflow_status` 都遍历 `state/requirements/*.yaml` 做 title lookup，在 active_requirements 多的仓库下有 O(n·m) 开销。
  - **缓解**：`render_work_item_id` 优先读 runtime 缓存（O(1)）；state fallback 只在 runtime 未命中时发生；实测可接受（当前 state/requirements 文件数 <30）；不做缓存优化。
- **R4 regressions 的 title 源**：`current_regression` 是 `reg-NN`，无独立 state yaml，title 需从父 requirement 的 regression 目录 / 产物文件读取。
  - **缓解**：本 change 对 `reg-*` id 的渲染暂时降级为 `reg-NN (regression)`（不显示 title，但不抛错）；真正的 regression title 渲染作为后续 sug 登记（不阻塞 req-30）。
