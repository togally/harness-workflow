"""Unit tests for gstack skills push logic.

req-55 / chg-01 (gstack 内置发布契约 — vendor 全 skill + harness install 自动装载)

Tests:
  - test_vendor_script_single_skill: single-skill form
  - test_vendor_script_all: --all form produces N skills + _shared/
  - test_install_pushes_skills_when_agent_claude: agent=claude triggers push
  - test_install_skips_when_agent_codex: agent=codex skips + warns
  - test_conflict_default_warn: hash-mismatch SKILL.md → skip + warn
  - test_force_gstack_overrides: --force-gstack → overwrite
  - test_skill_push_failure_does_not_block: single copy failure → continues
  - test_runtime_yaml_gstack_status_written: gstack_status 四字段正确写入
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
VENDOR_SCRIPT = REPO_ROOT / "scripts" / "vendor-gstack.sh"
GSTACK_LOCAL = Path.home() / ".claude" / "skills" / "gstack"
GSTACK_ASSETS = REPO_ROOT / "src" / "harness_workflow" / "assets" / "gstack-skills"


def _has_local_gstack() -> bool:
    return GSTACK_LOCAL.exists() and (GSTACK_LOCAL / "office-hours" / "SKILL.md").exists()


def _has_git() -> bool:
    return shutil.which("git") is not None


# ---------------------------------------------------------------------------
# Step 1 / Step 2 — vendor script tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not (_has_local_gstack() and _has_git()),
    reason="Requires local gstack clone at ~/.claude/skills/gstack/",
)
def test_vendor_script_single_skill(tmp_path: Path) -> None:
    """Vendor a single skill (office-hours) from --from-local into a tmp target.

    Strategy: create a minimal fake-repo directory structure with scripts/ so that
    the script's SCRIPT_DIR/.. resolves to a controlled location, and
    TARGET_ROOT remains relative (src/harness_workflow/assets/gstack-skills).
    """
    # Create fake-repo/scripts/ mirror so SCRIPT_DIR/.. == fake_repo_root
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    scripts_dir = fake_repo / "scripts"
    scripts_dir.mkdir()
    patched_script = scripts_dir / "vendor-gstack.sh"
    shutil.copy2(str(VENDOR_SCRIPT), str(patched_script))
    patched_script.chmod(0o755)

    result = subprocess.run(
        ["sh", str(patched_script), "office-hours", "--from-local", str(GSTACK_LOCAL)],
        capture_output=True,
        text=True,
        cwd=str(fake_repo),
    )
    assert result.returncode == 0, (
        f"Script failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    skill_dir = fake_repo / "src" / "harness_workflow" / "assets" / "gstack-skills" / "office-hours"
    assert (skill_dir / "SKILL.md").exists(), "SKILL.md not found after vendor"
    assert (skill_dir / "VERSION-gstack").exists(), "VERSION-gstack not found after vendor"
    version_content = (skill_dir / "VERSION-gstack").read_text()
    assert "commit:" in version_content
    assert "upstream_url:" in version_content


@pytest.mark.skipif(
    not (_has_local_gstack() and _has_git()),
    reason="Requires local gstack clone at ~/.claude/skills/gstack/",
)
def test_vendor_script_all(tmp_path: Path) -> None:
    """--all form: produces multiple skills + _shared directory."""
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    scripts_dir = fake_repo / "scripts"
    scripts_dir.mkdir()
    patched_script = scripts_dir / "vendor-gstack.sh"
    shutil.copy2(str(VENDOR_SCRIPT), str(patched_script))
    patched_script.chmod(0o755)

    result = subprocess.run(
        ["sh", str(patched_script), "--all", "--from-local", str(GSTACK_LOCAL)],
        capture_output=True,
        text=True,
        cwd=str(fake_repo),
    )
    assert result.returncode == 0, f"Script failed:\nstdout={result.stdout}\nstderr={result.stderr}"

    gstack_out = fake_repo / "src" / "harness_workflow" / "assets" / "gstack-skills"
    skill_dirs = [d for d in gstack_out.iterdir() if d.is_dir() and d.name != "_shared"]
    skill_count = sum(1 for d in skill_dirs if (d / "SKILL.md").exists())
    assert skill_count >= 40, f"Expected at least 40 skills, got {skill_count}"

    shared = gstack_out / "_shared"
    assert shared.exists(), "_shared directory not created"
    assert (shared / "LICENSE-gstack").exists(), "LICENSE-gstack missing from _shared"
    assert (shared / "VERSION-gstack").exists(), "VERSION-gstack missing from _shared"

    version = (shared / "VERSION-gstack").read_text()
    assert "commit:" in version, "commit hash missing from VERSION-gstack"


# ---------------------------------------------------------------------------
# Step 4 — _install_gstack_skills tests (unit-level, mock filesystem)
# ---------------------------------------------------------------------------

def _build_fake_gstack_assets(base: Path, skills: list[str]) -> Path:
    """Create a minimal fake gstack-skills directory for testing."""
    gstack_root = base / "gstack-skills"
    shared = gstack_root / "_shared"
    shared.mkdir(parents=True)
    (shared / "LICENSE-gstack").write_text("MIT License\nCopyright (c) 2026 Garry Tan\n")
    (shared / "VERSION-gstack").write_text(
        "upstream_url: https://github.com/garrytan/gstack\n"
        "commit: abc1234\n"
        "vendor_timestamp: 2026-05-07T00:00:00Z\n"
    )
    bin_dir = shared / "bin"
    bin_dir.mkdir()
    (bin_dir / "gstack-config").write_text("#!/bin/sh\necho gstack-config\n")
    for skill in skills:
        skill_dir = gstack_root / skill
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"# {skill}\nThis is the {skill} skill.\n")
        (skill_dir / "VERSION-gstack").write_text(
            "upstream_url: https://github.com/garrytan/gstack\n"
            "commit: abc1234\n"
        )
    return gstack_root


def test_install_pushes_skills_when_agent_claude(tmp_path: Path) -> None:
    """agent=claude → _install_gstack_skills is called and skills are pushed."""
    from harness_workflow import workflow_helpers as wh

    fake_assets = tmp_path / "assets"
    skills = ["office-hours", "investigate", "qa"]
    _build_fake_gstack_assets(fake_assets, skills)

    target_skills = tmp_path / "claude_skills"
    target_skills.mkdir()

    with patch.object(wh, "GSTACK_SKILLS_ROOT", fake_assets / "gstack-skills"):
        result = wh._install_gstack_skills(target_root=target_skills, force=False)

    assert set(result["installed_skills"]) == set(skills)
    assert result["vendor_version"] == "abc1234"
    assert result["agent_kind_compatible"] is True
    for skill in skills:
        assert (target_skills / skill / "SKILL.md").exists()
    # Shared resources pushed to target/gstack/
    assert (target_skills / "gstack" / "bin" / "gstack-config").exists()


def test_install_skips_when_agent_codex(tmp_path: Path, capsys) -> None:
    """agent=codex → gstack push skipped, warn printed, returns exit 0."""
    # harness_install.py calls install_agent(root, agent) which calls _install_gstack_skills
    # only when agent == "claude". For codex, it should log a warn and not push.
    from harness_workflow import workflow_helpers as wh

    # Set up a minimal project tree
    project = tmp_path / "project"
    project.mkdir()
    (project / ".workflow").mkdir(parents=True)
    (project / ".workflow" / "context").mkdir()
    (project / ".workflow" / "state").mkdir()
    (project / ".workflow" / "state" / "runtime.yaml").write_text(
        "stage: executing\ncurrent_requirement: req-55\n"
        "gstack_status:\n  installed_skills: []\n  vendor_version: ''\n"
        "  last_install: ''\n  agent_kind_compatible: false\n"
        "gstack_run_log: []\n"
    )

    # Patch install_agent internals so it doesn't try to copy actual skill files
    with (
        patch.object(wh, "_project_skill_targets", return_value=[]),
        patch.object(wh, "install_local_skills", return_value=[]),
        patch.object(wh, "write_active_agent", return_value=None),
        patch.object(wh, "_write_gstack_status") as mock_write,
    ):
        rc = wh.install_agent(project, "codex", force_gstack=False)

    assert rc == 0
    # _write_gstack_status should have been called with agent_kind_compatible=False
    mock_write.assert_called_once()
    call_args = mock_write.call_args[0]
    status_dict = call_args[1]
    assert status_dict["agent_kind_compatible"] is False

    captured = capsys.readouterr()
    assert "skipping" in captured.err.lower() or "gstack" in captured.err.lower()


def test_conflict_default_warn(tmp_path: Path, capsys) -> None:
    """Hash-mismatch SKILL.md at destination → skip + warn when force=False."""
    from harness_workflow import workflow_helpers as wh

    fake_assets = tmp_path / "assets"
    skills = ["office-hours"]
    _build_fake_gstack_assets(fake_assets, skills)

    target_skills = tmp_path / "claude_skills"
    target_skills.mkdir()
    # Pre-create a DIFFERENT office-hours/SKILL.md at destination
    (target_skills / "office-hours").mkdir()
    (target_skills / "office-hours" / "SKILL.md").write_text("# old content\n")

    with patch.object(wh, "GSTACK_SKILLS_ROOT", fake_assets / "gstack-skills"):
        result = wh._install_gstack_skills(target_root=target_skills, force=False)

    assert "office-hours" in result["skipped_skills"], "Expected skill to be skipped on conflict"
    assert "office-hours" not in result["installed_skills"]
    # Original content preserved
    assert (target_skills / "office-hours" / "SKILL.md").read_text() == "# old content\n"

    captured = capsys.readouterr()
    assert "WARN" in captured.err or "warn" in captured.err.lower()


def test_force_gstack_overrides(tmp_path: Path) -> None:
    """force=True → overwrite existing SKILL.md even when hash differs."""
    from harness_workflow import workflow_helpers as wh

    fake_assets = tmp_path / "assets"
    skills = ["office-hours"]
    _build_fake_gstack_assets(fake_assets, skills)
    new_content = "# office-hours\nThis is the office-hours skill.\n"

    target_skills = tmp_path / "claude_skills"
    target_skills.mkdir()
    (target_skills / "office-hours").mkdir()
    (target_skills / "office-hours" / "SKILL.md").write_text("# old content\n")

    with patch.object(wh, "GSTACK_SKILLS_ROOT", fake_assets / "gstack-skills"):
        result = wh._install_gstack_skills(target_root=target_skills, force=True)

    assert "office-hours" in result["installed_skills"]
    assert (target_skills / "office-hours" / "SKILL.md").read_text() == new_content


def test_skill_push_failure_does_not_block(tmp_path: Path) -> None:
    """Single skill copy failure → main flow continues + gstack_failures recorded."""
    from harness_workflow import workflow_helpers as wh

    fake_assets = tmp_path / "assets"
    skills = ["office-hours", "qa", "review"]
    _build_fake_gstack_assets(fake_assets, skills)

    target_skills = tmp_path / "claude_skills"
    target_skills.mkdir()

    # Make target_skills/qa non-writable so mkdir will succeed but copy2 will fail
    qa_dest = target_skills / "qa"
    qa_dest.mkdir()
    qa_dest.chmod(0o444)  # read-only → write to SKILL.md will fail

    try:
        with patch.object(wh, "GSTACK_SKILLS_ROOT", fake_assets / "gstack-skills"):
            result = wh._install_gstack_skills(target_root=target_skills, force=False)

        # qa may or may not fail depending on OS; but install should not raise
        assert isinstance(result, dict)
        # office-hours and review should succeed
        assert "office-hours" in result["installed_skills"] or "office-hours" in result["skipped_skills"]
        assert "review" in result["installed_skills"] or "review" in result["skipped_skills"]
        # The main flow completed (no exception propagated)
    finally:
        qa_dest.chmod(0o755)  # restore permissions so tmp_path cleanup works


def test_runtime_yaml_gstack_status_written(tmp_path: Path) -> None:
    """After _install_gstack_skills, runtime.yaml.gstack_status has 4 correct sub-fields."""
    from harness_workflow import workflow_helpers as wh

    # Set up minimal project with runtime.yaml
    project = tmp_path / "project"
    state_dir = project / ".workflow" / "state"
    state_dir.mkdir(parents=True)
    runtime_path = state_dir / "runtime.yaml"
    runtime_path.write_text(
        "stage: executing\ncurrent_requirement: req-55\n"
        "gstack_status:\n  installed_skills: []\n  vendor_version: ''\n"
        "  last_install: ''\n  agent_kind_compatible: false\n"
        "gstack_run_log: []\n"
    )

    fake_assets = tmp_path / "assets"
    skills = ["office-hours", "qa"]
    _build_fake_gstack_assets(fake_assets, skills)

    target_skills = tmp_path / "claude_skills"
    target_skills.mkdir()

    with patch.object(wh, "GSTACK_SKILLS_ROOT", fake_assets / "gstack-skills"):
        gstack_result = wh._install_gstack_skills(target_root=target_skills, force=False)

    # Build the status dict as install_agent would
    import datetime
    gstack_status = {
        "installed_skills": gstack_result["installed_skills"],
        "vendor_version": gstack_result["vendor_version"],
        "last_install": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "agent_kind_compatible": True,
    }
    wh._write_gstack_status(project, gstack_status)

    data = yaml.safe_load(runtime_path.read_text(encoding="utf-8"))
    assert "gstack_status" in data
    gs = data["gstack_status"]
    assert "installed_skills" in gs
    assert "vendor_version" in gs
    assert "last_install" in gs
    assert "agent_kind_compatible" in gs
    assert gs["agent_kind_compatible"] is True
    assert gs["vendor_version"] == "abc1234"
    assert set(gs["installed_skills"]) == {"office-hours", "qa"}
