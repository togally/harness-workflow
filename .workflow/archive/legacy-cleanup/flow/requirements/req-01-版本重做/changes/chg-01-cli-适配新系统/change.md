# Change: CLI 适配新系统

## 背景

Chg-07 重构后，`harness.py` CLI 依赖的 `assets/templates/` 已被删除，且路径模型已从版本管理改为需求管理。测试套件 15 个用例中 15 个失败。

## 目标

让 `harness.py` 和 `test_harness_cli.py` 完整通过，同时对齐新系统架构。

## 变更范围

1. **scripts/ → tools/ 重命名**：`SKILL.md` 的测试期望 `tools/lint_harness_repo.py`
2. **恢复 assets/templates/**：更新模板内容，适配新系统路径
3. **更新 harness.py**：
   - runtime 路径：`workflow/context/rules/workflow-runtime.yaml` → `workflow/state/runtime.yaml`
   - 需求目录：`workflow/versions/active/{version}/` → `flow/requirements/`
   - 去掉 `version` 命令概念（新系统无 version 层）
   - `requirement`、`change`、`plan`、`next`、`archive`、`regression` 等命令按新路径重写
4. **更新 test_harness_cli.py**：
   - 路径断言更新为新系统路径
   - 去掉 `version` 相关测试（`test_use_and_status_follow_runtime` 等）
   - 新增 requirement-based 流程测试

## 验收标准

- `python3 tests/test_harness_cli.py` 全部通过（0 failures，0 errors）
- `harness.py init / requirement / change / plan / next / regression / archive` 按新路径创建正确文件
