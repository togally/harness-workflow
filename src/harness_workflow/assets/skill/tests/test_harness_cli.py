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


if __name__ == "__main__":
    unittest.main()
