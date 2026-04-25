"""Tests for req-42（archive 重定义：对人不挪 + 摘要废止）/ chg-04（pytest 三层级 + scaffold mirror 收口）.

AC-6：覆盖三层级 archive 行为，每层独立 fixture + 独立断言。

层级划分（来自 FLAT_LAYOUT_FROM_REQ_ID=39 / FLOW_LAYOUT_FROM_REQ_ID=41）：
- legacy（req-id ≤ 38）   → source_root = artifacts/main/requirements/
                            target = artifacts/main/archive/requirements/{slug}/
- state-flat（39-40）      → 同 legacy 归档路径，额外迁 .workflow/state/requirements/{req-id}/ → target/state_requirements/
- flow（req-id ≥ 41）      → source_root = .workflow/flow/requirements/
                            target = .workflow/flow/archive/main/{slug}/
                            对人 folder（artifacts/main/requirements/{slug}/）原位保留
                            不产摘要 md

Fixture 隔离矩阵（风险 R-12 缓解）：
  | 层级       | dummy req-id | req_id 数字 | 预期分支           |
  |-----------|-------------|------------|-------------------|
  | legacy    | req-36      | 36         | legacy（≤38）     |
  | state-flat| req-40      | 40         | state-flat（39-40）|
  | flow      | req-97      | 97         | flow（≥41）        |

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


def _init_legacy_fixture(root: Path) -> tuple[str, str, Path]:
    """构造 req-id = req-36（legacy ≤ 38）的 dummy 工作区。

    返回 (req_id, dir_name, artifacts_req_dir)。
    legacy 层：对人 folder 在 artifacts/main/requirements/{dir_name}/，
              归档目标 artifacts/main/archive/requirements/{dir_name}/。
    """
    from harness_workflow.slug import slugify_preserve_unicode

    req_id = "req-36"
    req_title = "legacy-archive-test"
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    _base_dirs(root)

    # 对人 folder（source）：artifacts/main/requirements/{dir_name}/
    artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    artifacts_req_dir.mkdir(parents=True)
    (artifacts_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    (artifacts_req_dir / "chg-01-变更简报.md").write_text("# 变更简报\n", encoding="utf-8")

    _write_state_yaml(root, dir_name, req_id, req_title)
    _write_runtime(root, req_id, req_title)
    return req_id, dir_name, artifacts_req_dir


def _init_state_flat_fixture(root: Path) -> tuple[str, str, Path, Path]:
    """构造 req-id = req-40（state-flat ∈ [39, 40]）的 dummy 工作区。

    返回 (req_id, dir_name, artifacts_req_dir, state_req_machine_dir)。
    state-flat 层：
      - 对人 folder 在 artifacts/main/requirements/{dir_name}/
      - 归档目标 artifacts/main/archive/requirements/{dir_name}/
      - .workflow/state/requirements/{req_id}/ 机器型目录额外迁到 target/state_requirements/
    """
    from harness_workflow.slug import slugify_preserve_unicode

    req_id = "req-40"
    req_title = "state-flat-archive-test"
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"

    _base_dirs(root)

    # 对人 folder（source）
    artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    artifacts_req_dir.mkdir(parents=True)
    (artifacts_req_dir / "需求摘要.md").write_text("# 需求摘要\n", encoding="utf-8")
    (artifacts_req_dir / "chg-01-变更简报.md").write_text("# 变更简报\n", encoding="utf-8")

    # 机器型 state 目录：.workflow/state/requirements/{req_id}/
    state_req_machine_dir = root / ".workflow" / "state" / "requirements" / req_id
    state_req_machine_dir.mkdir(parents=True)
    (state_req_machine_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")

    # sessions
    sessions_dir = root / ".workflow" / "state" / "sessions" / req_id
    chg_dir = sessions_dir / "chg-01-test-change"
    chg_dir.mkdir(parents=True)
    (chg_dir / "session-memory.md").write_text("# Session Memory\n", encoding="utf-8")

    _write_state_yaml(root, dir_name, req_id, req_title)
    _write_runtime(root, req_id, req_title)
    return req_id, dir_name, artifacts_req_dir, state_req_machine_dir


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
    # Tier 1: legacy（req-id ≤ 38）
    # -----------------------------------------------------------------------

    def test_archive_requirement_legacy_tier(self) -> None:
        """AC-6 legacy 层（req-36 ≤ 38）：archive 走旧路径，folder 搬到 artifacts/main/archive/requirements/。"""
        from harness_workflow.workflow_helpers import archive_requirement

        req_id, dir_name, artifacts_req_dir = _init_legacy_fixture(self.root)

        rc = archive_requirement(self.root, req_id)
        self.assertEqual(rc, 0, f"archive_requirement 应返回 0，实际 {rc}")

        # 断言 1: 归档目标目录存在（folder 已整搬到 artifacts/main/archive/requirements/）
        archive_req_base = self.root / "artifacts" / "main" / "archive" / "requirements"
        archived_dirs = list(archive_req_base.glob(f"{req_id}-*"))
        self.assertTrue(
            archived_dirs,
            f"legacy 层：归档后 artifacts/main/archive/requirements/ 下应有 {req_id}-* 目录，"
            f"但未找到。目录内容：{list(archive_req_base.iterdir()) if archive_req_base.exists() else '(不存在)'}",
        )
        archive_dir = archived_dirs[0]

        # 断言 2: 归档目录内容完整（含原对人文档）
        self.assertTrue(
            (archive_dir / "requirement.md").exists(),
            f"legacy 层：归档目录 {archive_dir} 应含 requirement.md",
        )

        # 断言 3: 源对人 folder 已迁走（legacy 路径下对人 folder 不保留原位）
        self.assertFalse(
            artifacts_req_dir.exists(),
            f"legacy 层：source 对人 folder 应已迁走，但 {artifacts_req_dir} 仍存在",
        )

        # 断言 4: flow/archive 下不应有该 req（legacy 不走 flow 路径）
        flow_archive_base = self.root / ".workflow" / "flow" / "archive" / "main"
        flow_archived = list(flow_archive_base.glob(f"{req_id}-*")) if flow_archive_base.exists() else []
        self.assertEqual(
            flow_archived,
            [],
            f"legacy 层：flow/archive 下不应有 {req_id}-*，但发现 {flow_archived}",
        )

    # -----------------------------------------------------------------------
    # Tier 2: state-flat（req-id ∈ [39, 40]）
    # -----------------------------------------------------------------------

    def test_archive_requirement_state_flat_tier(self) -> None:
        """AC-6 state-flat 层（req-40 ∈ [39,40]）：archive 走 artifacts/archive 路径 + 额外迁 state_requirements。"""
        from harness_workflow.workflow_helpers import archive_requirement

        req_id, dir_name, artifacts_req_dir, state_req_machine_dir = _init_state_flat_fixture(self.root)

        rc = archive_requirement(self.root, req_id)
        self.assertEqual(rc, 0, f"archive_requirement 应返回 0，实际 {rc}")

        # 断言 1: 归档目标目录存在（folder 已整搬到 artifacts/main/archive/requirements/）
        archive_req_base = self.root / "artifacts" / "main" / "archive" / "requirements"
        archived_dirs = list(archive_req_base.glob(f"{req_id}-*"))
        self.assertTrue(
            archived_dirs,
            f"state-flat 层：归档后 artifacts/main/archive/requirements/ 下应有 {req_id}-* 目录，"
            f"但未找到。目录内容：{list(archive_req_base.iterdir()) if archive_req_base.exists() else '(不存在)'}",
        )
        archive_dir = archived_dirs[0]

        # 断言 2: 归档目录含 state_requirements/ 子目录（state-flat 独有：机器型文档一起收齐）
        state_machine_dst = archive_dir / "state_requirements"
        self.assertTrue(
            state_machine_dst.exists(),
            f"state-flat 层：归档目录 {archive_dir} 应含 state_requirements/ 子目录，"
            f"但未找到。归档目录内容：{list(archive_dir.iterdir()) if archive_dir.exists() else '(不存在)'}",
        )

        # 断言 3: .workflow/state/requirements/{req_id}/ 机器型目录已迁走
        self.assertFalse(
            state_req_machine_dir.exists(),
            f"state-flat 层：.workflow/state/requirements/{req_id}/ 应已迁走，但 {state_req_machine_dir} 仍存在",
        )

        # 断言 4: 源对人 folder 已迁走（state-flat 和 legacy 一样，对人 folder 不保留原位）
        self.assertFalse(
            artifacts_req_dir.exists(),
            f"state-flat 层：source 对人 folder 应已迁走，但 {artifacts_req_dir} 仍存在",
        )

        # 断言 5: flow/archive 下不应有该 req（state-flat 不走 flow 路径）
        flow_archive_base = self.root / ".workflow" / "flow" / "archive" / "main"
        flow_archived = list(flow_archive_base.glob(f"{req_id}-*")) if flow_archive_base.exists() else []
        self.assertEqual(
            flow_archived,
            [],
            f"state-flat 层：flow/archive 下不应有 {req_id}-*，但发现 {flow_archived}",
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
