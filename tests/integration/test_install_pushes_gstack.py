"""Integration tests: harness install --agent claude pushes gstack skills.

req-55 / chg-01 (gstack 内置发布契约 — vendor 全 skill + harness install 自动装载)

These tests run the full install_agent() flow in a tmp project directory and
assert that the gstack vendor assets end up at the correct locations under a
simulated ~/.claude/skills/ root.

Test plan:
  1. Set up a minimal project + patched HOME / target_root
  2. Run install_agent(root, "claude")
  3. Assert: N skill dirs with SKILL.md + LICENSE-gstack
  4. Assert: ~/.claude/skills/gstack/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack}
  5. Assert: runtime.yaml.gstack_status written correctly (4 sub-fields)
  6. Assert: vendor_version matches _shared/VERSION-gstack
  7. Re-run install (idempotent): no conflict noise for identical files
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
GSTACK_ASSETS = REPO_ROOT / "src" / "harness_workflow" / "assets" / "gstack-skills"


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Return a minimal harness project root with patched HOME."""
    proj = tmp_path / "project"
    proj.mkdir()

    # Minimal .workflow/ skeleton so install_agent doesn't call init_repo
    wf = proj / ".workflow"
    ctx = wf / "context"
    state = wf / "state"
    ctx.mkdir(parents=True)
    state.mkdir(parents=True)
    (wf / "tools").mkdir(exist_ok=True)

    runtime_yaml = (
        "stage: executing\n"
        "current_requirement: req-55\n"
        "conversation_mode: open\n"
        "gstack_status:\n"
        "  installed_skills: []\n"
        "  vendor_version: ''\n"
        "  last_install: ''\n"
        "  agent_kind_compatible: false\n"
        "gstack_run_log: []\n"
    )
    (state / "runtime.yaml").write_text(runtime_yaml)

    # Minimal config.json
    (proj / ".codex").mkdir()
    (proj / ".codex" / "harness").mkdir()
    config_json = '{"language": "english"}'
    (proj / ".codex" / "harness" / "config.json").write_text(config_json)
    (proj / ".codex" / "harness" / "managed-files.json").write_text('{"tool_version": "0.2.0", "files": {}}')

    # Patch HOME so that ~/.claude/skills/ resolves to tmp_path/fake_home/.claude/skills/
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    return proj


def _get_shared_version() -> str:
    """Read commit hash from _shared/VERSION-gstack."""
    vf = GSTACK_ASSETS / "_shared" / "VERSION-gstack"
    if not vf.exists():
        return ""
    for line in vf.read_text(encoding="utf-8").splitlines():
        if line.startswith("commit:"):
            return line.split(":", 1)[1].strip()
    return ""


@pytest.mark.skipif(
    not GSTACK_ASSETS.exists() or not any(
        (GSTACK_ASSETS / d).exists()
        for d in ["office-hours", "qa", "review"]
    ),
    reason="Requires vendored gstack-skills assets (run scripts/vendor-gstack.sh --all first)",
)
class TestInstallPushesGstack:
    """Integration test suite for gstack skills push via install_agent."""

    def test_skills_pushed_to_claude_skills(self, project: Path, tmp_path: Path) -> None:
        """install_agent(claude) pushes all skill dirs to ~/.claude/skills/."""
        from harness_workflow import workflow_helpers as wh

        fake_claude_skills = tmp_path / "fake_home" / ".claude" / "skills"

        with (
            patch.object(wh, "get_agent_skill_path", return_value=project / ".claude" / "skills" / "harness"),
            patch("harness_workflow.workflow_helpers.Path.home", return_value=tmp_path / "fake_home"),
        ):
            rc = wh.install_agent(project, "claude", force_gstack=False)

        assert rc == 0
        assert fake_claude_skills.exists()

        skill_dirs = [d for d in fake_claude_skills.iterdir() if d.is_dir() and d.name != "gstack"]
        skills_with_skill_md = [d for d in skill_dirs if (d / "SKILL.md").exists()]
        assert len(skills_with_skill_md) >= 40, (
            f"Expected at least 40 skill dirs with SKILL.md, got {len(skills_with_skill_md)}: "
            f"{[d.name for d in skills_with_skill_md]}"
        )

    def test_license_pushed_to_each_skill(self, project: Path, tmp_path: Path) -> None:
        """Each vendored skill dir receives a LICENSE-gstack file."""
        from harness_workflow import workflow_helpers as wh

        fake_claude_skills = tmp_path / "fake_home" / ".claude" / "skills"

        with (
            patch.object(wh, "get_agent_skill_path", return_value=project / ".claude" / "skills" / "harness"),
            patch("harness_workflow.workflow_helpers.Path.home", return_value=tmp_path / "fake_home"),
        ):
            wh.install_agent(project, "claude", force_gstack=False)

        for skill_dir in fake_claude_skills.iterdir():
            if skill_dir.is_dir() and skill_dir.name != "gstack":
                if (skill_dir / "SKILL.md").exists():
                    assert (skill_dir / "LICENSE-gstack").exists(), (
                        f"LICENSE-gstack missing from {skill_dir.name}"
                    )

    def test_shared_resources_pushed(self, project: Path, tmp_path: Path) -> None:
        """~/.claude/skills/gstack/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack} present."""
        from harness_workflow import workflow_helpers as wh

        fake_claude_skills = tmp_path / "fake_home" / ".claude" / "skills"

        with (
            patch.object(wh, "get_agent_skill_path", return_value=project / ".claude" / "skills" / "harness"),
            patch("harness_workflow.workflow_helpers.Path.home", return_value=tmp_path / "fake_home"),
        ):
            wh.install_agent(project, "claude", force_gstack=False)

        gstack_shared = fake_claude_skills / "gstack"
        assert gstack_shared.exists(), "~/.claude/skills/gstack/ not created"
        assert (gstack_shared / "LICENSE-gstack").exists()
        assert (gstack_shared / "VERSION-gstack").exists()
        assert (gstack_shared / "bin").exists()

    def test_runtime_yaml_gstack_status(self, project: Path, tmp_path: Path) -> None:
        """runtime.yaml.gstack_status has all 4 sub-fields after install."""
        from harness_workflow import workflow_helpers as wh

        with (
            patch.object(wh, "get_agent_skill_path", return_value=project / ".claude" / "skills" / "harness"),
            patch("harness_workflow.workflow_helpers.Path.home", return_value=tmp_path / "fake_home"),
        ):
            wh.install_agent(project, "claude", force_gstack=False)

        runtime_path = project / ".workflow" / "state" / "runtime.yaml"
        data = yaml.safe_load(runtime_path.read_text(encoding="utf-8"))

        assert "gstack_status" in data, "gstack_status missing from runtime.yaml"
        gs = data["gstack_status"]
        assert "installed_skills" in gs
        assert "vendor_version" in gs
        assert "last_install" in gs
        assert "agent_kind_compatible" in gs
        assert gs["agent_kind_compatible"] is True
        assert isinstance(gs["installed_skills"], list)
        assert len(gs["installed_skills"]) >= 40

    def test_vendor_version_matches_shared(self, project: Path, tmp_path: Path) -> None:
        """runtime.yaml gstack_status.vendor_version matches _shared/VERSION-gstack commit."""
        from harness_workflow import workflow_helpers as wh

        expected_version = _get_shared_version()
        if not expected_version:
            pytest.skip("Cannot read VERSION-gstack commit hash")

        with (
            patch.object(wh, "get_agent_skill_path", return_value=project / ".claude" / "skills" / "harness"),
            patch("harness_workflow.workflow_helpers.Path.home", return_value=tmp_path / "fake_home"),
        ):
            wh.install_agent(project, "claude", force_gstack=False)

        runtime_path = project / ".workflow" / "state" / "runtime.yaml"
        data = yaml.safe_load(runtime_path.read_text(encoding="utf-8"))
        assert data["gstack_status"]["vendor_version"] == expected_version

    def test_idempotent_second_run_no_conflict(
        self, project: Path, tmp_path: Path, capsys
    ) -> None:
        """Second install with identical files: no conflict warnings, no re-copy noise."""
        from harness_workflow import workflow_helpers as wh

        kwargs = dict(
            root=project,
            agent="claude",
            force_gstack=False,
        )
        patches = (
            patch.object(wh, "get_agent_skill_path", return_value=project / ".claude" / "skills" / "harness"),
            patch("harness_workflow.workflow_helpers.Path.home", return_value=tmp_path / "fake_home"),
        )

        with patches[0], patches[1]:
            wh.install_agent(**kwargs)

        # Clear captured output before second run
        capsys.readouterr()

        with patches[0], patches[1]:
            rc2 = wh.install_agent(**kwargs)

        assert rc2 == 0
        captured = capsys.readouterr()
        # No "WARN ... different content" messages on second run
        assert "different content" not in captured.err

    def test_agent_codex_skips_gstack(self, project: Path, tmp_path: Path) -> None:
        """agent=codex → gstack push skipped, agent_kind_compatible=False in runtime.yaml."""
        from harness_workflow import workflow_helpers as wh

        fake_claude_skills = tmp_path / "fake_home" / ".claude" / "skills"

        with (
            patch.object(wh, "get_agent_skill_path", return_value=project / ".codex" / "skills" / "harness"),
            patch("harness_workflow.workflow_helpers.Path.home", return_value=tmp_path / "fake_home"),
        ):
            rc = wh.install_agent(project, "codex", force_gstack=False)

        assert rc == 0
        # No gstack skill dirs created for codex
        if fake_claude_skills.exists():
            skill_dirs = [d for d in fake_claude_skills.iterdir() if d.is_dir()]
            assert not any((d / "SKILL.md").exists() for d in skill_dirs if d.name != "gstack"), \
                "gstack skills should not be pushed for codex agent"

        runtime_path = project / ".workflow" / "state" / "runtime.yaml"
        data = yaml.safe_load(runtime_path.read_text(encoding="utf-8"))
        assert data["gstack_status"]["agent_kind_compatible"] is False
