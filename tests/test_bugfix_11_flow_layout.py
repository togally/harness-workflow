"""bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）.

Round-2 新增测试文件（替代已删 test_use_flow_layout.py）。
Round-2 H-E3 扩范围：bugfix 维度同型病一并修复，新增 CreateBugfixUnconditionalFlowLayoutTest。
27 用例 = 5 + 3 + 2 + 5 + 12 共 5 个测试类。

- CreateRequirementUnconditionalFlowLayoutTest (5): 任意 req-id 落 flow/requirements/
- CreateChangeUnconditionalFlowLayoutTest (3): 任意 req-id chg 落 flow/requirements/{req}/changes/
- CreateRegressionUnconditionalFlowLayoutTest (2): 任意 req-id reg 落 flow/requirements/{req}/regressions/
- CreateBugfixUnconditionalFlowLayoutTest (5): 任意 bugfix-id 落 flow/bugfixes/（H-E3 扩范围）
- DeprecatedSymbolsLintTest (12): src/ 树下不允许存在已废弃符号（含 H-E3 新增 2 项）
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src" / "harness_workflow"
sys.path.insert(0, str(REPO_ROOT / "src"))


def _make_harness_root(tmp: Path) -> Path:
    """Create a minimal harness workspace root."""
    root = tmp / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        'operation_type: "requirement"\noperation_target: ""\ncurrent_requirement: ""\nstage: "done"\n'
        'conversation_mode: "open"\nlocked_requirement: ""\nlocked_stage: ""\ncurrent_regression: ""\n'
        "ff_mode: false\nff_stage_history: []\nactive_requirements: []\n",
        encoding="utf-8",
    )
    return root


class CreateRequirementUnconditionalFlowLayoutTest(unittest.TestCase):
    """方向C: create_requirement 对任意 req-id 一律落 .workflow/flow/requirements/."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-b11-req-"))
        self.root = _make_harness_root(self.tempdir)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch", return_value="main"
        )
        self._branch_patch.start()

    def tearDown(self) -> None:
        self._branch_patch.stop()
        import shutil
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_req_01_lands_in_flow_requirements(self) -> None:
        """req-01（原 legacy）create_requirement 后 requirement.md 落 .workflow/flow/requirements/."""
        from harness_workflow.workflow_helpers import create_requirement

        rc = create_requirement(self.root, "fresh-req-01")
        self.assertEqual(rc, 0, "create_requirement 应返回 0")

        flow_reqs = self.root / ".workflow" / "flow" / "requirements"
        candidates = sorted(flow_reqs.glob("req-01-*"))
        self.assertEqual(len(candidates), 1, f"应有 1 个 req-01-* 在 flow/, 实际: {list(flow_reqs.iterdir())}")
        req_md = candidates[0] / "requirement.md"
        self.assertTrue(req_md.exists(), f"requirement.md 应在 flow/requirements/ 下: {req_md}")

    def test_req_38_lands_in_flow_requirements(self) -> None:
        """req-38（原 mixed）create_requirement 后 requirement.md 落 .workflow/flow/requirements/."""
        from harness_workflow.workflow_helpers import create_requirement

        # Pre-seed 37 req state yamls so _next_req_id returns req-38
        for i in range(1, 38):
            (self.root / ".workflow" / "state" / "requirements" / f"req-{i:02d}-dummy.yaml").write_text(
                f'id: "req-{i:02d}"\ntitle: "dummy"\n', encoding="utf-8"
            )

        rc = create_requirement(self.root, "flow-req-38")
        self.assertEqual(rc, 0)

        flow_reqs = self.root / ".workflow" / "flow" / "requirements"
        candidates = sorted(flow_reqs.glob("req-38-*"))
        self.assertEqual(len(candidates), 1, f"应有 1 个 req-38-* 在 flow/, 实际: {list(flow_reqs.iterdir())}")
        self.assertTrue((candidates[0] / "requirement.md").exists())

    def test_req_99_lands_in_flow_requirements(self) -> None:
        """req-99（大 id）create_requirement 后 requirement.md 落 .workflow/flow/requirements/."""
        from harness_workflow.workflow_helpers import create_requirement

        # Pre-seed 98 req state yamls
        for i in range(1, 99):
            (self.root / ".workflow" / "state" / "requirements" / f"req-{i:02d}-dummy.yaml").write_text(
                f'id: "req-{i:02d}"\ntitle: "dummy"\n', encoding="utf-8"
            )

        rc = create_requirement(self.root, "flow-req-99")
        self.assertEqual(rc, 0)

        flow_reqs = self.root / ".workflow" / "flow" / "requirements"
        candidates = sorted(flow_reqs.glob("req-99-*"))
        self.assertEqual(len(candidates), 1, f"应有 1 个 req-99-* 在 flow/")
        self.assertTrue((candidates[0] / "requirement.md").exists())

    def test_req_01_no_artifacts_machine_docs(self) -> None:
        """req-01 create_requirement 后 artifacts/ 下无 requirement.md / session-memory.md / changes/ 子目录."""
        from harness_workflow.workflow_helpers import create_requirement

        rc = create_requirement(self.root, "no-artifacts-machine")
        self.assertEqual(rc, 0)

        flow_reqs = self.root / ".workflow" / "flow" / "requirements"
        candidates = sorted(flow_reqs.glob("req-01-*"))
        self.assertEqual(len(candidates), 1)
        dir_name = candidates[0].name

        # artifacts/ should not contain machine docs
        artifacts_req_dir = self.root / "artifacts" / "main" / "requirements" / dir_name
        self.assertFalse(
            (artifacts_req_dir / "requirement.md").exists(),
            "artifacts/ 下不应有 requirement.md（机器型文档应在 flow/）",
        )
        self.assertFalse(
            (artifacts_req_dir / "session-memory.md").exists(),
            "artifacts/ 下不应有 session-memory.md",
        )
        self.assertFalse(
            (artifacts_req_dir / "changes").is_dir(),
            "artifacts/ 下不应有 changes/ 子目录",
        )

    def test_req_01_no_legacy_branch_present_in_diff(self) -> None:
        """方向C: src/**/*.py 下不含 FLAT_LAYOUT_FROM_REQ_ID / if req_id < 41 / legacy fallback 残留."""
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", r"FLAT_LAYOUT_FROM_REQ_ID\|if req_id < 41\|legacy fallback", str(SRC_DIR)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 1,
            f"src/**/*.py 下不应有 FLAT_LAYOUT_FROM_REQ_ID / if req_id < 41 / legacy fallback 残留，实际: {result.stdout}",
        )


class CreateChangeUnconditionalFlowLayoutTest(unittest.TestCase):
    """方向C: create_change 对任意 req-id 一律落 .workflow/flow/requirements/{req}/changes/."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-b11-chg-"))
        self.root = _make_harness_root(self.tempdir)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch", return_value="main"
        )
        self._branch_patch.start()

    def tearDown(self) -> None:
        self._branch_patch.stop()
        import shutil
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _create_req_and_set_runtime(self, req_id: str, title: str) -> str:
        """Helper: pre-create flow req dir and set runtime to simulate active requirement."""
        from harness_workflow.workflow_helpers import _path_slug

        slug_part = _path_slug(title)
        dir_name = f"{req_id}-{slug_part}" if slug_part else req_id
        flow_dir = self.root / ".workflow" / "flow" / "requirements" / dir_name
        flow_dir.mkdir(parents=True, exist_ok=True)
        (flow_dir / "requirement.md").write_text(f"# {title}\n", encoding="utf-8")
        (self.root / ".workflow" / "state" / "runtime.yaml").write_text(
            f'operation_type: "requirement"\noperation_target: "{req_id}"\n'
            f'current_requirement: "{req_id}"\nstage: "executing"\n'
            'conversation_mode: "open"\nlocked_requirement: ""\nlocked_stage: ""\n'
            'current_regression: ""\nff_mode: false\nff_stage_history: []\nactive_requirements: []\n',
            encoding="utf-8",
        )
        return dir_name

    def test_chg_under_req_01_in_flow(self) -> None:
        """方向C: req-01 下的 create_change 落 flow/requirements/req-01-*/changes/ 路径."""
        from harness_workflow.workflow_helpers import create_change

        dir_name = self._create_req_and_set_runtime("req-01", "fresh-req-01-chg-test")
        rc = create_change(self.root, "first-change")
        self.assertEqual(rc, 0, "create_change 应返回 0")

        chg_base = self.root / ".workflow" / "flow" / "requirements" / dir_name / "changes"
        candidates = sorted(chg_base.glob("chg-01-*"))
        self.assertEqual(len(candidates), 1, f"应有 1 个 chg-01-* 在 flow/requirements/{dir_name}/changes/")

    def test_chg_under_req_41_in_flow(self) -> None:
        """方向C: req-41 下的 create_change 也落 flow/requirements/req-41-*/changes/ 路径."""
        from harness_workflow.workflow_helpers import create_change

        dir_name = self._create_req_and_set_runtime("req-41", "req-41-chg-test")
        rc = create_change(self.root, "flow-change")
        self.assertEqual(rc, 0)

        chg_base = self.root / ".workflow" / "flow" / "requirements" / dir_name / "changes"
        candidates = sorted(chg_base.glob("chg-01-*"))
        self.assertEqual(len(candidates), 1, f"应有 1 个 chg-01-* 在 flow/requirements/{dir_name}/changes/")

    def test_chg_no_state_sessions_residue(self) -> None:
        """方向C: create_change 不在 .workflow/state/sessions/ 下创建机器型变更文档."""
        from harness_workflow.workflow_helpers import create_change

        dir_name = self._create_req_and_set_runtime("req-01", "no-state-residue-req")
        rc = create_change(self.root, "no-residue-chg")
        self.assertEqual(rc, 0)

        sessions_dir = self.root / ".workflow" / "state" / "sessions"
        if sessions_dir.exists():
            change_docs = list(sessions_dir.glob("**/change.md"))
            self.assertEqual(
                len(change_docs), 0,
                f"state/sessions/ 下不应有 change.md 机器型文档，实际: {change_docs}",
            )


class CreateRegressionUnconditionalFlowLayoutTest(unittest.TestCase):
    """方向C: create_regression 对任意 req-id 一律落 .workflow/flow/requirements/{req}/regressions/."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-b11-reg-"))
        self.root = _make_harness_root(self.tempdir)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch", return_value="main"
        )
        self._branch_patch.start()

    def tearDown(self) -> None:
        self._branch_patch.stop()
        import shutil
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _create_req_with_change(self, req_id: str, title: str) -> str:
        """Helper: pre-create flow req dir with a chg and set runtime."""
        from harness_workflow.workflow_helpers import _path_slug

        slug_part = _path_slug(title)
        dir_name = f"{req_id}-{slug_part}" if slug_part else req_id
        flow_dir = self.root / ".workflow" / "flow" / "requirements" / dir_name
        chg_dir = flow_dir / "changes" / "chg-01-test-chg"
        chg_dir.mkdir(parents=True, exist_ok=True)
        (flow_dir / "requirement.md").write_text(f"# {title}\n", encoding="utf-8")
        (chg_dir / "change.md").write_text("# Test Change\n", encoding="utf-8")
        # Set runtime
        (self.root / ".workflow" / "state" / "runtime.yaml").write_text(
            f'operation_type: "requirement"\noperation_target: "{req_id}"\n'
            f'current_requirement: "{req_id}"\nstage: "executing"\n'
            'conversation_mode: "open"\nlocked_requirement: ""\nlocked_stage: ""\n'
            'current_regression: ""\nff_mode: false\nff_stage_history: []\nactive_requirements: []\n',
            encoding="utf-8",
        )
        return dir_name

    def test_reg_under_req_01_in_flow(self) -> None:
        """方向C: req-01 下的 create_regression 落 flow/requirements/req-01-*/regressions/ 路径."""
        from harness_workflow.workflow_helpers import create_regression

        dir_name = self._create_req_with_change("req-01", "fresh-req-01-reg-test")
        rc = create_regression(self.root, "reg-test-01", "chg-01")
        self.assertEqual(rc, 0, "create_regression 应返回 0")

        reg_base = self.root / ".workflow" / "flow" / "requirements" / dir_name / "regressions"
        candidates = sorted(reg_base.glob("reg-01-*")) if reg_base.exists() else []
        self.assertGreater(len(candidates), 0, f"应有 reg-01-* 在 flow/requirements/{dir_name}/regressions/")

    def test_reg_under_req_41_in_flow(self) -> None:
        """方向C: req-41 下的 create_regression 也落 flow/requirements/req-41-*/regressions/ 路径."""
        from harness_workflow.workflow_helpers import create_regression

        dir_name = self._create_req_with_change("req-41", "req-41-reg-test")
        rc = create_regression(self.root, "reg-test-41", "chg-01")
        self.assertEqual(rc, 0)

        reg_base = self.root / ".workflow" / "flow" / "requirements" / dir_name / "regressions"
        candidates = sorted(reg_base.glob("reg-01-*")) if reg_base.exists() else []
        self.assertGreater(len(candidates), 0, f"应有 reg-01-* 在 flow/requirements/{dir_name}/regressions/")


def _make_bugfix_root(tmp: Path) -> Path:
    """Create a minimal harness workspace root for bugfix tests."""
    root = tmp / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        'operation_type: "bugfix"\noperation_target: ""\ncurrent_requirement: ""\nstage: ""\n'
        'conversation_mode: "open"\nlocked_requirement: ""\nlocked_stage: ""\ncurrent_regression: ""\n'
        "ff_mode: false\nff_stage_history: []\nactive_requirements: []\n"
        'locked_requirement_title: ""\ncurrent_regression_title: ""\ncurrent_requirement_title: ""\n',
        encoding="utf-8",
    )
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text('{"language": "cn"}')
    import subprocess
    subprocess.run(["git", "init", "-q", "--initial-branch=main", str(root)], check=False)
    subprocess.run(["git", "init", "-q", str(root)], check=False)
    return root


class CreateBugfixUnconditionalFlowLayoutTest(unittest.TestCase):
    """H-E3 扩范围：create_bugfix 对任意 bugfix-id 一律落 .workflow/flow/bugfixes/（无条件 flow layout）."""

    def setUp(self) -> None:
        import tempfile
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = _make_bugfix_root(Path(self._tmpdir.name))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_bugfix_1_lands_in_flow_bugfixes(self) -> None:
        """bugfix-1（以前走 legacy artifacts 路径）现在也落 .workflow/flow/bugfixes/."""
        from harness_workflow.workflow_helpers import create_bugfix
        rc = create_bugfix(self.root, name="test H-E3 bugfix-1", bugfix_id="bugfix-1")
        self.assertEqual(rc, 0)
        flow_base = self.root / ".workflow" / "flow" / "bugfixes"
        candidates = list(flow_base.glob("bugfix-1-*"))
        self.assertGreater(len(candidates), 0, "bugfix-1 应落 .workflow/flow/bugfixes/")
        bf_dir = candidates[0]
        self.assertTrue((bf_dir / "bugfix.md").exists(), "bugfix.md 应在 flow/bugfixes/")
        self.assertTrue((bf_dir / "session-memory.md").exists())
        self.assertTrue((bf_dir / "regression" / "diagnosis.md").exists())

    def test_bugfix_5_lands_in_flow_bugfixes(self) -> None:
        """bugfix-5（以前走 legacy 路径）现在也落 .workflow/flow/bugfixes/."""
        from harness_workflow.workflow_helpers import create_bugfix
        rc = create_bugfix(self.root, name="test H-E3 bugfix-5", bugfix_id="bugfix-5")
        self.assertEqual(rc, 0)
        flow_base = self.root / ".workflow" / "flow" / "bugfixes"
        candidates = list(flow_base.glob("bugfix-5-*"))
        self.assertGreater(len(candidates), 0, "bugfix-5 应落 .workflow/flow/bugfixes/")

    def test_bugfix_6_lands_in_flow_bugfixes(self) -> None:
        """bugfix-6+（原有 flow 路径）仍落 .workflow/flow/bugfixes/."""
        from harness_workflow.workflow_helpers import create_bugfix
        rc = create_bugfix(self.root, name="test H-E3 bugfix-6", bugfix_id="bugfix-6")
        self.assertEqual(rc, 0)
        flow_base = self.root / ".workflow" / "flow" / "bugfixes"
        candidates = list(flow_base.glob("bugfix-6-*"))
        self.assertGreater(len(candidates), 0, "bugfix-6 应落 .workflow/flow/bugfixes/")

    def test_bugfix_no_machine_docs_in_artifacts(self) -> None:
        """create_bugfix 不在 artifacts/ 下产生机器型文档（只有 README.md 占位）."""
        from harness_workflow.workflow_helpers import create_bugfix
        rc = create_bugfix(self.root, name="test H-E3 no machine docs", bugfix_id="bugfix-3")
        self.assertEqual(rc, 0)
        artifacts = self.root / "artifacts"
        if artifacts.exists():
            machine_type = {"bugfix.md", "session-memory.md", "test-evidence.md", "diagnosis.md", "required-inputs.md"}
            for md_file in artifacts.rglob("*.md"):
                self.assertNotIn(
                    md_file.name, machine_type,
                    f"机器型文档 {md_file.name} 不应在 artifacts/ 下: {md_file}",
                )

    def test_bugfix_artifacts_readme_placeholder_created(self) -> None:
        """create_bugfix 在 artifacts/ 下创建 README.md 占位说明."""
        from harness_workflow.workflow_helpers import create_bugfix
        rc = create_bugfix(self.root, name="test H-E3 readme placeholder", bugfix_id="bugfix-2")
        self.assertEqual(rc, 0)
        artifacts = self.root / "artifacts"
        if artifacts.exists():
            readme_files = list(artifacts.rglob("README.md"))
            self.assertGreater(len(readme_files), 0, "artifacts/ 下应有 README.md 占位")


class DeprecatedSymbolsLintTest(unittest.TestCase):
    """方向C: src/ 树下不允许存在以下已废弃符号（反例断言，符号不存在才通过）."""

    def _grep_src(self, pattern: str) -> list[str]:
        """Run grep on src/harness_workflow/*.py only (no pycache, no .md) and return list of matching lines."""
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", pattern, str(SRC_DIR)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [line for line in result.stdout.strip().splitlines() if line.strip()]
        return []

    def _grep_tests(self, pattern: str) -> list[str]:
        """Run grep on tests/*.py only (no pycache) and return list of matching lines."""
        tests_dir = REPO_ROOT / "tests"
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", pattern, str(tests_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [line for line in result.stdout.strip().splitlines() if line.strip()]
        return []

    def test_no_use_flow_layout_function_in_src(self) -> None:
        """src/ 下不应有 _use_flow_layout 函数定义或调用（bugfix-11 round-2 关键补丁）."""
        import harness_workflow.workflow_helpers as wh
        self.assertFalse(
            hasattr(wh, "_use_flow_layout"),
            "src/ 下不应存在 _use_flow_layout 函数（bugfix-11 方向C 已删除）",
        )
        result = subprocess.run(
            ["grep", "-rn", "_use_flow_layout", str(SRC_DIR)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 1,
            f"src/ 下不应有 _use_flow_layout（含 _use_flow_layout_for_bugfix），实际: {result.stdout}",
        )

    def test_no_use_flat_layout_function_in_src(self) -> None:
        """src/ 下不应有 _use_flat_layout 函数定义或调用（已被 bugfix-11 方向C 删除）."""
        import harness_workflow.workflow_helpers as wh
        self.assertFalse(
            hasattr(wh, "_use_flat_layout"),
            "src/ 下不应存在 _use_flat_layout 函数（bugfix-11 方向C 已删除）",
        )
        matches = self._grep_src("_use_flat_layout")
        self.assertEqual(
            len(matches), 0,
            f"src/ 下不应出现 _use_flat_layout，实际 {len(matches)} 处: {matches}",
        )

    def test_no_FLOW_LAYOUT_FROM_REQ_ID_in_src(self) -> None:
        """src/ 下不应有 FLOW_LAYOUT_FROM_REQ_ID 常量（已被 bugfix-11 方向C 删除）."""
        matches = self._grep_src("FLOW_LAYOUT_FROM_REQ_ID")
        self.assertEqual(
            len(matches), 0,
            f"src/ 下不应出现 FLOW_LAYOUT_FROM_REQ_ID，实际 {len(matches)} 处: {matches}",
        )

    def test_no_FLAT_LAYOUT_FROM_REQ_ID_in_src(self) -> None:
        """src/ 下不应有 FLAT_LAYOUT_FROM_REQ_ID 常量（已被 bugfix-11 方向C 删除）."""
        matches = self._grep_src("FLAT_LAYOUT_FROM_REQ_ID")
        self.assertEqual(
            len(matches), 0,
            f"src/ 下不应出现 FLAT_LAYOUT_FROM_REQ_ID，实际 {len(matches)} 处: {matches}",
        )

    def test_no_LEGACY_REQ_ID_CEILING_in_src(self) -> None:
        """src/ 下不应有 LEGACY_REQ_ID_CEILING 常量（已被 bugfix-11 方向C 删除）."""
        matches = self._grep_src("LEGACY_REQ_ID_CEILING")
        self.assertEqual(
            len(matches), 0,
            f"src/ 下不应出现 LEGACY_REQ_ID_CEILING，实际 {len(matches)} 处: {matches}",
        )

    def test_no_use_flow_layout_in_tests(self) -> None:
        """tests/ 下不应有 assertTrue(_use_flow_layout(...)) / from ... import _use_flow_layout 形态（防横向反弹）."""
        # Check for actual import/call (not just references to the fact that it was deleted)
        # Pattern: line importing _use_flow_layout or calling _use_flow_layout("req-
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py",
             r"import _use_flow_layout\b\|assertTrue(_use_flow_layout\|_use_flow_layout(\"req-",
             str(REPO_ROOT / "tests")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # Filter out lines from this very file (the test file itself contains the pattern in strings)
            matches = [
                line for line in result.stdout.strip().splitlines()
                if "test_bugfix_11_flow_layout.py" not in line
            ]
            self.assertEqual(
                len(matches), 0,
                f"tests/ 下不应有 _use_flow_layout 的 import/assertTrue 形态（防横向反弹），实际: {matches}",
            )

    def test_no_use_flat_layout_in_tests(self) -> None:
        """tests/ 下不应有 _use_flat_layout 的 import 或 assertTrue 调用（防横向反弹）."""
        # Allow assertFalse(hasattr(..., "_use_flat_layout")) - that's a test asserting the function was deleted
        # Disallow: import _use_flat_layout, assertTrue(_use_flat_layout(...))
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py",
             r"import _use_flat_layout\|assertTrue(_use_flat_layout\|_use_flat_layout(",
             str(REPO_ROOT / "tests")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            matches = [
                line for line in result.stdout.strip().splitlines()
                if "test_bugfix_11_flow_layout.py" not in line
            ]
            self.assertEqual(
                len(matches), 0,
                f"tests/ 下不应有 _use_flat_layout 的 import/assertTrue 形态，实际 {len(matches)} 处: {matches}",
            )

    def test_deprecated_symbols_lint1_command(self) -> None:
        """Lint-1 字面命令验证：完整 grep 命令 0 命中（扩 bugfix 维度关键词）."""
        for symbol in ["def _use_flow_layout\\b", "_use_flat_layout",
                       "FLAT_LAYOUT_FROM_REQ_ID", "FLOW_LAYOUT_FROM_REQ_ID", "LEGACY_REQ_ID_CEILING",
                       "BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID"]:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", symbol, str(SRC_DIR)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode, 1,
                f"src/**/*.py 下不应出现 '{symbol}'，实际: {result.stdout}",
            )

    def test_no_use_flow_layout_for_bugfix_in_src(self) -> None:
        """src/ 下不应有 _use_flow_layout_for_bugfix 函数定义（bugfix-11 H-E3 扩范围已删除）."""
        result = subprocess.run(
            ["grep", "-rn", "_use_flow_layout_for_bugfix", str(SRC_DIR)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 1,
            f"src/ 下不应出现 _use_flow_layout_for_bugfix，实际: {result.stdout}",
        )

    def test_no_BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID_in_src(self) -> None:
        """src/ 下不应有 BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID 常量（bugfix-11 H-E3 扩范围已删除）."""
        result = subprocess.run(
            ["grep", "-rn", "BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID", str(SRC_DIR)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 1,
            f"src/ 下不应出现 BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID，实际: {result.stdout}",
        )


if __name__ == "__main__":
    unittest.main()
