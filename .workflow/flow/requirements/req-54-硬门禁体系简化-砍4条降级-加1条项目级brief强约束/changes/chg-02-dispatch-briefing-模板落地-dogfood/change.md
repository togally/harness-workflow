---
id: chg-02
title: "dispatch-briefing-模板落地-dogfood"
parent_req: req-54
operation_type: change
---

## Goal

把 chg-01 在 base-role.md / harness-manager.md 落下的「硬门禁八：subagent dispatch briefing 必含项目级加载链提示」**实操化**——给主 agent / harness-manager 的派发流程写出可复制的 boilerplate 字面段，并在本会话主 agent 后续派发自身（含本 req-54 后续 stage）时按硬门禁八注入 brief，dogfood 自证。

## Scope

### In scope

- **chg-01 落地后再实施**（依赖 base-role.md 硬门禁八整段已存在）。
- harness-manager.md §3.6.2（chg-01 已写占位）正文**完整化**，给出三块字面 boilerplate 段、scope 枚举、违反判定 grep 命令。
- 在 harness-manager.md 的「派发协议」「构建 briefing」步骤说明中显式列出新字段：`project_level_loading_brief`（即注入的 boilerplate 字面段）；briefing 构造伪代码追加该字段。
- 在 base-role.md 「Subagent 嵌套调用规则」段（L273+）的「**派发协议**」小节内追加一条 **第 5 项**：`5. 项目级加载链提示（必含）：按硬门禁八，briefing 必显式包含 role-loading-protocol Step 7.6 / 7.6.1 + boilerplate 字面段 + scope 字段。`
- **dogfood 自证**：本会话主 agent 在 chg-02 / chg-03 后续 stage 派发 subagent 时，必须按硬门禁八注入 brief；done 阶段交付总结记录"硬门禁八 dogfood 自证"行（落 done.md 阶段产出，非本 chg 直接产物，但本 chg 提供 brief 模板供主 agent 引用）。
- 4 mirror 同步（与 chg-01 同款 4 文件子集中的 base-role.md + harness-manager.md 两文件）。

### Out of scope

- 不动 src/ Python 代码（briefing 字段构造是文档约束，不需要 helper 改动；现有 `harness-manager.md` 已用伪代码描述 briefing 构造，本 chg 仅在文档层增加 `project_level_loading_brief` 字段）。
- 不动 tests/（chg-03 负责）。
- 不动 stage-role.md / WORKFLOW.md（chg-01 已处理）。

## Acceptance

- AC-04 / AC-05 / AC-08（来自 req-54 requirement.md）
- harness-manager.md §3.6.2 含完整 boilerplate 字面 + scope 枚举 + 违反判定（不再是 chg-01 占位）
- base-role.md 「派发协议」第 5 项命中
- 本会话主 agent 在 chg-02 完成后下一次派发 subagent 时（如 chg-02 → chg-03 之间），briefing 必含 `artifacts/project/` + `Step 7.6` 字面（dogfood 实证）

## Dependencies

- 上游：chg-01（base-role.md 硬门禁八整段 + harness-manager.md §3.6.2 占位已落地）
- 下游：chg-03（lint chg-02 落地的 boilerplate 段是否齐全）
