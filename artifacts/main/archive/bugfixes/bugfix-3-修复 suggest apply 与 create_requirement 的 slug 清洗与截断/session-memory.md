# Session Memory

## 1. Current Goal

- bugfix-3：修复 `suggest --apply` / `create_requirement` / `create_bugfix` 的 slug 清洗与长度截断缺口，叠加 `apply_suggestion` 成功后的源文件归档。

## 2. Context Chain

- Level 0: 主 agent → executing（bugfix-3 派发）
- Level 1: Subagent-L1（开发者，executing 角色）→ 本次 TDD 闭环

## 3. Completed Tasks

- [x] Step 1：TDD 先红 —— 新增 `tests/test_slug_paths.py` 5 条测试，首次运行 5 fail（证明缺陷真实）
- [x] Step 2：源码修复 `src/harness_workflow/workflow_helpers.py`
  - `_path_slug(title, max_len=60)` 新增（L2182~2196，紧邻 `slugify`）
  - `create_requirement` dir_name 清洗（L3278~3284）
  - `create_bugfix` dir_name 清洗（L3342~3346）
  - `apply_suggestion` title 截断 + 源文件 `target.replace(archive_dir/name)` + frontmatter 翻转（L3101~3121）
- [x] Step 3：同步适配老断言
  - `tests/test_cli.py` L1052 / L1059：bugfix 目录从 raw title 改为 kebab-case
  - `tests/test_suggest_cli.py` L138~155：apply 后归档路径断言
  - `tests/test_smoke_req28.py` L305~311：同上
- [x] Step 4：再绿 —— 新增 5 条全绿；全量 `python3 -m unittest discover tests` → 176 tests, 1 failure (pre-existing), 36 skipped，对齐基线零新增回归
- [x] Step 5：对人文档 `实施说明.md` 落盘
- [x] Step 6：action-log 追加条目

## 4. Validated Approaches

- 用 `mock.patch("harness_workflow.workflow_helpers._get_git_branch", return_value="main")` + tempdir 真实写入读回，参考 `tests/test_suggest_cli.py` / `tests/test_smoke_req29.py` 风格；`builtins.input` mock 为 "n" 屏蔽 create_requirement 的交互。
- 先红证明（初次运行 `test_slug_paths` 5/5 fail）：
  - `test_slash_in_title_does_not_create_nested_dir`：产出嵌套 `req-01-清理 .workflow/flow/archive/main/ 目录` 多级
  - `test_long_title_slug_is_truncated_but_state_keeps_original`：slug 段 240 字符未截断
  - `test_whitespace_only_title_falls_back_to_id_only`：`req-01-/???` 含非法分隔
  - `test_slash_in_bugfix_title_does_not_create_nested_dir`：`bugfix-1-修复 a/b/c 路径拆分 bug` 嵌套
  - `test_apply_sug08_style_long_line_produces_flat_dir_and_archives_source`：源文件未归档 + req 目录 3 级嵌套
- 再绿证明：
  - `python3 -m unittest tests.test_slug_paths` → `Ran 5 tests in 0.133s  OK`
  - `python3 -m unittest discover tests` → `Ran 176 tests in 28.713s  FAILED (failures=1, skipped=36)`（failure 为 pre-existing `test_human_docs_checklist_for_req29`，与基线一致）

## 5. Failed Paths

- 无。TDD 首版测试期望"req-01-" 尾带 dash 的变体已在源码阶段修正为 `strip('-')` 后统一回退到 id-only（`req-NN`）。

## 6. Candidate Lessons

```markdown
### 2026-04-20 slug 清洗须在"入口层"统一下沉
- Symptom: title 含 `/` 被 Path 自动拆成多级嵌套目录，污染 artifacts 与 state yaml。
- Cause: create_requirement / create_bugfix 直接 f-string 拼 raw title，未走 slugify_preserve_unicode；create_change / create_regression / rename_* 已正确，但 create 族有漏补。
- Fix: 新增 `_path_slug` helper（复用 slugify_preserve_unicode + 长度上限 60 + strip 末尾 dash），所有 dir_name 生成路径统一走它。
```

## 7. Next Steps

- 主 agent 决定是否推进 `harness next` 或 `harness ff`；本 subagent 不自动切 stage。
- 预估上下文消耗：中（主要读 workflow_helpers.py 与既有测试，新增 1 个测试文件 + 1 份对人文档）。
- 维护建议：当前会话上下文约 50% 余量充足，不建议强制 `/compact`；如主 agent 后续还要连跑 testing/acceptance 在同会话内，可在进入 testing 前做一次 `/compact`。

## 8. Open Questions

- 无，Validation Criteria 全部对齐。

---

## Testing Stage（Subagent-L1, 独立测试工程师，2026-04-20）

### 产出
- 单测补充：`tests/test_slug_paths_extra.py` 新增 4 条（反斜杠+Windows 非法字符 / 多行 title / 同 title 幂等新 id / 无 frontmatter sug 归档），全绿。注明：属覆盖扩展而非"先红后绿"（修复已生效，原漏洞已无法在新码上复现）。
- E2E tempdir：`/tmp/harness-bugfix3-e2e-20260420-115447/`（保留作取证），4 场景全 PASS：
  1. `harness suggest --apply sug-08` → `req-01-清理-workflow-flow-...-早/` 单级；sug 搬 archive；frontmatter `pending`→`applied`；runtime 正确。
  2. `harness requirement "含/斜杠/的 标题"` → `req-02-含-斜杠-的-标题/` 单级；state yaml title 保留原文。
  3. 长 title 72 字 → slug 60 字（恰 max_len）；state yaml title 保留完整 72 字。
  4. `harness bugfix "含/路径/的 缺陷"` → `bugfix-1-含-路径-的-缺陷/` 单级。
- 主仓全量 discover：180 tests / 1 failure (pre-existing test_human_docs_checklist_for_req29) / 0 errors / 36 skipped。零新增回归。
- 对人文档：`测试结论.md` 已落盘（≤ 1 页，最小模板字段齐全）。
- test-evidence.md 已按 Validation Criteria 逐条核对填充。

### 测试结论
bugfix-3 达到 acceptance 门槛。4 条 Validation Criteria 全部 PASS，未发现新缺陷；建议 acceptance 通过后对 `apply_all_suggestions`（workflow_helpers.py L3261）开同类 sug 跟踪——该路径仍用旧 `f"{req_id}-{title}"` 拼接，属本类缺陷的潜在复发点，不在 bugfix-3 范围内。

### 上下文消耗评估
中等（~40% 额度）。主要操作：读 bugfix/实施/diagnosis/testing 相关角色文件、workflow_helpers.py 关键段、slug.py、既有 test_slug_paths.py；1 个新测试文件、1 份对人文档、1 份 test-evidence 填充、session-memory 追加。建议后续 acceptance subagent 在独立 agent 中启动，不与 testing 共用会话。

---

## Acceptance Stage（Subagent-L1, 独立验收官，2026-04-20）

### 硬门禁
- 执行 `harness validate --human-docs --bugfix bugfix-3`：初始 2/5（`实施说明.md` / `测试结论.md`）；本 subagent 产出《验收摘要.md》后升到 3/5。`回归简报.md` 为 regression 阶段遗留，`交付总结.md` 属 done 阶段。已在《验收摘要.md#未达项处理建议》显式列出，建议主 agent 在 done 前后置补齐《回归简报.md》即可，无需回退到 executing。

### 逐条核查结论
- Validation Criteria 6/6 全部 [x]（AC-1~AC-6，详见 `acceptance-report.md`）；
- Regression 根因 4/4 全部修复到位（`apply_suggestion` 截断 / `create_requirement` slug 清洗 / `create_bugfix` slug 清洗 / sug 归档 + frontmatter 翻转）；
- 主仓全量 `python3 -m unittest discover tests` 本轮实跑 → 180 tests / 1 pre-existing failure / 36 skipped / 0 errors，零新增回归（failure=`test_human_docs_checklist_for_req29`，与 bugfix-3 完全解耦，可复现）；
- 状态一致性：`runtime.yaml` `stage=acceptance` ↔ `state/bugfixes/bugfix-3-*.yaml` `stage=acceptance`；无漂移。

### 产出
- `artifacts/main/bugfixes/bugfix-3-.../acceptance-report.md`（agent 侧详细验收报告，含 0 硬门禁章节 / 1 AC 逐条 / 2 根因逐条 / 3 非回归 / 4 状态漂移 / 5 AI 建议 / 6 人工判定项 / 7 产出清单）；
- `artifacts/main/bugfixes/bugfix-3-.../验收摘要.md`（对人文档，≤ 1 页，最小模板字段齐全）。

### AI 侧最终建议
建议通过（acceptance pass）。理由：6/6 AC 全部满足 + 4/4 根因修复到位 + 零新增回归 + 状态一致。

附带建议（不阻断本次验收）：
1. 主 agent 在 done 阶段前后置派发 regression 角色补产《回归简报.md》；
2. 新开 sug 跟踪 `apply_all_suggestions`（L3261）同源风险。

### 上下文消耗评估
低-中（本 subagent 独立会话，约 30%）。主要读取：workflow_helpers.py 关键段落、9 条 slug 单测、test-evidence / 实施说明 / 测试结论 / diagnosis / runtime.yaml / state/bugfixes yaml；1 份 acceptance-report.md、1 份验收摘要.md、session-memory 追加、action-log 追加。无需 `/compact`。建议 done 阶段另开 agent 独立执行六层回顾。

---

## Done Stage（主 agent / 技术总监，2026-04-20）

### 产出
- `done-report.md`：六层回顾完整覆盖，附实现时长（总 ≈3h 22m：regression 11m / executing 19m / testing 2h 21m / acceptance 30m），工具层发现 2 条、改进建议 4 条（全部转 sug 池）。
- `交付总结.md`：对人文档（req 级，≤ 1 页，字段按 done.md 最小模板）。
- `回归简报.md`：主 agent 基于 `regression/diagnosis.md` 补齐 regression 阶段历史遗漏的对人文档（契约 3），不回退 stage。
- sug 池新增 3 条：sug-10（regression 对人文档契约自校验）/ sug-11（`apply_all_suggestions` 同源隐患下沉 `_path_slug`）/ sug-12（`create_suggestion` frontmatter 补齐 title + priority）。sug-09（本轮 done 前由用户 `/harness-suggest` 新增）保留。
- 经验沉淀：`.workflow/context/experience/roles/executing.md` 新增"经验七：title → path 段清洗必须在入口层统一下沉到同一 helper"，包含 5 条经验内容 + 2 条反例 + 来源引用。

### 六层回顾要点
- **Context**：角色行为符合 SOP；经验文件已补 executing 经验七。
- **Tools**：发现 `harness suggest` frontmatter 不完整（契约 6 违反）、`harness next` 不派发下一 stage subagent、`harness validate --human-docs` 前置/后置未分档；已转 sug-09 / sug-12。
- **Flow**：模式 B 五阶段完整走完（regression → executing → testing → acceptance → done），planning 按合规跳过。
- **State**：runtime.yaml ↔ state/bugfixes yaml 一致；无漂移。
- **Evaluation**：testing / acceptance 独立执行；acceptance 独立复跑全量 tests 确认数字，未盲信 testing。
- **Constraints**：硬门禁一~五 + 对人文档契约 1/2/3/4/6 全执行到位。

### AI 侧 done 判定
六层全通过；退出条件全满足。建议人工最终判定 done，择期 `harness archive bugfix-3`。

### 上下文消耗评估
主 agent 本会话累计约 60-65%。done 产出完成后建议 `/compact` 一次再进入归档 / 下一需求。
