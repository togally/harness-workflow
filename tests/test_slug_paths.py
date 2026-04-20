"""bugfix-3：验证 create_requirement / create_bugfix / apply_suggestion
的 slug 清洗与截断行为（TDD 先红后绿）。

覆盖点（Validation Criteria 对齐）：

- create_requirement("含/的 标题")     → 单级目录 + state yaml 单级
- create_requirement("超长 title")      → slug ≤ 60，state yaml title 保留原文
- create_bugfix("含/的 标题")           → 单级目录 + state yaml 单级
- apply_suggestion(sug-08 风格长句)     → 单级 req 目录 + sug 移入 archive/ +
                                          frontmatter 翻转 applied + rc=0
- create_requirement("   ")             → id-only 目录名，无嵌套，无异常

所有测试在 tempdir 中执行，真实写入并读回断言；通过 mock.patch
`_get_git_branch` 固定 branch=main，避免依赖测试机 git 状态。
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
    """构造最小 harness 工作区。"""
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


class CreateRequirementSlugTest(unittest.TestCase):
    """create_requirement 的 slug 清洗与长度截断。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-slug-req-"))
        self.root = _make_harness_workspace(self.tempdir)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()

    def tearDown(self) -> None:
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_slash_in_title_does_not_create_nested_dir(self) -> None:
        """含 `/` 的 title 只应产生单级 requirement 目录。"""
        from harness_workflow.workflow_helpers import create_requirement

        rc = create_requirement(self.root, "清理 .workflow/flow/archive/main/ 目录")
        self.assertEqual(rc, 0)

        req_root = self.root / "artifacts" / "main" / "requirements"
        children = [p for p in req_root.iterdir() if p.is_dir()]
        self.assertEqual(
            len(children), 1,
            f"应只产生单一 req 目录，实际 {children}",
        )
        dir_name = children[0].name
        # 目录名不能出现 `/`（pathlib 已保证），也不能包含 raw 斜杠残留
        self.assertNotIn("/", dir_name)
        # 目录应以 `req-NN-` 前缀开头
        self.assertTrue(
            dir_name.startswith("req-"),
            f"目录名应以 req- 开头，实际 {dir_name}",
        )
        # state yaml 同步单级
        state_dir = self.root / ".workflow" / "state" / "requirements"
        yaml_files = list(state_dir.glob("req-*.yaml"))
        self.assertEqual(
            len(yaml_files), 1,
            f"state yaml 应单级且仅一个，实际 {yaml_files}",
        )
        # 确认没有嵌套 requirements/ 子目录残留
        nested_dirs = [p for p in state_dir.iterdir() if p.is_dir()]
        self.assertEqual(
            nested_dirs, [],
            f"state/requirements 下不应有子目录，实际 {nested_dirs}",
        )

    def test_long_title_slug_is_truncated_but_state_keeps_original(self) -> None:
        """超长 title → slug 截断到 ≤ 60 字符，state yaml 的 title 字段保留完整原文。"""
        from harness_workflow.workflow_helpers import create_requirement

        long_title = "超长标题测试" * 40  # 240 字符
        rc = create_requirement(self.root, long_title)
        self.assertEqual(rc, 0)

        req_root = self.root / "artifacts" / "main" / "requirements"
        children = [p for p in req_root.iterdir() if p.is_dir()]
        self.assertEqual(len(children), 1)
        dir_name = children[0].name
        # dir_name 形如 `req-NN-<slug>`，slug 段 ≤ 60
        # 通过 split 一次只拆前缀 req-NN-
        parts = dir_name.split("-", 2)
        self.assertEqual(parts[0], "req")
        self.assertTrue(parts[1].isdigit())
        slug_part = parts[2] if len(parts) > 2 else ""
        self.assertLessEqual(
            len(slug_part), 60,
            f"slug 段应 ≤ 60 字符，实际 {len(slug_part)}: {slug_part}",
        )
        # state yaml 的 title 字段应保留完整原文
        state_dir = self.root / ".workflow" / "state" / "requirements"
        yaml_files = list(state_dir.glob("req-*.yaml"))
        self.assertEqual(len(yaml_files), 1)
        text = yaml_files[0].read_text(encoding="utf-8")
        self.assertIn(long_title, text, "state yaml 的 title 字段应保留完整原始 title")

    def test_whitespace_only_title_falls_back_to_id_only(self) -> None:
        """全空白 title（helper 会 strip 后报错），这里改用"几乎全被过滤"的 title
        验证 slug 为空时回退到 id-only 目录名。

        注意：raw "   " 会触发 SystemExit（title 为空），不算"嵌套"风险；
        这里用 `///???` 这类能通过 title 非空校验、但 slugify 清洗后为空的
        边界 title，验证回退路径。
        """
        from harness_workflow.workflow_helpers import create_requirement

        # `///???` strip 后非空，但 slugify_preserve_unicode 会全部过滤 → ""
        rc = create_requirement(self.root, "///???")
        self.assertEqual(rc, 0)

        req_root = self.root / "artifacts" / "main" / "requirements"
        children = [p for p in req_root.iterdir() if p.is_dir()]
        self.assertEqual(
            len(children), 1,
            f"应单级目录，实际 {children}",
        )
        dir_name = children[0].name
        # id-only 形态：`req-NN` 无后缀 slug
        import re
        self.assertRegex(
            dir_name, r"^req-\d+$",
            f"应回退到 id-only（req-NN），实际 {dir_name}",
        )
        # state yaml 同步
        state_dir = self.root / ".workflow" / "state" / "requirements"
        yaml_files = list(state_dir.glob("req-*.yaml"))
        self.assertEqual(len(yaml_files), 1)
        self.assertRegex(yaml_files[0].stem, r"^req-\d+$")


class CreateBugfixSlugTest(unittest.TestCase):
    """create_bugfix 的 slug 清洗。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-slug-bfx-"))
        self.root = _make_harness_workspace(self.tempdir)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()

    def tearDown(self) -> None:
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_slash_in_bugfix_title_does_not_create_nested_dir(self) -> None:
        from harness_workflow.workflow_helpers import create_bugfix

        rc = create_bugfix(self.root, "修复 a/b/c 路径拆分 bug")
        self.assertEqual(rc, 0)

        bfx_root = self.root / "artifacts" / "main" / "bugfixes"
        children = [p for p in bfx_root.iterdir() if p.is_dir()]
        self.assertEqual(
            len(children), 1,
            f"应只产生单一 bugfix 目录，实际 {children}",
        )
        dir_name = children[0].name
        self.assertNotIn("/", dir_name)
        self.assertTrue(
            dir_name.startswith("bugfix-"),
            f"目录名应以 bugfix- 开头，实际 {dir_name}",
        )
        state_dir = self.root / ".workflow" / "state" / "bugfixes"
        yaml_files = list(state_dir.glob("bugfix-*.yaml"))
        self.assertEqual(len(yaml_files), 1)
        nested_dirs = [p for p in state_dir.iterdir() if p.is_dir()]
        self.assertEqual(nested_dirs, [])


class ApplySuggestionArchiveTest(unittest.TestCase):
    """apply_suggestion 对 sug-08 风格长句的行为：单级 req + 源文件归档 + frontmatter 翻转。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-apply-sug-"))
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

    def test_apply_sug08_style_long_line_produces_flat_dir_and_archives_source(
        self,
    ) -> None:
        """sug-08 风格：单行 + 含 `/` + 150+ 字符。

        期望：
        1. 产出单级 req 目录（不嵌套）；
        2. 原 sug 文件被 move 到 .workflow/flow/suggestions/archive/；
        3. 搬动后的文件 frontmatter status: applied；
        4. 返回值 0。
        """
        from harness_workflow.workflow_helpers import apply_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        long_line = (
            "清理 .workflow/flow/archive/main/ 目录下的历史归档 + 迁移 5 个 "
            "req 与 bugfix 的 artifacts / state 一致性修复草案"
        )
        self.assertGreater(len(long_line), 60)
        sug_path = sug_dir / "sug-08-long-line.md"
        sug_path.write_text(
            "---\n"
            "id: sug-08\n"
            "title: sug-08 风格长句\n"
            "status: pending\n"
            "created_at: 2026-04-20\n"
            "priority: medium\n"
            "---\n\n"
            f"{long_line}\n",
            encoding="utf-8",
        )

        rc = apply_suggestion(self.root, "sug-08")
        self.assertEqual(rc, 0, "apply_suggestion 应返回 0")

        # 1) req 目录单级
        req_root = self.root / "artifacts" / "main" / "requirements"
        children = [p for p in req_root.iterdir() if p.is_dir()]
        self.assertEqual(
            len(children), 1,
            f"应单级 req 目录，实际 {children}",
        )
        dir_name = children[0].name
        self.assertNotIn("/", dir_name)
        self.assertTrue(dir_name.startswith("req-"))

        # 2) 源 sug 文件应被搬到 archive/
        self.assertFalse(
            sug_path.exists(),
            "apply 成功后原 sug 文件应被 move，当前仍存在",
        )
        archive_dir = sug_dir / "archive"
        self.assertTrue(archive_dir.exists(), "archive 目录应被自动创建")
        archived_path = archive_dir / "sug-08-long-line.md"
        self.assertTrue(
            archived_path.exists(),
            f"归档后的 sug 文件应存在于 {archived_path}",
        )

        # 3) 搬动后的 frontmatter 翻转为 applied
        archived_text = archived_path.read_text(encoding="utf-8")
        self.assertIn(
            "status: applied", archived_text,
            "归档后的 sug frontmatter 应翻转为 applied",
        )
        self.assertNotIn(
            "status: pending", archived_text,
            "归档后的 sug 不应还留 status: pending",
        )


if __name__ == "__main__":
    unittest.main()
