# Requirement

## 1. Title

归档后自动检测 Git 并询问是否提交

## 2. Goal

在 `harness archive` 成功归档需求后，如果当前项目是 Git 仓库，自动询问用户是否需要执行 `git commit`（附带默认提交信息），并在用户确认后自动提交变更。

## 3. Scope

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

## 4. Acceptance Criteria

- [ ] `harness archive` 成功后，若当前目录是 Git 仓库，提示用户是否提交
- [ ] 用户确认后，自动执行 `git add -A` 和 `git commit -m "archive: req-XX"`
- [ ] 非 Git 仓库或用户拒绝时，不报错且正常结束
- [ ] 文档已更新

## 5. Split Rules

### chg-01 Git 提交询问与执行
- 修改 `core.py` 中的 `archive_requirement` 函数
- 归档成功后调用 `_is_git_repo(root)` 检测
- 若是 Git 仓库，通过 `input()` 或等效方式询问用户
- 确认后执行 `git add -A` 和 `git commit`
- 可选询问是否 `git push`

### chg-02 文档与验证
- 更新 README 中 `harness archive` 的说明
- 在临时 Git 仓库验证归档后的提交流程
- 重新安装包
