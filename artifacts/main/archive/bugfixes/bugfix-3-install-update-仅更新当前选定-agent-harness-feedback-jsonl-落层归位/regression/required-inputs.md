# Regression Required Inputs · bugfix-3

诊断师 (regression Subagent-L1) 已完成只读独立诊断，**未发现需要人工补充的硬阻塞**。
本文件保留以备 testing/executing 阶段如遇下列开放问题，可向人请援。

## 1. Current Problem

- Issue summary: install/update 跨 agent 全量刷新；`.harness/feedback.jsonl` 落在六层架构外
- Related regression: bugfix-3
- Linked change: 待 testing 拆分

## 2. Required Human Inputs（**当前均为 no**，仅作 testing/executing 备查）

| Item | Required | Notes |
| --- | --- | --- |
| Configuration | no | 无外部配置依赖 |
| Test data | no | 已有现成 `.harness/feedback.jsonl` 数据（主仓 182 行 / PetMall 28 行）作为迁移测试 fixture |
| Account details | no | 不涉及外部账号 |
| External dependency details | no | 纯本地代码 / 文件改动 |

## 3. 可向人确认的开放问题（非阻塞，testing/executing 决定时再问）

下列问题诊断师无法独立定夺，留给 testing/executing 阶段或主 agent 决策；如需人工拍板，再请人答复：

### Q1. 历史 `.harness/feedback.jsonl` 数据是否保留？

- 选项 A（**诊断师推荐**）：保留 + 自动迁移到 `.workflow/state/feedback/feedback.jsonl`（数据连续，`harness feedback` 历史汇总不断档）。
- 选项 B：清空，从迁移当天重新累积（`harness feedback` 失去历史）。
- 选项 C：保留旧位置只读快照 `.workflow/context/backup/feedback-pre-migration.jsonl`，新位置从空开始。

### Q2. `update_repo` 是否提供 `--all-platforms` escape hatch？

- 选项 A（**诊断师推荐**）：提供。迁移期某些用户可能短期内同时用 codex + claude 双开，需要保留全量刷新能力，作为 `active_agent` 主路径外的兜底。
- 选项 B：不提供。强制 single-agent 语义；多 agent 用户只能多次 `harness install --agent X` 切换。

### Q3. `platforms.yaml.enabled[]` 字段是否仍保留？

- 选项 A（**诊断师推荐**）：保留。`enabled` = "兼容池"（哪些 agent 目录可以共存而不会被清理）；`active_agent` = "当前操作目标"。两者解耦。
- 选项 B：废弃 `enabled[]`，只留 `active_agent`，并在 update 时清理非激活 agent 的目录。**风险**：会破坏现存多 agent 项目（如 PetMall 同时挂着 codex/claude/qoder/kimi 全套）。

### Q4. `bugfix-3` ID 复用是否同期一起修？

- 选项 A：不一起。本 bugfix 范围只两条；编号问题另立独立缺陷（已在 diagnosis.md "衍生发现"登记）。
- 选项 B：搭便车一起修。**风险**：跨范围、易超时、违反"最小修复"原则。

## 4. Next Step

- testing 阶段读本文件 → 决定是否需要就 Q1~Q4 向人请援
- 若 testing 直接采纳"推荐"，无需打扰人，diagnosis.md 已具备实施所需全部技术信息
