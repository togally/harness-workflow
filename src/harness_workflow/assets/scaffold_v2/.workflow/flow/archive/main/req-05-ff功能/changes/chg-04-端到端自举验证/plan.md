# Plan: chg-04

## Steps

1. 等待 chg-01~chg-03 全部完成
2. 在当前会话或新会话中，确认 `runtime.yaml` 中 `current_requirement` 为 `req-05-ff功能`
3. 手动或通过 `harness ff` 启动 ff 模式（根据 chg-02 的实现）
4. 让 AI 自动完成 planning → executing → testing → acceptance → done 的推进
5. 在每个 stage 结束时检查产出完整性
6. 完成后执行 `harness archive req-05-ff功能`
7. 撰写 ff 模式的经验总结，更新到 `.workflow/context/experience/stage/` 或新建 `.workflow/context/experience/tool/harness-ff.md`
8. 撰写 skill 缺失处理与平台错误恢复的经验总结，更新到 `.workflow/context/experience/tool/` 或 `constraints/` 相关经验文件
9. 输出自举验证报告

## Artifacts

- 归档后的 `.workflow/flow/archive/main/req-05-ff功能/`
- 更新的经验文件
- 自举验证报告（可写入 `session-memory.md` 或独立文件）

## Dependencies

- 依赖 chg-01、chg-02、chg-03 全部完成
