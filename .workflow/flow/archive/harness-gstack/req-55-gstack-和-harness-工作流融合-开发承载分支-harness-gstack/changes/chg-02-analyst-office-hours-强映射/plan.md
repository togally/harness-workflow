---
id: chg-02
title: "analyst → /office-hours 强映射 + adapter 后处理"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Plan Steps

> 执行序：Step 1~3 改 analyst.md（核心改造），Step 4 落映射 yaml + README，Step 5 自测。

### Step 1: 改 analyst.md 注入"调用 /office-hours"步骤

- 文件：`.workflow/context/roles/analyst.md`
- 改动点：在 Step A1 末尾（"读完 base-role / stage-role / analyst SOP / 项目级覆盖"之后）和 Step A2 头（"开始与用户深谈 / 提问"之前）之间插入新段 `Step A1.5: gstack 强映射触发协议`
- 内容（伪代码 + 自然语言混合）：
  ```
  ## Step A1.5: gstack 强映射触发协议（路径 α）
  
  本角色与 gstack /office-hours 强映射；触发流程：
  
  1. 检查 .workflow/state/runtime.yaml.gstack_status.agent_kind_compatible
     - false 或 gstack_status 不存在 → 跳到 Step A1.5.fallback
  2. 输出 batched-report 给主 agent：
     "本 req 已配置 analyst → /office-hours 强映射；
      请在 Claude Code 主对话执行：/office-hours
      主题：<本 req 标题>
      完成后把 design doc path 反馈给我（格式：
      ~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md）"
  3. 暂停，等主 agent / 用户配合完成 /office-hours，把 path 回传
  4. 接到 path 后跳到 Step A1.5.adapter
  ```

### Step 2: 改 analyst.md 注入 adapter 后处理 SOP（章节 mapping 详表）

- 文件：同 Step 1（追加同段）
- 内容：
  ```
  ## Step A1.5.adapter: design doc → requirement.md 重组 SOP
  
  接到 office-hours design doc path 后，按下表把 design doc 重组覆盖本 req requirement.md：
  
  | design doc 段（startup mode） | requirement.md 段 | 处理方式 |
  |---|---|---|
  | # Design: <title> 头部 | frontmatter | 重写 yaml id / title / created_at / operation_type / stage="analysis" |
  | ## Problem Statement + ## Demand Evidence | ## Goal | 汇总成 2~3 条 bullet |
  | ## Constraints + ## Recommended Approach | ## Scope.Included | 提炼为可交付项清单 |
  | ## Approaches Considered（"未选"分支） | ## Scope.Excluded | 列"已比选但不采用" |
  | ## Success Criteria | ## Acceptance Criteria | 强对齐：编号化 AC-01/02/...，每条 [AC-NN:简短描述] |
  | ## Next Steps + ## The Assignment | ## Split Rules | 转 chg 拆分原则 |
  | 多余段（## Premises / ## Cross-Model Perspective / ## Open Questions / ## Distribution Plan / ## Dependencies / ## What I noticed / ## Reviewer Concerns）| ## Office Hours Notes | 整体追加，保留 Spec Review Loop 思考价值 |
  
  Builder mode 的段映射类似（部分段名差异：## The Plan ← Recommended Approach；## Validation ← Success Criteria）；按段名语义匹配，缺失段 skip + 记 warn 到 Office Hours Notes
  ```

### Step 3: 改 analyst.md 注入 fallback 协议

- 文件：同 Step 1（追加同段）
- 内容：
  ```
  ## Step A1.5.fallback: gstack 不可用时的退出协议
  
  触发场景：
  - 场景 1：runtime.yaml.gstack_status.agent_kind_compatible == false（用户用的不是 Claude Code agent）
  - 场景 2：runtime.yaml.gstack_status 不存在（gstack 未装载）
  - 场景 3：主 agent 拒派发 / 用户拒跑 /office-hours
  
  行为：
  - analyst 走原生 Step A1~A3 / A4 / A5 手工填实 requirement.md
  - 在 batched-report 写入：「/office-hours 未启用，本 req requirement.md 由 analyst 手工填实（fallback 模式）」
  - 不阻塞 stage 推进
  - recovery hint：后续 req 装载 gstack 后通过 dogfood 模式补 office-hours 自适用证据
  ```

### Step 4: 写 role-command-map.yaml + README.md

- 创建目录：`.workflow/context/integrations/gstack/`
- 文件 1：`.workflow/context/integrations/gstack/role-command-map.yaml`
  ```yaml
  # Schema: { role-id: [gstack-skill-id, ...] }
  # harness 角色 ↔ gstack 命令强映射；当前仅 analyst → /office-hours 一条
  
  analyst: ["/office-hours"]
  
  # 渐进扩展（路标，不在本 req 落地）：
  # req-56  executing:   ["/investigate"]
  # req-57  testing:     ["/qa"]
  # req-58  acceptance:  ["/review"]
  # req-59  regression:  ["/codex"]
  ```
- 文件 2：`.workflow/context/integrations/gstack/README.md`（≤ 50 行）：
  - § 1 一句话定位
  - § 2 调用矩阵（角色 / gstack skill / 触发时机 / fallback 行为）
  - § 3 触发悖论说明（subagent 不能派发 slash skill，由主 agent / 用户兜底）
  - § 4 adapter mapping 压缩版（3 行表格指向 analyst.md 详表）
  - § 5 渐进扩展规划路标

### Step 5: 自测（mock office-hours 输出走 adapter）

- 准备：构造 mock design doc（startup mode 模板填假数据）落 `/tmp/mock-design.md`
- 执行：手工按 analyst.md adapter mapping 表，把 mock 重组到 `/tmp/mock-requirement.md`
- 验证：
  - frontmatter 正确（id/title/created_at/operation_type/stage）
  - Goal 含 Problem Statement + Demand Evidence 汇总
  - Acceptance Criteria 编号化为 AC-NN 格式
  - Office Hours Notes 含所有多余段
  - 整体结构与 harness requirement.md 模板一致
- 纠正 mapping 表中执行时发现的偏差，回填 analyst.md

## Verification Checklist

- [ ] AC-03：analyst.md 在 Step A2 前嵌入"调用 /office-hours"段（含触发协议 + adapter mapping + fallback）
- [ ] AC-04：adapter mapping 表完整覆盖 startup / builder mode 核心段映射；多余段 → Office Hours Notes
- [ ] role-command-map.yaml 含 1 行映射 + 注释渐进扩展
- [ ] README ≤ 50 行
- [ ] mock 自测通过

## Open Questions

- analyst.md 当前 Step A1 / A2 的精确锚点（落地时先读当前文件确认插入位置）
- adapter mapping 表对 builder mode 段名差异的处理细节（Builder mode 是否真有 ## The Plan / ## Validation 段，还是与 startup mode 共享段名？落地时调研 office-hours SKILL.md L1525~1662 确认）
