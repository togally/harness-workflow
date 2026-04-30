---
id: req-53
title: "新增-harness-命令-给项目添加规范-经验-工具-引导式"
stage: testing
verdict: PASS
created_at: 2026-04-29
---

## 测试范围
- req-53 40 TC + bugfix-13 防回归 10 TC + 关键 lint + dogfood + 契约不破

## req-53 测试实跑（完整 stdout）

```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/jiazhiwei/claudeProject/workspace/harness-workflow
configfile: pyproject.toml
collecting ... collected 40 items

tests/test_req53_pad_cli.py::test_tc01_pad_rule_coding_parsed PASSED     [  2%]
tests/test_req53_pad_cli.py::test_tc02_pad_experience_stage_parsed PASSED [  5%]
tests/test_req53_pad_cli.py::test_tc03_pad_tool_no_scope_normalize PASSED [  7%]
tests/test_req53_pad_cli.py::test_tc04_illegal_kind_abort PASSED         [ 10%]
tests/test_req53_pad_cli.py::test_tc05_illegal_rule_scope_abort PASSED   [ 12%]
tests/test_req53_pad_cli.py::test_tc06_illegal_experience_scope_abort PASSED [ 15%]
tests/test_req53_pad_cli.py::test_tc07_pad_list_stub PASSED              [ 17%]
tests/test_req53_pad_cli.py::test_tc08_pad_empty_interactive_non_tty PASSED [ 20%]
tests/test_req53_pad_add.py::test_tc01_add_rule_coding_落位 PASSED       [ 22%]
tests/test_req53_pad_add.py::test_tc02_add_experience_stage_落位 PASSED  [ 25%]
tests/test_req53_pad_add.py::test_tc03_add_tool_不分scope_落位 PASSED    [ 27%]
tests/test_req53_pad_add.py::test_tc04_add_frontmatter_字段完整 PASSED   [ 30%]
tests/test_req53_pad_add.py::test_tc05_add_write_if_missing_幂等 PASSED  [ 32%]
tests/test_req53_pad_add.py::test_tc06_add_illegal_kind_不落位 PASSED    [ 35%]
tests/test_req53_pad_add.py::test_tc07_add_tool_frontmatter_tool_id PASSED [ 37%]
tests/test_req53_pad_add.py::test_tc08_dogfood_add_fresh_repo_三类 PASSED [ 40%]
tests/test_req53_pad_index.py::test_tc01_index_rule_表格追加 PASSED      [ 42%]
tests/test_req53_pad_index.py::test_tc02_index_experience_子目录追加 PASSED [ 45%]
tests/test_req53_pad_index.py::test_tc03_index_tool_列表追加 PASSED      [ 47%]
tests/test_req53_pad_index.py::test_tc04_stderr_活证 PASSED              [ 50%]
tests/test_req53_pad_index.py::test_tc05_stdout_git_commit_提示 PASSED   [ 52%]
tests/test_req53_pad_index.py::test_tc06_git_add_staged PASSED           [ 55%]
tests/test_req53_pad_index.py::test_tc07_非git仓_silent_skip PASSED      [ 57%]
tests/test_req53_pad_index.py::test_tc08_幂等_不重复登记 PASSED          [ 60%]
tests/test_req53_pad_index.py::test_tc09_表头缺失_自动补 PASSED          [ 62%]
tests/test_req53_pad_index.py::test_tc10_install_不覆盖_ac04 PASSED      [ 65%]
tests/test_req53_pad_list.py::test_tc01_list_空仓三段全无 PASSED         [ 67%]
tests/test_req53_pad_list.py::test_tc02_list_rule_按scope分组 PASSED     [ 70%]
tests/test_req53_pad_list.py::test_tc03_list_experience_五子分类 PASSED  [ 72%]
tests/test_req53_pad_list.py::test_tc04_list_tool_列表段解析 PASSED      [ 75%]
tests/test_req53_pad_list.py::test_tc05_list_多次pad后汇总 PASSED        [ 77%]
tests/test_req53_pad_interactive.py::test_tc01_interactive_非TTY_abort PASSED [ 80%]
tests/test_req53_pad_interactive.py::test_tc02_interactive_questionary_mock PASSED [ 82%]
tests/test_req53_pad_interactive.py::test_tc03_interactive_cancel PASSED [ 85%]
tests/test_req53_pad_interactive.py::test_tc04_interactive_tool_no_scope_step PASSED [ 87%]
tests/test_req53_pad_dogfood.py::test_dogfood_01_fresh_install_then_pad PASSED [ 90%]
tests/test_req53_pad_dogfood.py::test_dogfood_02_多次pad_同scope_多条 PASSED [ 92%]
tests/test_req53_pad_dogfood.py::test_dogfood_03_混合_rule_experience_tool PASSED [ 95%]
tests/test_req53_pad_dogfood.py::test_dogfood_04_pad后install_不覆盖 PASSED [ 97%]
tests/test_req53_pad_dogfood.py::test_dogfood_05_feedback_jsonl_不被破坏 PASSED [100%]

======================== 40 passed in 66.40s (0:01:06) =========================
```

## bugfix-13 防回归（完整 stdout）

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

============================== 10 passed in 6.80s ==============================
```

## 全 suite（完整 tail -3）

```
FAILED tests/test_validate_test_case_design_completeness.py::test_cli_contract_choices_include_artifact_placement
FAILED tests/test_workflow_next_subprocess.py::test_tc04_subprocess_rfe_execute_advances_to_executing_only
FAILED tests/test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops
FAILED tests/test_workflow_next_workdone_gate.py::test_tc05_same_role_jump_not_blocked_by_workdone_gate
51 failed, 797 passed, 40 skipped, 1 warning, 17 subtests passed in 200.91s (0:03:20)
```

说明：failed=51 与 baseline 一致，不增；passed=797（baseline + 40 req-53 新增 TC）。

## 关键 lint（每条 paste stdout）

### 4.1 PAD_KINDS 常量落地

```
214:PAD_KINDS: dict[str, list[str]] = {
```

### 4.2 dispatch 分支落地

```
714:    if args.command == "pad":
```

### 4.3 三份模板文件存在

```
experience.md.tmpl
rule.md.tmpl
tool.md.tmpl
```

### 4.4 kind 错误信息字符串

```
        return "kind 必须是 rule/experience/tool 之一"
```

### 4.5 rule scope 错误信息字符串

```
    - rule:       "rule scope 必须是 coding/architecture/api/database/security 之一"
        # rule scope 必须是 coding/architecture/api/database/security 之一
```

## dogfood（完整脚本输出）

```
=== STEP 1: git init ===
Initialized empty Git repository in /private/tmp/req53-testing-dogfood/.git/

=== STEP 2: harness install ===
[install_repo] force_managed received: False
[install_repo] project skeleton: created 8 files / skipped 0 files
[harness] project-level loaded: 1 files from artifacts/project/constraints/（fallback=n/a）
[harness] project-level loaded: 5 files from artifacts/project/experience/（fallback=n/a）
[harness] project-level loaded: 1 files from artifacts/project/tools/（fallback=n/a）
...（install 完整输出省略，install PASS）

=== STEP 3: harness pad rule coding 禁止-API-硬编码 ===
[harness] project-level loaded: 2 files from artifacts/project/constraints/（fallback=n/a）
[harness pad] added artifacts/project/constraints/coding/禁止-api-硬编码.md ✓
✓ git staged. 提示 git commit -m "feat: 项目级 rule-禁止-API-硬编码"

=== STEP 4: harness pad list ===
=== Project-level Catalog (artifacts/project/) ===

[rule] (artifacts/project/constraints/)
  coding:
    - coding/禁止-api-硬编码.md — 禁止-API-硬编码
  architecture:
    (无)
  api:
    (无)
  database:
    (无)
  security:
    (无)

[experience] (artifacts/project/experience/{scope}/)
  roles:
    (无)
  stage:
    (无)
  regression:
    (无)
  risk:
    (无)
  tool:
    (无)

[tool] (artifacts/project/tools/)
  - my-tool-name.md — 一句话用途说明

=== STEP 5: verify file falls into correct path ===
禁止-api-硬编码.md

=== STEP 6: verify index.md was updated ===
| coding/禁止-api-硬编码.md | 禁止-API-硬编码 | coding | always | (空) |
（index.md 含上述行，表格自动登记 PASS）

=== STEP 7: illegal scope ABORT test: harness pad rule standards 'xxx' ===
[harness pad] ABORT: rule scope 必须是 coding/architecture/api/database/security 之一
exit code: 2

=== STEP 8: git staged files ===
"artifacts/project/constraints/coding/\347\246\201\346\255\242-api-\347\241\254\347\274\226\347\240\201.md"
artifacts/project/constraints/index.md
```

## 契约（exit code）

### artifact-placement

```
PASS: artifact-placement lint — artifacts/ 下无机器型文件
exit code: 0
```

### user-write-protected-zones

```
PASS: user-write-protected-zones
exit code: 0
```

## AC 对照表（10 条 AC）

- AC-01（落位正确）：✓ `harness pad rule coding "禁止-API-硬编码"` 后，`artifacts/project/constraints/coding/禁止-api-硬编码.md` 存在，含 frontmatter + `## 内容` 占位段（TC-01/TC-04 覆盖）
- AC-02（index.md 自动登记）：✓ constraints/index.md 新增 `| coding/禁止-api-硬编码.md | 禁止-API-硬编码 | coding | always | (空) |`（TC-01-index + dogfood STEP 6 验证）
- AC-03（加载链可观测）：✓ stderr 含 `[harness] project-level loaded: 2 files from artifacts/project/constraints/（fallback=n/a）`（TC-04-stderr 覆盖 + dogfood STEP 3 实跑）
- AC-04（install 不覆盖）：✓ `install --force-managed` 后内容文件 + index.md 新行仍在（TC-10 + test_dogfood_04 覆盖）
- AC-05（lint 通过）：✓ `harness validate --contract user-write-protected-zones` exit=0
- AC-06（list 子命令）：✓ `harness pad list` 按 kind/scope 分组打印全部条目（TC-01~TC-05-list 覆盖）
- AC-07（fresh repo dogfood）：✓ tmpdir + git init + install + pad experience tool "apifox-用法" → 落位 + index 登记 + install --check 不报错（test_dogfood_01 + TC-08-fresh-repo 覆盖）
- AC-08（interactive 模式）：✓ 裸跑 `harness pad` 非 TTY 报错（TC-01-interactive）；monkeypatch 模拟三步答完后落地行为与位置参数一致（TC-02-interactive-mock 覆盖）
- AC-09（git tracking 提醒）：✓ stdout 含 `✓ git staged. 提示 git commit -m "feat: 项目级 rule-..."` + git diff --cached 含内容文件+index.md（TC-05/TC-06 覆盖）
- AC-10（PetMallPlatform 真实仓自验）：⚠ 仅在 dogfood 空仓模拟验证（task scope 限 harness-workflow 仓，不入 PetMallPlatform 真实仓）；其余 9 条 AC 全部 PASS，功能满足。

## 结论

- verdict: PASS
- 总评: req-53 全部 40 TC + bugfix-13 防回归 10 TC 均通过，关键 lint 5 条全绿，dogfood 新鲜仓落位/index 登记/git stage/非法 ABORT 均验证通过，两项契约 exit=0，baseline failed=51 不增。
- 缺陷清单: 无
- 路由建议: PASS → acceptance
