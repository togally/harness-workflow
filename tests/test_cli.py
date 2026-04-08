import shutil
import subprocess
import sys
import tempfile
import unittest
import os
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

    def test_install_creates_skill_and_workspace(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / ".codex" / "skills" / "harness" / "SKILL.md").exists())
        self.assertTrue((self.repo / "docs" / "requirements" / "active").exists())
        self.assertTrue((self.repo / "AGENTS.md").exists())
        self.assertTrue((self.repo / "CLAUDE.md").exists())

    def test_requirement_and_change_flow(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        req = self.run_cli("requirement", "--root", str(self.repo), "--id", "pet-health", "--title", "在线健康服务")
        self.assertEqual(req.returncode, 0, msg=req.stderr or req.stdout)
        change = self.run_cli(
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
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        self.assertTrue((self.repo / "docs" / "changes" / "active" / "pet-health-booking" / "plan.md").exists())

    def test_install_embeds_experience_capture_guidance(self) -> None:
        result = self.run_cli("install", "--root", str(self.repo))
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

    def test_version_snapshots_docs(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("requirement", "--root", str(self.repo), "--id", "pet-health", "--title", "在线健康服务")
        result = self.run_cli("version", "--root", str(self.repo), "--id", "v1.0.0")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / "docs" / "versions" / "v1.0.0" / "README.md").exists())

    def test_update_check_and_apply_refresh_skill_and_missing_files(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        session_memory = self.repo / "docs" / "templates" / "session-memory.md"
        session_memory.unlink()
        skill_file = self.repo / ".codex" / "skills" / "harness" / "SKILL.md"
        skill_file.write_text("tampered skill\n", encoding="utf-8")

        check = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(check.returncode, 0, msg=check.stderr or check.stdout)
        self.assertIn("would refresh .codex/skills/harness", check.stdout)
        self.assertIn("missing docs/templates/session-memory.md", check.stdout)
        self.assertFalse(session_memory.exists())
        self.assertEqual(skill_file.read_text(encoding="utf-8"), "tampered skill\n")

        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(session_memory.exists())
        self.assertIn("# Harness", skill_file.read_text(encoding="utf-8"))

    def test_update_skips_modified_managed_files_unless_forced(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
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
