# Session Memory — req-46 planning

## 1. Current Goal

承接 requirement_review stage 的 sug-audit.md 产出，把 10 主题簇 + 45 条 sug 验证结果落实到具体 chg 拆分：
- 优先级排序（P0 阻塞 → P1 契约硬化 → P2 体验 → P3 极小修）
- 依赖图（DAG）显式声明
- 工作量估算（小 / 中 / 大，对应 token 量级）
- 至少 5~10 个簇 chg（最终 10 个）
- 首批 chg 推荐（≥ 2 条，最终 3 条）
- **不创建 chg 工件**，仅产出 roadmap 供用户审核

## 2. Context Chain

- Level 0：主 agent（harness-manager / opus，harness requirement 派发入口）
- Level 1：analyst-L1（opus，requirement_review + planning 续跑，stage 流转点豁免按 HM-1=A 自决推进）

## 3. Completed Tasks

- [x] 承接 requirement_review session-memory + sug-audit 产出
- [x] 完成 chg 拆分（10 个簇 chg：chg-1 over-chain dogfood / chg-2 usage-log runtime / chg-3 CLI 顺修 / chg-4 mirror 漂移 / chg-5 契约 lint / chg-6 archive 路径 / chg-7 testing 红线 / chg-8 install 体验 / chg-9 runtime 同步 / chg-10 杂项）
- [x] 优先级排序：P0 = chg-1 / chg-2 / chg-7；P1 = chg-4 / chg-5 / chg-6 / chg-9；P2 = chg-3 / chg-8；P3 = chg-10
- [x] 依赖图（DAG）落地：关键路径 chg-2 → chg-4 → chg-5 → chg-6；并行路径 chg-1 / chg-7 / chg-8 / chg-3 / chg-9
- [x] 工作量估算：3 大 / 5 中 / 2 小（合计 ~600~1500k token，必须分批）
- [x] 首批 chg 推荐：chg-1 + chg-2 + chg-7（3 个 P0，14 sug 出池）
- [x] 第二批 / 第三批后续推荐
- [x] 池清理计划（每 chg 对应的 sug 出池清单）
- [x] 风险与限制段（chg-2 / chg-5 / chg-6 / chg-7 + 整体风险）
- [x] 落地 roadmap.md（artifacts/main/requirements/req-46-.../planning/roadmap.md）
- [x] requirement.md §5 Split Rules 已含本 roadmap 的引用

## 4. Results

### 4.1 roadmap.md（独立文件）

落位：`artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/roadmap.md`

关键结构：
- §1 优先级模型 + 工作量估算
- §2 chg 拆分（10 个簇 chg，每 chg 含 7 字段：优先级 / 工作量 / 解决 sug / 改动范围 / 验收点 / 前置依赖 / 后置阻塞）
- §3 依赖图 DAG（ASCII art）
- §4 工作量汇总表
- §5 首批 chg 推荐（chg-1 + chg-2 + chg-7）+ 第二/三批后续
- §6 池清理计划（按 chg 列 sug delete / archive 清单）
- §7 default-pick D-11 ~ D-16
- §8 风险与限制
- §9 不在本 roadmap 范围

### 4.2 chg 概览

| chg | 优先级 | 工作量 | 解决 sug 数 | 主线 sug |
|-----|-------|-------|-----------|---------|
| chg-1 over-chain dogfood 复验 + 兜底加固 | P0 | 中 | 7 | sug-38 |
| chg-2 usage-log runtime 强制接通 + 口径修正 | P0 | 大 | 5 | sug-39 |
| chg-3 apply / rename / suggest CLI 顺修 + migrate 散落 .md | P2 | 中 | 6 | sug-08 / sug-19 / sug-48 |
| chg-4 scaffold_v2 mirror 漂移批量修复 + 自动同步告警 | P1 | 中 | 2 | sug-15 / sug-21 |
| chg-5 契约硬门禁 lint 套件 | P1 | 大 | 9 | sug-22 / sug-23 |
| chg-6 archive 路径关注点分离 + 双源整合 | P1 | 大 | 4 | sug-29 / sug-30 |
| chg-7 testing 红线 + safer dogfood + revert dry-run | P0 | 中 | 4 | sug-51 / sug-52 |
| chg-8 install / update / archive CLI 体验顺修 | P2 | 小 | 4 | sug-10 / sug-14 / sug-20 / sug-24 |
| chg-9 runtime / enter / archive / next 状态同步 | P1 | 中 | 3 | sug-13 / sug-26 / sug-37 |
| chg-10 杂项小修 | P3 | 小 | 2 | sug-17（stale）/ sug-28 |

> 注：sug 数总和 > 45，因为部分 sug 有 dup 标记和多 chg 协同。实际不重复 sug 总计 45（含 6 个 applied-out + 5 个 stale + 32 个 live + 2 个 dup-of）。

### 4.3 首批 14 sug 出池清单

| sug-id | 处理方式 | 所属 chg |
|--------|---------|---------|
| sug-09 / sug-12 / sug-40 | delete（stale）| chg-1 |
| sug-46 / sug-50 / sug-38 | archive（dogfood 复验后 applied-out）| chg-1 |
| sug-25 / sug-39 / sug-41 / sug-42 / sug-53 | archive（applied-out）| chg-2 |
| sug-32 | delete（stale）| chg-7 |
| sug-31 / sug-51 / sug-52 | archive（applied-out）| chg-7 |

### 4.4 默认决策清单（default-pick / planning stage）

承接 requirement_review D-1 ~ D-10，新增 D-11 ~ D-16（详见 roadmap.md §7）：

| 决策 | 选 | 一句话理由 |
|-----|---|-----------|
| D-11 raw_artifact validate gate 不绿是否 ABORT | B | 工具自身设计未做 stage 感知；raw_artifact ✓ 留痕放行；工具修复挪到 chg-5 |
| D-12 chg 拆分上限 | A（10 个）| 用户期望 5~10 个，10 簇自然映射 10 chg |
| D-13 chg-2 排首批 | A | 数据底座最高优先级 |
| D-14 chg-7 排首批 | A | sug-51 是 P0 数据安全 |
| D-15 sug-46 双份归 chg-1 | A | 同主题顺手清 |
| D-16 sug-25 archive 不 delete | B | 契约 6 status: applied 应翻转入 archive 保留历史 |

## 5. Next Steps

- planning stage 出口决策 = user（stage_policies.planning = user）
- 主 agent 接受用户拍板首批 chg 范围（推荐 chg-1 + chg-2 + chg-7）后，用 `harness change` 创建对应 chg 工件
- 创建 chg 工件后，由 analyst（同 stage）在每 chg 写 change.md + plan.md（含 §4 测试用例设计）
- 然后 `harness next` 推进到 ready_for_execution（exit_decision = explicit，需 --execute 显式）
- executing 阶段由 sonnet executing 角色实施

## 6. Open Issues / 待处理捕获问题

- raw_artifact validate gate 工具自身设计与 analyst.md 硬门禁原文不一致（已挪 chg-5 解决）
- artifact-placement lint 命中历史 archive 残留（不在本 stage 范围；归 chg-6 archive 路径整合解决）
- chg-2 runtime hook 改造涉及 Agent 工具返回路径，技术方案待 chg planning 阶段进一步细化（不在 roadmap 范围）

## 7. 模型一致性自检

- 期望 model：opus（roles.analyst.model）
- 实际 model：opus（briefing 注入 expected_model = opus，已自检一致）
- 时间戳：planning 入口由主 agent 在 requirement_review stage 自决推进时写入（auto exit_decision，无用户介入）
