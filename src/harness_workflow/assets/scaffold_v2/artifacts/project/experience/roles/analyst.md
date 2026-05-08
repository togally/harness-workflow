---
schema_version: 1
scope: experience-roles
created_by: req-55（gstack 和 harness 工作流融合）/ chg-05（dogfood 活证 — 候选 P 第 8 轮重写）
---

# analyst 项目级经验文件

> 本文件是 analyst 角色在本项目中积累的经验沉淀，覆盖跨 req 的实操观察、retro 笔记和改进方向。

## gstack-harness 融合 retro（首次填写：req-56+）

> 占位段：本节由下一个真实 `/harness-requirement` 触发时由其 analyst 在 chg-02 adapter SOP 完成后回填。回填时把"req-56+"替换为实际触发的 req-id。

### 1. 调 /office-hours 的姿势
- 触发协议路径 α 实操经验（subagent 提示主 agent → 用户跑 → 反馈 path → analyst 跑 adapter）
- 实际触发是否流畅 / 用户疑惑点 / 反馈 path 时是否正确

### 2. adapter 章节 mapping 实操细节
- 哪些段 mapping trivial（如 Success Criteria → Acceptance Criteria）
- 哪些段需人工裁剪（如 Recommended Approach 多技术细节）
- 哪些段映射不到位（mapping 表 fallback 是否够用）
- 是否需要反馈给 chg-02 修订 adapter mapping 表

### 3. fallback 触发场景
- 本次是否触发 fallback？
- 假设性观察："如果用户拒跑 /office-hours，体验如何"

### 4. 多余段处理选择
- 本次按 adapter SOP 全保留追加到 Office Hours Notes？还是部分裁剪？
- 保留量是否影响 requirement.md 可读性
- 给后续 req 的改进方向
