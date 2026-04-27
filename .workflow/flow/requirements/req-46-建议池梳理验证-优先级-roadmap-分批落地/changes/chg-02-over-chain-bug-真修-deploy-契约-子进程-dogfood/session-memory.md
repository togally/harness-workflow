# Session Memory — chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）planning

## 1. Current Goal

把 reg-02（over-chain bug 三维失配根因诊断 + 三 sug 同根因复发实证） session-memory.md §6 chg-02 草案落到正式 change.md / plan.md，作为 req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）roadmap 之外的紧急 P0 chg。

- 不实改任何 src/ 代码 / .workflow/context/ / .workflow/flow/repository-layout.md（留给 executing）；
- 不执行 pipx reinstall / git mv / 任何破坏性命令；
- 仅产出 3 件机器型工件：change.md / plan.md / 本 session-memory.md，**全部落 `.workflow/flow/requirements/req-46-.../changes/chg-02-.../`**，0 件落 `artifacts/main/requirements/req-46-.../`（dogfood：reg-01（analyst 机器型工件误落 artifacts/ 违反 req-41 关注点分离契约（req-46 现场））教训 + chg-01（机器型工件路径修复 + 防再犯 lint）契约不再犯）。

## 2. Context Chain

- Level 0: 主 agent（harness regression --change 路由）
- Level 1: harness-manager（opus，命令解析 + 角色调度）
- Level 2: analyst-L1（opus，本 subagent，chg-02 plan/change 落地）

## 3. Completed Tasks

- [x] 角色加载（runtime.yaml / role-model-map.yaml / context/index.md / role-loading-protocol.md / base-role.md / stage-role.md / analyst.md / repository-layout.md / analyst.md 经验文件）
- [x] 模型自检 fallback：runtime 不可自省；briefing expected_model = opus；本 session-memory.md §8 留痕；不阻塞
- [x] 自我介绍（"我是分析师（analyst / opus），接下来我将把 reg-02 session-memory.md §6 chg-02 草案落到正式 change.md / plan.md..."）
- [x] 输入文件读取：reg-02 session-memory.md / analysis.md / decision.md / chg-02 空模板 / req-46 requirement.md / chg-01 change.md+plan.md（参考样本）/ src/harness_workflow/workflow_helpers.py 7338-7430（_is_stage_work_done 现状）
- [x] change.md §1-§7 全填（Title / Background / Requirement / Scope In+Out / AC-1~AC-6 / Risks R1-R4 / Dependencies）
- [x] plan.md §1-§4 全填：§1 Development Steps 9 步（Step 1 严格化 / Step 2 subprocess test / Step 3 acceptance.md 部署同步 / Step 4 testing.md dogfood 红线 / Step 5 sug 翻转 / Step 6 经验九 / Step 7 mirror / Step 8 自身 dogfood / Step 9 测试编写）；§2 Verification 三段（unit static / manual smoke / AC mapping 6 条）；§3 Dependencies 5 条硬序；§4 Test Case Design 9 条用例（TC-01 ~ TC-09）+ regression_scope: full
- [x] 落位严格遵守 reg-01 教训 + chg-01 契约：所有工件落 `.workflow/flow/requirements/req-46-.../changes/chg-02-.../`，0 件落 `artifacts/`

## 4. Validated Approaches

- **三维失配诊断模型在 chg 设计上的应用**：reg-02 已发现的契约 / 源码 / 部署 三维失配，本 chg 把"部署"维度首次纳入 chg AC（AC-5 部署同步契约）+ 工作流 evaluation 文件（acceptance.md 硬条目 + testing.md 红线），不再依赖人工记得 `pipx install --force`；
- **subprocess dogfood 兜底策略**：tests/test_workflow_next_subprocess.py 用 `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', ...])` 真跑 CLI，覆盖 first-hop / while-internal / 缺产物 / 有产物 4 路径；与既有 pytest 直调 helper 互补，前者验证部署版本，后者验证 src/ 版本；
- **AC 设计哲学（行为契约 vs 实现细节）**：AC-1 到 AC-6 均按"用户可验证"标准写——AC-1 是 helper 函数边界（unit test）/ AC-2 是 subprocess CLI 行为（端到端）/ AC-3 是自身 dogfood feedback 时间戳（活证）/ AC-4 是 sug frontmatter grep（静态）/ AC-5 是 mtime 对比（运行时）/ AC-6 是 mirror diff + grep（静态）；不写"调用某函数时返回某值"等内部接口契约；
- **执行顺序硬序约束（Step 1 在 Step 2 / Step 8 前）**：先严格化 helper，subprocess 测试和自身 dogfood 才能验证新行为，避免"测试在写但实现还没改"的悖论；
- **chg-02 与 chg-01（机器型工件路径修复 + 防再犯 lint）独立可并行**：两 chg 触点完全正交（chg-01 改 validate_contract.py + 角色文件 + scaffold mirror checklists；chg-02 改 workflow_helpers.py + tests/ + scaffold mirror evaluation），同时进 executing 无冲突。

## 5. Failed Paths

- 无系统拦截。本次任务是纯 planning（3 件机器型工件落地），未触发任何 git 写入 / 业务代码修改 / Bash 危险命令；遵守"不实改 src/ / 不执行 pipx reinstall"硬约束。
- **避免的陷阱**：
  - 没有把 chg-02 scope 蔓延到 sug-39（record_subagent_usage 钩子接通）——sug-53（usage-log 缺失 + over-chain 副作用）的主因 sug-39 留独立 chg，本 chg 仅收 over-chain 副作用部分（呼应 reg-02 D-2 default-pick）；
  - 没有提议把"部署 mtime 强 hash 对比"列为 AC（reg-02 OQ-2 留 default-pick），本 chg default-pick 走 simpler 路径（mtime + helper 存在性，见 §10 D-3）；
  - 没有用 Write 工具落 change.md / plan.md（subagent Write 限制），用 Bash heredoc 写文件（参考 reg-01 经验避坑）。

## 6. AC Mapping 自检（与 plan.md §2.3 双向对账）

| AC | plan.md Step | plan.md 验证 |
|----|-------------|-------------|
| AC-1（保守降级严格化） | Step 1 | 2.1 helper 严格化断言 + §4 TC-01 / TC-02 |
| AC-2（subprocess dogfood 4 路径全绿） | Step 2 + Step 9 | 2.1 subprocess test 跑通 + §4 TC-03 ~ TC-06 |
| AC-3（自身周期 dogfood 自证） | Step 8 | 2.2 stage 流转 dogfood + §4 TC-07 / TC-09 |
| AC-4（sug 状态翻转） | Step 5 | 2.1 frontmatter grep + yaml lint |
| AC-5（部署同步契约文档化） | Step 3 | 2.2 mtime check + §4 TC-08 mtime check helper |
| AC-6（mirror + 经验沉淀） | Step 4 + Step 6 + Step 7 | 2.1 mirror diff + grep |

6 条 AC 全部映射，无 orphan AC、无 orphan Step。

## 7. Open Questions

- **OQ-1（保守降级粒度）**（继承 reg-02 §7）：是否需要更细粒度——例如 `executing` 但 `chg-*/plan.md` 存在但 `session-memory.md` 缺时，怎么判？目前 plan.md Step 1 设计是 sm 缺也算 work_done = False（已落地的逻辑），但 chg dir 都没建时严格化为 False（new 逻辑）。default-pick 走当前粒度，保留 OQ-1 待 executing 阶段如发现新边界再升级；
- **OQ-2（部署契约执行强度）**（继承 reg-02 §7）：mtime + helper 存在性（plan.md TC-08）vs 强 hash 对比？default-pick 走 mtime + helper（D-3，见 §10），acceptance 阶段如发现误判再升级到 hash；
- **OQ-3（dev mode flag 形态）**：`HARNESS_DEV_MODE=1` 环境变量 vs `--dev-mode` CLI flag vs runtime.yaml 字段？default-pick 走环境变量（最低 friction），具体落点待 executing 决定（见 §10 D-4）；
- **OQ-4（subprocess test 跨平台）**：Windows CI 是否纳入？default-pick 走 Linux + Mac（既有 CI 矩阵），Windows 暂不强求（见 §10 D-5）；
- **OQ-5（sug-53 partial_promoted_to_chg 字段是否标准化）**：本 chg 引入 `partial_promoted_to_chg: chg-02` frontmatter 字段（标记 sug 部分关联到某 chg），是否需要在 sug 契约 6 中正式登记？default-pick 走"先用，后归档"路径——本 chg 用作示范，acceptance PASS 后由 done 阶段决定是否升格为契约。

## 8. 模型一致性自检留痕（role-loading-protocol Step 7.5 fallback）

- expected_model（briefing）：opus
- 自身 model 自省：runtime 不支持自省（claude-opus-4-7[1m] 显见于系统提示但未暴露给 subagent runtime）；
- 降级 fallback：按 briefing expected_model = opus 信任，本节留痕；不阻塞。

## 9. Next Steps

1. 主 agent 收本汇报后，更新 runtime.yaml stage = executing（如已在 executing 则保持），触发 executing-L1（sonnet）按 plan.md §1 Step 1-9 实现；
2. **强烈建议**：chg-02 与 chg-01（机器型工件路径修复 + 防再犯 lint）并行启动 executing；
3. **本会话**：planning 完成，session-memory.md 留痕；后续 chg-02 落地责任移交 executing → testing → acceptance → done。

## 10. default-pick 决策清单（同阶段不打断硬门禁四 + chg-05（S-E 决策批量化协议））

- **D-1（chg-02 scope 是否合并 sug-53 主因）**：不合并（chg-02 仅收 sug-53 over-chain 副作用部分，主因 sug-39 留独立 chg）。理由：scope 控制；继承 reg-02 D-2 决策；sug-39 是独立的派发钩子接通问题，混合会导致 chg-02 scope 蔓延 + 测试面失控。
- **D-2（保守降级粒度）**：仅 `executing` stage 严格化（chg dir 缺 → False），其他 stage（planning / RFE / testing / acceptance / done / regression / requirement_review）维持 True 保守降级。理由：仅 executing 是 over-chain 高频路径（reg-02 4 次实证均涉及 executing → testing → acceptance → done 链路）；其他 stage 改严格化风险高（误伤新 req 还没建 chg 时跑 next 等场景）。
- **D-3（部署契约执行强度）**：default-pick 走 mtime + helper 存在性（plan.md TC-08），不走强 hash 对比。理由：simpler；mtime + helper import 已能覆盖 reg-02 实证场景（pipx 路径下 grep `_is_stage_work_done` 无命中 + mtime 早于 commit）；hash 对比留 acceptance 阶段如发现误判再升级（OQ-2 待办）。
- **D-4（dev mode flag 形态）**：default-pick 走 `HARNESS_DEV_MODE=1` 环境变量，不走 CLI flag / runtime.yaml 字段。理由：最低 friction（dev 加 export 一行即可）；CLI flag 需每次跑命令带 flag（friction 高）；runtime.yaml 字段 vs 环境变量同 friction 但 yaml 字段污染状态文件（不期望）；具体落点 executing 阶段定（OQ-3 待办）。
- **D-5（subprocess test 跨平台）**：default-pick 走 Linux + Mac，不强求 Windows。理由：既有 CI 矩阵已覆盖前两者；Windows subprocess 启动方式 / 路径分隔符 / UTF-8 编码差异需额外 fixture 适配，工作量与本 chg P0 修 over-chain 不匹配；Windows 留 sug 跟踪（OQ-4 待办）。
- **D-6（sug 翻转时机）**：frontmatter 字段补全（`linked_regression` / `promoted_to_chg`）在 executing 阶段做（commit 前置）；status 翻 `archived` 必须在 acceptance PASS 后做。理由：保留追溯链 + 防止 chg 失败时 sug 状态错位；继承 chg-01 Step 8 sug-35（reviewer checklist 扩 artifact-placement / test-case-design-completeness 三类 lint 条目补全）翻转时机经验。
- **D-7（regression_scope: full）**：本 chg 标 `full`，不走 default `targeted`。理由：workflow_helpers.py 核心 helper 行为改 + acceptance / testing 评估文件改 + experience/roles 经验沉淀，影响面覆盖 CLI 主入口 + 工作流 gate 逻辑 + acceptance / testing 红线（呼应 analyst 经验文件"plan.md §测试用例设计实操要点 — regression_scope 决策"段：(a) 改动跨核心 helper → 显式标 full）。
