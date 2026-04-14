# Requirement

## 1. Title

done 报告头部记录实现时长

## 2. Goal

当前需求走完整个 Harness workflow 后，产出的 `done-report.md`（以及可能的 `testing-report.md`、`acceptance-report.md`）头部缺少对"需求实现耗时"的记录。

这导致：
- 无法快速回溯一个需求从创建到完成的总周期
- 无法评估各阶段的耗时分布，难以识别流程瓶颈
- 归档后的需求缺少关键的时间维度元数据

本需求的目标：**在 done 报告（及相关制品报告）的头部增加实现时长记录**，定义时长的计算方式、展示格式和数据来源，使每个归档需求都带有清晰的时间度量。

## 3. Scope

**包含**：
- 定义"实现时长"的计算口径（总时长 vs 分阶段时长）
- 确定需要增加时长记录的报告类型（至少包含 `done-report.md`）
- 设计时长展示格式（头部元数据表格或固定字段）
- 确定数据来源和采集方式（`state/requirements/{id}.yaml`、`runtime.yaml` 或其他状态文件）
- 更新 `done.md`（done 阶段检查清单）或相关模板，要求 done 阶段必须填写时长
- 更新现有已归档需求的报告（可选，如模板更新后新需求生效即可则不必追溯）

**不包含**：
- 实时自动计时系统的开发（不引入后台守护进程或定时器）
- 改变各阶段的核心工作方式（只增加报告头部的元数据字段）
- 非 Harness workflow 报告的其他文档模板

## 4. Acceptance Criteria

- [ ] `done-report.md` 头部包含"实现时长"字段，格式统一、可读
- [ ] 时长的计算口径在 `stages.md` 或相关文档中有明确定义
- [ ] 数据来源稳定可靠（不依赖易丢失的会话上下文）
- [ ] 至少一个示例报告（req-06 自身或另一个示例）验证了时长记录的正确性
- [ ] 如果涉及 `state/requirements/{id}.yaml` 或 `runtime.yaml` 字段变更，文档已同步更新

## 5. Split Rules

### chg-01 实现时长定义与数据采集机制

定义"实现时长"的计算口径：
- **总时长**：从 `requirement_review` 阶段开始到 `done` 阶段结束的时间跨度
- **分阶段时长**（可选）：各 stage 的停留时间
- 数据来源：
  - 方案 A：在 `state/requirements/{id}.yaml` 中记录各 stage 的进入时间戳
  - 方案 B：在 `runtime.yaml` 中记录当前需求的 `started_at` 和 `completed_at`
  - 方案 C：从 `session-memory.md` 或 `git log` 中间接推算
- 评估并选定一个主方案，必要时设计降级策略

### chg-02 报告模板更新

更新 `done.md`（done 阶段检查清单）中的报告输出规范：
- 在 `done-report.md` 头部增加固定格式的时长记录区块
- 可选同步更新 `testing-report.md`、`acceptance-report.md` 的头部格式
- 提供模板示例，确保后续需求可直接复用

### chg-03 端到端验证

用 req-06 自身验证新机制：
- 从 requirement_review 走到 done
- 检查 `done-report.md` 头部的时长记录是否准确
- 如发现现有 stage 时间数据缺失，验证降级策略是否生效
