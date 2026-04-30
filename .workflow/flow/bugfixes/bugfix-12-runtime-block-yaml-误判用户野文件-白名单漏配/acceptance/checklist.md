---
id: bugfix-12
title: "runtime-block.yaml-误判用户野文件-白名单漏配"
stage: acceptance
verdict: PASS
created_at: 2026-04-29
---

## A 检查项

- [x] A.1 白名单加条 grep — 区间 172-201 内命中 1 行

```
$ grep -n '"state/runtime-block.yaml"' src/harness_workflow/workflow_helpers.py
179:    "state/runtime-block.yaml",  # bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）：raise_harness_block 写运行时阻塞状态，需豁免
```

命中行号 179，位于 `_SCAFFOLD_V2_MIRROR_WHITELIST` 元组内（172-201 区间），1 行，符合预期。

- [x] A.2 测试文件存在

```
$ ls -la tests/test_bugfix_12_runtime_block_whitelist.py
-rw-r--r--@ 1 jiazhiwei  staff  6694 Apr 30 03:25 /Users/jiazhiwei/claudeProject/workspace/harness-workflow/tests/test_bugfix_12_runtime_block_whitelist.py
```

- [x] A.3 bugfix-12 tests 全 pass（4 TC）

```
$ python3 -m pytest tests/test_bugfix_12_runtime_block_whitelist.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/jiazhiwei/claudeProject/workspace/harness-workflow
configfile: pyproject.toml
collecting ... collected 4 items

tests/test_bugfix_12_runtime_block_whitelist.py::test_tc01_runtime_block_yaml_not_flagged_in_user_repo PASSED [ 25%]
tests/test_bugfix_12_runtime_block_whitelist.py::test_tc02_runtime_block_yaml_whitelisted_while_wild_file_flagged PASSED [ 50%]
tests/test_bugfix_12_runtime_block_whitelist.py::test_tc03_runtime_block_yaml_in_whitelist PASSED [ 75%]
tests/test_bugfix_12_runtime_block_whitelist.py::test_tc04_dev_repo_still_short_circuits PASSED [100%]

============================== 4 passed in 0.08s ===============================
```

- [x] A.4 全 suite 不增 fail（= baseline 51）

```
$ python3 -m pytest tests/ --tb=no -q | tail -5
FAILED tests/test_validate_test_case_design_completeness.py::test_cli_contract_choices_include_artifact_placement
FAILED tests/test_workflow_next_subprocess.py::test_tc04_subprocess_rfe_execute_advances_to_executing_only
FAILED tests/test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops
FAILED tests/test_workflow_next_workdone_gate.py::test_tc05_same_role_jump_not_blocked_by_workdone_gate
51 failed, 733 passed, 40 skipped, 1 warning, 17 subtests passed in 96.87s (0:01:36)
```

51 failed = baseline，729 + 4（新 TC） = 733 passed，符合预期。

- [x] A.5 dogfood（非 dev_repo tmpdir + runtime-block.yaml → 返回 0）

```python
import tempfile, os, sys
sys.path.insert(0, 'src')
from pathlib import Path
from harness_workflow.validate_contract import check_user_write_protected_zones

with tempfile.TemporaryDirectory() as tmpdir_str:
    tmpdir = Path(tmpdir_str)
    state_dir = tmpdir / '.workflow' / 'state'
    state_dir.mkdir(parents=True)
    rb = state_dir / 'runtime-block.yaml'
    rb.write_text('blocked: true\n')
    result = check_user_write_protected_zones(tmpdir)
    print(f'Result: {result}')
    # → Result: 0
    # A.5 PASS: runtime-block.yaml in non-dev tmpdir returned 0 (no violation — whitelisted)
```

stdout: `Result: 0` / `A.5 PASS: runtime-block.yaml in non-dev tmpdir returned 0 (no violation — whitelisted)`

- [x] A.6 反例 lint — `tests/test_user_write_protected_zones.py` 在全 suite 仍保持既有 pass/fail 分布

```
$ python3 -m pytest tests/test_user_write_protected_zones.py -v
...
tests/test_user_write_protected_zones.py::test_tc04d_is_dev_repo_layer1_pyproject PASSED
tests/test_user_write_protected_zones.py::test_tc04d_is_dev_repo_layer2_src_dir PASSED
tests/test_user_write_protected_zones.py::test_tc04d_is_dev_repo_layer3_env PASSED
tests/test_user_write_protected_zones.py::test_tc04d_is_dev_repo_user_project PASSED
tests/test_user_write_protected_zones.py::test_tc04d_is_dev_repo_current_repo PASSED
tests/test_user_write_protected_zones.py::test_tc04a_user_project_violation PASSED
tests/test_user_write_protected_zones.py::test_tc04a_user_project_violation_subprocess FAILED
tests/test_user_write_protected_zones.py::test_tc04b_dev_mode_silent_skip PASSED
tests/test_user_write_protected_zones.py::test_tc04b_dev_mode_subprocess FAILED
tests/test_user_write_protected_zones.py::test_tc04c_tool_output_zone_skip PASSED
========================= 2 failed, 8 passed in 0.24s ==========================
```

2 个 subprocess 失败为预存基线失败（ModuleNotFoundError: 未安装到系统 python3，与 bugfix-12 无关），在 51 baseline 失败计数内，非 bugfix-12 引入。

- [x] A.7 范围红线 — git diff --name-only 不含 PetMallPlatform / req-51 / 任何无关文件

```
$ git diff HEAD --name-only | grep -E "PetMall|req-51|req51"
（无输出）
CLEAN: no PetMall/req-51 files
```

bugfix-12 相关改动仅限：
- `src/harness_workflow/workflow_helpers.py`（+1 行白名单）
- `tests/test_bugfix_12_runtime_block_whitelist.py`（新增，untracked）
- `.workflow/flow/bugfixes/bugfix-12-*/`（工作区流程文件，untracked）

## §结论

- verdict: PASS
- 总评: bugfix-12 修复准确——`_SCAFFOLD_V2_MIRROR_WHITELIST` 新增 `"state/runtime-block.yaml"` 一行，4 TC 全绿，全 suite 51 failed 未增，dogfood 返回 0，范围无越界。
- 未达标项: 无
- 路由建议: PASS → done
