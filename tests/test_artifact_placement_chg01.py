"""Tests for chg-01（机器型工件路径修复 + 防再犯 lint）— TC-01 through TC-08.

ref: .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/
         changes/chg-01-机器型工件路径修复-防再犯-lint/plan.md §4

覆盖：
    TC-01  4 文件静态落位 + 空目录清理 + requirement.md 保留
    TC-02  干净仓库跑 lint → PASS (exit 0)
    TC-03  构造反例：stage-name 子目录 + 机器型文件 → FAIL (exit 1)
    TC-04  artifacts/.../requirement.md 白名单豁免 → PASS
    TC-05  构造新工件名反例：sug-audit.md / roadmap.md → FAIL
    TC-06  scaffold_v2 mirror diff clean（仅 chg-01 相关 4 文件一致）
    TC-07  sug-35 状态翻转（在 acceptance PASS 后执行，本 test 模拟文件状态）
    TC-08  dogfood：本 chg 自身产出工件均落 .workflow/flow/ 而非 artifacts/
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from harness_workflow.validate_contract import (
    check_artifact_placement,
    _MACHINE_TYPE_FILENAMES,
    _STAGE_NAME_SUBDIRS,
    _REQUIREMENT_MD_WHITELIST_PATTERN,
)

# ─────────────────────── repo root constant ────────────────────────

REPO_ROOT = Path(__file__).parent.parent
REQ46_SLUG = "req-46-建议池梳理验证-优先级-roadmap-分批落地"
CHG01_SLUG = "chg-01-机器型工件路径修复-防再犯-lint"


def _req46_flow_base() -> Path:
    """Return req-46 flow directory (active or archive)."""
    active = REPO_ROOT / ".workflow/flow/requirements" / REQ46_SLUG
    if active.exists():
        return active
    archive = REPO_ROOT / ".workflow/flow/archive/main" / REQ46_SLUG
    if archive.exists():
        return archive
    return active  # return active path for error messages


# ────────────────────────── TC-01 ──────────────────────────────────

class TestTC01_FileRegressionAndCleanup:
    """TC-01: 4 文件物理回归 + 2 空目录清理 + requirement.md 保留."""

    def test_req_review_session_memory_in_flow(self):
        target = _req46_flow_base() / "requirement-review" / "session-memory.md"
        assert target.is_file(), f"Missing: {target}"

    def test_req_review_sug_audit_in_flow(self):
        target = _req46_flow_base() / "requirement-review" / "sug-audit.md"
        assert target.is_file(), f"Missing: {target}"

    def test_planning_session_memory_in_flow(self):
        target = _req46_flow_base() / "planning" / "session-memory.md"
        assert target.is_file(), f"Missing: {target}"

    def test_planning_roadmap_in_flow(self):
        target = _req46_flow_base() / "planning" / "roadmap.md"
        assert target.is_file(), f"Missing: {target}"

    def test_requirement_review_dir_gone_from_artifacts(self):
        bad_dir = (
            REPO_ROOT
            / "artifacts/main/requirements"
            / REQ46_SLUG
            / "requirement-review"
        )
        assert not bad_dir.exists(), f"Stage dir should be gone: {bad_dir}"

    def test_planning_dir_gone_from_artifacts(self):
        bad_dir = (
            REPO_ROOT
            / "artifacts/main/requirements"
            / REQ46_SLUG
            / "planning"
        )
        assert not bad_dir.exists(), f"Stage dir should be gone: {bad_dir}"

    def test_requirement_md_whitelist_raw_copy_preserved(self):
        # req-46's requirement.md may be in artifacts (active) or in flow/archive (if archived)
        wl_artifacts = REPO_ROOT / "artifacts/main/requirements" / REQ46_SLUG / "requirement.md"
        wl_flow = _req46_flow_base() / "requirement.md"
        assert wl_artifacts.is_file() or wl_flow.is_file(), (
            f"requirement.md not found in artifacts ({wl_artifacts}) or flow ({wl_flow})"
        )


# ────────────────────────── TC-02 ──────────────────────────────────

class TestTC02_LintPassOnCleanRepo:
    """TC-02: 干净仓库（无违规）跑 lint → PASS (exit 0)."""

    def test_lint_exits_zero(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        rc = check_artifact_placement(root)
        assert rc == 0

    def test_lint_pass_with_whitelist_human_docs(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        req_dir = root / "artifacts/main/requirements/req-46-test"
        req_dir.mkdir(parents=True)
        (req_dir / "requirement.md").write_text("# req")      # whitelist
        (req_dir / "交付总结.md").write_text("# done")           # whitelist
        rc = check_artifact_placement(root)
        assert rc == 0

    def test_current_repo_lint_exits_zero(self):
        """AC-2: 当前仓库（chg-01 落地后）跑 lint → exit 0."""
        rc = check_artifact_placement(REPO_ROOT)
        assert rc == 0, "Current repo has artifact-placement violations!"


# ────────────────────────── TC-03 ──────────────────────────────────

class TestTC03_LintCatchesStageDirAndMachineType:
    """TC-03: 构造反例：stage-name 子目录 + 机器型文件 → FAIL (exit 1)."""

    def test_stage_name_subdir_triggers_fail(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        stage_dir = (
            root / "artifacts/main/requirements/req-test-x/executing"
        )
        stage_dir.mkdir(parents=True)
        (stage_dir / "session-memory.md").write_text("# machine type")
        rc = check_artifact_placement(root)
        assert rc in (1, 64), "Stage-name subdir should trigger FAIL"

    def test_all_stage_name_subdirs_in_set(self):
        expected = {
            "requirement-review", "planning", "executing",
            "testing", "acceptance", "done", "regression", "regressions",
        }
        assert expected == _STAGE_NAME_SUBDIRS

    def test_stage_dir_without_files_still_fails(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        stage_dir = (
            root / "artifacts/main/requirements/req-test-y/planning"
        )
        stage_dir.mkdir(parents=True)
        # stage-name 子目录本身存在即 FAIL（规则 0）
        rc = check_artifact_placement(root)
        assert rc in (1, 64)

    def test_session_memory_in_stage_subdir_fails(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        stage_dir = (
            root / "artifacts/main/requirements/req-test-z/regression"
        )
        stage_dir.mkdir(parents=True)
        (stage_dir / "session-memory.md").write_text("# reg session")
        rc = check_artifact_placement(root)
        assert rc in (1, 64)


# ────────────────────────── TC-04 ──────────────────────────────────

class TestTC04_WhitelistRequirementMd:
    """TC-04: artifacts/.../requirement.md 白名单豁免 → PASS."""

    def test_requirement_md_at_req_level_passes(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        req_dir = root / "artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地"
        req_dir.mkdir(parents=True)
        (req_dir / "requirement.md").write_text("# requirement")
        rc = check_artifact_placement(root)
        assert rc == 0, "requirement.md at req-level should be whitelisted"

    def test_whitelist_pattern_matches(self):
        valid = "artifacts/main/requirements/req-46-test/requirement.md"
        assert _REQUIREMENT_MD_WHITELIST_PATTERN.match(valid)

    def test_whitelist_pattern_rejects_stage_subdir(self):
        bad = "artifacts/main/requirements/req-46-test/planning/requirement.md"
        assert not _REQUIREMENT_MD_WHITELIST_PATTERN.match(bad)

    def test_requirement_md_in_stage_subdir_fails(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        stage_dir = root / "artifacts/main/requirements/req-test/planning"
        stage_dir.mkdir(parents=True)
        (stage_dir / "requirement.md").write_text("# should not be here")
        rc = check_artifact_placement(root)
        # Both: stage-name dir (rule 0) + requirement.md not at req-level (rule 1) → FAIL
        assert rc in (1, 64)


# ────────────────────────── TC-05 ──────────────────────────────────

class TestTC05_NewFilenamesCaughtByLint:
    """TC-05: sug-audit.md / roadmap.md 等新扩展文件名被 lint 命中."""

    def test_sug_audit_in_machine_type_set(self):
        assert "sug-audit.md" in _MACHINE_TYPE_FILENAMES

    def test_roadmap_in_machine_type_set(self):
        assert "roadmap.md" in _MACHINE_TYPE_FILENAMES

    def test_sug_audit_in_artifacts_fails(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        req_dir = root / "artifacts/main/requirements/req-test"
        req_dir.mkdir(parents=True)
        (req_dir / "sug-audit.md").write_text("# sug audit")
        rc = check_artifact_placement(root)
        assert rc in (1, 64)

    def test_roadmap_in_artifacts_fails(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()
        req_dir = root / "artifacts/main/requirements/req-test"
        req_dir.mkdir(parents=True)
        (req_dir / "roadmap.md").write_text("# roadmap")
        rc = check_artifact_placement(root)
        assert rc in (1, 64)

    def test_session_memory_remains_in_machine_type_set(self):
        assert "session-memory.md" in _MACHINE_TYPE_FILENAMES


# ────────────────────────── TC-06 ──────────────────────────────────

class TestTC06_ScaffoldV2MirrorConsistency:
    """TC-06: scaffold_v2 mirror diff 4 个 chg-01 涉及文件一致."""

    LIVE_ROLES = REPO_ROOT / ".workflow/context/roles"
    SCAFFOLD_ROLES = REPO_ROOT / "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles"
    LIVE_CHECKLISTS = REPO_ROOT / ".workflow/context/checklists"
    SCAFFOLD_CHECKLISTS = REPO_ROOT / "src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists"

    FILES_TO_CHECK = [
        ("roles", "harness-manager.md"),
        ("roles", "analyst.md"),
        ("roles", "stage-role.md"),
        ("checklists", "review-checklist.md"),
    ]

    @pytest.mark.parametrize("subdir,fname", FILES_TO_CHECK)
    def test_file_content_identical(self, subdir, fname):
        live_root = self.LIVE_ROLES if subdir == "roles" else self.LIVE_CHECKLISTS
        scaffold_root = self.SCAFFOLD_ROLES if subdir == "roles" else self.SCAFFOLD_CHECKLISTS
        live_f = live_root / fname
        scaffold_f = scaffold_root / fname
        assert live_f.is_file(), f"Missing live: {live_f}"
        assert scaffold_f.is_file(), f"Missing scaffold: {scaffold_f}"
        assert live_f.read_text() == scaffold_f.read_text(), (
            f"Mirror drift: {fname} content differs between live and scaffold_v2"
        )

    def test_checklist_dir_no_diff(self):
        result = subprocess.run(
            ["diff", "-rq",
             str(self.LIVE_CHECKLISTS),
             str(self.SCAFFOLD_CHECKLISTS)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"checklists/ diff found:\n{result.stdout}"


# ────────────────────────── TC-07 ──────────────────────────────────

class TestTC07_Sug35FrontmatterFlip:
    """TC-07: sug-35 状态翻转验证（执行时机：acceptance PASS 后）.

    注：Step 8 在 acceptance PASS 后执行，本 test 仅验证翻转逻辑正确性
    （可在 executing → testing → acceptance 之前先预验证文件格式，
     Step 8 完成后再断言最终状态）。
    """

    SUG_35_PATTERN = "sug-35-reviewer-checklist-artifact-placement-test-case-design-completeness-lint.md"
    SUGGESTIONS_DIR = REPO_ROOT / ".workflow/flow/suggestions"
    # Note: archive may be at suggestions/archive/ (nested) or flow/archive/suggestions/ (flat)
    ARCHIVE_DIR = REPO_ROOT / ".workflow/flow/archive/suggestions"
    ARCHIVE_DIR_NESTED = REPO_ROOT / ".workflow/flow/suggestions/archive"

    def _find_sug35(self) -> Path | None:
        for search_dir in (self.SUGGESTIONS_DIR, self.ARCHIVE_DIR, self.ARCHIVE_DIR_NESTED):
            if search_dir.is_dir():
                for f in search_dir.iterdir():
                    if f.name == self.SUG_35_PATTERN:
                        return f
        return None

    def test_sug35_exists_somewhere(self):
        f = self._find_sug35()
        assert f is not None, f"sug-35 file not found in suggestions/ or archive/suggestions/"

    def test_sug35_has_valid_frontmatter(self):
        f = self._find_sug35()
        if f is None:
            pytest.skip("sug-35 file not found")
        content = f.read_text()
        assert "status:" in content, "sug-35 missing status field"

    def test_sug35_pending_or_archived(self):
        """Before acceptance PASS, sug-35 should be pending; after, archived."""
        f = self._find_sug35()
        if f is None:
            pytest.skip("sug-35 file not found")
        content = f.read_text()
        assert ("status: pending" in content or "status: archived" in content), (
            "sug-35 status must be 'pending' (before acceptance) or 'archived' (after)"
        )


# ────────────────────────── TC-08 ──────────────────────────────────

class TestTC08_Dogfood:
    """TC-08: Dogfood — 本 chg 自身工件落 .workflow/flow/，非 artifacts/."""

    @property
    def CHG01_FLOW_DIR(self) -> Path:
        """req-46/chg-01 flow directory (active or archive)."""
        return _req46_flow_base() / "changes" / CHG01_SLUG

    def test_change_md_in_flow(self):
        assert (self.CHG01_FLOW_DIR / "change.md").is_file(), f"Missing: {self.CHG01_FLOW_DIR}/change.md"

    def test_plan_md_in_flow(self):
        assert (self.CHG01_FLOW_DIR / "plan.md").is_file(), f"Missing: {self.CHG01_FLOW_DIR}/plan.md"

    def test_session_memory_in_flow(self):
        assert (self.CHG01_FLOW_DIR / "session-memory.md").is_file(), f"Missing: {self.CHG01_FLOW_DIR}/session-memory.md"

    def test_no_machine_type_files_in_artifacts_req46(self):
        """chg-01 执行后，artifacts/main/requirements/req-46-.../ 下无机器型工件."""
        artifacts_req46 = (
            REPO_ROOT
            / "artifacts/main/requirements"
            / REQ46_SLUG
        )
        if not artifacts_req46.exists():
            pytest.skip("artifacts/main/requirements/req-46-... does not exist (gitignored OK)")
        for f in artifacts_req46.rglob("*"):
            if not f.is_file():
                continue
            # Check for machine-type filenames
            assert f.name not in _MACHINE_TYPE_FILENAMES or (
                f.name == "requirement.md"
                and _REQUIREMENT_MD_WHITELIST_PATTERN.match(
                    str(f.relative_to(REPO_ROOT))
                )
            ), f"Machine-type file found in artifacts/: {f.relative_to(REPO_ROOT)}"

    def test_no_stage_name_subdirs_in_artifacts_req46(self):
        """Step 1 完成后，artifacts/req-46-.../ 无 stage-name 子目录."""
        artifacts_req46 = (
            REPO_ROOT
            / "artifacts/main/requirements"
            / REQ46_SLUG
        )
        if not artifacts_req46.exists():
            pytest.skip("artifacts/main/requirements/req-46-... does not exist (gitignored OK)")
        for child in artifacts_req46.iterdir():
            assert child.name not in _STAGE_NAME_SUBDIRS, (
                f"Stage-name subdir still exists: {child.relative_to(REPO_ROOT)}"
            )

    def test_analyst_md_has_artifact_placement_gate(self):
        analyst_md = REPO_ROOT / ".workflow/context/roles/analyst.md"
        content = analyst_md.read_text()
        assert "harness validate --contract artifact-placement" in content, (
            "analyst.md missing artifact-placement exit gate"
        )

    def test_stage_role_md_has_path_self_check(self):
        stage_role_md = REPO_ROOT / ".workflow/context/roles/stage-role.md"
        content = stage_role_md.read_text()
        assert "路径自检" in content, "stage-role.md missing 路径自检 SOP checkpoint"

    def test_harness_manager_has_expected_artifact_paths(self):
        hm_md = REPO_ROOT / ".workflow/context/roles/harness-manager.md"
        content = hm_md.read_text()
        assert "expected_artifact_paths" in content, (
            "harness-manager.md missing expected_artifact_paths field"
        )

    def test_checklist_has_artifact_placement_sampling(self):
        checklist = REPO_ROOT / ".workflow/context/checklists/review-checklist.md"
        content = checklist.read_text()
        assert "artifact-placement 反向抽样" in content, (
            "review-checklist.md missing artifact-placement 反向抽样 entry"
        )
