# Session Memory — bugfix-3

## 1. Current Goal

- 对用户反馈"pipx 重装后新项目 install/update 生成数据不正确"做独立只读诊断，判断是否真实问题、根因、路由方向。

## 2. Context Chain

- Level 0: 主 agent (harness-manager) → stage: regression
- Level 1: Subagent-L1（regression 诊断师）→ 任务：bugfix-3 独立诊断

## 3. Current Status

- Regression 诊断完成。判定为**真实问题**，根因定位到 `update_repo` 链路上的两处实现 bug。
- 路由决策：`testing`（先补用例再修复）。
- 已完成只读诊断，未改动目标项目任何文件。

## 4. Completed Tasks

- [x] 加载角色链：runtime.yaml → tools/index.md → project-overview.md → base-role.md → stage-role.md → regression.md → experience/roles/regression.md → evaluation/regression.md → stage-tools.md
- [x] 硬门禁三自我介绍
- [x] 检查 pipx 安装状态：确认为 editable 安装，指向主仓库源码，版本 0.1.0
- [x] 核查目标项目 `.workflow/state/runtime.yaml`：operation_target=req-02/stage=done/active_requirements=[]，是目标项目自身历史，非主仓污染
- [x] 核查目标项目 `state/requirements/`、`state/sessions/`、`flow/requirements/`、`flow/suggestions/`：全部为空，未拷入主仓库数据
- [x] 对比 `diff -rq scaffold_v2/.workflow/ 目标项目/.workflow/`：14 处 differ，聚焦 context/roles 与 context/experience
- [x] 检查 `.codex/harness/managed-files.json`：确认 `context/roles/{acceptance,done,executing,planning,regression,requirement-review,stage-role,testing}.md` 等全部未登记
- [x] 核查 `.workflow/context/backup/legacy-cleanup/`：发现 `experience/index.md` 和 `index.md-2` 两份历史副本，证明 update 循环归档
- [x] 核查 `.claude/skills/harness` vs 模板：一致，仅多 overlay `agent/claude.md`
- [x] 产出 `regression/diagnosis.md`、`regression/回归简报.md`、`regression/required-inputs.md`

## 5. Validated Approaches

- 只读诊断：`ls`、`diff -rq`、`grep` on JSON、读源码 workflow_helpers.py。未使用 Write/Edit 于目标项目。
- 根因一针见血：不停留在"文件不对"层面，追到 `_sync_requirement_workflow_managed_files` + `_refresh_managed_state` + `LEGACY_CLEANUP_TARGETS` 的具体行号。
- 排除类调查：pipx 版本、runtime 污染、skill overlay 一并核查并证伪，避免把精力消耗在非根因。

## 6. Failed Paths

- 一度怀疑"主仓 req-02~11 数据被拷到目标项目"（任务描述引导），经 `ls state/` 查证为空，排除。
- 一度怀疑"skill 内容错误"，`diff -rq skill_template/ target/.claude/skills/harness/` 仅差 overlay，排除。

## 7. Results

- **真实问题**：2 处 update 实现 bug
  - 根因 A（主）：scaffold_v2 新增/改动文件 + `managed-files.json` 未登记 → `skipped modified` + `_refresh_managed_state` 条件过严 → 永不下发
  - 根因 B（次）：`LEGACY_CLEANUP_TARGETS` 错把 `.workflow/context/experience/index.md` 当 legacy → 每次 update 循环归档
- **路由**：testing（补用例 → executing 修复 `workflow_helpers.py`）
- **非根因已排除**：主仓数据污染、pipx 装旧包、skill 错乱

## 8. Candidate Lessons

### 2026-04-20 regression 诊断：pipx editable vs "包版本不对"
- Symptom: 用户在"pipx reinstall"后感知"生成数据不对"，直觉归因为"包没装好"
- Cause: 实际是 editable 模式（跑主仓源码）+ update 幂等性 bug。"包没装好"是错误假设
- Fix: 诊断时先 `cat __editable__.*.pth`，一行确认 editable 与否；再对比 `managed-files.json` 与 scaffold 目录，避免被表层现象带偏

### 2026-04-20 regression 诊断：LEGACY_CLEANUP_TARGETS 需与 `_refresh_*` 生成器白名单互斥
- Symptom: `experience/index.md` 被归档 + 重建 + 再归档，垃圾副本累加
- Cause: `LEGACY_CLEANUP_TARGETS` 只做"文件名/路径匹配"，未考虑该文件是否在同一 `update_repo` 调用内被另一个生成器重新生成
- Fix: 配置 LEGACY_CLEANUP_TARGETS 时，必须排除所有"活跃再生成产物"（`experience/index.md` 等）。可在 testing 用例中加"连续两次 update 不产生 `legacy-cleanup/.../index.md-N`"断言

## 9. Next Steps

- 主 agent：`harness regression --confirm`（保留 current_regression）→ `harness regression --testing`
- testing 角色：补两条用例
  1. "存量且未登记的 scaffold 文件，update 后必须到达最新模板"
  2. "连续两次 update 不得在 `legacy-cleanup/` 下产生 `index.md-N`"
- executing 角色：修 `_sync_requirement_workflow_managed_files` / `_refresh_managed_state` 的 adopt-as-managed 分支 + 从 `LEGACY_CLEANUP_TARGETS` 删除 `experience/index.md`

## 10. Open Questions

- 用户主观"不对"具体指 A/B/C/D 哪一条？已在 `required-inputs.md` 留问，不阻塞路由。
- 是否要顺带为目标项目清理 `legacy-cleanup/.workflow/context/experience/index.md*` 副本？可放在 executing 的"用户侧副作用修复"子任务。

## 11. 待处理捕获问题（职责外）

- 目标项目 `.codex/harness/config.json` 中 `language: english`，但目标项目 CLAUDE.md / known-risks.md 明显是中文项目。可能存在 language 配置与实际内容不匹配，但这是独立问题，不在 bugfix-3 范围。记录备查。

---

## Testing 阶段（2026-04-20，Subagent-L1 testing 角色）

### Context Chain（延长）

- Level 0: 主 agent (harness-manager) → stage: testing（regression 回退而来，ff_stage_history 保留 regression / planning / testing / acceptance）
- Level 1: Subagent-L1（testing 角色）→ 任务：bugfix-3 TDD 红阶段补两条回归用例

### 已完成 TODO（本阶段）

- [x] 加载角色链：runtime.yaml → tools/index.md → stage-tools.md → project-overview.md → base-role.md → stage-role.md → testing.md → evaluation/testing.md → experience/roles/testing.md
- [x] 硬门禁三自我介绍
- [x] 硬门禁一：派发 toolsManager 查询"pytest fixture / tmp_path / yaml 读写"→ 本地 keywords.yaml 无匹配，按 SOP 追加到 `.workflow/tools/index/missing-log.yaml`，回退使用项目既有 unittest + tempfile 约定
- [x] 探查 `workflow_helpers.py` 关键函数行号（LEGACY_CLEANUP_TARGETS 71 / _load_managed_state 2052 / _refresh_managed_state 2140 / _sync_... 2541 / _unique_backup_destination 2606 / cleanup_legacy_... 2618 / update_repo 2854 / _refresh_experience_index 3585）
- [x] 参照 `tests/test_archive_path.py` 风格，新增测试文件 `tests/test_workflow_helpers_update_idempotent.py`（unittest + tempfile + monkeypatch `_get_git_branch`，不跑真 CLI）
- [x] 用例 1（根因 A）：`test_unregistered_stale_scaffold_file_is_adopted_by_update` → `PYTHONPATH=src python3 -m pytest ... -x` 实跑 **FAIL**，失败点命中 `skipped modified .workflow/context/roles/executing.md`
- [x] 用例 2（根因 B）：`test_experience_index_md_not_cycled_into_legacy_cleanup` → 实跑 **FAIL**，失败点命中 `archived legacy ... -> .../legacy-cleanup/.../experience/index.md-2`
- [x] 产出 `test-evidence.md`（覆盖两条用例的命名、路径、红阶段失败摘要、覆盖充分性论证）
- [x] 产出 `testing/测试简报.md`（对人文档 ≤ 1 页，testing 角色契约字段）
- [x] 追加 `.workflow/state/action-log.md` testing 阶段条目
- [x] 追加 `session-memory.md` testing 阶段条目（本段）

### 产出路径

- 测试代码：`tests/test_workflow_helpers_update_idempotent.py`
- 测试证据：`artifacts/main/bugfixes/bugfix-3-.../test-evidence.md`
- 对人简报：`artifacts/main/bugfixes/bugfix-3-.../testing/测试简报.md`
- 工具系统副作用：`.workflow/tools/index/missing-log.yaml` 追加一条"pytest fixture / tmp_path / yaml 读写"未命中记录
- action-log：`.workflow/state/action-log.md` 顶部新增 testing 阶段条目

### 经验候选（待 executing 完成绿阶段后沉淀到 `context/experience/roles/testing.md`）

- **候选一：TDD 红阶段必须实跑到 FAIL 并核对失败路径与诊断根因一一对齐**
  - 场景：regression 诊断已给出根因行号，testing 阶段补回归用例。
  - 经验：用例写完立刻 `pytest -x` 实跑；不仅看"是否 FAIL"，还要看 `update_repo` 的 stdout 中是否出现诊断里指名道姓的字样（`skipped modified <该文件>` / `archived legacy ... index.md-2`）。只有失败路径与诊断证据链对齐才算"真红"，否则可能是测试 fixture 构造错漏。
  - 来源：bugfix-3 — testing 阶段补幂等性用例

- **候选二：helper 级集成测试优先于 CLI 子进程测试**
  - 场景：验证 `update_repo` 行为时，可选 `subprocess.run([sys.executable, '-m', 'harness_workflow', 'update', ...])` 或直接 import `update_repo(root=...)` 调用。
  - 经验：直接调 helper 层（后者）+ tempdir + monkeypatch `_get_git_branch` 更快（本次 2 条用例 0.86s）且可在断言失败时直接拿 Python traceback，不需要解析 CLI stdout。CLI 子进程测试只在验证 argparse / 命令入口时才用。
  - 来源：bugfix-3 — testing 阶段参考 `test_archive_path.py` 风格

- **候选三：legacy-cleanup 递增副本的最小复现步数 = 2 次 update**
  - 场景：`LEGACY_CLEANUP_TARGETS` 与活跃生成器交叉导致"搬家 - 重建 - 再搬家"循环。
  - 经验：断言"连续 N 次 update"这类行为时，最小能暴露递增副本的 N 就是 2（第 1 次 update 生成 `index.md`+ 搬家 1 份，第 2 次 update 搬家产生 `-2`）。更大的 N 只是放大噪音。写用例时选择最小步数利于后续维护者理解 bug。
  - 来源：bugfix-3 — 用例 2 设计

### 下一步

- **建议路由**：回 executing 修复。
  - 根因 A 修复方向（诊断已给）：`_sync_requirement_workflow_managed_files` 首次遇到"存量但未登记 scaffold 文件"视为 adopt-as-managed，直接覆盖并写 hash；或对 scaffold_v2 全量默认 overwrite + 记 hash，仅对用户自定义文件（如 `development-standards.md`）保留 skip-on-modified。
  - 根因 B 修复方向：从 `LEGACY_CLEANUP_TARGETS` 中移除 `Path(".workflow") / "context" / "experience" / "index.md"`；对目标项目已堆积的 `legacy-cleanup/.workflow/context/experience/index.md*` 做一次性清理（可选）。
- **绿阶段验收标准**：重跑 `tests/test_workflow_helpers_update_idempotent.py` 两条用例必须全部 PASS；同时跑全量 `pytest` 确认零回归（基线：`tests/test_archive_path.py` 等 20 个既有测试文件）。
- **是否需要补充人工输入**：否。诊断 `required-inputs.md` 是非阻塞信息，用例 1 + 2 已覆盖根因 A 与 B 两条，不需要用户额外提供优先级。

### 上下文消耗评估

- 本 subagent 累计读取文件 ~15 个（多数 ≤ 200 行），run_in_background 0 次，pytest 实跑 3 次（单用例 x2 + 合并 x1，累计 < 3s）。预估当前 agent 上下文占比 ~35-45%，远未到 70% 评估阈值，无需压缩。
- 交接给主 agent 后，若继续驱动 executing，主 agent 层若已接近 70% 可考虑 `/compact`，但 testing 阶段产出已全部持久化到 session-memory / test-evidence / 测试简报，`/compact` 损失风险低。

---

## Executing 阶段（2026-04-20，Subagent-L1 executing 角色）

### Context Chain（延长）

- Level 0: 主 agent (harness-manager) → stage: testing（红用例已 FAIL，准备进 executing 绿阶段）
- Level 1: Subagent-L1（testing 角色）→ 已产出两条红用例（上一段）
- Level 1: Subagent-L1（executing 角色，本段）→ 任务：落根因 A+B 修复 + 红 → 绿 + 全量 pytest 零回归 + 手动烟测

### 已完成 TODO（本阶段，按 bugfix.md Fix Plan 步骤编号）

- [x] Step 0：硬门禁三自我介绍（"我是开发者（executing 角色）Subagent-L1 ..."）
- [x] 加载角色链：runtime.yaml → tools/index.md → stage-tools.md → project-overview.md → base-role.md → stage-role.md → executing.md → experience/roles/executing.md（经验一~七）→ flow/stages.md
- [x] 硬门禁一：派发 toolsManager 查询"python AST 编辑 / dict 读写 / hash 计算"→ keywords.yaml 无匹配，追加 missing-log.yaml 一条 executing 未命中记录，回退标准 Edit/Read/Grep
- [x] 读取诊断产物：`regression/diagnosis.md`（根因 A/B 行号与修复方向）+ `test-evidence.md`（红阶段失败证据）+ 红用例 `tests/test_workflow_helpers_update_idempotent.py`（两条用例）
- [x] 定位代码：`LEGACY_CLEANUP_TARGETS` L71-L89 / `_refresh_managed_state` L2140-L2150 / `_sync_requirement_workflow_managed_files` L2541-L2593 / `_load_managed_state` L2052-L2057
- [x] **Step A（bugfix.md 填写）** ✅：Problem Description / Root Cause Analysis（A+B 引用 diagnosis.md）/ Fix Scope（将改 / 不改边界）/ Fix Plan（5 步含判据和顺序）/ Validation Criteria（6 项 checklist）
- [x] **Step 1（根因 B）** ✅：`LEGACY_CLEANUP_TARGETS` 移除 `Path(".workflow") / "context" / "experience" / "index.md"`，加注释
- [x] **Step 2（根因 A）** ✅：`_sync_requirement_workflow_managed_files` 在 `force_managed` 分支之后、兜底 `skipped modified` 之前新增 adopt-as-managed 分支（判据：`relative not in managed_state`）
- [x] **Step 3（红用例转绿）** ✅：`pytest tests/test_workflow_helpers_update_idempotent.py -v` → 2 passed in 1.01s
- [x] **Step 4（全量零回归）** ✅：`pytest --no-header -q` → 146 passed / 50 skipped / 1 failed；唯一 failure `test_smoke_req29` 经 `git stash` 对比验证为 HEAD baseline 下同样 FAIL 的 pre-existing，零新增回归
- [x] **Step 5（手动烟测）** ✅：`/tmp/petmall-bugfix3-smoke` 临时副本 `harness update` 第一次 32 条 `adopted` + 0 条 `skipped modified` + 无 `archived legacy .workflow/context/experience/index.md` + `legacy-cleanup/experience/` 无新增 `index.md-N`；对比 HEAD baseline 的 32 条 `skipped modified` + 循环归档，修复效果验证通过
- [x] Step B：对人文档 `changes/实施说明.md` 产出（按 executing.md 72-86 行模板，字段全 + ≤ 1 页）
- [x] Step C：session-memory.md 追加 executing 阶段条目（本段）
- [x] Step D：action-log.md 顶部追加 executing 阶段条目

### 产出路径

- 代码修复：`src/harness_workflow/workflow_helpers.py`（+15/-1，2 处改动：`LEGACY_CLEANUP_TARGETS` 移除 + `_sync_requirement_workflow_managed_files` 新增 adopt 分支）
- 对人文档：`artifacts/main/bugfixes/bugfix-3-pipx-重装后新项目-install-update-生成数据不正确/changes/实施说明.md`
- bugfix 计划：`artifacts/main/bugfixes/bugfix-3-.../bugfix.md`（五节全填）
- 红绿证据：`pytest tests/test_workflow_helpers_update_idempotent.py -v` → 2 passed；全量 `pytest` → 146 passed / 50 skipped / 1 pre-existing failure
- 工具系统副作用：`.workflow/tools/index/missing-log.yaml` 追加 executing 未命中记录
- action-log：`.workflow/state/action-log.md` 顶部新增 executing 阶段条目

### 衍生发现（上报主 agent，不扩大修复）

- **第二次 update 仍有 3 条 `skipped modified`**（`.workflow/context/experience/index.md` / `.workflow/state/runtime.yaml` / `.codex/skills/harness/SKILL.md`）。根因：`_sync_...` 写完 hash 后，同一次 update 调用里 `_refresh_experience_index` / `save_requirement_runtime` / `install_local_skills` 又把文件改了。属于"多生成器共享文件语义冲突"，**不**属于根因 A/B。HEAD baseline 下也存在（比 fix 后多出 29 条 scaffold 漏登记类的 skipped modified）。建议新开 sug 跟踪"update 幂等性二阶段：解除多生成器 hash 竞争"，不在本 bugfix 范围。
- `adopt` 判据假设"漏登记 = 可信任覆盖"，对"用户手动创建了一个与 scaffold 同名但从未登记的自定义文件"会误覆盖；scaffold_v2 下暴露的文件都是受管模板，用户自建同路径场景在真实使用中概率极低，当前不新增白名单。若未来反例出现再扩展。

### 经验候选（待 acceptance 通过后沉淀到 `context/experience/roles/executing.md`）

- **候选一：managed-state 幂等性的"三态判据"——owned / modified / unregistered 必须各有明确分支**
  - 场景：`_sync_requirement_workflow_managed_files` 需要在每次 update 调用中，对每个 scaffold 文件决定"覆盖 / 跳过 / 采纳"。
  - 经验：这类"状态机 + hash 登记表"的同步函数，必须把目标文件状态分三态处理：
    - **owned**（hash 登记 & 与当前文件匹配）→ 按模板差异 updated / current；
    - **modified**（hash 登记 & 与当前文件不匹配）→ `skipped modified`，保护用户自定义；
    - **unregistered**（hash 未登记）→ adopt-as-managed（用模板覆盖 + 补录 hash），绝不能走 `skipped modified`（否则会像 bugfix-3 一样陷入"永远追不上模板"的死锁）。
  - 合并 owned / unregistered 两态为一条 `force_managed` 或 "hash 匹配" 判据是常见踩坑——当且仅当显式识别 unregistered 态，才能让"老项目 + 新 scaffold"的场景从首次 update 起就进入稳态。
  - 来源：bugfix-3 根因 A 修复
- **候选二：LEGACY_CLEANUP_TARGETS 必须与"活跃再生成器白名单"互斥校验**
  - 场景：`cleanup_legacy_workflow_artifacts` 扫描 `LEGACY_CLEANUP_TARGETS` 列表把文件搬到 `legacy-cleanup/`，但 `_refresh_experience_index` 等 helper 会在同一次 update 调用里把文件重新生成出来。
  - 经验：任何 cleanup target 列表都必须在 code review 阶段检查——**被列入的路径是否在其他 helper 里被活跃再生成**？若是，必须从列表中移除；否则会陷入 "搬家 → 重建 → 搬家" 循环，`_unique_backup_destination` 产生递增垃圾副本。建议在后续迭代中给 LEGACY_CLEANUP_TARGETS 加一条静态检查（import 时扫 `_refresh_*` / 模板生成器的输出清单并断言互斥）。
  - 反例：req-20 tools 目录误清理 + bugfix-3 experience/index.md 循环归档，同类问题出现两次，说明口头 review 不够，需要机制防御。
  - 来源：bugfix-3 根因 B 修复 + 经验三（req-20 tools 误清理）同源延展

### 下一步建议

- 主 agent 推进 testing 复跑：`pytest tests/test_workflow_helpers_update_idempotent.py -v` 应稳 2 passed（已在本阶段验证过）；全量 pytest 应 146 passed + 50 skipped + 1 pre-existing failure（允许容忍）。
- testing 通过后进 acceptance，逐条核对 bugfix.md#Validation Criteria 6 项。
- 衍生问题建议：done 阶段前由主 agent 起 sug 跟踪"update 幂等性二阶段：多生成器共享文件的 hash 竞争消除"（不属本 bugfix，不能在 executing 扩大范围）。

### 上下文消耗评估

- 本 subagent 累计读取文件 ~12 个（workflow_helpers 分 3 次读，其他多数 ≤ 200 行），Edit 3 次（bugfix.md 整体写、workflow_helpers.py 2 处点改）、Write 2 次（实施说明.md / action-log 追加）、Bash 10 次左右（pytest x3 + smoke x2 + git stash x2 + 清理）。
- 预估当前 agent 上下文占比 ~50-60%，接近但未到 70% 阈值。交接给主 agent 后若继续驱动 testing / acceptance，主 agent 层若已超 70% 应 `/compact` 一次；本 subagent 产出已全部持久化到 session-memory / 实施说明 / action-log / bugfix.md，`/compact` 损失风险低。

---

## Acceptance 阶段（2026-04-20，Subagent-L1 acceptance 角色）

### Context Chain（延长）

- Level 0: 主 agent (harness-manager) → stage: acceptance（executing 完成后推进）
- Level 1: Subagent-L1（regression 诊断师）→ 已完成独立诊断（顶部段落）
- Level 1: Subagent-L1（testing 角色）→ 已完成红用例（testing 段落）
- Level 1: Subagent-L1（executing 角色）→ 已完成根因 A+B 修复 + 红→绿 + 烟测（executing 段落）
- Level 1: Subagent-L1（acceptance 角色，本段）→ 任务：对照 bugfix.md Validation Criteria 6 项独立核查，不信任 executing 简报

### 已完成核查项（本阶段）

- [x] Step 0：硬门禁三自我介绍（"我是验收官（acceptance 角色，Subagent-L1）..."）
- [x] 加载角色链：runtime.yaml → tools/index.md → stage-tools.md → project-overview.md → base-role.md → stage-role.md → acceptance.md → evaluation/acceptance.md → experience/roles/acceptance.md
- [x] 硬门禁一：派发 toolsManager（内联匹配 Read/Grep/Glob 为主；Bash 用于独立复跑 pytest 与烟测，briefing 授权）
- [x] 读取全部工件：bugfix.md / regression/diagnosis.md / regression/回归简报.md / test-evidence.md / testing/测试简报.md / changes/实施说明.md / session-memory.md / `git diff HEAD src/harness_workflow/workflow_helpers.py`（16 增 1 删）/ tests/test_workflow_helpers_update_idempotent.py（209 行）
- [x] **条款 #1** ✅：独立跑红用例 `pytest tests/test_workflow_helpers_update_idempotent.py -v` → `2 passed in 0.75s`
- [x] **条款 #2** ✅：独立跑全量 `pytest -q --no-header` → 146 passed / 50 skipped / 1 failed；`git stash push -u src/...workflow_helpers.py tests/test_workflow_helpers_update_idempotent.py` 后在 HEAD baseline 独立跑 `test_smoke_req29::HumanDocsChecklistTest` 同样 FAIL → 确认 pre-existing；`git stash pop` 恢复后红用例仍 2 passed → 零新增回归
- [x] **条款 #3** ✅：`rm -rf /tmp/petmall-bugfix3-acceptance-smoke/` + `cp -R PetMallPlatform ...` + `cd ... && harness update` 两次
  - 基线：副本初始已带 `index.md` + `index.md-2`（历史堆积，不清理范围）
  - Run1：32 adopted / 0 skipped modified / 0 archived legacy
  - Run2：0 adopted / 0 archived legacy / 3 skipped modified（experience/index.md、runtime.yaml、SKILL.md；均非 roles/*.md，属 executing D1 衍生问题）
  - `legacy-cleanup/.../experience/` 仍为 `index.md`+`index.md-2`，**无** `index.md-3` 新增，循环归档已终止
  - 清理：`rm -rf /tmp/petmall-bugfix3-acceptance-smoke/`
- [x] **条款 #4** 内容通过 / 契约偏：`changes/实施说明.md` 字段齐全（23 行）；但 `validate --human-docs --bugfix bugfix-3` 期望落 bugfix 根目录 `实施说明.md`，列入未达项（D3）
- [x] **条款 #5** ✅：session-memory.md L142-L207 为 executing 条目，context_chain 延长、Step 0~D ✅、经验候选 2 条 ≥ 1、衍生问题登记
- [x] **条款 #6** ✅：`.workflow/state/action-log.md` 顶部存在 bugfix-3 executing 条目
- [x] **状态漂移**：runtime.yaml `stage=acceptance` vs bugfix-3 state `stage=acceptance` 一致 ✓
- [x] **代码变更范围边界**：`git diff --stat HEAD` → 代码层仅 `src/harness_workflow/workflow_helpers.py`（+16/-1）；状态元数据 `runtime.yaml` / `missing-log.yaml` / `feedback.jsonl` 为工作流正常副作用；`tests/...update_idempotent.py` Untracked（testing 阶段新增未 commit），符合 bugfix.md Fix Scope"不改红用例"口径
- [x] **对人文档硬门禁**：`harness validate --human-docs --bugfix bugfix-3` → **0/5**（5 份全不达）。原因：3 份对人文档落在子目录 + testing 阶段文件名错为"测试简报"；内容齐全但路径/命名违反 `src/harness_workflow/validate_human_docs.py#BUGFIX_LEVEL_DOCS`
- [x] 产出 `acceptance-report.md`（agent 侧详报：条款逐条 + 证据 + 衍生问题 D1~D4 + 经验候选 2 条）
- [x] 产出 `验收摘要.md`（对人文档，**直落 bugfix 根目录**，按 acceptance.md L69-L82 最小字段模板，3 个字段 + 辅助核查）
- [x] 追加 `.workflow/state/action-log.md` 顶部 acceptance 阶段条目
- [x] 追加本 session-memory.md acceptance 阶段条目（本段）

### 最终结论

**acceptance conditional pass**

- bugfix.md 6 项 Validation Criteria 实质全部 PASS（代码修复独立烟测有效，无新增回归，状态无漂移）
- 但对人文档落盘路径+命名违反 `BUGFIX_LEVEL_DOCS` 契约（0/5），违反 acceptance.md Step 1 硬门禁
- 本 subagent 不自行修复（briefing 执行规则），将 D3 作为阻塞项上报主 agent

### 衍生问题清单（上报主 agent）

- **D1**（executing 已登记）：第二次 update 3 条 `skipped modified`，多生成器共享文件 hash 竞争；建议 done 起 sug
- **D2**（executing 已登记）：`adopt` 判据对用户自建同路径文件误覆盖风险；概率极低，留待反例
- **D3**（本阶段新发现，**阻塞 done**）：对人文档落盘路径/命名不符 BUGFIX_LEVEL_DOCS 契约；建议 `mv regression/回归简报.md ./回归简报.md`、`mv changes/实施说明.md ./实施说明.md`、`mv testing/测试简报.md ./测试结论.md`，然后重跑 validate 应达 4/5（`交付总结.md` 留到 done）
- **D4**（pre-existing）：`test_smoke_req29::HumanDocsChecklistTest` FAIL；req-29 归档 slug 清洗后测试代码未同步，独立追踪

### 经验候选（上报主 agent，由 done 阶段决定是否沉淀）

- **候选一（→ executing.md）**：bugfix 对人文档必须直落 bugfix 根目录，子目录是 agent 过程产物专用。每个 stage 角色产出对人文档后应当场跑 `harness validate --human-docs --bugfix <id>` 自检，不留到 acceptance 才暴露
- **候选二（→ acceptance.md）**：acceptance 独立复跑必须覆盖 pre-existing failure 的 HEAD baseline 验证——`git stash` 回到基线独立复跑同一 failing test，确认同样 FAIL 才算 pre-existing；是对经验一"以工具输出为准"的延展

### 下一步

- **主 agent 接收本报告** → 决定是否先修 D3 再推进 done
- 若主 agent 采纳建议：派 executing subagent 做 mv + 改名 → 重跑 validate 应达 4/5 → acceptance 复核转 pass → `harness next` 进 done
- 若主 agent 不处理 D3：acceptance 停在 conditional pass，不推进 done
- done 阶段：主 agent 起 sug 跟踪 D1

### 上下文消耗评估

- 本 subagent 累计 Read ~18 个文件（多数 ≤ 200 行）、Bash ~15 次（pytest x4 + smoke x2 + git stash x2 + ls/grep/diff 若干）、Edit/Write 3 次（acceptance-report.md / 验收摘要.md / session-memory 追加）
- 预估当前 agent 上下文占比 ~50-55%（未到 70% 阈值），无需 `/compact`
- 所有关键决策、证据、结论均已持久化到 acceptance-report.md / 验收摘要.md / session-memory / action-log，交接给主 agent 后无信息丢失风险
