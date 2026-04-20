"""bugfix-3：独立测试工程师补测（Subagent-L1, testing 阶段）。

test_slug_paths.py 覆盖了 5 条基础 Validation Criteria。本文件补充以下
边界，覆盖开发者单测遗漏但用户可复现的风险点：

- 反斜杠 `\\` 与 Windows 非法字符 `:*?"<>|` 在 title 中也不应污染路径；
- title 含 `\\n`（换行）时（例如被粘贴到 CLI 的多行建议首行），
  路径应单级、state yaml 不应被换行撑破；
- 同一 title 连续调用 create_requirement 两次，第二次应产生新 id
  且不崩溃；
- apply_suggestion 对 **无 frontmatter** 的历史 sug 文件仍应归档（filename
  fallback 路径）。

与 test_slug_paths.py 同源的 tempdir + mock.patch 风格，确保真实写入读回。
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(
            [
                'operation_type: "requirement"',
                'operation_target: ""',
                'current_requirement: ""',
                'stage: "done"',
                'conversation_mode: "open"',
                'locked_requirement: ""',
                'locked_stage: ""',
                'current_regression: ""',
                "ff_mode: false",
                "ff_stage_history: []",
                "active_requirements: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root


class ExtraEdgeCaseTest(unittest.TestCase):
    """独立补测：反斜杠 / Windows 非法字符 / 换行 / 幂等 / 无 frontmatter sug。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-slug-extra-"))
        self.root = _make_harness_workspace(self.tempdir)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()
        self._input_patch = mock.patch("builtins.input", return_value="n")
        self._input_patch.start()

    def tearDown(self) -> None:
        self._input_patch.stop()
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_backslash_and_windows_illegal_chars_in_title(self) -> None:
        """含反斜杠与 Windows 非法字符的 title 仍应单级、无残留非法字符。"""
        from harness_workflow.workflow_helpers import create_requirement

        # 全部 POSIX + Windows 非法字符一次性塞进 title
        rc = create_requirement(self.root, 'a\\b:c*d?e"f<g>h|i 标题')
        self.assertEqual(rc, 0)

        req_root = self.root / "artifacts" / "main" / "requirements"
        children = [p for p in req_root.iterdir() if p.is_dir()]
        self.assertEqual(len(children), 1, f"应单级目录，实际 {children}")
        dir_name = children[0].name
        # 所有非法字符都不应出现在目录名
        for bad in '\\:*?"<>|/':
            self.assertNotIn(
                bad, dir_name,
                f"目录名不应含非法字符 {bad!r}，实际 {dir_name}",
            )
        # state yaml 也应单级
        state_dir = self.root / ".workflow" / "state" / "requirements"
        yaml_files = list(state_dir.glob("req-*.yaml"))
        self.assertEqual(len(yaml_files), 1)
        self.assertEqual([p for p in state_dir.iterdir() if p.is_dir()], [])

    def test_newline_in_title_does_not_create_multiple_paths(self) -> None:
        """title 含 `\\n` 时 create_requirement 应单级目录。

        触发路径：用户（或上游工具）意外把多行字符串直接当 title 传入，
        `_path_slug` 会把 `\\n` 当非法字符折叠为 `-`，不应出现多行路径。
        """
        from harness_workflow.workflow_helpers import create_requirement

        multi = "第一行 title\n第二行噪声\n第三行"
        rc = create_requirement(self.root, multi)
        self.assertEqual(rc, 0)

        req_root = self.root / "artifacts" / "main" / "requirements"
        children = [p for p in req_root.iterdir() if p.is_dir()]
        self.assertEqual(len(children), 1, f"应单级目录，实际 {children}")
        dir_name = children[0].name
        self.assertNotIn("\n", dir_name)
        # 目录名不应是 "第一行 title" 单独一行（证明换行真被折叠）
        self.assertTrue(dir_name.startswith("req-"))
        # state yaml 的 title 保留原文完整多行
        state_dir = self.root / ".workflow" / "state" / "requirements"
        yaml_files = list(state_dir.glob("req-*.yaml"))
        self.assertEqual(len(yaml_files), 1)
        # state yaml title 字段序列化后原换行应保留或可还原（至少首行出现）
        text = yaml_files[0].read_text(encoding="utf-8")
        self.assertIn("第一行 title", text)

    def test_repeated_create_requirement_produces_new_ids(self) -> None:
        """同一 title 连续调用两次 create_requirement 应产生不同 id，第二次不崩溃。"""
        from harness_workflow.workflow_helpers import create_requirement

        rc1 = create_requirement(self.root, "重复 title 测试")
        self.assertEqual(rc1, 0)
        rc2 = create_requirement(self.root, "重复 title 测试")
        self.assertEqual(rc2, 0)

        req_root = self.root / "artifacts" / "main" / "requirements"
        children = sorted(p.name for p in req_root.iterdir() if p.is_dir())
        self.assertEqual(
            len(children), 2,
            f"两次调用应得到两个独立目录，实际 {children}",
        )
        # id 应不同（req-NN 段）
        ids = {c.split("-", 2)[1] for c in children}
        self.assertEqual(len(ids), 2, f"两次调用 id 应不同，实际 {ids}")

    def test_apply_suggestion_on_legacy_sug_without_frontmatter(self) -> None:
        """无 frontmatter 的历史 sug 文件：apply 应按 filename fallback 命中，
        归档到 archive/（即使没有 status: pending 可翻转也应迁移）。"""
        from harness_workflow.workflow_helpers import apply_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        sug_path = sug_dir / "sug-42-legacy-no-frontmatter.md"
        # 纯 markdown，无 YAML frontmatter
        sug_path.write_text(
            "# 历史遗留建议\n\n建议内容正文，不含 frontmatter。\n",
            encoding="utf-8",
        )

        rc = apply_suggestion(self.root, "sug-42")
        self.assertEqual(rc, 0, "filename fallback 应命中并返回 0")

        # 源文件应被搬走
        self.assertFalse(
            sug_path.exists(),
            "apply 后历史 sug 源文件应被 move 到 archive",
        )
        archived = sug_dir / "archive" / "sug-42-legacy-no-frontmatter.md"
        self.assertTrue(
            archived.exists(),
            f"归档后文件应在 {archived}",
        )
        # 无 frontmatter 时 status 翻转是 no-op（文本里没有 pending 可替换），
        # 但文件本身必须被搬走且内容完好
        archived_text = archived.read_text(encoding="utf-8")
        self.assertIn("历史遗留建议", archived_text)


if __name__ == "__main__":
    unittest.main()
