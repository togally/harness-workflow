# chg-03: 实现 `harness bugfix` 命令

## 变更目标

在 Harness CLI 中新增 `harness bugfix "<issue>"` 子命令，支持创建 bugfix 需求目录、初始化状态文件，并进入 regression 阶段。

## 变更范围

- `src/harness_workflow/cli.py`（或等效的 CLI 入口文件）
- `src/harness_workflow/core.py`（状态管理/目录创建逻辑）
- `pyproject.toml`（如有入口点变更）

## 验收标准

- [ ] `harness bugfix "xxx"` 命令可用
- [ ] 命令执行后创建 `.workflow/flow/bugfixes/bugfix-{id}-{title}/` 目录
- [ ] 目录内生成 `bugfix.md`、`session-memory.md`、`regression/diagnosis.md`（空模板）
- [ ] `runtime.yaml` 的 `current_requirement` 更新为 `bugfix-{id}`，`stage` 更新为 `regression`
- [ ] `state/bugfixes/bugfix-{id}.yaml` 状态文件已创建
