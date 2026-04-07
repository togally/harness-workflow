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

    def test_version_snapshots_docs(self) -> None:
        self.run_cli("install", "--root", str(self.repo))
        self.run_cli("requirement", "--root", str(self.repo), "--id", "pet-health", "--title", "在线健康服务")
        result = self.run_cli("version", "--root", str(self.repo), "--id", "v1.0.0")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / "docs" / "versions" / "v1.0.0" / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
