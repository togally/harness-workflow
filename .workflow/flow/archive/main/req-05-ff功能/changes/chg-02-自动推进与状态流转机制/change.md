# Change: chg-02

## Title

自动推进与状态流转机制

## Goal

为 ff 模式提供状态标记和自动推进能力，使主 agent 能够在 ff 模式下自动调用 stage 推进逻辑，无需用户手动输入 `harness next`。

## Scope

**包含**：
- `runtime.yaml` 中增加 ff 模式状态字段（如 `ff_mode: true`）
- 主 agent 识别 ff 模式后的行为调整
- ff 模式下自动推进时 session-memory 的保存和加载规范
- 流转规则中 ff 模式的特殊处理（如自动调用 `harness next` 等价逻辑）

**不包含**：
- 修改 `harness` CLI 工具本身（如 `harness.py` 的 argparse）
- 非 ff 模式下的状态流转改动

## Acceptance Criteria

- [ ] `runtime.yaml` 能够记录 `ff_mode` 状态
- [ ] 主 agent 在 ff 模式下能够识别并自动推进 stage
- [ ] ff 模式下每次 stage 推进时，session-memory 保存完整
- [ ] 文档化 ff 模式的状态流转规则
