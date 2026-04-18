# Requirement

## 1. Title

每个需求在各个阶段的流转可以做一个记录，然后我可以指定校验某个项目的流程是否符合我们的要求

## 2. Goal

- 在需求经过 `harness next` 阶段切换时，自动记录进入每个阶段的时间戳
- 提供 `harness validate` 命令，校验当前项目的流程是否合规（如是否缺少必要的测试报告、验收报告等）

## 3. Scope

**包含**：
- `harness next` 自动在 requirement state YAML 中写入 `stage_timestamps`
- 新增 `harness validate` CLI 命令及对应核心函数
- `validate` 检查当前激活需求的必要产物是否齐全

**不包含**：
- 可视化图表或 Web 界面
- 对已完成归档需求的回溯校验

## 4. Acceptance Criteria

- [ ] `harness next` 时，当前需求的 `stage_timestamps` 会记录新阶段的时间戳
- [ ] `harness validate` 能输出当前需求在各阶段缺少的产物或报告
- [ ] 文档已更新

## 5. Split Rules

### chg-01 阶段时间戳自动记录
- 修改 `core.py` 中 `workflow_next` 逻辑
- 每次进入新阶段时写入 `stage_timestamps[next_stage] = ISO8601 时间戳`
- 回溯补录已有需求的时间戳（可选）

### chg-02 新增 validate 命令
- CLI 增加 `harness validate` 子命令
- 核心函数检查当前 requirement 的 changes 是否都有 testing-report 和 acceptance-report
- 输出缺失项列表

### chg-03 文档与验证
- 更新 README 说明 `harness validate`
- 本地验证时间戳和校验命令
- pipx inject 重新安装
