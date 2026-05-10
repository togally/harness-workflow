"""pytest lint tests for req-56 / chg-02: analyst.md Step A1.5 改造 + adapter 强制门 + mirror 同步.

7 用例 P0（per chg-02 plan.md §4 测试用例表）:
  TC-01: grep `office_hours_mode` analyst.md Step A1.5 块 → 命中 ≥ 1
  TC-02: grep `必经环节` analyst.md Step A1.5.adapter 段 → 命中 ≥ 1
  TC-03: grep `harness validate --contract artifact-placement` Step A1.5 退出门段 → 命中 ≥ 1
  TC-04: grep `请选择.*office-hours|是否.*office-hours` analyst.md → 命中 == 0（offer 句式已删）
  TC-05: grep `Step A1.5.escape` analyst.md → 命中 ≥ 1（fallback 改名 escape）
  TC-06: diff -q live mirror → silent（0 差异）
  TC-07: harness validate --human-docs → lint 跑通（returncode ∈ {0,1} + 含 Summary）

所有用例用 subprocess/grep 实现，不修改任何被测文件。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_ANALYST = REPO_ROOT / ".workflow" / "context" / "roles" / "analyst.md"
MIRROR_ANALYST = REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "roles" / "analyst.md"


class TestOfficeHoursModeInStepA15:
    """TC-01: grep `office_hours_mode` 在 analyst.md Step A1.5 内 ≥ 1 次."""

    def test_office_hours_mode_field_referenced(self) -> None:
        result = subprocess.run(
            ["grep", "-c", "office_hours_mode", str(LIVE_ANALYST)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        assert count >= 1, (
            f"Expected at least 1 occurrence of 'office_hours_mode' in analyst.md, got {count}\n"
            f"File: {LIVE_ANALYST}"
        )


class TestAdapterMustPassLabel:
    """TC-02: grep `必经环节` 在 analyst.md Step A1.5.adapter 段 ≥ 1 次."""

    def test_adapter_must_pass_label_present(self) -> None:
        result = subprocess.run(
            ["grep", "-c", "必经环节", str(LIVE_ANALYST)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        assert count >= 1, (
            f"Expected at least 1 occurrence of '必经环节' in analyst.md, got {count}"
        )


class TestExitGateValidatePresent:
    """TC-03: grep `harness validate --contract artifact-placement` 在 Step A1.5 退出门段 ≥ 1 次."""

    def test_exit_gate_validate_contract_present(self) -> None:
        result = subprocess.run(
            ["grep", "-c", "harness validate --contract artifact-placement", str(LIVE_ANALYST)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        # analyst.md may reference this in Step A1.5 exit gate AND other places; ≥1 is sufficient
        assert count >= 1, (
            f"Expected at least 1 occurrence of 'harness validate --contract artifact-placement' in analyst.md, got {count}"
        )


class TestOfferSentenceDeleted:
    """TC-04: grep `请选择.*office-hours|是否.*office-hours` analyst.md → 命中 == 0."""

    def test_offer_sentence_deleted(self) -> None:
        text = LIVE_ANALYST.read_text(encoding="utf-8")
        # Use python regex to check both patterns
        pattern = re.compile(r"请选择.*office-hours|是否.*office-hours")
        matches = pattern.findall(text)
        assert len(matches) == 0, (
            f"Expected 0 matches for offer sentence pattern, got {len(matches)}: {matches}"
        )


class TestEscapeSubsectionPresent:
    """TC-05: grep `Step A1.5.escape` analyst.md → 命中 ≥ 1（fallback 改名 escape）."""

    def test_escape_subsection_renamed_present(self) -> None:
        result = subprocess.run(
            ["grep", "-c", "Step A1.5.escape", str(LIVE_ANALYST)],
            capture_output=True, text=True,
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        assert count >= 1, (
            f"Expected at least 1 occurrence of 'Step A1.5.escape' in analyst.md, got {count}"
        )


class TestLiveMirrorDiffSilent:
    """TC-06: diff -q live mirror → silent (0 differences)."""

    def test_live_mirror_diff_silent(self) -> None:
        result = subprocess.run(
            ["diff", "-q", str(LIVE_ANALYST), str(MIRROR_ANALYST)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"Live and mirror analyst.md differ!\n"
            f"Live:   {LIVE_ANALYST}\n"
            f"Mirror: {MIRROR_ANALYST}\n"
            f"Diff stdout: {result.stdout}\n"
            f"Diff stderr: {result.stderr}"
        )


class TestHumanDocsLintRuns:
    """TC-07: harness validate --human-docs → lint 跑通（returncode ∈ {0,1} + stdout 含 Summary）.

    注：testing/executing 阶段 raw_artifact pending 时 by-design exit 1；
    本 TC 只断言 lint 进程不崩溃且输出含 Summary。
    """

    def test_human_docs_lint_runs_without_crash(self) -> None:
        env = {"PYTHONPATH": str(REPO_ROOT / "src")}
        import os
        full_env = dict(os.environ)
        full_env.update(env)

        result = subprocess.run(
            [sys.executable, "-m", "harness_workflow.cli", "validate", "--human-docs",
             "--root", str(REPO_ROOT)],
            capture_output=True, text=True,
            cwd=str(REPO_ROOT),
            env=full_env,
        )
        assert result.returncode in (0, 1), (
            f"validate --human-docs crashed (returncode={result.returncode})\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "Summary" in result.stdout, (
            f"Expected 'Summary' in stdout of --human-docs lint\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
