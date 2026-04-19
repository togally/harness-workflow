# Plan: chg-01

## Steps

1. 读取当前 `stages.md`，分析 `harness ff` 的现有定义和 stage 流转规则
2. 设计 ff 模式的启动条件：
   - 允许从 `requirement_review` 启动（需求文档已产出）
   - 允许从 `planning` 启动（已有 change/plan 文档或用户明确说 ff）
3. 设计 ff 模式下各 stage 的自动完成判定规则：
   - `requirement_review`：requirement.md 包含背景、目标、范围、验收标准 → AI 可自主确认
   - `planning`：所有变更都有 change.md + plan.md → AI 可自主确认
   - `executing`：所有 plan 步骤完成且内部测试通过 → AI 可自主确认
   - `testing`：测试运行通过，报告已产出 → AI 可自主确认
   - `acceptance`：验收标准已核对通过 → AI 可自主确认
   - `done`：六层回顾完成 → 终止或进入 archive
4. 设计 AI 自主决策边界：
   - 可以自行决定：文档补充、拆分规则细化、测试策略选择、小型实现细节
   - 必须停下来：涉及外部系统凭据、可能破坏生产环境、用户意图不明确、regression 无法自动恢复
5. 设计失败处理路径：
   - 遇到 regression 时，AI 尝试自动诊断和修复（一次）
   - 若仍无法解决，ff 模式暂停，转为正常模式等待用户输入
6. 编写更新后的 `stages.md` 中 `harness ff` 章节
7. 自我 review：检查与现有 stage 定义是否有冲突

## Artifacts

- 更新后的 `.workflow/flow/stages.md`

## Dependencies

- 无（本变更为首个设计变更，为后续变更提供语义基础）
