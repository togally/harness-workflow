---
id: chg-02
title: "src 硬编码 main 全面去除：validate_contract.py + workflow_helpers.py 关键点改 branch-aware + 反例 lint 防回归"
requirement: req-52
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `src/harness_workflow/validate_contract.py`

**变更点 A：第 550 ~ 553 行 `_ARCHIVE_EXEMPTION_DIRS` 集合**

当前形态：
```python
_ARCHIVE_EXEMPTION_DIRS = {
    str(artifacts_dir / "main" / "archive"),
    str(artifacts_dir / "main" / "regressions"),
}
```

改为 branch-aware（glob 任意子目录）：
```python
# req-52 / chg-02：硬编码 main 改 branch-aware glob，覆盖任意 git branch 下的历史 archive / regressions 子目录。
_ARCHIVE_EXEMPTION_DIRS = set()
if artifacts_dir.exists():
    for branch_dir in artifacts_dir.iterdir():
        if not branch_dir.is_dir():
            continue
        archive_dir = branch_dir / "archive"
        regressions_dir = branch_dir / "regressions"
        if archive_dir.exists():
            _ARCHIVE_EXEMPTION_DIRS.add(str(archive_dir))
        if regressions_dir.exists():
            _ARCHIVE_EXEMPTION_DIRS.add(str(regressions_dir))
```

**变更点 B：第 559 ~ 577 行规则 0（stage-name 子目录扫描根）**

当前形态：`req_base = artifacts_dir / "main" / "requirements"`，仅扫 main 分支。

改为遍历 artifacts/ 下所有 branch 子目录：
```python
# req-52 / chg-02：硬编码 main 改 branch-aware，覆盖任意 git branch 下的 requirements 树。
if artifacts_dir.exists():
    for branch_dir in artifacts_dir.iterdir():
        if not branch_dir.is_dir():
            continue
        # 跳过 chg-01 新主路径 artifacts/project/（项目级承载层，无 requirements 子树）
        if branch_dir.name == "project":
            continue
        req_base = branch_dir / "requirements"
        if not req_base.is_dir():
            continue
        for req_dir in req_base.iterdir():
            if not req_dir.is_dir():
                continue
            if _is_under_archive(req_dir):
                continue  # 历史豁免
            for child in req_dir.iterdir():
                if child.is_dir() and child.name in _STAGE_NAME_SUBDIRS:
                    try:
                        rel = child.relative_to(root)
                    except ValueError:
                        rel = child
                    violations.append(
                        f"artifacts/ 下发现 stage-name 子目录（机器型工件禁落此处）：{rel}/"
                    )
```

**变更点 C：第 1114 行 docstring 注释**

注释 `artifacts/main/project/` 改为 `artifacts/project/`（主路径）+ 末尾追加："（legacy `artifacts/{branch}/project/` 由 req-52 / chg-01 双轨过渡兼容）"。

### 1.2 `src/harness_workflow/workflow_helpers.py`

**变更点 D：第 197 ~ 202 行 `_SCAFFOLD_V2_MIRROR_WHITELIST` 项目级条目**

当前：
```python
# req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）：
# artifacts/main/project/{constraints,experience,tools}/ 三类项目级机器型文档承载层
# （chg-01（契约底座-artifacts-project-豁免）已在 repository-layout.md §2.1 / §3 顶部豁免段落地）。
# 跨项目语义不通用，不纳入 scaffold_v2 mirror；harness install / update / force-managed 全流程跳过。
"artifacts/main/project/",
```

改为：
```python
# req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）+
# req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-02（src硬编码main全面去除-branch-aware）：
# 项目级三类机器型文档承载层（constraints / experience / tools）。chg-01（契约底座-artifacts-project-豁免）
# 已落 §2.1 / §3 豁免段；req-52 / chg-01（契约层路径迁移-无branch项目级-双轨过渡）OQ-A = D-modified
# 主路径迁移到 artifacts/project/（无 branch），legacy artifacts/{branch}/project/ 双轨过渡兼容。
# 白名单匹配语义为 substring（any(white in relative for white in WHITELIST)），下两条覆盖：
#   - "artifacts/project/" 主路径（无 branch，跟项目走）
#   - "/project/" substring 兜底捕获 artifacts/<任意 branch>/project/... legacy 路径
# 共同保证：harness install / update / force-managed 全流程跳过项目级承载层。
"artifacts/project/",
"/project/",
```

> **注意**：`"/project/"` 是 substring 兜底，会同时覆盖 `artifacts/<任意 branch>/project/` 与 `artifacts/main/project/`（legacy）；副作用面排查：mirror dict 中可能含 `.workflow/context/project/...` 路径，但本白名单语义就是 substring 包含 `/project/` 即豁免——此前 `.workflow/context/project/` 也由 harness-manager.md 硬门禁五例外白名单豁免（live 同步行为），口径一致，无回归风险。executing 阶段应跑 mirror dict 全量 grep `/project/` 自检确认副作用面收敛。

**变更点 E：第 4147 ~ 4154 行 `_next_req_id` 扫描归档树**

当前：
```python
branch = _get_git_branch(root) or "main"
scan_dirs = [
    root / ".workflow" / "state" / "requirements",
    root / ".workflow" / "flow" / "requirements",
    resolve_requirement_root(root),
    root / "artifacts" / branch / "archive" / "requirements",
    root / ".workflow" / "flow" / "archive" / "main",
]
```

改为：
```python
# req-52 / chg-02：硬编码 main 改 glob，覆盖任意历史 branch 归档子目录。
branch = _get_git_branch(root) or "main"
scan_dirs = [
    root / ".workflow" / "state" / "requirements",
    root / ".workflow" / "flow" / "requirements",
    resolve_requirement_root(root),
    root / "artifacts" / branch / "archive" / "requirements",
]
flow_archive = root / ".workflow" / "flow" / "archive"
if flow_archive.exists():
    for branch_dir in flow_archive.iterdir():
        if branch_dir.is_dir():
            scan_dirs.append(branch_dir)
```

**变更点 F：第 4180 ~ 4188 行 `_next_bugfix_id` 同上**

```python
# req-52 / chg-02：硬编码 main 改 glob。
branch = _get_git_branch(root) or "main"
scan_dirs = [
    root / "artifacts" / "bugfixes",
    root / "artifacts" / branch / "bugfixes",
    root / ".workflow" / "state" / "bugfixes",
    root / ".workflow" / "flow" / "bugfixes",
    root / "artifacts" / branch / "archive" / "bugfixes",
]
flow_archive = root / ".workflow" / "flow" / "archive"
if flow_archive.exists():
    for branch_dir in flow_archive.iterdir():
        if branch_dir.is_dir():
            scan_dirs.append(branch_dir)
```

**变更点 G：第 3426 / 3428 / 6548 / 8140 行 docstring 注释更新**

把现有注释中的 `artifacts/main/project/` 字面引用改为 `artifacts/project/`（主路径）+ 加一句"legacy `artifacts/{branch}/project/` 由 req-52 / chg-01 双轨过渡兼容"。

### 1.3 新增 `tests/test_req52_no_main_hardcode.py`

```python
"""req-52 / chg-02：src 硬编码 main 反例 lint，防回归。

用例：
- TC-01-grep-main-literal：grep src 全树 '"main"' 字面值，命中数 ≤ 白名单
- TC-02-path-join-main：grep src 全树 '/ "main" /' Path 拼接形态，命中数 = 0
- TC-03-artifacts-main-prefix：grep src 全树 '"artifacts/main/' 前缀，命中数 = 0
- TC-04-whitelist-exemption：白名单豁免单测（ff_auto.py + _get_git_branch fallback 形态被豁免）
"""
import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "harness_workflow"

# 白名单：以下 grep 命中行被豁免（合理的 fallback 默认值，非硬编码 main 路径）
_HARDCODE_MAIN_WHITELIST_PATTERNS = [
    re.compile(r'_get_git_branch\([^)]*\)\s*or\s*"main"'),  # 标准 fallback 形式
    re.compile(r'^\s*return\s*"main"\s*$'),                  # ff_auto.py:210 fallback 函数
    re.compile(r'^\s*#'),                                     # 整行注释
    re.compile(r'^\s*"""'),                                   # docstring 行
    re.compile(r"^\s*'''"),                                   # docstring 行
]


def _grep_src(pattern: str) -> list[tuple[Path, int, str]]:
    """rglob src 全树，按 regex pattern 抓取命中（文件 / 行号 / 行内容）。"""
    hits = []
    py_files = list(SRC_ROOT.rglob("*.py"))
    rgx = re.compile(pattern)
    for f in py_files:
        # 跳过 assets/scaffold_v2/（mirror 副本，由 chg-01 / mirror sync 处理）
        if "scaffold_v2" in str(f):
            continue
        try:
            for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if rgx.search(line):
                    hits.append((f.relative_to(REPO_ROOT), lineno, line))
        except UnicodeDecodeError:
            continue
    return hits


def _is_whitelisted(line: str) -> bool:
    return any(p.search(line) for p in _HARDCODE_MAIN_WHITELIST_PATTERNS)


def test_grep_main_literal_no_hardcode():
    """TC-01：grep src 全树 '"main"' 字面值，命中数 ≤ 白名单。"""
    hits = _grep_src(r'"main"')
    violations = [(f, n, l) for f, n, l in hits if not _is_whitelisted(l)]
    assert not violations, (
        f"src 树发现非白名单硬编码 main 字面值，需改 branch-aware：\n"
        + "\n".join(f"  {f}:{n}: {l.strip()}" for f, n, l in violations)
    )


def test_path_join_main_zero():
    """TC-02：grep src 全树 '/ "main" /' Path 拼接形态，命中数 = 0。"""
    hits = _grep_src(r'/\s*"main"\s*/')
    violations = [(f, n, l) for f, n, l in hits if not _is_whitelisted(l)]
    assert not violations, (
        f"src 树发现 Path 拼接硬编码 main 形态（防 validate_contract.py:551/552/562 同型病）：\n"
        + "\n".join(f"  {f}:{n}: {l.strip()}" for f, n, l in violations)
    )


def test_artifacts_main_prefix_zero():
    """TC-03：grep src 全树 '"artifacts/main/' 前缀字面值，命中数 = 0。"""
    hits = _grep_src(r'"artifacts/main/')
    violations = [(f, n, l) for f, n, l in hits if not _is_whitelisted(l)]
    assert not violations, (
        f"src 树发现 artifacts/main/ 字面前缀（防 _SCAFFOLD_V2_MIRROR_WHITELIST 同型病）：\n"
        + "\n".join(f"  {f}:{n}: {l.strip()}" for f, n, l in violations)
    )


def test_whitelist_exemption():
    """TC-04：白名单豁免单测——确认 ff_auto.py + _get_git_branch fallback 形态被豁免。"""
    sample_lines = [
        '    return "main"',                        # ff_auto.py:210
        '    branch = _get_git_branch(root) or "main"',  # workflow_helpers 兜底
        '    current_branch = _get_git_branch(root) or "main"',  # 同上
    ]
    for line in sample_lines:
        assert _is_whitelisted(line), f"白名单应豁免但未豁免：{line!r}"
```

### 1.4 同步更新 `tests/test_req51_project_level_protection.py:238`

当前断言 `assert "artifacts/main/project/" in _SCAFFOLD_V2_MIRROR_WHITELIST`，本 chg 把白名单字面值改为 `"artifacts/project/"` + `"/project/"`，更新断言为：

```python
# req-52 / chg-02：白名单字面值从 "artifacts/main/project/" 改为 "artifacts/project/" + "/project/"
assert "artifacts/project/" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
    f"_SCAFFOLD_V2_MIRROR_WHITELIST 缺少 'artifacts/project/' 主路径条目（req-52 / chg-01 OQ-A = D-modified）"
)
assert "/project/" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
    f"_SCAFFOLD_V2_MIRROR_WHITELIST 缺少 '/project/' substring 兜底条目（req-52 / chg-02 兼容 legacy artifacts/{{branch}}/project/）"
)
```

## 2. 实施步骤（顺序 + 命令）

### Step 1：先跑现有 5 份 req-51 tests 取基线 PASS 数

```bash
pytest tests/test_req51_project_level_protection.py tests/test_req51_project_level_loading.py tests/test_req51_project_level_dogfood.py -v
# 期望：全 PASS，记录 PASS 数；后续改动不得回归
```

### Step 2：编辑 `validate_contract.py` 三处变更点 A / B / C

- 用 Edit 工具按 1.1 顺序改 _ARCHIVE_EXEMPTION_DIRS 集合 + 规则 0 扫描 + docstring 注释；
- 自检：

```bash
grep -nE '/ "main" /' src/harness_workflow/validate_contract.py   # 期望 0 命中
grep -n "branch_dir.iterdir" src/harness_workflow/validate_contract.py   # ≥ 2 命中（A + B）
```

### Step 3：编辑 `workflow_helpers.py` 五处变更点 D / E / F / G

- 用 Edit 工具按 1.2 顺序改 _SCAFFOLD_V2_MIRROR_WHITELIST + _next_req_id + _next_bugfix_id + 3 段注释；
- 自检：

```bash
grep -n '"artifacts/project/"' src/harness_workflow/workflow_helpers.py   # ≥ 1 命中（白名单主路径）
grep -n '"/project/"' src/harness_workflow/workflow_helpers.py   # ≥ 1 命中（白名单 substring 兜底）
grep -n 'flow_archive = root / "\.workflow"' src/harness_workflow/workflow_helpers.py   # ≥ 2 命中（_next_req_id + _next_bugfix_id）
```

### Step 4：新增 `tests/test_req52_no_main_hardcode.py`

```bash
pytest tests/test_req52_no_main_hardcode.py -v   # 期望 ≥ 4 用例 PASS
```

### Step 5：同步更新 `tests/test_req51_project_level_protection.py:238`

- 用 Edit 工具改断言为本 plan §1.4 形态；
- 重跑：

```bash
pytest tests/test_req51_project_level_protection.py -v   # 期望全 PASS（无回归）
```

### Step 6：契约自检全绿

```bash
harness validate --contract artifact-placement   # exit 0（核心病灶 1 ~ 3 修复后扫描覆盖面扩大但合规）
harness validate --contract all                  # exit 0
```

### Step 7：5 份 req-51 tests 回归确认

```bash
pytest tests/test_req51_project_level_protection.py tests/test_req51_project_level_loading.py tests/test_req51_project_level_dogfood.py -v   # 期望全 PASS
```

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（破坏面收敛在 validate_contract.py + workflow_helpers.py 两文件 + 新增 test 文件）
> 波及接口清单（git diff --name-only 预估）：
> - `src/harness_workflow/validate_contract.py`
> - `src/harness_workflow/workflow_helpers.py`
> - `tests/test_req52_no_main_hardcode.py`（新建）
> - `tests/test_req51_project_level_protection.py`（断言同步）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-grep-main-literal | `tests/test_req52_no_main_hardcode.py::test_grep_main_literal_no_hardcode` | PASS：src 全树字面 `"main"` 命中数 ≤ 白名单（约 12 ~ 14 处兜底） | AC-03 / AC-04 | P0 |
| TC-02-path-join-main | `tests/test_req52_no_main_hardcode.py::test_path_join_main_zero` | PASS：`/ "main" /` 形态命中 = 0 | AC-03 / AC-04 | P0 |
| TC-03-artifacts-main-prefix | `tests/test_req52_no_main_hardcode.py::test_artifacts_main_prefix_zero` | PASS：`"artifacts/main/` 前缀命中 = 0 | AC-03 / AC-04 | P0 |
| TC-04-whitelist-exemption | `tests/test_req52_no_main_hardcode.py::test_whitelist_exemption` | PASS：ff_auto.py + `_get_git_branch fallback` 形态被豁免 | AC-04 | P0 |
| TC-05-validate-contract-branch-aware | 在 dev branch（非 main）仓跑 `harness validate --contract artifact-placement` | exit 0；archive / regressions / requirements 子目录扫描覆盖任意 branch | AC-03 | P0 |
| TC-06-mirror-whitelist-double-entry | grep `_SCAFFOLD_V2_MIRROR_WHITELIST` 含 `"artifacts/project/"` + `"/project/"` 两条 | 2 个断言都为 True | AC-03 / AC-08 | P0 |
| TC-07-req51-tests-no-regression | `pytest tests/test_req51_project_level_*.py -v` | 全 PASS（断言已同步） | AC-08 | P1 |

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：硬编码 main 反例 lint 全 PASS
pytest tests/test_req52_no_main_hardcode.py -v

# L2：grep src 全树字面值确认（手动复核）
grep -rn '"main"' src/harness_workflow/ | grep -v "scaffold_v2" | grep -vE '_get_git_branch\([^)]*\)\s*or\s*"main"' | grep -vE '^\s*return\s*"main"\s*$' | grep -vE '^[^:]+:[0-9]+:\s*#'
# 期望：输出为空（除 docstring 行可能命中，需肉眼确认）

# L3：Path 拼接形态命中 = 0
grep -rn '/ "main" /' src/harness_workflow/ | grep -v "scaffold_v2"
# 期望：输出为空

# L4：artifacts/main/ 字面前缀命中 = 0
grep -rn '"artifacts/main/' src/harness_workflow/ | grep -v "scaffold_v2"
# 期望：输出为空

# L5：白名单双轨条目
grep -nE '"artifacts/project/"|"/project/"' src/harness_workflow/workflow_helpers.py
# 期望 ≥ 2 命中

# L6：现有 req-51 tests 无回归
pytest tests/test_req51_project_level_protection.py tests/test_req51_project_level_loading.py tests/test_req51_project_level_dogfood.py -v

# L7：契约自检全绿
harness validate --contract artifact-placement
harness validate --contract all
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

| live 文件 | mirror 文件 | 同步动作 |
|-----------|------------|---------|
| `src/harness_workflow/validate_contract.py` | （src 不进 mirror） | N/A，src/harness_workflow/ 是 Python 源码而非 scaffold_v2 模板，不纳入硬门禁五 |
| `src/harness_workflow/workflow_helpers.py` | （src 不进 mirror） | N/A，同上 |
| `tests/test_req52_no_main_hardcode.py`（新建） | （tests 不进 mirror） | N/A |

**注意**：本 chg 改动均在 `src/harness_workflow/` Python 源码层 + `tests/`，**不**触碰 `src/harness_workflow/assets/scaffold_v2/` mirror 模板，**无**硬门禁五同步要求；mirror 同步由 chg-01 处理。
