# chg-06 更新 lint 和测试文件

## 目标

将 `lint_harness_repo.py` 和 `test_harness_cli.py` 从旧架构更新为新架构，消除对已不存在文件/目录的检查。

## 背景

`lint_harness_repo.py` 的 `REQUIRED_DIRS` 和 `REQUIRED_FILES` 仍检查旧架构文件：
- `REQUIRED_DIRS` 包含：`.workflow/versions`（CLI 硬依赖，暂保留）、`.workflow/context/hooks`（不存在）、`.workflow/context/rules`（本次删除）、`.workflow/templates`（不存在）
- `REQUIRED_FILES` 包含：`.workflow/README.md`、`.workflow/memory/constitution.md`、`.workflow/context/rules/agent-workflow.md`、`.workflow/context/rules/risk-rules.md`（均不存在）

`test_harness_cli.py` 中大量测试引用 `workflow/versions/active/{version}/requirements/`、`changes/` 等旧路径，与新 `flow/requirements/` 结构不符。

## 范围

### 修改文件
- `.claude/skills/harness/scripts/lint_harness_repo.py`：
  - 更新 `REQUIRED_DIRS` 为新架构实际存在的目录
  - 更新 `REQUIRED_FILES` 为新架构实际存在的文件
  - 保留 `.workflow/versions` 检查（CLI 硬依赖）
- `.claude/skills/harness/tests/test_harness_cli.py`：
  - 标记使用旧路径的测试为 skip 或更新路径
  - 确保现有通过的测试不被破坏

### 不修改
- `harness_workflow` 已安装包（只读）
- 其他任何文件

## 验收标准

- [ ] `lint_harness_repo.py` 的 `REQUIRED_DIRS` 不再包含不存在的旧目录（`context/hooks`、`context/rules`、`templates`）
- [ ] `lint_harness_repo.py` 的 `REQUIRED_FILES` 更新为当前架构实际存在的文件
- [ ] `python lint_harness_repo.py` 在当前仓库根目录执行通过（或仅有已知警告）
- [ ] `test_harness_cli.py` 中引用旧路径的测试已注明 skip 原因
