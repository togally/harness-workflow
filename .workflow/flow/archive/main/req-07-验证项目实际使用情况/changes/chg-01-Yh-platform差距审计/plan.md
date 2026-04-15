# Plan: chg-01

## Steps

1. 读取 Yh-platform 的 `stages.md`、各角色文件、约束文件、工具清单
2. 读取 harness-workflow 的最新对应文件
3. 逐文件对比差异，记录到审计报告：
   - `stages.md`：缺少 ff 模式、时长记录等章节
   - 角色文件：是否缺少 ff 说明、done 报告模板是否过时
   - 约束文件：`boundaries.md`、`recovery.md` 是否完整
   - 工具清单：是否有新增工具未同步
4. 对比 `state/` 结构：
   - `runtime.yaml` 缺少的字段
   - `requirements/*.yaml` 的旧字段名
   - `sessions/` 目录的空缺
5. 对比 `flow/` 结构：
   - archive 中 req-01 的缺失产物
   - requirements 中的残留目录
6. 检查 `harness_workflow` 已安装包的 scaffold 模板路径
7. 产出 `audit-report.md`

## Artifacts

- `audit-report.md`（可放在 req-07 目录下或 session-memory 中）

## Dependencies

- 无
