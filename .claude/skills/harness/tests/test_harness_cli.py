import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CLI = SKILL_ROOT / "scripts" / "harness.py"
COMMAND_SAMPLES = ["harness", "harness-requirement", "harness-change", "harness-next"]

_SKIP_VERSION = "Legacy version-centric test: version concept removed in req-02/chg-07"


class HarnessCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-skill-test-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(CLI), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def read_config(self) -> dict[str, str]:
        return json.loads((self.repo / ".codex" / "harness" / "config.json").read_text(encoding="utf-8"))

    @unittest.skip(_SKIP_VERSION)
    def test_init_creates_harness_workspace_and_default_language(self) -> None:
        result = self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / "workflow" / "versions" / "active").exists())
        self.assertEqual(self.read_config()["language"], "english")
        self.assertTrue((self.repo / "workflow" / "context" / "rules" / "workflow-runtime.yaml").exists())

    @unittest.skip(_SKIP_VERSION)
    def test_language_version_requirement_change_and_plan_flow(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("language", "cn", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

        requirement = self.run_cli("requirement", "在线健康服务", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / "workflow" / "versions" / "active" / "v1.0.0" / "需求" / "在线健康服务"
        self.assertTrue((requirement_dir / "requirement.md").exists())

    @unittest.skip(_SKIP_VERSION)
    def test_use_and_status_follow_runtime(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        use_result = self.run_cli("use", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(use_result.returncode, 0, msg=use_result.stderr or use_result.stdout)

    @unittest.skip(_SKIP_VERSION)
    def test_done_stage_requires_verification_and_lesson_capture(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))

    @unittest.skip(_SKIP_VERSION)
    def test_enter_and_exit_toggle_harness_conversation_mode(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        exit_result = self.run_cli("exit", "--root", str(self.repo))
        self.assertEqual(exit_result.returncode, 0, msg=exit_result.stderr or exit_result.stdout)

    @unittest.skip(_SKIP_VERSION)
    def test_active_switches_current_version(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        result = self.run_cli("active", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    @unittest.skip(_SKIP_VERSION)
    def test_update_check_and_apply_refresh_skills_and_missing_files(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")

    @unittest.skip(_SKIP_VERSION)
    def test_archive_moves_requirement_and_linked_changes_into_version_archive(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.run_cli("change", "Online Booking", "--root", str(self.repo), "--requirement", "online-health-service")
        result = self.run_cli("archive", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    @unittest.skip(_SKIP_VERSION)
    def test_regression_flow_can_confirm_and_convert_into_change(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        start = self.run_cli("regression", "Button effect is unsatisfactory", "--root", str(self.repo))
        self.assertEqual(start.returncode, 0, msg=start.stderr or start.stdout)

    @unittest.skip(_SKIP_VERSION)
    def test_rename_updates_version_and_requirement_links(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

    @unittest.skip(_SKIP_VERSION)
    def test_update_repairs_manual_folder_renames(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

    @unittest.skip(_SKIP_VERSION)
    def test_update_rolls_back_when_current_version_directory_is_deleted(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

    @unittest.skip(_SKIP_VERSION)
    def test_update_rolls_back_deleted_requirement_and_change_state(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

    @unittest.skip(_SKIP_VERSION)
    def test_update_reports_missing_active_version(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

    def test_installed_skill_uses_global_harness_commands(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("harness requirement", skill_text)
        self.assertNotIn("python3 scripts/harness.py", skill_text)
        self.assertIn("python3 tools/lint_harness_repo.py", skill_text)
        self.assertNotIn("python3 scripts/lint_harness_repo.py", skill_text)


if __name__ == "__main__":
    unittest.main()
