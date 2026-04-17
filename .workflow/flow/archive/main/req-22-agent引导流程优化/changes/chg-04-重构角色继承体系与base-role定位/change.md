# chg-04: 重构角色继承体系与 base-role 定位

## 目标

修正 req-22 在角色架构设计层面的核心缺陷：base-role 的适用范围被错误地窄化为"stage 角色的抽象父类"，且角色加载协议缺失模型一致性约束。通过重新定位 base-role 为"所有角色的通用规约"、新建 stage-role 承接 stage 专属公共规则、在协议中声明模型一致性，建立清晰的三层角色继承体系。

## 范围

### 包含

- 修改 `.workflow/context/roles/role-loading-protocol.md`：
  - 新增模型一致性声明
  - 更新 stage 角色加载顺序为 `base-role.md → stage-role.md → {具体角色}.md`
- 重构 `.workflow/context/roles/base-role.md`：
  - 标题和引言重新定位为"所有角色必须遵循的通用规约"
  - 删除"stage 角色专属"、"主 agent"等限定性描述
  - 删除"流转规则（按需）"章节
  - 删除 Session Start 约定和 Stage 切换上下文交接约定（下沉到 stage-role.md）
  - 删除按 stage 加载经验文件的具体映射（改为由 stage-role.md 按角色维护）
  - 新增"经验沉淀规则"章节：统一所有角色的经验沉淀时机、格式和路径
  - 新增"上下文维护规则"章节：明确上下文负载达到 60% 时必须评估并使用 `/compact` 或 `/clear`
- 新建 `.workflow/context/roles/stage-role.md`：
  - 定位为 stage 角色的公共父类，继承 base-role 的通用规约
  - 包含 Session Start 约定、Stage 切换上下文交接约定
  - 包含按角色加载经验文件的规则（引用 chg-05 重构后的路径）
  - 包含 stage 角色的流转规则（按需）
- 更新 `.workflow/context/index.md`：
  - 在"抽象父类"表格中新增 `stage-role.md`
  - 更新 `base-role.md` 的职责描述
- 更新 `.workflow/context/roles/directors/technical-director.md`：
  - SOP Step 3 中为 subagent 加载角色的描述更新为三层加载

### 不包含

- 不修改 `WORKFLOW.md` 和 `context/index.md` 的索引结构（仅更新描述）
- 不移动 `context/experience/stage/` 下的文件（由 chg-05 负责）
- 不修改各 stage 角色文件的具体 SOP 内容（仅更新继承声明/经验引用）
- 不引入新的 harness 命令或 stage

## 验收标准

- [ ] `role-loading-protocol.md` 中包含"所有角色必须使用与主 agent 相同模型"的明确声明
- [ ] `base-role.md` 的标题/引言不再限定为"stage 角色的抽象父类"，而是"所有角色的通用规约"
- [ ] `base-role.md` 中无"流转规则（按需）"章节
- [ ] `base-role.md` 中包含"经验沉淀规则"章节，定义沉淀时机、格式和路径
- [ ] `base-role.md` 中包含"上下文维护规则"章节，明确 60% 阈值约束
- [ ] `stage-role.md` 文件存在，包含 Session Start、Stage 切换交接、经验加载规则、流转规则
- [ ] `role-loading-protocol.md` 中 stage 角色的加载顺序已更新为 `base-role → stage-role → 具体角色`
- [ ] `technical-director.md` 中 subagent 加载流程描述与新的三层继承一致
- [ ] `context/index.md` 中正确列出 `base-role.md` 和 `stage-role.md` 的继承关系
