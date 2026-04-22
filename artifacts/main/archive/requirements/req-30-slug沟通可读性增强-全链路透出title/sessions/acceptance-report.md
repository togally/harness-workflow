# Acceptance Report — req-30（slug 沟通可读性增强：全链路透出 title）

> 本报告首次提到 req-30（slug 沟通可读性增强：全链路透出 title）和 chg-01（state schema — title 冗余字段）/ chg-02（CLI 渲染 — render_work_item_id helper）/ chg-03（角色契约 — id + title 硬门禁）/ chg-04（归档 meta — title 落盘，optional 延期）；后续沿用简写 id（契约 7 — AC-10 自证）。

## 验收概要

- 需求：req-30（slug 沟通可读性增强：全链路透出 title）
- 方案：方案 B（结构 + 渲染双管齐下）
- 交付时间：2026-04-21
- 交付产物：4 个 change（chg-01 / chg-02 / chg-03 必选 + chg-04 optional 延期），32 条新增单测，9 个角色文件契约 7 更新，活跃 req-30 state yaml 含 title
- 验收结论：✅ **通过**（9 AC ✅ + 1 AC 计划内延期覆盖 / 可推进 done）
- 人工判定建议：**通过**；AC-07（chg-04 归档 meta 落盘）建议在 done 阶段登 sug 池独立处理，维持 req-30 主线干净完成。

---

## 逐条 AC 核查

| AC | 需求条款 | 对应 change / 实现 | 证据 | 判定 | 备注 |
|----|---------|--------------------|------|------|------|
| AC-01 | session-memory / done-report / briefing / acceptance 报告首次引用工作项时带 title | chg-03（角色契约 — id + title 硬门禁）：stage-role.md 契约 7 + 7 stage + director briefing 模板 | `session-memory.md` 第 1/63/185 行；本 acceptance-report.md 首行；`action-log.md` grep 带 title 共 77 处；`test_chg03_title_contract.py::TestReq30SelfCertification` 2/2 绿 | ✅ | 自证样本通过 |
| AC-02 | stage-role.md / 各 stage 角色文件"汇报模板"显式写明 id + title 双字段 | chg-03 Step 1 + Step 2：stage-role.md 契约 7 + 7 stage + technical-director.md | `grep "契约 7" .workflow/context/roles/` 命中 9 文件（stage-role + 7 stage + director）；requirement-review.md / planning.md / executing.md / testing.md / acceptance.md / regression.md / done.md 均含契约 7 注脚与模板示例 | ✅ | 覆盖全部 9 角色 |
| AC-03 | harness status / next / ff / suggest --list 默认在同行附带 title | chg-02（CLI 渲染 — render_work_item_id helper） | 本仓库实跑 `workflow_status()` 输出 `current_requirement: req-30（slug沟通可读性增强：全链路透出title）` + `active_requirements: req-30（...）`；`list_suggestions()` 每行 `sug-NN（title）` 渲染正常；testing smoke 1/2/4 通过 | ✅ | next 主输出不含 id，按 plan 跳过无影响 |
| AC-04 | title 缺失时降级打印 `(no title)` 不报错 | chg-02 helper 4 级 fallback | 独立验证 `render_work_item_id('req-999', runtime=None, root=root) == 'req-999 (no title)'`、空 id → `(none)`；`test_render_missing_title_fallback` + `test_render_empty_id_returns_none_placeholder` 绿 | ✅ | 不抛错路径验证通过 |
| AC-05 | runtime.yaml 新增 current_requirement_title / current_regression_title / locked_requirement_title；活跃需求 state yaml title 非空 | chg-01（state schema — title 冗余字段）Step 1 + Step 5 | `DEFAULT_STATE_RUNTIME` 第 57-72 行含三字段；ordered_keys（第 536 行起）保留字段顺序；`state/requirements/req-30-*.yaml` title 非空；smoke 仓库 v2 runtime.yaml 三字段齐全 | ✅ | schema + 活跃 req 双验证 |
| AC-06 | 所有写 state yaml 的代码路径同步写 title，新建缺 title 失败 | chg-01 Step 3 + Step 4 | `_resolve_title_for_id` 在 `create_requirement` / `create_bugfix` / `harness_regression` / `regression_action` / `archive_requirement` / `enter_workflow` / `set_regression_mode` / `set_conversation_mode` 等所有写入点成对写；`create_requirement` / `create_bugfix` 对空 title 抛 `SystemExit` 保留；12 条 chg-01 单测覆盖 | ✅ | 11 写入点全覆盖，grep 证据已列 |
| AC-07 | 归档目录每个索引/摘要显式含 title 字段（首行或 `_meta.yaml`） | chg-04（归档 meta — title 落盘）**optional 延期** | `chg-04/change.md` §1.1 登记延期决策；现状归档目录名（`req-29-批量建议合集（2条）/`）+ `需求摘要.md` 首行 `# 需求摘要：{id} {title}` 模板已覆盖 human 可读层；`_meta.yaml` 硬约束未落地 | ⚠️ 延期 | 需求 §8 / planning / executing 三处一致登记；建议 done 登 sug |
| AC-08 | experience/index.md 来源列带 title；新增硬校验 | chg-03 Step 4 + Step 5 | `.workflow/state/experience/index.md` 第 64-74 行含"来源字段校验规则（契约 7）"；`context/experience/roles/planning.md` 经验一来源段已改写为 `req-29（批量建议合集 2 条）— sug-01（ff --auto）+ sug-08（archive 判据）合集`；`context/experience/roles/acceptance.md` 经验一来源 "req-29 — ff --auto..." 为存量条目，按"新增时校验、存量按需补"策略不算违规 | ✅ | 规则 + 示范回填双备 |
| AC-09 | L2 / L3 至少 2 单测 + 1 smoke，零回归 | chg-01 × 12 + chg-02 × 12 + chg-03 × 8 = 32 条 | 独立复跑 `pytest tests/test_runtime_title_fields.py tests/test_render_work_item_id.py tests/test_chg03_title_contract.py`：**32 passed**；全量 220 collected / 183 passed / 36 skipped / 1 pre-existing failed（`test_smoke_req29` 与 req-30 无关） | ✅ | 超额覆盖（32 >> 3），smoke 级 `test_workflow_status_prints_current_requirement_with_title` 包含 |
| AC-10 | req-30 自身对人文档作为新约定示范样本 | chg-03 Step 6 + Step 7 | `需求摘要.md` / `实施说明.md` × 3 / `变更简报.md` × 3 / `测试结论.md` / `session-memory.md` / 本 `acceptance-report.md` 首次引用 req-30 均带完整 title；`test_chg03_title_contract.py::TestReq30SelfCertification` 2/2 绿 | ✅ | 全部自证样本可 grep 证据 |

**综合：9 ✅ + 1 延期覆盖（AC-07，计划内 / 非阻断）。**

---

## 独立验证证据三元组（需求 → 实现 → 证据）

| AC | 需求条款（requirement.md 行号） | 实现位点 | 独立证据 |
|----|------------------------------|---------|---------|
| AC-01 | requirement.md:105 | stage-role.md 契约 7（#7 节）+ 角色文件注脚 | `grep "req-30（slug" .workflow/state/sessions/req-30/session-memory.md` 命中首行；action-log 77 处带 title |
| AC-02 | requirement.md:106 | stage-role.md + 7 stage + director briefing | `grep "契约 7" .workflow/context/roles/` 9 文件全命中 |
| AC-03 | requirement.md:110 | workflow_helpers.py:5251 / 5254 / 5256 / 5379 / 3429 | 实跑 workflow_status + list_suggestions stdout 含 title |
| AC-04 | requirement.md:111 | workflow_helpers.py:461 render_work_item_id fallback | 独立 Python 调用 helper 4 分支验证 |
| AC-05 | requirement.md:115 | workflow_helpers.py:57-72 DEFAULT_STATE_RUNTIME | yaml 字段列表 + 当前 req-30 yaml 非空 |
| AC-06 | requirement.md:116 | workflow_helpers.py _resolve_title_for_id 在 11 写入点 | chg-01 12 单测 + grep `_title` 26 处命中 |
| AC-07 | requirement.md:120 | chg-04 延期 | 现状归档目录名 + 需求摘要.md 首行 |
| AC-08 | requirement.md:121 | state/experience/index.md:64 + planning.md:44 | grep 校验规则 + 经验来源段 |
| AC-09 | requirement.md:125 | 3 新测试文件 32 用例 | 独立复跑 `32 passed`；全量零新增回归 |
| AC-10 | requirement.md:126 | 所有 req-30 对人文档首次引用 | grep 每份对人文档首段 + 自证测试 |

---

## 差异 / 缺口

### 计划内延期（非阻断）

- **AC-07 延期**（chg-04 归档 `_meta.yaml` / 首行 title 强约束未落地）：
  - 三处一致登记：需求 §8 "chg-04（可选）"；planning session-memory "chg-04 optional"；executing session-memory 第 161-171 行延期决策。
  - 现状替代覆盖：归档目录名已含 slug（人可读）+ `需求摘要.md` 首行模板在 planning / requirement-review 角色约定。
  - 风险：若未来有批量扫描脚本需要 `_meta.yaml` 统一消费，仍需独立交付。
  - 建议：done 阶段登 sug 池（"归档 `_meta.yaml` 落盘 + migrate_requirements 补齐"），不作为 req-30 阻断项。

### 非阻断性差异（设计合理性）

1. **AC-04 legacy yaml 非标准空串兜底**：若未来手工写 `title: ''` 字面量，yaml 读回为字符串 `"''"`，会显示 `（''）`；CLI 自身写回不出此问题。testing 已登记为"可选增强"；非当前 AC 要求。
2. **regression id（reg-NN）title 渲染**：`_resolve_title_for_id` 对 reg-* 返回空串；当前靠 `current_regression_title` runtime 缓存兜底，其他 reg 引用场景走 `(no title)` 降级。不在 AC-04 要求范围内。
3. **存量经验文件来源段**：`context/experience/roles/acceptance.md` 经验一来源 "req-29 — ff --auto..." 按 AC-08 "新增时校验、存量按需补"策略允许保留，不视为违规。
4. **契约 7 agent 运行时遵守度**：testing 测试结论明确"静态断言 ≠ 运行时验证"——静态 grep 全部通过，但 agent 在真实任务中是否自动按 `{id}（{title}）` 首次引用属 agent 行为，需后续抽样观察。本轮 session-memory / 实施说明 / 变更简报 / acceptance-report 均已自证合规。

---

## 衍生建议（转 sug / 后续 bugfix）

1. **sug 候选 1**：归档 `_meta.yaml` 落盘（对应 chg-04 延期内容）——done 阶段决定是否登 sug 池。
2. **sug 候选 2**：legacy yaml 非标准空串 title 的 `.strip("'\"")` 兜底（testing 已登记为"可选增强"）。
3. **sug 候选 3**：regression reg-NN 独立 title 源 / state yaml（当前靠 runtime 缓存兜底，跨 session 可能漂移）。
4. **sug 候选 4**：`harness status --lint` 自动化工具（契约 7 grep 校验）——chg-03/change.md §5.2 "Out of scope" 明确登记为"后续 sug"。
5. **sug 候选 5**：辅助角色（harness-manager.md / tools-manager.md / reviewer）汇报模板契约 7 覆盖——chg-03/change.md §5.2 明确排除。

---

## 综合判定

- **阻断性差异**：无。
- **非阻断性差异**：5 项（AC-04 legacy 非标准空串、reg-NN title 源、存量经验来源段、agent 运行时遵守度、辅助角色未覆盖），均非 AC 硬门禁要求，转后续迭代处理。
- **计划内延期**：AC-07（chg-04 optional），三处一致登记 + done 登 sug 建议。
- **回归测试**：32 条新增单测零回归，全量 183 passed + 1 pre-existing（req-29 归档 checklist，与 req-30 无关）。
- **自证样本**：req-30 自身所有对人文档 + session-memory + acceptance-report 首次引用 req-30 均带 title，契约 7 自证通过。
- **建议人工判定**：✅ **通过**（无条件）。可直接推进 done；AC-07 延期建议在 done 阶段六层回顾时决定登 sug / 不做。

---

## ff 模式说明

- 本 acceptance 阶段在 ff 模式下执行，AI 已自主完成逐条 AC 核查。
- 核心 AC-01~AC-06 / AC-08~AC-10 全部 ✅ 通过，AC-07 延期已三处一致登记。
- **判定：通过**，主 agent 可自动推进到 `done`。

---

## 参考文件清单

- 需求权威：`artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/requirement.md`
- 对人文档：`artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/需求摘要.md` / `测试结论.md`
- 4 个 change：
  - `changes/chg-01-state-schema-title冗余字段/`（change.md + plan.md + 变更简报.md + 实施说明.md）
  - `changes/chg-02-cli-render-work-item-id-helper/`（同上 4 份）
  - `changes/chg-03-role-contract-experience-index-title硬门禁/`（同上 4 份）
  - `changes/chg-04-archive-meta-title落盘/`（change.md + plan.md，optional 延期）
- 阶段记录：`.workflow/state/sessions/req-30/session-memory.md` + `test-evidence.md`
- 代码实现：`src/harness_workflow/workflow_helpers.py`（`DEFAULT_STATE_RUNTIME` / `render_work_item_id` / `_resolve_title_for_id` / `_resolve_title_for_suggestion` / `_render_id_list` + 11 写入点同步）
- 新增测试：`tests/test_runtime_title_fields.py` / `tests/test_render_work_item_id.py` / `tests/test_chg03_title_contract.py`
- 契约文档：`.workflow/context/roles/stage-role.md`（契约 7）+ 9 角色文件
- 索引：`.workflow/state/experience/index.md`（来源字段校验规则）+ `.workflow/context/experience/roles/planning.md`（示范回填）
