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

    def test_install_creates_dual_skills_and_default_english_config(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".codex" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / ".claude" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / "docs" / "context").exists())
        self.assertTrue((self.repo / "docs" / "versions" / "active").exists())
        self.assertEqual(self.read_config()["language"], "english")

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

        requirement = self.run_cli("requirement", "Online Health Service", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "requirements" / "online-health-service"
        self.assertTrue((requirement_dir / "requirement.md").exists())

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
        changes_index = (requirement_dir / "changes.md").read_text(encoding="utf-8")
        self.assertIn("online-booking", changes_index)

        plan = self.run_cli("plan", "Online Booking", "--root", str(self.repo))
        self.assertEqual(plan.returncode, 0, msg=plan.stderr or plan.stdout)
        self.assertIn("docs/versions/active/v1.0.0/changes/online-booking/plan.md", plan.stdout)

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


if __name__ == "__main__":
    unittest.main()
