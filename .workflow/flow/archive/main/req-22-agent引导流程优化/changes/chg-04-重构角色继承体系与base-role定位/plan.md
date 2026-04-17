# Plan: chg-04 重构角色继承体系与 base-role 定位

## 执行顺序

### Step 1: 修改 role-loading-protocol.md
- 在"核心原则"章节新增模型一致性原则：
  ```markdown
  - **模型一致性**：所有角色（含 subagent）应使用与主 agent 相同的模型，以保证执行质量一致性
  ```
- 在"通用加载步骤"Step 5 中更新 stage 角色的加载顺序描述：
  ```
  base-role.md → stage-role.md → {具体角色}.md
  ```
- 更新"流程速查图"中 stage 角色的加载链路
- 产物：更新后的 `role-loading-protocol.md`

### Step 2: 重构 base-role.md
- 修改标题：从 `Base Role` 改为 `基础角色（Base Role）——所有角色的通用规约`
- 修改引言：删除"所有 stage 角色的抽象父类"，改为"Harness 工作流中所有角色（含顶级角色 Director、辅助角色 toolsManager、stage 角色）必须遵循的通用规约"
- 保留"硬门禁一：工具优先"、"硬门禁二：操作说明与日志"
- 删除"通用准则"中按 stage 加载经验的具体映射（改为在 stage-role.md 中定义）
- 删除"Session Start 约定"和"Stage 切换上下文交接约定"（迁移到 stage-role.md）
- 删除"角色生命周期中的通用加载职责"中关于"流转规则（按需）"的章节
- 将原"角色生命周期中的通用加载职责"精简为只保留通用的上下文维护原则，删除按 stage 过滤的经验文件映射
- 新增`## 经验沉淀规则`章节：
  - 沉淀时机：角色任务完成后、退出条件检查前
  - 沉淀内容：本轮执行中发现的通用约束、最佳实践、常见错误、工具使用技巧
  - 沉淀路径：`context/experience/` 下对应的分类目录（由 stage-role.md 按角色指定）
  - 沉淀格式：场景 → 经验内容 → 来源（需求 ID）
  - 强制检查：退出条件中必须包含"是否有可泛化的经验需要沉淀"
- 新增`## 上下文维护规则`章节：
  - 当上下文负载达到 **60%**（约 ~61440 tokens）时，必须评估是否执行维护
  - 评估标准：
    - 历史消息仍相关但可压缩 → `/compact`
    - 历史消息已无效或任务刚开始/已完成 → `/clear`
    - 达到强制维护阈值（85% 以上）→ 必须立即执行维护动作
  - 执行 `/compact` 或 `/clear` 前，必须确认关键决策已保存到文件
- 产物：更新后的 `base-role.md`

### Step 3: 新建 stage-role.md
- 文件路径：`.workflow/context/roles/stage-role.md`
- 标题：`# Stage 角色公共规约（stage-role）`
- 引言：本文件继承 `base-role.md` 的通用规约，是所有 stage 执行角色的公共父类。
- 包含章节：
  1. `## Session Start 约定`（从原 base-role.md 迁移）
  2. `## Stage 切换上下文交接约定`（从原 base-role.md 迁移）
  3. `## 经验文件加载规则`：
     - 读取 `context/experience/index.md`
     - 按角色名加载对应经验文件（路径引用 chg-05 重构后的 `experience/roles/{角色名}.md`）
     - 不得批量加载整棵经验目录树
  4. `## 流转规则（按需）`：如需判断 stage 推进条件或归档规则，读取 `flow/stages.md`
- 产物：新建的 `stage-role.md`

### Step 4: 更新 technical-director.md
- SOP Step 3 中关于为 subagent 加载角色的描述更新为：
  ```markdown
  - 根据 `runtime.yaml` 中的 `stage`，按 `role-loading-protocol.md` 为 subagent 加载角色：
    - 先加载 `base-role.md`
    - 再加载 `stage-role.md`
    - 最后按 `stage` 加载对应角色文件（如 `executing.md`、`planning.md` 等）
  ```
- 产物：更新后的 `technical-director.md`

### Step 5: 更新 context/index.md
- 在"抽象父类"表格中新增一行：
  | **Stage 角色公共规约（stage-role）** | 所有 stage 执行角色的公共父类，继承 base-role 并叠加 stage 专属规则 | `.workflow/context/roles/stage-role.md` |
- 更新 `base-role.md` 的职责描述为：所有角色（含 Director、toolsManager、stage 角色）的通用规约
- 产物：更新后的 `context/index.md`

### Step 6: 验证
- 使用 grep 检查 `base-role.md` 中是否已无 `"stage 角色"`、`"主 agent"`、`"流转规则（按需）"` 等过时描述
- 检查 `role-loading-protocol.md` 中加载顺序是否已更新
- 检查 `stage-role.md` 是否包含所有必需的 4 个章节
- 产物：验证通过标记

## 依赖关系

- **前置依赖**：无（chg-04 不依赖 chg-05 的文件移动，stage-role.md 中的经验路径可以先写为 `experience/roles/{角色名}.md`，chg-05 负责实际移动文件）
- **后续影响**：chg-05 将完成经验文件的实际迁移并更新 stage-role.md 中的引用
