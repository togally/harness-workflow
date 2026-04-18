# Change: chg-02

## Title

CLI 命令实现

## Goal

在 `core.py` 和 `cli.py` 中实现 suggest 的增删查用命令。

## Scope

**包含**：
- `harness suggest "<content>" [--title <title>]`
- `harness suggest --list`
- `harness suggest --apply <id>`
- `harness suggest --delete <id>`
- 更新 CLI 参数解析

**不包含**：
- 修改现有 requirement/change 的创建逻辑（直接复用）

## Acceptance Criteria

- [ ] 四个命令均已实现并能正确操作文件
- [ ] `--apply` 能正确调用 `create_requirement` 并创建正式需求
- [ ] 命令有适当的错误提示
