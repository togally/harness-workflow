"""tests/test_workspace_mode.py

req-57（多项目工作区路书 + .workflow 本地化）/ chg-01 + chg-02 + chg-03 + chg-04 测试

TC-01 detect_workspace_subprojects 命中：root 无项目文件 + ≥2 子目录各有项目文件
TC-02 detect_workspace_subprojects 不命中：root 自身有 pom.xml（单项目仓兼容）
TC-03 detect_workspace_subprojects 不命中：只 1 个子目录有项目文件
TC-04 WorkspaceDetector 通过 infer_domains 主路由命中 priority=5 先于 MavenMultiModule
TC-05 _scan_stack 在 workspace 模式下输出 ### {dir} ({stack-label}) 多段
TC-06 _scan_layout 在 workspace 模式下路径含 sub-project 前缀
TC-07 _scan_scripts 在 workspace 模式下按 sub-project 分段
TC-08 _scan_domain_files workspace 模式扫整个 sub-project + 200 文件上限截断
TC-09 _ensure_workflow_dir_ignored 三态边界：无 / 精确含 / 模糊含 / legacy negation
TC-10 单项目仓 1.0.0 行为兼容：_scan_stack/_scan_layout 不分段
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.playbook.domain_inference import (
    detect_workspace_subprojects,
    infer_domains,
    WorkspaceDetector,
)
from harness_workflow.tools.harness_playbook_refresh import (
    _scan_stack,
    _scan_layout,
    _scan_scripts,
    _scan_domain_files,
)
from harness_workflow.workflow_helpers import _ensure_workflow_dir_ignored


def _make_workspace(tmp: Path, layout: dict[str, dict[str, str]]) -> Path:
    """搭建多项目 workspace。layout = {sub_project_name: {file_name: content}}。"""
    for sub_name, files in layout.items():
        sub_dir = tmp / sub_name
        sub_dir.mkdir(parents=True, exist_ok=True)
        for fname, content in files.items():
            (sub_dir / fname).write_text(content, encoding="utf-8")
    return tmp


# ---------------------------------------------------------------------------
# TC-01: detect_workspace_subprojects 命中
# ---------------------------------------------------------------------------
def test_tc01_detect_workspace_hits_multi_subprojects(tmp_path):
    _make_workspace(tmp_path, {
        "frontend-admin": {"package.json": '{"name":"admin"}'},
        "backend-api": {"pom.xml": "<project><artifactId>api</artifactId></project>"},
    })
    result = detect_workspace_subprojects(tmp_path)
    assert result == ["backend-api", "frontend-admin"]


# ---------------------------------------------------------------------------
# TC-02: 单项目仓兼容（root 自身有 pom.xml）
# ---------------------------------------------------------------------------
def test_tc02_detect_skipped_when_root_is_single_project(tmp_path):
    (tmp_path / "pom.xml").write_text("<project></project>")
    (tmp_path / "module-a").mkdir()
    (tmp_path / "module-a" / "pom.xml").write_text("<project></project>")
    result = detect_workspace_subprojects(tmp_path)
    assert result == [], "root 自有 pom.xml 时不应识别为 workspace"


# ---------------------------------------------------------------------------
# TC-03: 单 sub-project 不命中（≥2 是触发条件）
# ---------------------------------------------------------------------------
def test_tc03_detect_skipped_with_only_one_subproject(tmp_path):
    _make_workspace(tmp_path, {
        "lonely": {"package.json": '{"name":"only-one"}'},
    })
    result = detect_workspace_subprojects(tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# TC-04: WorkspaceDetector 主路由命中 priority=5
# ---------------------------------------------------------------------------
def test_tc04_workspace_detector_priority_above_maven(tmp_path):
    _make_workspace(tmp_path, {
        "svc-a": {"pom.xml": "<project></project>"},
        "svc-b": {"pom.xml": "<project></project>"},
    })
    mode, domains = infer_domains(tmp_path)
    assert mode == "workspace"
    assert sorted(domains) == ["svc-a", "svc-b"]
    assert WorkspaceDetector().priority < 10  # 先于 MavenMultiModule


# ---------------------------------------------------------------------------
# TC-05: _scan_stack workspace 多段含 stack-label
# ---------------------------------------------------------------------------
def test_tc05_scan_stack_multisection_with_label(tmp_path):
    _make_workspace(tmp_path, {
        "vue-app": {"package.json": '{"name":"app","dependencies":{"vue":"^3"}}'},
        "java-svc": {"pom.xml": "<project><artifactId>svc</artifactId></project>"},
    })
    out = _scan_stack(tmp_path)
    assert "### vue-app (Node/Vue)" in out
    assert "### java-svc (Java/Maven)" in out
    assert "Node.js: app" in out
    assert "Java/Maven: svc" in out


# ---------------------------------------------------------------------------
# TC-06: _scan_layout workspace 路径前缀
# ---------------------------------------------------------------------------
def test_tc06_scan_layout_with_subproject_prefix(tmp_path):
    _make_workspace(tmp_path, {
        "frontend": {"package.json": '{"name":"f"}', "vite.config.ts": "//"},
        "backend": {"pom.xml": "<project></project>"},
    })
    (tmp_path / "frontend" / "src").mkdir()
    (tmp_path / "frontend" / "src" / "main.ts").write_text("//")
    (tmp_path / "backend" / "src").mkdir()

    out = _scan_layout(tmp_path)
    assert "### frontend" in out
    assert "### backend" in out
    assert "`frontend/src/`" in out
    assert "`backend/src/`" in out


# ---------------------------------------------------------------------------
# TC-07: _scan_scripts workspace 分段
# ---------------------------------------------------------------------------
def test_tc07_scan_scripts_per_subproject(tmp_path):
    _make_workspace(tmp_path, {
        "fe": {"package.json": '{"name":"fe","scripts":{"dev":"vite","build":"vite build"}}'},
        "be": {"pom.xml": "<project></project>"},
    })
    out = _scan_scripts(tmp_path)
    assert "### fe" in out
    assert "### be" in out
    assert "npm run dev" in out
    assert "mvn clean install" in out


# ---------------------------------------------------------------------------
# TC-08: _scan_domain_files workspace 200 上限
# ---------------------------------------------------------------------------
def test_tc08_scan_domain_files_workspace_truncates(tmp_path):
    _make_workspace(tmp_path, {
        "huge": {"pom.xml": "<project></project>"},
        "small": {"pom.xml": "<project></project>"},
    })
    huge_src = tmp_path / "huge" / "src"
    huge_src.mkdir(parents=True)
    for i in range(250):
        (huge_src / f"File{i}.java").write_text("class A{}")

    out = _scan_domain_files(tmp_path / "artifacts/playbooks/domains/huge", tmp_path, "huge")
    lines = out.split("\n")
    assert len(lines) == 201, f"应截断到 200 + 1 提示行，实际 {len(lines)}"
    assert "还有 50 个代码文件未列出" in lines[-1]


# ---------------------------------------------------------------------------
# TC-09: _ensure_workflow_dir_ignored 三态边界
# ---------------------------------------------------------------------------
class TestGitignoreReversal:
    def test_no_gitignore_creates_new(self, tmp_path):
        _ensure_workflow_dir_ignored(tmp_path)
        content = (tmp_path / ".gitignore").read_text()
        assert ".workflow/" in content

    def test_exact_match_skips_silently(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("__pycache__/\n.workflow/\n")
        before = gi.read_text()
        _ensure_workflow_dir_ignored(tmp_path)
        assert gi.read_text() == before, "幂等：精确含 .workflow/ 时不应改动"

    def test_legacy_negation_removed_and_appended(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("__pycache__/\n!.workflow/\n")
        _ensure_workflow_dir_ignored(tmp_path)
        result = gi.read_text()
        assert "!.workflow/" not in result, "legacy negation 应被清除"
        assert ".workflow/" in result

    def test_fuzzy_match_appends_with_warning(self, tmp_path, capsys):
        gi = tmp_path / ".gitignore"
        gi.write_text("__pycache__/\n.work*\n")
        _ensure_workflow_dir_ignored(tmp_path)
        result = gi.read_text()
        assert ".workflow/" in result
        captured = capsys.readouterr()
        assert "请检查冗余" in captured.err


# ---------------------------------------------------------------------------
# TC-10: 单项目仓 1.0.0 行为兼容（不分段）
# ---------------------------------------------------------------------------
def test_tc10_single_project_compat_no_sectioning(tmp_path):
    (tmp_path / "pom.xml").write_text(
        "<project><artifactId>my-app</artifactId></project>"
    )
    (tmp_path / "src").mkdir()
    out_stack = _scan_stack(tmp_path)
    out_layout = _scan_layout(tmp_path)
    # 不出现 ### 子标题（workspace mode 才有）
    assert "###" not in out_stack
    assert "###" not in out_layout
    assert "Java/Maven: my-app" in out_stack
