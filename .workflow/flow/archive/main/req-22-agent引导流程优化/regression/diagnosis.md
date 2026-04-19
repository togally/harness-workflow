# Regression Diagnosis: req-22

## 问题描述

用户在 acceptance 阶段对 req-22 的交付物提出 5 项架构/设计层面的结构性问题：

1. 角色加载协议中应声明所有角色为保证质量都应使用与主 agent 相同的模型
2. 经验文件目前按 stage 划分已不合适，应改为按角色划分，同时修改 base-role 中的经验文件加载说明
3. base-role.md 中的流转规则（按需）已不合适，应由各个角色自己维护；顶级角色对用户目标负责设计流程，其他角色各有自己的流程
4. base-role.md 不应区分"主角色/stage 角色"，它是所有角色必须遵循的通用规约；各角色特色由各自维护；如 stage 角色需要公共规则，应再抽出一个文档继承 base-role，stage 角色再继承该文档
5. 基础角色（base-role.md）中应该包含经验沉淀相关规则

## 证据

- 当前 `role-loading-protocol.md` 中未包含任何关于模型一致性的说明
- 当前 `base-role.md` 标题明确为"所有 stage 角色的抽象父类"，且经验文件加载按 stage 过滤（如 `requirement_review` / `planning` → `requirement.md`）
- 当前 `base-role.md` 中包含"流转规则（按需）"章节，建议读取 `.workflow/flow/stages.md`
- 当前 `base-role.md` 中多次出现"stage 角色"、"主 agent"等概念，将 base-role 的适用范围限定为 stage 角色
- 当前 `base-role.md` 中未包含统一的经验沉淀规则，各角色的经验沉淀行为散落在不同文件的 SOP 末尾

## 根因分析

req-22 的三次 regression 修复已完成了"角色加载协议抽离"和"统一 stage 角色模板"的目标，但在角色继承层级和 base-role 的普适性定位上仍停留在旧架构思维：

1. **base-role 的定位偏差**：`base-role.md` 被设计为"stage 角色的抽象父类"，而非"所有角色的通用规约"。随着技术总监（Director）、工具管理员（toolsManager）等新角色的引入，很多通用准则（如工具优先、操作日志、上下文维护）其实适用于所有角色，而不仅限于 stage 角色。

2. **经验文件组织与角色粒度不匹配**：新增角色后，经验文件仍按 stage 划分（如 `requirement.md`、`development.md`），但同一 stage 内不同角色的经验需求不同（如 planning 阶段架构师和工具管理员所需经验不同），按 stage 加载会造成经验污染或遗漏。

3. **流转规则归属不清**：`base-role.md` 作为"抽象父类"承载了"按需读取 stages.md"的流转规则，但流转规则实际上与角色职责强相关——技术总监负责全局流程守护，stage 角色只关心自己的进入/退出条件，辅助角色不参与流转。将流转规则放在 base-role 中造成了职责耦合。

4. **模型一致性缺失**：当前协议未规定 subagent 应使用与主 agent 相同的模型，可能导致不同 subagent 因模型能力差异而产生执行质量不一致的问题。

5. **经验沉淀规则缺失于通用层**：经验沉淀是所有角色在执行完任务后都应进行的上下文维护动作，但当前没有统一规则说明何时沉淀、沉淀到哪里、沉淀格式是什么。各角色仅在 SOP 末尾零散提及，容易遗漏或格式不一致。

## 结论

- [x] 真实问题
- [ ] 误判

这是 req-22 设计层面的结构性缺陷，需在 planning 阶段重新调整 chg-01 和 chg-02 的设计，并补充到 chg-03 的实现细节中。

## 路由决定

- **问题类型**：需求/设计（实现架构调整）
- **目标阶段**：planning

## 修复方向建议

1. **修改 `role-loading-protocol.md`**：在"核心原则"或"通用加载步骤"中新增模型一致性声明，明确"所有角色（含 subagent）应使用与主 agent 相同的模型以保证执行质量一致性"。

2. **重构经验文件组织**：
   - 将 `context/experience/stage/` 下的经验文件按角色重命名/重组（如 `context/experience/roles/requirement-review.md`、`context/experience/roles/planning.md` 等）
   - 更新 `base-role.md` 中的经验加载说明，改为按角色加载而非按 stage 加载

3. **调整 base-role 定位与职责边界**：
   - 将 `base-role.md` 重新定位为"所有角色必须遵循的通用规约"
   - 删除其中关于"stage 角色专属"的描述
   - 删除"流转规则（按需）"章节，将其下沉到 `technical-director.md` 或各 stage 角色的 SOP 中
   - **新增"经验沉淀规则"章节**：明确所有角色在任务完成后必须检查是否有可泛化的经验，并统一沉淀格式和路径（如 `context/experience/` 下的分类规则）

4. **新建 stage-role.md（可选但建议）**：
   - 若 stage 角色确实存在公共规则（如 Session Start 约定、Stage 切换上下文交接、按角色加载经验文件等），新建 `.workflow/context/roles/stage-role.md`
   - `stage-role.md` 继承 `base-role.md` 的通用规约，并叠加 stage 角色的公共特性
   - 更新 `role-loading-protocol.md`：stage 角色的加载顺序变为 `base-role.md → stage-role.md → {具体角色}.md`
   - 更新所有 stage 角色文件，明确其继承链为 base-role → stage-role

---

## 第五次 Regression 记录

### 触发时间
2026-04-17

### 触发原因
用户在 acceptance 阶段执行 `harness regression`，反馈 2 项测试/验证层面的问题：
1. 项目中的 checklist 是否还符合当前项目情况需要确认
2. 需要新建一个项目测试全流程以及所有 Python 工具是否能正常运行，并在新项目中添加多余配置后再跑 Python 工具验证是否能正确兼容老项目

### 证据

- `tools/lint_harness_repo.py` 运行结果（在当前仓库根目录执行）：
  ```
  Missing required files:
  - .workflow/README.md
  - .workflow/memory/constitution.md
  - .workflow/context/rules/agent-workflow.md
  - .workflow/context/rules/risk-rules.md
  - .workflow/versions
  - .workflow/versions/active
  - .workflow/context/hooks
  - .workflow/context/rules
  - .workflow/templates
  ```
  上述缺失项绝大多数是 req-01 架构重构后已废弃的旧路径（如 `.workflow/versions`、`.workflow/context/rules/agent-workflow.md`），说明 lint 脚本已严重过时。

- `src/harness_workflow/` 下的 CLI 包和测试脚本尚未在当前仓库的最新架构上执行过端到端验证。

### 根因分析

1. **lint 脚本严重过时**：`tools/lint_harness_repo.py` 检查的是旧六层架构/旧工作流（`.workflow/versions`、`.workflow/context/rules/agent-workflow.md` 等），未随 req-01 和 req-22 的架构演进同步更新。这是一个历史遗留问题，但会直接误导任何试图使用它验证仓库健康度的人。

2. **端到端工具链验证缺失**：req-22 的测试验证（V1~V5）主要聚焦于文档结构、角色文件和引导逻辑的可读性/一致性，未包含实际的 Python 工具运行测试（新建空项目 → 初始化 → 运行工具 → 兼容性测试）。用户要求在 acceptance 前补齐这一环，是合理的前置条件。

3. **checklist 与工具的联动问题**：`review-checklist.md` 中提到了"关联脚本同步更新"（来自 `experience/roles/planning.md` 中的经验），但 lint 脚本显然没有被纳入本轮同步范围。

### 结论

- [x] 真实问题
- [ ] 误判

这不是设计层面的返工，而是**实现/测试覆盖度不足**：交付物中包含了已严重过时的验证工具，且缺少端到端的实际运行测试。

### 路由决定

- **问题类型**：实现/测试（工具修复 + 端到端验证补充）
- **目标阶段**：testing

### 修复方向建议

1. **修复/重写 `tools/lint_harness_repo.py`**：
   - 移除对已废弃路径的检查（`.workflow/versions`、`.workflow/context/rules/agent-workflow.md` 等）
   - 新增对新架构核心路径的检查：
     - `WORKFLOW.md`
     - `.workflow/context/index.md`
     - `.workflow/state/runtime.yaml`
     - `.workflow/context/roles/role-loading-protocol.md`
     - `.workflow/context/roles/base-role.md`
     - `.workflow/context/roles/stage-role.md`
     - `.workflow/context/roles/directors/technical-director.md`
     - `.workflow/flow/stages.md`
   - 检查 CLAUDE.md/AGENTS.md 是否引用当前有效的入口文件

2. **端到端 Python 工具验证**：
   - 在临时目录中新建一个空项目
   - 使用 `harness init` 或等效方式初始化 `.workflow` 结构
   - 运行 `harness` CLI 基本命令（如 `harness version`、`harness status` 等）
   - 运行更新后的 `lint_harness_repo.py`，确认在新项目上通过
   - 在项目中添加"多余配置"（如额外文件、自定义目录），再次运行工具验证兼容性/容错性

3. **checklist 对齐**：
   - 确认 `review-checklist.md` 是否因 req-22 的新增产物（如 `role-loading-protocol.md`、`stage-role.md`、经验文件目录改为 `roles/`）需要补充检查项
   - 如有缺失，同步更新

4. **更新 `session-memory.md`**：记录 lint 脚本修复和端到端测试的执行摘要

---

## 第六次 Regression 记录

### 触发时间
2026-04-17

### 触发原因
用户在 acceptance 阶段执行 `harness regression`，反馈内容包含两部分：
1. "沉淀一下测试经验"
2. "想设计一个 bugfix 功能用来快速修复和验证 bug"

### 证据

- req-22 的全部验收标准（chg-04 9 项、chg-05 5 项、brief regression 修复 4 项、需求级 4 项）均已通过独立测试和端到端验证
- 用户未指出 req-22 的任何具体验收项未满足
- "沉淀测试经验"是 done 阶段的标准回顾动作，不是验收失败
- "设计 bugfix 功能"是一个全新的功能需求，与 req-22 的验收范围无关

### 根因分析

1. **不是 req-22 的缺陷**：req-22（agent引导流程优化）的所有交付物（角色继承体系重构、经验文件目录重构、lint 脚本修复、scaffold 模板同步、端到端测试通过）均已满足验收标准。

2. **新需求与旧需求的边界混淆**：用户在 req-22 的 acceptance 阶段提出了一个全新功能（bugfix 快速修复与验证），这应当作为独立的新需求进入 `requirement_review` 阶段，而不是通过 regression 回退到 req-22 的修复流程。

### 结论

- [ ] 真实问题
- [x] 误判

这是用户将"新需求讨论"误用为 `harness regression` 入口。req-22 本身无缺陷，无需进一步修复。

### 路由决定

- **问题类型**：误判
- **目标阶段**：acceptance（回到触发前的 stage）

### 建议

1. **完成 req-22 验收**：确认 req-22 通过，执行 `harness next` 进入 `done` 阶段
2. **在 done 阶段沉淀测试经验**：将端到端测试的教训写入 `experience/roles/testing.md` 或相关经验文件
3. **创建新需求**：执行 `harness requirement "bugfix 快速修复与验证功能"` 启动独立的需求评审流程
