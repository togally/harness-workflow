# Session Memory — reg-02（对人文档家族缺失 + artifacts 扁平化重构）

## 1. Current Goal

诊断 reg-02：req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）到 acceptance 阶段才发现 1 需求摘要 + 6 变更简报缺失；同时承接用户新架构方向（artifacts 只装对人文档 + 扁平路径 + 白名单扩展 + 机器型文档迁离）。

## 2. Context Chain

- Level 0: 主 agent → regression
- Level 1: 诊断师 subagent（本 session，Opus 4.7） → 独立诊断 + 根因分析 + 路由决策
  - expected_model: opus；角色文件 `.workflow/context/roles/regression.md` + `.workflow/context/experience/roles/regression.md` 已加载
  - 不派发下层 subagent（按 briefing 约束）

## 3. Completed Tasks

- [x] 加载硬前置（runtime.yaml / base-role.md / stage-role.md / regression.md / regression 经验 / risk.md & boundaries.md & recovery.md / role-model-map.yaml / requirement-review.md + planning.md / evaluation testing.md + acceptance.md）
- [x] 扫现场：`harness validate --human-docs` 证实 10 pending / 16，7 份为真缺失（1 需求摘要 + 6 变更简报）；其余 3 份（测试结论 / 验收摘要 / 交付总结）为契约豁免或阶段未到
- [x] 复核 req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界）） / chg-04（S-D 对人文档缩减）豁免范围 —— 未误伤需求摘要 / 变更简报
- [x] 三层根因定位：角色契约层（退出条件有文字但无命令级自检）+ reviewer lint 层（acceptance gate 条款未被 subagent 执行 + lint 本身未精简）+ 历史豁免层（无误伤，排除）
- [x] 梳理架构重构影响面（artifacts 语义重定义 / 扁平路径 / 对人文档白名单扩展 / 机器型文档迁离目标位 / CLI + workflow_helpers + ff_auto + decision_log + validate_human_docs + scaffold_v2 + 各 role.md 改动面 / 历史不迁建议）
- [x] 覆写 regression.md / analysis.md / decision.md（`artifacts/main/requirements/req-38-.../regressions/reg-02-对人文档家族缺失-artifacts-扁平化重构/`）
- [x] decision.md `route_to: "requirement_review"` 已设置，附"转新 requirement"语义注释；主 agent 应识别转新 req

## 4. Results

### 4.1 真实问题判决（一行）

req-38 requirement_review / planning / acceptance 三层都漏掉"对人文档存在性自检"，直接缺 1 份需求摘要 + 6 份变更简报；同时用户提出的 artifacts 扁平化 + 对人文档白名单扩展属新架构需求、与契约加固强耦合，合并处理最经济。

### 4.2 根因 3 层

1. 角色契约层：`requirement-review.md` / `planning.md` 退出条件写了对人文档硬门禁但**无命令级自检**；
2. reviewer lint 层：`.workflow/evaluation/acceptance.md` gate 条款未被 acceptance subagent 执行；`validate_human_docs.py` 仍扫 req-31 / chg-04 废止的测试结论 / 验收摘要（误报噪音）；
3. 历史豁免层：无误伤（复核通过）。

### 4.3 推荐路径（三线合并）

- 当次追补：X2（按新扁平结构直补 req-38 的 7 份对人文档）；
- 契约加固：Y1 + Y2 + Y3 + Y4（可选 Y5）；
- 架构重构：Z1 + Z2 + Z3（Z3 = 历史不迁）。

### 4.4 路由建议

`harness regression --requirement "对人文档家族契约化 + artifacts 扁平化"` 转新 req（暂称 req-39）。
预估切 6 个 chg：chg-a（layout 契约新建）/ chg-b（lint 重写 + 精简）/ chg-c（requirement-review + planning 自检硬门禁代码化）/ chg-d（acceptance gate 强执行）/ chg-e（workflow_helpers + ff_auto + decision_log + scaffold_v2 同步）/ chg-f（req-38 7 份对人文档追补作为试点 + 活证）。

**不推荐**塞进 req-38 做 chg-07：req-38 主题与"对人文档契约化 + 扁平化"正交，且 req-38 已到 acceptance，退回 planning 会拖累签字节奏。

## 5. Next Steps

- 主 agent 读 `decision.md` 后执行 `harness regression --requirement "对人文档家族契约化 + artifacts 扁平化"`；
- req-38 的 acceptance 暂挂，待新 req 的 chg-f 补齐 req-38 对人文档后再回 req-38 走完 acceptance + done + archive；
- 本 subagent 不修改任何 role.md / CLI / evaluation 文件（规约约束，执行交后续 chg）；不推进 stage。

## 6. default-pick 决策清单（req-31 / chg-05 同阶段不打断原则）

- 无 default-pick 争议点 —— 用户在 briefing 中已明确给出当次追补 X2 / 契约加固 Y1-Y4 / 架构重构 Z1-Z3 的候选路径与推荐方向，诊断师按推荐方向判决；三层根因为客观事实，无争议。

## 7. 上下文消耗评估

- 读文件 ~12 次（均为中小体积文本，最大单文件 stage-role.md ~290 行）；
- 工具调用 ~18 次（Read / Bash / Edit / Write）；
- 占比估算 < 50%，未触发 70% 阈值，无需 /compact 或 /clear。

## 8. 经验沉淀候选（base-role 经验沉淀规则）

> 本次可沉淀至 `.workflow/context/experience/roles/regression.md` 的经验：

- **经验：退出条件文字 ≠ 执行闭环，契约加固须代码化阻塞**
  - 场景：req-38 发现 requirement_review / planning 退出条件写了对人文档硬门禁但 subagent 可"自觉"跳过，拖到 acceptance 才暴露。
  - 做法：契约类硬门禁必须配 `harness validate --*` 命令级自检 + 退出前"未绿即 ABORT"的代码分支，不能只靠角色自述 checklist。
  - 来源：req-38 / reg-02（对人文档家族缺失 + artifacts 扁平化重构）。
- **经验：lint 扫描项需与契约精简同步演进**
  - 场景：`validate_human_docs.py` 仍扫 req-31 / chg-04 废止的测试结论 / 验收摘要，产生 Summary 噪音。
  - 做法：每次 stage-role.md 契约 3 / 4 表格调整，必须连带改 `HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` 等代码常量 + 加跨文件一致性测试。
  - 来源：req-38 / reg-02。

（沉淀动作本身留给后续 stage / 新 req 完成，本 subagent 仅候选登记。）
