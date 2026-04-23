"""chg-08（pyproject.toml package-data 补齐 + 加打包契约测试（防漏装回归））

打包契约测试：保证 src/harness_workflow/assets/scaffold_v2/.workflow/ 下所有 mirror
文件都被 setuptools package-data patterns 打入 wheel；并防止 dev 端 mirror 树被运行时
数据污染。

来源：req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2
mirror 保持一致））/ reg-02（req-36 AC-5 收口：CLI 路由 + packaging 双根因）根因 B。
"""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    import tomllib  # Python ≥ 3.11
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

import pytest


# ----- 共享 helper -----


def _dev_mirror_root() -> Path:
    """dev 端 scaffold_v2 mirror 的源码路径（src/ 下）。"""
    here = Path(__file__).resolve().parent
    return here.parent / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow"


def _dev_mirror_relative_files() -> set[str]:
    """枚举 dev 端 mirror 下所有文件（相对 .workflow/ 的 POSIX 路径）。"""
    root = _dev_mirror_root()
    files: set[str] = set()
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        # 过滤显式垃圾文件，避免误把 .DS_Store / __pycache__ / .pyc 当 mirror 内容
        rel = p.relative_to(root).as_posix()
        if rel.endswith(".DS_Store") or "__pycache__" in rel.split("/") or rel.endswith(".pyc"):
            continue
        files.add(rel)
    return files


def _load_package_data_patterns() -> list[str]:
    """读取 pyproject.toml `[tool.setuptools.package-data].harness_workflow` 列表。"""
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return list(data["tool"]["setuptools"]["package-data"]["harness_workflow"])


def _setuptools_glob_match(rel_to_package: str, patterns: list[str]) -> bool:
    """模拟 setuptools include_package_data 的 glob 匹配语义。

    setuptools >= 69 支持 `**/*` 递归 glob；细分 patterns（如 `assets/scaffold_v2/.workflow/context/*.md`）
    只匹配该层文件，不递归。本函数实现两层语义：
    - 含 `**` 的 pattern 用 fnmatch 全路径匹配（跨目录通配）
    - 不含 `**` 的 pattern 仅匹配同层 `*` / `?`（不跨目录）

    rel_to_package: 相对于 src/harness_workflow/ 的 POSIX 路径。
    """
    for pat in patterns:
        if "**" in pat:
            # 递归 glob：把 ** 翻译为 fnmatch 等价的多段通配
            # fnmatch 不原生支持 **，把 ** 段视为 0 或多层目录通配
            # 简单实现：把 `**/*` 视为"任意深度任意文件"
            if pat.endswith("/**/*"):
                prefix = pat[: -len("/**/*")]
                if rel_to_package.startswith(prefix + "/") or rel_to_package == prefix:
                    return True
            else:
                # 通用回退：把 ** 替换为 *，再用 fnmatch（保守，可能少匹配）
                if fnmatch.fnmatch(rel_to_package, pat.replace("**/", "*/").replace("**", "*")):
                    return True
        else:
            # 非递归：只匹配同层
            if "/" in pat:
                pat_dir, pat_name = pat.rsplit("/", 1)
                if "/" in rel_to_package:
                    rel_dir, rel_name = rel_to_package.rsplit("/", 1)
                    if rel_dir == pat_dir and fnmatch.fnmatch(rel_name, pat_name):
                        return True
            else:
                if "/" not in rel_to_package and fnmatch.fnmatch(rel_to_package, pat):
                    return True
    return False


def _packaged_mirror_relative_files() -> set[str]:
    """按 pyproject patterns 模拟 setuptools 实际打包的 mirror 文件集合。"""
    patterns = _load_package_data_patterns()
    package_root = REPO_ROOT / "src" / "harness_workflow"
    mirror_root = package_root / "assets" / "scaffold_v2" / ".workflow"
    out: set[str] = set()
    for p in mirror_root.rglob("*"):
        if not p.is_file():
            continue
        rel_to_pkg = p.relative_to(package_root).as_posix()
        rel_to_mirror = p.relative_to(mirror_root).as_posix()
        if rel_to_mirror.endswith(".DS_Store") or "__pycache__" in rel_to_mirror.split("/") or rel_to_mirror.endswith(".pyc"):
            continue
        if _setuptools_glob_match(rel_to_pkg, patterns):
            out.add(rel_to_mirror)
    return out


# ----- 测试用例 -----


def test_wheel_contains_all_scaffold_v2_mirror_files() -> None:
    """STEP-1（红）→ STEP-2（绿）：dev mirror 全集 == pyproject patterns 实际匹配集。

    判据：按 pyproject.toml `[tool.setuptools.package-data]` 中
    `harness_workflow` patterns 模拟 setuptools include_package_data 的 glob
    匹配语义，得到"实际会被打入 wheel 的 mirror 文件集合"，与 dev 端 mirror 文件
    全集做对比。

    current 状态（chg-08 STEP-1 红）：pyproject 用 14 行细分 patterns 漏装多类文件
    （reg-02 analysis.md 列出 7 类）。STEP-2 替换为
    `assets/scaffold_v2/.workflow/**/*` 全量 glob 后必绿（setuptools >= 69 支持 `**/*`）。

    R-F 提示：editable / src-import 模式下 `importlib.resources.files()` 命中 src/
    与 dev 同源恒 PASS，无法暴露 packaging 漏装；本测试改读 pyproject patterns 直接
    模拟匹配语义，editable 与真 wheel 下行为一致。
    """
    dev = _dev_mirror_relative_files()
    packaged = _packaged_mirror_relative_files()
    missing = sorted(dev - packaged)
    extra = sorted(packaged - dev)
    assert dev == packaged, (
        f"\nscaffold_v2 mirror 打包不完整：\n"
        f"  漏装（dev 有 / pyproject patterns 不匹配）{len(missing)} 个：\n    "
        + "\n    ".join(missing[:30])
        + (f"\n    ...(共 {len(missing)} 个)" if len(missing) > 30 else "")
        + f"\n  误装（pyproject patterns 匹配 / dev 无）{len(extra)} 个：\n    "
        + "\n    ".join(extra[:10])
        + (f"\n    ...(共 {len(extra)} 个)" if len(extra) > 10 else "")
    )


def test_dev_mirror_no_runtime_artifacts() -> None:
    """回归保护：dev 端 mirror 树不得包含运行时态产物。

    chg-03（历史漂移 reconcile：live ↔ scaffold_v2 mirror）已 reconcile，本测试
    锁死禁止再混入 sessions / feedback / bugfixes / requirements / flow/archive
    / flow/requirements / flow/suggestions / .DS_Store / __pycache__ / .pyc。

    说明：`state/runtime.yaml` 与 `state/action-log.md` 在 mirror 中作为 install
    bootstrap 的**初始空模板**保留（reg-01 analysis.md §2.4 白名单 = 不同步，但
    首次 install 必须有空模板做 bootstrap），不是 runtime 污染，本测试豁免。
    """
    dev = _dev_mirror_relative_files()
    forbidden_substrings = [
        "state/sessions/",
        "state/feedback/",
        "state/bugfixes/",
        "state/requirements/",
        "flow/archive/",
        "flow/requirements/",
        "flow/suggestions/",
        ".DS_Store",
        "__pycache__",
        ".pyc",
    ]
    violations: list[tuple[str, str]] = []
    for rel in sorted(dev):
        for sub in forbidden_substrings:
            if sub in rel:
                violations.append((rel, sub))
                break
    assert not violations, (
        f"\ndev 端 scaffold_v2 mirror 含运行时态污染（共 {len(violations)} 条）：\n"
        + "\n".join(f"  {rel}  ← 命中 {sub}" for rel, sub in violations[:20])
        + (f"\n  ...(共 {len(violations)} 条)" if len(violations) > 20 else "")
    )
