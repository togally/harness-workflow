"""Tests updated for bugfix-11 方向C（废弃三段式分水岭）.

原测试覆盖 archive_requirement 的 state-flat (req-id >= 39) 和 legacy (req-id <= 38) 行为。
bugfix-11 方向C 废弃三段式分水岭后：
- 所有 req 一律走 flow layout
- archive_requirement 对所有 req（含原 req-37/38/39/40）走 flow layout 路径：
  .workflow/flow/requirements/{slug}/ → .workflow/flow/archive/main/{slug}/
  对人 folder（artifacts/main/requirements/{slug}/）原位保留
- 不再产 artifacts/archive/ 路径（flow req 走 flow/archive）
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
) -> tuple[Path, Path]:
    """Create harness repo in done stage for archiving. Returns (artifacts_req_dir, flow_req_dir)."""
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "flow" / "archive").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    # 对人 folder（artifacts/main/requirements/）
    artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    artifacts_req_dir.mkdir(parents=True)
    (artifacts_req_dir / "需求摘要.md").write_text("# 需求摘要\n", encoding="utf-8")
    (artifacts_req_dir / "chg-01-变更简报.md").write_text("# 变更简报 chg-01\n", encoding="utf-8")

    # state yaml
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

    # 机器型 flow folder（方向C 权威路径）
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_req_dir.mkdir(parents=True)
    (flow_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    changes_dir = flow_req_dir / "changes"
    changes_dir.mkdir(parents=True)
    chg_dir = changes_dir / "chg-01-test-change"
    chg_dir.mkdir(parents=True)
    (chg_dir / "change.md").write_text("# Change\n", encoding="utf-8")

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
    return artifacts_req_dir, flow_req_dir


class ArchiveRequirementFlatTest(unittest.TestCase):
    """bugfix-11 方向C: 所有 req（含原 state-flat / legacy 区间）归档走 flow layout."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_archive_requirement_collects_both_state_and_artifacts(self) -> None:
        """方向C: req-39 归档后 flow/archive 有机器型文档 + 对人 folder 原位保留（flow layout 行为）."""
        from harness_workflow.workflow_helpers import archive_requirement

        artifacts_req_dir, flow_req_dir = _init_harness_repo_for_archive(
            self.root, "req-39", "archive test 39"
        )

        rc = archive_requirement(self.root, "req-39")
        self.assertEqual(rc, 0)

        # 方向C: 机器型文档迁到 flow/archive/main/
        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode("archive test 39") or "archive-test-39"
        dir_name = f"req-39-{slug}"
        flow_archive_dir = self.root / ".workflow" / "flow" / "archive" / "main" / dir_name
        self.assertTrue(
            flow_archive_dir.exists(),
            f"方向C: 机器型文档应迁到 flow/archive/main/{dir_name}，但未找到",
        )
        self.assertTrue(
            (flow_archive_dir / "requirement.md").exists(),
            "flow archive 目录应含 requirement.md",
        )

        # 对人 folder 原位保留（方向C）
        self.assertTrue(
            artifacts_req_dir.exists(),
            "方向C: 对人 folder 应原位保留，不应被迁走",
        )

    def test_archive_requirement_legacy_req_unchanged(self) -> None:
        """方向C: req-37（原 legacy 区间）也走 flow layout，归档到 flow/archive/main/ + 对人 folder 原位."""
        from harness_workflow.workflow_helpers import archive_requirement

        artifacts_req_dir, flow_req_dir = _init_harness_repo_for_archive(
            self.root, "req-37", "legacy archive test"
        )

        rc = archive_requirement(self.root, "req-37")
        self.assertEqual(rc, 0)

        # 方向C: req-37 也走 flow layout（废弃 legacy 分支）
        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode("legacy archive test") or "legacy-archive-test"
        dir_name = f"req-37-{slug}"
        flow_archive_dir = self.root / ".workflow" / "flow" / "archive" / "main" / dir_name
        self.assertTrue(
            flow_archive_dir.exists(),
            f"方向C: req-37 也应归档到 flow/archive/main/{dir_name}",
        )

        # 对人 folder 原位保留
        self.assertTrue(
            artifacts_req_dir.exists(),
            "方向C: 对人 folder 应原位保留（不迁走）",
        )

        # 旧路径 artifacts/archive/ 下不应有该 req
        old_archive_base = self.root / "artifacts" / "main" / "archive" / "requirements"
        old_archived = list(old_archive_base.glob("req-37-*")) if old_archive_base.exists() else []
        self.assertEqual(
            old_archived,
            [],
            "方向C: artifacts/archive/requirements/ 下不应有 req-37（方向C 废弃 legacy 路径）",
        )


if __name__ == "__main__":
    unittest.main()
