"""req-52 / chg-03：项目级索引懒加载测试。

用例：
- TC-01-index-parsing：解析 index.md markdown 表，返回 4 字段
- TC-02-when-load-filter：when_load 过滤行为（always / on-stage:executing / on-keyword:foo）
- TC-03-fallback-main-path：主路径不存在时 fallback 到 legacy artifacts/{branch}/project/
- TC-04-empty-when-no-index：主路径 + legacy 均无 index.md 时返回 []（向后兼容）
- TC-05-skip-placeholder-row：跳过含 HTML 注释的占位行
"""
from pathlib import Path
import sys

import pytest

# Ensure harness_workflow src is importable regardless of install state
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import _load_project_level_index, _parse_index_md  # noqa: E402


def _write_index(target: Path, rows: list[dict]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "schema_version: 1",
        "scope: constraints",
        "---",
        "",
        "# 项目级 constraints 索引",
        "",
        "| path | title | scope | when_load | 备注 |",
        "|------|-------|-------|-----------|------|",
    ]
    for r in rows:
        lines.append(f"| {r['path']} | {r['title']} | {r['scope']} | {r['when_load']} | |")
    target.write_text("\n".join(lines), encoding="utf-8")


def test_index_parsing(tmp_path):
    """TC-01：解析 index.md 表格，返回 4 字段。"""
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    _write_index(idx, [
        {"path": "rule-a.md", "title": "项目独有规则 A", "scope": "constraints", "when_load": "always"},
        {"path": "rule-b.md", "title": "项目独有规则 B", "scope": "constraints", "when_load": "on-stage:executing"},
    ])
    rows = _load_project_level_index(tmp_path, "constraints")
    assert len(rows) == 2
    assert rows[0]["path"] == "rule-a.md"
    assert rows[0]["when_load"] == "always"
    assert rows[1]["when_load"] == "on-stage:executing"
    assert all(r["source"] == "main" for r in rows)


def test_when_load_filter(tmp_path):
    """TC-02：when_load 过滤行为（agent 调用方按 stage 自行 filter，本 helper 仅返回 list）。"""
    idx = tmp_path / "artifacts" / "project" / "experience" / "roles" / "index.md"
    _write_index(idx, [
        {"path": "x.md", "title": "x", "scope": "experience-roles", "when_load": "always"},
        {"path": "y.md", "title": "y", "scope": "experience-roles", "when_load": "on-stage:executing"},
        {"path": "z.md", "title": "z", "scope": "experience-roles", "when_load": "on-keyword:lint"},
    ])
    rows = _load_project_level_index(tmp_path, "experience-roles")
    assert len(rows) == 3
    when_loads = [r["when_load"] for r in rows]
    assert "always" in when_loads
    assert "on-stage:executing" in when_loads
    assert "on-keyword:lint" in when_loads


def test_fallback_main_to_legacy(tmp_path, monkeypatch):
    """TC-03：主路径不存在时 fallback 到 legacy artifacts/{branch}/project/。"""
    # 仅在 legacy 路径写 index.md
    legacy_idx = tmp_path / "artifacts" / "main" / "project" / "constraints" / "index.md"
    _write_index(legacy_idx, [
        {"path": "legacy-rule.md", "title": "legacy", "scope": "constraints", "when_load": "always"},
    ])
    # mock _get_git_branch -> "main"
    import harness_workflow.workflow_helpers as wh
    monkeypatch.setattr(wh, "_get_git_branch", lambda root: "main")
    rows = _load_project_level_index(tmp_path, "constraints")
    assert len(rows) == 1
    assert rows[0]["path"] == "legacy-rule.md"
    assert rows[0]["source"] == "legacy"


def test_empty_when_no_index(tmp_path, monkeypatch):
    """TC-04：主路径 + legacy 均无 index.md 时返回 []。"""
    import harness_workflow.workflow_helpers as wh
    monkeypatch.setattr(wh, "_get_git_branch", lambda root: "main")
    rows = _load_project_level_index(tmp_path, "constraints")
    assert rows == []


def test_skip_placeholder_row(tmp_path):
    """TC-05：跳过含 HTML 注释的占位行（与本 chg index.md 模板内置示例行匹配）。"""
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        "---\nscope: constraints\n---\n\n"
        "| path | title | scope | when_load | 备注 |\n"
        "|------|-------|-------|-----------|------|\n"
        "| <!-- 示例：my-rule.md --> | <!-- 示例 --> | constraints | always | |\n"
        "| real-rule.md | real | constraints | always | |\n",
        encoding="utf-8",
    )
    rows = _load_project_level_index(tmp_path, "constraints")
    assert len(rows) == 1
    assert rows[0]["path"] == "real-rule.md"
