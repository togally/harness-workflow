"""req-52 / chg-02：src 硬编码 main 反例 lint，防回归。

用例：
- TC-01-grep-main-literal：grep src 全树 '"main"' 字面值，命中数 ≤ 白名单
- TC-02-path-join-main：grep src 全树 '/ "main" /' Path 拼接形态，命中数 = 0
- TC-03-artifacts-main-prefix：grep src 全树 '"artifacts/main/' 前缀，命中数 = 0
- TC-04-whitelist-exemption：白名单豁免单测（ff_auto.py + _get_git_branch fallback 形态被豁免）
"""
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "harness_workflow"

# 白名单：以下 grep 命中行被豁免（合理的 fallback 默认值 / 非路径用途，非硬编码 main 路径）
_HARDCODE_MAIN_WHITELIST_PATTERNS = [
    re.compile(r'_get_git_branch\([^)]*\)\s*or\s*"main"'),  # 标准 fallback 形式
    re.compile(r'^\s*return\s*"main"\s*$'),                  # ff_auto.py:210 fallback 函数
    re.compile(r'current_branch.*:\s*str\s*=\s*"main"'),     # 函数参数默认值（非路径）
    re.compile(r'\.get\(\s*"main"\s*\)'),                    # dict.get("main")（JSON key，非路径）
    re.compile(r'"agent".*"main"'),                          # agent 标识符（非路径）
    re.compile(r'source\s*=\s*"main"'),                      # _parse_index_md source="main"（标记符，非路径）
    re.compile(r'source\s*∈\s*"main"'),                      # docstring source ∈ "main" | "legacy"（说明，非路径）
    re.compile(r'∈\s*"main"'),                               # docstring ∈ "main" 模式（说明，非路径）
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
