"""Unit tests for `archive_requirement` 路径拼接（req-26 / chg-04）。

覆盖 AC-05：
- `harness archive` 生成的归档路径中每个 `{branch}` 段只出现一次，
  不得出现 `archive/main/main/...` 这类双层 branch；
- 对已存在的历史双层 branch 路径保持不动（Excluded 的历史清洗）。

Helper 层直接调用 `archive_requirement`，不跑真 CLI（briefing 硬约束）。
tempdir 隔离；通过 monkey-patch `_get_git_branch` 固定 branch 为 `main`，
避免依赖真实 git 仓库状态。
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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    """构造最小 harness 工作区，布局对齐 chg-03 test 基线。"""
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime(root: Path, *, current_requirement: str = "", active_ids: list[str] | None = None) -> None:
    active_ids = active_ids or []
    lines = [
        'operation_type: "requirement"',
        'operation_target: ""',
        f'current_requirement: "{current_requirement}"',
        'stage: "done"',
        'conversation_mode: "open"',
        'locked_requirement: ""',
        'locked_stage: ""',
        'current_regression: ""',
        "ff_mode: false",
        "ff_stage_history: []",
    ]
    if active_ids:
        lines.append("active_requirements:")
        for aid in active_ids:
            lines.append(f"  - {aid}")
    else:
        lines.append("active_requirements: []")
    lines.append("")
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def _seed_requirement_dir(root: Path, folder_name: str) -> Path:
    """在 `artifacts/main/requirements/` 下放一个可归档的 requirement 目录。"""
    req_dir = root / "artifacts" / "main" / "requirements" / folder_name
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "requirement.md").write_text(
        f"# {folder_name}\n\nseed content\n", encoding="utf-8"
    )
    (req_dir / "changes").mkdir(parents=True, exist_ok=True)
    return req_dir


def _seed_requirement_state(root: Path, req_id: str, slug: str, title: str) -> Path:
    state_path = (
        root / ".workflow" / "state" / "requirements" / f"{req_id}-{slug}.yaml"
    )
    _write(
        state_path,
        "\n".join(
            [
                f'id: "{req_id}"',
                f'title: "{title}"',
                'stage: "done"',
                'status: "active"',
                'created_at: "2026-04-19"',
                'started_at: "2026-04-19"',
                'completed_at: "2026-04-19"',
                "stage_timestamps: {}",
                'description: ""',
                "",
            ]
        ),
    )
    return state_path


class ArchivePathTest(unittest.TestCase):
    """AC-05：`harness archive` 归档路径不得出现双层 branch。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-archive-path-"))
        self.root = _make_harness_workspace(self.tempdir)
        # Patch `_get_git_branch` 固定为 "main"，避免依赖测试机 git 状态
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()
        # Patch input/subprocess 避免 Git commit 交互
        self._input_patch = mock.patch("builtins.input", return_value="n")
        self._input_patch.start()

    def tearDown(self) -> None:
        self._input_patch.stop()
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_archive_path_no_double_branch(self) -> None:
        """新归档路径：`artifacts/main/archive/requirements/req-xx-.../`，branch 段只出现一次。

        bug 活证：旧代码会产出 `artifacts/main/archive/main/req-xx`（双层 main）。
        修复后，primary 形态下 archive_base 已含 branch，不再拼第二层。

        req-28 / chg-03（AC-14）：归档按 id 前缀分流到 ``requirements/`` 或
        ``bugfixes/`` 子树。req-* 落到 ``archive/requirements/<dir>``。
        """
        from harness_workflow.workflow_helpers import archive_requirement

        folder_name = "req-99-demo-archive"
        _seed_requirement_dir(self.root, folder_name)
        _seed_requirement_state(self.root, "req-99", "demo-archive", "Demo Archive")
        _write_runtime(
            self.root,
            current_requirement="req-99",
            active_ids=["req-99"],
        )

        rc = archive_requirement(self.root, folder_name)
        self.assertEqual(rc, 0)

        archive_root = self.root / "artifacts" / "main" / "archive"
        self.assertTrue(archive_root.exists(), "archive root 应存在")

        # 关键断言 1：目标目录在 `archive/requirements/req-99-.../`
        expected_target = archive_root / "requirements" / folder_name
        self.assertTrue(
            expected_target.exists(),
            f"归档目标应在 {expected_target}，目录树: "
            f"{[p.relative_to(self.root).as_posix() for p in archive_root.rglob('*') if p.is_dir()]}",
        )

        # 关键断言 2：archive 下不得出现 `main/` 子目录（双层 branch 征兆）
        double_branch = archive_root / "main"
        self.assertFalse(
            double_branch.exists(),
            f"不得产生双层 branch 路径 {double_branch.relative_to(self.root).as_posix()}",
        )

        # 关键断言 3：归档目标路径字符串中 `main` 段只出现一次
        target_rel = expected_target.relative_to(self.root).as_posix()
        self.assertEqual(
            target_rel.count("/main/"),
            1,
            f"归档路径 {target_rel} 中 `/main/` 段应只出现一次",
        )

    def test_archive_path_preserves_legacy(self) -> None:
        """历史 `archive/main/main/...` 目录存在时，新归档不得破坏它（Excluded）。

        预置历史脏数据 `artifacts/main/archive/main/req-88-legacy/`，
        然后对新 req 执行 archive：
        - 历史目录必须原封不动；
        - 新目录落到 `artifacts/main/archive/req-77-new/`，不复用旧的双层路径。
        """
        from harness_workflow.workflow_helpers import archive_requirement

        # 预置历史双层 branch 脏数据
        legacy_dir = (
            self.root / "artifacts" / "main" / "archive" / "main" / "req-88-legacy"
        )
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_marker = legacy_dir / "MARKER.txt"
        legacy_marker.write_text("do-not-touch", encoding="utf-8")

        # 准备新归档对象
        folder_name = "req-77-new-archive"
        _seed_requirement_dir(self.root, folder_name)
        _seed_requirement_state(self.root, "req-77", "new-archive", "New Archive")
        _write_runtime(
            self.root,
            current_requirement="req-77",
            active_ids=["req-77"],
        )

        rc = archive_requirement(self.root, folder_name)
        self.assertEqual(rc, 0)

        archive_root = self.root / "artifacts" / "main" / "archive"

        # 断言 1：历史脏目录及标记文件保持不动
        self.assertTrue(legacy_dir.exists(), "历史双层 branch 目录不得被删除")
        self.assertTrue(legacy_marker.exists(), "历史标记文件不得被删除")
        self.assertEqual(
            legacy_marker.read_text(encoding="utf-8"),
            "do-not-touch",
            "历史标记文件内容不得被改写",
        )

        # 断言 2：新归档落到单层 branch 路径下（req-28 / chg-03：归到 requirements/ 子树）
        new_target = archive_root / "requirements" / folder_name
        self.assertTrue(
            new_target.exists(),
            f"新归档目标应在 {new_target.relative_to(self.root).as_posix()}",
        )

        # 断言 3：新归档不得被错误复用到双层 branch 路径下
        wrong_target = archive_root / "main" / folder_name
        self.assertFalse(
            wrong_target.exists(),
            f"新归档不得落到双层 branch 路径 {wrong_target.relative_to(self.root).as_posix()}",
        )


if __name__ == "__main__":
    unittest.main()
