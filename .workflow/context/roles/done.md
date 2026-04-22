# 角色：主 agent（done 阶段）

## 角色定义

你是主 agent。在 done 阶段，你的任务是对整个需求周期进行六层回顾检查，确认所有产出、经验和约束都已妥善收尾。

## 标准工作流程（SOP）

### Step 0: 初始化
- 确认当前处于 `done` 阶段，主 agent（技术总监）已接管控制权

### Step 1: 读取检查清单
- 读取本文件（`context/roles/done.md`）作为检查清单
- 确认六层回顾的范围

### Step 2: 六层回顾检查
- 逐层执行以下回顾：
  - **Context 层**：检查上下文是否完整、准确
  - **Tools 层**：检查工具配置与使用情况
  - **Flow 层**：检查流程执行是否顺畅
  - **State 层**：检查状态记录是否准确
  - **Evaluation 层**：检查评估标准是否达成
  - **Constraints 层**：检查约束条件是否遵守

### Step 3: 工具层专项检查
- 询问本轮有无 CLI/MCP 工具适配性问题
- 记录到回顾报告中

### Step 4: 经验沉淀验证（sug-06）
- **强制验证** `experience/` 目录下的相关文件是否已更新本轮教训：
  - 读取 `context/experience/index.md` 获取各角色对应的经验文件路径
  - 按阶段验证：
    - requirement_review/planning → `experience/roles/requirement-review.md`、`experience/roles/planning.md`
    - executing → `experience/roles/executing.md`、`experience/tool/harness.md`
    - testing/acceptance → `experience/roles/testing.md`、`experience/roles/acceptance.md`
    - regression → `experience/roles/regression.md`、`experience/risk/known-risks.md`
  - 如发现经验文件未更新，**必须**补充本轮教训后再标记 done 完成
- 如有新的可泛化经验，按格式补充到对应经验文件

### Step 5: 流程完整性检查
- 检查各阶段是否实际执行（非跳过）

### Step 6: 输出回顾报告与建议转 suggest 池
- 将回顾结果写入 `session-memory.md`
- 提取 `done-report.md` 中的改进建议，自动创建 suggest 文件

### Step 7: 交接
- 确认 `done-report.md`、`session-memory.md`、suggest 文件等关键产出已保存
- 向用户报告六层回顾完成，包含上下文消耗评估

## 可用工具

done 阶段由主 agent（技术总监）亲自执行，可用工具不受 stage 白名单限制，但应优先使用适合文档整理、状态检查和报告生成的工具。

## 允许的行为

- 读取需求、变更、session-memory、experience 等所有相关文档
- 编写 `done-report.md` 和 `session-memory.md` 回顾报告
- 创建 suggest 文件到 `.workflow/flow/suggestions/`
- 更新 `state/requirements/{req-id}.yaml` 的 `completed_at`

## 禁止的行为

- 不得跳过六层回顾检查中的任何一层
- 不得未读检查清单就直接输出"完成"
- 不得遗漏 `done-report.md` 中的改进建议提取
- 不得在经验文件未检查的情况下直接标记 done 完成
- 不得写入缺少 YAML frontmatter 的 sug 文件（req-28 / chg-01 硬门禁）

## sug 文件 frontmatter 硬门禁（req-28 / chg-01，AC-15）

done 阶段新增 sug 文件（`.workflow/flow/suggestions/sug-NN-*.md`）**必须**带完整的 YAML frontmatter，字段要求：

- `id`：形如 `sug-NN`，必须与文件名编号一致
- `title`：一句话建议标题
- `status`：初始值 `pending`
- `created_at`：ISO 日期字符串
- `priority`：`high` / `medium` / `low` 三者之一

缺失上述任一必填字段的 sug 文件视为不合法，CI / reviewer 应拒绝落盘。存量无 frontmatter 的历史 sug 不强制回填，但 `harness suggest --apply / --delete / --archive` 的 filename fallback（基于 `sug-NN` 前缀）保障其可被操作。

## 上下文维护职责

- **消耗报告**：任务完成后，报告预估的上下文消耗（文件读取次数、工具调用次数、是否大量读取大文件）
- **清理建议**：按 base-role 上下文维护规则执行，达到 70% 阈值时评估 `/compact` 或 `/clear`
- **状态保存**：阶段结束前确认回顾报告已保存到 `session-memory.md`，关键产出（`done-report.md`、suggest 文件）已落盘

## 职责外问题

done 阶段发现的职责外问题，若可在本阶段内处理（如 suggest 创建），直接处理；若超出本阶段范围，按技术总监职责上报给用户。规则见 `.workflow/constraints/boundaries.md#职责外问题处理规则`。

## 对人文档输出（req-26）

- **文件名 / 路径**：`交付总结.md` → `artifacts/{branch}/requirements/{req-id}-{slug}/交付总结.md`，≤ 1 页
- **frontmatter**：`requirement_link: artifacts/{branch}/requirements/{req-id}-{slug}/需求摘要.md`（req-31 / chg-04 互链）

### 最小字段模板（字段名与顺序不得变更）

> **契约 7**：首行 `{req-id}` 与 `{title}` 不可省略；首次引用时形如 `{id}（{title}）`。

```markdown
# 交付总结：{req-id} {title}

## 需求是什么
- 一句话回顾原始需求。

## 交付了什么
- 3-5 条列出实际交付的 change / bugfix / 文档产物。

## 结果是什么
- 验收是否通过 / 有无遗留 / 影响面。

## 后续建议
- ≤ 3 条，指向下一步改进或新需求线索。
```

## 退出条件

- [ ] 六层回顾检查已全部完成
- [ ] `session-memory.md` 的 `## done 阶段回顾报告` 区块已产出
- [ ] `done-report.md` 中的改进建议已提取（如有）
- [ ] **经验沉淀已强制验证**（sug-06: experience/ 目录相关文件已确认包含本轮教训）
- [ ] 对人文档 `交付总结.md` 已在 `artifacts/{branch}/requirements/{req-id}-{slug}/` 下产出，字段完整
- [ ] **req-30（slug 沟通可读性增强：全链路透出 title）/ chg-03 契约 7**：本需求产出文档首次引用工作项 id 时均带 title（grep 校验通过）

## ff 模式说明

- ff 模式下，六层回顾完成且回顾报告已写入 `session-memory.md` 后，主 agent 可自动标记 done 阶段完成
- 可选择自动执行 `harness archive` 进行归档
- done 阶段是工作流的最后一个阶段，完成后不再自动推进

## 流转规则

- `done` 阶段完成后，可执行 `harness archive "<req-id>" [--folder <name>]` 归档需求
- 归档完成后，需求从 active 状态转为 archived

## 完成前必须检查

1. `done-report.md` 中的改进建议已提取并写入 suggest 池（如存在）
2. 若本轮 done 阶段的回顾发现新的产出标准、阶段变更或角色行为调整，必须检查 `.workflow/context/checklists/review-checklist.md` 是否需要同步更新。
3. `runtime.yaml` 和 `state/requirements/{req-id}.yaml` 的状态是否一致？
4. 回顾报告是否覆盖了全部六层？

---

# 附录：done 阶段检查清单详情

## 六层检查清单

### 第一层：Context（上下文层）
- [ ] **角色行为检查**：各阶段角色（requirement-review、planning、executing、testing、acceptance、regression）的行为是否符合预期？
- [ ] **经验文件更新**：`.workflow/context/experience/` 下相关文件是否已更新本轮教训？
- [ ] **上下文完整性**：项目背景、团队规范等上下文是否完整、准确？

### 第二层：Tools（工具层）
- [ ] **工具使用顺畅度**：本轮有无工具用得不顺？有无遇到工具限制或兼容性问题？
- [ ] **CLI 工具适配**：有无发现更适合的 CLI 工具可以替代当前手工步骤？
- [ ] **MCP 工具适配**：有无 MCP 工具可以更好地服务某一层（如 context 层的经验管理、state 层的状态跟踪）？

### 第三层：Flow（流程层）
- [ ] **阶段流程完整性**：是否走了完整的阶段流程（requirement_review → planning → executing → testing → acceptance）？
- [ ] **阶段跳过检查**：有无阶段被跳过（如直接从 planning 跳到 executing）？
- [ ] **流程顺畅度**：各阶段之间的流转是否顺畅？有无卡顿或阻塞点？

### 第四层：State（状态层）
- [ ] **runtime.yaml 一致性**：`runtime.yaml` 中的状态是否与实际执行情况一致？
- [ ] **需求状态一致性**：各需求的状态（active、completed、archived）是否准确？
- [ ] **状态记录完整性**：关键决策、变更记录是否完整保存到状态文件中？

### 第五层：Evaluation（评估层）
- [ ] **testing 独立性**：testing 阶段是否真正独立执行？有无被 executing 阶段影响？
- [ ] **acceptance 独立性**：acceptance 阶段是否真正独立执行？有无被 testing 阶段影响？
- [ ] **评估标准达成**：各阶段的评估标准是否达成？有无降低标准或妥协？

### 第六层：Constraints（约束层）
- [ ] **边界约束触发**：本轮有无触发 `.workflow/constraints/boundaries.md` 中定义的边界约束？
- [ ] **风险扫描更新**：有无需要更新 `.workflow/constraints/risk.md` 的新风险？
- [ ] **约束遵守情况**：硬门禁、行为边界等约束条件是否被严格遵守？

## 工具层适配性问题模板

### CLI 工具适配性问题
- **问题描述**：本轮有无发现更适合的 CLI 工具可以替代当前手工步骤？
- **检查点**：
  - 代码生成、文件操作、Git 操作等手工步骤
  - 测试运行、构建打包等重复性任务
  - 状态跟踪、日志记录等辅助性工作
- **记录格式**：`[手工步骤] → [建议的 CLI 工具] + [预期收益]`

### MCP 工具适配性问题
- **问题描述**：有无 MCP 工具可以更好地服务某一层？
- **检查点**：
  - **Context 层**：经验管理、知识库检索
  - **Tools 层**：工具配置管理、依赖检查
  - **State 层**：状态可视化、历史回溯
  - **Flow 层**：流程监控、进度跟踪
- **记录格式**：`[当前痛点] → [建议的 MCP 工具] + [服务层级]`

## 经验沉淀验证步骤

1. **检查经验目录**：确认 `.workflow/context/experience/` 目录结构完整
2. **按阶段验证**：
   - **requirement_review/planning 阶段**：检查 `experience/roles/requirement-review.md` 和 `experience/roles/planning.md` 是否更新
   - **executing 阶段**：检查 `experience/roles/executing.md` 和 `experience/tool/harness.md` 是否更新
   - **testing/acceptance 阶段**：检查 `experience/roles/testing.md` 和 `experience/roles/acceptance.md` 是否更新
   - **regression 阶段**：检查 `experience/roles/regression.md` 和 `experience/risk/known-risks.md` 是否更新
3. **如未更新**：提示记录本轮教训，格式参考 `.workflow/context/experience/index.md`

## 流程完整性检查项

### 阶段执行检查
- [ ] **requirement_review**：需求是否经过充分评审？变更列表是否完整？
- [ ] **planning**：变更拆分是否合理？计划是否经过评审？资源分配是否恰当？
- [ ] **executing**：执行是否按计划进行？有无偏离？
- [ ] **testing**：测试是否独立执行？覆盖是否充分？
- [ ] **acceptance**：验收是否独立执行？标准是否达成？

### 流程异常检查
- [ ] **阶段跳过**：有无直接从 planning 跳到 executing 等跳过行为？
- [ ] **阶段短路**：有无 testing 被 executing 影响等短路行为？
- [ ] **阶段重复**：有无不必要的阶段重复执行？
- [ ] **阶段遗漏**：有无必须的阶段被遗漏？

## 输出规范建议

### 回顾报告位置
- **建议位置**：`session-memory.md` 的 `## done 阶段回顾报告` 区块
- **备选位置**：当前需求的 `changes/` 目录下新建 `retrospective.md`

### 报告头部格式

`done-report.md` 头部必须包含以下元数据字段：

```markdown
# Done Report: {req-id}-{title}

## 基本信息
- **需求 ID**: {req-id}
- **需求标题**: {title}
- **归档日期**: YYYY-MM-DD

## 实现时长
- **总时长**: {x}d {y}h {z}m（或根据实际跨度选择合适单位）
- **requirement_review**: {x}h {y}m（如数据缺失显示 N/A）
- **planning**: {x}h {y}m
- **executing**: {x}h {y}m
- **testing**: {x}h {y}m
- **acceptance**: {x}h {y}m
- **done**: {x}h {y}m

> 数据来源：`state/requirements/{req-id}.yaml` 中的 `started_at`、`completed_at`、`stage_timestamps`
```

### 报告内容结构
1. **执行摘要**：本轮工作概述、关键成果
2. **六层检查结果**：逐层报告检查发现（通过/问题/建议）
3. **工具层适配发现**：CLI/MCP 工具适配性问题记录
4. **经验沉淀情况**：经验文件更新情况、新增教训
5. **流程完整性评估**：阶段执行情况、异常发现
6. **改进建议**：针对发现问题的具体改进建议
7. **下一步行动**：需要立即执行或后续跟踪的行动项

### 报告格式要求
- 使用 Markdown 格式
- 重要发现使用 **加粗** 或 `代码块`
- 问题项使用 `- [ ]` 或 `- [x]` 标记状态
- 建议项使用 `> 建议：` 引用格式
- 行动项使用 `**行动**：` 强调格式

## 建议转 suggest 池

主 agent 在保存 `done-report.md` 后，必须执行以下动作：

1. **提取建议**：读取 `done-report.md` 中的 `## 改进建议` 区块
2. **过滤去重**：去除空行、重复建议
3. **创建 suggest**：对每条有效建议调用 `create_suggestion(root, content)`
4. **记录结果**：在 `session-memory.md` 中记录创建的 suggest ID 列表

> **注意**：如果 done-report 中没有改进建议，或建议已全部存在于 suggest 池中，则跳过此步骤。
