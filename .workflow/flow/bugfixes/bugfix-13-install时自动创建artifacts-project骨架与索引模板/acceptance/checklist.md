---
id: bugfix-13
title: "install时自动创建artifacts-project骨架与索引模板"
stage: acceptance
verdict: PASS
created_at: 2026-04-29
---

# Acceptance Checklist — bugfix-13

角色：Subagent-L1（acceptance / Sonnet）
时间：2026-04-29
runtime 确认：`current_requirement=bugfix-13 / stage=acceptance`

---

## A.1 模板树存在（10 文件）

```
$ find /Users/jiazhiwei/claudeProject/workspace/harness-workflow/src/harness_workflow/assets/templates/project-skeleton/ -type f | wc -l
      10
```

- [x] **PASS** — 模板文件恰好 10 个，符合预期。

---

## A.2 helper 定义 + 调用（≥ 2 命中）

```
$ grep -n "_bootstrap_project_skeleton" src/harness_workflow/workflow_helpers.py
3745:def _bootstrap_project_skeleton(root: Path, check: bool = False) -> list[str]:
3816:    _bootstrap_actions = _bootstrap_project_skeleton(root, check=check)
```

- [x] **PASS** — 2 命中：第 3745 行定义，第 3816 行调用，符合预期（≥ 2 命中）。

---

## A.3 bugfix-13 测试 10 TC 全 pass

```
$ pytest tests/test_bugfix_13_project_skeleton_bootstrap.py -v
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

============================== 10 passed in 8.98s ==============================
```

- [x] **PASS** — 10/10 TC 全部通过。

---

## A.4 README 不含裸 id 不含 legacy fallback

```
$ grep -c "legacy fallback" artifacts/project/README.md
0
```

- [x] **PASS** — 0 命中，无 "legacy fallback" 字样。裸 UUID 正则检查亦为 0 命中。

---

## A.5 README 模板同步

```
$ diff -q artifacts/project/README.md src/harness_workflow/assets/templates/project-skeleton/README.md
(无输出——完全一致)
```

- [x] **PASS** — diff 无输出，live README 与模板文件字节级一致。

---

## A.6 dogfood fresh repo（`mktemp -d + git init + harness install` → artifacts/project/ 含 10 文件）

以工作区源码（PYTHONPATH 指向 workspace/src）运行，与测试套件 TC-01 同等方式：

```
$ TMPDIR=$(mktemp -d) && cd "$TMPDIR" && git init -q \
  && PYTHONPATH=/Users/jiazhiwei/claudeProject/workspace/harness-workflow/src \
     python3.14 -m harness_workflow.cli install 2>&1 | grep -E "project skeleton|created"

[install_repo] project skeleton: created 10 files / skipped 0 files
- created artifacts/project/README.md
- created artifacts/project/constraints/.gitkeep
- created artifacts/project/constraints/index.md
- created artifacts/project/experience/.gitkeep
- created artifacts/project/experience/regression/index.md
- created artifacts/project/experience/risk/index.md
- created artifacts/project/experience/roles/index.md
- created artifacts/project/experience/stage/index.md
- created artifacts/project/experience/tool/index.md
- created artifacts/project/tools/.gitkeep

--- find artifacts/project/ -type f | wc -l
      10
```

**部署差距观察（旁支，不计入 FAIL）**：
- 系统 PATH 中的 `harness`（pipx 安装，来自 GitHub commit `1994ab2`，0.2.0 版本）不含 bugfix-13 代码，直接运行 `harness install` 不会创建 artifacts/project/。
- 这与 bugfix-11 acceptance 发现的 pipx 部署分叉问题同类（见 sug-60）。
- 本次 dogfood 采用工作区源码执行（与所有 10 TC 方式一致），功能完全正确。
- **路由建议**：done 阶段需提醒执行 `pipx install --force` 重装以同步部署版本。

- [x] **PASS（工作区源码）** — artifacts/project/ 含 10 文件，完全符合预期。
  - 旁支注记：live pipx 0.2.0 未含 bugfix-13，不阻断 PASS 判定（源码层正确，部署为运维事项）。

---

## A.7 全 suite 51 failed（baseline 不增）/ passed ≥ 755

```
$ pytest tests/ -v --tb=no -q 2>&1 | tail -5

FAILED tests/test_validate_test_case_design_completeness.py::test_cli_contract_choices_include_artifact_placement
FAILED tests/test_workflow_next_subprocess.py::test_tc04_subprocess_rfe_execute_advances_to_executing_only
FAILED tests/test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops
FAILED tests/test_workflow_next_workdone_gate.py::test_tc05_same_role_jump_not_blocked_by_workdone_gate
====== 51 failed, 755 passed, 40 skipped, 1 warning in 138.89s (0:02:18) =======
```

- [x] **PASS** — 51 failed（= baseline，无新增）；755 passed（≥ 755 门槛）；40 skipped；无新增 FAIL。

---

## A.8 req-51 dogfood 没破

```
$ pytest tests/test_req51_project_level_dogfood.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/jiazhiwei/claudeProject/workspace/harness-workflow
configfile: pyproject.toml
collecting ... collected 7 items

tests/test_req51_project_level_dogfood.py::test_dogfood_01_fixture_write_three_types PASSED [ 14%]
tests/test_req51_project_level_dogfood.py::test_dogfood_02_install_preserve_all PASSED [ 28%]
tests/test_req51_project_level_dogfood.py::test_dogfood_03_validate_protected_zones PASSED [ 42%]
tests/test_req51_project_level_dogfood.py::test_dogfood_04_validate_all PASSED [ 57%]
tests/test_req51_project_level_dogfood.py::test_dogfood_05_loading_merge PASSED [ 71%]
tests/test_req51_project_level_dogfood.py::test_dogfood_06_petmall_runbook_existence PASSED [ 85%]
tests/test_req51_project_level_dogfood.py::test_dogfood_07_feedback_events PASSED [100%]

============================== 7 passed in 12.94s ==============================
```

- [x] **PASS** — 7/7 TC 全通过，req-51 dogfood 未被 bugfix-13 破坏。

---

## A.9 范围红线

```
$ git diff --name-only | grep -E "PetMallPlatform|req-51|req-52|bugfix-11|bugfix-12" \
  | grep -v "session-memory\|usage-log\|state/bugfixes\|acceptance/checklist"
(无输出)
```

完整 git diff --name-only 输出：
```
.workflow/context/experience/roles/analyst.md
.workflow/context/experience/roles/executing.md
.workflow/context/roles/harness-manager.md
.workflow/context/roles/role-loading-protocol.md
.workflow/context/roles/tools-manager.md
.workflow/flow/bugfixes/bugfix-11-petmallplatform-artifacts误放机器型流程文档/acceptance/checklist.md  ← done 阶段 verdict 更新（状态推进，非落地内容）
.workflow/flow/bugfixes/bugfix-11-petmallplatform-artifacts误放机器型流程文档/session-memory.md  ← done 阶段 six-layer review 追加（状态推进）
.workflow/flow/repository-layout.md
.workflow/state/action-log.md
.workflow/state/bugfixes/bugfix-11-petmallplatform-artifacts误放机器型流程文档.yaml  ← stage: done / status: done（状态推进）
.workflow/state/feedback/feedback.jsonl
.workflow/state/platforms.yaml
.workflow/state/runtime.yaml
.workflow/state/sessions/bugfix-11/usage-log.yaml  ← done 阶段 usage 追加（状态推进）
README.md
src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md
src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
src/harness_workflow/validate_contract.py
src/harness_workflow/workflow_helpers.py
```

涉及 bugfix-11 的 4 个文件均为**状态推进**（done 阶段 session-memory / state yaml / usage-log / acceptance/checklist verdict 更新），不含 PetMallPlatform 或 bugfix-11 落地内容回滚/新增。无 req-51 / req-52 / bugfix-12 落地内容改动。

- [x] **PASS** — 范围红线无违反；扩展方向正确，未回滚既有内容。

---

## §结论

| 项 | 状态 | 备注 |
|----|------|------|
| A.1 模板树存在（10 文件） | PASS | wc -l = 10 |
| A.2 helper 定义 + 调用（≥ 2） | PASS | 2 命中（定义 L3745 + 调用 L3816） |
| A.3 10 TC 全 pass | PASS | 10/10 |
| A.4 README 无裸 id / legacy fallback | PASS | grep -c = 0 |
| A.5 README 模板同步 | PASS | diff -q 无输出 |
| A.6 dogfood 含 10 文件 | PASS（工作区源码） | 旁支：live pipx 未重装，部署为运维事项 |
| A.7 全 suite 51 failed / passed ≥ 755 | PASS | 51 failed = baseline；755 passed |
| A.8 req-51 dogfood 未破 | PASS | 7/7 |
| A.9 范围红线 | PASS | 无落地内容越界 |

**verdict**: PASS

**总评**: bugfix-13（install 时自动创建 artifacts/project 骨架与索引模板）源码层落地完整：
- `_bootstrap_project_skeleton` helper 已在 `workflow_helpers.py` 实现并接入 `install_repo` 主路径；
- 10 个模板文件（README.md + constraints/ experience/ tools/ 骨架）齐全；
- 10 TC 测试全通过，包含 fresh/幂等/用户内容保留/check-mode/链路联动；
- req-51 dogfood 未破，全 suite 51 failed baseline 不增；
- 范围红线无违反。

**未达标项**: 0（无）

**旁支观察（不计入未达标）**:
- live pipx CLI（0.2.0，来自 GitHub commit `1994ab2`）不含 bugfix-13，直接运行 `harness install` 不触发骨架创建。done 阶段需执行 `pipx install --force /Users/jiazhiwei/claudeProject/workspace/harness-workflow` 同步部署版本。

**路由建议**: acceptance PASS → harness next（推进至 done 阶段）；done 阶段注意重装 pipx 部署。
