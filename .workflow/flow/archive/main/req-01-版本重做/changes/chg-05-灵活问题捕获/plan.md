# Plan: chg-05 灵活问题捕获机制

## 执行顺序

### Step 1 — 更新 constraints/boundaries.md：增加职责外问题规则
- 在 `.workflow/constraints/boundaries.md` 新增 `## 职责外问题处理规则` 章节
- 内容包含：
  - **触发条件**：以下两种情况均触发
    1. AI 在执行过程中主动识别到职责范围外的 bug / 需求 / 风险
    2. 用户在对话中口头提出任何问题、想法、不满（不论是否用了正式命令）
  - **各角色行为**：不自行处理，不忽略，标记为"职责外问题"并交主 agent 决策
  - **上报格式**（供各角色使用的简短记录格式）：
    ```
    - 来源阶段: <stage>
    - 来源: AI识别 / 用户口头
    - 问题描述: <一句话>
    - 处置状态: pending
    ```
  - **主 agent 决策规则**（写在本节，WORKFLOW.md 引用）
- 验证：文件包含该章节，格式清晰无歧义

### Step 2 — 更新各角色文件：增加职责外规则引用
- 目标文件：`.workflow/context/roles/` 下 6 个角色文件
  - `requirement-review.md`、`planning.md`、`executing.md`、`testing.md`、`acceptance.md`、`regression.md`
- 每个角色文件的 `## 允许的行为` 或 `## 禁止的行为` 下方新增一行引用：
  ```
  ## 职责外问题
  遇到职责范围外的问题，不自行处理，记录并上报给主 agent。规则见 `.workflow/constraints/boundaries.md#职责外问题处理规则`。
  ```
- 验证：6 个角色文件均含该引用，措辞一致

### Step 3 — 更新 WORKFLOW.md：增加主 agent 接收上报规则
- 在 `WORKFLOW.md` 的 `## 全局硬门禁` 后（或新增 `## 职责外问题处理` 章节）增加：
  - 主 agent 接收上报的行为规则
  - 记录到 session-memory `## 待处理捕获问题` 区块
  - 询问时机：当前节点任务完成时、用户触发 harness 命令前
  - 询问格式：逐条列出，每条提供三个选项
    - A. 升级为正式 regression
    - B. 本次忽略（不再提醒）
    - C. 下次再说（保留 pending）
- 验证：WORKFLOW.md 含该规则，逻辑完整

### Step 4 — 更新 session-memory 格式规范
- 在现有 session-memory（`.workflow/state/sessions/req-01/session-memory.md`）末尾增加 `## 待处理捕获问题` 区块作为示范
- 区块格式：
  ```markdown
  ## 待处理捕获问题

  | # | 来源阶段 | 来源 | 问题描述 | 处置状态 |
  |---|----------|------|----------|----------|
  | 1 | executing | 用户口头 | xxx | pending |
  ```
- 同时在 `.workflow/context/experience/` 下查找是否有 session-memory 模板，若有则同步更新
- 验证：格式区块存在，字段完整

## 产物清单
- 修改：`.workflow/constraints/boundaries.md`（新增职责外问题处理规则）
- 修改：`.workflow/context/roles/*.md`（6 个文件，各增加引用）
- 修改：`WORKFLOW.md`（增加主 agent 处理规则）
- 修改：`.workflow/state/sessions/req-01/session-memory.md`（增加待处理捕获问题区块）

## 依赖
- 建议在 chg-04 之后执行（无强依赖，但设计更复杂，优先完成机械性修复）
- Step 1 是 Step 2 的前提（角色文件引用 boundaries.md 中的章节）
- Step 3 可与 Step 2 并行
