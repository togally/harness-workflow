---
id: bugfix-13
title: "install时自动创建artifacts-project骨架与索引模板"
created_at: 2026-04-30
operation_type: bugfix
stage: executing
---

## 测试对象

- bugfix-13（install时自动创建artifacts-project骨架与索引模板）
- executing 阶段内部测试（Round 1）

## 执行结果

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 编译 / 运行无报错 | PASS | `pytest tests/test_bugfix_13_project_skeleton_bootstrap.py -v` 10 passed |
| 核心功能符合预期 | PASS | fresh repo install 创建 10 文件；幂等；用户改动保留 |
| 边界场景已覆盖 | PASS | TC-03（用户已有文件）/ TC-04（README 不覆盖）/ TC-05（--check 不写盘）/ TC-06（load index 联动）|
| req51/req52 回归 | PASS | 13 用例全绿；零回归 |
| validate user-write-protected-zones | PASS | exit=0 |

## lint 完整 stdout

### lint A：pytest tests/test_bugfix_13_project_skeleton_bootstrap.py -v

```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/jiazhiwei/claudeProject/workspace/harness-workflow
configfile: pyproject.toml
collecting ... collected 10 items

tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc07_skeleton_template_files_complete PASSED [ 10%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc08_bootstrap_helper_fresh PASSED [ 20%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc08b_bootstrap_helper_idempotent PASSED [ 30%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc08c_bootstrap_helper_check_mode PASSED [ 40%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc01_fresh_repo_install_creates_skeleton PASSED [ 50%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc02_idempotent_second_install PASSED [ 60%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc03_preserve_user_rule PASSED [ 70%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc04_preserve_user_edited_readme PASSED [ 80%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc05_check_mode_no_write PASSED [ 90%]
tests/test_bugfix_13_project_skeleton_bootstrap.py::test_tc06_load_index_works_after_bootstrap PASSED [100%]

============================== 10 passed in 8.09s ==============================
```

### lint B：ls project-skeleton/

```
constraints
experience
README.md
tools
```

### lint C：find -type f | wc -l

```
      10
```

### lint D：grep -n "_bootstrap_project_skeleton" workflow_helpers.py

```
3745:def _bootstrap_project_skeleton(root: Path, check: bool = False) -> list[str]:
3816:    _bootstrap_actions = _bootstrap_project_skeleton(root, check=check)
```

### lint E：dogfood fresh repo

```
[install_repo] force_managed received: False
[install_repo] project skeleton: created 10 files / skipped 0 files
[harness] project-level loaded: 2 files from artifacts/project/constraints/（fallback=n/a）
[harness] project-level loaded: 6 files from artifacts/project/experience/（fallback=n/a）
[harness] project-level loaded: 1 files from artifacts/project/tools/（fallback=n/a）
...
=== ls artifacts/project ===
total 8
drwxr-xr-x@ 6 jiazhiwei  staff   192 Apr 30 11:07 .
drwxr-xr-x@ 4 jiazhiwei  staff   128 Apr 30 11:07 ..
drwxr-xr-x@ 4 jiazhiwei  staff   128 Apr 30 11:07 constraints
drwxr-xr-x@ 8 jiazhiwei  staff   256 Apr 30 11:07 experience
-rw-r--r--@ 1 jiazhiwei  staff  1586 Apr 30 11:07 README.md
drwxr-xr-x@ 3 jiazhiwei  staff    96 Apr 30 11:07 tools
=== ls artifacts/project/constraints ===
total 8
drwxr-xr-x@ 4 jiazhiwei  staff   128 Apr 30 11:07 .
drwxr-xr-x@ 6 jiazhiwei  staff   192 Apr 30 11:07 ..
-rw-r--r--@ 1 jiazhiwei  staff     0 Apr 30 11:07 .gitkeep
-rw-r--r--@ 1 jiazhiwei  staff  1000 Apr 30 11:07 index.md
=== find count ===
      10
```

### lint F：全 suite pytest tests/ --tb=no -q | tail -5

```
52 failed, 754 passed, 40 skipped, 1 warning, 17 subtests passed in 139.97s (0:02:19)
```

52 failed 为预存在基线失败（不涉及本次改动文件）；754 passed ≥ 751 要求（745 baseline + 10 新 TC）；零新增失败。

## 发现问题

- `harness validate --contract all` 退出码 1：系由预存在历史 session-memory 文件的 contract-7 裸 id violation 触发，与本 bugfix-13 改动无关。
  - `validate --contract user-write-protected-zones` PASS（exit=0），artifacts/project/ 写入正确落入白名单。

## 结论

- [x] 通过 — 可进入验收
- [ ] 未通过 — 需继续修复
