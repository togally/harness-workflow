# Session Memory — chg-01（机器型工件路径修复 + 防再犯 lint）planning

## 1. Current Goal

把 reg-01（analyst 机器型工件误落 artifacts/ 违反 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 关注点分离契约（req-46（建议池梳理验证 + 优先级 roadmap + 分批落地） 现场））session-memory.md §6 chg-01 草案落到正式 change.md / plan.md，供 executing 阶段（sonnet）直接执行。

- 不执行 git mv（留给 chg-01 executing）；
- 不实改 src/ / .workflow/context/ / repository-layout.md（留给 executing）；
- 仅产出 3 件机器型工件：change.md / plan.md / 本 session-memory.md，全部落 `.workflow/flow/requirements/req-46-.../changes/chg-01-机器型工件路径修复-防再犯-lint/`，**0 件**落 `artifacts/main/requirements/req-46-.../`（dogfood：本 chg 自身就是修这个）。

## 2. Context Chain

- Level 0: 主 agent（harness next）
- Level 1: harness-manager（opus，命令解析 + 角色调度）
- Level 2: analyst-L1（opus，本 subagent，chg-01 plan/change 落地）

## 3. Completed Tasks

- [x] 角色加载（runtime.yaml / tools/index.md / context/index.md / role-loading-protocol.md / base-role.md / stage-role.md / analyst.md / repository-layout.md）
- [x] 模型自检 fallback：runtime 无法自省 model；briefing expected_model = opus；session-memory 留痕本节
- [x] 自我介绍（"我是分析师（analyst / opus）..."）
- [x] 输入文件读取：reg-01 session-memory §6 + analysis.md + chg-01 空模板 change.md / plan.md
- [x] 关键引用核对：sug-35 路径 / `_MACHINE_TYPE_FILENAMES` 函数位 / scaffold_v2 mirror 目录结构 / review-checklist.md 现状章节
- [x] change.md §1-§7 全填，符合契约 7 + 硬门禁六（id 首次引用带完整 title / 简短描述）
- [x] plan.md §1-§4 全填，9 步骤 + 8 测试用例（TC-01 ~ TC-08 标 P0/P1 + AC 引用）+ 完整 AC mapping + 4 条硬序约束 + regression_scope: full
- [x] session-memory.md（本文件）落到 .workflow/flow/.../changes/chg-01-.../，0 件工件落 artifacts/

## 4. Validated Approaches

- 直接套用 reg-01 §6 的 5 改动 + 7 AC 草案，分解为 9 步骤 + 8 测试用例；AC 与 Step 严格 1:1 ~ 1:N mapping，无悬空 AC。
- TC-08（dogfood）作为 P1 综合用例，验证本 chg 自身生命周期不再误落——自证修复有效。
- regression_scope: full 决策依据：lint 规则升级 + 工作流退出门禁 + 三角色文件 + CLI 流转 gate 改动，影响面覆盖全仓库扫描行为，非局部修。
- 硬序约束 1（git mv 必须先做）防止 lint 升级后自我命中阻塞 chg 推进——这是 reg-01 修复路径的关键陷阱，已在 plan §3 显式标注。

## 5. Failed Paths

- 无。本次任务是纯文档级落地（change.md / plan.md / session-memory.md），无需调用 Bash / Edit src 代码，未触发任何系统拦截或工具失败。

## 6. Key Decisions（default-pick 决策清单）

- **D-1（briefing 字段名）**：选 `expected_artifact_paths`（而非 `artifact_paths_whitelist` / `expected_paths`）。理由：与 reg-01 §6 草案一致 + 与 `task_context_index` 命名风格对齐（`expected_*` 前缀表示"派发方期望"语义）。无 default-pick 决策（用户已通过 reg-01 草案隐含确认）。
- **D-2（lint 升级路径模式 vs 黑名单扩文件名）**：选"路径模式扫 + 白名单豁免 + 黑名单扩文件名"三管齐下（plan Step 4）。理由：单纯扩文件名无法覆盖未来新工作产出类（sug-audit / roadmap 之外的）；单纯路径模式扫无法覆盖白名单 raw `requirement.md` 误命中修复；三管齐下保稳。
- **D-3（regression_scope: full vs targeted）**：选 full。理由：lint 改动影响全仓库扫描行为 + 退出门禁影响所有 stage 流转，非局部改动。
- **D-4（sug-35 翻转时机）**：选"acceptance PASS 后"（plan Step 8 + 硬序约束 4）。理由：保留追溯链 + 防止 chg 失败时 sug 状态错位失去回溯参考。
- **D-5（Risk 1 lint 误伤缓解）**：选"先 WARN 后 FAIL 渐进"。理由：避免一次性切 FAIL 阻塞合规场景；两周观察期。
- **D-6（artifacts/.../requirement.md 是否保留）**：选保留（§2 白名单合法位）。理由：repository-layout.md §2 明确列入白名单（raw authoritative 副本，供外部审阅）。
- 整体 default-pick：所有决策都有 reg-01 草案 + repository-layout.md 契约文字直接支撑，无需用户拍板，符合 stage-role.md 流转点豁免子条款（planning → ready_for_execution 由用户对"需求 + 推荐拆分"合并产物拍板，不为细节决策再开二次确认）。

## 7. Open Questions

- **OQ-1（CLI 退出 gate 具体接入位置）**：plan Step 5 写"`src/harness_workflow/cli.py` 或 `workflow_next` helper（具体位置 executing 阶段定位）"——本 planning 阶段未定位精确文件，留给 executing subagent 做。理由：定位精确文件需读 `cli.py` / `workflow_helpers.py` 全文，non-essential for plan correctness；executing 阶段（sonnet）按 plan §1 Step 5 描述自定位即可。
- **OQ-2（scaffold_v2 mirror 是否需补 stage 级 session-memory 落位段到 repository-layout.md）**：plan Step 7 写"必要时同步 ... 默认不动 ... 仅当 Step 3/4 实施过程中发现路径表不完整再回补（视情况记 sug）"——本 planning 阶段未做出确定决策。理由：repository-layout.md §3 当前列 `changes/{chg-id}-{slug}/session-memory.md` + `regressions/{reg-id}-{slug}/session-memory.md`，未明列 stage 级（如 `requirement-review/session-memory.md` / `planning/session-memory.md`）；req-46 现场用了 stage 级形态，是否合规存在解释空间——暂留给 executing 视情况记 sug，不阻塞本 chg。

## 8. Next Steps（planning 阶段）

1. 主 agent 收本汇报后，按 stage_policies `ready_for_execution → executing` `explicit` 出口决策，等用户 `harness next --execute` 显式拍板进 executing。
2. executing subagent（sonnet）按 plan.md §1 Step 1 ~ Step 9 顺序执行，严格遵守 §3 硬序约束（Step 1 → Step 4 → Step 5 → Step 7 同 commit → Step 8 acceptance 后）。
3. testing subagent 按 plan §4 测试用例 TC-01 ~ TC-08 执行（regression_scope: full），P0 用例必须全绿；TC-08 dogfood 作为综合验证。
4. acceptance PASS 后翻转 sug-35 状态（Step 8）+ 启动 req-46 后续 chg-02 / chg-03 / chg-NN（roadmap 首批）。

---

## Executing 阶段追加（sonnet / chg-01 落地）

### 模型自检（executing-L1，Step 7.5）

- expected_model（briefing）：sonnet
- 执行角色：executing（开发者）
- 自省 fallback：runtime 不支持 model 自省；按 briefing expected_model = sonnet 信任，本节留痕；不阻塞

### Executing Steps 状态追踪

- [x] Step 1：4 个文件物理回归（mv）+ 2 空目录清理（rmdir）— 文件已在 .workflow/flow/，artifacts/{req-review,planning}/ 目录已清
- [x] Step 2：harness-manager.md §3.6 加 expected_artifact_paths 字段约定 + 派发示例
- [x] Step 3：analyst.md 硬门禁 + 退出条件（Part A + B）各加 artifact-placement lint；stage-role.md 加序号 2.5 路径自检 SOP 检查点
- [x] Step 4：validate_contract.py 升级：规则 0（stage-name 子目录扫）+ 白名单豁免（requirement.md）+ 扩展 frozenset（sug-audit.md / roadmap.md）+ archive 豁免（防历史脏数据误命中）
- [x] Step 5：analyst.md 退出条件加 artifact-placement lint（Part A + B 各一条）；workflow_helpers.py workflow_next() 在 requirement_review / planning 出口注入 lint gate（ABORT 阻塞流转）；apply_stage_transition() 同步加注入（带 root fallback WARN）
- [x] Step 6：review-checklist.md 加 artifact-placement 反向抽样（高）条目（"根目录制品仓库"节）+ 阶段速查表 requirement_review / planning 各加一条
- [x] Step 7：scaffold_v2 mirror 同步 4 文件：harness-manager.md / analyst.md / stage-role.md / review-checklist.md；diff -rq checklists/ CLEAN；roles/ 仅 pre-existing usage-reporter.md 漂移（非本 chg 引入，已记录）
- [ ] Step 8：sug-35 状态翻转（acceptance PASS 后执行 — 硬序约束 4）
- [x] Step 9：tests/test_artifact_placement_chg01.py 写入 TC-01 ~ TC-08（40 个 pytest 用例），全绿；现有 test_validate_artifact_placement.py 10 用例全绿；全仓库 pytest -q 628 passed（pre-existing 4 smoke failures 非本 chg 引入）

### Key Decisions（executing 阶段）

- D-ex-1（Step 1 用 mv 非 git mv）：4 文件从未入 git（artifacts/ gitignored），用 `mv` 直接移动，随后 .workflow/ 端 git add，符合目标。
- D-ex-2（archive exemption 扩展）：artifacts/main/archive/ 和 artifacts/main/regressions/ 均加入 lint 豁免，防止历史遗留数据（pre-req-41）触发误报。
- D-ex-3（scaffold_v2 usage-reporter 漂移）：pre-existing，本 chg 不修复，记录为 sug 留后续处理。
- D-ex-4（apply_stage_transition _root fallback）：meta 无 _root 时降级 WARN 不阻塞，符合 change.md §6 风险 1 缓解（先 WARN 后 FAIL 渐进）。

## 9. 模型一致性自检留痕（role-loading-protocol Step 7.5 fallback）

- expected_model（briefing）：opus
- 自身 model 自省：runtime 不支持自省（claude-opus-4-7[1m] 显见于系统提示但是否暴露给 subagent runtime 不确定）；
- 降级 fallback：按 briefing expected_model = opus 信任，本节留痕；不阻塞。
