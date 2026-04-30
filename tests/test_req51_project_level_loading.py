"""req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并）dogfood 测试。

覆盖范围：
- TC-01-loading-protocol-step76-grep：role-loading-protocol.md 含 "Step 7.6：项目级覆盖加载" 段
- TC-02-tools-manager-step20-grep：tools-manager.md 含 "项目级合并" 段，明确路径
- TC-03-experience-override-by-name：项目级覆盖全局同名文件（analyst.md）
- TC-04-tools-keywords-merge：项目级覆盖全局同名 keywords.yaml
- TC-05-fallback-when-project-missing：项目级目录不存在时 fallback 全局
- TC-06-fallback-when-global-missing：全局目录不存在时仅返回项目级
- TC-07-mirror-byte-equal：live + mirror 字节比对 silent
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import _merge_project_level_files  # noqa: E402


def test_tc01_loading_protocol_step76_grep() -> None:
    """TC-01-loading-protocol-step76-grep：role-loading-protocol.md 含 Step 7.6 段落。
    AC-05（加载顺序与冲突解决）。
    优先级 P0。
    """
    rlp = REPO_ROOT / ".workflow" / "context" / "roles" / "role-loading-protocol.md"
    assert rlp.exists(), f"role-loading-protocol.md 不存在：{rlp}"
    text = rlp.read_text(encoding="utf-8")
    assert "Step 7.6：项目级覆盖加载" in text, "role-loading-protocol.md 缺少 Step 7.6 标题"
    # 含 artifacts/{branch}/project/ ≥ 2 命中
    count = text.count("artifacts/{branch}/project/")
    assert count >= 2, f"artifacts/{{branch}}/project/ 命中数 < 2：{count}"
    # 含 OQ-2 = A 和 OQ-3 = A 引用
    assert "OQ-2 = A" in text, "role-loading-protocol.md 缺 OQ-2 = A 引用"
    assert "OQ-3 = A" in text, "role-loading-protocol.md 缺 OQ-3 = A 引用"


def test_tc02_tools_manager_step20_grep() -> None:
    """TC-02-tools-manager-step20-grep：tools-manager.md 含项目级合并段。
    AC-06（工具项目级化）。
    优先级 P0。
    """
    tm = REPO_ROOT / ".workflow" / "context" / "roles" / "tools-manager.md"
    assert tm.exists(), f"tools-manager.md 不存在：{tm}"
    text = tm.read_text(encoding="utf-8")
    assert "项目级合并" in text, "tools-manager.md 缺少 '项目级合并' 标题"
    # req-52 / chg-02：路径从 artifacts/main/project/tools/ 迁移到 artifacts/project/tools/（主路径，无 branch）
    count = text.count("artifacts/project/tools/")
    assert count >= 4, f"artifacts/project/tools/ 命中数 < 4：{count}"
    # 含 OQ-2 = A 引用
    assert "OQ-2 = A" in text, "tools-manager.md 缺 OQ-2 = A 引用"


def test_tc03_experience_override_by_name(tmp_path: Path) -> None:
    """TC-03-experience-override-by-name：项目级覆盖全局同名 analyst.md。
    AC-05（加载顺序与冲突解决）。
    优先级 P0。
    """
    global_dir = tmp_path / ".workflow" / "context" / "experience" / "roles"
    project_dir = tmp_path / "artifacts" / "main" / "project" / "experience" / "roles"
    global_dir.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)

    (global_dir / "analyst.md").write_text("GLOBAL_VERSION", encoding="utf-8")
    (project_dir / "analyst.md").write_text("PROJECT_LOCAL_VERSION", encoding="utf-8")

    merged = _merge_project_level_files(global_dir, project_dir)
    assert "analyst.md" in merged, "merged dict 应含 analyst.md"
    # 项目级覆盖全局：merged["analyst.md"] 指向项目级路径
    assert "artifacts/main/project" in merged["analyst.md"].as_posix(), (
        f"merged analyst.md 未指向项目级路径：{merged['analyst.md']}"
    )
    assert merged["analyst.md"].read_text(encoding="utf-8") == "PROJECT_LOCAL_VERSION", (
        "项目级覆盖失败：应读到 PROJECT_LOCAL_VERSION"
    )


def test_tc04_tools_keywords_merge(tmp_path: Path) -> None:
    """TC-04-tools-keywords-merge：项目级覆盖全局同名 keywords.yaml。
    AC-06（工具项目级化）。
    优先级 P0。
    """
    global_dir = tmp_path / ".workflow" / "tools" / "index"
    project_dir = tmp_path / "artifacts" / "main" / "project" / "tools" / "index"
    global_dir.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)

    (global_dir / "keywords.yaml").write_text(
        "global-tool:\n  keywords: [k1, k2]\n", encoding="utf-8"
    )
    (project_dir / "keywords.yaml").write_text(
        "global-tool:\n  keywords: [k1-overridden]\nproject-tool:\n  keywords: [k3]\n",
        encoding="utf-8",
    )

    merged = _merge_project_level_files(global_dir, project_dir)
    assert "keywords.yaml" in merged, "merged dict 应含 keywords.yaml"
    # 项目级覆盖：merged["keywords.yaml"] 指向项目级
    assert "artifacts/main/project" in merged["keywords.yaml"].as_posix(), (
        f"merged keywords.yaml 未指向项目级路径：{merged['keywords.yaml']}"
    )


def test_tc05_fallback_when_project_missing(tmp_path: Path) -> None:
    """TC-05-fallback-when-project-missing：项目级目录不存在时 fallback 全局，不报错。
    AC-05（fallback）。
    优先级 P0。
    """
    global_dir = tmp_path / ".workflow" / "context" / "experience" / "roles"
    project_dir = tmp_path / "artifacts" / "main" / "project" / "experience" / "roles"
    global_dir.mkdir(parents=True, exist_ok=True)
    # 不创建 project_dir

    (global_dir / "analyst.md").write_text("GLOBAL_ONLY", encoding="utf-8")

    merged = _merge_project_level_files(global_dir, project_dir)
    assert "analyst.md" in merged, "全局 analyst.md 应在 merged dict 中"
    assert merged["analyst.md"].read_text(encoding="utf-8") == "GLOBAL_ONLY", (
        "fallback 失败：应读到 GLOBAL_ONLY"
    )
    # 无 KeyError 不报错 → 通过无异常即可


def test_tc06_fallback_when_global_missing(tmp_path: Path) -> None:
    """TC-06-fallback-when-global-missing：全局目录不存在时仅返回项目级，不报错。
    AC-05（fallback）。
    优先级 P1。
    """
    global_dir = tmp_path / ".workflow" / "context" / "experience" / "roles"
    project_dir = tmp_path / "artifacts" / "main" / "project" / "experience" / "roles"
    project_dir.mkdir(parents=True, exist_ok=True)
    # 不创建 global_dir

    (project_dir / "custom.md").write_text("PROJECT_ONLY", encoding="utf-8")

    merged = _merge_project_level_files(global_dir, project_dir)
    assert "custom.md" in merged, "项目级 custom.md 应在 merged dict 中"
    assert merged["custom.md"].read_text(encoding="utf-8") == "PROJECT_ONLY", (
        "fallback 失败：应读到 PROJECT_ONLY"
    )


def test_tc07_mirror_byte_equal() -> None:
    """TC-07-mirror-byte-equal：live + mirror 字节比对 silent（diff -q）。
    AC-04（mirror 同步）。
    优先级 P0。
    """
    live_rlp = REPO_ROOT / ".workflow" / "context" / "roles" / "role-loading-protocol.md"
    mirror_rlp = (
        REPO_ROOT
        / "src"
        / "harness_workflow"
        / "assets"
        / "scaffold_v2"
        / ".workflow"
        / "context"
        / "roles"
        / "role-loading-protocol.md"
    )
    live_tm = REPO_ROOT / ".workflow" / "context" / "roles" / "tools-manager.md"
    mirror_tm = (
        REPO_ROOT
        / "src"
        / "harness_workflow"
        / "assets"
        / "scaffold_v2"
        / ".workflow"
        / "context"
        / "roles"
        / "tools-manager.md"
    )

    assert live_rlp.read_text(encoding="utf-8") == mirror_rlp.read_text(encoding="utf-8"), (
        f"role-loading-protocol.md live vs mirror 不一致"
    )
    assert live_tm.read_text(encoding="utf-8") == mirror_tm.read_text(encoding="utf-8"), (
        f"tools-manager.md live vs mirror 不一致"
    )
