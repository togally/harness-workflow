# Session Memory

## 1. Current Goal

实现 stage 状态机扩展：将 `executing → done` 路径扩展为 `executing → testing → acceptance → done`，并新增 `--testing` regression 回退支持。

## 2. Current Status

**已完成**，所有修改验证通过。

## 3. Validated Approaches

### 修改1：apply_stage_transition（core.py）

将 `executing → done` 改为三步：
- `executing → testing`：stage="testing", status="in_progress", suggested_skill="subagent-driven-development"
- `testing → acceptance`：stage="acceptance", status="in_progress", suggested_skill="verification-before-completion"
- `acceptance → done`：保持原有 done 内容

验证命令：
```
python3 -c "import sys; sys.path.insert(0, 'src'); from harness_workflow.core import apply_stage_transition; print('OK')"
```

### 修改2：create_version（core.py）

在 `create_version` 函数中，在已有目录创建之后追加：
```python
(layout["version_dir"] / "testing").mkdir(parents=True, exist_ok=True)
(layout["version_dir"] / "testing" / "bugs").mkdir(parents=True, exist_ok=True)
(layout["version_dir"] / "acceptance").mkdir(parents=True, exist_ok=True)
```
注意：`_required_dirs` 不接收 version_id，故在 `create_version` 中单独处理，而非加入 `_required_dirs`。

### 修改3：regression_action（core.py）

新增 `to_testing: bool = False` 参数。当 `--testing` 被触发时：
1. 检查 regression_status == "confirmed"（必须先 --confirm）
2. 创建 `testing/bugs/<regression_id>.md`（内容来自 regression.md）
3. 清除 regression 状态，将版本 stage 回退为 testing
4. 调用 persist_workflow_state 持久化

### 修改4：_sync_artifact_statuses（core.py）

新增 `testing` 和 `acceptance` 阶段处理：
- `testing`：设置 focus_change 的 meta.yaml status 为 "testing"
- `acceptance`：设置所有 change 的 meta.yaml status 为 "acceptance"（如未完成）

### 修改5：CLI（cli.py）

- 在 regression parser 中添加 `--testing` 标志
- 在 `regression_action` 调用中传入 `to_testing=args.testing`
- 检查 `args.title` 时也纳入 `args.testing` 以正确路由到 action 分支

## 4. Failed Paths

无（首次尝试即成功）

## 5. Candidate Lessons

### 2026-04-11 版本目录动态创建需在 create_version 而非 _required_dirs 中处理
- Symptom: `_required_dirs` 不接收 version_id，无法生成版本级子目录路径
- Cause: `_required_dirs(root)` 只处理全局目录，版本目录是动态的
- Fix: 在 `create_version` 函数中，在已有 layout 目录创建代码后直接添加 mkdir 调用

## 6. Next Steps

- 可考虑在 `acceptance` stage 自动创建 `acceptance/sign-off.md` 模板文件
- 可考虑在 `testing` stage 自动创建 `testing/test-cases.md` 模板文件

## 7. Open Questions

- `testing/test-cases.md` 和 `acceptance/sign-off.md` 是否需要对应的模板文件 (`.tmpl`)?
