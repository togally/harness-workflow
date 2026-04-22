# Change

## 1. Title

端到端 smoke：验证 sug-01~sug-06 集成后的闭环无回退

## 2. Goal

在 chg-01 ~ chg-05 全部合入后，通过**一次完整的 requirement 生命周期**验证 sug-01~sug-06 集成效果：

- 全流程命令无需人工改 yaml；
- 无目录命名异常（空格 / 缺前缀）；
- 无归档路径双层 branch；
- 每个 stage 都产出对应的中文对人文档。

本 change 是 req-26 的收口，不引入新能力。

## 3. Requirement

- `req-26`

## 4. Scope

### Included

- 设计并执行一次端到端 smoke 脚本（或人工操作剧本），覆盖：
  - 新建 requirement；
  - requirement_review → planning → executing → testing → acceptance → done；
  - 中途至少一次 `harness regression --confirm`；
  - 中途至少一次 `harness rename`；
  - `harness archive` 成功收尾。
- 在每个 stage 后核对对人文档产出与命名。
- 产出一份 smoke 报告（落到本 change 自己的 `artifacts/` 目录下，作为本 change 的交付凭证），记录每条 AC 的核对证据。

### Excluded

- 不修复任何 CLI 代码。如 smoke 中发现新 bug：
  - 属于 chg-01 ~ chg-05 已修缺陷的回退 → 报告主 agent 走 regression；
  - 属于新缺陷 → 登记到本 change 的遗留问题清单，由后续 bugfix / 需求承接。
- 不做性能 / 压力测试。
- 不动 `.workflow/flow/` 历史文档、不清洗 `artifacts/` 历史脏数据。

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-07**：完整链路一次跑通，六条 sug 集成效果逐条可核对。
- 同时作为 AC-01 ~ AC-06 的终极集成验证（非取代单元级验证）。

## 6. Risks

- chg-01 ~ chg-05 合入顺序差异可能让本 change 先于前置合入就开跑 → 必须在执行前硬性校验前 5 个 change 已 executed / acceptance 通过；
- smoke 脚本若写成一次性命令序列，难以调试 → 建议分阶段，每步留 checkpoint（打印 state、列产物目录）；
- 人工 smoke 与自动化 smoke 取舍：若项目测试栈支持（pytest + subprocess），优先自动化；否则落为人工剧本。
