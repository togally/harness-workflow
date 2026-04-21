# Harness 审查检查清单

## 头部说明

### 用途
本清单是 Harness Workflow 各阶段审查工作的统一产出标准依据，用于防止关键制品、角色行为、状态记录被遗漏。审查员（或担任审查职责的 agent）在执行审查任务前必须读取本清单，并逐条核对。

### 适用阶段
- `requirement_review`：需求与变更范围审查
- `planning`：计划与资源分配审查
- `testing`：测试结果与覆盖度审查
- `acceptance`：验收标准与产出完整性审查
- `done`：流程闭环与归档审查

### 更新规则
**每次需求或任务变更引入新产出类型时，必须同步更新本清单。**
- 新增阶段 → 在"阶段速查表"中补充该阶段的检查子集
- 新增制品目录 → 在"制品完整性检查专节"中补充对应条目
- 新增约束或评估标准 → 在六层检查框架对应层级中补充检查项
- 更新后需在变更的 `session-memory.md` 中记录修改摘要

---

## 六层检查框架

### 第一层：Context（上下文层）
- [ ] **角色行为检查（高）**：当前阶段角色文件（`.workflow/context/roles/{stage}.md`）是否已被完整加载？角色行为是否符合预期？
- [ ] **角色自我介绍检查（高）**：`base-role.md` 的硬门禁三是否生效？各角色在执行实质性任务前是否向用户说明了身份和任务意图？
- [ ] **角色加载协议检查（高）**：`.workflow/context/roles/role-loading-protocol.md` 是否存在且为最新版本？所有角色加载顺序是否符合协议（base-role → stage-role → 具体角色）？
- [ ] **经验文件更新（高）**：`.workflow/context/experience/` 下与当前角色相关的经验文件是否已更新本轮教训？
- [ ] **上下文完整性（中）**：项目背景（`project-overview.md`）、团队规范（`development-standards.md`）等上下文是否完整、准确？
- [ ] **角色体系完整性（中）**：`base-role.md`、`stage-role.md`、顶级角色（`technical-director.md`）等核心角色文件是否完整且一致？
- [ ] **经验索引有效性（中）**：经验目录结构是否清晰？新增经验是否已按分类归档到正确位置（`experience/roles/`、`experience/tool/`、`experience/risk/`）？

### 第二层：Tools（工具层）
- [ ] **工具使用顺畅度（高）**：本轮有无工具用得不顺？有无遇到工具限制或兼容性问题？
- [ ] **CLI 适配性（中）**：有无发现更适合的 CLI 工具可以替代当前手工步骤？
- [ ] **MCP 适配性（中）**：有无 MCP 工具可以更好地服务某一层（如 context 层的经验管理、state 层的状态跟踪）？
- [ ] **工具新增记录（低）**：若本轮新增或修改了工具脚本，相关文档（`tools/index.md` 等）是否同步更新？

### 第三层：Flow（流程层）
- [ ] **阶段流程完整性（高）**：是否走了完整的阶段流程（标准需求：requirement_review → planning → executing → testing → acceptance → done；bugfix 需求：regression → executing → testing → acceptance → done）？
- [ ] **阶段跳过检查（高）**：有无阶段被跳过（如标准需求直接从 planning 跳到 executing；bugfix 需求跳过 regression 或 executing）？
- [ ] **bugfix 模式识别（中）**：若 `current_requirement` 以 `bugfix-` 开头，是否启用了 bugfix 快速流程？是否避免了 loading `planning` 角色？
- [ ] **阶段短路检查（高）**：有无 testing 被 executing 影响、acceptance 被 testing 影响等短路行为？
- [ ] **阶段重复检查（中）**：有无不必要的阶段重复执行？
- [ ] **流程顺畅度（中）**：各阶段之间的流转是否顺畅？有无卡顿或阻塞点？

### 第四层：State（状态层）
- [ ] **runtime.yaml 一致性（高）**：`runtime.yaml` 中的 `current_requirement`、`stage`、`locked_stage` 是否与实际执行情况一致？
- [ ] **需求状态一致性（高）**：`.workflow/state/requirements/*.yaml` 中的状态（active、completed、archived）是否准确？
- [ ] **状态记录完整性（高）**：关键决策、变更记录是否完整保存到状态文件和 `session-memory.md` 中？
- [ ] **阶段时间戳准确性（中）**：`stage_timestamps` 是否真实反映了各阶段的实际进入时间？

### 第五层：Evaluation（评估层）
- [ ] **testing 独立性（高）**：testing 阶段是否真正独立执行？有无被 executing 阶段影响？
- [ ] **acceptance 独立性（高）**：acceptance 阶段是否真正独立执行？有无被 testing 阶段影响？
- [ ] **评估标准达成（高）**：各阶段的评估标准是否达成？有无降低标准或妥协？
- [ ] **评估文件加载（中）**：testing / acceptance / regression 阶段是否已加载对应的 `evaluation/{stage}.md`？

### 第六层：Constraints（约束层）
- [ ] **边界约束触发（高）**：本轮有无触发 `.workflow/constraints/boundaries.md` 中定义的边界约束？
- [ ] **风险扫描更新（高）**：有无需要更新 `.workflow/constraints/risk.md` 的新风险？
- [ ] **约束遵守情况（高）**：硬门禁、行为边界、禁止行为等约束条件是否被严格遵守？
- [ ] **恢复路径有效性（低）**：若本轮遇到失败，是否参照 `constraints/recovery.md` 的恢复路径处理？
- [ ] `[高]` suggest 批量转换操作是否遵守 `.workflow/constraints/suggest-conversion.md` 的打包要求

---

## 制品完整性检查专节

### Flow 制品
- [ ] **需求文件（高）**：`.workflow/flow/requirements/{req-id}/requirement.md` 存在且内容完整
- [ ] **变更目录（高）**：`.workflow/flow/requirements/{req-id}/changes/` 下包含所有已规划的变更子目录（`chg-XX-*/`）
- [ ] **变更计划（高）**：每个变更子目录下包含 `change.md` 和 `plan.md`
- [ ] **bugfix 目录规范（中）**：若当前为 bugfix 需求，`.workflow/flow/bugfixes/{bugfix-id}/` 下是否包含 `bugfix.md`、`session-memory.md` 和 `regression/diagnosis.md`？
- [ ] **归档产物（高）**：`.workflow/flow/archive/` 下已归档的需求文件与变更记录是否完整、命名规范

### 根目录制品仓库
- [ ] **artifacts/requirements/ 摘要（高）**：根目录 `artifacts/requirements/` 下是否包含当前需求对应的制品摘要或导出文件（如存在）
- [ ] **artifacts 同步性（中）**：`artifacts/requirements/` 中的文件是否与 `.workflow/flow/requirements/` 下的原始需求保持一致？有无遗漏同步？

### State 制品
- [ ] **运行时状态（高）**：`.workflow/state/runtime.yaml` 存在且字段完整
- [ ] **需求状态文件（高）**：`.workflow/state/requirements/{req-id}.yaml` 存在且状态准确
- [ ] **经验状态索引（中）**：`.workflow/state/experience/index.md` 存在且加载规则有效

### Session 与报告制品
- [ ] **session-memory.md（高）**：当前需求/变更目录下存在 `session-memory.md`，且记录了关键决策、问题、下一步任务
- [ ] **done-report.md（高）**：done 阶段是否输出 `done-report.md`？头部元数据是否完整？
- [ ] **测试报告（高）**：testing 阶段是否输出测试报告或测试运行结果记录？
- [ ] **验收报告（高）**：acceptance 阶段是否输出验收结论或验收报告？

### Experience 制品
- [ ] **阶段经验沉淀（高）**：`.workflow/context/experience/` 下对应阶段的经验文件是否已更新
- [ ] **已知风险库（中）**：若本轮涉及 regression 或风险发现，`experience/risk/known-risks.md` 是否已更新
- [ ] **工具经验（中）**：若本轮涉及工具使用问题，`experience/tool/harness.md` 是否已记录

---

## 阶段速查表

各阶段审查时，优先核对以下子集，再视情况扩展至完整六层框架和制品专节。

### requirement_review 阶段重点
- [ ] `requirement.md` 已存在且目标、范围、验收条件清晰（高）
- [ ] 需求已正确注册到 `.workflow/state/requirements/{req-id}.yaml`（高）
- [ ] 变更列表（changes/）已初步规划，目录命名规范（高）
- [ ] 角色文件 `roles/requirement-review.md` 已加载（中）
- [ ] 经验文件 `experience/roles/requirement-review.md` 已加载（中）

### planning 阶段重点
- [ ] 每个变更子目录下已包含 `change.md` 和 `plan.md`（高）
- [ ] 变更执行顺序和依赖关系已明确（高）
- [ ] `runtime.yaml` 中 `stage` 为 `planning`（中）
- [ ] 角色文件 `roles/planning.md` 已加载（中）
- [ ] 经验文件 `experience/roles/planning.md` 已加载（低）

### executing 阶段重点
- [ ] 当前变更的 `plan.md` 已被读取并遵循（高）
- [ ] `session-memory.md` 已持续更新，记录关键决策和遇到的问题（高）
- [ ] 禁止行为未被触发（高）
- [ ] 角色文件 `roles/executing.md` 已加载（中）
- [ ] 经验文件 `experience/roles/executing.md` + `experience/tool/harness.md` 已加载（中）

### testing 阶段重点
- [ ] testing 阶段独立执行，未受 executing 阶段结果预设影响（高）
- [ ] 测试覆盖度充分，预存测试和新增测试均已运行（高）
- [ ] 测试报告或运行结果已记录（高）
- [ ] 角色文件 `roles/testing.md` 和 `evaluation/testing.md` 已加载（中）
- [ ] 经验文件 `experience/roles/testing.md` 已加载（中）

### acceptance 阶段重点
- [ ] acceptance 阶段独立执行，未受 testing 阶段结果预设影响（高）
- [ ] 验收标准逐项核对，无降低标准或妥协（高）
- [ ] 验收结论已记录（高）
- [ ] 角色文件 `roles/acceptance.md` 和 `evaluation/acceptance.md` 已加载（中）
- [ ] 经验文件 `experience/roles/acceptance.md` 已加载（中）

### done 阶段重点
- [ ] 六层回顾检查已逐层执行（高）
- [ ] 制品完整性检查专节已逐项核对（高）
- [ ] `done-report.md` 已输出且头部元数据完整（高）
- [ ] 改进建议已提取并转存到 `.workflow/flow/suggestions/`（中）
- [ ] 经验文件已按阶段验证更新（中）
- [ ] `artifacts/requirements/` 制品仓库无遗漏（高）

### 契约 7 校验（req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ sug-26）

- [ ] 已执行 `harness validate --contract 7` 或 `harness status --lint`，返回 0（高）
- [ ] 本次新增 / 修改的对人文档（requirement.md / change.md / plan.md / session-memory.md / 各 `*.md` 对人文档）首次引用 `req-*` / `chg-*` / `sug-*` / `bugfix-*` / `reg-*` 均带 title（形如 `req-31（批量建议合集（20条））`）（高）
- [ ] 若命中历史 legacy 裸 id，已判定为"只对本次提交之后引用生效"的 fallback，不强制回补（中）
