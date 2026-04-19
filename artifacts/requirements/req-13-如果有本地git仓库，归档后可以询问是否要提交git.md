# 如果有本地git仓库，归档后可以询问是否要提交git

> req-id: req-13 | 完成时间: 2026-04-15 | 分支: main

## 需求目标

在 `harness archive` 成功归档需求后，如果当前项目是 Git 仓库，自动询问用户是否需要执行 `git commit`（附带默认提交信息），并在用户确认后自动提交变更。

## 交付范围

**包含**：
- `harness archive` 成功后检测当前目录是否为 Git 仓库
- 若是 Git 仓库，提示用户并询问是否自动提交
- 提供默认提交信息（如 `archive: req-XX-xxx`）
- 用户确认后执行 `git add` 和 `git commit`
- 可选地询问是否 `git push`

**不包含**：
- 非 Git 仓库的额外处理
- 自动推送（必须经用户确认）
- 复杂的提交信息编辑交互

## 验收标准

- [ ] `harness archive` 成功后，若当前目录是 Git 仓库，提示用户是否提交
- [ ] 用户确认后，自动执行 `git add -A` 和 `git commit -m "archive: req-XX"`
- [ ] 非 Git 仓库或用户拒绝时，不报错且正常结束
- [ ] 文档已更新

## 变更列表

- **chg-01** Git 提交询问与执行：在 `archive_requirement` 成功后，检测 Git 仓库并询问用户是否自动提交归档变更。
- **chg-02** 文档与验证：更新 README 文档，验证 Git 提交流程，并重新安装包。
