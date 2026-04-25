# Session Memory — req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））done 阶段

## 1. Current Goal

对 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））执行六层回顾 + 按 chg-05（done 交付总结扩效率与成本段）新模板产出 `交付总结.md`，识别可沉淀经验 / 可转 suggest 候选 / 可追加 constraint 教训。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）
- Level 1: done subagent（done / opus）— 本文件作者

## 3. 模型自检

- **expected_model**：opus（briefing 要求 + role-model-map.yaml `done: "opus"`）
- **实际运行模型**：Opus 4.7（claude-opus-4-7[1m]）
- **映射一致性**：PASS

## 4. 六层回顾

### 4.1 Context 层（上下文层）

- 角色行为：analyst（合并 req-review + planning）+ executing × 8 + testing + acceptance 全程符合 req-40（阶段合并）方向 C 新规；done.md 模板 chg-05 扩展后字段顺序固定，本次产出严格遵循新字段名（"需求是什么 / 交付了什么 / 结果是什么 / 后续建议 / 效率与成本"）。
- 经验文件更新：chg-04 / chg-05 / chg-07 三 session-memory 已沉淀 Candidate Lessons（git mv vs cp、聚合器需 req.yaml 在 flow/、契约 7 扫描 YAML frontmatter 不跳过等），但 `.workflow/context/experience/roles/executing.md` / `done.md` 是否同步落地需在本回顾 Step 4 验证。
- 上下文完整性：req-41 自身作为方向 C dogfood 活证，requirement.md 五节齐全 + 8 chg × {change.md, plan.md, session-memory.md} 全在 flow/requirements/{slug}/ 子树，artifacts/ 仅 raw 副本 + 交付总结，符合"关注点分离"。
- **Context 层结论**：PASS（轻度建议：done 阶段经验文件 sug-06 强制验证 Step 4 应在产出交付总结后做）。

### 4.2 Tools 层（工具层）

- helper 落地：`done_efficiency_aggregate(root, req_id, slug)` 直接可调，本次成功拿到字典；调用时发现 helper 签名要求 `root: Path` 而非 str（裸字符串报 TypeError）—— 工具人体工学小坑，但有 test 覆盖 13 用例。
- CLI 工具适配：`harness validate --human-docs --requirement req-41` exit 0；`harness validate --contract all` 由 stage-role.md 契约 4 第三 bullet 强制；contract-7 lint 在 chg-07 dogfood 修复 107 违规后归零。
- MCP / 其他工具：本 req 无新工具引入；`record_subagent_usage` helper 已实现但派发链路未真实接通（见 State 层）。
- **Tools 层结论**：PASS（建议 sug：`done_efficiency_aggregate` 接受 str root 并自动 Path 包装）。

### 4.3 Evaluation 层（评估层）

- testing 独立：testing subagent（sonnet）独立产出 testing-report.md，AC-01~16 + R1 + revert + 契约 7 + req-29 + req-30 五项合规扫描全 PASS；非 executing 自证。
- acceptance 独立：acceptance subagent（sonnet）独立签字 16 条 AC，lint exit 0，契约 7 违规数 = 0。
- 评估标准达成：所有 16 条 AC 通过；pre-existing FAIL（test_smoke_req28::ReadmeRefreshHintTest）按 stash 验证为存量 stale failure，与 req-41 无关。
- **Evaluation 层结论**：PASS。

### 4.4 Flow 层（流程层）

- 阶段流程完整：requirement_review（analyst seed）→ planning（analyst part B，第 2 轮拆 8 chg + DAG）→ ready_for_execution（用户拍板）→ executing（8 chg 串/并行）→ testing → acceptance → done，无跳过。
- 阶段流转：req-40（阶段合并方向 C）后 analyst 一人承载 req_review + planning 两 stage，本 req 也是该机制的端到端跑通；analyst Part A → Part B 内部串接顺畅，用户在 planning → ready_for_execution 流转点拍板一次。
- 流程顺畅：8 chg DAG 4 路并行（chg-01 后 chg-02/03/04/08）+ 2 路并行（chg-04 后 chg-05/06）+ chg-07 单点收口，无明显阻塞；executing 阶段未触发 regression（regressions/ 目录空）。
- **Flow 层结论**：PASS。

### 4.5 State 层（状态层）

> 本层是 chg-06（harness-manager Step 4 派发硬门禁）+ base-role.md 新增 `done 六层回顾 State 层自检` 段的核心校验点。

- **runtime ↔ req yaml 一致性**：⚠️ runtime.yaml `stage: done`，但 req.yaml `stage: executing`；本 req 流程已走完但 req yaml 未更新到 testing / acceptance / done 任一状态。bugfix-3（runtime ↔ req yaml stage 不同步）老坑复发苗头。
- **stage_timestamps 完整性**：⚠️ req.yaml 仅含 planning / ready_for_execution / executing 三个时间戳，testing / acceptance / done 缺失，导致 `done_efficiency_aggregate` 各阶段耗时分布大量 `⚠️ 无数据`。
- **usage-log 完整性**：⚠️ usage-log.yaml 仅 1 条 entry（chg-07 executing），8 chg × executing + analyst + testing + acceptance + done subagent 全部漏采；按 base-role.md State 层自检规则应"断言 entries 数 ≥ 派发次数 - 容差"，本 req 派发次数 ≥ 11，entries = 1，缺失 ≥ 10，远超容差—— **应报"usage 采集不完整"**。chg-06 文字硬门禁落地了，但派发链路未真正接通。
- **状态记录完整性**：8 chg session-memory + req 顶层 session-memory + sessions/{testing,acceptance}/session-memory 全部齐全；本 done session-memory 即将落盘补齐 sessions/done/。
- **State 层结论**：⚠️ FAIL with caveats（usage 采集不完整 + req yaml stage 不同步 + stage_timestamps 缺失三个问题，但都是"过程数据缺失"非"业务结果失败"，不阻塞 done 推进，转 sug 候选）。

### 4.6 Constraints 层（约束层）

- 硬门禁一（工具优先）：本 done session 直接调 `done_efficiency_aggregate` helper 拿字典，未额外 toolsManager 派发（done 阶段允许主 agent 亲自执行）。
- 硬门禁三（自我介绍）：本 session start 已按新模板自我介绍（done / opus）。
- 硬门禁四（同阶段不打断）：本回顾无争议点；交付总结字段缺数据按 helper 输出 `⚠️ 无数据`，default-pick = 不编造。
- 硬门禁六（对人汇报 ID 必带描述 + 批量列举子条款）：本交付总结 8 chg 列表每条带描述；后续建议 sug 候选每条带描述；State 层批量列举 8 chg + analyst / testing / acceptance / done 时严守批量列举子条款。
- 硬门禁七（周转汇报不列选项 + 必报本阶段已结束）：本汇报无 Ra/Rb 违反；末尾收"本阶段已结束"。
- 契约 4：本 req-id ≥ 41，testing / acceptance / requirement_review / planning / executing / regression 六 stage 对人 brief 已全豁免；done 交付总结产出且字段完整，硬门禁满足。
- 契约 7：本 session-memory + 交付总结首次引用 id（req-41 / chg-01~08 / reg-01 / req-39 / req-40 / req-31 / req-30 / req-29 / req-28 / bugfix-3）均带 title 或 ≤ 15 字描述；DAG 表 + chg 列表批量列举遵守反向豁免。
- 风险扫描：本 req 无外部凭据 / 数据丢失 / 不可回滚动作；scaffold_v2 mirror diff 由 chg-07 / chg-04 / chg-06 / chg-08 各自同步收口；无 known risk 触发。
- **Constraints 层结论**：PASS。

## 5. 可沉淀经验候选（待 Step 4 强制验证）

- **经验 1（done.md / executing.md）**：`done_efficiency_aggregate` 调用规约——root 必须 Path 实例，字符串报 TypeError；建议 helper 内部加 `Path()` 包装。
- **经验 2（done.md）**：交付总结 §效率与成本段缺数据时一律 `⚠️ 无数据`，禁止编造；本 req 即活证（usage-log 仅 1 entry，9+ 阶段标无数据）。
- **经验 3（executing.md）**：`git mv` 仅对 tracked 文件有效，dogfood 迁移未提交工件须用 `cp -r + rm -rf`（chg-07 验证）。
- **经验 4（known-risks.md）**：runtime ↔ req yaml stage 字段不同步是 bugfix-3 老坑复发苗头；done 阶段六层回顾应主动 grep 检测。

## 6. 可转 suggest 候选（不自动登记）

- **sug 候选 1**（high）：`record_subagent_usage` 派发链路真实接通——chg-06 文字硬门禁已落地，但 req-41 自身周期 usage-log 仅 1 entry 是反证；建议下一 req 加端到端 dogfood + State 层自检失败时阻断 done。
- **sug 候选 2**（medium）：req yaml `stage_timestamps` 与 runtime.yaml `stage` 字段双向同步—— `harness next` / `harness archive` 联动写时间戳 + stage 字段。
- **sug 候选 3**（low）：契约 7 / 硬门禁六 CLI `render_work_item_id` 调用覆盖 stdout 路径审计独立 req（chg-08 §7 已留 TODO）。
- **sug 候选 4**（low）：`done_efficiency_aggregate` 接受 str root，自动 Path 包装。

## 7. 可追加 constraint 教训

- 无新硬门禁建议；现有硬门禁六 / 七 + 契约 7 在本 req 全程稳定生效，无需调整。
- 建议 `.workflow/constraints/risk.md` 加一条："runtime.yaml `stage` 与 `state/requirements/{req-id}.yaml` `stage` 字段双向同步缺失"作为高频 known risk（bugfix-3 复发苗头第二次出现）。

## 8. Completed Tasks

- [x] 加载硬前置：runtime.yaml / base-role.md / stage-role.md / done.md / role-model-map.yaml
- [x] 读取 req-41 requirement.md / testing-report.md / acceptance-report.md / 顶层 session-memory.md
- [x] 读取 8 chg session-memory + sessions/{testing,acceptance}/session-memory + usage-log.yaml + req.yaml
- [x] 调用 `done_efficiency_aggregate(Path('.'), 'req-41', '机器型工件回...')` 获取效率字典
- [x] 六层回顾（Context / Tools / Evaluation / Flow / State / Constraints）逐层产出结论
- [x] 产出 `artifacts/main/requirements/req-41-{slug}/交付总结.md`（按 chg-05 新模板五字段固定顺序）
- [x] 产出本 done session-memory.md（六层结论 + sug 候选 + 经验候选合并）

## 9. Default-pick 决策清单

- D-1：交付总结字段缺数据时 → 一律 `⚠️ 无数据`，不编造（done.md 模板硬约束 + Step 6.6）。
- D-2：State 层 usage 采集不完整 → 报告"usage 采集不完整"列缺失派发清单，但**不阻塞** done 推进（按 done.md SOP 流程 done 是回顾不是阻断点；通过 sug 候选转 1 升级处理）。
- D-3：经验沉淀 → 不直接修改 `experience/roles/{done,executing}.md`（待主 agent / 用户决策是否接纳本 session §5 候选）；本 session 仅留候选清单。
- D-4：suggest 不自动登记（briefing 明确"留给主 agent / 用户"）。

## 10. Open Questions

- 无（State 层三个 ⚠️ 已转 sug 候选 1 / 2，不阻塞本阶段）。

## 11. Results

- `artifacts/main/requirements/req-41-{slug}/交付总结.md`：按 chg-05 新模板五字段（需求是什么 / 交付了什么 / 结果是什么 / 后续建议 / 效率与成本）落地，含 frontmatter `requirement_link`。
- `.workflow/flow/requirements/req-41-{slug}/sessions/done/session-memory.md`：本文件，六层回顾 + sug 候选 + 经验候选 + default-pick 清单。

## 12. Next Steps

- 主 agent 收本 done subagent batched-report；按硬门禁七停下报状态，不推进 stage（briefing 禁止）；不自动 `harness archive`；不 commit git；不修代码 / 角色 / 契约。

---

本阶段已结束。
