"""req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）
/ chg-04（ProjectProfile.mcp_project_ids 多 provider map）

pytest 用例：roundtrip / unset placeholder / legacy missing section。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from harness_workflow.project_scanner import (
    ProjectProfile,
    load_project_profile,
    render_project_profile,
)


# ---------------------------------------------------------------------------
# 工具函数：render → 写临时文件 → load
# ---------------------------------------------------------------------------


def _render_and_load(profile: ProjectProfile) -> ProjectProfile:
    """Helper: render profile to temp file, then load it back."""
    text = render_project_profile(profile, now=lambda: __import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc))
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as f:
        f.write(text)
        tmp_path = Path(f.name)
    try:
        loaded = load_project_profile(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return loaded


# ---------------------------------------------------------------------------
# test_project_profile_mcp_project_ids_roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mcp_project_ids",
    [
        pytest.param({}, id="empty_dict"),
        pytest.param({"apifox": "abc123"}, id="single_provider"),
        pytest.param({"apifox": "abc", "postman": "xyz"}, id="multi_provider"),
    ],
)
def test_project_profile_mcp_project_ids_roundtrip(mcp_project_ids: dict[str, str]) -> None:
    """render → load → mcp_project_ids 反射一致（roundtrip 恒等）。"""
    profile = ProjectProfile(mcp_project_ids=mcp_project_ids)
    loaded = _render_and_load(profile)

    assert loaded is not None
    assert loaded.mcp_project_ids == mcp_project_ids, (
        f"roundtrip mismatch: expected={mcp_project_ids!r}, got={loaded.mcp_project_ids!r}"
    )
    # parse_errors 不应包含 mcp_project_ids 相关错误
    mcp_errors = [e for e in loaded.parse_errors if "mcp_project_ids" in e]
    assert not mcp_errors, f"unexpected parse_errors: {mcp_errors}"


# ---------------------------------------------------------------------------
# test_project_profile_mcp_project_ids_unset_placeholder
# ---------------------------------------------------------------------------


def test_project_profile_mcp_project_ids_unset_placeholder() -> None:
    """value 为空字符串 "" → render 输出 (unset) → load 回读为 ""。"""
    profile = ProjectProfile(mcp_project_ids={"apifox": ""})
    text = render_project_profile(
        profile,
        now=lambda: __import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc),
    )

    # render 输出应含 "(unset)" 字符串
    assert "apifox: (unset)" in text, f"expected 'apifox: (unset)' in rendered text:\n{text}"

    # load 后 mcp_project_ids["apifox"] 应为 ""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as f:
        f.write(text)
        tmp_path = Path(f.name)
    try:
        loaded = load_project_profile(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    assert loaded is not None
    assert loaded.mcp_project_ids.get("apifox", "MISSING") == "", (
        f"expected empty string, got: {loaded.mcp_project_ids.get('apifox', 'MISSING')!r}"
    )


# ---------------------------------------------------------------------------
# test_project_profile_mcp_project_ids_legacy_missing_section
# ---------------------------------------------------------------------------


def test_project_profile_mcp_project_ids_legacy_missing_section() -> None:
    """加载无 MCP 段的旧样本 → mcp_project_ids == {} + parse_errors 含条目，不抛异常。"""
    # 构造一个不含 MCP 段落的旧 profile 文本
    legacy_text = """\
---
generated_at: 2025-01-01T00:00:00+00:00
content_hash: abc123
schema: project-profile/v1
---
## 结构化字段

- package_name: old-project
- language: python
- project_headline: (unset)
- stack_tags:
  - python+pyproject
- deps_top:
  - (none)
- entrypoints:
  - (none)

## 项目用途（LLM 填充）

<!-- placeholder -->

## 项目规范（LLM 填充）

<!-- placeholder -->
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as f:
        f.write(legacy_text)
        tmp_path = Path(f.name)
    try:
        loaded = load_project_profile(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    assert loaded is not None, "load_project_profile should return a profile, not None"
    assert loaded.mcp_project_ids == {}, (
        f"expected empty dict for legacy profile, got: {loaded.mcp_project_ids!r}"
    )
    # parse_errors 应含 mcp_project_ids 相关条目
    mcp_errors = [e for e in loaded.parse_errors if "mcp_project_ids" in e]
    assert mcp_errors, (
        f"expected parse_errors entry about mcp_project_ids, got parse_errors={loaded.parse_errors!r}"
    )
