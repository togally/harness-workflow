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

    def read_runtime(self) -> dict[str, object]:
        return json.loads((self.repo / "docs" / "context" / "rules" / "workflow-runtime.yaml").read_text(encoding="utf-8"))

    def read_version_meta(self, version: str) -> dict[str, object]:
        return json.loads(
            (self.repo / "docs" / "versions" / "active" / version / "meta.yaml").read_text(encoding="utf-8")
        )

    def test_init_creates_harness_workspace_and_default_language(self) -> None:
        result = self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue((self.repo / "docs" / "versions" / "active").exists())
        self.assertEqual(self.read_config()["language"], "english")
        self.assertTrue((self.repo / "docs" / "context" / "rules" / "workflow-runtime.yaml").exists())

    def test_language_version_requirement_change_and_plan_flow(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("language", "cn", "--root", str(self.repo))
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))

        requirement = self.run_cli("requirement", "在线健康服务", "--root", str(self.repo))
        self.assertEqual(requirement.returncode, 0, msg=requirement.stderr or requirement.stdout)
        requirement_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "需求" / "在线健康服务"
        self.assertTrue((requirement_dir / "requirement.md").exists())
        self.assertEqual(self.read_version_meta("v1.0.0")["suggested_skill"], "brainstorming")

        change = self.run_cli("change", "在线问诊预约", "--root", str(self.repo), "--requirement", "在线健康服务")
        self.assertEqual(change.returncode, 0, msg=change.stderr or change.stdout)
        change_dir = self.repo / "docs" / "versions" / "active" / "v1.0.0" / "变更" / "在线问诊预约"
        self.assertTrue((change_dir / "plan.md").exists())

        plan = self.run_cli("plan", "在线问诊预约", "--root", str(self.repo))
        self.assertEqual(plan.returncode, 0, msg=plan.stderr or plan.stdout)
        self.assertIn("docs/versions/active/v1.0.0/变更/在线问诊预约/plan.md", plan.stdout)
        self.assertEqual(self.read_version_meta("v1.0.0")["suggested_skill"], "writing-plans")

        next_result = self.run_cli("next", "--root", str(self.repo))
        self.assertEqual(next_result.returncode, 0, msg=next_result.stderr or next_result.stdout)
        self.assertEqual(self.read_version_meta("v1.0.0")["stage"], "ready_for_execution")

    def test_use_and_status_follow_runtime(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        use_result = self.run_cli("use", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(use_result.returncode, 0, msg=use_result.stderr or use_result.stdout)
        self.assertEqual(self.read_runtime()["current_version"], "v1.0.0")
        status = self.run_cli("status", "--root", str(self.repo))
        self.assertEqual(status.returncode, 0, msg=status.stderr or status.stdout)
        self.assertIn("current_version: v1.0.0", status.stdout)
        self.assertIn("suggested_skill:", status.stdout)

    def test_active_switches_current_version(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
        self.run_cli("version", "v1.0.0", "--root", str(self.repo))
        self.run_cli("version", "v1.1.0", "--root", str(self.repo))
        result = self.run_cli("active", "v1.0.0", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Current active version set to v1.0.0", result.stdout)
        self.assertEqual(self.read_runtime()["current_version"], "v1.0.0")

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

    def test_update_reports_missing_active_version(self) -> None:
        self.run_cli("init", "--root", str(self.repo), "--write-agents", "--write-claude")
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
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("harness requirement", skill_text)
        self.assertNotIn("python3 scripts/harness.py", skill_text)
        self.assertIn("python3 tools/lint_harness_repo.py", skill_text)
        self.assertNotIn("python3 scripts/lint_harness_repo.py", skill_text)


if __name__ == "__main__":
    unittest.main()
