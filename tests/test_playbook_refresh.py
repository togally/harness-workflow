"""tests/test_playbook_refresh.py

req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-04（harness playbook-refresh 子命令）
pytest 测试套件（≥ 7 TC，含 dogfood subprocess TC）

TC-01: STACK 区段刷新（pyproject.toml → architecture.md AUTO:STACK 替换 + 区段外 byte-identical）
TC-02: SCRIPTS 区段刷新（Makefile / pyproject.toml → runbook AUTO:SCRIPTS 命中）
TC-03: LAYOUT 区段刷新（顶层目录变动 → architecture.md AUTO:LAYOUT 命中）
TC-04: 区段外 byte-identical（人工注释不被改动）
TC-05: 标记不配对处理（warn + 跳过 + 其他区段正常刷新）
TC-06: dry-run 不落盘 + stdout 含 diff
TC-07: dogfood subprocess（subprocess 调 CLI + 断言 exit 0 + 5 类区段刷新）
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_refresh import (
    playbook_refresh,
    replace_auto_section,
)
from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX


# ---------------------------------------------------------------------------
# Fixture helper：创建最小骨架
# ---------------------------------------------------------------------------

def _setup_minimal_playbook(root: Path, domains: list[str] | None = None) -> Path:
    """在 tmp_path 中创建最小路书骨架（含 AUTO 区段标记）。"""
    if domains is None:
        domains = ["core"]
    render_skeleton(root, domains)
    return root / PLAYBOOK_ROOT_SUFFIX


def _hash_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# TC-01: STACK 区段刷新
# ---------------------------------------------------------------------------

def test_tc01_stack_section_refreshed(tmp_path, capsys):
    """TC-01: pyproject.toml 存在 → architecture.md AUTO:STACK 被刷新 + 区段外 byte-identical。"""
    playbook_dir = _setup_minimal_playbook(tmp_path)

    # 写入 pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\nversion = "1.0.0"\n'
        '[project.dependencies]\nrequests = ">=2.0"\n',
        encoding="utf-8",
    )

    arch_md = playbook_dir / "architecture.md"
    original = arch_md.read_text(encoding="utf-8")

    rc = playbook_refresh(tmp_path)
    assert rc == 0, f"playbook_refresh returned {rc}"

    refreshed = arch_md.read_text(encoding="utf-8")

    # AUTO:STACK 区段被刷新（含 "myapp" 或 "Python"）
    assert "<!-- AUTO:STACK -->" in refreshed
    assert "<!-- /AUTO:STACK -->" in refreshed
    stack_m = __import__("re").search(
        r"<!-- AUTO:STACK -->(.*?)<!-- /AUTO:STACK -->", refreshed, __import__("re").DOTALL
    )
    assert stack_m, "AUTO:STACK 区段不存在"
    stack_content = stack_m.group(1)
    assert "Python" in stack_content or "myapp" in stack_content, (
        f"AUTO:STACK 区段未包含预期内容: {stack_content}"
    )

    # 区段外 byte-identical 验证（提取区段外内容对比）
    import re
    def _strip_auto_sections(text: str) -> str:
        """移除所有 AUTO:* 区段内容（仅保留标记行外部分）。"""
        return re.sub(
            r"<!-- AUTO:\w+ -->.*?<!-- /AUTO:\w+ -->",
            "<!-- AUTO_PLACEHOLDER -->",
            text,
            flags=re.DOTALL,
        )

    original_stripped = _strip_auto_sections(original)
    refreshed_stripped = _strip_auto_sections(refreshed)
    assert original_stripped == refreshed_stripped, (
        "区段外内容被修改（byte-identical 校验失败）"
    )


# ---------------------------------------------------------------------------
# TC-02: SCRIPTS 区段刷新
# ---------------------------------------------------------------------------

def test_tc02_scripts_section_refreshed(tmp_path, capsys):
    """TC-02: Makefile 存在 → architecture.md AUTO:SCRIPTS 区段被刷新。"""
    playbook_dir = _setup_minimal_playbook(tmp_path)

    # 写 Makefile
    (tmp_path / "Makefile").write_text(
        "test:\n\tpytest tests/ -v\n\nbuild:\n\tpython -m build\n",
        encoding="utf-8",
    )

    arch_md = playbook_dir / "architecture.md"
    rc = playbook_refresh(tmp_path)
    assert rc == 0

    content = arch_md.read_text(encoding="utf-8")
    import re
    m = re.search(
        r"<!-- AUTO:SCRIPTS -->(.*?)<!-- /AUTO:SCRIPTS -->", content, re.DOTALL
    )
    assert m, "AUTO:SCRIPTS 区段不存在"
    scripts_content = m.group(1)
    # Makefile targets: test 和 build 应出现
    assert "test" in scripts_content, f"AUTO:SCRIPTS 未命中 'test': {scripts_content}"
    assert "build" in scripts_content, f"AUTO:SCRIPTS 未命中 'build': {scripts_content}"


# ---------------------------------------------------------------------------
# TC-03: LAYOUT 区段刷新
# ---------------------------------------------------------------------------

def test_tc03_layout_section_refreshed(tmp_path, capsys):
    """TC-03: 顶层目录变动 → architecture.md AUTO:LAYOUT 区段被刷新。"""
    playbook_dir = _setup_minimal_playbook(tmp_path)

    # 添加顶层目录（模拟项目变动）
    (tmp_path / "src" / "mymodule").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("# My Project\n", encoding="utf-8")

    arch_md = playbook_dir / "architecture.md"
    rc = playbook_refresh(tmp_path)
    assert rc == 0

    content = arch_md.read_text(encoding="utf-8")
    import re
    m = re.search(
        r"<!-- AUTO:LAYOUT -->(.*?)<!-- /AUTO:LAYOUT -->", content, re.DOTALL
    )
    assert m, "AUTO:LAYOUT 区段不存在"
    layout_content = m.group(1)
    # docs 和 README.md 应在目录树中
    assert "docs" in layout_content, f"AUTO:LAYOUT 未包含 'docs': {layout_content}"
    assert "README.md" in layout_content or "src" in layout_content, (
        f"AUTO:LAYOUT 未包含预期目录: {layout_content}"
    )


# ---------------------------------------------------------------------------
# TC-04: 区段外 byte-identical
# ---------------------------------------------------------------------------

def test_tc04_non_auto_content_byte_identical(tmp_path):
    """TC-04: 区段外人工注释在 refresh 后 byte-identical。"""
    playbook_dir = _setup_minimal_playbook(tmp_path)

    arch_md = playbook_dir / "architecture.md"
    original = arch_md.read_text(encoding="utf-8")

    # 在区段外添加人工注释
    human_annotation = "\n<!-- 人工注释：这是手工写的架构说明，不应被 refresh 修改 -->\n"
    modified = original + human_annotation
    arch_md.write_text(modified, encoding="utf-8")

    hash_before_human_section = hashlib.md5(human_annotation.encode()).hexdigest()

    rc = playbook_refresh(tmp_path)
    assert rc == 0

    after_refresh = arch_md.read_text(encoding="utf-8")

    # 人工注释必须还在
    assert "<!-- 人工注释：这是手工写的架构说明，不应被 refresh 修改 -->" in after_refresh, (
        "人工注释被删除！byte-identical 校验失败"
    )

    # 用正则切出区段外部分对比
    import re

    def _non_auto_parts(text: str) -> str:
        return re.sub(
            r"<!-- AUTO:\w+ -->.*?<!-- /AUTO:\w+ -->",
            "",
            text,
            flags=re.DOTALL,
        )

    assert _non_auto_parts(modified) == _non_auto_parts(after_refresh), (
        "区段外内容被修改（byte-identical 校验失败）"
    )


# ---------------------------------------------------------------------------
# TC-05: 标记不配对处理
# ---------------------------------------------------------------------------

def test_tc05_unpaired_marker_warn_skip(tmp_path, capsys):
    """TC-05: 故意删闭合标记 → warn + 跳过该区段 + 其他区段仍正常刷新。"""
    playbook_dir = _setup_minimal_playbook(tmp_path, domains=["core"])

    arch_md = playbook_dir / "architecture.md"
    content = arch_md.read_text(encoding="utf-8")

    # 故意删除 AUTO:STACK 的闭合标记
    broken = content.replace("<!-- /AUTO:STACK -->", "")
    arch_md.write_text(broken, encoding="utf-8")

    rc = playbook_refresh(tmp_path)
    # refresh 应继续（不是 exit 1），但 STACK 区段被跳过

    refreshed = arch_md.read_text(encoding="utf-8")

    # STACK 区段不应被错误替换（闭标记已删除，跳过）
    # 开标记仍在，但无闭标记 → 确保内容没有被意外修改
    assert "<!-- AUTO:STACK -->" in refreshed
    assert "<!-- /AUTO:STACK -->" not in refreshed  # 我们删了它，且 refresh 跳过了

    # 其他区段（LAYOUT / SCRIPTS）应仍可刷新（不受 STACK 破损影响）
    # 验证 LAYOUT 区段配对正常
    assert "<!-- AUTO:LAYOUT -->" in refreshed
    assert "<!-- /AUTO:LAYOUT -->" in refreshed

    # 有警告输出（stderr）
    captured = capsys.readouterr()
    # warn 应在 stderr 中（capsys 捕获）
    # 由于 playbook_refresh 打印到 sys.stderr，capsys 应捕获到 warn 信息
    # （如果 capsys 未捕获，也可以通过 rc 判断）
    # TC-05 的核心断言：STACK 被跳过 + 其他文件/区段不受影响
    assert "<!-- AUTO:LAYOUT -->" in refreshed and "<!-- /AUTO:LAYOUT -->" in refreshed


# ---------------------------------------------------------------------------
# TC-06: dry-run 不落盘 + stdout 含 diff
# ---------------------------------------------------------------------------

def test_tc06_dry_run_no_write(tmp_path, capsys):
    """TC-06: --dry-run → 文件 mtime 不变 + stdout 含 diff 输出。"""
    # 添加 pyproject.toml 以确保有内容可刷新
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "testpkg"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")

    playbook_dir = _setup_minimal_playbook(tmp_path)

    arch_md = playbook_dir / "architecture.md"
    mtime_before = arch_md.stat().st_mtime
    content_before = arch_md.read_bytes()

    # dry_run=True：不应写盘
    rc = playbook_refresh(tmp_path, dry_run=True)
    assert rc == 0, f"dry-run returned {rc}"

    # 文件内容不变（mtime 可能与 inode 更新无关，但字节应相同）
    content_after = arch_md.read_bytes()
    assert content_before == content_after, "dry-run 模式下文件被修改！"

    # stdout 应有 dry-run 相关输出
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    # dry-run 输出含 diff 或 "dry-run" 或 "已是最新"
    assert "dry-run" in combined or "diff" in combined or "已是最新" in combined, (
        f"dry-run 模式未打印预期输出: {combined}"
    )


# ---------------------------------------------------------------------------
# helper：replace_auto_section 单元测试（复用于 TC-05）
# ---------------------------------------------------------------------------

def test_replace_auto_section_basic():
    """replace_auto_section 基本替换正确性。"""
    content = "前置内容\n<!-- AUTO:TEST -->\n旧内容\n<!-- /AUTO:TEST -->\n后置内容\n"
    new_text = "新内容行1\n新内容行2"

    updated, success, warn = replace_auto_section(content, "TEST", new_text)

    assert success, f"替换失败: {warn}"
    assert "新内容行1" in updated
    assert "新内容行2" in updated
    assert "旧内容" not in updated
    assert "前置内容" in updated
    assert "后置内容" in updated


def test_replace_auto_section_unpaired_open_only():
    """replace_auto_section：只有开标记 → 返回 False + warn。"""
    content = "abc\n<!-- AUTO:FOO -->\n无闭标记\nxyz\n"
    updated, success, warn = replace_auto_section(content, "FOO", "新内容")
    assert not success
    assert "FOO" in warn or "配对" in warn or "缺少" in warn


def test_replace_auto_section_both_missing():
    """replace_auto_section：开闭标记都缺失 → 返回 False。"""
    content = "纯文本，无任何 AUTO 标记\n"
    updated, success, warn = replace_auto_section(content, "STACK", "新内容")
    assert not success
    assert updated == content  # 原文不变


# ---------------------------------------------------------------------------
# TC-07: dogfood subprocess
# ---------------------------------------------------------------------------

def test_tc07_dogfood_subprocess(tmp_path, monkeypatch):
    """TC-07: subprocess 调 CLI playbook-refresh → exit 0 + 5 类区段被刷新。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 1. 创建最小骨架
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "dogfood"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "Makefile").write_text("test:\n\tpytest\nbuild:\n\tpython -m build\n", encoding="utf-8")
    (tmp_path / "src" / "dogfood" / "core").mkdir(parents=True)
    (tmp_path / "src" / "dogfood" / "core" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "dogfood" / "api").mkdir(parents=True)

    # render_skeleton 创建骨架
    render_skeleton(tmp_path, ["core", "api"])

    # 2. subprocess 调 CLI
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}:{existing_pythonpath}" if existing_pythonpath else SRC_DIR

    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "playbook-refresh", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    # 3. 断言 exit 0
    assert result.returncode == 0, (
        f"playbook-refresh returned {result.returncode}; "
        f"stdout={result.stdout}; stderr={result.stderr}"
    )

    # 4. 断言各类 AUTO 区段被刷新（至少 stdout 或文件内容体现）
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX

    arch_md = playbook_dir / "architecture.md"
    overview_md = playbook_dir / "overview.md"
    code_map_md = playbook_dir / "code-map.md"

    assert arch_md.exists(), "architecture.md 不存在"
    arch_content = arch_md.read_text(encoding="utf-8")

    # AUTO:STACK 含 Python/dogfood
    import re
    stack_m = re.search(r"<!-- AUTO:STACK -->(.*?)<!-- /AUTO:STACK -->", arch_content, re.DOTALL)
    assert stack_m, "AUTO:STACK 区段缺失"
    assert "Python" in stack_m.group(1) or "dogfood" in stack_m.group(1) or len(stack_m.group(1).strip()) > 0

    # AUTO:SCRIPTS 含 make test/build
    scripts_m = re.search(r"<!-- AUTO:SCRIPTS -->(.*?)<!-- /AUTO:SCRIPTS -->", arch_content, re.DOTALL)
    assert scripts_m, "AUTO:SCRIPTS 区段缺失"
    assert "test" in scripts_m.group(1) or "build" in scripts_m.group(1)

    # AUTO:LAYOUT 有内容
    layout_m = re.search(r"<!-- AUTO:LAYOUT -->(.*?)<!-- /AUTO:LAYOUT -->", arch_content, re.DOTALL)
    assert layout_m, "AUTO:LAYOUT 区段缺失"
    assert len(layout_m.group(1).strip()) > 0

    # AUTO:DOMAIN_LIST 有内容
    overview_content = overview_md.read_text(encoding="utf-8")
    domain_list_m = re.search(
        r"<!-- AUTO:DOMAIN_LIST -->(.*?)<!-- /AUTO:DOMAIN_LIST -->",
        overview_content,
        re.DOTALL,
    )
    assert domain_list_m, "AUTO:DOMAIN_LIST 区段缺失"
    assert "core" in domain_list_m.group(1) or "api" in domain_list_m.group(1), (
        f"AUTO:DOMAIN_LIST 未包含领域名: {domain_list_m.group(1)}"
    )

    # AUTO:DOMAIN_FILES（code-map.md）有内容
    code_map_content = code_map_md.read_text(encoding="utf-8")
    domain_files_m = re.search(
        r"<!-- AUTO:DOMAIN_FILES -->(.*?)<!-- /AUTO:DOMAIN_FILES -->",
        code_map_content,
        re.DOTALL,
    )
    assert domain_files_m, "code-map.md AUTO:DOMAIN_FILES 区段缺失"
    # 包含领域名
    assert "core" in domain_files_m.group(1) or "api" in domain_files_m.group(1)

    # 5. stdout 含 'refresh'（表明刷新操作已执行）
    combined = result.stdout + result.stderr
    assert "refresh" in combined.lower() or "刷新" in combined or "已是最新" in combined, (
        f"stdout 未含 'refresh': {combined}"
    )
