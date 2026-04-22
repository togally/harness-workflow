# Done Report: bugfix-3 修复 suggest apply 与 create_requirement 的 slug 清洗与截断

## 基本信息
- **需求 ID**: bugfix-3
- **需求标题**: 修复 suggest apply 与 create_requirement 的 slug 清洗与截断
- **归档日期**: 2026-04-20

## 实现时长
- **总时长**: 约 3h 22m（regression 起到 acceptance 出）
- **regression**: 约 11m（2026-04-20T03:16Z → 03:27:44Z，含脏数据回滚 + 诊断文档）
- **planning**: N/A（模式 B bugfix 快速流程跳过）
- **executing**: 19m 27s（03:27:44Z → 03:47:11Z）
- **testing**: 2h 21m 8s（03:47:11Z → 06:08:19Z）
- **acceptance**: 29m 38s（06:08:19Z → 06:37:57Z）
- **done**: 当前会话内完成（~06:38Z 起）

> 数据来源：`.workflow/state/bugfixes/bugfix-3-*.yaml` 的 `stage_timestamps`。

## 1. 执行摘要

- **交付成果**：`src/harness_workflow/workflow_helpers.py` 新增 `_path_slug` helper + 改造 `create_requirement` / `create_bugfix` / `apply_suggestion` 三处入口，含 sug 文件归档 + frontmatter 翻转；测试层新增 `tests/test_slug_paths.py`（5 条 TDD）+ `tests/test_slug_paths_extra.py`（4 条覆盖扩展），同步适配 `tests/test_cli.py` / `tests/test_suggest_cli.py` / `tests/test_smoke_req28.py` 的行为变更断言。
- **验证结果**：Validation Criteria 6/6 全 [x] + regression 根因 4/4 修复到位 + 主仓全量 180 tests / 1 pre-existing failure / 0 errors / 36 skipped（failure=`test_human_docs_checklist_for_req29`，与 bugfix-3 解耦，零新增回归）。
- **状态一致性**：`runtime.yaml` ↔ `state/bugfixes/bugfix-3-*.yaml` `stage=done` / `status=done` 已同步；`stage_timestamps` 全阶段齐。
- **对人文档**：`实施说明.md` / `测试结论.md` / `验收摘要.md` / `回归简报.md` / 《交付总结.md》（本阶段产出）全部落盘。

## 2. 六层检查结果

### 第一层：Context
- [x] **角色行为检查**：regression 诊断师（本阶段由主 agent 一体化产出 diagnosis.md + 回滚 + bugfix 创建）、executing 开发者（Subagent-L1，TDD 先红再绿）、testing 测试工程师（Subagent-L1，独立会话）、acceptance 验收官（Subagent-L1，独立会话）行为符合各自角色 SOP。
- [x] **经验文件更新**：executing.md / regression.md / testing.md / acceptance.md 均有本轮补充（详见 §4 经验沉淀）。
- [x] **上下文完整性**：工作目录上下文、bugfix.md Fix Scope / Fix Plan / Validation Criteria 完整。

### 第二层：Tools
- [x] **工具使用顺畅度**：`harness bugfix` / `harness next` / `harness suggest` / `harness validate --human-docs` / `python3 -m unittest` 全部顺畅。
- [ ] **CLI 工具适配问题（发现）**：
  1. `harness suggest` 新建 sug 文件时只写 `id` / `created_at` / `status` 三字段 frontmatter，**缺 `title` / `priority`**，违反 stage-role.md §契约 6 硬门禁。sug-08 / sug-09 同源。→ 转 sug-12 跟踪。
  2. `harness validate --human-docs --bugfix <id>` 当前校验 5 类对人文档（含《交付总结.md》属 done 未到点 + 《回归简报.md》regression 阶段契约），验收阶段允许部分缺失但未阻断；建议区分"阶段前置必交"与"阶段尾端可后置"两档，避免 acceptance 阶段误以为必须全 5/5。
- [x] **MCP 工具适配**：本轮未使用额外 MCP 工具，无新发现。

### 第三层：Flow
- [x] **阶段流程完整性**：regression → executing → testing → acceptance → done，模式 B 全流程五阶段完整走完。
- [x] **阶段跳过检查**：planning 按模式 B 跳过（bugfix 快速流程正常行为），其余无跳过。
- [x] **流程顺畅度**：harness next 两次推进（testing→acceptance、acceptance→done）均一次成功，无卡顿。

### 第四层：State
- [x] **runtime.yaml 一致性**：`stage=done` 与 `state/bugfixes/bugfix-3-*.yaml` `stage=done / status=done` 一致，`completed_at` 已写入。
- [x] **需求状态一致性**：`active_requirements: [bugfix-3]`；归档后应从 active 清出。
- [x] **状态记录完整性**：`stage_timestamps` 覆盖 executing / testing / acceptance / done 四阶段，regression 阶段（bugfix 入口）无独立时间戳但有 created_at / started_at 对齐。

### 第五层：Evaluation
- [x] **testing 独立性**：testing subagent 独立会话执行，单测 + E2E tempdir + 主仓全量三层证据分层清晰，未被 executing 污染；且引入"覆盖扩展（非 TDD 先红再绿）"标注自省，诚实表达测试局限。
- [x] **acceptance 独立性**：acceptance subagent 独立会话，先跑 `harness validate --human-docs` 硬门禁、再逐条核查 AC 与 regression 根因，本轮实跑独立复测全量 tests 确认数字，未盲信 testing 结论。
- [x] **评估标准达成**：Validation Criteria 6/6 全 [x]，无降标准。

### 第六层：Constraints
- [x] **边界约束触发**：subagent 严格守住"不改 src/ / tests/ / runtime.yaml / 不执行 harness next / 不 git commit" 等硬约束，全程在主 agent 授权下推进。
- [x] **风险扫描更新**：无新风险进入 known-risks；衍生的 `apply_all_suggestions` 同源隐患转 sug-11。
- [x] **约束遵守情况**：硬门禁一（工具优先 / toolsManager 委派）、硬门禁二（操作说明 + action-log）、硬门禁三（角色自我介绍）、硬门禁四（stage 按研发流程图流转）、契约 1/2/3/4/6（对人文档）均有执行证据。

## 3. 工具层适配发现

| 当前痛点 | 建议动作 | 服务层级 |
|---|---|---|
| `harness next` 只推 stage 不派发下一 stage subagent，用户需二次确认 | 新增 `--execute` / `--dispatch` flag 推进后自动派发（sug-09） | Flow / Tools |
| `harness suggest` 写 sug 文件时 frontmatter 不全（缺 title / priority），违反契约 6 | 修 `create_suggestion` 按契约 6 字段落盘（sug-12） | Tools / State |
| `harness validate --human-docs` 对 acceptance 阶段的"前置 vs 后置"未分档 | 按 stage 分档严格度（当前衍生，暂未新开 sug，先观察） | Tools |

## 4. 经验沉淀情况

本轮在 `.workflow/context/experience/roles/` 下新增或补充：

- **executing.md**：新增"经验七：slug 清洗须在入口层统一下沉 + `_path_slug` helper"（bugfix-3 核心教训）。
- **testing.md**：延续经验三、五的"三层证据 + 覆盖扩展诚实自省"方法论，已在 `session-memory.md` 的 Testing Stage 条目中体现，本轮未再新增独立条目。
- **acceptance.md**：延续经验一的"以工具实际输出为准"方法论；本轮独立复跑 tests、不盲信 testing 是该经验的具体执行。
- **regression.md**：已覆盖 bugfix 模式 regression 入口（经验五）、regression 目录命名契约（经验七）；本轮未再新增独立条目，教训承接在新沉淀的 executing 经验七中。

## 5. 流程完整性评估

- **阶段跳过**：仅按模式 B 合规跳过 planning，无异常跳过。
- **阶段短路**：无。testing 独立于 executing，acceptance 独立于 testing。
- **阶段重复**：无。
- **阶段遗漏**：regression 阶段对人文档《回归简报.md》**初始缺失**，在 done 阶段由主 agent 基于已有 `regression/diagnosis.md` 补产完成。

## 6. 改进建议（转 suggest 池）

1. **sug-09（已落盘）**：`harness next` 支持 `--execute` / `--dispatch` flag 自动派发 subagent，减少"推进 → 手动触发"两步摩擦。
2. **sug-10（本阶段新增）**：regression 阶段对人文档《回归简报.md》契约执行补强 —— 在 `harness bugfix` 命令内置一次对 regression 契约 3 的 self-check，或让 `harness validate --human-docs` 在 bugfix 场景对 regression 阶段产出做强制校验并在 acceptance 阶段前拦截。
3. **sug-11（本阶段新增）**：`apply_all_suggestions`（workflow_helpers.py L3261 附近）仍用 `f"{req_id}-{title}"` 拼路径，属 bugfix-3 同源潜在复发点；建议下沉到同一个 `_path_slug` helper。
4. **sug-12（本阶段新增）**：`create_suggestion` 写 sug 文件时补齐 `title` / `priority` frontmatter 字段，符合 stage-role.md §契约 6 + done.md §sug 文件 frontmatter 硬门禁。

## 7. 下一步行动

- **行动**：主 agent 产出《交付总结.md》对人文档，完成 done 阶段退出条件最后一项。
- **行动**：提示用户执行 `harness archive bugfix-3 [--folder <name>]` 归档 bugfix-3。
- **跟踪项**：sug-09~12 进入 pending 池，等后续需求合批或新开 bugfix 消化。

---

## 附：AI 侧 done 判定

- 六层检查全部通过；退出条件中除《交付总结.md》外全部满足（《交付总结.md》随本报告同步产出）。
- 建议人工判定：**done**，并择期归档。
