"""Tests for apply_all_suggestions path-slug + 原子顺序（req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 1.1）。

本文件覆盖 chg-01 change.md §5.1 + plan.md Step 1 的三条关键断言：

- test_case_a：`pack_title` 含全角括号 `（20条）` 时，apply-all 后 requirement.md
  必须包含 `## 合并建议清单` 段（即路径拼接正确、req_dir 能解析到、追加清单生效）。
- test_case_b：`pack_title` 含空格 / 单双引号 / 斜杠时同上。
- test_case_c：**原子化**保证——mock `req_md.write_text` 让其抛 OSError，断言
  sug body 文件 **不被删除**（失败时保留原文件）。

Helper 层直接调用 workflow_helpers 函数；tempdir 隔离；
monkey-patch `_get_git_branch` 固定为 `main`，避免依赖测试机 git 状态。
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
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime(root: Path) -> None:
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


def _seed_pending_suggestions(root: Path, count: int = 2) -> list[Path]:
    sug_dir = root / ".workflow" / "flow" / "suggestions"
    paths: list[Path] = []
    for i in range(1, count + 1):
        p = sug_dir / f"sug-0{i}-sample-{i}.md"
        p.write_text(
            f"---\nid: sug-0{i}\ntitle: \"样例标题 {i}\"\nstatus: pending\ncreated_at: 2026-04-21\npriority: medium\n---\n\n样例建议 {i} 正文\n",
            encoding="utf-8",
        )
        paths.append(p)
    return paths


class ApplyAllPathSlugTest(unittest.TestCase):
    """chg-01 Step 1.1：apply_all_suggestions path-slug bug + 原子顺序回归。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-applyall-"))
        self.root = _make_harness_workspace(self.tempdir)
        _write_runtime(self.root)
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

    # ---------- test_case_a: 全角括号 title ----------
    def test_apply_all_with_fullwidth_parens_keeps_list(self) -> None:
        """pack_title 含全角括号 `（20条）` 时，requirement.md 必须含合并建议清单。

        bug 活证：旧实现用 `f"{req_id}-{title}"` 未经 _path_slug 清洗，
        含 `（）` 会导致 req_dir 路径解析 miss；清单追加被静默跳过，
        但 sug body 照常 unlink —— 数据永久丢失。
        """
        from harness_workflow.workflow_helpers import apply_all_suggestions

        _seed_pending_suggestions(self.root, 2)
        pack_title = "批量建议合集（20条）"
        rc = apply_all_suggestions(self.root, pack_title=pack_title)

        self.assertEqual(rc, 0, "apply_all 应返回 0")

        # 定位生成的 req_dir（通过 glob artifacts/main/requirements/req-01-*）
        reqs_dir = self.root / "artifacts" / "main" / "requirements"
        candidates = sorted(reqs_dir.glob("req-01-*"))
        self.assertEqual(
            len(candidates),
            1,
            f"应存在恰好 1 个 req-01-* 目录，实际 {candidates}",
        )
        req_md = candidates[0] / "requirement.md"
        self.assertTrue(req_md.exists(), f"requirement.md 应存在于 {req_md}")
        text = req_md.read_text(encoding="utf-8")
        self.assertIn(
            "## 合并建议清单",
            text,
            "apply-all 应把 sug 清单追加到 requirement.md 末尾",
        )
        self.assertIn("sug-01", text)
        self.assertIn("sug-02", text)

    # ---------- test_case_b: 空格 / 特殊字符 title ----------
    def test_apply_all_with_special_chars_keeps_list(self) -> None:
        """pack_title 含空格 / 单双引号 / 斜杠时，apply-all 仍能追加清单。"""
        from harness_workflow.workflow_helpers import apply_all_suggestions

        _seed_pending_suggestions(self.root, 2)
        pack_title = "pack title / with 'special' and \"quotes\""
        rc = apply_all_suggestions(self.root, pack_title=pack_title)

        self.assertEqual(rc, 0, "apply_all 应返回 0")

        reqs_dir = self.root / "artifacts" / "main" / "requirements"
        candidates = sorted(reqs_dir.glob("req-01-*"))
        self.assertEqual(
            len(candidates),
            1,
            f"应存在恰好 1 个 req-01-* 目录，实际 {candidates}",
        )
        req_md = candidates[0] / "requirement.md"
        text = req_md.read_text(encoding="utf-8")
        self.assertIn(
            "## 合并建议清单",
            text,
            "含特殊字符的 pack_title 下 apply-all 仍必须追加清单",
        )

    # ---------- test_case_c: 原子顺序保护 ----------
    def test_apply_all_atomic_order_does_not_unlink_on_write_failure(self) -> None:
        """mock write_text 抛 OSError → 断言 sug body 文件不被 unlink。

        bug 活证：旧实现先写 `req_md.write_text(...)`，失败后仍照常进入
        `path.unlink()` 循环——body 物理删除。修复后应：写入原子 rename 失败
        时，返回非零、stderr 记录错误、且 sug body 保留完整。
        """
        from harness_workflow.workflow_helpers import apply_all_suggestions

        sug_paths = _seed_pending_suggestions(self.root, 2)
        pack_title = "atomic-test"

        # Patch Path.write_text 仅在 `.md.tmp` 路径上抛 OSError，模拟"req_md 创建后、
        # apply-all 合并清单的原子写入阶段"磁盘失败。修复方案要求写 tmp →
        # tmp.replace(req_md) 原子 rename；失败时不进入 unlink 循环。
        original_write_text = Path.write_text

        def failing_write_text(self, *a, **kw):  # noqa: ANN001
            if self.name.endswith(".md.tmp"):
                raise OSError("simulated disk failure")
            return original_write_text(self, *a, **kw)

        with mock.patch.object(Path, "write_text", new=failing_write_text):
            rc = apply_all_suggestions(self.root, pack_title=pack_title)

        # 期望：返回非零（写入失败中止 unlink），sug body 文件仍然存在
        self.assertNotEqual(rc, 0, "写入失败时 apply_all 应返回非零")
        for sp in sug_paths:
            self.assertTrue(
                sp.exists(),
                f"write_text 失败时 sug body 文件必须保留，实际被删: {sp}",
            )


if __name__ == "__main__":
    unittest.main()
