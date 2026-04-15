# Change: chg-01

## Title
Git 提交询问与执行

## Goal
在 `archive_requirement` 成功后，检测 Git 仓库并询问用户是否自动提交归档变更。

## Scope

**包含**：
- 修改 `core.py` 中的 `archive_requirement`
- 归档成功后检测当前目录是否为 Git 仓库（通过 `.git` 目录或 `git rev-parse --is-inside-work-tree`）
- 若是 Git 仓库，通过 `input()` 询问用户是否提交
- 用户确认后执行 `git add -A` 和 `git commit -m "archive: req-XX-title"`
- 可选询问是否 `git push`

**不包含**：
- 修改归档的核心移动逻辑
- 自动 push（需用户确认）

## Acceptance Criteria

- [ ] 归档成功后检测到 Git 仓库并询问提交
- [ ] 用户确认后正确执行 `git add` 和 `git commit`
- [ ] 非 Git 仓库时不报错
