---
id: chg-04
title: "接入主流程 + stderr 日志 + 端到端 CLI 验证：_merge_project_level_files 接入 install_repo / update_repo + 日志输出 + subprocess 真实 CLI 触发 stderr 断言"
requirement: req-52
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `src/harness_workflow/workflow_helpers.py`

**变更点 A：第 8279 ~ 8307 行 `_merge_project_level_files` docstring 改造**

当前 docstring（第 8283 ~ 8295 行）含："本 helper 不接入 install_repo / update_repo 主流程；仅供 role-loading-protocol Step 7.6 与 tools-manager Step 2.0 的加载链按文档 SOP 解析使用..."

改写为：
```python
def _merge_project_level_files(
    global_dir: Path,
    project_dir: Path,
) -> dict[str, Path]:
    """req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并）+
    req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-04（接入主流程-stderr日志-端到端CLI验证）：
    把全局子树与项目级子树按 basename 合并，同名时项目级覆盖全局。

    返回：dict[basename, Path]，basename 为相对 global_dir / project_dir 的路径字符串。

    fallback：
    - global_dir 不存在 → 仅返回 project_dir 内容（如有）；
    - project_dir 不存在 → 仅返回 global_dir 内容（向后兼容）；
    - 两者都不存在 → 返回 {}。

    集成（chg-04 落地）：
    - 由 install_repo / update_repo 入口段调用（line ~3790 区域），对三个 scope 大类
      （constraints / experience / tools）逐个触发探测；结果通过 _log_project_level_load 输出 stderr。
    - 加载链消费：role-loading-protocol Step 7.6 / 7.6.1（chg-03 索引懒加载）+ tools-manager Step 2.0。
    """
    # 函数体不变（保持 req-51 / chg-03 落地版本）
    merged: dict[str, Path] = {}
    if global_dir.exists():
        for f in global_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(global_dir).as_posix()
                merged[rel] = f
    if project_dir.exists():
        for f in project_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(project_dir).as_posix()
                merged[rel] = f  # 同名覆盖全局
    return merged
```

**变更点 B：在 `_merge_project_level_files` 函数后新增 `_log_project_level_load` helper**

```python
def _log_project_level_load(
    root: Path,
    scope: str,
    hits: int,
    fallback_used: bool,
) -> None:
    """req-52 / chg-04：项目级加载链 stderr 日志输出 helper。

    格式：[harness] project-level loaded: {N} files from {path}（fallback={legacy_path or "n/a"}）

    入参：
    - root: 项目根目录
    - scope: ∈ {"constraints", "experience", "tools"}
    - hits: 命中文件数
    - fallback_used: 是否走了 legacy 路径（artifacts/{branch}/project/）

    行为：仅写 stderr，不写盘；e2e pytest 断言依赖此格式（OQ-C = A）。
    """
    # 主路径（chg-01 OQ-A 主路径）
    main_path = f"artifacts/project/{scope}/"
    if fallback_used:
        branch = _get_git_branch(root) or "main"
        legacy_path = f"artifacts/{branch}/project/{scope}/"
        msg = (
            f"[harness] project-level loaded: {hits} files from {legacy_path}"
            f"（fallback=主路径 {main_path} 不存在）"
        )
    else:
        msg = (
            f"[harness] project-level loaded: {hits} files from {main_path}"
            f"（fallback=n/a）"
        )
    print(msg, file=sys.stderr)
```

**变更点 C：`install_repo` 入口段集成（约第 3786 行后，feedback.jsonl 迁移段后）**

在 install_repo 函数体中、`_migrate_workflow_dir` 之后、平台选择交互之前（约 line ~3791 处）插入 1 块代码：

```python
    # ---- req-52 / chg-04（接入主流程-stderr日志-端到端CLI验证）：项目级合并行为预热 + 日志输出 ----
    # 三个 scope 大类（constraints / experience / tools）各跑一次 _merge_project_level_files，
    # 触发主路径 / legacy fallback 探测 + stderr 日志（OQ-C = A）。
    # check=True（dry-run）模式下也输出日志，方便 e2e pytest 用 --check 观测。
    for scope in ("constraints", "experience", "tools"):
        # 主路径（chg-01 OQ-A 无 branch 主路径）
        main_project = root / "artifacts" / "project" / scope
        # legacy fallback（chg-01 双轨过渡）
        branch = _get_git_branch(root) or "main"
        legacy_project = root / "artifacts" / branch / "project" / scope

        global_dir_map = {
            "constraints": root / ".workflow" / "context" / "constraints",
            "experience": root / ".workflow" / "context" / "experience",
            "tools": root / ".workflow" / "tools",
        }
        global_dir = global_dir_map[scope]

        # 优先主路径，fallback legacy
        if main_project.exists():
            merged = _merge_project_level_files(global_dir, main_project)
            project_hits = sum(1 for f in main_project.rglob("*") if f.is_file())
            _log_project_level_load(root, scope, project_hits, fallback_used=False)
        elif legacy_project.exists():
            merged = _merge_project_level_files(global_dir, legacy_project)
            project_hits = sum(1 for f in legacy_project.rglob("*") if f.is_file())
            _log_project_level_load(root, scope, project_hits, fallback_used=True)
        else:
            # 两条路径均不存在：日志记录 0 文件
            _log_project_level_load(root, scope, hits=0, fallback_used=False)
        # merged 暂不消费，仅触发探测 + 日志
```

**注意**：`update_repo` 是 `install_repo` 空壳委托（`force_skill=True`，line 4113），不需独立改动，自动继承本日志逻辑。

### 1.2 新增 `tests/test_req52_e2e_log.py`

```python
"""req-52 / chg-04：端到端真实 CLI 触发 + stderr 日志断言（OQ-D = A）。

用例：
- TC-01-zero-files：项目级 0 文件（无 artifacts/project/，无 legacy）→ stderr 含 "0 files"
- TC-02-main-path-hit：项目级 ≥ 1 文件（artifacts/project/constraints/rule.md）→ stderr 含 "from artifacts/project/constraints/" + ≥ 1 file
- TC-03-legacy-fallback：仅 artifacts/{branch}/project/ 有文件 → stderr 含 "fallback=主路径" 提示

测试触发方式：subprocess.run([sys.executable, "-m", "harness_workflow.cli", "install", "--check"]) 真实子进程。
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_harness_install_check(cwd: Path) -> subprocess.CompletedProcess:
    """子进程触发真实 CLI `harness install --check`。"""
    env = dict(os.environ)
    # 让子进程能找到 harness_workflow 包
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install", "--check"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _bootstrap_minimal_repo(target: Path) -> None:
    """在 target 创建一个最小可跑 harness install --check 的仓骨架。

    复制必要的 .workflow/ 子树（仅 contract / runtime 必需文件）；
    init git repo 以便 _get_git_branch 不报错。
    """
    # 复制 scaffold_v2 mirror 作为最小骨架
    scaffold = REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2"
    shutil.copytree(scaffold, target, dirs_exist_ok=True)
    # init git
    subprocess.run(["git", "init", "-q"], cwd=str(target), check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "main"], cwd=str(target), check=False)


def test_zero_files_e2e(tmp_path):
    """TC-01：项目级 0 文件 → stderr 含 'project-level loaded: 0 files'。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    _bootstrap_minimal_repo(repo)
    # 不创建 artifacts/project/* 任何子目录

    result = _run_harness_install_check(repo)
    assert result.returncode == 0, f"stderr={result.stderr}\nstdout={result.stdout}"
    # 断言三 scope 各有 1 行 "0 files"
    assert "[harness] project-level loaded: 0 files" in result.stderr, (
        f"stderr 缺少零文件日志：{result.stderr}"
    )
    # 三 scope 各一次（≥ 3 行）
    count = result.stderr.count("[harness] project-level loaded:")
    assert count >= 3, f"期望 ≥ 3 行 project-level loaded（constraints/experience/tools），实际 {count} 行：{result.stderr}"


def test_main_path_hit_e2e(tmp_path):
    """TC-02：项目级 ≥ 1 文件（主路径 artifacts/project/constraints/rule.md）→ stderr 含 'from artifacts/project/constraints/'。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    _bootstrap_minimal_repo(repo)

    # 在主路径 artifacts/project/constraints/ 写 1 个文件
    rule = repo / "artifacts" / "project" / "constraints" / "rule.md"
    rule.parent.mkdir(parents=True, exist_ok=True)
    rule.write_text("# 项目独有规则\n", encoding="utf-8")

    result = _run_harness_install_check(repo)
    assert result.returncode == 0, f"stderr={result.stderr}\nstdout={result.stdout}"
    # 断言主路径命中：含 "from artifacts/project/constraints/" + 文件数 ≥ 1
    assert "from artifacts/project/constraints/" in result.stderr, (
        f"stderr 缺少主路径日志：{result.stderr}"
    )
    # 断言 fallback=n/a（主路径命中）
    assert "fallback=n/a" in result.stderr, (
        f"主路径命中时应有 'fallback=n/a' 标记：{result.stderr}"
    )


def test_legacy_fallback_e2e(tmp_path):
    """TC-03：仅 legacy artifacts/{branch}/project/ 有文件 → stderr 含 fallback 主路径不存在提示。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    _bootstrap_minimal_repo(repo)

    # 仅在 legacy 路径写文件（branch = main，由 _bootstrap_minimal_repo init）
    legacy = repo / "artifacts" / "main" / "project" / "experience" / "legacy-exp.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("# legacy 经验\n", encoding="utf-8")
    # 主路径 artifacts/project/experience/ 不存在

    result = _run_harness_install_check(repo)
    assert result.returncode == 0, f"stderr={result.stderr}\nstdout={result.stdout}"
    # 断言 legacy 命中：含 "from artifacts/main/project/experience/"
    assert "from artifacts/main/project/experience/" in result.stderr, (
        f"stderr 缺少 legacy fallback 日志：{result.stderr}"
    )
    # 断言 fallback=主路径 ... 不存在 提示
    assert "fallback=主路径" in result.stderr, (
        f"legacy fallback 时应有 'fallback=主路径' 提示：{result.stderr}"
    )
```

### 1.3 scaffold_v2 mirror 同步

- 本 chg 仅改 `src/harness_workflow/workflow_helpers.py` Python 源码；
- **不**触碰 `src/harness_workflow/assets/scaffold_v2/` mirror 模板；
- **不**触碰 `.workflow/context/roles/*.md` 契约文档（这些由 chg-01 处理）；
- 无硬门禁五同步要求。

## 2. 实施步骤（顺序 + 命令）

### Step 1：先跑现有 5 份 req-51 tests + 现有 install_repo 单测取基线

```bash
pytest tests/test_req51_project_level_*.py tests/test_install_repo_sync_contract.py -v
# 期望：全 PASS，记录 PASS 数；后续改动不得回归
```

### Step 2：编辑 `workflow_helpers.py` 三处变更点 A / B / C

- 用 Edit 工具按 §1.1 顺序：
  - 改 `_merge_project_level_files` docstring（变更点 A）；
  - 在其后新增 `_log_project_level_load` helper（变更点 B）；
  - 在 `install_repo` 入口段插入项目级日志调用块（变更点 C）；
- 自检：

```bash
grep -n "^def _log_project_level_load" src/harness_workflow/workflow_helpers.py   # 期望 1 命中
grep -nE "本 helper 不接入 install_repo" src/harness_workflow/workflow_helpers.py   # 期望 0 命中（已删除）
grep -n "for scope in (\"constraints\", \"experience\", \"tools\"):" src/harness_workflow/workflow_helpers.py   # 期望 1 命中
python3 -c "from harness_workflow.workflow_helpers import _log_project_level_load; print('OK')"
```

### Step 3：新增 `tests/test_req52_e2e_log.py`

```bash
pytest tests/test_req52_e2e_log.py -v   # 期望 ≥ 3 用例 PASS
```

### Step 4：手动 dogfood 真实触发 stderr 日志

```bash
# 在本仓真实跑 harness install --check，肉眼确认 stderr 含三行 "[harness] project-level loaded:"
harness install --check 2>&1 | grep "project-level loaded"
# 期望：3 行（constraints / experience / tools 各一）
```

### Step 5：5 份 req-51 tests + install_repo 单测回归确认

```bash
pytest tests/test_req51_project_level_*.py tests/test_install_repo_sync_contract.py -v   # 全 PASS
```

### Step 6：契约自检全绿

```bash
harness validate --human-docs           # exit 0
harness validate --contract all         # exit 0
```

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（破坏面收敛在 workflow_helpers.py 三处改动 + 新增 1 份 e2e test）
> 波及接口清单（git diff --name-only 预估）：
> - `src/harness_workflow/workflow_helpers.py`（_merge docstring + _log helper + install_repo 入口段）
> - `tests/test_req52_e2e_log.py`（新建）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-zero-files-e2e | `pytest tests/test_req52_e2e_log.py::test_zero_files_e2e`（subprocess `harness install --check`） | PASS：stderr 含 ≥ 3 行 `project-level loaded: 0 files`；returncode = 0 | AC-06 / AC-07 | P0 |
| TC-02-main-path-hit-e2e | `pytest tests/test_req52_e2e_log.py::test_main_path_hit_e2e`（artifacts/project/constraints/rule.md 写入）| PASS：stderr 含 `from artifacts/project/constraints/` + `fallback=n/a`；returncode = 0 | AC-06 / AC-07 | P0 |
| TC-03-legacy-fallback-e2e | `pytest tests/test_req52_e2e_log.py::test_legacy_fallback_e2e`（仅 legacy 写入）| PASS：stderr 含 `from artifacts/main/project/experience/` + `fallback=主路径` 提示；returncode = 0 | AC-02 / AC-06 / AC-07 | P0 |
| TC-04-docstring-no-disclaimer | grep `src/harness_workflow/workflow_helpers.py` 不含 "本 helper 不接入 install_repo / update_repo 主流程" 字样 | grep 命中 = 0 | AC-06 | P0 |
| TC-05-helper-registered | `python3 -c "from harness_workflow.workflow_helpers import _log_project_level_load; print('OK')"` | stdout = "OK"；exit 0 | AC-06 | P0 |
| TC-06-install-repo-stderr-runtime | 直跑 `harness install --check`（本仓） | stderr 含 ≥ 3 行 `[harness] project-level loaded:` | AC-06 / AC-07 | P0 |
| TC-07-req51-no-regression | `pytest tests/test_req51_project_level_*.py -v` | 全 PASS（无回归） | AC-08 | P0 |

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：端到端 CLI 触发 + stderr 断言全 PASS（本 chg 核心）
pytest tests/test_req52_e2e_log.py -v

# L2：docstring "不接入主流程" 字样消除
! grep -n "本 helper 不接入 install_repo" src/harness_workflow/workflow_helpers.py
! grep -n "本 helper 不接入 install_repo / update_repo 主流程" src/harness_workflow/workflow_helpers.py

# L3：_log_project_level_load helper 注册
grep -n "^def _log_project_level_load" src/harness_workflow/workflow_helpers.py
python3 -c "from harness_workflow.workflow_helpers import _log_project_level_load; print('OK')"

# L4：install_repo 入口段集成
grep -nE 'for scope in \("constraints", "experience", "tools"\):' src/harness_workflow/workflow_helpers.py

# L5：手动 dogfood 真实 CLI 触发 stderr 日志
harness install --check 2>&1 | grep -c "\[harness\] project-level loaded:"
# 期望 ≥ 3（三 scope 各一行）

# L6：5 份 req-51 tests + install_repo 单测无回归
pytest tests/test_req51_project_level_protection.py tests/test_req51_project_level_loading.py tests/test_req51_project_level_dogfood.py tests/test_install_repo_sync_contract.py -v

# L7：契约自检全绿
harness validate --human-docs
harness validate --contract all
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

| live 文件 | mirror 文件 | 同步动作 |
|-----------|------------|---------|
| `src/harness_workflow/workflow_helpers.py` | （src 不进 mirror） | N/A，src/harness_workflow/ Python 源码不属硬门禁五保护面 |
| `tests/test_req52_e2e_log.py`（新建） | （tests 不进 mirror） | N/A |

**注意**：本 chg 改动均在 `src/harness_workflow/` Python 源码层 + `tests/`，**不**触碰 `src/harness_workflow/assets/scaffold_v2/` mirror 模板，**无**硬门禁五同步要求。
