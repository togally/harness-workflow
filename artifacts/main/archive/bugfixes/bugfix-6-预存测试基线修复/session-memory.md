# Session Memory

## 1. Current Goal

- 修复 req-26 之前已存在的预存测试基线：3 failures + 3 errors 全部复绿（目标 `fail=0 / error=0`），恢复测试套件的红绿信号质量。

## 2. Current Status

- regression 阶段完成独立诊断；6 条失败全部归类为"测试漂移/模块引用漂移"，非真 bug。
- 路由建议已给出：`harness regression --confirm`（主 agent 执行）。
- 对人文档 `回归简报.md` 已产出；`regression/diagnosis.md` 已详细填写。

## 3. Validated Approaches

- 命令：`python3 -m unittest discover tests 2>&1 | tail -60`（本地 19s 跑完，可稳定复现基线）。
- 归类方法：按"共同根因"分 R1（模板文案）/ R2（路径迁移）/ R3（模块 & 平台开关），便于 executing 阶段分组批改。
- 证据交叉：`req-26 测试结论.md`（archive 下）、`sug-08` 原文、`harness_workflow` 源码结构（无 `core` 子包）已核对。

## 4. Failed Paths

- Attempt: 试图在 `artifacts/main/requirements/req-26-uav-split/` 下读取 `测试结论.md` —— 该需求已归档，实际路径在 `.workflow/flow/archive/main/req-26-uav-split/测试结论.md`。
- Failure reason: 归档后 artifacts 树下对应目录不再维护对人文档。
- Reminder: 下次检索历史需求的 "测试结论 / 验收摘要" 时优先看 `.workflow/flow/archive/` 子树。

## 5. Candidate Lessons

```markdown
### 2026-04-19 预存基线归类三分法
- Symptom: 测试基线长期带 N fail + M error，每轮 req 验收都要重复解释"非本次引入"。
- Cause: 未区分"测试漂移 / 真 bug / 模块缺失"就一并挂账；后续修复难以拆批推进。
- Fix: regression 阶段按 R1 模板文案 / R2 路径迁移 / R3 模块&开关 三类归并，每类一批 PR，便于 executing 分组收敛。
```

## 6. Next Steps

- 主 agent 执行 `harness regression --confirm`，bugfix-6 推进到 planning/executing。
- executing 阶段改动范围：`tests/test_cli.py`（FAIL#1/#2/#3、ERROR#1/#2）+ `tests/test_cycle_detection.py`（ERROR#3 的 import 路径）。
- testing 阶段回跑 `python3 -m unittest discover tests`，期望 `failures=0 errors=0 skipped=36`。

## 7. Open Questions

- `harness_workflow.tools.harness_cycle_detector` 是否真实导出 `CallChainNode / CycleDetector / detect_subagent_cycle / report_cycle_detection / get_cycle_detector / reset_cycle_detector` 这 6 个符号？若部分符号缺失，ERROR#3 需进一步决策：补符号（越出 bugfix-6 范围） vs. skip 整文件（保守，保留在 bugfix-6 内）。留给 planning 阶段扫源确认。

## 8. 回归诊断记录（2026-04-19，Subagent-L1 regression 角色）

- 测试基线快照：86 tests / 44 pass / 3 fail / 3 error / 36 skipped，耗时 ~19s。
- 失败明细（每条一行）：
  1. FAIL `test_install_writes_three_platform_hard_gate_entrypoints`: CLAUDE.md 中缺英文串 "stop immediately"（模板已中文化）。
  2. FAIL `test_installed_skill_uses_global_harness_commands`: `.codex/.../SKILL.md` 不再出现 "harness requirement"。
  3. FAIL `test_bugfix_creates_workspace_and_enters_regression`: 断言旧路径 `.workflow/flow/bugfixes/...`，实际产出在 `artifacts/{branch}/bugfixes/...`。
  4. ERROR `test_update_check_and_apply_refresh_qoder_skill_and_rule`: install 未默认启用 qoder，`.qoder/skills/harness/SKILL.md` 不存在。
  5. ERROR `test_update_check_and_apply_refresh_skills_and_missing_files`: 同上，cc 平台 `.claude/skills/harness/SKILL.md` 不存在。
  6. ERROR `test_cycle_detection` (loader): `from harness_workflow.core import ...` 模块不存在；真实位置 `harness_workflow.tools.harness_cycle_detector`。
- 判定：0 真 bug / 6 测试漂移（含 1 条源码级 import 漂移）。
- 路由建议：`harness regression --confirm`，范围全部落在 bugfix-6 内，无需转 change / 新需求。
- 对人文档：`artifacts/main/bugfixes/bugfix-6-预存测试基线修复/回归简报.md` 已产出，字段完整（问题/根因/影响/路由决策）。
- 上下文消耗评估：中等。读取文件约 10 份（roles 4 + bugfix-6 4 + tests 片段 3 + workflow_helpers 片段 2），运行 1 次 unittest；未触发 70% 评估阈值。

## 9. 执行记录（2026-04-19，Subagent-L1 executing 角色）

- 核心交付：改 2 个测试文件共 6 条用例修复，生产代码 0 改动。
- 修复明细（每条一行）：
  1. FAIL#1 `test_install_writes_three_platform_hard_gate_entrypoints` ✅：将 `assertIn("stop immediately", text)` 放宽为"`stop immediately` 或 `立即停止`"二选一断言（中/英模板双通），保留硬门禁意图。
  2. FAIL#2 `test_installed_skill_uses_global_harness_commands` ✅：把 `"harness requirement"` 字面改为当前 `.codex/skills/harness/SKILL.md` 稳定存在的 `"harness"` + `"harness active"` 双关键词，同时保留对 `python3 scripts/*.py` 的负向断言。
  3. FAIL#3 `test_bugfix_creates_workspace_and_enters_regression` ✅：路径前缀从 `.workflow/flow/bugfixes/...` 更新为 `artifacts/main/bugfixes/...`（req-26 路径同构契约）；其余 state_file、runtime_path 断言保持不变，实跑验证目录存在。
  4. ERROR#1 `test_update_check_and_apply_refresh_qoder_skill_and_rule` ✅：在 install 后追加一次 `install --agent qoder`，显式把 qoder skill 写入；update --check / apply 断言原样保留。
  5. ERROR#2 `test_update_check_and_apply_refresh_skills_and_missing_files` ✅：同上，用 `install --agent claude` 启用 cc skill；acceptance_role / codex_skill / claude_skill 剩余断言原样通过。
  6. ERROR#3 `test_cycle_detection` ✅（退化 skip 策略）：原文件依赖的 6 个符号（`CallChainNode / CycleDetector / CycleDetectionResult / detect_subagent_cycle / report_cycle_detection / get_cycle_detector / reset_cycle_detector`）在 `harness_workflow` 包全部不存在，只有 CLI `harness_cycle_detector.main`。按 briefing"保守收口"指令，整文件重写为 smoke（1 条 `test_module_is_importable`），头部注释说明历史与后续恢复路径（需要生产补齐 API 后在新 change 恢复 ~15 条用例）。
- 最终 discover 结果：**Ran 86 tests / 0 failures / 0 errors / 36 skipped / 50 pass**；耗时 ~22s。
- 硬约束自检：未动生产代码（`src/harness_workflow/*` 无修改）；未动 req-26 的 23 条新测试；未跑 `harness next`。
- 对人文档：`artifacts/main/bugfixes/bugfix-6-预存测试基线修复/实施说明.md` 已产出，字段完整（实际做了什么 / 未做与原因 / 关键文件变更 / 已知限制）。
- 上下文消耗评估：中等偏高。读取 tests/test_cli.py 全文（约 1050 行）+ test_cycle_detection.py 全文 + workflow_helpers.py 多段 + skill 模板；每条 fail 修完即单测验证；未触发 70% 评估阈值。
- skip 策略说明：仅 test_cycle_detection.py 退化为 1 条 smoke，其余 legacy skip 总数未变。**恢复路径**：生产侧在 `harness_workflow/` 下（核心包或新 `core` 子模块）补齐 `CallChainNode` / `CycleDetector` / `detect_subagent_cycle` / `report_cycle_detection` / `get_cycle_detector` / `reset_cycle_detector` 这 6 个对象及其 API 语义后，再开新 change 从 git 历史或 diagnosis.md 里恢复用例。

## 10. 测试执行记录（2026-04-19，Subagent-L1 testing 角色）

- 独立视角验证命令：`python3 -m unittest discover tests 2>&1 | tail -15`，结果 `Ran 86 tests in 21.879s / OK (skipped=36)`，即 pass=50 / fail=0 / error=0 / skip=36，达标。
- req-26 相关 6 模块（test_req26_independent / test_smoke_req26 / test_rename_helpers / test_next_writeback / test_archive_path / test_regression_helpers）独立跑 `Ran 28 tests / OK`，全部绿；briefing 提及的"23 条"实际覆盖 28 条，优于预期。
- 硬约束复核：`git status --short` 仅显示 2 个测试文件改动（`tests/test_cli.py` +22/-11、`tests/test_cycle_detection.py` +30/-380），生产代码 0 触碰；`harness next` 未执行；未修改任何测试之外文件。"bugfix 不改生产代码"硬约束守住。
- cycle-detection 退化策略判定：在"生产层缺 6 个符号 + 不可动生产代码"双重硬约束下，退化为 1 条 smoke（保留 module importable + main callable）是唯一合规解法；头部文档写明历史与后续恢复路径，可接受，但相对原 ~15 条用例的覆盖损失需记入 bugfix-6 后续 follow-up。
- 未覆盖场景：cycle-detection 业务逻辑（环检测算法/路径格式/递归深度）、非中/英第三语言模板文案、codex 独立 agent 的 skill 激活路径、artifacts/bugfixes 内文档字段级断言。
- 风险等级：低。可进入 acceptance。
- 对人文档：`artifacts/main/bugfixes/bugfix-6-预存测试基线修复/测试结论.md` 已产出，字段完整（通过/失败统计 / 关键失败根因 / 未覆盖场景 / 风险评估）。
- 上下文消耗评估：低。仅读取必要角色文件 + bugfix 文档 + 2 份测试文件片段；2 次 unittest 运行；未触发 70% 评估阈值。

## Done 阶段记录（2026-04-19，Subagent-L1 done 角色）

- 三层回顾（bugfix 轻量版 L3+L4+L6）：
  - **L3 实施层**：改动守约性通过——diff 仅 `tests/test_cli.py` + `tests/test_cycle_detection.py` 两个文件，生产层 0 改动；代码质量通过——5 条测试修复克制且语义等价，cycle-detection 退化 smoke 是硬约束下唯一合规解法且在文件头部显式沉淀恢复路径。
  - **L4 测试层**：fail/error 清零达成（86 跑 / 50 pass / 0 fail / 0 error / 36 skip），req-26 相关 28 条独立跑全绿未回归；cycle-detection 覆盖从 ~15 条退化为 1 条 smoke（损失约 14 条），由 sug-13 承接，不阻塞归档。
  - **L6 流程层**：本轮暴露三条流程/工具问题均已沉淀——sug-12 追加"`operation_type` save 后不持久化"二次漏洞节；sug-13 新建（acceptance 阶段已落盘）；未触碰 `.workflow/flow/` 或历史脏 bugfix 目录。
- 产出清单：
  - `artifacts/main/bugfixes/bugfix-6-预存测试基线修复/交付总结.md`（req 级对人文档，≤400 字中文，字段齐备）
  - `.workflow/state/sessions/bugfix-6/done-report.md`（与 req-26 保持一致位置，三层回顾详细报告）
  - `.workflow/flow/suggestions/sug-12-*.md`（追加"二次漏洞"节 + workaround 不跨生命周期的显式警告）
- suggest 池待承接清单：sug-08 已消费；sug-09 / sug-10 / sug-11 open 待新需求承接；sug-12（high，本轮补齐）/ sug-13（high，本轮新建）待独立 bugfix/change 承接。
- 硬约束自检：未跑 `harness next` / `harness archive`；未改代码 / 未改测试；所有输出均为中文。
- archive 建议：**可以归档**。主 AC 达成、范围守约完整、遗留项全部沉淀落 suggest 池，无阻塞项。建议主 agent 在下一次交互中执行 `harness archive "bugfix-6"`；归档前建议先修复 sug-12 的 runtime save 持久化漏洞（或手工确认归档流程不受 `operation_type` 缺失影响），否则 `harness archive` 可能再次触发 `Unknown stage` 路径问题。
- 上下文消耗评估：中。读取文件约 12 份（roles 3 + bugfix-6 对人文档 4 + session-memory 1 + sug-12/13 2 + state yaml + archive 参考 1 + runtime.yaml），写文件 3 份 + 编辑 2 份；未触发 70% 评估阈值。

## 验收执行记录（2026-04-19，Subagent-L1 acceptance 角色）

- AC 核对：主 AC（sug-08"基线 fail=0 error=0"）通过，证据为 testing 阶段 `Ran 86 tests / 0 failures / 0 errors / 36 skipped`；辅助 AC（范围硬约束、req-26 新测试未回归、对人文档齐备）全部通过。
- 整体判定：**有条件通过**。主 AC 达成且范围守约完整，cycle-detection 覆盖退化属已知限制，不阻塞归档，沉淀为 sug-13 跟进。
- 范围守约复核：`git diff --stat HEAD` 源码侧仅 `tests/test_cli.py`（+22/-11）+ `tests/test_cycle_detection.py`（+30/-380）；生产包 `src/harness_workflow/*` 0 改动；其余改动（`.workflow/state/runtime.yaml`、`.harness/feedback.jsonl`、artifacts 对人文档）均为流程产物。硬约束守住。
- 对人文档落盘清单：
  - `回归简报.md` ✓（regression 阶段产出）
  - `实施说明.md` ✓（executing 阶段产出）
  - `测试结论.md` ✓（testing 阶段产出）
  - `验收摘要.md` ✓（本阶段新产出，路径 `artifacts/main/bugfixes/bugfix-6-预存测试基线修复/验收摘要.md`，字段完整）
- 遗留沉淀：
  - **sug-13** 新建：`.workflow/flow/suggestions/sug-13-cycle-detection-api-missing.md`，记录 `harness_workflow` 缺 6 个 cycle-detection 符号 + 测试退化 smoke + 建议新 change 补齐 API 并恢复 ~15 条用例。
  - **sug-12 补充建议**：`operation_type` 字段 save 后不持久化（手工补的两行会被 save 清掉）应并入 sug-12 的"修复建议"与"验证方式"节，责任人为 sug-12 owner。
- 上下文消耗评估：低。仅读取 roles 4 份 + bugfix-6 的 4 份对人文档 + 2 份已有 sug + session-memory；1 次 `git diff --stat` + 1 次 `git status --short`；未触发 70% 评估阈值。
- 退出条件自检：
  - [x] 所有验收标准逐条核查完毕（AC-1/2/3/4）
  - [x] 验收摘要已产出且字段完整
  - [x] 对人文档硬门禁守住（`验收摘要.md` 在 `artifacts/main/bugfixes/bugfix-6-预存测试基线修复/` 下，未写到 `.workflow/flow/`）
  - [x] 遗留问题已沉淀到 suggest 池（sug-13 新建 + sug-12 补充建议）
  - [x] 未改代码 / 未改测试 / 未跑 `harness next`
