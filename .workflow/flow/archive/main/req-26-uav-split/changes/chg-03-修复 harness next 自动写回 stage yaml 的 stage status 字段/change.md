# Change

## 1. Title

修复 `harness next`：自动写回 `.workflow/state/requirements/{id}.yaml` 的 `stage` / `status`

## 2. Goal

让 `harness next` 在推进 stage 时，除了修改 `.workflow/state/runtime.yaml` 之外，**同时**自动写回 `.workflow/state/requirements/{id}.yaml`（以及 `bugfixes/{id}.yaml`，如适用）的 `stage` / `status` 字段，消除 `harness archive` 对人工改 yaml 的依赖。

## 3. Requirement

- `req-26`

## 4. Scope

### Included

- 修 `harness next` 推进逻辑：推进成功后，同步写 `.workflow/state/requirements/{id}.yaml` 的 `stage` / `status`；
- 处理三种场景：
  - 普通 stage 推进（requirement_review → planning → executing → testing → acceptance → done）；
  - `harness ff`（快速前进）多步推进时，每一跳都落一次写入；
  - `harness regression --confirm` / `--testing` 推进 regression_stage 时，相应更新 regression 的状态文件（与 chg-01 共享常量，不重复实现）。
- 扩写 / 新增回归用例，覆盖"requirement_review → ... → done → archive"完整链路，中途不手工改 yaml。

### Excluded

- 不修改 stage 流转顺序；
- 不扩展 stage yaml 的 schema（仅写已有字段）；
- 不处理历史已错位的 stage yaml（属 Excluded 的历史清洗）。

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-03**：
  - `harness next` 成功推进后，`.workflow/state/requirements/{id}.yaml` 的 `stage` / `status` 与 runtime.yaml 一致；
  - 完整链路回归用例无需人工改 yaml。

## 6. Risks

- stage yaml 与 runtime.yaml 双份状态一致性风险：需要明确"以 runtime.yaml 为单一真相源，stage yaml 是物化缓存"或反之，实施时必须文档化抉择并在代码中体现；
- 并发风险：CLI 为单进程单次调用，不考虑并发写，但必须保证单次命令内"写 runtime + 写 stage yaml"原子（失败任一都回滚）。
