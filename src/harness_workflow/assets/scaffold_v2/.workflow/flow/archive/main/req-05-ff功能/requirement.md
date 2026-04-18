# Requirement

## 1. Title

ff 功能自动直行到归档

## 2. Goal

当前 `harness ff`（fast-forward）命令仅能在 `requirement_review` / `planning` 阶段"跳过讨论门，直达执行确认"，仍需要用户在每个关键节点进行人工确认。

本需求的目标是：
- **增强 `harness ff` 命令**，使其能够自动驱动需求从创建一路走到 `done` 甚至 `archive`
- **免除中间阶段的人工确认**：planning、executing、testing、acceptance 各阶段的核心工作仍需完整执行，但遇到需要用户决策的节点时，由 AI 根据上下文和最佳实践自主选出最佳方案并继续
- **保持流程完整性**：不跳过任何 stage 的实质产出（plan.md、代码变更、测试报告、验收报告等），只是移除"等待用户确认"的阻塞点

期望做完后的状态：
- 用户执行 `harness requirement "XXX"` 创建需求
- 用户执行 `harness ff` 后，AI 自动完成 requirement_review → planning → executing → testing → acceptance → done（可选 → archive）的完整闭环
- 每个阶段的产出文件完整，session-memory 齐全，无需人工中途介入

## 3. Scope

**包含**：
- `harness ff` 命令的行为定义与增强设计
- 各阶段"用户确认点"的识别与替代策略（AI 自主决策规则）
- `runtime.yaml` 和 stage 流转规则的适配（支持 ff 模式下的状态自动推进）
- 主 agent 在 ff 模式下的特殊职责（自动 stage 推进、失败时自动触发 regression 或暂停求援）
- 必要的状态标记（如 `ff_mode: true`）和 session-memory 规范
- 现有角色文件和 `stages.md` 中关于 ff 的文档更新
- **skill 缺失时的处理机制**：当 agent 需要调用某个 skill 但发现不存在时，定义搜索、安装替代方案或寻找等效工具的标准流程
- **平台错误恢复机制**：当底层平台调用失败（如连续 API Error 400）导致会话不可用时，定义恢复路径

**不包含**：
- 非 `harness ff` 场景下的流程改动（正常 `harness next` 仍保留人工确认）
- 需要外部 API 或 webhook 才能实现的触发自动化（保持纯本地 CLI 驱动）
- 改变各阶段 subagent 的核心工作方式（只改"确认机制"，不改"工作方式"）
- 引入新的 GUI/Web 界面

## 4. Acceptance Criteria

- `harness ff` 的完整行为在 `stages.md` 中有明确定义：
  - 适用条件（哪些 stage 可以从 ff 启动）
  - 自动推进规则（每个 stage 何时视为"完成"并自动进入下一 stage）
  - AI 自主决策边界（什么情况下 AI 可以自行决定，什么情况下必须停下来向用户求援）
  - ff 失败时的处理路径（进入 regression 还是暂停等待人工）
- `runtime.yaml` 支持记录 ff 模式状态（或等价的机制）
- 主 agent 的 ff 模式职责在 `WORKFLOW.md` 或角色文件中有补充说明
- 提供一个完整的 ff 端到端测试/示例，验证 req-05 自身可以用 ff 模式走完（自举验证）
- `constraints/recovery.md` 中包含 "平台级错误/会话损坏" 和 "skill 缺失" 两类情况的恢复路径
- `context/experience/` 中沉淀本次关于 skill 缺失和平台错误恢复的经验教训

## 5. Split Rules

### chg-01 `harness ff` 命令语义增强设计

重新定义 `harness ff` 的语义：
- 从 `requirement_review` 或 `planning` 启动时，进入 fast-forward 模式
- 明确 ff 模式下各 stage 的"完成判定"由 AI 自主执行（无需用户说"确认"）
- 定义 ff 模式的终止条件：
  - 正常终止：到达 `done`（可选执行 `archive`）
  - 异常终止：遇到无法自主决策的问题、regression 无法自动恢复、上下文爆炸需要 handoff

### chg-02 自动推进与状态流转机制

修改 `runtime.yaml` 和 stage 推进逻辑：
- 增加 ff 模式标识（如 `ff_mode: true`）
- 主 agent 在 ff 模式下自动调用 `harness next` 等价的推进逻辑
- 明确自动推进时如何保存和加载 session-memory

### chg-03 角色文件与约束更新

更新以下文档，补充 ff 模式下的特殊规则：
- `stages.md`：ff 命令的完整定义
- `WORKFLOW.md`：主 agent 在 ff 模式下的协调职责
- 各阶段角色文件（可选）：在"退出条件"中增加"ff 模式下由 AI 自主确认"的说明
- `constraints/boundaries.md`：ff 模式下 AI 自主决策的边界
- `constraints/recovery.md`：新增"平台级错误/会话损坏"和"skill 缺失"两类情况的恢复路径

### chg-04 端到端自举验证与经验沉淀

用 ff 模式完成 req-05 自身的需求归档，作为 live 验证：
- 从 requirement_review 到 archive 全程使用 ff
- 验证所有文件产出完整
- 记录 ff 模式的实际问题和改进点
- 在 `context/experience/` 下沉淀 skill 缺失处理和平台错误恢复的经验教训
