# Requirement

## 1. Title

修复 base-role 到 stage 角色的继承链断裂，确保所有通用规约被各子角色执行

## 2. Background

`base-role.md` 是 Harness Workflow 中所有角色（含 Director、stage 角色、辅助角色）的通用规约，定义了以下硬门禁和行为准则：

1. **硬门禁一：工具优先** — 执行实质性操作前必须先启动 toolsManager 查询可用工具
2. **硬门禁二：操作说明与日志** — 每操作前/后必须说明，并追加到 `action-log.md`
3. **硬门禁三：角色自我介绍** — 每次开始实质性任务前必须向用户说明身份和意图
4. **上下文维护规则** — 60% 评估阈值时必须评估是否使用 `/compact` 或 `/clear`
5. **SOP 结构约定** — 初始化、执行、退出、交接四个阶段必须完整覆盖

但在实际执行中，这些要求被各子角色系统性忽略。原因是在继承链 `base-role.md → stage-role.md → {具体角色}.md` 中，`stage-role.md` 没有将 `base-role.md` 的抽象要求转化为可执行的角色 SOP 步骤，导致各具体 stage 角色在编写自身 SOP 时只关注业务逻辑，遗漏了通用规约。

**Regression 补充说明（2026-04-17）：**

req-24 在 acceptance 阶段被驳回，发现了更深层的根因：`base-role.md` 硬门禁一的原文表述本身存在语义错误。原文"启动 toolsManager 查询可用工具"暗示角色自行查询工具列表，但正确语义是**委派工具管理员 subagent（toolsManager）去匹配并推荐适合当前任务的工具**，角色本身不应直接操作工具查询。由于所有子角色文件从 `base-role.md` 继承此表述，导致全部角色文件均使用了错误的委派语义。本次 regression 的核心修正目标即为从根源文件开始，统一修正工具优先的正确委派语义。

## 3. Goal

1. 修复 `stage-role.md`，使其成为 `base-role.md` 通用规约的有效"翻译层"
2. 批量更新所有 stage 角色文件（executing, testing, planning, acceptance, regression, requirement-review, done）和技术总监文件，确保每项 base-role 硬门禁都在子角色 SOP 中有明确的执行步骤和检查点
3. 建立可验证的继承一致性检查机制，防止未来新增角色再次遗漏 base-role 要求

## 4. Scope

**包含：**
- `stage-role.md` 的重构：增加"继承自 base-role 的执行清单"
- 所有 stage 角色 `.md` 文件的 SOP 更新
- `technical-director.md` 中上下文监控职责与 base-role 60% 阈值的对齐
- 各角色"上下文维护职责"中增加 60% 评估的具体执行标准
- 增加"继承检查清单"或验收模板，确保新增角色时可核对

- 修正 `base-role.md` 硬门禁一的工具优先表述（根源文件），将"启动 toolsManager 查询工具"改为"委派工具管理员 subagent，由其匹配并推荐工具"
- 将 `stage-role.md` 和所有 stage 角色文件（executing、testing、planning、acceptance、regression、requirement-review、done、technical-director）中的工具优先表述统一改为委派语义

**不包含：**
- 修改 base-role.md 中工具优先以外的规则内容
- 修改 tools/stage-tools.md 的工具白名单
- 修改 flow/stages.md 的流转规则
- 新增或删除任何角色

## 5. Acceptance Criteria

- [ ] `stage-role.md` 中包含明确的 base-role 继承执行清单，将每条抽象要求映射为可检查的子类行为
- [ ] `executing.md` 的 SOP 中明确包含：工具优先查询、自我介绍、操作日志、60% 上下文评估、经验沉淀、交接步骤
- [ ] `testing.md`、`planning.md`、`acceptance.md`、`regression.md`、`requirement-review.md`、`done.md` 的 SOP 同样包含上述全部通用步骤
- [ ] `technical-director.md` 的监控职责从 60% 阈值开始，且在 subagent 返回/阶段转换时强制检查上下文
- [ ] 存在一份可复用的"角色文件继承检查清单"，未来新增角色时可逐条核对
- [ ] `base-role.md` 硬门禁一的表述为：委派工具管理员 subagent（toolsManager），由其匹配并推荐适合当前任务的工具，而非角色自行查询工具列表
- [ ] 所有角色文件（`stage-role.md`、`executing.md`、`testing.md`、`planning.md`、`acceptance.md`、`regression.md`、`requirement-review.md`、`done.md`、`technical-director.md`）中的工具优先步骤均使用委派语义，不出现"自行查询"或"启动工具查询"的表述

## 6. Split Rules

- chg-01: 重构 `stage-role.md`，增加 base-role 继承执行清单和通用 SOP 模板
- chg-02: 更新 `technical-director.md` 的上下文监控职责，与 base-role 60% 阈值对齐
- chg-03: 批量更新所有 stage 角色文件（executing, testing, planning, acceptance, regression, requirement-review, done）的 SOP 和上下文维护职责
- chg-04: 创建"角色文件继承检查清单"并验证所有现有角色文件的一致性
- chg-05: 修正 `base-role.md` 硬门禁一的工具优先表述，将自行查询语义改为委派 toolsManager subagent 语义
- chg-06: 批量更新 `stage-role.md` 和所有 stage 角色文件（executing、testing、planning、acceptance、regression、requirement-review、done、technical-director，共 8 个子角色文件）的工具优先表述，统一改为委派语义
