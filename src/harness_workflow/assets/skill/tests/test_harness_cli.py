import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CLI = SKILL_ROOT / "scripts" / "harness.py"


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

    def test_init_creates_harness_workspace_and_default_language(self) -> None:
        result = self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / "docs" / "versions" / "active").exists())
        self.assertEqual(self.read_config()["language"], "english")

    def test_language_version_requirement_change_and_plan_flow(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("language", "cn", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

        requirement = self.run_cli("requirement", "在线健康服务", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "需求" / "在线健康服务"
        self.assertTrue((requirement_dir / "requirement.md").exists())

        change = self.run_cli("change", "在线问诊预约", "--root", str(self.repo), "--requirement", "在线健康服务")
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "变更" / "在线问诊预约"
        self.assertTrue((change_dir / "plan.md").exists())

        plan = self.run_cli("plan", "在线问诊预约", "--root", str(self.repo))
        self.assertEqual(plan.returncode, 0, msg=plan.stderr or plan.stdout)
        self.assertIn("docs/versions/active/v1.0.0/变更/在线问诊预约/plan.md", plan.stdout)

    def test_update_check_and_apply_refresh_skills_and_missing_files(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        session_memory = self.repo / "docs" / "templates" / "session-memory.md"
        session_memory.unlink()
        codex_skill = self.repo / ".codex" / "skills" / "harness" / "SKILL.md"
        claude_skill = self.repo / ".claude" / "skills" / "harness" / "SKILL.md"
        codex_skill.parent.mkdir(parents=True, exist_ok=True)
        claude_skill.parent.mkdir(parents=True, exist_ok=True)
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
