# Testing Stage Experience

## 经验一：预存测试失败必须随模板演进同步修复

### 场景

当 CLI 行为、目录结构或核心流程发生演进后，`tests/test_cli.py` 等预存测试出现失败。

### 经验内容

模板/产品演进后，旧测试断言往往会失效。长期放任失败会：

1. **降低测试可信度**——开发者对红灯麻木，真正的问题被掩盖
2. **增加回归风险**——后续改动在已有失败基线上难以判断是否引入新问题
3. **拖累交付节奏**——每次发版前都要临时处理堆积的失败

修复策略：
- **行为变更导致的失败** → 更新断言以匹配新行为
- **已移除功能的测试** → 直接删除，不要保留无意义的失败
- **新增功能的缺失覆盖** → 补充对应测试用例
- **批量失败时先分类** → 按失败原因分组，统一修复模式

### 反例

将 4 个预存测试失败搁置多轮需求，导致后续每次执行测试前都需要先确认"哪些是已知的"。

### 来源

req-19 — 修复 `tests/test_cli.py` 中与模板演进相关的 4 个失败用例

---

## 经验二：测试是产品行为的同步文档

### 场景

产品功能或命令参数发生变更时。

### 经验内容

测试代码不只是"验证逻辑"，更是产品行为的**可执行文档**。当行为变化时：

- 优先修改测试以反映新行为，而不是注释掉或跳过
- 如果旧行为有意的兼容性被破坏，应在测试中断言新的错误提示或替代路径
- 删除与已移除功能强耦合的测试，避免维护僵尸代码

### 反例

某命令参数被移除后，对应的测试仍然期望旧参数存在，导致持续失败；最终选择跳过该测试，而非清理或更新。

### 来源

req-19 — `test_version_with_empty_name_fails` 随版本命令移除而被删除

---

## 经验：dogfood fallback 处理——旧契约工件无 plan §测试用例设计 时如何独立补 + 标注（bugfix-6 引入）

### 场景

执行 testing 阶段时，发现：
- **req 流程**：上游 plan.md 因历史 / 遗忘 / 跨契约引入时机问题缺 §测试用例设计 段；
- **bugfix 流程**：上游 diagnosis.md 因 regression 阶段在 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 引入 C1 之前完成，缺 §测试用例设计 段（典型 dogfood 边界：本 bugfix 自身就是引入该契约的载体）。

### 经验内容

**fallback 路径**：

1. **不阻塞**：testing 不能因为上游缺段就 abort；走独立设计 + 显式标注路径。
2. **独立补充时**：testing 自行设计用例（继承 testing.md Step 2.5 末尾"testing 仍可独立补充反例 / 边界用例"例外子条款），但**必须**在 test-evidence.md 头部第一段显著标注："本 testing 是旧契约 fallback 路径"+ 说明原因（哪个契约引入 / 为什么本周期还没赶上）+ 承诺"X+1 周期起应消费 plan/diagnosis §测试用例设计，不再 fallback"。
3. **矩阵列字段**：在测试矩阵表的"子项"列标注"（testing 独立补）"标签，让 reviewer / acceptance / done 阶段能 grep 出所有 fallback 项目，统计 dogfood 边界规模。
4. **缺陷登记单独成段**：fallback 期间发现的真实缺陷必须独立登记，不能和"上游契约缺段"混淆——前者是业务缺陷需 follow-up，后者是契约债务需 sug 跟进。

**何时不应 fallback**：

- 上游契约**已**引入但 analyst / regression **故意跳过**未产出 → 应触发 regression 回调而非 fallback（fallback 是"契约本身刚引入还没渗透"专属，不是"角色失职"兜底）。
- 跨多个 stage 都缺段 → 升级为 bugfix 修复，不在 testing 单 stage 内自行兜底。

### 反例

- testing 独立补但不标注 → acceptance / done 阶段无法识别哪些用例是"上游设计"哪些是"testing 独立补"，dogfood 边界 invisible。
- testing 用 fallback 路径吸收上游应做的"波及接口完整性"判定 → 上游 analyst / regression 失职被 testing 掩盖，根因长期不浮现。

### 来源

bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））— testing 阶段 test-evidence.md 第 3 行 dogfood fallback 标注 + B2 testing.md Step 2 改写后的过渡期处理样本

## 经验三：文档验证不能替代实际工具运行

### 场景

req-22 的 V1~V5 测试主要依赖文档结构检查和静态引用扫描，结果全部通过。但当真正运行 `harness init` 和 CLI 测试时，发现 scaffold 模板严重不同步、lint 脚本检查的是已废弃的旧架构路径。

### 经验内容

静态检查（文档完整性、路径一致性、grep 引用扫描）只能验证"文件是否存在、引用是否对齐"，无法发现以下问题：

1. **scaffold 模板与代码库脱节** — 新文件未复制、旧目录未重命名、package-data 未更新
2. **lint 脚本逻辑过时** — 检查的路径在文档层面不存在，但脚本本身仍能"正常运行"（只是结果错误）
3. **package 安装未生效** — `pyproject.toml` 修改后未 reinstall，运行时仍加载旧代码

因此，任何涉及 CLI、模板、lint 工具的变更，**必须包含至少一次端到端的实际运行**：

- 在临时目录新建空项目 → 初始化 → 运行核心命令
- 运行 lint 脚本并确认结果正确（不仅是"不报错"）
- 运行预存测试脚本确认全部通过
- 添加"多余配置"（额外文件、自定义目录）后再次运行，验证兼容性/容错性

### 反例

V5 之前所有测试都通过，但 `harness init` 生成的新项目缺少 `role-loading-protocol.md`、`stage-role.md` 等核心文件，且 `experience/stage/` 仍是旧目录名。这些问题只有实际运行才能暴露。

### 来源

req-22 — 第五次 regression 修复中的端到端工具验证

---

## 经验四：lint 脚本和 scaffold 模板必须随架构演进同步更新

### 场景

当架构从 v1 演进为 v2 后，`.workflow/versions`、`.workflow/context/rules/agent-workflow.md` 等路径被废弃，但 `tools/lint_harness_repo.py` 仍在检查它们；scaffold_v2 也保留了旧目录结构和旧版 `context/index.md`。

### 经验内容

架构演进时，有三类产物最容易被遗漏，必须建立强制同步清单：

1. **lint/验证脚本** — 任何被脚本硬编码检查的路径、文件名、目录结构变更后，脚本必须同步更新
2. **scaffold/模板文件** — 新增、重命名、删除的文件必须同步到模板，不能依赖"以后补"
3. **package-data / MANIFEST** — Python 包的 `pyproject.toml` 或 `setup.py` 中的 `package-data` 必须包含新增模板路径，否则安装后运行时找不到文件

修复策略：
- 将 lint 脚本的检查列表设计为"正向清单"（检查必须存在的文件），而非"负向清单"（检查禁止存在的文件），这样架构废弃路径不会残留在脚本中
- 每次架构变更后，执行一次"模板差异对比"：`diff -r .workflow/ scaffold_v2/.workflow/`
- 将 `pyproject.toml` 的 `package-data` 纳入 checklist 的"工具与配置一致性"检查项

### 反例

`lint_harness_repo.py` 在当前仓库运行时直接报出 9 个缺失项，但这些缺失项绝大多数是已废弃路径。如果只看"脚本报错了"，会误判为当前仓库有问题；如果只看"脚本能运行"，又会误导用户认为仓库不健康。

### 来源

req-22 — `lint_harness_repo.py` 重写与 `scaffold_v2` 同步修复

---

## 经验五：AC 可降级为静态契约，但必须有运行时闭环路径

### 场景

req-26 的 AC-06 是"各 stage 角色在真实会话中按契约产出 7 份对人文档"，本质是 agent 行为，而非 helper 函数行为。chg-06 smoke 把 AC-06 降级为三项静态契约（stage-role.md 含契约章节、7 个角色各有对人文档条目、scaffold_v2 与 roles/ 文本一致），未验证 agent 实际落盘。

### 经验内容

当 AC 的验证对象是 agent 运行时行为而非代码行为时：

1. **允许降级为静态契约**——前提是静态契约本身完整覆盖规格（字段名、字段顺序、路径前缀、反例排除清单等）。
2. **必须在测试结论 / 验收摘要中显式标记"未覆盖场景"**——不能以静态通过冒充运行时通过，参见 req-26 `测试结论.md` 第 13-17 行的"未覆盖场景"节。
3. **必须规划下一步运行时闭环**——在 done 阶段转 suggest（sug-09）或约定下一个需求作为首次完整示范（sug-11），把"静态 → 运行时"的缺口作为独立行动项承接。
4. **验收时必须至少抽查一次实际落盘**——即使不在 smoke 里写测试，acceptance 阶段应 `ls artifacts/{branch}/...` 核对对人文档是否真实存在，不仅依赖代码 grep。

### 反例

若只做静态契约不补运行时验证，agent 可能"角色文件写了硬门禁但实际不执行"，契约在代码层通过、在行为层失效——sug-06 的机制价值归零。

### 来源

req-26 — AC-06 双轨对人文档机制 / chg-06 smoke 降级为静态契约

---

## 经验：bugfix-6 新契约下消费 plan.md §测试用例设计 + 独立反例补充实操

### 场景

bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））B2 修复点要求 testing 角色「直接消费 plan.md §测试用例设计」而非自行设计；同时仍需补充独立反例以保证测试反向覆盖。

### 经验内容

req-43（交付总结完善）testing 实操要点：

1. **直接消费 plan.md 用例表**：5 chg plan.md §测试用例设计段共 39 条用例（chg-01 8 条 / chg-02 7 条 / chg-03 8 条 / chg-04 8 条 / chg-05 8 条），testing 阶段用 executing 已写的 pytest（test_req43_chg{01..05}.py）跑，无需重新设计；
2. **独立反例补充必要**：每个 chg 补 1-2 条 plan.md **未列**的反例（共 9 条），覆盖：(a) 非法入参（如 task_type=unknown_type）；(b) 边界条件（如 usage dict 缺 total_tokens / 同 stage 多次写 exited_at / 完全不存在的 req-id / 0 字节 yaml）；(c) 状态字段必检（如 done.md bugfix 模板必须含修复了什么/修复验证 + 不含 chg-NN）；
3. **dogfood 实测必跑**：plan.md 用例可能是 mock fixture 通过，dogfood 实测才发现真实链路缺口；req-43 chg-01 dogfood 实测 = `usage-log.yaml` 不存在，由此暴露 L-01 followup → 转 sug-39（chg-01 派发钩子真实接通 record_subagent_usage）；
4. **followup vs 缺陷的判定**：helper 实现正确（pytest 全过）+ 文字契约升格但运行时未接 → 标 followup（PASS-with-followup）；helper 实现错误 / 契约失效 → 标 缺陷（FAIL）；req-43 chg-01 属前者；
5. **合规扫描 5 项常态化**：R1 越界 / revert 抽样 / 契约 7（id+title）/ req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet）） 映射回归 / req-30（slug 沟通可读性增强：全链路透出 title）model 透出 — 每 req testing 阶段必跑，且不计入 plan.md 用例数（独立的 testing 流程要求）。

### 反例

- 只跑 plan.md 用例不补独立反例 → 边界 / 非法入参 / 状态字段必检漏覆盖；
- 不跑 dogfood 实测 → mock 通过但真实链路断 → 直到下个 req 用到时才暴露（req-42 实证：未跑 dogfood，usage-log 缺失被晚发现一轮）；
- 把 followup 标为 FAIL → 阻断 acceptance / done，过度 conservative；把缺陷标为 followup → 隐藏问题，质量退化。

### 来源

req-43（交付总结完善）— testing 阶段 5 chg PASS / 9 独立反例补充 / 5 项合规扫描 + L-01 followup 判定（test-report.md）

---

## 经验：CLI bug 修复 dogfood 实跑验证（mock + inline 脚本两栈互证）

### 场景

CLI bug 修复 req（如 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 的 apply / apply-all / rename 三 CLI 路径修复）测试时，pytest 用例可能用 fixture 隔离环境通过，但真实仓库链路是否跑通仍需实证。

### 经验内容

req-44 testing 阶段 dogfood 实跑实操：

1. **mock seed sug 全链验证**：seed 一条 sug-99（带 frontmatter title + DOGFOOD-BODY-MARKER），调 `apply_suggestion` → 校验 (a) req title 来自 frontmatter（不是 content 头）；(b) requirement.md 含 DOGFOOD-BODY-MARKER；(c) sug 已 archive；
2. **mock rename 跨字段验证**：调 `rename_requirement(cur_req, "Renamed Dogfood Req")` → 校验 (a) 三处目录（artifacts/ + state/ + .workflow/flow/）都改名；(b) `runtime.yaml.current_requirement_title = "Renamed Dogfood Req"`；
3. **inline python3 脚本承载**：dogfood 不必落 tests/ 目录新文件，可写一段 inline 脚本调 helper 直跑，校验后输出 `[dogfood] all assertions passed ✅`；
4. **dogfood 跑后清理**：seed 的 mock req / sug / runtime 字段须 revert 回原状（避免污染下一阶段 acceptance 抽样基线）。

### 反例

- 只跑 pytest 不跑 dogfood → mock fixture 通过但真实仓库的 `_use_flow_layout` / `resolve_requirement_root` 路径未实证 → bugfix-6 后路径不匹配类 bug 再次复发风险；
- dogfood 跑后不清理 → 下一阶段 acceptance 抽样到的 runtime / 文件已被 dogfood 改写，污染验收基线。

### 来源

req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） — testing 阶段 2 dogfood 实跑（apply 全链 + rename runtime 同步）实证 plan.md TC + 反例之外的真实链路

---

## 经验：testing 阶段红线 — 破坏性 git 命令禁用 + dogfood tmpdir mock 强制（req-45 引入）

### 场景

testing 阶段在 revert dry-run / 回滚抽样 / dogfood 实跑等场景下，可能直接对**当前仓库工作区**实跑 `git restore` / `git reset --hard` / `git checkout .` / `git clean -f` / `git branch -D` 等破坏性命令。req-45（harness next over-chain bug 修复（紧急）） 1st testing 实证：testing subagent 在 revert dry-run 步骤跑 `git restore .`，丢失 src/harness_workflow/workflow_helpers.py + validate_contract.py 全部 executing 改动（`_is_stage_work_done` helper / `check_stage_work_completion` / `run_contract_cli` 分支），触发 BUG-03 P0 Critical，需 regression 路由后 2nd executing 重做 + commit b64bcd7 + push。

### 经验内容

**红线（不可越过）**：

1. **任何破坏性 git 命令在 testing 阶段一律禁止对当前仓库工作区操作**：
   - 禁用清单：`git restore` / `git reset --hard` / `git checkout .` / `git checkout HEAD --` / `git clean -f` / `git branch -D` / `git push --force` 等会销毁工作区或历史的命令。
   - 与 base-role 硬门禁四例外条款 (i) 数据丢失风险并列生效——但本红线对 testing 阶段更严格：例外条款 (i) 是"写入前确认"，testing 红线是"绝对禁用"，不允许"用户确认后执行"。
2. **dogfood 实跑必须用 tmpdir mock 工作区**：
   - 模式：`tempfile.mkdtemp()` + 手工构造 `.workflow/state/runtime.yaml` + `.workflow/flow/requirements/{req-slug}/...` 关键产物 + 直调 helper（如 `workflow_next(tmpdir_root)` / `_is_stage_work_done(...)`）。
   - 不动当前仓库 git 状态：`git status` 在 dogfood 前后必须保持无新增 / 无修改 / 无删除（除主动落 testing 产物如 `test-report.md`）。
3. **revert 抽样改用 stash/log 只读检视**：需要验证"修复前后行为差异"时，用 `git log --oneline` / `git show {sha}` / `git diff {sha}^..{sha}` 等只读命令对比，不实跑 revert。

**自检方法**：

- testing subagent 退出前 grep `.workflow/state/action-log.md` 本 stage 段是否含禁用命令字串，命中即视为红线违反，必须 regression 路由 + executing 重做。
- 长期：建议补 lint `harness validate --contract testing-no-destructive-git`（sug-51（1st testing 跑 git restore 擦 src/ 事故 — testing 红线 + safer dogfood 协议） 跟踪），扫 testing 阶段 action-log。

### 反例

- testing 跑 `git restore .` 想"恢复 dogfood 试探的临时改动"→ 实际擦了 executing 真实工件 → BUG-03 P0 Critical → regression + 2nd executing 重做 + commit b64bcd7 + push（典型反例 = req-45 1st testing）。
- dogfood 直接在当前仓库 `harness next`（不用 tmpdir mock）→ runtime.yaml 被改写 / artifacts 被产 / git 状态被污染 → acceptance 抽样基线漂移。

### 来源

req-45（harness next over-chain bug 修复（紧急）） — 1st testing `git restore .` 事故 + sug-51（1st testing 跑 git restore 擦 src/ 事故 — testing 红线 + safer dogfood 协议）

---

## 经验：CLI bug 修复类 chg dogfood 实跑模板（unit 全绿 ≠ dogfood pass，req-45 引入）

### 场景

修复 verdict-driven stage / `harness next` / `harness validate` / `harness suggest` 等 CLI 自身行为类 bug 时（如 req-45（harness next over-chain bug 修复（紧急）） chg-01（verdict stage work-done gate + workflow_next 集成）），unit 测试可能用 fixture / mock 通过，但真实 CLI 链路（`workflow_next` while 循环 / 第一格 `_write_stage_transition` / `_get_exit_decision`）是否实际跑通还需 dogfood 实证。req-45 1st testing 9 unit 全过但 dogfood 跑 `harness next` 暴露 BUG-01（gate 插桩位置错），凸显 unit pass != dogfood pass 的根本鸿沟。

### 经验内容

**dogfood 标准流程模板**（CLI bug 类 testing 必跑）：

1. **构造 tmpdir mock 工作区**：
   ```python
   import tempfile, yaml
   from pathlib import Path
   tmpdir = Path(tempfile.mkdtemp())
   (tmpdir / ".workflow/state").mkdir(parents=True)
   (tmpdir / ".workflow/flow/requirements/req-99-mock-bug").mkdir(parents=True)
   yaml.safe_dump({"current_requirement": "req-99", "stage": "testing", ...},
                  (tmpdir / ".workflow/state/runtime.yaml").open("w"))
   ```
2. **关键产物 mock 缺失场景**（验 gate 阻断）：
   - testing → 不创 `test-report.md`；
   - acceptance → 不创 `acceptance/checklist.md`；
   - executing → chg/session-memory.md 不含 ✅；
3. **直调 helper 断言落点**：
   ```python
   from harness_workflow.workflow_helpers import workflow_next
   rc = workflow_next(tmpdir)
   final_runtime = yaml.safe_load((tmpdir / ".workflow/state/runtime.yaml").read_text())
   assert final_runtime["stage"] == "testing"  # 第一格 gate 阻断，未跳 acceptance
   ```
4. **stdout 断言含禁止跳转提示**：捕获 stdout 含 `"Stage testing 工作未完成"` 等 gate 阻断文字。
5. **与 unit TC 并列**：plan.md §测试用例设计应**同时**含 unit TC（`tests/test_*.py` mock fixture 通过）+ dogfood TC（如 TC-D-01 dogfood 实测 over-chain 阻断），缺 dogfood TC 视为 testing 设计不全。

**何时必跑 dogfood**：

- chg 修改影响 `harness next` / `harness validate` / `harness suggest` / `harness rename` / `harness install` / `harness update` 等 CLI 行为；
- chg 修改 `workflow_helpers.py::_get_exit_decision` / `workflow_next` / `validate_contract.py` 等 stage 流转 / 契约 lint 入口。

**何时可豁免 dogfood**：

- 纯文档 chg（`.workflow/context/roles/*.md` / `.workflow/flow/*.md` 改写）+ 不接 CLI；
- 纯重构（行为不变 + 测试不变 + 全量回归 0 new fail）。

### 反例

- 9 unit 全过就报 PASS 不跑 dogfood → BUG-01 类 over-chain 漏发现 → 主 agent / 用户后续真跑时才暴露 → regression 路由 + 二次 testing（典型反例 = req-45 1st testing）。
- dogfood 用 `harness next` 直接跑当前仓库（不 tmpdir mock）→ 同时违反 testing 红线（git 状态被污染 + runtime 被改写），需补救 + acceptance 抽样基线漂移。

### 来源

req-45（harness next over-chain bug 修复（紧急）） — 2nd testing dogfood tmpdir mock + workflow_next 直调 + stdout / stage 双断言模板 + sug-52（dogfood 验证机制成熟度 — testing 标准 dogfood 实跑流程模板）
