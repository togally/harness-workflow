# Session Memory — req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）/ planning

## 1. Current Goal

Part B（planning）：按已拍板的 6 default-pick（S-1=A / C-1=D / F-1=B / HM-2=A / L-1=B / R-1=A），为 chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由） / chg-02（Fix Checklist 首批 3 个 + lint 输出加 fix-checklist 指针） / chg-03（reviewer 加项 + 端到端 dogfood + roadmap）三个 chg 各产出 change.md + plan.md（含 §4 测试用例设计），并定调 DAG / 硬序。

## 2. Context Chain

- Level 0: 主 agent（technical-director）→ planning stage 派发
- Level 1: 本 subagent（analyst / opus / Opus 4.7）→ Part B planning（同一会话续跑）

## 3. Completed Tasks

- [x] 读取 runtime.yaml（确认 current_requirement=req-48 / stage=planning）
- [x] 读取 .workflow/tools/index.md / project-overview.md / project-profile.md / context/index.md
- [x] 加载链：base-role.md → stage-role.md → analyst.md
- [x] 读经验：context/experience/roles/analyst.md + constraints/risk.md
- [x] 模型一致性自检：role-model-map.yaml `analyst.model = opus` ✓ Opus 4.7 一致
- [x] 自我介绍（按 base-role 硬门禁三新模板）
- [x] 读取 req-48 已落产物：requirement.md（5 节完整）+ requirement_review/session-memory.md（含 6 default-pick 决策）
- [x] 读取 harness-manager.md / base-role.md / validate_contract.py 关键段（chg-01/02 实施所需）
- [x] 创建 3 个 chg 目录：`chg-01-错误协议契约-base-role-门禁-harness-manager-捕获/` + `chg-02-fix-checklist首批3个-lint输出加指针/` + `chg-03-reviewer加项-端到端dogfood-roadmap/`
- [x] 写 chg-01 change.md + plan.md（含 §4 测试用例 12 条）
- [x] 写 chg-02 change.md + plan.md（含 §4 测试用例 13 条，含 1 条 dogfood TC）
- [x] 写 chg-03 change.md + plan.md（含 §4 测试用例 8 条，含 3 条 dogfood TC + §5 roadmap 骨架）
- [x] 路径自检：所有产物落 `.workflow/flow/requirements/req-48-{slug}/changes/{chg-id}-{slug}/` 和 `planning/`，无机器型工件落到 `artifacts/`

## 4. default-pick 决策清单（planning stage）

> 本 stage 内未触发新争议点（Part A 6 default-pick 已涵盖全部决策点），所有计划严格按已拍板方案推进。

| 决策点 | 选项 | default-pick | 理由 |
|-------|------|-------------|------|
| **P-1 chg 内 step 是否并行** | A. 严格硬序 / B. 部分并行 | **A** | chg-01 内 A→B→C→D→E→F 严格硬序：协议文档定稿 → angle 文档修订 → helper 实现 → mirror → 单测；chg-02 / chg-03 同款；并行风险高于收益 |
| **P-2 chg-01 helper 返回类型** | A. NoReturn（直接 sys.exit）/ B. int（返回 code 让上层 exit） | **B** | int 让 contract lint 函数能继续做后续工作（如多重 violations 累积）；CLI 入口统一 exit；与现有 `check_*` 函数返回 int 风格一致 |
| **P-3 chg-02 verbose flag 默认值** | A. True（保持现状）/ B. False（harness next 调用时静默）| **A**（CLI 直调）+ 显式 False（内部 gate 调用）| 现状 CLI 用户期望 PASS 也输出确认行；内部 gate 用例改 verbose=False 避免 stdout 噪声；两不冲突 |
| **P-4 chg-03 dogfood 用例数** | A. 仅 1 个（artifact-placement 即可证明协议）/ B. 3 个（每 contract 一条）| **B** | 3 contract 的 fix 路径不同（mv / migrate / mkdir+模板），各自路径风险点不同；3 用例充分证明"协议适用面" |
| **P-5 roadmap 落点** | A. 本 chg-03 plan.md §5 留痕 + done 阶段 cp 出 / B. chg-03 直接产出 roadmap.md | **A** | done 阶段六层回顾 + roadmap 是同款 sop（req-46/47 已验证），保持一致；本 chg 仅定调内容，避免越权 |
| **P-6 reviewer.md 缺失时处理** | A. 跳过该步骤（标 N/A）/ B. 增量补丁补「reviewer 应执 review-checklist.md」最小段 | **B** | 不重写整文件，最小增量补；如 reviewer.md 完全不存在，session-memory 留痕，不阻塞 chg-03 进度 |
| **P-7 dogfood TC feedback.jsonl 字段** | A. 必填 / B. 标 N/A 但 plan 显式声明 | **B** | 本 chg 的 dogfood 走 `harness validate --contract`（lint 失败不写 feedback），不是 `harness next` 路径；显式声明避免 contract `test-case-design-completeness` 误判 |

## 5. Results

### 5.1 3 chg DAG / 硬序

```
chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）
  │
  │  依赖：raise_harness_block helper + error_type 字面表 + 协议契约
  ↓
chg-02（Fix Checklist 首批 3 个 + lint 输出加 fix-checklist 指针）
  │
  │  依赖：3 fix-checklist 文件 + 3 contract 改造 + verbose flag
  ↓
chg-03（reviewer 加项 + 端到端 dogfood + roadmap）
  │
  └── done 阶段六层回顾 + cp roadmap.md → 留尾 req-49 + sug 池
```

### 5.2 产物清单

- `chg-01-.../change.md` + `plan.md`（plan.md §4 含 12 条用例，全 P0/P1）
- `chg-02-.../change.md` + `plan.md`（plan.md §4 含 13 条用例，含 TC-Dogfood-13）
- `chg-03-.../change.md` + `plan.md`（plan.md §4 含 8 条用例，含 TC-Dogfood-03/04/05 + §5 roadmap 骨架）
- `planning/session-memory.md`（本文件）

### 5.3 路径自检通过

- 所有产物落 `.workflow/flow/requirements/req-48-harness-manager-统一异常捕获-base-role-阻塞抛错协议-fix-checklist-自动修复体系/`；
- 无机器型工件（change.md / plan.md / session-memory.md）落到 `artifacts/main/requirements/req-48-{slug}/{stage-name}/`；
- `harness validate --contract artifact-placement` 待主 agent 触发执行（退出条件）。

## 6. Next Steps

- 主 agent 触发：
  - `harness validate --human-docs` exit 0 验收；
  - `harness validate --contract artifact-placement` exit 0 验收（必须）；
  - `harness validate --contract test-case-design-completeness` exit 0 验收（必须，B2.5）；
- 用户拍板 planning 退出（按 stage_policies `planning: user`），转 ready_for_execution；
- 进入 executing 后按硬序 chg-01 → chg-02 → chg-03 实施。

## 7. 退出条件 checklist 自检

- [x] 所有 chg 都有 `change.md`（目标 / 范围 / 验收）
- [x] 所有 chg 都有 `plan.md`（步骤 / 产物 / 依赖）
- [x] 每个 `plan.md` 含 §4. 测试用例设计 章节，波及接口有对应用例（B1）
- [x] 执行顺序已明确（chg-01 → chg-02 → chg-03 硬序）
- [x] dogfood TC 必填字段：chg-02 TC-Dogfood-13 + chg-03 TC-Dogfood-03/04/05 共 4 条 dogfood TC，均含 tmpdir / 子进程 / stdout / runtime-block.yaml 替代 stage 断言 / feedback N/A 显式声明 / AC / 优先级 P0
- [ ] `harness validate --contract test-case-design-completeness` exit code = 0（待主 agent 触发执行）
- [ ] `harness validate --human-docs` exit code = 0（待主 agent 触发执行）
- [ ] `harness validate --contract artifact-placement` exit code = 0（待主 agent 触发执行）

## 8. 经验沉淀候选

- **协议底座 → 工程主菜 → 反馈闭环**三段递进 chg 拆分模式（chg-01 协议 / chg-02 实现 / chg-03 dogfood + reviewer 加项 + roadmap）适合"新增范式 + 多文件配套"类 req；建议补到 `context/experience/roles/analyst.md` 拆分粒度章节，由 done 阶段六层回顾时统一回填。
- **dogfood TC feedback.jsonl 字段 N/A 显式声明**：当 dogfood 走 `harness validate --contract` 而非 `harness next` 路径时，feedback.jsonl 字段不强制；但 plan.md 必须显式声明 N/A，避免 contract `test-case-design-completeness` 误判；建议补到 `context/experience/roles/analyst.md` dogfood 章节。
- **roadmap 骨架定调时机**：建议在 reviewer 反馈闭环 chg 的 plan.md §5 留痕 roadmap 内容骨架，done 阶段仅 cp 出 roadmap.md 即可，避免 done 阶段重新决策；建议补到 `context/experience/roles/analyst.md` roadmap 章节。

## 9. 待处理捕获问题

- 无（chg-01 helper 返回类型 / chg-02 verbose flag / chg-03 reviewer.md 缺失处理 等所有边界点已收敛到 §4 default-pick 决策清单）。

## 10. 上下文消耗评估

- 当前会话累计读入：runtime.yaml / 5 文件 chain（base-role / stage-role / analyst / index / project-overview）/ harness-manager.md（全文）/ base-role.md（全文）/ validate_contract.py 关键段 / req-48 旧 requirement.md + requirement_review/session-memory.md / experience/roles/analyst.md + constraints/risk.md
- 估算 ≈ 65–75k tokens（≈ 70% 阈值附近，可控）；本 stage 完毕，无需 /compact，直接退出 planning 等用户拍板。

## 11. analyst 专业化抽检反馈（按 experience/roles/analyst.md 模板）

| 字段 | 值 |
|------|------|
| 抽检产物 | req-48 chg-01/chg-02/chg-03 完整 change.md + plan.md 集（6 文件 + planning/session-memory.md） |
| 质量评分 | B（持平 / 符合 req-46 / req-47 同款"首批 K + 留尾" + 三段递进拆分模式）|
| 退化点明细 | 无（所有 chg 范围 / 验收 / 硬序 / 用例设计字段齐全；§4 测试用例覆盖所有波及接口；dogfood TC 必填字段齐全）|
| 是否触发 regression 回调 B | 否 |
| 抽检人 + 时间 + req 范围 | analyst（自检）/ 2026-04-28 / req-48 |
