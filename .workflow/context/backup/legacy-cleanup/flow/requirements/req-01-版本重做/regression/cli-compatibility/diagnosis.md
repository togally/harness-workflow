## 问题描述

Testing 阶段运行 `test_harness_cli.py`：15 个用例，12 failures + 3 errors。

## 证据

```
FileNotFoundError: .claude/skills/harness/assets/templates/docs-README.md.tmpl
FAIL: test_use_and_status_follow_runtime — Version does not exist: v1.0.0
```

运行命令：`python3 .claude/skills/harness/tests/test_harness_cli.py`

## 根因分析

Chg-07（新版系统构建）删除了 `assets/templates/` 目录，但 `scripts/harness.py` 仍依赖该目录生成文件。具体断链：

1. `harness.py init` 读取 `assets/templates/*.tmpl` 初始化工作区 → 模板不存在 → FileNotFoundError
2. 测试断言旧路径 `workflow/versions/active/{version}/`、`workflow/context/rules/workflow-runtime.yaml` → 新系统已改为 `flow/requirements/`、`workflow/state/runtime.yaml`
3. `test_installed_skill_uses_global_harness_commands` 期望 `python3 tools/lint_harness_repo.py` → 脚本实际在 `scripts/`

根本原因：Chg-07 改变了系统架构（版本管理 → 需求管理），但未同步更新 CLI 脚本和测试套件。

## 结论

- [x] 真实问题

## 路由决定

- 问题类型：实现/测试（CLI 与新系统路径、数据模型不兼容）
- 目标阶段：executing（作为新 change 实现）

## 需要人工提供的信息

无，根因明确，修复方向已确定（Direction A：修复 CLI 对齐新系统）。
