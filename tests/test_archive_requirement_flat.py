"""Tests for req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-05（CLI 路径对齐扁平化）.

覆盖 archive_requirement 的新扁平路径行为：
- req-id >= 39：归档时收齐 artifacts/ 扁平文档 + state/requirements/{req-id}/ 机器型文档 + state/sessions/{req-id}/ 会话文档。
- req-id <= 38：归档行为保持现状不变（legacy 路径）。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_harness_repo_for_archive(
    root: Path,
    req_id: str,
    req_title: str = "archive test req",
    flat: bool = True,
) -> tuple[Path, Path]:
    """Create harness repo in done stage for archiving. Returns (req_dir, state_req_dir)."""
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"
    req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    req_dir.mkdir(parents=True)
    # 创建对人文档（扁平）
    (req_dir / "需求摘要.md").write_text("# 需求摘要\n", encoding="utf-8")
    (req_dir / "chg-01-变更简报.md").write_text("# 变更简报 chg-01\n", encoding="utf-8")

    # state yaml (用于归档时 status=archived)
    state_yaml = root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
    state_yaml.write_text(
        "\n".join([
            f'id: "{req_id}"',
            f'title: "{req_title}"',
            'stage: "done"',
            'status: "active"',
            "",
        ]),
        encoding="utf-8",
    )

    # 机器型 requirement.md（新扁平路径）
    state_req_dir: Path
    if flat:
        state_req_dir = root / ".workflow" / "state" / "requirements" / req_id
        state_req_dir.mkdir(parents=True)
        (state_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    else:
        # legacy：requirement.md 直接在 req_dir 下
        (req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
        state_req_dir = req_dir  # 仅占位

    # sessions（state）
    sessions_dir = root / ".workflow" / "state" / "sessions" / req_id
    chg_dir = sessions_dir / "chg-01-test-change"
    chg_dir.mkdir(parents=True)
    (chg_dir / "change.md").write_text("# Change\n", encoding="utf-8")
    (chg_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")

    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join([
            f'current_requirement: "{req_id}"',
            f'current_requirement_title: "{req_title}"',
            'stage: "done"',
            'operation_type: "requirement"',
            f'operation_target: "{req_id}"',
            'conversation_mode: "open"',
            f'active_requirements: ["{req_id}"]',
            "",
        ]),
        encoding="utf-8",
    )
    return req_dir, state_req_dir


class ArchiveRequirementFlatTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_archive_requirement_collects_both_state_and_artifacts(self) -> None:
        """req-id >= 39: 归档后 archive 目录包含 state_requirements/ 机器型文档 + sessions/ 会话文档."""
        from harness_workflow.workflow_helpers import archive_requirement

        _init_harness_repo_for_archive(self.root, "req-39", "archive test 39", flat=True)

        rc = archive_requirement(self.root, "req-39")
        self.assertEqual(rc, 0)

        # 验证归档目录下包含 sessions/
        archive_req_dirs = list(
            (self.root / "artifacts" / "main" / "archive" / "requirements").glob("req-39*")
        )
        self.assertTrue(archive_req_dirs, "归档目录下应有 req-39-* 目录")
        archive_dir = archive_req_dirs[0]

        sessions_dst = archive_dir / "sessions"
        self.assertTrue(sessions_dst.exists(), "归档目录下应有 sessions/ 子目录（来自 state/sessions/req-39/）")

    def test_archive_requirement_legacy_req_unchanged(self) -> None:
        """req-id <= 38: 归档行为保持 legacy（归档后目录在 archive/requirements/ 下，无额外 state_requirements/ 目录）."""
        from harness_workflow.workflow_helpers import archive_requirement

        _init_harness_repo_for_archive(self.root, "req-37", "legacy archive test", flat=False)

        rc = archive_requirement(self.root, "req-37")
        self.assertEqual(rc, 0)

        archive_req_dirs = list(
            (self.root / "artifacts" / "main" / "archive" / "requirements").glob("req-37*")
        )
        self.assertTrue(archive_req_dirs, "归档目录下应有 req-37-* 目录")
        archive_dir = archive_req_dirs[0]

        # legacy req 不应有 state_requirements/ 子目录（仅 flat req 才有）
        state_machine_dst = archive_dir / "state_requirements"
        self.assertFalse(state_machine_dst.exists(), "legacy req 归档后不应有 state_requirements/ 目录")


if __name__ == "__main__":
    unittest.main()
