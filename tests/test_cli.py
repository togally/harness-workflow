import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMAND_SAMPLES = ["harness", "harness-requirement", "harness-change", "harness-next"]
skip_legacy_version_flow = unittest.skip(
    "legacy version-flow workspace commands are outside the requirement-flow scaffold"
)


class HarnessCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-workflow-test-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "harness_workflow", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )

    def read_config(self) -> dict[str, str]:
        return json.loads((self.repo / ".codex" / "harness" / "config.json").read_text(encoding="utf-8"))

    def read_runtime(self) -> dict[str, object]:
        return json.loads((self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml").read_text(encoding="utf-8"))

    def read_version_meta(self, version: str) -> dict[str, object]:
        return json.loads(
            (self.repo / ".workflow" / "versions" / "active" / version / "meta.yaml").read_text(encoding="utf-8")
        )

    def write_requirement_runtime(
        self,
        *,
        current_requirement: str = "",
        stage: str = "",
        conversation_mode: str = "open",
        locked_requirement: str = "",
        locked_stage: str = "",
        current_regression: str = "",
        active_requirements: list[str] | None = None,
    ) -> None:
        runtime_path = self.repo / ".workflow" / "state" / "runtime.yaml"
        runtime_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f'current_requirement: "{current_requirement}"',
            f'stage: "{stage}"',
            f'conversation_mode: "{conversation_mode}"',
            f'locked_requirement: "{locked_requirement}"',
            f'locked_stage: "{locked_stage}"',
            f'current_regression: "{current_regression}"',
            "active_requirements:",
        ]
        for requirement in active_requirements or []:
            lines.append(f"  - {requirement}")
        runtime_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @unittest.skip("legacy version-flow scaffold expectations were replaced by requirement-flow entrypoints")
    def test_install_creates_triple_skills_and_default_english_config(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".codex" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / ".claude" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / ".qoder" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / ".qoder" / "rules" / "harness-workflow.md").exists())
        for command in COMMAND_SAMPLES:
            self.assertTrue((self.repo / ".qoder" / "commands" / f"{command}.md").exists())
            self.assertTrue((self.repo / ".claude" / "commands" / f"{command}.md").exists())
            self.assertTrue((self.repo / ".codex" / "skills" / command / "SKILL.md").exists())
        self.assertTrue((self.repo / ".workflow" / "context").exists())
        self.assertTrue((self.repo / ".workflow" / "versions" / "active").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "hooks" / "README.md").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "hooks" / "session-start.md").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "hooks" / "context-maintenance.md").exists())
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "context-maintenance" / "10-classify-project-scale.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "context-maintenance" / "20-decide-clear-or-compact.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "context-maintenance" / "30-switch-plan-and-act-mode.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "context-maintenance" / "executing" / "10-keep-active-plan-and-code-context.md").exists()
        )
        context_policy = (
            self.repo / ".workflow" / "context" / "hooks" / "context-maintenance" / "10-classify-project-scale.md"
        ).read_text(encoding="utf-8")
        self.assertIn("80%", context_policy)
        self.assertIn("60%", context_policy)
        self.assertIn("32k", context_policy)
        context_modes = (
            self.repo / ".workflow" / "context" / "hooks" / "context-maintenance" / "30-switch-plan-and-act-mode.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Plan Mode", context_modes)
        self.assertIn("Act Mode", context_modes)
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "node-entry" / "requirement-review" / "10-discussion-only.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-reply" / "requirement-review" / "10-request-human-review-first.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-reply" / "changes-review" / "10-request-change-review-first.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-reply" / "plan-review" / "10-request-plan-review-first.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-reply" / "ready-for-execution" / "10-request-execution-confirmation.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "node-entry" / "requirement-review" / "20-wait-for-human-approval.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "node-entry" / "changes-review" / "20-wait-for-human-approval.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "node-entry" / "plan-review" / "20-wait-for-human-approval.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "node-entry" / "ready-for-execution" / "10-wait-for-explicit-confirmation.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "during-task" / "requirement-review" / "20-no-auto-stage-advance.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "during-task" / "changes-review" / "20-no-auto-stage-advance.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "during-task" / "plan-review" / "20-no-auto-stage-advance.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "during-task" / "ready-for-execution" / "10-no-implementation-before-confirmation.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-reply" / "done" / "10-request-lesson-capture-before-closure.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "node-entry" / "done" / "10-verify-lessons-before-closeout.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "during-task" / "done" / "10-no-closeout-before-lesson-capture.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-complete" / "40-require-session-memory-sync.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-complete" / "50-require-experience-promotion-check.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "node-entry" / "idle" / "10-formalize-workspace-first.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "during-task" / "idle" / "10-no-implementation-prep.md").exists()
        )
        self.assertTrue(
            (self.repo / ".workflow" / "context" / "hooks" / "before-reply" / "idle" / "10-offer-only-workflow-actions.md").exists()
        )
        self.assertEqual(self.read_config()["language"], "english")
        self.assertTrue((self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "rules" / "development-flow.md").exists())

    def test_install_scaffolds_new_workflow_entrypoint_files(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / "WORKFLOW.md").exists())
        self.assertTrue((self.repo / "AGENTS.md").exists())
        self.assertTrue((self.repo / ".workflow" / "state" / "runtime.yaml").exists())
        self.assertTrue((self.repo / ".workflow" / "flow" / "requirements").exists())
        self.assertFalse((self.repo / ".workflow" / "flow" / "archive").exists())
        self.assertFalse((self.repo / "flow").exists())
        self.assertFalse((self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml").exists())
        agents_text = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("WORKFLOW.md", agents_text)

    def test_install_writes_three_platform_hard_gate_entrypoints(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        entry_files = [
            self.repo / "AGENTS.md",
            self.repo / "CLAUDE.md",
            self.repo / ".qoder" / "rules" / "harness-workflow.md",
            self.repo / ".qoder" / "commands" / "harness.md",
            self.repo / ".claude" / "commands" / "harness.md",
            self.repo / ".codex" / "skills" / "harness" / "SKILL.md",
        ]
        for path in entry_files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("WORKFLOW.md", text, msg=path.as_posix())
            self.assertIn(".workflow/context/index.md", text, msg=path.as_posix())
            self.assertIn(".workflow/state/runtime.yaml", text, msg=path.as_posix())
            self.assertIn("Hard Gate", text, msg=path.as_posix())
            self.assertIn("stop immediately", text, msg=path.as_posix())

    def test_update_does_not_restore_legacy_runtime_entrypoint(self) -> None:
        install = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(install.returncode, 0, msg=install.stderr or install.stdout)
        legacy_runtime = self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml"
        self.assertFalse(legacy_runtime.exists())

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertFalse(legacy_runtime.exists())

    def test_status_prefers_requirement_runtime_over_legacy_version_runtime(self) -> None:
        install = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(install.returncode, 0, msg=install.stderr or install.stdout)
        self.write_requirement_runtime(
            current_requirement="req-01",
            stage="acceptance",
            active_requirements=["req-01"],
        )
        legacy_runtime = self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml"
        legacy_runtime.parent.mkdir(parents=True, exist_ok=True)
        legacy_runtime.write_text(
            json.dumps(
                {
                    "current_version": "v0.2.0-refactor",
                    "conversation_mode": "harness",
                    "locked_version": "v0.2.0-refactor",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        result = self.run_cli("status", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("current_requirement: req-01", result.stdout)
        self.assertIn("stage: acceptance", result.stdout)
        self.assertIn("conversation_mode: open", result.stdout)
        self.assertNotIn("current_version:", result.stdout)

    def test_update_succeeds_on_existing_repo(self) -> None:
        install = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(install.returncode, 0, msg=install.stderr or install.stdout)

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".workflow" / "context" / "index.md").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "experience" / "tool" / "harness.md").exists())

    def test_language_command_switches_to_cn(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        result = self.run_cli("language", "cn", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        config = self.read_config()
        self.assertEqual(config["language"], "cn")
        self.assertIn("Language set to cn", result.stdout)

    @skip_legacy_version_flow
    def test_version_requirement_change_and_plan_use_version_container(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        version = self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(version.returncode, 0, msg=version.stderr or version.stdout)
        runtime = self.read_runtime()
        self.assertEqual(runtime["current_version"], "v1.0.0")
        self.assertEqual(runtime["conversation_mode"], "harness")
        self.assertEqual(runtime["locked_version"], "v1.0.0")

        requirement = self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "requirements" / "online-health-service"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertTrue((requirement_dir / "completion.md").exists())
        self.assertIn("startup", (requirement_dir / "completion.md").read_text(encoding="utf-8").lower())
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "requirement_review")
        self.assertEqual(meta["suggested_skill"], "brainstorming")
        self.assertTrue(meta["approval_required"])
        self.assertIn("Do not write production code", str(meta["assistant_prompt"]))
        runtime = self.read_runtime()
        self.assertEqual(runtime["conversation_mode"], "harness")
        self.assertEqual(runtime["locked_stage"], "requirement_review")
        self.assertEqual(runtime["locked_artifact_kind"], "requirement")
        self.assertEqual(runtime["locked_artifact_id"], "online-health-service")

        change = self.run_cli(
            "change",
            "Online Booking",
            "--root",
            str(self.repo),
            "--requirement",
            "online-health-service",
        )
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "changes" / "online-booking"
        self.assertTrue((change_dir / "change.md").exists())
        self.assertTrue((change_dir / "plan.md").exists())
        self.assertTrue((change_dir / "regression" / "required-inputs.md").exists())
        self.assertIn("mvn compile", (change_dir / "acceptance.md").read_text(encoding="utf-8"))
        changes_index = (requirement_dir / "changes.md").read_text(encoding="utf-8")
        self.assertIn("online-booking", changes_index)

        plan = self.run_cli("plan", "Online Booking", "--root", str(self.repo))
        self.assertEqual(plan.returncode, 0, msg=plan.stderr or plan.stdout)
        self.assertIn(".workflow/versions/active/v1.0.0/changes/online-booking/plan.md", plan.stdout)
        self.assertEqual(self.read_version_meta("v1.0.0")["suggested_skill"], "writing-plans")

    @unittest.skip("legacy version-flow status expectations were replaced by requirement-flow runtime routing")
    def test_use_status_next_and_ff_follow_workflow_runtime(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))

        status = self.run_cli("status", "--root", str(self.repo))
        self.assertEqual(status.returncode, 0, msg=status.stderr or status.stdout)
        self.assertIn("current_version: v1.0.0", status.stdout)
        self.assertIn("stage: requirement_review", status.stdout)
        self.assertIn("suggested_skill: brainstorming", status.stdout)
        self.assertIn("conversation_mode: harness", status.stdout)
        self.assertIn("locked_artifact_kind: requirement", status.stdout)

        next_result = self.run_cli("next", "--root", str(self.repo))
        self.assertEqual(next_result.returncode, 0, msg=next_result.stderr or next_result.stdout)
        self.assertIn("changes_review", next_result.stdout)
        self.assertEqual(self.read_version_meta("v1.0.0")["stage"], "changes_review")

        self.run_cli("change", "Online Booking", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.assertEqual(self.read_version_meta("v1.0.0")["stage"], "plan_review")

        ff_result = self.run_cli("ff", "--root", str(self.repo))
        self.assertEqual(ff_result.returncode, 0, msg=ff_result.stderr or ff_result.stdout)
        self.assertIn("ready_for_execution", ff_result.stdout)
        self.assertEqual(self.read_version_meta("v1.0.0")["stage"], "ready_for_execution")

    @unittest.skip("pre-existing version-flow gate behavior is outside this entrypoint migration")
    def test_done_stage_requires_verification_and_lesson_capture(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo), "--execute")
        result = self.run_cli("next", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "done")
        self.assertIn("session-memory.md", str(meta["assistant_prompt"]))
        self.assertIn("promoted", str(meta["assistant_prompt"]))
        self.assertIn("session-memory.md", str(meta["next_action"]))

    @skip_legacy_version_flow
    def test_use_switches_current_version(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        result = self.run_cli("use", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(self.read_runtime()["current_version"], "v1.0.0")

    def test_update_check_and_apply_refresh_qoder_skill_and_rule(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        qoder_skill = self.repo / ".qoder" / "skills" / "harness" / "SKILL.md"
        qoder_command = self.repo / ".qoder" / "commands" / "harness-requirement.md"
        claude_command = self.repo / ".claude" / "commands" / "harness-requirement.md"
        codex_wrapper = self.repo / ".codex" / "skills" / "harness-requirement" / "SKILL.md"
        qoder_rule = self.repo / ".qoder" / "rules" / "harness-workflow.md"
        context_index = self.repo / ".workflow" / "context" / "index.md"
        qoder_skill.write_text("tampered qoder skill\n", encoding="utf-8")
        qoder_command.unlink()
        claude_command.unlink()
        codex_wrapper.unlink()
        qoder_rule.unlink()
        context_index.unlink()

        check = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(check.returncode, 0, msg=check.stderr or check.stdout)
        self.assertIn("would refresh .qoder/skills/harness", check.stdout)
        self.assertIn("missing .qoder/commands/harness-requirement.md", check.stdout)
        self.assertIn("missing .claude/commands/harness-requirement.md", check.stdout)
        self.assertIn("missing .codex/skills/harness-requirement/SKILL.md", check.stdout)
        self.assertIn("missing .qoder/rules/harness-workflow.md", check.stdout)
        self.assertIn("missing .workflow/context/index.md", check.stdout)

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(qoder_command.exists())
        self.assertTrue(claude_command.exists())
        self.assertTrue(codex_wrapper.exists())
        self.assertTrue(qoder_rule.exists())
        self.assertTrue(context_index.exists())
        self.assertIn("# Harness", qoder_skill.read_text(encoding="utf-8"))

    @skip_legacy_version_flow
    def test_active_switches_current_version(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        result = self.run_cli("active", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Current active version set to v1.0.0", result.stdout)
        self.assertEqual(self.read_runtime()["current_version"], "v1.0.0")

    @skip_legacy_version_flow
    def test_enter_and_exit_toggle_harness_conversation_mode(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))

        exit_result = self.run_cli("exit", "--root", str(self.repo))
        self.assertEqual(exit_result.returncode, 0, msg=exit_result.stderr or exit_result.stdout)
        runtime = self.read_runtime()
        self.assertEqual(runtime["conversation_mode"], "open")
        self.assertEqual(runtime["locked_version"], "")
        self.assertEqual(runtime["locked_stage"], "")
        self.assertEqual(runtime["locked_artifact_kind"], "")
        self.assertEqual(runtime["locked_artifact_id"], "")

        enter_result = self.run_cli("enter", "--root", str(self.repo))
        self.assertEqual(enter_result.returncode, 0, msg=enter_result.stderr or enter_result.stdout)
        self.assertIn("Entered harness mode: v1.0.0 / requirement_review", enter_result.stdout)
        runtime = self.read_runtime()
        self.assertEqual(runtime["conversation_mode"], "harness")
        self.assertEqual(runtime["locked_version"], "v1.0.0")
        self.assertEqual(runtime["locked_stage"], "requirement_review")
        self.assertEqual(runtime["locked_artifact_kind"], "requirement")
        self.assertEqual(runtime["locked_artifact_id"], "online-health-service")

    @skip_legacy_version_flow
    def test_cn_language_uses_cn_templates_and_directories(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("language", "cn", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

        requirement = self.run_cli("requirement", "在线健康服务", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "需求" / "在线健康服务"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertIn("需求标题", (requirement_dir / "requirement.md").read_text(encoding="utf-8"))

        change = self.run_cli("change", "在线问诊预约", "--root", str(self.repo))
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "变更" / "在线问诊预约"
        self.assertTrue((change_dir / "change.md").exists())
        self.assertIn("变更标题", (change_dir / "change.md").read_text(encoding="utf-8"))

    @skip_legacy_version_flow
    def test_change_can_exist_without_requirement(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        change = self.run_cli("change", "Quick Login UI Fix", "--root", str(self.repo))
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "changes" / "quick-login-ui-fix"
        self.assertTrue((change_dir / "change.md").exists())

    @skip_legacy_version_flow
    def test_archive_moves_requirement_and_linked_changes_into_version_archive(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")

        result = self.run_cli("archive", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        archive_requirement = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "archive" / "online-health-service"
        self.assertTrue((archive_requirement / "requirement.md").exists())
        self.assertTrue((archive_requirement / "changes" / "online-booking" / "plan.md").exists())
        self.assertFalse((self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "requirements" / "online-health-service").exists())
        self.assertFalse((self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "changes" / "online-booking").exists())
        meta = self.read_version_meta("v1.0.0")
        self.assertNotIn("online-health-service", meta["requirement_ids"])
        self.assertNotIn("online-booking", meta["change_ids"])

    @unittest.skip("legacy regression status assertions target version-flow runtime output")
    def test_regression_flow_can_confirm_and_convert_into_change(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

        start = self.run_cli("regression", "Button effect is unsatisfactory", "--root", str(self.repo))
        self.assertEqual(start.returncode, 0, msg=start.stderr or start.stdout)
        regression_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "regressions" / "button-effect-is-unsatisfactory"
        self.assertTrue((regression_dir / "regression.md").exists())

        status = self.run_cli("status", "--root", str(self.repo))
        self.assertIn("mode: regression", status.stdout)
        self.assertIn("current_regression: button-effect-is-unsatisfactory", status.stdout)

        confirm = self.run_cli("regression", "--confirm", "--root", str(self.repo))
        self.assertEqual(confirm.returncode, 0, msg=confirm.stderr or confirm.stdout)

        convert = self.run_cli("regression", "--change", "Button Interaction Polish", "--root", str(self.repo))
        self.assertEqual(convert.returncode, 0, msg=convert.stderr or convert.stdout)
        change_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "changes" / "button-interaction-polish"
        self.assertTrue((change_dir / "change.md").exists())
        runtime = self.read_runtime()
        self.assertEqual(runtime["mode"], "normal")
        self.assertEqual(runtime["current_regression"], "")
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["regression_status"], "")
        self.assertEqual(meta["regression_ids"], [])
        regression_meta = (
            self.repo
            / ".workflow"
            / "versions"
            / "active"
            / "v1.0.0"
            / "regressions"
            / "button-effect-is-unsatisfactory"
            / "meta.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn('status: "converted"', regression_meta)
        self.assertIn('linked_change: "button-interaction-polish"', regression_meta)

    @skip_legacy_version_flow
    def test_rename_updates_version_and_requirement_links(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")

        version_result = self.run_cli("rename", "version", "v1.0.0", "release-1", "--root", str(self.repo))
        self.assertEqual(version_result.returncode, 0, msg=version_result.stderr or version_result.stdout)
        self.assertTrue((self.repo / ".workflow" / "versions" / "active" / "release-1").exists())
        self.assertEqual(self.read_runtime()["current_version"], "release-1")

        requirement_result = self.run_cli(
            "rename",
            "requirement",
            "Online Health Service",
            "Customer Health Service",
            "--root",
            str(self.repo),
        )
        self.assertEqual(requirement_result.returncode, 0, msg=requirement_result.stderr or requirement_result.stdout)
        requirement_dir = self.repo / ".workflow" / "versions" / "active" / "release-1" / "requirements" / "customer-health-service"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertFalse((self.repo / ".workflow" / "versions" / "active" / "release-1" / "requirements" / "online-health-service").exists())
        change_meta = (
            self.repo / ".workflow" / "versions" / "active" / "release-1" / "changes" / "online-booking" / "meta.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn('requirement: "customer-health-service"', change_meta)
        self.assertIn("customer-health-service", self.read_version_meta("release-1")["requirement_ids"])

    @unittest.skip("legacy update repair behavior targets version-flow runtime files")
    def test_update_repairs_manual_folder_renames(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")

        old_version = self.repo / ".workflow" / "versions" / "active" / "v1.0.0"
        new_version = self.repo / ".workflow" / "versions" / "active" / "release-1"
        shutil.move(str(old_version), str(new_version))
        shutil.move(
            str(new_version / "requirements" / "online-health-service"),
            str(new_version / "requirements" / "customer-health-service"),
        )
        shutil.move(
            str(new_version / "changes" / "online-booking"),
            str(new_version / "changes" / "customer-booking"),
        )

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(self.read_runtime()["current_version"], "release-1")
        self.assertEqual(self.read_config()["current_version"], "release-1")
        version_meta = self.read_version_meta("release-1")
        self.assertEqual(version_meta["id"], "release-1")
        self.assertIn("customer-health-service", version_meta["requirement_ids"])
        self.assertIn("customer-booking", version_meta["change_ids"])
        requirement_meta = (
            self.repo / ".workflow" / "versions" / "active" / "release-1" / "requirements" / "customer-health-service" / "meta.yaml"
        ).read_text(encoding="utf-8")
        change_meta = (
            self.repo / ".workflow" / "versions" / "active" / "release-1" / "changes" / "customer-booking" / "meta.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn('id: "customer-health-service"', requirement_meta)
        self.assertIn('id: "customer-booking"', change_meta)
        self.assertIn('requirement: "customer-health-service"', change_meta)

    @unittest.skip("legacy update rollback behavior targets version-flow runtime files")
    def test_update_rolls_back_when_current_version_directory_is_deleted(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        shutil.rmtree(self.repo / ".workflow" / "versions" / "active" / "v1.1.0")

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(self.read_config()["current_version"], "v1.0.0")
        self.assertEqual(self.read_runtime()["current_version"], "v1.0.0")

    @unittest.skip("legacy update rollback behavior targets version-flow runtime files")
    def test_update_rolls_back_deleted_requirement_and_change_state(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")
        self.run_cli("plan", "Online Booking", "--root", str(self.repo))

        shutil.rmtree(self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "changes" / "online-booking")
        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "requirement_review")
        self.assertEqual(meta["current_artifact_kind"], "requirement")
        self.assertEqual(meta["current_artifact_id"], "online-health-service")
        self.assertNotIn("online-booking", meta["change_ids"])

        shutil.rmtree(self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "requirements" / "online-health-service")
        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "idle")
        self.assertEqual(meta["current_artifact_kind"], "")
        self.assertEqual(meta["current_artifact_id"], "")
        self.assertEqual(meta["requirement_ids"], [])

    def test_update_check_and_apply_refresh_skills_and_missing_files(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        acceptance_role = self.repo / ".workflow" / "context" / "roles" / "acceptance.md"
        acceptance_role.unlink()
        codex_skill = self.repo / ".codex" / "skills" / "harness" / "SKILL.md"
        claude_skill = self.repo / ".claude" / "skills" / "harness" / "SKILL.md"
        codex_skill.write_text("tampered codex skill\n", encoding="utf-8")
        claude_skill.write_text("tampered claude skill\n", encoding="utf-8")

        check = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(check.returncode, 0, msg=check.stderr or check.stdout)
        self.assertIn("would refresh .codex/skills/harness", check.stdout)
        self.assertIn("would refresh .claude/skills/harness", check.stdout)
        self.assertIn("missing .workflow/context/roles/acceptance.md", check.stdout)
        self.assertFalse(acceptance_role.exists())

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(acceptance_role.exists())
        self.assertIn("# Harness", codex_skill.read_text(encoding="utf-8"))
        self.assertIn("# Harness", claude_skill.read_text(encoding="utf-8"))

    @unittest.skip("legacy update blockers target version-flow runtime repair")
    def test_update_reports_missing_active_version(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        (self.repo / ".codex" / "harness" / "config.json").write_text(
            json.dumps({"language": "english", "current_version": ""}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml").write_text(
            json.dumps({"current_version": "", "executing_version": "", "active_versions": {}}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

        result = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
        self.assertIn("workflow action required:", result.stdout)
        self.assertIn('harness active "v1.0.0"', result.stdout)

    @unittest.skip("legacy init expectations target the removed workflow-runtime entrypoint")
    def test_init_standalone_creates_docs_structure(self) -> None:
        result = self.run_cli("init", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".workflow" / "context").exists())
        self.assertTrue((self.repo / ".workflow" / "versions" / "active").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml").exists())

    @skip_legacy_version_flow
    def test_plan_with_nonexistent_change_fails(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        result = self.run_cli("plan", "No Such Change", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Change does not exist", result.stderr)

    @skip_legacy_version_flow
    def test_requirement_duplicate_title_is_idempotent(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        first = self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(first.returncode, 0, msg=first.stderr or first.stdout)
        second = self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(second.returncode, 0, msg=second.stderr or second.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["requirement_ids"].count("online-health-service"), 1)

    @skip_legacy_version_flow
    def test_change_duplicate_title_is_idempotent(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        first = self.run_cli("change", "Online Booking", "--root", str(self.repo))
        self.assertEqual(first.returncode, 0, msg=first.stderr or first.stdout)
        second = self.run_cli("change", "Online Booking", "--root", str(self.repo))
        self.assertEqual(second.returncode, 0, msg=second.stderr or second.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["change_ids"].count("online-booking"), 1)

    @skip_legacy_version_flow
    def test_regression_reject_clears_regression_state(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("regression", "Broken layout", "--root", str(self.repo))
        result = self.run_cli("regression", "--reject", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Regression rejected", result.stdout)
        runtime = self.read_runtime()
        self.assertEqual(runtime["mode"], "normal")
        self.assertEqual(runtime["current_regression"], "")
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["regression_status"], "")
        self.assertEqual(meta["current_regression"], "")
        self.assertNotIn("broken-layout", meta["regression_ids"])

    @skip_legacy_version_flow
    def test_regression_cancel_clears_regression_state(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("regression", "Broken layout", "--root", str(self.repo))
        result = self.run_cli("regression", "--cancel", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Regression cancelled", result.stdout)
        runtime = self.read_runtime()
        self.assertEqual(runtime["mode"], "normal")
        self.assertEqual(runtime["current_regression"], "")

    @skip_legacy_version_flow
    def test_regression_status_shows_active_regression(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("regression", "Broken layout", "--root", str(self.repo))
        result = self.run_cli("regression", "--status", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("current_regression: broken-layout", result.stdout)
        self.assertIn("regression_status: analysis", result.stdout)

    @skip_legacy_version_flow
    def test_next_from_idle_stage_fails_without_requirement(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        result = self.run_cli("next", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requirement", result.stderr.lower())

    @unittest.skip("pre-existing version-flow gate behavior is outside this entrypoint migration")
    def test_next_from_done_stage_fails(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo), "--execute")
        self.run_cli("next", "--root", str(self.repo))
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "done")
        result = self.run_cli("next", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)

    @skip_legacy_version_flow
    def test_enter_when_no_version_exists(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        result = self.run_cli("enter", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Entered harness mode", result.stdout)
        runtime = self.read_runtime()
        self.assertEqual(runtime["conversation_mode"], "harness")

    @skip_legacy_version_flow
    def test_rename_change_updates_version_meta(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")
        result = self.run_cli("rename", "change", "Online Booking", "Booking Revamp", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Change renamed", result.stdout)
        new_change_dir = self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "changes" / "booking-revamp"
        self.assertTrue((new_change_dir / "change.md").exists())
        self.assertFalse(
            (self.repo / ".workflow" / "versions" / "active" / "v1.0.0" / "changes" / "online-booking").exists()
        )
        meta = self.read_version_meta("v1.0.0")
        self.assertIn("booking-revamp", meta["change_ids"])
        self.assertNotIn("online-booking", meta["change_ids"])

    def test_language_with_invalid_value_fails(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        result = self.run_cli("language", "klingon", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported language", result.stderr)

    @skip_legacy_version_flow
    def test_active_with_nonexistent_version_fails(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        result = self.run_cli("active", "no-such-version", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Version does not exist", result.stderr)

    def test_installed_skill_uses_global_harness_commands(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        skill_text = (self.repo / ".codex" / "skills" / "harness" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("harness requirement", skill_text)
        self.assertNotIn("python3 scripts/harness.py", skill_text)
        self.assertIn(".workflow/state/runtime.yaml", skill_text)
        self.assertNotIn("python3 scripts/lint_harness_repo.py", skill_text)


    @skip_legacy_version_flow
    def test_feedback_collects_events_and_exports_json(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Test Req", "--root", str(self.repo))
        self.run_cli("next", "--root", str(self.repo))
        self.run_cli("change", "Test Change", "--root", str(self.repo))
        self.run_cli("ff", "--root", str(self.repo))

        # Should have recorded stage_advance and ff events
        feedback_log = self.repo / ".harness" / "feedback.jsonl"
        self.assertTrue(feedback_log.exists())
        lines = feedback_log.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreater(len(lines), 0)
        events = [json.loads(line) for line in lines]
        event_types = [e["event"] for e in events]
        self.assertIn("stage_advance", event_types)
        self.assertIn("ff", event_types)

        # Export feedback
        result = self.run_cli("feedback", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Feedback exported", result.stdout)

    @skip_legacy_version_flow
    def test_feedback_events_are_recorded_on_ff(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Test Req", "--root", str(self.repo))
        result = self.run_cli("ff", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        feedback_log = self.repo / ".harness" / "feedback.jsonl"
        self.assertTrue(feedback_log.exists(), "feedback.jsonl should exist after ff")
        lines = [line for line in feedback_log.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1, "At least one event should be recorded")
        events = [json.loads(line) for line in lines]
        event_types = [e["event"] for e in events]
        self.assertIn("stage_skip", event_types)
        self.assertIn("ff", event_types)
        skip_event = next(e for e in events if e["event"] == "stage_skip")
        self.assertIn("from_stage", skip_event["data"])

    @skip_legacy_version_flow
    def test_feedback_command_exports_summary(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Test Req", "--root", str(self.repo))
        self.run_cli("ff", "--root", str(self.repo))
        result = self.run_cli("feedback", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        out_path = self.repo / "harness-feedback.json"
        self.assertTrue(out_path.exists(), "harness-feedback.json should exist after feedback export")
        summary = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertIn("generated_at", summary)
        self.assertIn("project_hash", summary)
        self.assertIn("summary", summary)
        self.assertIn("stage_skips", summary["summary"])
        self.assertIn("events_total", summary)
        self.assertGreaterEqual(summary["events_total"], 1)

    def test_install_creates_core_workflow_files(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertFalse((self.repo / ".workflow" / "context" / "mcp-registry.yaml").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "index.md").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "roles" / "acceptance.md").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "experience" / "tool" / "harness.md").exists())

    @skip_legacy_version_flow
    def test_feedback_reset_clears_log(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Test Req", "--root", str(self.repo))
        self.run_cli("ff", "--root", str(self.repo))
        result = self.run_cli("feedback", "--reset", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        out_path = self.repo / "harness-feedback.json"
        self.assertTrue(out_path.exists())
        feedback_log = self.repo / ".harness" / "feedback.jsonl"
        self.assertTrue(feedback_log.exists())
        content = feedback_log.read_text(encoding="utf-8").strip()
        self.assertEqual(content, "", "Feedback log should be empty after reset")

    @unittest.skip("legacy init expectations target the removed workflow-runtime entrypoint")
    def test_init_creates_docs_without_skills(self) -> None:
        result = self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".workflow" / "context").exists())
        self.assertTrue((self.repo / ".workflow" / "versions" / "active").exists())
        self.assertTrue((self.repo / ".workflow" / "context" / "rules" / "workflow-runtime.yaml").exists())
        # init does NOT copy the full skill tree into .claude/skills/harness or .qoder/skills/harness
        self.assertFalse((self.repo / ".claude" / "skills" / "harness" / "SKILL.md").exists())
        self.assertFalse((self.repo / ".qoder" / "skills" / "harness" / "SKILL.md").exists())

    def test_version_requires_name(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        result = self.run_cli("version", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)

    def test_requirement_creates_workspace_when_missing(self) -> None:
        # create_requirement now auto-initializes workspace if missing
        result = self.run_cli("requirement", "Some Feature", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".workflow" / "state" / "runtime.yaml").exists())

    def test_change_requires_active_version(self) -> None:
        # Without install, the harness workspace does not exist, so change creation fails
        result = self.run_cli("change", "Some Change", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("harness", result.stderr.lower())

    @skip_legacy_version_flow
    def test_plan_requires_existing_change(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        result = self.run_cli("plan", "nonexistent", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Change does not exist", result.stderr)

    @skip_legacy_version_flow
    def test_next_from_idle_fails_without_requirement(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        result = self.run_cli("next", "--root", str(self.repo))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requirement", result.stderr.lower())

    @skip_legacy_version_flow
    def test_ff_skips_to_ready_for_execution_from_idle(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo))
        result = self.run_cli("ff", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("ready_for_execution", result.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "ready_for_execution")

    def test_language_aliases_accepted(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        for alias, expected in [("en", "english"), ("zh", "cn"), ("chinese", "cn")]:
            result = self.run_cli("language", alias, "--root", str(self.repo))
            self.assertEqual(result.returncode, 0, msg=f"Alias '{alias}' failed: {result.stderr or result.stdout}")
            config = self.read_config()
            self.assertEqual(config["language"], expected, msg=f"Alias '{alias}' should map to '{expected}'")


if __name__ == "__main__":
    unittest.main()
