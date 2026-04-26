"""Tests for bugfix flow layout (bugfix-6 A1/A2/A5).

Covers:
- A1: new bugfix >= bugfix-6 writes machine-type docs to .workflow/flow/bugfixes/
- A1: artifacts/ only gets README.md placeholder
- A2: create_suggestion / create_change / create_requirement don't write machine-type docs to artifacts/
- A5: migrate_bugfix_layout moves bugfix-1~5 docs to .workflow/flow/bugfixes/
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from harness_workflow.workflow_helpers import (
    BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID,
    _use_flow_layout_for_bugfix,
    create_bugfix,
    migrate_bugfix_layout,
)


# ─────────────────────── helpers ────────────────────────


def _make_root(tmp_path: Path) -> Path:
    """Set up a minimal harness repo root with required config."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text('{"language": "cn"}')
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "operation_type: requirement\noperation_target: ''\ncurrent_requirement: ''\n"
        "current_requirement_title: ''\nstage: ''\nconversation_mode: open\n"
        "locked_requirement: ''\nlocked_requirement_title: ''\nlocked_stage: ''\n"
        "current_regression: ''\ncurrent_regression_title: ''\n"
        "ff_mode: false\nff_stage_history: []\nactive_requirements: []\n"
    )
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    # Git init so _get_git_branch works
    import subprocess
    subprocess.run(["git", "init", "-q", "--initial-branch=main", str(root)], check=False)
    subprocess.run(["git", "init", "-q", str(root)], check=False)  # fallback
    return root


# ─────────────────────── A1: flow layout constant ────────────────────────


def test_bugfix_flow_layout_from_bugfix_id_constant():
    """BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID should be 6."""
    assert BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID == 6


def test_use_flow_layout_for_bugfix_6():
    assert _use_flow_layout_for_bugfix("bugfix-6") is True


def test_use_flow_layout_for_bugfix_7():
    assert _use_flow_layout_for_bugfix("bugfix-7") is True


def test_use_flow_layout_for_bugfix_5():
    """bugfix-5 walks legacy path (A5 migration)."""
    assert _use_flow_layout_for_bugfix("bugfix-5") is False


def test_use_flow_layout_for_bugfix_1():
    assert _use_flow_layout_for_bugfix("bugfix-1") is False


def test_use_flow_layout_unknown_id():
    """Unknown id format defaults to True (safe default)."""
    assert _use_flow_layout_for_bugfix("bugfix-abc") is True


# ─────────────────────── A1: create_bugfix flow layout ────────────────────────


def test_create_bugfix_flow_layout_machine_docs_in_flow(tmp_path):
    """New bugfix-7+ writes machine-type docs to .workflow/flow/bugfixes/."""
    root = _make_root(tmp_path)
    rc = create_bugfix(root, name="test A1 flow", bugfix_id="bugfix-7")
    assert rc == 0

    # Machine-type docs should be in .workflow/flow/bugfixes/
    flow_dir = root / ".workflow" / "flow" / "bugfixes"
    matching = list(flow_dir.glob("bugfix-7-*"))
    assert len(matching) == 1, f"Expected 1 bugfix-7 dir, got: {matching}"
    bf_dir = matching[0]

    assert (bf_dir / "bugfix.md").exists(), "bugfix.md must be in flow dir"
    assert (bf_dir / "session-memory.md").exists(), "session-memory.md must be in flow dir"
    assert (bf_dir / "test-evidence.md").exists(), "test-evidence.md must be in flow dir"
    assert (bf_dir / "regression" / "diagnosis.md").exists(), "diagnosis.md must be in flow dir"
    assert (bf_dir / "regression" / "required-inputs.md").exists(), "required-inputs.md must be in flow dir"


def test_create_bugfix_flow_layout_artifacts_readme_only(tmp_path):
    """New bugfix-7+ creates only README.md in artifacts/, no machine-type docs."""
    root = _make_root(tmp_path)
    rc = create_bugfix(root, name="test A1 artifacts", bugfix_id="bugfix-7")
    assert rc == 0

    artifacts_bugfixes = root / "artifacts"
    all_md_files = list(artifacts_bugfixes.rglob("*.md")) if artifacts_bugfixes.exists() else []

    machine_type = {
        "bugfix.md", "session-memory.md", "test-evidence.md",
        "diagnosis.md", "required-inputs.md",
    }
    for md_file in all_md_files:
        assert md_file.name not in machine_type, (
            f"Machine-type file {md_file.name} found in artifacts/: {md_file}"
        )

    # Should have README.md placeholder
    readme_files = [f for f in all_md_files if f.name == "README.md"]
    assert len(readme_files) >= 1, "README.md placeholder should exist in artifacts/"


# ─────────────────────── A2: verify create_suggestion / create_requirement ────────────────────────


def test_create_suggestion_does_not_write_to_artifacts(tmp_path):
    """create_suggestion writes to .workflow/flow/suggestions/, not artifacts/."""
    root = _make_root(tmp_path)
    # ensure_harness_root check needs .workflow/context to exist
    (root / ".workflow" / "context").mkdir(parents=True, exist_ok=True)
    from harness_workflow.workflow_helpers import create_suggestion
    rc = create_suggestion(root, content="test suggestion A2", title="test-A2")
    assert rc == 0
    artifacts = root / "artifacts"
    if artifacts.exists():
        sug_files = list(artifacts.rglob("*.md"))
        assert len(sug_files) == 0, f"Suggestion files found in artifacts/: {sug_files}"
    flow_sugs = root / ".workflow" / "flow" / "suggestions"
    assert flow_sugs.exists(), ".workflow/flow/suggestions/ must exist"
    assert len(list(flow_sugs.glob("*.md"))) >= 1, "suggestion file must be in flow/suggestions/"


# ─────────────────────── A5: migrate_bugfix_layout ────────────────────────


def test_migrate_bugfix_layout_dry_run(tmp_path):
    """migrate_bugfix_layout --dry-run returns 0 and doesn't move files."""
    root = _make_root(tmp_path)
    # Create a fake bugfix-3 in artifacts/
    bf_dir = root / "artifacts" / "main" / "bugfixes" / "bugfix-3-test"
    bf_dir.mkdir(parents=True)
    (bf_dir / "bugfix.md").write_text("# bugfix-3")
    (bf_dir / "session-memory.md").write_text("# session")
    (bf_dir / "test-evidence.md").write_text("# test")
    reg_dir = bf_dir / "regression"
    reg_dir.mkdir()
    (reg_dir / "diagnosis.md").write_text("# diag")
    (reg_dir / "required-inputs.md").write_text("# inputs")

    rc = migrate_bugfix_layout(root, dry_run=True)
    assert rc == 0

    # Files should not have moved
    assert (bf_dir / "bugfix.md").exists(), "dry-run should not move files"
    flow_dir = root / ".workflow" / "flow" / "bugfixes"
    assert not flow_dir.exists() or not list(flow_dir.glob("bugfix-3-*")), "dry-run must not create flow dir"


def test_migrate_bugfix_layout_moves_machine_docs(tmp_path):
    """migrate_bugfix_layout moves bugfix-1~5 machine-type docs to flow/bugfixes/."""
    root = _make_root(tmp_path)
    bf_dir = root / "artifacts" / "main" / "bugfixes" / "bugfix-2-some-bug"
    bf_dir.mkdir(parents=True)
    (bf_dir / "bugfix.md").write_text("# bugfix-2")
    (bf_dir / "session-memory.md").write_text("# session")
    (bf_dir / "test-evidence.md").write_text("# test")
    reg_dir = bf_dir / "regression"
    reg_dir.mkdir()
    (reg_dir / "diagnosis.md").write_text("# diag")
    (reg_dir / "required-inputs.md").write_text("# inputs")

    rc = migrate_bugfix_layout(root, dry_run=False)
    assert rc == 0

    flow_bf = root / ".workflow" / "flow" / "bugfixes" / "bugfix-2-some-bug"
    assert (flow_bf / "bugfix.md").exists(), "bugfix.md should be in flow/"
    assert (flow_bf / "session-memory.md").exists()
    assert (flow_bf / "test-evidence.md").exists()
    assert (flow_bf / "regression" / "diagnosis.md").exists()
    assert (flow_bf / "regression" / "required-inputs.md").exists()


def test_migrate_bugfix_layout_readme_placeholder(tmp_path):
    """migrate_bugfix_layout creates README.md placeholder in old artifacts/ dir."""
    root = _make_root(tmp_path)
    bf_dir = root / "artifacts" / "main" / "bugfixes" / "bugfix-4-another"
    bf_dir.mkdir(parents=True)
    (bf_dir / "bugfix.md").write_text("# bugfix-4")
    (bf_dir / "session-memory.md").write_text("# session")

    migrate_bugfix_layout(root, dry_run=False)
    assert (bf_dir / "README.md").exists(), "README.md placeholder must be created in artifacts/ dir"
    readme_content = (bf_dir / "README.md").read_text()
    assert "bugfix-4" in readme_content, "README must mention bugfix-4"


def test_migrate_bugfix_layout_skips_bugfix_6_plus(tmp_path):
    """migrate_bugfix_layout skips bugfix-6+ (already on flow path)."""
    root = _make_root(tmp_path)
    bf6_dir = root / "artifacts" / "main" / "bugfixes" / "bugfix-6-new"
    bf6_dir.mkdir(parents=True)
    (bf6_dir / "bugfix.md").write_text("# bugfix-6")

    migrate_bugfix_layout(root, dry_run=False)

    # bugfix-6 should NOT be moved
    assert (bf6_dir / "bugfix.md").exists(), "bugfix-6 must not be moved"
    flow_dir = root / ".workflow" / "flow" / "bugfixes"
    if flow_dir.exists():
        assert not list(flow_dir.glob("bugfix-6-*")), "bugfix-6+ must not appear in flow/"


def test_migrate_bugfix_layout_idempotent(tmp_path):
    """migrate_bugfix_layout is idempotent - skips already-migrated dirs."""
    root = _make_root(tmp_path)
    bf_dir = root / "artifacts" / "main" / "bugfixes" / "bugfix-1-old"
    bf_dir.mkdir(parents=True)
    (bf_dir / "bugfix.md").write_text("# bugfix-1")

    # Run migration twice
    migrate_bugfix_layout(root, dry_run=False)
    rc2 = migrate_bugfix_layout(root, dry_run=False)
    assert rc2 == 0, "Second run should return 0 (idempotent)"
