"""Tests for req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） / chg-01（apply / apply-all CLI 路径与内容修复）.

覆盖 plan.md §4 测试用例 TC-01 ~ TC-06：
- TC-01: apply-all 后 bugfix-6 路径成功（flow layout req-id >= 41）
- TC-02: apply-all legacy req-id 路径兼容（_use_flow_layout 返回 False）
- TC-03: apply-all req_md 不存在时不 unlink
- TC-04: apply 单 sug 取 sug.title 当 req title
- TC-05: apply 单 sug 真写入 requirement.md
- TC-06: apply 单 sug 后 bugfix-6 路径落位
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
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime(root: Path, current_requirement: str = "") -> None:
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(
            [
                'operation_type: "requirement"',
                f'operation_target: "{current_requirement}"',
                f'current_requirement: "{current_requirement}"',
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


def _seed_pending_sug(root: Path, sug_id: str, title: str, body: str) -> Path:
    sug_dir = root / ".workflow" / "flow" / "suggestions"
    slug = sug_id.replace("-", "_")
    p = sug_dir / f"{sug_id}-{slug}.md"
    p.write_text(
        f"---\nid: {sug_id}\ntitle: \"{title}\"\nstatus: pending\ncreated_at: 2026-04-25\npriority: medium\n---\n\n{body}\n",
        encoding="utf-8",
    )
    return p


def _pre_create_flow_req(root: Path, req_id: str, title: str) -> tuple[str, Path]:
    """Pre-create a flow layout req directory with empty requirement.md (simulating create_requirement for flow req-id >= 41)."""
    from harness_workflow.workflow_helpers import _path_slug
    slug_part = _path_slug(title)
    dir_name = f"{req_id}-{slug_part}" if slug_part else req_id
    flow_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_dir.mkdir(parents=True, exist_ok=True)
    req_md = flow_dir / "requirement.md"
    req_md.write_text(f"# {title}\n\n## Goal\n...\n", encoding="utf-8")
    # also create artifacts dir (create_requirement does this)
    (root / "artifacts" / "main" / "requirements" / dir_name).mkdir(parents=True, exist_ok=True)
    return dir_name, req_md


class TestApplyAllFlowPath(unittest.TestCase):
    """TC-01: apply-all 后 bugfix-6 路径成功."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req44-chg01-"))
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

    def test_tc01_apply_all_flow_layout_success(self) -> None:
        """TC-01: req-id >= 41, apply-all uses .workflow/flow/requirements/ path, sug unlinked, req_md contains 合并建议清单."""
        from harness_workflow.workflow_helpers import apply_all_suggestions, _use_flow_layout

        # Force req id to be >= 41 so _use_flow_layout returns True
        # We do this by pre-seeding enough req dirs to bump _next_req_id to >= 41
        # Simpler: override _next_req_id via req state dirs
        for i in range(1, 41):
            (self.root / ".workflow" / "state" / "requirements" / f"req-{i:02d}-dummy.yaml").write_text(
                f'id: "req-{i:02d}"\ntitle: "dummy {i}"\n', encoding="utf-8"
            )

        sug1 = _seed_pending_sug(self.root, "sug-43", "旧路径检查导致 abort", "BODY-SUG-43")
        sug2 = _seed_pending_sug(self.root, "sug-44", "apply 取 title", "BODY-SUG-44")

        pack_title = "批量建议合集（flow测试）"
        rc = apply_all_suggestions(self.root, pack_title=pack_title)

        self.assertEqual(rc, 0, "apply_all 应返回 0")

        # sug files should be unlinked
        self.assertFalse(sug1.exists(), "sug-43 应被 unlink")
        self.assertFalse(sug2.exists(), "sug-44 应被 unlink")

        # requirement.md should be in .workflow/flow/requirements/
        flow_reqs = root = self.root / ".workflow" / "flow" / "requirements"
        candidates = sorted(flow_reqs.glob("req-41-*"))
        self.assertEqual(len(candidates), 1, f"应存在恰好 1 个 req-41-* 在 flow/, 实际 {list(flow_reqs.iterdir())}")
        req_md = candidates[0] / "requirement.md"
        self.assertTrue(req_md.exists(), f"requirement.md 应存在于 {req_md}")
        text = req_md.read_text(encoding="utf-8")
        self.assertIn("## 合并建议清单", text, "requirement.md 应含 ## 合并建议清单")
        self.assertIn("sug-43", text)
        self.assertIn("sug-44", text)
        # Verify _use_flow_layout returns True for req-41
        self.assertTrue(_use_flow_layout("req-41"))

    def test_tc02_apply_all_legacy_path_compatible(self) -> None:
        """TC-02: legacy req-id（_use_flow_layout returns False）, body written to artifacts/ path."""
        from harness_workflow.workflow_helpers import apply_all_suggestions

        # No pre-seeding, so _next_req_id will be req-01 (_use_flow_layout returns False)
        sug1 = _seed_pending_sug(self.root, "sug-01", "legacy sug title", "LEGACY-BODY")

        pack_title = "legacy pack"
        rc = apply_all_suggestions(self.root, pack_title=pack_title)
        self.assertEqual(rc, 0, "legacy 路径 apply-all 应返回 0")

        # req_md should be in artifacts/main/requirements/ for legacy req-id
        reqs_dir = self.root / "artifacts" / "main" / "requirements"
        candidates = sorted(reqs_dir.glob("req-01-*"))
        self.assertEqual(len(candidates), 1, f"应存在恰好 1 个 req-01-*, 实际 {list(reqs_dir.iterdir())}")
        req_md = candidates[0] / "requirement.md"
        self.assertTrue(req_md.exists())
        text = req_md.read_text(encoding="utf-8")
        self.assertIn("## 合并建议清单", text)
        self.assertIn("LEGACY-BODY", text)

    def test_tc03_apply_all_missing_req_md_no_unlink(self) -> None:
        """TC-03: req_md 不存在时，exit != 0, sug 文件保留, stderr 含 ERROR."""
        from harness_workflow.workflow_helpers import apply_all_suggestions

        # Force flow layout (req-id >= 41)
        for i in range(1, 41):
            (self.root / ".workflow" / "state" / "requirements" / f"req-{i:02d}-dummy.yaml").write_text(
                f'id: "req-{i:02d}"\ntitle: "dummy {i}"\n', encoding="utf-8"
            )

        sug1 = _seed_pending_sug(self.root, "sug-50", "test sug", "BODY-MISSING-REQ")

        # Override create_requirement to succeed but NOT create the requirement.md
        # We do this by making _append_sug_body_to_req_md raise FileNotFoundError via
        # deleting the flow dir after create_requirement, but that's brittle.
        # Better: patch _append_sug_body_to_req_md to raise FileNotFoundError
        with mock.patch(
            "harness_workflow.workflow_helpers._append_sug_body_to_req_md",
            side_effect=FileNotFoundError("requirement.md not found"),
        ):
            import io
            from contextlib import redirect_stderr
            err_buf = io.StringIO()
            with redirect_stderr(err_buf):
                rc = apply_all_suggestions(self.root, pack_title="missing-req-test")

        self.assertNotEqual(rc, 0, "req_md 不存在时 apply_all 应返回非零")
        self.assertTrue(sug1.exists(), "sug 文件应被保留（不 unlink）")
        self.assertIn("ERROR", err_buf.getvalue())


class TestApplySuggestionContent(unittest.TestCase):
    """TC-04/05/06: apply 单 sug title + body 写入 + flow 路径落位."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req44-apply-"))
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

    def test_tc04_apply_uses_sug_frontmatter_title(self) -> None:
        """TC-04: sug frontmatter title 优先于 content 首行."""
        from harness_workflow.workflow_helpers import apply_suggestion, load_requirement_runtime

        sug_path = _seed_pending_sug(
            self.root, "sug-10",
            "正确标题 from frontmatter",
            "# 这是 content 首行\n\n正文内容...",
        )

        rc = apply_suggestion(self.root, "sug-10")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        title_in_runtime = str(runtime.get("current_requirement_title", ""))
        # Title should come from frontmatter, not content's "# 这是 content 首行"
        self.assertIn("正确标题", title_in_runtime, f"runtime title 应含 frontmatter title, 实际: {title_in_runtime}")
        self.assertNotIn("这是 content 首行", title_in_runtime)

    def test_tc05_apply_writes_sug_body_to_requirement_md(self) -> None:
        """TC-05: apply 后 requirement.md 末含 ## 合并建议清单 + sug body marker."""
        from harness_workflow.workflow_helpers import apply_suggestion

        sug_path = _seed_pending_sug(
            self.root, "sug-11",
            "Body Test Sug",
            "BODY-MARKER-XYZ 正文内容",
        )

        rc = apply_suggestion(self.root, "sug-11")
        self.assertEqual(rc, 0)

        # Find the created requirement.md (legacy path, req-01)
        reqs_dir = self.root / "artifacts" / "main" / "requirements"
        candidates = sorted(reqs_dir.glob("req-01-*"))
        self.assertEqual(len(candidates), 1)
        req_md = candidates[0] / "requirement.md"
        self.assertTrue(req_md.exists())
        text = req_md.read_text(encoding="utf-8")
        self.assertIn("## 合并建议清单", text, "requirement.md 应含 ## 合并建议清单")
        self.assertIn("BODY-MARKER-XYZ", text, "requirement.md 应含 sug body 内容")

    def test_tc06_apply_single_sug_flow_layout_path(self) -> None:
        """TC-06: req-id >= 41, apply 单 sug 后 requirement.md 落在 .workflow/flow/requirements/."""
        from harness_workflow.workflow_helpers import apply_suggestion

        # Force req-id >= 41
        for i in range(1, 41):
            (self.root / ".workflow" / "state" / "requirements" / f"req-{i:02d}-dummy.yaml").write_text(
                f'id: "req-{i:02d}"\ntitle: "dummy {i}"\n', encoding="utf-8"
            )

        sug_path = _seed_pending_sug(
            self.root, "sug-45",
            "Flow Layout Sug Title",
            "FLOW-BODY-MARKER",
        )

        rc = apply_suggestion(self.root, "sug-45")
        self.assertEqual(rc, 0)

        # requirement.md should be in flow layout
        flow_reqs = self.root / ".workflow" / "flow" / "requirements"
        candidates = sorted(flow_reqs.glob("req-41-*"))
        self.assertEqual(len(candidates), 1, f"应在 flow/ 找到 req-41-*, 实际 {list(flow_reqs.iterdir())}")
        req_md = candidates[0] / "requirement.md"
        self.assertTrue(req_md.exists())
        text = req_md.read_text(encoding="utf-8")
        self.assertIn("## 合并建议清单", text)
        self.assertIn("FLOW-BODY-MARKER", text)

        # artifacts/ should NOT have the body content (only the placeholder dir)
        artifacts_reqs = self.root / "artifacts" / "main" / "requirements"
        for d in artifacts_reqs.iterdir():
            if d.name.startswith("req-41-") and (d / "requirement.md").exists():
                art_text = (d / "requirement.md").read_text(encoding="utf-8")
                self.assertNotIn("FLOW-BODY-MARKER", art_text,
                    "artifacts/ 的 requirement.md 不应含 sug body（仅 flow/ 路径写入）")


if __name__ == "__main__":
    unittest.main()
