"""Tests updated for bugfix-11 方向C（废弃三段式分水岭）.

原测试覆盖三层级 archive 行为（legacy/state-flat/flow）。
bugfix-11 方向C 废弃三段式分水岭后：
- 所有 req 一律走 flow layout（.workflow/flow/requirements/）
- legacy（req-36）和 state-flat（req-40）fixture 更新为 flow layout
- 归档路径统一为 .workflow/flow/archive/main/{slug}/
- 对人 folder（artifacts/main/requirements/{slug}/）原位保留
- 不再走 artifacts/main/archive/requirements/ 路径

Fixture 隔离矩阵（方向C 后）：
  | 层级   | dummy req-id | 预期分支                     |
  |-------|-------------|------------------------------|
  | 原 legacy    | req-36 | flow layout（方向C 废弃 legacy） |
  | 原 state-flat| req-40 | flow layout（方向C 废弃 state-flat） |
  | flow         | req-97 | flow layout（不变）           |

每 fixture 独立 tmp_path，独立 dummy req-id，互不干扰。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _base_dirs(root: Path) -> None:
    """创建所有层级都需要的基础目录和 config.json。"""
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "flow" / "archive").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True, exist_ok=True)
    (root / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_runtime(root: Path, req_id: str, req_title: str) -> None:
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


def _write_state_yaml(root: Path, dir_name: str, req_id: str, req_title: str) -> None:
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


def _init_legacy_fixture(root: Path) -> tuple[str, str, Path, Path]:
    """构造 req-id = req-36（原 legacy ≤ 38）的 dummy 工作区（方向C 后走 flow layout）。

    返回 (req_id, dir_name, artifacts_req_dir, flow_req_dir)。
    方向C：对人 folder 在 artifacts/main/requirements/{dir_name}/（原位保留）
           机器型 folder 在 .workflow/flow/requirements/{dir_name}/
           归档目标 .workflow/flow/archive/main/{dir_name}/。
    """
    from harness_workflow.slug import slugify_preserve_unicode

    req_id = "req-36"
    req_title = "legacy-archive-test"
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    _base_dirs(root)

    # 对人 folder（source）：artifacts/main/requirements/{dir_name}/（原位保留）
    artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    artifacts_req_dir.mkdir(parents=True)
    (artifacts_req_dir / "chg-01-变更简报.md").write_text("# 变更简报\n", encoding="utf-8")

    # 机器型 flow folder（方向C 权威路径）
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_req_dir.mkdir(parents=True)
    (flow_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")

    _write_state_yaml(root, dir_name, req_id, req_title)
    _write_runtime(root, req_id, req_title)
    return req_id, dir_name, artifacts_req_dir, flow_req_dir


def _init_state_flat_fixture(root: Path) -> tuple[str, str, Path, Path]:
    """构造 req-id = req-40（原 state-flat ∈ [39, 40]）的 dummy 工作区（方向C 后走 flow layout）。

    返回 (req_id, dir_name, artifacts_req_dir, flow_req_dir)。
    方向C：对人 folder 在 artifacts/main/requirements/{dir_name}/（原位保留）
           机器型 folder 在 .workflow/flow/requirements/{dir_name}/
           归档目标 .workflow/flow/archive/main/{dir_name}/。
    """
    from harness_workflow.slug import slugify_preserve_unicode

    req_id = "req-40"
    req_title = "state-flat-archive-test"
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    _base_dirs(root)

    # 对人 folder（source）：原位保留（方向C）
    artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    artifacts_req_dir.mkdir(parents=True)
    (artifacts_req_dir / "需求摘要.md").write_text("# 需求摘要\n", encoding="utf-8")
    (artifacts_req_dir / "chg-01-变更简报.md").write_text("# 变更简报\n", encoding="utf-8")

    # 机器型 flow folder（方向C 权威路径）
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_req_dir.mkdir(parents=True)
    (flow_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    changes_dir = flow_req_dir / "changes"
    changes_dir.mkdir(parents=True)
    chg_dir = changes_dir / "chg-01-test-change"
    chg_dir.mkdir(parents=True)
    (chg_dir / "session-memory.md").write_text("# Session Memory\n", encoding="utf-8")

    _write_state_yaml(root, dir_name, req_id, req_title)
    _write_runtime(root, req_id, req_title)
    return req_id, dir_name, artifacts_req_dir, flow_req_dir


def _init_flow_fixture(root: Path) -> tuple[str, str, Path, Path]:
    """构造 req-id = req-97（flow ≥ 41）的 dummy 工作区。

    返回 (req_id, dir_name, artifacts_req_dir, flow_req_dir)。
    flow 层（req-42 新规）：
      (i)  对人 folder artifacts/main/requirements/{dir_name}/ 原位保留（不迁移）
      (ii) 不产摘要 md（顶层 artifacts/main/requirements/ 下无 req-97-xxx.md）
      (iii) 机器型 folder .workflow/flow/requirements/{dir_name}/ 迁到
            .workflow/flow/archive/main/{dir_name}/
    """
    from harness_workflow.slug import slugify_preserve_unicode

    req_id = "req-97"
    req_title = "flow-archive-test"
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    _base_dirs(root)

    # 对人 folder（artifacts — 归档后应原位）
    artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    artifacts_req_dir.mkdir(parents=True)
    (artifacts_req_dir / "交付总结.md").write_text("# 交付总结\n", encoding="utf-8")
    (artifacts_req_dir / "chg-01-变更简报.md").write_text("# 变更简报\n", encoding="utf-8")

    # 机器型 flow folder（.workflow/flow/requirements/{dir_name}/）
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_req_dir.mkdir(parents=True)
    (flow_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    changes_dir = flow_req_dir / "changes"
    changes_dir.mkdir(parents=True)
    chg01 = changes_dir / "chg-01-test-change"
    chg01.mkdir(parents=True)
    (chg01 / "change.md").write_text("# Change\n", encoding="utf-8")
    (chg01 / "plan.md").write_text("# Plan\n", encoding="utf-8")

    # state yaml（流 req 的 state.yaml 用 flat style：flat dir_name.yaml）
    _write_state_yaml(root, dir_name, req_id, req_title)
    _write_runtime(root, req_id, req_title)
    return req_id, dir_name, artifacts_req_dir, flow_req_dir


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class ArchiveRequirementThreeTiersTest(unittest.TestCase):
    """AC-6：三层级 archive 行为各自独立验证。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    # -----------------------------------------------------------------------
    # Tier 1: 原 legacy（req-id ≤ 38）→ 方向C 后走 flow layout
    # -----------------------------------------------------------------------

    def test_archive_requirement_legacy_tier(self) -> None:
        """方向C: req-36（原 legacy ≤ 38）归档走 flow layout，机器型迁 flow/archive + 对人 folder 原位。"""
        from harness_workflow.workflow_helpers import archive_requirement

        req_id, dir_name, artifacts_req_dir, flow_req_dir = _init_legacy_fixture(self.root)

        rc = archive_requirement(self.root, req_id)
        self.assertEqual(rc, 0, f"archive_requirement 应返回 0，实际 {rc}")

        # 断言 1: 机器型文档迁到 flow/archive/main/（方向C）
        flow_archive_base = self.root / ".workflow" / "flow" / "archive" / "main"
        archived_dirs = list(flow_archive_base.glob(f"{req_id}-*"))
        self.assertTrue(
            archived_dirs,
            f"方向C: 归档后 flow/archive/main/ 下应有 {req_id}-* 目录，"
            f"但未找到。目录内容：{list(flow_archive_base.iterdir()) if flow_archive_base.exists() else '(不存在)'}",
        )
        archive_dir = archived_dirs[0]

        # 断言 2: flow archive 目录内容完整（含 requirement.md）
        self.assertTrue(
            (archive_dir / "requirement.md").exists(),
            f"方向C: flow archive 目录 {archive_dir} 应含 requirement.md",
        )

        # 断言 3: 对人 folder 原位保留（方向C）
        self.assertTrue(
            artifacts_req_dir.exists(),
            f"方向C: 对人 folder 应原位保留，但 {artifacts_req_dir} 不存在",
        )

        # 断言 4: 旧 artifacts/archive/ 路径下不应有该 req（方向C 废弃 legacy 归档路径）
        old_archive_base = self.root / "artifacts" / "main" / "archive" / "requirements"
        old_archived = list(old_archive_base.glob(f"{req_id}-*")) if old_archive_base.exists() else []
        self.assertEqual(
            old_archived,
            [],
            f"方向C: artifacts/archive/requirements/ 下不应有 {req_id}-*（废弃 legacy 路径），但发现 {old_archived}",
        )

    # -----------------------------------------------------------------------
    # Tier 2: 原 state-flat（req-id ∈ [39, 40]）→ 方向C 后走 flow layout
    # -----------------------------------------------------------------------

    def test_archive_requirement_state_flat_tier(self) -> None:
        """方向C: req-40（原 state-flat ∈ [39,40]）归档走 flow layout，机器型迁 flow/archive + 对人 folder 原位。"""
        from harness_workflow.workflow_helpers import archive_requirement

        req_id, dir_name, artifacts_req_dir, flow_req_dir = _init_state_flat_fixture(self.root)

        rc = archive_requirement(self.root, req_id)
        self.assertEqual(rc, 0, f"archive_requirement 应返回 0，实际 {rc}")

        # 断言 1: 机器型文档迁到 flow/archive/main/（方向C）
        flow_archive_base = self.root / ".workflow" / "flow" / "archive" / "main"
        archived_dirs = list(flow_archive_base.glob(f"{req_id}-*"))
        self.assertTrue(
            archived_dirs,
            f"方向C: 归档后 flow/archive/main/ 下应有 {req_id}-* 目录，"
            f"但未找到。目录内容：{list(flow_archive_base.iterdir()) if flow_archive_base.exists() else '(不存在)'}",
        )
        archive_dir = archived_dirs[0]

        # 断言 2: flow archive 目录内容完整（含 requirement.md 和 changes/）
        self.assertTrue(
            (archive_dir / "requirement.md").exists(),
            f"方向C: flow archive 目录 {archive_dir} 应含 requirement.md",
        )
        self.assertTrue(
            (archive_dir / "changes").exists(),
            f"方向C: flow archive 目录 {archive_dir} 应含 changes/ 子目录",
        )

        # 断言 3: 对人 folder 原位保留（方向C）
        self.assertTrue(
            artifacts_req_dir.exists(),
            f"方向C: 对人 folder 应原位保留，但 {artifacts_req_dir} 不存在",
        )

        # 断言 4: 旧 artifacts/archive/ 路径下不应有该 req（方向C 废弃 state-flat 路径）
        old_archive_base = self.root / "artifacts" / "main" / "archive" / "requirements"
        old_archived = list(old_archive_base.glob(f"{req_id}-*")) if old_archive_base.exists() else []
        self.assertEqual(
            old_archived,
            [],
            f"方向C: artifacts/archive/requirements/ 下不应有 {req_id}-*（废弃 state-flat 路径），但发现 {old_archived}",
        )

    # -----------------------------------------------------------------------
    # Tier 3: flow（req-id ≥ 41，req-42 新规）
    # -----------------------------------------------------------------------

    def test_archive_requirement_flow_tier(self) -> None:
        """AC-6 flow 层（req-97 ≥ 41）：(i) 对人 folder 原位 + (ii) 无摘要 md + (iii) 机器型迁 flow/archive。"""
        from harness_workflow.workflow_helpers import archive_requirement

        req_id, dir_name, artifacts_req_dir, flow_req_dir = _init_flow_fixture(self.root)

        rc = archive_requirement(self.root, req_id)
        self.assertEqual(rc, 0, f"archive_requirement 应返回 0，实际 {rc}")

        # 断言 (i): 对人 folder 原位保留（AC-6(i) / AC-1）
        self.assertTrue(
            artifacts_req_dir.exists(),
            f"flow 层 (i)：对人 folder 应原位保留，但 {artifacts_req_dir} 不存在",
        )
        self.assertTrue(
            (artifacts_req_dir / "交付总结.md").exists(),
            "flow 层 (i)：对人 folder 内容应完整（含 交付总结.md）",
        )

        # 断言 (ii): 顶层 artifacts/main/requirements/ 下无 req-97-xxx.md 摘要文件（AC-6(ii) / AC-2）
        top_level_mds = list(
            (self.root / "artifacts" / "main" / "requirements").glob(f"{req_id}-*.md")
        )
        self.assertEqual(
            top_level_mds,
            [],
            f"flow 层 (ii)：不应产出摘要 md，但顶层发现 {top_level_mds}",
        )

        # 断言 (iii-a): .workflow/flow/archive/main/{dir_name}/ 存在（AC-6(iii) / AC-3）
        flow_archive_dir = self.root / ".workflow" / "flow" / "archive" / "main" / dir_name
        self.assertTrue(
            flow_archive_dir.exists(),
            f"flow 层 (iii)：flow/archive/main/{dir_name}/ 应存在，但未找到",
        )
        self.assertTrue(
            (flow_archive_dir / "requirement.md").exists(),
            f"flow 层 (iii)：flow archive 目录应含 requirement.md",
        )
        self.assertTrue(
            (flow_archive_dir / "changes").exists(),
            f"flow 层 (iii)：flow archive 目录应含 changes/ 子树",
        )

        # 断言 (iii-b): .workflow/flow/requirements/{dir_name}/ 已迁走
        self.assertFalse(
            flow_req_dir.exists(),
            f"flow 层 (iii)：.workflow/flow/requirements/{dir_name}/ 应已迁走，但 {flow_req_dir} 仍存在",
        )

        # 断言 (iv): artifacts/main/archive/requirements/ 下不应有 flow req（flow 不走旧归档路径）
        old_archive_base = self.root / "artifacts" / "main" / "archive" / "requirements"
        old_archived = list(old_archive_base.glob(f"{req_id}-*")) if old_archive_base.exists() else []
        self.assertEqual(
            old_archived,
            [],
            f"flow 层：artifacts/main/archive/requirements/ 下不应有 {req_id}-*，但发现 {old_archived}",
        )


if __name__ == "__main__":
    unittest.main()
