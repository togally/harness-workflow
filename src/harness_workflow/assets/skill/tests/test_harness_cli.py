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

    def test_init_creates_harness_workspace(self) -> None:
        result = self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / "docs" / "requirements" / "active").exists())
        self.assertTrue((self.repo / "docs" / "changes" / "active").exists())
        self.assertTrue((self.repo / "docs" / "versions").exists())
        self.assertTrue((self.repo / "AGENTS.md").exists())
        self.assertTrue((self.repo / "CLAUDE.md").exists())

    def test_requirement_creates_requirement_workspace(self) -> None:
        self.run_cli("init", "--root", str(self.repo))
        result = self.run_cli(
            "requirement",
            "--root",
            str(self.repo),
            "--id",
            "pet-health",
            "--title",
            "在线健康服务",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        requirement_dir = self.repo / "docs" / "requirements" / "active" / "pet-health"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertTrue((requirement_dir / "meta.yaml").exists())
        self.assertTrue((requirement_dir / "changes.md").exists())

    def test_change_creates_change_workspace_and_links_requirement(self) -> None:
        self.run_cli("init", "--root", str(self.repo))
        self.run_cli(
            "requirement",
            "--root",
            str(self.repo),
            "--id",
            "pet-health",
            "--title",
            "在线健康服务",
        )
        result = self.run_cli(
            "change",
            "--root",
            str(self.repo),
            "--id",
            "pet-health-booking",
            "--title",
            "在线问诊预约",
            "--requirement",
            "pet-health",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        change_dir = self.repo / "docs" / "changes" / "active" / "pet-health-booking"
        self.assertTrue((change_dir / "change.md").exists())
        self.assertTrue((change_dir / "design.md").exists())
        self.assertTrue((change_dir / "plan.md").exists())
        self.assertTrue((change_dir / "session-memory.md").exists())
        changes_index = (self.repo / "docs" / "requirements" / "active" / "pet-health" / "changes.md").read_text(encoding="utf-8")
        self.assertIn("pet-health-booking", changes_index)

    def test_version_snapshots_active_workspaces(self) -> None:
        self.run_cli("init", "--root", str(self.repo))
        self.run_cli(
            "requirement",
            "--root",
            str(self.repo),
            "--id",
            "pet-health",
            "--title",
            "在线健康服务",
        )
        self.run_cli(
            "change",
            "--root",
            str(self.repo),
            "--id",
            "pet-health-booking",
            "--title",
            "在线问诊预约",
        )
        result = self.run_cli("version", "--root", str(self.repo), "--id", "v1.0.0")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        version_dir = self.repo / "docs" / "versions" / "v1.0.0"
        self.assertTrue((version_dir / "README.md").exists())
        self.assertTrue((version_dir / "snapshot" / "requirements" / "active" / "pet-health" / "requirement.md").exists())
        self.assertTrue((version_dir / "snapshot" / "changes" / "active" / "pet-health-booking" / "change.md").exists())

    def test_init_embeds_experience_capture_guidance(self) -> None:
        result = self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        workflow = (self.repo / "docs" / "context" / "rules" / "agent-workflow.md").read_text(encoding="utf-8")
        self.assertIn("被纠正时", workflow)
        self.assertIn("走不通的路", workflow)

        claude = (self.repo / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("经验沉淀", claude)

        index_text = (self.repo / "docs" / "context" / "experience" / "index.md").read_text(encoding="utf-8")
        self.assertIn("置信度规则", index_text)
        self.assertIn("高置信度", index_text)

        change = self.run_cli(
            "change",
            "--root",
            str(self.repo),
            "--id",
            "pet-health-booking",
            "--title",
            "在线问诊预约",
        )
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        session_memory = (
            self.repo / "docs" / "changes" / "active" / "pet-health-booking" / "session-memory.md"
        ).read_text(encoding="utf-8")
        self.assertIn("走不通的路", session_memory)
        self.assertIn("经验沉淀候选", session_memory)

    def test_update_check_and_apply_refresh_skill_and_missing_files(self) -> None:
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
        self.assertEqual(codex_skill.read_text(encoding="utf-8"), "tampered codex skill\n")
        self.assertEqual(claude_skill.read_text(encoding="utf-8"), "tampered claude skill\n")

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(session_memory.exists())
        self.assertIn("# Harness", codex_skill.read_text(encoding="utf-8"))
        self.assertIn("# Harness", claude_skill.read_text(encoding="utf-8"))

    def test_update_skips_modified_managed_files_unless_forced(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        workflow = self.repo / "docs" / "context" / "rules" / "agent-workflow.md"
        original = workflow.read_text(encoding="utf-8")
        workflow.write_text(original + "\n自定义修改\n", encoding="utf-8")

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("skipped modified docs/context/rules/agent-workflow.md", result.stdout)
        self.assertIn("自定义修改", workflow.read_text(encoding="utf-8"))

        forced = self.run_cli("update", "--root", str(self.repo), "--force-managed")
        self.assertEqual(forced.returncode, 0, msg=forced.stderr or forced.stdout)
        self.assertNotIn("自定义修改", workflow.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
