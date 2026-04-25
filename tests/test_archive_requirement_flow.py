"""Tests for req-42（archive 重定义：对人不挪 + 摘要废止）/ chg-02（archive_requirement helper 改写）.

AC-1: flow req（req-id >= 42）归档后 artifacts/main/requirements/{slug}/ 原位仍存在。
AC-2: 归档后不产出 {req-id}-{slug}.md 摘要文件；generate_requirement_artifact 已从源码删除。
AC-3: 归档后 .workflow/flow/archive/main/{slug}/ 存在含 requirement.md / changes/ 等机器型子树。
legacy fallback: req-id <= 38 仍走旧路径（folder 搬到 artifacts/{branch}/archive/requirements/{slug}/）。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_flow_req_for_archive(
    root: Path,
    req_id: str,
    req_title: str = "archive flow test",
) -> tuple[Path, Path]:
    """构造 req-id >= 41 的 flow req fixture，供 archive_requirement 测试使用。

    返回 (artifacts_req_dir, flow_req_dir)：
    - artifacts_req_dir: artifacts/main/requirements/{req_id}-{slug}/（对人 folder）
    - flow_req_dir:      .workflow/flow/requirements/{req_id}-{slug}/（机器型 folder）
    """
    from harness_workflow.slug import slugify_preserve_unicode

    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    # 基础目录
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

    # 对人 folder（artifacts/main/requirements/{dir_name}/）
    artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    artifacts_req_dir.mkdir(parents=True)
    (artifacts_req_dir / "交付总结.md").write_text("# 交付总结\n", encoding="utf-8")
    (artifacts_req_dir / "chg-01-变更简报.md").write_text("# 变更简报 chg-01\n", encoding="utf-8")

    # 机器型 folder（.workflow/flow/requirements/{dir_name}/）
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_req_dir.mkdir(parents=True)
    (flow_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    changes_dir = flow_req_dir / "changes"
    changes_dir.mkdir(parents=True)
    chg01 = changes_dir / "chg-01-test-change"
    chg01.mkdir(parents=True)
    (chg01 / "change.md").write_text("# Change\n", encoding="utf-8")
    (chg01 / "plan.md").write_text("# Plan\n", encoding="utf-8")
    sessions_dir = flow_req_dir / "sessions"
    sessions_dir.mkdir(parents=True)
    sess_chg01 = sessions_dir / "chg-01-test-change"
    sess_chg01.mkdir(parents=True)
    (sess_chg01 / "session-memory.md").write_text("# Session Memory\n", encoding="utf-8")

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

    # runtime.yaml
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


class ArchiveRequirementFlowSmoke(unittest.TestCase):
    """AC-1 / AC-2 / AC-3 smoke：req-42 flow req 归档行为验证。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_archive_requirement_req_42_smoke(self) -> None:
        """AC-1+AC-2+AC-3: req-42 归档后对人 folder 原位 + 无摘要 md + flow/archive 有机器型副本。"""
        from harness_workflow.workflow_helpers import archive_requirement

        artifacts_req_dir, _ = _init_flow_req_for_archive(
            self.root, "req-42", "archive-重定义-对人不挪-摘要废止"
        )

        rc = archive_requirement(self.root, "req-42")
        self.assertEqual(rc, 0)

        # AC-1: 对人 folder 原位仍存在
        self.assertTrue(
            artifacts_req_dir.exists(),
            f"AC-1 失败：对人 folder 应原位保留，但 {artifacts_req_dir} 不存在",
        )
        self.assertTrue(
            (artifacts_req_dir / "交付总结.md").exists(),
            "AC-1 失败：对人 folder 内容应完整保留",
        )

        # AC-2: 顶层无摘要 md 文件（不产出 req-42-xxx.md）
        top_level_mds = list(
            (self.root / "artifacts" / "main" / "requirements").glob("req-42-*.md")
        )
        self.assertEqual(
            top_level_mds,
            [],
            f"AC-2 失败：不应产出摘要 md 文件，但发现 {top_level_mds}",
        )

        # AC-3: .workflow/flow/archive/main/{slug}/ 存在含机器型子树
        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode("archive-重定义-对人不挪-摘要废止") or "archive-重定义-对人不挪-摘要废止"
        dir_name = f"req-42-{slug}"
        flow_archive_dir = self.root / ".workflow" / "flow" / "archive" / "main" / dir_name
        self.assertTrue(
            flow_archive_dir.exists(),
            f"AC-3 失败：flow archive 目录应存在，但 {flow_archive_dir} 不存在",
        )
        self.assertTrue(
            (flow_archive_dir / "requirement.md").exists(),
            "AC-3 失败：flow archive 目录应含 requirement.md",
        )
        self.assertTrue(
            (flow_archive_dir / "changes").exists(),
            "AC-3 失败：flow archive 目录应含 changes/ 子树",
        )

        # AC-3: .workflow/flow/requirements/{slug}/ 不再存在（已迁走）
        flow_req_original = self.root / ".workflow" / "flow" / "requirements" / dir_name
        self.assertFalse(
            flow_req_original.exists(),
            f"AC-3 失败：flow/requirements 下原目录应已迁走，但 {flow_req_original} 仍存在",
        )

    def test_archive_requirement_req_41_flow_behavior(self) -> None:
        """req-41 也走 flow 路径：对人 folder 原位 + 无摘要 md + flow/archive 有机器型副本。"""
        from harness_workflow.workflow_helpers import archive_requirement

        artifacts_req_dir, _ = _init_flow_req_for_archive(
            self.root, "req-41", "机器型工件回flow"
        )

        rc = archive_requirement(self.root, "req-41")
        self.assertEqual(rc, 0)

        # 对人 folder 原位
        self.assertTrue(artifacts_req_dir.exists(), "req-41 对人 folder 应原位保留")

        # 无摘要 md
        top_mds = list((self.root / "artifacts" / "main" / "requirements").glob("req-41-*.md"))
        self.assertEqual(top_mds, [], f"req-41 不应产出摘要 md，但发现 {top_mds}")

        # flow/archive 存在
        flow_archive_base = self.root / ".workflow" / "flow" / "archive" / "main"
        flow_archive_dirs = list(flow_archive_base.glob("req-41-*"))
        self.assertTrue(flow_archive_dirs, "req-41 flow archive 目录应存在")

    def test_archive_requirement_legacy_fallback(self) -> None:
        """legacy（req-id <= 38）仍走旧路径：folder 搬到 artifacts/{branch}/archive/requirements/。"""
        from harness_workflow.workflow_helpers import archive_requirement

        # 使用 test_archive_requirement_flat.py 中相同的 legacy fixture 初始化方式
        _init_legacy_req_for_archive(self.root, "req-37", "legacy fallback test")

        rc = archive_requirement(self.root, "req-37")
        self.assertEqual(rc, 0)

        # legacy: archive 目录存在
        archive_req_dirs = list(
            (self.root / "artifacts" / "main" / "archive" / "requirements").glob("req-37*")
        )
        self.assertTrue(archive_req_dirs, "legacy req-37 应归档到 artifacts/main/archive/requirements/")

        # legacy: flow/archive 不存在（legacy 走旧路径）
        flow_archive_base = self.root / ".workflow" / "flow" / "archive" / "main"
        flow_archive_dirs = list(flow_archive_base.glob("req-37-*")) if flow_archive_base.exists() else []
        self.assertEqual(flow_archive_dirs, [], "legacy req-37 不应出现在 flow/archive 下")


def _init_legacy_req_for_archive(
    root: Path,
    req_id: str,
    req_title: str = "legacy test req",
) -> Path:
    """构造 req-id <= 38 的 legacy req fixture。返回 req_dir。"""
    from harness_workflow.slug import slugify_preserve_unicode

    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    req_dir.mkdir(parents=True)
    (req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")

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
    return req_dir


if __name__ == "__main__":
    unittest.main()
