# Regression Intake

## 1. Issue Title

change meta.yaml status 字段从未被工具更新，始终停留在 draft

## 2. Reported Concern

`harness status` 和 `workflow-runtime.yaml` 显示 `stage: done`，但所有 change 和 requirement 的 `meta.yaml` 中 `status` 仍为 `draft`。用户困惑：是否真的完成了流程，还是状态记录有误？

## 3. Current Behavior

- **复现路径**：完整走完一个版本（requirement → changes → plan → execution → done）后，检查各 change 的 `meta.yaml`
- **实际表现**：`workflow-runtime.yaml` 和版本级 `meta.yaml` 均显示 `stage: done, status: done`；各个 change 的 `meta.yaml` `status` 字段始终为 `draft`（初始值，从未被任何 harness 命令更新）
- **代码根因**：`core.py` 中 `apply_stage_transition` 只更新版本级状态；`update_item_meta` 仅在 regression 场景更新 regression 制品的状态；change/requirement 的 `meta.yaml` `status` 字段从未被工具写入
- **影响范围**：`harness status` 输出误导性信息；若未来功能依赖 change `status` 过滤或查询，会出错；`harness archive` 可能无法识别已完成的 change

## 4. Expected Outcome

每个 change 和 requirement 的 `meta.yaml` `status` 应随工作流推进而更新：
- change 被 `harness change` 创建时：`draft`
- 进入 executing 阶段时：`in_progress`
- 执行完成验证通过后：`done`
- requirement 同理

## 5. Next Step

问题已确认为真实设计缺陷，需要转为新 change 修复。
