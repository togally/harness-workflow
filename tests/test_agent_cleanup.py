"""chg-B：清掉 kimi/qoder 支持 — 测试套件

TC-01  cli.py install --agent choices 仅含 cc/codex（不含 kimi/qoder）
TC-02  platforms.yaml scaffold_v2 仅含 cc/codex
TC-03  不存在 kimi.md / qoder.md / qoder-*.tmpl 文件
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class AgentChoicesTest(unittest.TestCase):
    """TC-01: cli.py install --agent choices 仅含 cc/codex。"""

    def test_install_agent_choices_only_cc_codex(self) -> None:
        """install --agent 的 choices 列表不得含 kimi 或 qoder。"""
        from harness_workflow.cli import build_parser
        parser = build_parser()
        # 找到 install 子命令的 --agent 参数
        install_parser = None
        for action in parser._subparsers._group_actions:
            for choice_name, choice_parser in action.choices.items():
                if choice_name == "install":
                    install_parser = choice_parser
                    break
        self.assertIsNotNone(install_parser, "install 子命令应存在")

        agent_action = None
        for action in install_parser._actions:
            if hasattr(action, "option_strings") and "--agent" in action.option_strings:
                agent_action = action
                break
        self.assertIsNotNone(agent_action, "--agent 参数应存在")

        choices = agent_action.choices
        self.assertIsNotNone(choices, "--agent 应有 choices 列表")
        self.assertIn("cc", choices, "choices 应含 cc")
        self.assertIn("codex", choices, "choices 应含 codex")
        self.assertNotIn("kimi", choices, "choices 不得含 kimi（已移除）")
        self.assertNotIn("qoder", choices, "choices 不得含 qoder（已移除）")


class PlatformsYamlTest(unittest.TestCase):
    """TC-02: platforms.yaml scaffold_v2 仅含 cc/codex。"""

    def test_scaffold_v2_platforms_yaml_only_cc_codex(self) -> None:
        """scaffold_v2 的 platforms.yaml 应只包含 cc 和 codex。"""
        import yaml
        platforms_path = (
            REPO_ROOT
            / "src" / "harness_workflow" / "assets" / "scaffold_v2"
            / ".workflow" / "state" / "platforms.yaml"
        )
        self.assertTrue(platforms_path.exists(), "scaffold_v2 platforms.yaml 应存在")
        data = yaml.safe_load(platforms_path.read_text(encoding="utf-8")) or {}
        enabled = data.get("enabled", [])
        self.assertIn("cc", enabled, "platforms.yaml enabled 应含 cc")
        self.assertIn("codex", enabled, "platforms.yaml enabled 应含 codex")
        self.assertNotIn("kimi", enabled, "platforms.yaml enabled 不得含 kimi（已移除）")
        self.assertNotIn("qoder", enabled, "platforms.yaml enabled 不得含 qoder（已移除）")


class RemovedFilesTest(unittest.TestCase):
    """TC-03: 不存在 kimi.md / qoder.md / qoder-*.tmpl 文件。"""

    def test_kimi_md_does_not_exist(self) -> None:
        """agent/kimi.md 应已被删除。"""
        kimi_md = (
            REPO_ROOT / "src" / "harness_workflow" / "skills" / "harness" / "agent" / "kimi.md"
        )
        self.assertFalse(kimi_md.exists(), f"kimi.md 应已删除，但仍存在：{kimi_md}")

    def test_qoder_md_does_not_exist(self) -> None:
        """agent/qoder.md 应已被删除。"""
        qoder_md = (
            REPO_ROOT / "src" / "harness_workflow" / "skills" / "harness" / "agent" / "qoder.md"
        )
        self.assertFalse(qoder_md.exists(), f"qoder.md 应已删除，但仍存在：{qoder_md}")

    def test_qoder_templates_do_not_exist(self) -> None:
        """qoder-*.tmpl 模板文件应已被全部删除。"""
        templates_dir = (
            REPO_ROOT / "src" / "harness_workflow" / "assets" / "skill" / "assets" / "templates"
        )
        qoder_tmpls = list(templates_dir.glob("qoder-*.tmpl"))
        self.assertEqual(
            len(qoder_tmpls),
            0,
            f"qoder-*.tmpl 应已全部删除，但仍有：{[str(p) for p in qoder_tmpls]}",
        )


if __name__ == "__main__":
    unittest.main()
