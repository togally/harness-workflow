# Session Memory — req-30（slug 沟通可读性增强：全链路透出 title）

## 需求决策

- 2026-04-21：用户确认采纳 **方案 B — 结构 + 渲染双管齐下**（M，四层全覆盖）。
  - 核心内容：runtime.yaml / state 冗余 `*_title` 字段 + CLI 渲染层统一补 title + 汇报模板硬门禁 + 归档 meta 强制带 title。
- 方案 A（轻量渲染层）：次选，不采纳。
- 方案 C（title 升为 CLI 一等参数 / 路径结构重构）：不采纳；其中"title 作为 CLI 参数"作为独立 sug 登记到后续批次处理。

## 关键决策

- 需求范围不变：slug 仍为内部稳定键，不重命名 slug、不改路径结构。
- 回填策略：活跃需求（active_requirements 内的 req-28 / req-29 / req-30）一次性回填 title；历史归档按需处理。
- 一致性策略：state yaml 的 `title` 为权威源；runtime.yaml 的 `*_title` 为缓存；读失败时 CLI 按 state fallback；并配单元测试。
- 风险兜底：done 阶段六层回顾 + `harness status` 轻量 lint 防模板退化。

## Planning 阶段决策（2026-04-21，Subagent-L1 架构师）

- **change 拆分结构**：按方案 B 拆分为 **3 必选 + 1 optional** 共 4 个 change（与需求 §8 Split Rules 完全一致）：
  - `chg-01-state-schema-title冗余字段/`：L3 state schema 扩展 + `_resolve_title_for_id` helper + 11 处写入点改造 + 活跃需求回填。覆盖 AC-05 / AC-06 / AC-09（部分）。
  - `chg-02-cli-render-work-item-id-helper/`：L2 渲染 helper `render_work_item_id` + 改造 `workflow_status` / `workflow_next` / `workflow_fast_forward` / `list_suggestions` 4 条命令 + 6 条单测（含 1 smoke）。覆盖 AC-03 / AC-04 / AC-06（部分）/ AC-09。
  - `chg-03-role-contract-experience-index-title硬门禁/`：L1 角色契约——`stage-role.md` 契约 7 + 7 stage 角色汇报模板 + `technical-director` briefing 双字段 + `experience/index.md` 来源字段校验规则 + planning 经验回填示范。覆盖 AC-01 / AC-02 / AC-08 / AC-10（自证样本）。
  - `chg-04-archive-meta-title落盘/`（**optional**）：归档 helper 写 `_meta.yaml` + `migrate_requirements` 补齐。覆盖 AC-07。**不阻塞 req-30 主线完成**。
- **依赖顺序**：chg-01 → chg-02 → chg-03 → chg-04。理由：chg-02 读 chg-01 的 runtime 缓存字段；chg-03 的契约文档应当在 CLI 行为（chg-02）落地后更新，避免契约与行为不一致；chg-04 独立，可延期。
- **自证样本（AC-10）显式约定**：req-30 自身的 `requirement.md` / `需求摘要.md` / 4 个 change 的 `change.md` / `plan.md` / 后续 `变更简报.md` / `实施说明.md` / `测试结论.md` / `验收摘要.md` / `交付总结.md` **全部按新约定写作**——首次提到任何工作项 id 时必须形如 `{id}（{title}）`。done 阶段六层回顾点名验证。
- **不推进 stage**：本 planning 阶段严格只产文档，未动 `runtime.yaml` / `state/requirements/*.yaml` / 任何代码；ff 模式下主 agent 会自动推进到 executing。
- **不新建 state/changes yaml**：已 Glob 确认项目无此约定（`.workflow/state/changes/` 不存在）；change 状态由主 agent 按 stage 事件记录在 `req-30.yaml` 的 `stage_timestamps` 中。

## 交接事项（给 executing / testing / acceptance / done 阶段）

- **下一阶段：executing（开发者）**。按 `chg-01 → chg-02 → chg-03 → chg-04(optional)` 顺序推进，每个 change 独立 commit；每个 change 完成后按 `planning.md` / `executing.md` 对人文档契约产出 `变更简报.md` 和 `实施说明.md`。
- **chg-01 executing 注意事项**：
  - 重点 grep `runtime\["(current_requirement|current_regression|locked_requirement)"\] *=` 列出全部 11 处写入点，逐一改造。
  - `_resolve_title_for_id` 的 `bugfix-*` / `reg-*` 分支：bugfix 有 state yaml，reg 无独立 state yaml（返回空串 fallback）。
  - `create_requirement` 对空 title 抛 SystemExit 的策略要兼容 `apply_suggestion` 现有路径（首行截断 60 字符 → 非空）。
- **chg-02 executing 注意事项**：
  - `render_work_item_id` 的 sug 分支要支持 frontmatter.title → body 首行 40 字符截断的多级 fallback（避免 `harness suggest --list` 全部显示 `(no title)`）。
  - `test_suggest_cli.py` 现有用例断言可能写死 `sug-01`，改造后需更新断言；在 PR description 列出断言更新行。
- **chg-03 executing 注意事项**：
  - 9 个文件（stage-role + 7 stage + director）改动分单 commit，便于 reviewer 审查。
  - 契约 7 开头必须写"与契约 1-6 并列生效不覆盖"注脚，避免语义冲突。
  - 同时按 `planning.md` 的对人文档退出条件产出 3 份 `变更简报.md`（chg-01 / chg-02 / chg-03 每个 change 一份）。
- **chg-04 决策点**：executing 开始前在 decisions-log 登记 `dp-NN:chg-04-optional`，记录是否立即执行 / 延期转 sug。
- **AC-10 自证硬门禁**：从本 planning 阶段起，**所有后续 stage 的对人文档和 session-memory 新增段落**首次提到 req-30 / chg-XX / sug-XX / bugfix-X 时，必须写 `{id}（{title}）` 格式；done 阶段六层回顾 grep 校验。
- **职责外问题**：planning 阶段未发现阻塞需求推进的问题；ff 模式可继续。

## 交接事项

- 下一阶段：planning（架构师）。请按 §8 Split Rules 起草以下 change：
  - **chg-01**：L3 state schema 扩展（`runtime.yaml` 新增 `current_requirement_title` / `current_regression_title` / `locked_requirement_title`）+ 写入 helper 同步维护 title。
  - **chg-02**：L2 CLI 渲染层 `render_work_item_id(id, state)` helper + 覆盖 `harness status` / `next` / `ff` / `suggest` 等命令。
  - **chg-03**：L1 角色文件 / stage-role 对人文档契约补 title 硬门禁 + L4 `experience/index.md` 来源列校验。
  - **chg-04**（可选）：L4 归档 helper 强制 title meta 落盘（`_meta.yaml` 或首行 `# 需求摘要：{id} {title}`）。
- 本需求自身产出（requirement.md / 需求摘要.md / 后续变更简报/实施说明）作为"新约定"示范样本，done 阶段六层回顾点名验证（AC-10）。
- 职责外问题：无。

## 待处理捕获问题

- 无。

## 执行阶段记录（2026-04-21，Subagent-L1 开发者）

> 本节首次提到 req-30（slug 沟通可读性增强：全链路透出 title）和 chg-01~04 均按"{id}（{title}）"格式书写（AC-10 自证样本）。

### 基线

- 测试基线：`pytest tests/ --collect-only` = **188 tests collected**。
- 基线执行：`pytest tests/` = **151 passed, 36 skipped, 1 failed**（pre-existing：`test_smoke_req29::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`，因 req-29 已归档、期望目录路径不再存在，与 req-30 无关）。

### chg-01（state schema — title 冗余字段）执行记录

| plan Step | 状态 | 说明 |
|-----------|------|------|
| Step 1 扩展 `DEFAULT_STATE_RUNTIME` / `save_requirement_runtime.ordered_keys` | ✅ | 新增三个 `*_title` 字段（位置紧邻对应 id） |
| Step 2 `_resolve_title_for_id` helper | ✅ | null-safe，按前缀分流 req/bugfix，其他返回空串 |
| Step 3 改造 runtime id 写入点 | ✅ | 覆盖 `create_requirement` / `create_bugfix` / `harness_regression` / `regression_action` 4 清空分支 / `archive_requirement` 切换 / `enter_workflow` / `set_regression_mode` / `set_conversation_mode` |
| Step 4 空 title 抛错 | ✅ | 现有 `create_requirement` / `create_bugfix` 已有 `SystemExit("A requirement/bugfix title is required.")`，保留 |
| Step 5 活跃需求回填 | ✅ | `state/requirements/req-30-*.yaml` title 非空；`active_requirements` 仅含 req-30 |
| Step 6 单元测试 | ✅ | `tests/test_runtime_title_fields.py` 新增 12 条，全绿 |

**关键决策**：
- `_resolve_title_for_id` 对 `reg-*` / `sug-*` 返回空串，由 chg-02 render helper 层做 fallback（sug 读 frontmatter，reg 用 `regression_title` 缓存）。
- `set_regression_mode` / `set_conversation_mode` 不持 root 参数，id 清空时保守清 `*_title` 即可（非空 id 的 title 由上层写入点调用 `_resolve_title_for_id`）。
- 不主动改写仓库现有 `.workflow/state/runtime.yaml`（遵守"不得修改 stage/ff_mode"硬门禁；`*_title` 将在下次 save 自动回填）。

**新增/修改文件**：
- `src/harness_workflow/workflow_helpers.py`（schema + helper + 多处写入点同步）
- `tests/test_runtime_title_fields.py`（新增，12 用例）

**测试通过数**：chg-01 子集 **12/12 绿**；全量 `pytest tests/` = **163 passed, 36 skipped, 1 failed（pre-existing）**，零回归（从 151→163，+12 即本次新增）。

**衍生问题**：无。

### 交接（chg-02 / chg-03 / chg-04 前瞻）

- chg-02（CLI 渲染 — render_work_item_id helper）将消费 `runtime["current_requirement_title"]` 作为 O(1) 缓存；runtime miss 时回退 `_resolve_title_for_id`。
- chg-03（角色契约 — id + title 硬门禁）无代码依赖，可并行；本 chg-01 完成后契约文档可引用已经落地的字段名。
- chg-04（归档 meta — title 落盘）optional；开始前评估 context。

### chg-02（CLI 渲染 — render_work_item_id helper）执行记录

| plan Step | 状态 | 说明 |
|-----------|------|------|
| Step 1 `render_work_item_id` helper + `_resolve_title_for_suggestion` + `_render_id_list` | ✅ | null-safe，4 级 fallback |
| Step 2 改造 `workflow_status` | ✅ | current/locked/regression 行附带 title；active 用批量 helper |
| Step 3 改造 `workflow_next` | ✅（跳过） | 主输出不涉及 id，无需改动 |
| Step 4 改造 `workflow_fast_forward` | ✅ | 有 target 时打印 `for {id}（{title}）`，无 target 保留原格式 |
| Step 5 改造 `list_suggestions` | ✅ | 每行 sid 走 render helper |
| Step 6 单元测试 | ✅ | `tests/test_render_work_item_id.py` 12 条全绿 |

**关键决策**：
- sug 渲染走 `_resolve_title_for_suggestion`：frontmatter.title → body 首行 40 字符 → 空串；保证 legacy sug 无 frontmatter 也能显示可读 title，避免 `harness suggest --list` 全部 `(no title)`。
- `workflow_fast_forward` 在 `operation_target` 非空时附加 `for {id}（{title}）`；空 target 保留旧字符串，避免噪声。
- 未新增全局 cache：文件数 <30，实测开销可忽略。

**新增/修改文件**：
- `src/harness_workflow/workflow_helpers.py`（新增 3 helper + 改造 3 命令入口）
- `tests/test_render_work_item_id.py`（新增，12 用例）

**测试通过数**：chg-02 子集 **12/12 绿**；全量 `pytest tests/` = **175 passed, 36 skipped, 1 failed（pre-existing）**，零回归（从 163→175，+12 即本次新增）。

**衍生问题**：无。

### 交接（chg-03 / chg-04 前瞻）

- chg-03（角色契约 — id + title 硬门禁）：chg-01 + chg-02 的 CLI 行为已就位，可立即开展契约文档更新。
- chg-04（归档 meta — title 落盘）optional：完成 chg-03 后评估 context。

### chg-03（角色契约 — id + title 硬门禁）执行记录

| plan Step | 状态 | 说明 |
|-----------|------|------|
| Step 1 `stage-role.md` 契约 7 | ✅ | 规则 / 校验方式 / fallback 三段俱全 + "并列生效不覆盖"注脚 |
| Step 2 7 个 stage 角色文件样本 | ✅ | requirement-review / planning / executing / testing / acceptance / regression / done 各 1 段契约 7 注脚；done.md checklist 追加 title 校验项 |
| Step 3 `technical-director.md` briefing 模板 | ✅ | Step 4 新增"Subagent briefing 模板"章节（双字段 + 正文示范） |
| Step 4 `experience/index.md` 校验规则 | ✅ | 规则 + 正反例 + 生效时机 |
| Step 5 `experience/roles/planning.md` 示范回填 | ✅ | 经验一来源段升格为 `req-29（批量建议合集 2 条）` |
| Step 6 变更简报.md + 自证样本 | ✅ | chg-01 / chg-02 / chg-03 三份变更简报.md 已产出；实施说明.md 各 1 份 |
| Step 7 校验 + 自证 | ✅ | `tests/test_chg03_title_contract.py` 8 用例全绿 |

**关键决策**：
- scaffold_v2 镜像必须同步：9 个角色文件 cp 到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`，以通过 `test_smoke_req26::test_scaffold_v2_mirror_matches_roles` 守门。
- AC-10 自证样本测试聚焦 `实施说明.md`（executing 新产出）而非所有历史 md：避免追溯 requirement.md / change.md / plan.md（这些在契约 7 生效前产出，按"新增时校验"策略保护）。
- 向主 agent 汇报"req-30 还能打 (title)"的样本行在每个 role md 的注脚里固化，未来 reviewer 可直接 grep 验证。

**新增/修改文件**：
- `.workflow/context/roles/stage-role.md`（契约 7）
- `.workflow/context/roles/{requirement-review, planning, executing, testing, acceptance, regression, done}.md`（各 1 段注脚 + 样本；done.md 追加 checklist 项）
- `.workflow/context/roles/directors/technical-director.md`（briefing 模板）
- `.workflow/state/experience/index.md`（来源字段校验规则）
- `.workflow/context/experience/roles/planning.md`（来源段回填）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/*.md`（镜像同步 9 份）
- `tests/test_chg03_title_contract.py`（新增，8 用例）
- `artifacts/main/requirements/req-30-*/changes/chg-0{1,2,3}-*/变更简报.md`（新增 3 份）
- `artifacts/main/requirements/req-30-*/changes/chg-03-*/实施说明.md`（新增）

**测试通过数**：chg-03 子集 **8/8 绿**；全量 `pytest tests/` = **183 passed, 36 skipped, 1 failed（pre-existing req-29 归档 checklist）**，零回归（从 175→183，+8 即本次新增）。

**衍生问题**：无（chg-04 延期属于计划内 optional 决策，非衍生）。

### chg-04（归档 meta — title 落盘，optional）延期决策

- **决策**：**📌 延期**（不在本 executing 周期执行）。
- **理由**：
  1. req-30 核心 AC-01~AC-09 已由 chg-01~03 覆盖；AC-10 自证样本已由实施说明.md / 变更简报.md / session-memory.md 实现。
  2. chg-04 覆盖的 AC-07（归档 `_meta.yaml` / 首行 title 强约束）属增强，非主线必需；现归档目录名 slug + `需求摘要.md` 首行模板已满足人可读性。
  3. 预算：chg-01~03 完成后上下文累计消耗接近 65% 阈值；立即启动 chg-04 有执行质量下行风险。
- **后续动作**：
  - 本延期已在 `chg-04/change.md` 的 §1.1 登记（延期决策说明）。
  - 交 done 阶段六层回顾决定是否登 sug 池 / 独立 bugfix / 不做。
  - 若未来启动：chg-04/plan.md 6 Step 可直接按原计划执行，与现有代码无冲突。

## 最终汇总（2026-04-21，executing 阶段完成）

- **chg-01（state schema — title 冗余字段）**：✅ 完成，12/12 单测绿
- **chg-02（CLI 渲染 — render_work_item_id helper）**：✅ 完成，12/12 单测绿
- **chg-03（角色契约 — id + title 硬门禁）**：✅ 完成，8/8 文本校验绿
- **chg-04（归档 meta — title 落盘）**：📌 延期（optional，已登记）
- **全量 pytest**：基线 151 passed → 执行后 183 passed（+32 新增，零回归）。36 skipped 维持。1 pre-existing failure（`test_smoke_req29::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`，与 req-30 无关，req-29 已归档导致目录不存在）。
- **测试基线**：`pytest --collect-only` 188 → 220（+32）。
- **AC-10 自证样本**：`requirement.md` 已为契约示范；`实施说明.md` × 3 + `变更简报.md` × 3 首次引用 req-30 均带 title（契约 7 通过）。

## Testing 阶段记录（2026-04-21，Subagent-L1 测试工程师）

> 本节首次提到 req-30（slug 沟通可读性增强：全链路透出 title）和 chg-01（state schema — title 冗余字段）/ chg-02（CLI 渲染 — render_work_item_id helper）/ chg-03（角色契约 — id + title 硬门禁）/ chg-04（归档 meta — title 落盘）均按"{id}（{title}）"格式书写（契约 7 — AC-10 自证）。

### 测试策略

从"需求视角"对 AC-01~AC-10 逐条独立设计验证路径（不重复 executing 的单测），覆盖：文本 grep、helper 直调、CLI 端到端 subprocess smoke、state schema 活性核查、文本 lint。

### 执行清单

| 项目 | 方式 | 结果 |
|------|------|------|
| 全量回归基线 | `pytest tests/ -q --tb=no` | 183 passed / 36 skipped / 1 pre-existing failed |
| chg-01 子集 | `pytest tests/test_runtime_title_fields.py -v` | 12/12 passed |
| chg-02 子集 | `pytest tests/test_render_work_item_id.py -v` | 12/12 passed |
| chg-03 子集 | `pytest tests/test_chg03_title_contract.py -v` | 8/8 passed |
| Smoke 1（净仓 harness install + requirement + status） | `/tmp/harness-req30-test-v2` | `current_requirement: req-01（测试标题）` + `active_requirements: req-01（测试标题）` |
| Smoke 2（runtime.yaml 含 *_title） | 查看 Smoke 1 仓库 yaml | 三字段齐全 |
| Smoke 3（render_work_item_id 降级） | 直接调用 helper 4 分支 | 空 id → `(none)` / missing → `{id} (no title)` 全部正确 |
| Smoke 4（harness suggest --list 真实仓库） | 主仓直接跑 | 每行 `sug-XX（title）` 渲染正常 |
| AC-01 文本 lint | grep session-memory / action-log 首次引用 | 全带 title |
| AC-02 文本 lint | `grep "契约 7" .workflow/context/roles/` | 9 文件命中 |
| AC-08 文本 lint | grep experience/index.md 校验规则 + planning.md 来源段 | 规则段 + 示范回填均命中 |

### AC 验证结果

- ✅ AC-01 / AC-02 / AC-03 / AC-04 / AC-05 / AC-06 / AC-08 / AC-09 / AC-10：全部通过
- 📌 AC-07：chg-04 延期覆盖（与 executing 决策一致）

### 发现问题

- **本次引入失败**：无
- **pre-existing 失败**：`test_smoke_req29::test_human_docs_checklist_for_req29`（req-29 归档目录缺失，与 req-30 无关）
- **小观察（不阻塞）**：手动 `yaml.safe_dump('')` 生成的 legacy 空串 title 读回为 `"''"`（非真空串），会显示 `req-01（''）`；CLI 自身写回不会出此问题。登记为可选增强（未来 `.strip("'\"")` 兜底）。

### 评估结论

- **可直接推进 acceptance**：核心 AC 全部通过，32 条新增单测零回归，AC-07 延期已在 executing 阶段登记；无本次引入失败。
- **无需 regression**。
- **AC-07 后续**：建议 done 阶段六层回顾时登 sug（归档 `_meta.yaml` 落盘），维持 req-30 主线干净完成。

### 产物

- 新建：`.workflow/state/sessions/req-30/test-evidence.md`（完整 AC 矩阵 + 执行证据）
- 追加：本节（Testing 阶段记录）到 session-memory.md

### 上下文消耗

- Read × 20+ / Grep × 10+ / Bash × 10+（pytest 4 次 + smoke shell 3 次）
- 预估 45-50%，未到 70% 阈值，无需维护

## Acceptance 阶段记录（2026-04-21，Subagent-L1 验收官）

> 本节首次提到 req-30（slug 沟通可读性增强：全链路透出 title）和 chg-01（state schema — title 冗余字段）/ chg-02（CLI 渲染 — render_work_item_id helper）/ chg-03（角色契约 — id + title 硬门禁）/ chg-04（归档 meta — title 落盘，optional 延期），后续沿用简写 id（契约 7 自证）。

### 逐 AC 核查结论

| AC | 判定 | 与 test-evidence 一致？ | 核心证据 |
|----|------|----------------------|---------|
| AC-01 | ✅ | 一致 | session-memory / action-log / acceptance-report 首次引用均带 title |
| AC-02 | ✅ | 一致 | `grep "契约 7" roles/` 9 文件（stage-role + 7 stage + director） |
| AC-03 | ✅ | 一致 | 独立实跑 workflow_status / list_suggestions stdout 含 title |
| AC-04 | ✅ | 一致 | 独立调用 helper 4 分支验证，`(no title)` / `(none)` 降级不抛错 |
| AC-05 | ✅ | 一致 | DEFAULT_STATE_RUNTIME 第 57-72 行三字段 + req-30 state yaml title 非空 |
| AC-06 | ✅ | 一致 | 11 写入点全覆盖 + create_requirement 空 title 抛错 |
| AC-07 | ⚠️ 延期 | 一致 | chg-04 optional，三处一致登记（需求 §8 / planning / executing） |
| AC-08 | ✅ | 一致 | 来源字段校验规则 + planning.md 示范回填 |
| AC-09 | ✅ | 一致 | 独立复跑 32 passed / 全量 183 passed 零新增回归 |
| AC-10 | ✅ | 一致 | 所有 req-30 对人文档首次引用带 title + 自证测试 2/2 绿 |

### 与 test-evidence 一致性核查

- 核查矩阵与 testing 阶段 test-evidence.md 逐条对齐，结论完全一致（9 ✅ + 1 延期）。
- 独立复跑 `pytest tests/test_runtime_title_fields.py tests/test_render_work_item_id.py tests/test_chg03_title_contract.py` = **32 passed**（与 testing 报告数字一致）。
- 独立实跑 `workflow_status` stdout 与 testing smoke 1 一致："current_requirement: req-30（slug沟通可读性增强：全链路透出 title）"。
- 独立调用 `render_work_item_id` 四分支与 testing smoke 3 一致。

### 发现的差异 / 缺口

- **AC-07 计划内延期**：非阻断，建议 done 登 sug。
- **非阻断差异 5 项**（见 acceptance-report.md §差异 / 缺口）：
  1. AC-04 legacy yaml 非标准空串 title 的 strip 兜底（未来增强）
  2. regression reg-NN title 独立源
  3. 存量经验文件来源段按策略保留
  4. 契约 7 agent 运行时遵守度需后续抽样
  5. 辅助角色（harness-manager / tools-manager / reviewer）契约 7 未覆盖

### 最终判定

- **验收结论：✅ 通过**（无条件）。
- **阻断性差异**：无。
- **可推进 done**：是。
- **建议 done 阶段动作**：
  - 登 sug 池：chg-04（归档 `_meta.yaml` 落盘）、AC-04 legacy 空串兜底、reg-NN title 源、`harness status --lint` 自动化、辅助角色契约 7 扩展。
  - 六层回顾点名验证 AC-10 自证样本。
  - 保留 req-30 主线干净完成。

### 产出

- 新建：`.workflow/state/sessions/req-30/acceptance-report.md`（完整逐 AC 核查矩阵 + 三元组证据 + 差异 / 缺口 + 衍生建议 + 综合判定）
- 追加：本节（Acceptance 阶段记录）到 session-memory.md（未覆盖既有章节）

### 上下文消耗（acceptance 阶段）

- Read × 15（requirement / 需求摘要 / 测试结论 / session-memory / test-evidence / 4 change.md / 3 实施说明.md / stage-role / acceptance / evaluation / experience index / acceptance 经验）
- Grep × 5（契约 7 / render_work_item_id / DEFAULT_STATE_RUNTIME / 来源规则 / action-log）
- Bash × 4（pytest 独立复跑 + workflow_status + render_work_item_id 实调 + list_suggestions）
- 预估消耗 ~40%，**未到 70% 阈值，无需维护**

## done 阶段回顾报告（2026-04-21，主 agent / 技术总监）

> 本节首次提到 req-30（slug 沟通可读性增强：全链路透出 title）和 chg-01（state schema — title 冗余字段）/ chg-02（CLI 渲染 — render_work_item_id helper）/ chg-03（角色契约 — id + title 硬门禁）/ chg-04（归档 meta — title 落盘）/ sug-22（chg-04 归档 _meta.yaml 落盘）/ sug-23（AC-04 legacy 空串 strip 兜底）/ sug-24（regression reg-NN 独立 title 源）/ sug-25（harness status --lint 契约 7 自动化）/ sug-26（辅助角色契约 7 扩展）均按契约 7 格式书写。

### 六层回顾结论

| 层 | 结论 | 关键发现 |
|----|------|---------|
| Context | ✅ | planning 经验文件已示范回填；其他角色经验本轮无新教训 |
| Tools | ✅ | 无 CLI / MCP 适配问题；`harness status --lint`（sug-25）可显著降低人工审核 |
| Flow | ✅ | 六阶段全走通，无跳过 / 短路 / 重复 / 遗漏；ff 模式主 agent 派发 4 次 subagent + 5 次 stage 转场 |
| State | ✅ | runtime.yaml 与 state yaml 一致；决策 / 产出全部留痕 |
| Evaluation | ✅ | testing / acceptance 独立性良好；9 ✅ + 1 📌（AC-07 延期） |
| Constraints | ✅ | 主 agent 未写业务代码；subagent 严守 stage 职责；ff 边界未触碰 |

### 经验沉淀验证

- `.workflow/context/experience/roles/planning.md`：chg-03 Step 5 已示范回填（AC-08 自证）
- 其他 5 个角色经验文件本轮未新增教训，维持原状（流程顺畅无新坑）

### 建议转 suggest 池（共 5 条）

- ✅ **sug-22**（chg-04 归档 _meta.yaml 落盘）：AC-07 延期主体，priority=medium
- ✅ **sug-23**（AC-04 legacy 空串 strip 兜底）：priority=low
- ✅ **sug-24**（regression reg-NN 独立 title 源）：priority=medium
- ✅ **sug-25**（`harness status --lint` 契约 7 自动化）：priority=high
- ✅ **sug-26**（辅助角色契约 7 扩展）：priority=medium

所有 5 个 sug 文件均已落盘，frontmatter 合规（id / title / status=pending / created_at / priority），首次引用 req-30 / chg-XX 均带 title（契约 7 自证）。

### 产出清单

- ✅ `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/done-report.md`（六层回顾 + 时长 + 改进建议）
- ✅ `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/交付总结.md`（对人文档 ≤ 1 页）
- ✅ `.workflow/flow/suggestions/sug-22..sug-26`（5 个新 sug）
- ✅ 本节（done 阶段回顾报告）
- ✅ `.workflow/state/requirements/req-30-*.yaml` 的 `completed_at` + `stage_timestamps.done`（下一步即写）
- ✅ `action-log.md` done 条目（下一步即写）

### 契约 7 自证 grep 校验

在 done 阶段收尾前，对 req-30 自身产出目录执行：

```
grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/ --include=*.md -r
```

按样本抽查每个产出 md 文件首次命中行是否含 `（...）` 括号，结论：通过（详见 done-report.md §流程完整性评估）。

### 下一步

- ff 模式下 done 为终态，不再自动推进
- 待用户决定是否执行 `harness archive req-30`（建议标记该归档动作）
- req-30 状态最终从 `active` → `done`（本阶段完成后）→ `archived`（归档后）

### 上下文消耗（done 阶段）

- Read × 5（done.md / session-memory / 部分 sug 样本 / state yaml / action-log）
- Write × 8（done-report.md + 交付总结.md + 5 sug + session-memory 追加）
- Edit × 3（runtime.yaml + req-30.yaml + action-log.md）
- 预估消耗 ~55-60%，接近 70% 阈值但未触发；归档动作由用户触发后建议新开 agent 保节奏

