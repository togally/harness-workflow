# Change: chg-01

## Title

`harness ff` 命令语义增强设计

## Goal

重新定义 `harness ff` 的语义，使其能够从 `requirement_review` 或 `planning` 启动后，自动驱动需求一路走到 `done`，中间各阶段实质工作保留，但取消人工确认阻塞点。

## Scope

**包含**：
- `harness ff` 的启动条件（哪些 stage 可以启动 ff）
- ff 模式下各 stage 的"完成判定"规则（AI 自主判定何时可以推进到下一 stage）
- ff 模式的终止条件（正常终止 vs 异常终止）
- ff 模式下 AI 自主决策的边界（什么可以自行决定，什么必须停下来向用户求援）
- 在 `stages.md` 中更新 `harness ff` 的完整定义

**不包含**：
- `runtime.yaml` 的结构修改（属于 chg-02）
- 角色文件的具体文案更新（属于 chg-03）
- 实际代码/脚本实现（属于 chg-02 和后续执行）

## Acceptance Criteria

- `stages.md` 中 `harness ff` 的定义包含：
  - [ ] 启动条件
  - [ ] 自动推进规则
  - [ ] AI 自主决策边界
  - [ ] 失败处理路径
- 文档经过 review 无逻辑冲突
