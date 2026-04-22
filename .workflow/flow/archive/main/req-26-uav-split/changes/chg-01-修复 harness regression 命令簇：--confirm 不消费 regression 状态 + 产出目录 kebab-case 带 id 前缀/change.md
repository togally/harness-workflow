# Change

## 1. Title

修复 harness regression 命令簇：`--confirm` 不消费 regression 状态 + 产出目录 kebab-case 带 id 前缀

## 2. Goal

一次性修好 `harness regression` 命令簇中两处缺陷：

1. `--confirm <issue>` 不再消费/清空 regression 状态，后续 `--testing` 仍可识别并继续消费；
2. regression 生成的产出目录必须使用 kebab-case、且以 regression id 前缀开头（例如 `reg-07-xxx/`），不得含空格、不得无前缀。

两条缺陷同属 `harness regression` 命令簇，共享 CLI 入口代码、状态落盘路径与回归用例脚手架，集中修有助于减少重复开销与回归风险。

## 3. Requirement

- `req-26`

## 4. Scope

### Included

- 修改 `harness regression` CLI 的 `--confirm` 分支：读到 regression 标记后只更新阶段状态（例如 `regression_stage: confirmed`），**不得**清空 `current_regression` 或删除 state/runtime 中的 regression 入口字段。
- 在 `harness regression "<issue>"` 创建新 regression 工作区时，目录命名必须：
  - 使用 kebab-case（空格转 `-`，大写转小写，非法字符过滤）；
  - 以 `reg-{序号}-` 前缀开头；
  - 与 `.workflow/state/` 中的 regression id 保持一致，便于追溯。
- 扩写 / 新增 regression 回归用例：
  - 先 `harness regression --confirm <issue>`，再 `harness regression --testing`，验证状态仍可识别；
  - 调用 `harness regression "issue with spaces"`，验证产出目录为 `reg-XX-issue-with-spaces/` 而非 `regression issue with spaces/`。

### Excluded

- 不修改 regression 阶段的文档模板（required-inputs.md / diagnosis.md 等）路径与内容；
- 不调整 regression 状态在 runtime.yaml 中的 schema；
- 不触碰 `.workflow/flow/regressions/` 下已归档的历史 regression 产物（属 Excluded 的历史清洗）。

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-01**：`--confirm` 后 `--testing` 仍可识别并消费 regression；
- 覆盖 requirement.md 的 **AC-04**：regression 产出目录 kebab-case、带 id 前缀、无空格。

## 6. Risks

- 状态字段含义边界模糊：确认（confirm）与消费（consume）语义需要在 CLI 代码与文档中统一，避免下一轮 regression 又踩同一坑。
- kebab-case 转换的 Unicode 处理：中文 issue 名需保留为中文（与仓库既有命名约定一致），只剔除空格与非法路径字符，不做拼音化。
