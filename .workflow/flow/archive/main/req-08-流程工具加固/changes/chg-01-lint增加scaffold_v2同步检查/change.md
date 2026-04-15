# Change: chg-01

## Title

lint 增加 scaffold_v2 同步检查

## Goal

在 `lint_harness_repo.py` 或 CI 脚本中增加对 `src/harness_workflow/assets/scaffold_v2/` 与仓库 `.workflow/` 同步状态的检查，防止模板未同步就发布。

## Scope

**包含**：
- 修改 `lint_harness_repo.py`，增加 scaffold_v2 同步检查逻辑
- 至少检查 `stages.md` 和 `WORKFLOW.md` 两个关键文件的一致性
- 检查失败时输出明确的修复命令

**不包含**：
- 修改 `harness install` 或 `harness update` 的核心逻辑
- 重写整个 lint 脚本

## Acceptance Criteria

- [ ] `lint_harness_repo.py` 能够检测 scaffold_v2 与仓库 `.workflow/` 不同步的情况
- [ ] 不同步时返回非零退出码并给出修复提示
- [ ] 同步时正常通过
