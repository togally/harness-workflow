# 每个需求在各个阶段的流转可以做一个记录，然后我可以指定校验某个项目的流程是否符合我们的要求

> req-id: req-14 | 完成时间: 2026-04-15 | 分支: main

## 需求目标

- 在需求经过 `harness next` 阶段切换时，自动记录进入每个阶段的时间戳
- 提供 `harness validate` 命令，校验当前项目的流程是否合规（如是否缺少必要的测试报告、验收报告等）

## 交付范围

**包含**：
- `harness next` 自动在 requirement state YAML 中写入 `stage_timestamps`
- 新增 `harness validate` CLI 命令及对应核心函数
- `validate` 检查当前激活需求的必要产物是否齐全

**不包含**：
- 可视化图表或 Web 界面
- 对已完成归档需求的回溯校验

## 验收标准

- [ ] `harness next` 时，当前需求的 `stage_timestamps` 会记录新阶段的时间戳
- [ ] `harness validate` 能输出当前需求在各阶段缺少的产物或报告
- [ ] 文档已更新

## 变更列表

- **chg-01** 阶段时间戳自动记录：在 `harness next` 切换阶段时，自动为当前需求记录进入新阶段的时间戳。
- **chg-02** 新增 validate 命令：提供 `harness validate` 命令，自动检查当前激活需求的流程产物是否完整。
- **chg-03** 文档与验证：更新 README 文档，验证新功能，并重新安装包。
