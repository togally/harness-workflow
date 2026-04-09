import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


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
        return json.loads((self.repo / "docs" / "context" / "rules" / "workflow-runtime.yaml").read_text(encoding="utf-8"))

    def read_version_meta(self, version: str) -> dict[str, object]:
        return json.loads(
            (self.repo / "docs" / "versions" / "active" / version / "meta.yaml").read_text(encoding="utf-8")
        )

    def test_install_creates_triple_skills_and_default_english_config(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".codex" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / ".claude" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / ".qoder" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / ".qoder" / "commands" / "harness.md").exists())
        self.assertTrue((self.repo / ".qoder" / "rules" / "harness-workflow.md").exists())
        self.assertTrue((self.repo / "docs" / "context").exists())
        self.assertTrue((self.repo / "docs" / "versions" / "active").exists())
        self.assertEqual(self.read_config()["language"], "english")
        self.assertTrue((self.repo / "docs" / "context" / "rules" / "workflow-runtime.yaml").exists())
        self.assertTrue((self.repo / "docs" / "context" / "rules" / "development-flow.md").exists())

    def test_language_command_switches_to_cn(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        result = self.run_cli("language", "cn", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        config = self.read_config()
        self.assertEqual(config["language"], "cn")
        self.assertIn("Language set to cn", result.stdout)

    def test_version_requirement_change_and_plan_use_version_container(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        version = self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(version.returncode, 0, msg=version.stderr or version.stdout)
        runtime = self.read_runtime()
        self.assertEqual(runtime["current_version"], "v1.0.0")

        requirement = self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "requirements" / "online-health-service"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertTrue((requirement_dir / "completion.md").exists())
        self.assertIn("startup", (requirement_dir / "completion.md").read_text(encoding="utf-8").lower())
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "requirement_review")
        self.assertEqual(meta["suggested_skill"], "brainstorming")

        change = self.run_cli(
            "change",
            "Online Booking",
            "--root",
            str(self.repo),
            "--requirement",
            "online-health-service",
        )
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "changes" / "online-booking"
        self.assertTrue((change_dir / "change.md").exists())
        self.assertTrue((change_dir / "plan.md").exists())
        self.assertTrue((change_dir / "regression" / "required-inputs.md").exists())
        self.assertIn("mvn compile", (change_dir / "acceptance.md").read_text(encoding="utf-8"))
        changes_index = (requirement_dir / "changes.md").read_text(encoding="utf-8")
        self.assertIn("online-booking", changes_index)

        plan = self.run_cli("plan", "Online Booking", "--root", str(self.repo))
        self.assertEqual(plan.returncode, 0, msg=plan.stderr or plan.stdout)
        self.assertIn("docs/versions/active/v1.0.0/changes/online-booking/plan.md", plan.stdout)
        self.assertEqual(self.read_version_meta("v1.0.0")["suggested_skill"], "writing-plans")

    def test_use_status_next_and_ff_follow_workflow_runtime(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))

        status = self.run_cli("status", "--root", str(self.repo))
        self.assertEqual(status.returncode, 0, msg=status.stderr or status.stdout)
        self.assertIn("current_version: v1.0.0", status.stdout)
        self.assertIn("stage: requirement_review", status.stdout)
        self.assertIn("suggested_skill: brainstorming", status.stdout)

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
        qoder_command = self.repo / ".qoder" / "commands" / "harness.md"
        qoder_rule = self.repo / ".qoder" / "rules" / "harness-workflow.md"
        qoder_skill.write_text("tampered qoder skill\n", encoding="utf-8")
        qoder_command.unlink()
        qoder_rule.unlink()

        check = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(check.returncode, 0, msg=check.stderr or check.stdout)
        self.assertIn("would refresh .qoder/skills/harness", check.stdout)
        self.assertIn("missing .qoder/commands/harness.md", check.stdout)
        self.assertIn("missing .qoder/rules/harness-workflow.md", check.stdout)

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(qoder_command.exists())
        self.assertTrue(qoder_rule.exists())
        self.assertIn("# Harness", qoder_skill.read_text(encoding="utf-8"))

    def test_active_switches_current_version(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        result = self.run_cli("active", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Current active version set to v1.0.0", result.stdout)
        self.assertEqual(self.read_runtime()["current_version"], "v1.0.0")

    def test_cn_language_uses_cn_templates_and_directories(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("language", "cn", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

        requirement = self.run_cli("requirement", "在线健康服务", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "需求" / "在线健康服务"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertIn("需求标题", (requirement_dir / "requirement.md").read_text(encoding="utf-8"))

        change = self.run_cli("change", "在线问诊预约", "--root", str(self.repo))
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "变更" / "在线问诊预约"
        self.assertTrue((change_dir / "change.md").exists())
        self.assertIn("变更标题", (change_dir / "change.md").read_text(encoding="utf-8"))

    def test_change_can_exist_without_requirement(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        change = self.run_cli("change", "Quick Login UI Fix", "--root", str(self.repo))
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "changes" / "quick-login-ui-fix"
        self.assertTrue((change_dir / "change.md").exists())

    def test_archive_moves_requirement_and_linked_changes_into_version_archive(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")

        result = self.run_cli("archive", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        archive_requirement = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "archive" / "online-health-service"
        self.assertTrue((archive_requirement / "requirement.md").exists())
        self.assertTrue((archive_requirement / "changes" / "online-booking" / "plan.md").exists())
        self.assertFalse((self.repo / "docs" / "versions" / "active" / "v1.0.0" / "requirements" / "online-health-service").exists())
        self.assertFalse((self.repo / "docs" / "versions" / "active" / "v1.0.0" / "changes" / "online-booking").exists())
        meta = self.read_version_meta("v1.0.0")
        self.assertNotIn("online-health-service", meta["requirement_ids"])
        self.assertNotIn("online-booking", meta["change_ids"])

    def test_regression_flow_can_confirm_and_convert_into_change(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

        start = self.run_cli("regression", "Button effect is unsatisfactory", "--root", str(self.repo))
        self.assertEqual(start.returncode, 0, msg=start.stderr or start.stdout)
        regression_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "regressions" / "button-effect-is-unsatisfactory"
        self.assertTrue((regression_dir / "regression.md").exists())

        status = self.run_cli("status", "--root", str(self.repo))
        self.assertIn("mode: regression", status.stdout)
        self.assertIn("current_regression: button-effect-is-unsatisfactory", status.stdout)

        confirm = self.run_cli("regression", "--confirm", "--root", str(self.repo))
        self.assertEqual(confirm.returncode, 0, msg=confirm.stderr or confirm.stdout)

        convert = self.run_cli("regression", "--change", "Button Interaction Polish", "--root", str(self.repo))
        self.assertEqual(convert.returncode, 0, msg=convert.stderr or convert.stdout)
        change_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "changes" / "button-interaction-polish"
        self.assertTrue((change_dir / "change.md").exists())
        runtime = self.read_runtime()
        self.assertEqual(runtime["mode"], "normal")
        self.assertEqual(runtime["current_regression"], "")
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["regression_status"], "")
        self.assertEqual(meta["regression_ids"], [])
        regression_meta = (
            self.repo
            / "docs"
            / "versions"
            / "active"
            / "v1.0.0"
            / "regressions"
            / "button-effect-is-unsatisfactory"
            / "meta.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn('status: "converted"', regression_meta)
        self.assertIn('linked_change: "button-interaction-polish"', regression_meta)

    def test_rename_updates_version_and_requirement_links(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")

        version_result = self.run_cli("rename", "version", "v1.0.0", "release-1", "--root", str(self.repo))
        self.assertEqual(version_result.returncode, 0, msg=version_result.stderr or version_result.stdout)
        self.assertTrue((self.repo / "docs" / "versions" / "active" / "release-1").exists())
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
        requirement_dir = self.repo / "docs" / "versions" / "active" / "release-1" / "requirements" / "customer-health-service"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertFalse((self.repo / "docs" / "versions" / "active" / "release-1" / "requirements" / "online-health-service").exists())
        change_meta = (
            self.repo / "docs" / "versions" / "active" / "release-1" / "changes" / "online-booking" / "meta.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn('requirement: "customer-health-service"', change_meta)
        self.assertIn("customer-health-service", self.read_version_meta("release-1")["requirement_ids"])

    def test_update_repairs_manual_folder_renames(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")

        old_version = self.repo / "docs" / "versions" / "active" / "v1.0.0"
        new_version = self.repo / "docs" / "versions" / "active" / "release-1"
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
            self.repo / "docs" / "versions" / "active" / "release-1" / "requirements" / "customer-health-service" / "meta.yaml"
        ).read_text(encoding="utf-8")
        change_meta = (
            self.repo / "docs" / "versions" / "active" / "release-1" / "changes" / "customer-booking" / "meta.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn('id: "customer-health-service"', requirement_meta)
        self.assertIn('id: "customer-booking"', change_meta)
        self.assertIn('requirement: "customer-health-service"', change_meta)

    def test_update_rolls_back_when_current_version_directory_is_deleted(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        shutil.rmtree(self.repo / "docs" / "versions" / "active" / "v1.1.0")

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(self.read_config()["current_version"], "v1.0.0")
        self.assertEqual(self.read_runtime()["current_version"], "v1.0.0")

    def test_update_rolls_back_deleted_requirement_and_change_state(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")
        self.run_cli("plan", "Online Booking", "--root", str(self.repo))

        shutil.rmtree(self.repo / "docs" / "versions" / "active" / "v1.0.0" / "changes" / "online-booking")
        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "requirement_review")
        self.assertEqual(meta["current_artifact_kind"], "requirement")
        self.assertEqual(meta["current_artifact_id"], "online-health-service")
        self.assertNotIn("online-booking", meta["change_ids"])

        shutil.rmtree(self.repo / "docs" / "versions" / "active" / "v1.0.0" / "requirements" / "online-health-service")
        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        meta = self.read_version_meta("v1.0.0")
        self.assertEqual(meta["stage"], "idle")
        self.assertEqual(meta["current_artifact_kind"], "")
        self.assertEqual(meta["current_artifact_id"], "")
        self.assertEqual(meta["requirement_ids"], [])

    def test_update_check_and_apply_refresh_skills_and_missing_files(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        session_memory = self.repo / "docs" / "templates" / "session-memory.md"
        session_memory.unlink()
        codex_skill = self.repo / ".codex" / "skills" / "harness" / "SKILL.md"
        claude_skill = self.repo / ".claude" / "skills" / "harness" / "SKILL.md"
        codex_skill.write_text("tampered codex skill\n", encoding="utf-8")
        claude_skill.write_text("tampered claude skill\n", encoding="utf-8")

        check = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(check.returncode, 0, msg=check.stderr or check.stdout)
        self.assertIn("would refresh .codex/skills/harness", check.stdout)
        self.assertIn("would refresh .claude/skills/harness", check.stdout)
        self.assertIn("missing docs/templates/session-memory.md", check.stdout)
        self.assertFalse(session_memory.exists())

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(session_memory.exists())
        self.assertIn("# Harness", codex_skill.read_text(encoding="utf-8"))
        self.assertIn("# Harness", claude_skill.read_text(encoding="utf-8"))

    def test_update_reports_missing_active_version(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        (self.repo / ".codex" / "harness" / "config.json").write_text(
            json.dumps({"language": "english", "current_version": ""}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.repo / "docs" / "context" / "rules" / "workflow-runtime.yaml").write_text(
            json.dumps({"current_version": "", "executing_version": "", "active_versions": {}}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

        result = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
        self.assertIn("workflow action required:", result.stdout)
        self.assertIn('harness active "v1.0.0"', result.stdout)

    def test_installed_skill_uses_global_harness_commands(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        skill_text = (self.repo / ".codex" / "skills" / "harness" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("harness requirement", skill_text)
        self.assertNotIn("python3 scripts/harness.py", skill_text)
        self.assertIn("python3 tools/lint_harness_repo.py", skill_text)
        self.assertNotIn("python3 scripts/lint_harness_repo.py", skill_text)


if __name__ == "__main__":
    unittest.main()
