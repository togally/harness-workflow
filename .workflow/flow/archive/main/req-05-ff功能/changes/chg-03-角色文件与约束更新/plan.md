# Plan: chg-03

## Steps

1. 读取 `WORKFLOW.md`，分析主 agent 现有职责
2. 在 `WORKFLOW.md` 中增加"ff 模式协调职责"小节：
   - 主 agent 负责检测 `ff_mode` 标记
   - 负责在当前 stage 完成后自动推进到下一 stage
   - 负责在遇到边界外问题时暂停 ff 模式并向用户报告
3. 读取各阶段角色文件（`planning.md`、`executing.md`、`testing.md`、`acceptance.md`、`regression.md`）
4. 在每个角色文件的"退出条件"附近增加 ff 模式说明：
   - 例如："ff 模式下，若退出条件已满足，subagent 可直接报告完成，由主 agent 自动推进"
5. 读取 `constraints/boundaries.md`
6. 增加 ff 决策边界条目：
   - AI 可以自主决定：文档细化、实现方案选择、测试策略、代码修改（在 plan 范围内）
   - AI 必须暂停求援：涉及凭据/密钥、可能破坏生产环境、用户意图冲突、plan 范围外的大架构改动
7. 读取 `constraints/recovery.md`
8. 增加"平台级错误/会话损坏"恢复条目：
   - 场景：连续 API Error 400 且 harness 命令失效
   - 恢复步骤：先尝试 `/compact`，再尝试 `/clear`，最后建议新开 agent 并通过 `handoff.md` 恢复
9. 增加"skill 缺失"处理条目：
   - 场景：agent 调用 `Skill(xxx)` 返回 "Unknown skill"
   - 处理步骤：
     1. 先通过 `Read` 或 `Bash` 检查当前可用 skills（如检查 skill 目录）
     2. 尝试搜索功能相近的已安装 skill 或工具
     3. 如存在可安装 skill，尝试安装
     4. 如无法找到替代方案，记录问题并转由用户决策
   - 禁止：在 skill 缺失时直接失败卡住而不尝试恢复
10. 检查所有修改的一致性

## Artifacts

- 更新后的 `.workflow/WORKFLOW.md`
- 更新后的 `.workflow/context/roles/*.md`（按需）
- 更新后的 `.workflow/constraints/boundaries.md`
- 更新后的 `.workflow/constraints/recovery.md`

## Dependencies

- 依赖 chg-01 的 ff 语义设计
- 依赖 chg-02 的状态流转机制
