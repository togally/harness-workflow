# Requirement

## 0. Background

harness-workflow 作为工具被安装到其他项目中使用。需要验证在全新的外部仓库中，完整命令链路、脚本、产出目录与文件结构是否符合预期，避免用户从 git 克隆后首次使用出现断裂（例如命令找不到、脚本报错、产出目录结构错误、agent skill 安装路径错误、状态机流转异常等）。本需求旨在通过一次系统性的端到端回归测试，覆盖 harness-workflow 作为"外部工具"被消费时的真实用户路径，沉淀问题清单与修复优先级，保障新用户的首次使用体验。

## 1. Title

全面回归测试 harness-workflow 在新项目中的端到端可用性

## 2. Goal

- 在一个真实的外部项目仓库中，端到端验证 harness-workflow 的完整闭环：从 `harness install` 到 `harness archive` 的全部命令链路、脚本、产出、状态流转均可正常工作。
- 产出一份问题清单，包含每个问题的重现步骤、期望行为、实际行为与修复优先级（P0 / P1 / P2）。
- 为后续修复变更提供可排序、可追踪、可验证的输入。

## 3. Scope

### 3.1 包含

1. **全部 `harness <命令>` 入口**在新仓库中的行为验证，至少覆盖：
   - `install` / `update` / `status`
   - `requirement` / `change` / `bugfix`
   - `next` / `ff` / `regression`
   - `archive` / `suggest`
   - `tool-search` / `tool-rate`
   - `feedback` / `language` / `enter` / `exit` / `validate`
2. **所有产出目录与文件**的结构与内容正确性：
   - `artifacts/{branch}/requirements/`
   - `artifacts/{branch}/changes/`
   - `artifacts/{branch}/bugfixes/`
   - `artifacts/{branch}/archive/`
3. **所有脚本与 CLI 函数**执行正常，包括但不限于：
   - `harness_workflow.core` 模块
   - `workflow_helpers` 模块
   - 其他内部辅助脚本
4. **四个 agent skill 安装路径**验证：
   - codex
   - claude
   - kimi
   - qoder
5. **状态机流转**与 `runtime.yaml` 字段一致性：
   - `harness next` 正常推进 stage
   - `harness ff` 快进模式正确跳过允许阶段
   - `harness regression` 回归路由正确
   - `runtime.yaml` 字段（`current_requirement` / `stage` / `ff_mode` / `active_requirements` 等）与实际流转一致

### 3.2 排除

- **不包含**性能测试、压力测试、并发测试。
- **不包含**对已知历史遗留问题的深度根因分析（本轮只负责发现与记录）。

### 3.3 测试环境

- 必须在**真实的外部项目仓库**中执行。
- **不允许**使用 `/tmp` 目录或任何临时占位目录模拟。
- 该外部仓库需模拟典型的首次用户场景（全新克隆 / 全新安装）。

#### 3.3.1 具体方案：新建空仓库（方案 A）

采用**新建空仓库**方案作为本轮回归的测试环境：

- 在本机**临时路径**下新建一个空 git 仓库（`git init` 产物，无历史、无代码、无任何业务文件）。
- 新建完成后，在该空仓库中执行 `harness install`，再依次执行 3.1.1 列出的全部命令链路。
- **目的**：最大化环境纯净度，排除宿主项目已有代码、目录结构、配置文件对 harness-workflow 的干扰，模拟"全新用户首次从 git 克隆 harness-workflow 并在零业务上下文的项目中使用"的真实场景。
- 该仓库的生命周期仅限本次回归，回归结束后可保留用于复盘，不得被纳入任何正式代码基线。

### 3.4 Artifacts：回归过程的原始日志归档

- 每条 `harness <命令>` 执行时，必须**原样留存** stdout 与 stderr，不允许截断或摘要后写入。
- 日志归档根路径：本 req-25 目录下新建子目录 `regression-logs/`。
- 日志按 **chg-id 分组**存放：`regression-logs/<chg-id>/`。
- 日志文件命名规范：`<命令序号>-<命令名>.log`，例如：
  - `regression-logs/chg-01/01-install.log`
  - `regression-logs/chg-01/02-status.log`
  - `regression-logs/chg-02/01-requirement.log`
- 命令序号按执行顺序自 01 起递增；同一 chg 内命令序号不重复。
- 日志内容格式建议：文件开头注明命令全文、执行时间、工作目录，其后贴原始 stdout/stderr。

## 4. Acceptance Criteria

1. **命令覆盖完整性**：3.1.1 中列出的所有 `harness <命令>` 入口在新仓库中均被执行过至少一次，每条命令在问题清单中均有"通过 / 存在问题"的明确标注。
2. **产出结构一致性**：3.1.2 中列出的所有产出目录与文件，结构与内容与 `WORKFLOW.md`、`SKILL.md` 中规定一致；任何不一致均作为问题记录。
3. **脚本可执行性**：3.1.3 中列出的所有脚本与 CLI 函数均可被调用且无致命错误；非致命错误（警告、兼容性提示）记录在问题清单中。
4. **Agent skill 安装正确性**：3.1.4 中四个 agent skill 路径（codex / claude / kimi / qoder）在新仓库中均可正确安装与被识别；任何路径或识别失败均作为问题记录。
5. **状态机一致性**：3.1.5 中的所有状态流转动作执行后，`runtime.yaml` 字段变化与预期完全一致；任何字段漂移、遗漏或错配均作为问题记录。
6. **问题清单完整性**：最终产出的问题清单必须包含以下字段，且每条缺一不可：
   - 重现步骤
   - 期望行为
   - 实际行为
   - 修复优先级（P0 / P1 / P2）
7. **P0 问题必须在 req-25 内闭环**（收口边界）：
   - 所有被标注为 **P0（阻断性）** 的问题，**必须在本 req-25 周期内修完并回归验证通过**，才能推进到 acceptance 并完成验收。
   - P0 的定义：导致任一 `harness <命令>` 入口无法执行、产出目录结构错误不可用、状态机流转错乱无法恢复、或 agent skill 在新仓库中完全无法识别等"阻断用户首次使用"的问题。
   - P0 闭环的证据要求：修复对应的 change 已 merge，且在同一空仓库或等价新建空仓库中**重新执行**该命令链路，日志入 `regression-logs/` 并确认已消除。
8. **P1 / P2 允许延期，但必须注明延期原因**：
   - P1（重要非阻断）与 P2（体验 / 文案 / 边缘场景）问题允许列入清单延至后续 req 处理。
   - 每条被延期的 P1 / P2 问题在最终报告中必须注明：
     - 延期原因（为什么本轮不修）
     - 负责人预估（后续由谁主导）
     - 期望闭环的后续 req 标识或预估时间窗
9. **允许已记录的非 P0 问题通过**：只要 P0 全部闭环、P1 / P2 已按 8 的要求逐条记录并明确延期信息，即可视为验收通过；不要求本次需求内修复所有问题。

## 5. Split Rules

- Split the requirement into independently deliverable changes
- Each change should cover one clear unit of delivery
- When the requirement is complete, fill `completion.md` and record successful project startup validation
