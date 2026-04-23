"""bugfix-3 防回归 — runtime ↔ state yaml 同步、regression 路由消费、archive 选目标。

覆盖三组缺陷的不变式（regression 阶段先红，executing 阶段修绿）：

1. ``workflow_next`` 在 ``current_regression`` 非空时必须读 ``decision.md`` 路由 stage，
   不得无脑按 sequence + 1（缺陷 1 / sug-12）。
2. ``enter_workflow`` 切换 id 后，``operation_type`` / ``operation_target`` 必须与
   新 id 前缀一致；后续 ``workflow_next`` 必须把 stage 同步到 bugfix yaml（缺陷 2 / sug-13）。
3. ``harness archive`` 默认目标必须 = ``runtime.current_requirement``，不得从 done 列表
   盲取首个（缺陷 3 / 今日活证）。
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_workspace(tmpdir: Path, language: str = "english") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / "artifacts" / "main" / "regressions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime(
    root: Path,
    *,
    stage: str,
    operation_type: str = "requirement",
    operation_target: str = "",
    current_requirement: str = "",
    current_regression: str = "",
    active_ids: list[str] | None = None,
) -> None:
    active_ids = active_ids or []
    lines = [
        f'operation_type: "{operation_type}"',
        f'operation_target: "{operation_target}"',
        f'current_requirement: "{current_requirement}"',
        'current_requirement_title: ""',
        f'stage: "{stage}"',
        'conversation_mode: "open"',
        'locked_requirement: ""',
        'locked_stage: ""',
        f'current_regression: "{current_regression}"',
        'current_regression_title: ""',
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


def _seed_requirement_state(
    root: Path,
    req_id: str,
    slug: str,
    title: str,
    *,
    stage: str = "requirement_review",
    status: str = "active",
) -> Path:
    state_path = (
        root / ".workflow" / "state" / "requirements" / f"{req_id}-{slug}.yaml"
    )
    _write(
        state_path,
        "\n".join(
            [
                f'id: "{req_id}"',
                f'title: "{title}"',
                f'stage: "{stage}"',
                f'status: "{status}"',
                'created_at: "2026-04-23"',
                'started_at: "2026-04-23"',
                'completed_at: ""',
                "stage_timestamps: {}",
                'description: ""',
                "",
            ]
        ),
    )
    return state_path


def _seed_bugfix_state(
    root: Path,
    bugfix_id: str,
    slug: str,
    title: str,
    *,
    stage: str = "regression",
    status: str = "active",
) -> Path:
    state_path = (
        root / ".workflow" / "state" / "bugfixes" / f"{bugfix_id}-{slug}.yaml"
    )
    _write(
        state_path,
        "\n".join(
            [
                f'id: "{bugfix_id}"',
                f'title: "{title}"',
                f'stage: "{stage}"',
                f'status: "{status}"',
                "",
            ]
        ),
    )
    return state_path


def _seed_requirement_dir(root: Path, req_id: str, slug: str) -> Path:
    """Create artifacts/main/requirements/{req_id}-{slug}/ skeleton."""
    req_dir = root / "artifacts" / "main" / "requirements" / f"{req_id}-{slug}"
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "regressions").mkdir(exist_ok=True)
    return req_dir


def _seed_regression_dir(
    req_dir: Path,
    reg_id: str,
    slug: str,
    decision_text: str,
) -> Path:
    """Create regressions/{reg_id}-{slug}/decision.md with given text."""
    reg_dir = req_dir / "regressions" / f"{reg_id}-{slug}"
    reg_dir.mkdir(parents=True, exist_ok=True)
    (reg_dir / "decision.md").write_text(decision_text, encoding="utf-8")
    return reg_dir


# ---------------------------------------------------------------------------
# 缺陷 1：workflow_next 读 regression decision 路由
# ---------------------------------------------------------------------------


class RegressionRouteConsumptionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="bugfix3-reg-route-"))
        self.root = _make_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_next_consumes_regression_route_yaml_frontmatter(self) -> None:
        """decision.md 含 yaml frontmatter `route_to: planning` → next 切到 planning。

        当前 stage = acceptance（req 工作流），默认 sequence + 1 = done；
        但 reg 路由 = planning，应优先用 planning。
        """
        from harness_workflow.workflow_helpers import (
            load_simple_yaml,
            workflow_next,
        )

        state_path = _seed_requirement_state(
            self.root, "req-36", "install-fix", "Install Fix",
            stage="acceptance", status="active",
        )
        req_dir = _seed_requirement_dir(self.root, "req-36", "install-fix")
        decision_text = (
            "---\n"
            "route_to: planning\n"
            "---\n"
            "# Regression Decision\n\n"
            "## 1. Decision Status\n`confirmed`\n"
        )
        _seed_regression_dir(req_dir, "reg-01", "demo", decision_text)

        _write_runtime(
            self.root,
            stage="acceptance",
            operation_type="requirement",
            operation_target="req-36",
            current_requirement="req-36",
            current_regression="reg-01",
            active_ids=["req-36"],
        )

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        # runtime.stage 应被切到 planning（reg 路由覆盖 sequence + 1）
        runtime = load_simple_yaml(
            self.root / ".workflow" / "state" / "runtime.yaml"
        )
        self.assertEqual(
            runtime.get("stage"),
            "planning",
            msg=f"runtime.stage should follow reg.decision route_to=planning, got {runtime!r}",
        )

        # state yaml 同步
        state = load_simple_yaml(state_path)
        self.assertEqual(state.get("stage"), "planning")

        # current_regression 应被清空（消费完）
        self.assertEqual(str(runtime.get("current_regression", "")).strip(), "")

    def test_next_consumes_regression_route_text_marker(self) -> None:
        """decision.md 无 frontmatter，含中文 marker '路由：planning' → next 切到 planning。"""
        from harness_workflow.workflow_helpers import (
            load_simple_yaml,
            workflow_next,
        )

        state_path = _seed_requirement_state(
            self.root, "req-37", "demo", "Demo",
            stage="acceptance", status="active",
        )
        req_dir = _seed_requirement_dir(self.root, "req-37", "demo")
        decision_text = (
            "# Regression Decision\n\n"
            "## 1. Decision Status\n`confirmed`（真实问题；路由：planning，拆新 chg）。\n\n"
            "## 3. Follow-Up\n- 路由动作：harness next → planning\n"
        )
        _seed_regression_dir(req_dir, "reg-02", "demo2", decision_text)

        _write_runtime(
            self.root,
            stage="acceptance",
            operation_type="requirement",
            operation_target="req-37",
            current_requirement="req-37",
            current_regression="reg-02",
            active_ids=["req-37"],
        )

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        runtime = load_simple_yaml(
            self.root / ".workflow" / "state" / "runtime.yaml"
        )
        self.assertEqual(runtime.get("stage"), "planning")
        state = load_simple_yaml(state_path)
        self.assertEqual(state.get("stage"), "planning")

    def test_next_falls_back_to_sequence_when_no_route(self) -> None:
        """current_regression 非空但 decision.md 不含可解析路由 → 走默认 sequence（向后兼容）。"""
        from harness_workflow.workflow_helpers import (
            load_simple_yaml,
            workflow_next,
        )

        state_path = _seed_requirement_state(
            self.root, "req-38", "demo3", "Demo3",
            stage="executing", status="active",
        )
        req_dir = _seed_requirement_dir(self.root, "req-38", "demo3")
        decision_text = "# Regression Decision\n\n暂无明确路由说明。\n"
        _seed_regression_dir(req_dir, "reg-03", "demo3", decision_text)

        _write_runtime(
            self.root,
            stage="executing",
            operation_type="requirement",
            operation_target="req-38",
            current_requirement="req-38",
            current_regression="reg-03",
            active_ids=["req-38"],
        )

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        # 默认 sequence: executing → testing
        runtime = load_simple_yaml(
            self.root / ".workflow" / "state" / "runtime.yaml"
        )
        self.assertEqual(runtime.get("stage"), "testing")
        state = load_simple_yaml(state_path)
        self.assertEqual(state.get("stage"), "testing")


# ---------------------------------------------------------------------------
# 缺陷 2：enter_workflow + load_runtime 修复 operation_type 残留
# ---------------------------------------------------------------------------


class OperationTypeSyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="bugfix3-op-type-"))
        self.root = _make_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_enter_workflow_resets_operation_type_to_bugfix(self) -> None:
        """从 req-X 切到 bugfix-Y 后，operation_type 必须自动变为 bugfix。"""
        from harness_workflow.workflow_helpers import (
            enter_workflow,
            load_simple_yaml,
        )

        # 初始状态：上次操作 req-99
        _seed_requirement_state(
            self.root, "req-99", "old", "Old",
            stage="done", status="active",
        )
        _seed_bugfix_state(
            self.root, "bugfix-7", "login", "Login",
            stage="regression", status="active",
        )
        _write_runtime(
            self.root,
            stage="done",
            operation_type="requirement",
            operation_target="req-99",
            current_requirement="req-99",
            active_ids=["req-99", "bugfix-7"],
        )

        # 切换到 bugfix-7
        rc = enter_workflow(self.root, "bugfix-7")
        self.assertEqual(rc, 0)

        runtime = load_simple_yaml(
            self.root / ".workflow" / "state" / "runtime.yaml"
        )
        self.assertEqual(
            runtime.get("operation_type"),
            "bugfix",
            msg=f"enter bugfix-7 后 operation_type 必须切为 bugfix, got {runtime!r}",
        )
        self.assertEqual(runtime.get("operation_target"), "bugfix-7")
        self.assertEqual(runtime.get("current_requirement"), "bugfix-7")

    def test_next_after_enter_syncs_bugfix_yaml_not_requirement(self) -> None:
        """enter bugfix-Y 后 next，stage 必须写到 state/bugfixes/Y.yaml，不写到 requirements。"""
        from harness_workflow.workflow_helpers import (
            enter_workflow,
            load_simple_yaml,
            workflow_next,
        )

        req_path = _seed_requirement_state(
            self.root, "req-99", "old", "Old",
            stage="done", status="active",
        )
        bugfix_path = _seed_bugfix_state(
            self.root, "bugfix-7", "login", "Login",
            stage="regression", status="active",
        )
        _write_runtime(
            self.root,
            stage="done",  # 上次 req-99 的 stage
            operation_type="requirement",
            operation_target="req-99",
            current_requirement="req-99",
            active_ids=["req-99", "bugfix-7"],
        )

        # 切换到 bugfix-7（应同步重置 stage / operation_type）
        enter_workflow(self.root, "bugfix-7")

        # 切完后手工把 runtime.stage 设到 bugfix 流的起点（regression）
        # —— 模拟实际 enter 后用户手工或后续逻辑会把 stage 摆到 bugfix 流。
        # bugfix-3 现实场景：runtime.stage 已经在 regression（因为是从 bugfix create 来的），
        # 这里我们显式 patch runtime.stage 到 regression 模拟同步状态。
        runtime_path = self.root / ".workflow" / "state" / "runtime.yaml"
        runtime = load_simple_yaml(runtime_path)
        runtime["stage"] = "regression"
        from harness_workflow.workflow_helpers import save_requirement_runtime
        save_requirement_runtime(self.root, runtime)

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        # bugfix yaml 应该被推进到 executing
        bugfix_state = load_simple_yaml(bugfix_path)
        self.assertEqual(
            bugfix_state.get("stage"),
            "executing",
            msg=f"bugfix yaml stage 必须被同步推进到 executing, got {bugfix_state!r}",
        )
        # 反向：requirement yaml 不能被误改
        req_state = load_simple_yaml(req_path)
        self.assertEqual(
            req_state.get("stage"),
            "done",
            msg=f"requirement yaml 不应被误改, got {req_state!r}",
        )

    def test_load_runtime_fixes_stale_operation_type(self) -> None:
        """runtime.yaml 残留 operation_type=requirement 但 current=bugfix-* → 加载时自愈。"""
        from harness_workflow.workflow_helpers import load_requirement_runtime

        _write_runtime(
            self.root,
            stage="regression",
            operation_type="requirement",  # 残留值
            operation_target="req-99",      # 残留值
            current_requirement="bugfix-3", # 真实当前
        )

        payload = load_requirement_runtime(self.root)
        self.assertEqual(
            payload.get("operation_type"),
            "bugfix",
            msg="load_requirement_runtime 必须根据 current_requirement 前缀自愈 operation_type",
        )
        self.assertEqual(payload.get("operation_target"), "bugfix-3")


# ---------------------------------------------------------------------------
# 缺陷 3：archive 默认目标 = current_requirement
# ---------------------------------------------------------------------------


class ArchiveDefaultTargetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="bugfix3-archive-target-"))
        self.root = _make_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_prompt_uses_current_requirement_as_preselect(self) -> None:
        """non-tty 场景下，archive 必须把 current_requirement 作为默认值。

        模拟主 agent 跑 ``harness archive``（无参）的真实路径：
        - cli.py 收集 done_reqs (含 bugfix-2 + bugfix-3 两条)
        - 调用 prompt_requirement_selection(done_reqs, preselect=current_requirement)
        - non-tty 情况下，必须返回 current_requirement (bugfix-2)，不是列表首个 (bugfix-3)。
        """
        from harness_workflow.cli import prompt_requirement_selection

        done_reqs = [
            {"req_id": "bugfix-3", "title": "Bugfix Three", "stage": "done"},
            {"req_id": "bugfix-2", "title": "Bugfix Two", "stage": "done"},
        ]

        # 关键断言：non-tty 必须返回 preselect = current_requirement
        # 这条单测当前会绿（prompt_requirement_selection 已支持 preselect），
        # 但 cli.py 的 archive 分支没传 preselect → 真实场景下 preselect=None。
        # 第二条断言验证这个 bug 路径：
        result_with_preselect = prompt_requirement_selection(
            done_reqs, preselect="bugfix-2"
        )
        self.assertEqual(result_with_preselect, "bugfix-2")

        # 当前 cli.py archive 分支调用：preselect=args.requirement (=None)
        # 无 preselect → 默认取首个 → bugfix-3（错），暴露 cli.py 没读 current_requirement。
        result_without_preselect = prompt_requirement_selection(
            done_reqs, preselect=None
        )
        # 当前实现：返回 done_reqs[0] = bugfix-3（这就是用户活证里的 bug）
        # 不对此条做断言（行为正确但调用方误用），重点在 cli 层下一条。
        self.assertEqual(result_without_preselect, "bugfix-3")

    def test_cli_archive_passes_current_requirement_as_preselect(self) -> None:
        """cli.main archive 分支必须从 runtime 读 current_requirement 并传给 preselect。

        通过 monkey-patch prompt_requirement_selection 捕获实际传入的 preselect，
        断言它 = runtime.current_requirement。
        """
        from harness_workflow import cli as cli_mod

        # seed 两条 done bugfix
        _seed_bugfix_state(
            self.root, "bugfix-2", "two", "Bugfix Two",
            stage="done", status="active",
        )
        _seed_bugfix_state(
            self.root, "bugfix-3", "three", "Bugfix Three",
            stage="done", status="active",
        )
        _write_runtime(
            self.root,
            stage="done",
            operation_type="bugfix",
            operation_target="bugfix-2",
            current_requirement="bugfix-2",
            active_ids=["bugfix-2", "bugfix-3"],
        )

        captured: dict = {}
        original_prompt = cli_mod.prompt_requirement_selection

        def _spy(reqs, preselect=None):
            captured["preselect"] = preselect
            captured["req_ids"] = [r["req_id"] for r in reqs]
            return None  # 中止后续 archive 操作（避免真跑 shutil.move）

        cli_mod.prompt_requirement_selection = _spy
        try:
            old_argv = sys.argv
            sys.argv = ["harness", "archive", "--root", str(self.root)]
            try:
                rc = cli_mod.main()
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
            finally:
                sys.argv = old_argv
        finally:
            cli_mod.prompt_requirement_selection = original_prompt

        # 关键断言：preselect 必须 = runtime.current_requirement (bugfix-2)
        self.assertEqual(
            captured.get("preselect"),
            "bugfix-2",
            msg=(
                "cli.main archive 分支必须把 runtime.current_requirement 传给 "
                f"preselect，captured={captured!r}, rc={rc}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
