---
id: req-51
title: "项目级规则-经验-工具支持从制品引入"
stage: acceptance
verdict: PASS
created_at: 2026-04-29
---

## A 契约层

### A.1 `repository-layout.md` 含 `artifacts/{branch}/project/` 项目级承载段（grep 命中 ≥ 3）

命令：
```
$ grep -c "artifacts/{branch}/project/" .workflow/flow/repository-layout.md
```

stdout：
```
8
```

命中 8 次（≥ 3 要求满足）。详细行号：
```
$ grep -n "artifacts/{branch}/project/" .workflow/flow/repository-layout.md
25: ... artifacts/{branch}/project/{constraints,experience,tools}/ 三类项目级机器型文档由 req-51 显式豁免 ...
95: artifacts/{branch}/project/{constraints,experience,tools}/ 是 req-51 显式开放的项目级承载层 ...
99: | artifacts/{branch}/project/constraints/ | 项目独有规则 / 边界约束 ...
100: | artifacts/{branch}/project/experience/ | 项目独有经验沉淀 ...
101: | artifacts/{branch}/project/tools/ | 项目独有工具 catalog ...
120: > - artifacts/{branch}/project/constraints/
121: > - artifacts/{branch}/project/experience/
122: > - artifacts/{branch}/project/tools/
```

- [x] A.1 PASS — 8 命中（≥ 3），§2.1 项目级豁免段 + §3 豁免说明均存在

---

### A.2 `harness-manager.md` 硬门禁五例外白名单含 `artifacts/{branch}/project/`

命令：
```
$ grep -n "例外白名单\|artifacts/{branch}/project/" .workflow/context/roles/harness-manager.md | head -20
```

stdout：
```
32: 4. `.workflow/flow/`（stages.md 等流程定义，注意 flow/archive、flow/requirements、flow/suggestions 在例外白名单）
33: 5. `.workflow/state/experience/`（index.md 等本仓库经验沉淀，注意 state/experience/stage 在例外白名单）
37: **例外白名单**（不触发本硬门禁）：
48: - `artifacts/{branch}/project/`（req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified；三类项目级机器型文档承载层 ...）
55: 2. done 阶段六层回顾扫一次 `diff -rq ...`（排除例外白名单）...
```

白名单块头 line 37，项目级条目 line 48（间距 11 行，在块内）。

- [x] A.2 PASS — `artifacts/{branch}/project/` 在 line 48，白名单块（line 37）内

---

### A.3 scaffold_v2 mirror 同步（diff -q live mirror 4 文件 silent）

命令：
```
$ diff -q .workflow/flow/repository-layout.md \
    src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
exit=0

$ diff -q .workflow/context/roles/harness-manager.md \
    src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
exit=0

$ diff -q .workflow/context/roles/role-loading-protocol.md \
    src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
exit=0

$ diff -q .workflow/context/roles/tools-manager.md \
    src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md
exit=0
```

stdout：全部 silent（4 文件完全同源）

- [x] A.3 PASS — 4 个契约文件 live == mirror，字节级同源

---

## B 源码层

### B.1 `_SCAFFOLD_V2_MIRROR_WHITELIST` 含 `"artifacts/main/project/"`

命令：
```
$ grep -nE '"artifacts/main/project/"' src/harness_workflow/workflow_helpers.py | head -5
```

stdout：
```
200:    "artifacts/main/project/",
3427:    `_SCAFFOLD_V2_MIRROR_WHITELIST` 新加的 "artifacts/main/project/" 条目作 defense-in-depth 兜底。
8139:    `_SCAFFOLD_V2_MIRROR_WHITELIST` 新加的 "artifacts/main/project/" 条目仅用于
```

常量定义在 line 200（`_SCAFFOLD_V2_MIRROR_WHITELIST: tuple[str, ...] =` 从 line 172 起），另有 2 处 docstring 注释。

- [x] B.1 PASS — 常量 line 200 含 `"artifacts/main/project/"`，实际加入白名单

---

### B.2 `protected_zones` 不含 artifacts（保护精准）

命令：
```
$ grep -A 5 'protected_zones = \[' src/harness_workflow/validate_contract.py
```

stdout：
```
    protected_zones = [
        ".workflow",
    ]

    mirror = _scaffold_v2_file_contents(root, include_agents=False, include_claude=False, language="cn")
    managed = _load_managed_state(root)
```

`protected_zones` 只含 `".workflow"`，不含 `artifacts`。

- [x] B.2 PASS — `protected_zones` 仅 `.workflow`，artifacts 未入保护区（精准豁免）

---

### B.3 项目级目录占位：`artifacts/main/project/{constraints,experience,tools}/.gitkeep` + `README.md` 存在

命令：
```
$ ls -la artifacts/main/project/
```

stdout：
```
drwxr-xr-x@ 6 jiazhiwei  staff   192 Apr 30 00:20 .
drwxr-xr-x@ 8 jiazhiwei  staff   256 Apr 30 00:04 ..
drwxr-xr-x@ 3 jiazhiwei  staff    96 Apr 30 00:04 constraints
drwxr-xr-x@ 3 jiazhiwei  staff    96 Apr 30 00:04 experience
-rw-r--r--@ 1 jiazhiwei  staff  3276 Apr 30 00:20 README.md
drwxr-xr-x@ 3 jiazhiwei  staff    96 Apr 30 00:04 tools
```

命令：
```
$ ls -la artifacts/main/project/constraints/
$ ls -la artifacts/main/project/experience/
$ ls -la artifacts/main/project/tools/
```

stdout（三个子目录均同）：
```
-rw-r--r--@ 1 jiazhiwei  staff    0 Apr 30 00:04 .gitkeep
```

- [x] B.3 PASS — README.md (3276 bytes) + constraints/.gitkeep + experience/.gitkeep + tools/.gitkeep 全部存在

---

## C 测试层

### C.1 `tests/test_req51_*.py` 三个文件存在

命令：
```
$ ls tests/test_req51*.py
```

stdout：
```
tests/test_req51_project_level_dogfood.py
tests/test_req51_project_level_loading.py
tests/test_req51_project_level_protection.py
```

- [x] C.1 PASS — 3 个测试文件全部存在

---

### C.2 `pytest tests/ -k "req51" --tb=short -q` → 21 passed / 0 failed / 0 errors

命令：
```
$ python3 -m pytest tests/ -k "req51" --tb=short -q
```

stdout：
```
.....................                                                    [100%]
=============================== warnings summary ===============================
../../harness-workflow/tests/test_acceptance_gate_contract.py:90
  /Users/jiazhiwei/claudeProject/harness-workflow/tests/test_acceptance_gate_contract.py:90:
  PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 799 deselected, 1 warning in 11.61s
```

- [x] C.2 PASS — 21 passed / 0 failed / 0 errors（独立核查确认）

---

### C.3 全 suite → 51 failed = bugfix-11 baseline 不增；729 passed = baseline 708 + 21 req-51

命令：
```
$ python3 -m pytest tests/ --tb=no -q 2>&1 | tail -5
```

stdout：
```
FAILED tests/test_validate_test_case_design_completeness.py::test_cli_contract_choices_include_artifact_placement
FAILED tests/test_workflow_next_subprocess.py::test_tc04_subprocess_rfe_execute_advances_to_executing_only
FAILED tests/test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops
FAILED tests/test_workflow_next_workdone_gate.py::test_tc05_same_role_jump_not_blocked_by_workdone_gate
51 failed, 729 passed, 40 skipped, 1 warning, 17 subtests passed in 96.02s (0:01:36)
```

51 failed = bugfix-11 baseline（pre-existing，无新增）；729 passed 含 21 req-51 TC。与主 agent 独立核查数字一致（51 failed / 729 passed / 40 skipped）。

- [x] C.3 PASS — 51 failed 为 pre-existing baseline，无新增失败；729 passed 含 req-51 全 21 TC

---

### C.4 反例 lint：bugfix-11 防回归不破（grep 0 命中）

命令：
```
$ grep -rn "_use_flow_layout\|_use_flat_layout\|FLAT_LAYOUT_FROM_REQ_ID\|FLOW_LAYOUT_FROM_REQ_ID\|BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID" \
    src/harness_workflow/*.py
```

stdout：
```
（无输出）exit=1（grep 0 命中）
```

- [x] C.4 PASS — 0 命中，bugfix-11 防回归关键词未被引入

---

## D dogfood AC-07

### D.1 fresh repo 端到端：tmpdir + git init + install + 写项目级文件 + force-managed → 保留验证

命令（acceptance 独立执行 Python 脚本）：
```python
import tempfile, subprocess, sys, os
from pathlib import Path

with tempfile.TemporaryDirectory(prefix='harness-dogfood-accept-') as tmp:
    tmp = Path(tmp)
    # git init
    subprocess.run(['git', 'init', '--quiet'], cwd=tmp)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp)
    # harness install
    subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install'], cwd=tmp, ...)
    # write project-level files
    (tmp / 'artifacts/main/project/constraints').mkdir(parents=True)
    (tmp / 'artifacts/main/project/experience/roles').mkdir(parents=True)
    (tmp / 'artifacts/main/project/tools/catalog').mkdir(parents=True)
    (tmp / 'artifacts/main/project/constraints/my-rule.md').write_text('PROJECT_RULE: custom rule')
    (tmp / 'artifacts/main/project/experience/roles/analyst.md').write_text('PROJECT_EXPERIENCE: analyst override')
    (tmp / 'artifacts/main/project/tools/catalog/my-tool.md').write_text('# my-tool\nkeywords: [project, custom]')
    # harness install --force-managed
    subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install', '--force-managed'], cwd=tmp, ...)
    # verify preserved
    ...
    # validate --contract user-write-protected-zones
    subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'validate', '--contract', 'user-write-protected-zones'], cwd=tmp, ...)
```

stdout：
```
TMPDIR=/var/folders/6m/zn3fr14x6856870jqqfmpnx80000gn/T/harness-dogfood-accept-jtfft4qf
git init: OK
harness install exit=0
Files written: constraints/my-rule.md, experience/roles/analyst.md, tools/catalog/my-tool.md
harness install --force-managed exit=0
constraints/my-rule.md: 'PROJECT_RULE: custom rule'
experience/roles/analyst.md: 'PROJECT_EXPERIENCE: analyst override'
tools/catalog/my-tool.md: '# my-tool\nkeywords: [project, custom]'
Files preserved: YES (3/3)
validate --contract user-write-protected-zones exit=0
PASS: user-write-protected-zones
```

3 个项目级文件在 `harness install --force-managed` 后内容完全保留（before == after）。`user-write-protected-zones` exit=0。

- [x] D.1 PASS — fresh repo 端到端全链路通过：install → 写文件 → force-managed → 保留 → validate PASS

---

### D.2 加载顺序：fresh repo + 写项目级 analyst.md → 项目级胜出

命令（acceptance 独立执行 Python 脚本）：
```python
with tempfile.TemporaryDirectory(prefix='harness-dogfood-load-') as tmp:
    # git init + harness install
    ...
    # global analyst.md exists (.workflow/context/experience/roles/analyst.md)
    # write project-level analyst.md
    (tmp / 'artifacts/main/project/experience/roles/analyst.md').write_text(
        'PROJECT_ANALYST: project-level analyst override for dogfood D.2'
    )
    # test _merge_project_level_files
    from harness_workflow.workflow_helpers import _merge_project_level_files
    merged = _merge_project_level_files(global_dir, project_dir)
    content = merged['analyst.md'].read_text()
    is_project = 'PROJECT_ANALYST' in content
```

stdout：
```
TMPDIR=/var/folders/6m/zn3fr14x6856870jqqfmpnx80000gn/T/harness-dogfood-load-cnko0wcy
harness install exit=0
Global analyst.md exists: True
Global content (first 80): # 经验：分析师（analyst）  > 溯源：req-40 ...
Written project-level analyst.md
Merged analyst.md content (first 80): PROJECT_ANALYST: project-level analyst override for dogfood D.2
Is project-level: True
AC-05 D.2: project-level wins = PASS
All merged keys: ['planning.md', 'executing.md', 'analyst.md', 'testing.md', 'regression.md', 'requirement-review.md', 'acceptance.md']
```

项目级 analyst.md 覆盖全局（OQ-2 = A 落地）。

- [x] D.2 PASS — 加载顺序项目级优先，全局 analyst.md 被项目级版本完全覆盖

---

## E 范围红线

### E.1 git diff --name-only 不含 PetMallPlatform 任何文件

命令：
```
$ git diff --name-only | grep -i "petmall" | head -10
```

stdout（含中文路径 URL 编码）：
```
".workflow/flow/bugfixes/bugfix-11-petmallplatform-artifacts\350\257\257\346\224\276.../acceptance/checklist.md"
".workflow/flow/bugfixes/bugfix-11-petmallplatform-artifacts\350\257\257\346\224\276.../session-memory.md"
".workflow/state/bugfixes/bugfix-11-petmallplatform-artifacts\350\257\257\346\224\276....yaml"
```

注：这 3 个文件路径前缀均为 `.workflow/flow/bugfixes/` 或 `.workflow/state/bugfixes/`，是 harness-workflow 本仓库内部的 bugfix-11 跟踪文件（即"关于 PetMallPlatform 的 bugfix 元数据"，而非 PetMallPlatform 下游仓库的业务文件）。

验证（去引号后检查路径前缀）：
```python
lines = git_diff_names
petmall = [l.strip('"') for l in lines if 'petmall' in l.lower()]
# All start with '.workflow/flow/bugfixes/' or '.workflow/state/bugfixes/'
# → is_.workflow/: True for all 3
```

结论：diff 中无任何 `PetMallPlatform/` 下游仓库路径，3 条"petmall"行均为本仓 bugfix-11 元数据文件（路径以 `.workflow/` 开头）。

- [x] E.1 PASS — 无 PetMallPlatform 下游业务文件被修改；3 条 petmall 路径均为本仓 bugfix-11 元数据

---

### E.2 不含 `.workflow/project/` 路径回退（项目级路径必须是 `artifacts/{branch}/project/`）

命令：
```
$ git diff --name-only | grep ".workflow/project/" | head -10
```

stdout：
```
（无输出）exit=0（0 命中）
```

E.2 .workflow/project/ files in diff: 0

- [x] E.2 PASS — 0 命中，无任何 `.workflow/project/` 路径，项目级路径正确为 `artifacts/{branch}/project/`

---

## §结论

- verdict: PASS
- 总评：req-51 全部 11 个 acceptance 核查项（A.1～A.3、B.1～B.3、C.1～C.4、D.1～D.2、E.1～E.2）均独立实跑验证通过；21 个 req-51 TC 全 passed，全 suite 51 failed 为 pre-existing baseline 不增，fresh repo dogfood 全链路（git init → install → 写项目级 3 类文件 → force-managed → validate-protected-zones）均 PASS，加载顺序项目级覆盖全局验证通过，范围红线清洁。AC-01 ～ AC-07 全部达标，AC-08（PetMallPlatform 真实验证）属用户手动验收，acceptance 不强制拦截。
- 未达标项: 无
- 路由建议: PASS → done
