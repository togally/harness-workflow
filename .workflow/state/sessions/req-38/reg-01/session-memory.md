# Session Memory — reg-01（对人汇报批量列举 id 缺 title 不可读）

## 1. Current Goal

独立诊断 reg-01：判定是否真实问题、定位根因、给主 agent 路由建议。不执行修复。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）→ regression 阶段（current_requirement = req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步））
- Level 1: regression subagent（regression / opus）→ 本 session，独立诊断 reg-01

## 3. 模型自检留痕（降级）

- 期望 model = `opus`（按 `.workflow/context/role-model-map.yaml` roles.regression）
- briefing 声明 Opus 4.7；本 subagent 未能完全自省子版本号，按 role-loading-protocol 降级规则留痕。
- 自我介绍已按 base-role 硬门禁三格式 + stage-role Session Start 约定执行。

## 4. 前置加载完成清单

- [x] `.workflow/state/runtime.yaml`（current_requirement=req-38, current_regression=reg-01, stage=testing）
- [x] `.workflow/context/roles/base-role.md`（特别看硬门禁六）
- [x] `.workflow/context/roles/stage-role.md`（特别看契约 7）
- [x] `.workflow/context/roles/regression.md`
- [x] `.workflow/context/experience/roles/regression.md`
- [x] `.workflow/constraints/risk.md`
- [x] `.workflow/constraints/boundaries.md`
- [x] `.workflow/constraints/recovery.md`
- [x] `.workflow/context/role-model-map.yaml`

## 5. 诊断结论

### 5.1 是否真实问题

**真实问题**。用户反馈「根本不知道你在说什么」属于体验层确凿违反契约 7（req-30（slug 沟通可读性增强：全链路透出 title）） + 硬门禁六（req-35（base-role 加硬门禁：对人汇报 ID 必带简短描述））的根目的。

### 5.2 根因三层

1. **字面层**：硬门禁六例外条款只覆盖"同一 id 连续多次"，契约 7 的"同上下文后续简写"是宽泛表述；两者对"批量列举多个不同 id"没有交集条款。
2. **批量场景层**：DAG 完成度 / 阶段收束汇报 / 跨 chg 索引表 / 进度概览表等"批量列举 id"场景在现有规约里未显式定义，默认走契约 7 简写路径。
3. **agent 行为偏差层**：主 agent 主动选择"简写"追求视觉紧凑 / token 节省，忽略了"对人可读性"是契约 7 / 硬门禁六的根目的。

### 5.3 修复路径推荐

推荐组合 **路径 A（base-role.md 硬门禁六加批量列举子条款）+ 路径 B（stage-role.md 契约 7 加 id 密集展示豁免反向条款）**，一个 chg 内两条独立 S-x 子工作项；路径 C（新增 lint 命令）作为后续 sug 登记，不阻塞本 chg。

### 5.4 路由决策建议

- **推荐**：`harness regression --change "硬门禁六 + 契约 7 批量列举子条款补丁"` → 转为 req-38（api-document-upload 工具闭环） scope 内新 chg。
- **不推荐**：`--requirement`（过度工程）、`--reject`（体验违反确凿）、`--confirm` 直路 testing（需先 planning 拆 S-A / S-B）。

## 6. default-pick 决策清单

- 无 default-pick。本 session 未遇争议点（硬门禁四场景）；诊断结论与路由建议均基于规约字面条款 + 用户反馈直接推导，无需 options 并列。

## 7. Completed Tasks

- [x] 硬前置加载 9 份必需文件。
- [x] 自我介绍（regression / opus）。
- [x] 扫描触发现场证据（批量列举裸 id 的 batched-report 原文）。
- [x] 覆写 `regression.md` / `analysis.md` / `decision.md`。
- [x] 追加 req-38 session-memory 第 12 节诊断留痕。
- [x] 新建本 reg-01 session-memory。

## 8. 未做清单（按 briefing 禁止项）

- [x] 未派发下层 subagent。
- [x] 未修改 `.workflow/context/roles/base-role.md` / `stage-role.md` / 契约文件。
- [x] 未翻转 `meta.yaml` status（由主 agent 走 CLI）。
- [x] 未推进 stage，未跑任何 `harness *` 命令。

## 9. 契约 7 + 硬门禁六 自证

本 session 内所有 id 首次引用（req-38 / reg-01 / chg-01~05 / req-30 / req-31 / req-35 / req-37 / sug-26）均已带完整 title 或 ≤ 15 字简短描述；批量列举场景（如 chg-01~05）按 reg-01 新口径每条单独带描述，作为落地示范。

## 10. 交接给主 agent

- 诊断已完成；regression.md / analysis.md / decision.md 均已覆写，含真实问题判决 + 根因三层 + 修复路径组合 + 路由建议 + 候选 chg title。
- 主 agent 下一步：根据 decision.md 走 `harness regression --change "<title>"` CLI（推荐 title 见 decision.md §3）；该命令会翻转 reg-01 status 为 `confirmed` / `converted`，创建 req-38（api-document-upload 工具闭环） scope 内新 chg（下一个可用 chg 号）。
- 上下文消耗估算：本 subagent session 读文件 ~12 份（均 .md / .yaml，单份 ≤ 300 行），写 / Edit 操作 5 次，估算 < 20% 上下文占用，无需维护。
