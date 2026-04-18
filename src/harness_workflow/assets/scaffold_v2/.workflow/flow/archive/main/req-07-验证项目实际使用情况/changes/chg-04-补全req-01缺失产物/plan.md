# Plan: chg-04

## Steps

1. 读取 Yh-platform 中 req-01 的所有现有文件：
   - `archive/req-01-dockDetail新增字段/requirement.md`
   - `archive/req-01-dockDetail新增字段/changes/chg-01-.../` 下的 change.md、plan.md、session-memory.md、acceptance-report.md、test-results.md、regression/ 文件
2. 在 `state/sessions/req-01/` 下创建：
   - `session-memory.md`：根据已有记录重放各阶段执行摘要
   - `testing-report.md`：将 `test-results.md` 内容迁移并改名
   - `acceptance-report.md`：迁移已有内容
   - `done-report.md`：根据 req-01 的实际执行过程补全（包含实现时长头部）
3. 删除 `flow/requirements/req-01-dockDetail新增OSD字段/` 残留目录
4. 检查 archive 中 req-01 的结构，确保符合最新规范
5. 更新 `state/requirements/req-01-dockDetail新增字段.yaml` 为 archived 状态且字段规范正确

## Artifacts

- 补全后的 `state/sessions/req-01/` 目录
- 清理后的 `flow/requirements/`
- 完整的 archive 结构

## Dependencies

- 依赖 chg-03 的升级完成
