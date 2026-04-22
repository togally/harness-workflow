r"""End-to-end smoke for req-26 / chg-06 (AC-07).

本 smoke 把 sug-01 ~ sug-06 六条修复组合起来跑一次完整生命周期，在 tempdir 隔离
环境里通过 helper 函数（非真 CLI）模拟：

    init → requirement → change → next×N → regression(--confirm / --testing)
         → rename → archive

每步后逐条验证：

- AC-01：`regression_action(confirm=True)` 后 `runtime.current_regression` 仍在；
  随后的 `regression_action(to_testing=True)` 仍可识别并消费。
- AC-02：`create_change` 与 `rename_requirement` / `rename_change` 产出目录名无
  空格、无全角符号、保留 `{id}-` 前缀；rename 完成后 state yaml 与 runtime.yaml
  保持一致。
- AC-03：`workflow_next` 推进 stage 后，`.workflow/state/requirements/{id}.yaml`
  的 `stage` 字段与 runtime.yaml 同步；无需人工改 yaml 即可走到 done。
- AC-04：`create_regression` 产出目录以 `reg-\d+-` 前缀开头，kebab-case，无空格
  与全角符号。
- AC-05：`archive_requirement` 归档路径 `artifacts/{branch}/archive/` 下 branch
  段只出现一次，不得出现双层 branch。
- AC-06（降级为静态核查）：所有 stage 角色文件 / stage-role.md 含"对人文档"契约；
  scaffold_v2 镜像与本仓库 roles 目录文本一致。
- AC-07：以上六点在**同一个 tempdir 会话**中全部成立 → 一次端到端 smoke 通过。

硬约束（briefing 一致）：

- 不跑真 `harness` CLI 命令；
- 不污染本仓库 `.workflow/state/` 与 `artifacts/`；
- 不改 chg-01~05 已完成的代码。
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


# ---------------------------------------------------------------------------
# Helpers：铺最小工作区
# ---------------------------------------------------------------------------


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    """构造最小可用的 harness workspace（与既有 test_*_helpers.py 对齐）。"""
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(
            [
                'operation_type: ""',
                'operation_target: ""',
                'current_requirement: ""',
                'stage: ""',
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
    return root


def _single_dir(base: Path) -> Path:
    dirs = [d for d in base.iterdir() if d.is_dir()]
    assert len(dirs) == 1, f"expected exactly one dir under {base}, got {dirs}"
    return dirs[0]


# ---------------------------------------------------------------------------
# 主 smoke 用例（AC-07 终极集成）
# ---------------------------------------------------------------------------


class SmokeE2ETest(unittest.TestCase):
    """端到端 smoke：一个 tempdir 跑完整生命周期，联动验证 AC-01~05。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-smoke-req26-"))
        self.root = _make_harness_workspace(self.tempdir, language="english")
        # 将 git branch 固定为 "main"，避免依赖测试机真实 git 状态
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()
        # archive 入口可能交互式询问 commit，mock input 直接回 "n"
        self._input_patch = mock.patch("builtins.input", return_value="n")
        self._input_patch.start()

    def tearDown(self) -> None:
        self._input_patch.stop()
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_full_lifecycle_smoke(self) -> None:
        from harness_workflow.workflow_helpers import (
            archive_requirement,
            create_change,
            create_regression,
            create_requirement,
            load_requirement_runtime,
            load_simple_yaml,
            regression_action,
            rename_change,
            rename_requirement,
            workflow_next,
        )

        # -----------------------------------------------------------------
        # 1) 创建 requirement + 立即 rename，把 CJK 冒号 / 空格洗掉（AC-02 合并 B）
        # -----------------------------------------------------------------
        # create_requirement 本身不做 slug 化，业务流中可由 rename 一次性清洗。
        rc = create_requirement(self.root, "新需求 测试 流程")
        self.assertEqual(rc, 0, "create_requirement should succeed")

        runtime = load_requirement_runtime(self.root)
        req_id = str(runtime["current_requirement"])
        self.assertRegex(req_id, r"^req-\d+$")

        # rename 一次，确保目录命名走 slugify_preserve_unicode
        rc = rename_requirement(self.root, req_id, "新需求：测试 流程")
        self.assertEqual(rc, 0, "rename_requirement should succeed")

        reqs_base = self.root / "artifacts" / "main" / "requirements"
        req_dir = _single_dir(reqs_base)
        # AC-02：保留 req-{n}- 前缀；无空格 / 无全角冒号
        self.assertTrue(
            req_dir.name.startswith(f"{req_id}-"),
            f"dir {req_dir.name} must preserve {req_id}- prefix",
        )
        self.assertNotIn(" ", req_dir.name, f"dir {req_dir.name} must not contain space")
        self.assertNotIn("：", req_dir.name, f"dir {req_dir.name} must not contain fullwidth colon")
        self.assertIn("新需求", req_dir.name)

        # rename 后 state yaml 文件名 = 新目录名；内部 title 字段已更新
        state_dir = self.root / ".workflow" / "state" / "requirements"
        state_files = [p.name for p in state_dir.iterdir() if p.is_file()]
        self.assertIn(
            f"{req_dir.name}.yaml", state_files,
            f"state yaml file should be renamed to {req_dir.name}.yaml, got {state_files}",
        )

        # runtime.current_requirement 仍是纯 id，active_requirements 仍含该 id
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(str(runtime["current_requirement"]), req_id)
        self.assertIn(req_id, [str(x) for x in runtime.get("active_requirements", [])])

        # -----------------------------------------------------------------
        # 2) 推进 requirement_review → planning（AC-03）
        # P-1 default-pick C（req-31 chg-01）：planning 替代 changes_review
        # -----------------------------------------------------------------
        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        state_path = state_dir / f"{req_dir.name}.yaml"
        state = load_simple_yaml(state_path)
        self.assertEqual(state.get("stage"), "planning",
                         f"state yaml stage mismatch after first next: {state}")
        self.assertEqual(str(load_requirement_runtime(self.root)["stage"]), "planning")

        # -----------------------------------------------------------------
        # 3) 创建 change（AC-02：create_change 走 slugify_preserve_unicode）
        # -----------------------------------------------------------------
        rc = create_change(self.root, "新变更：含 空格 和 中文冒号：再一个")
        self.assertEqual(rc, 0)

        changes_dir = req_dir / "changes"
        chg_dir = _single_dir(changes_dir)
        self.assertRegex(chg_dir.name, r"^chg-\d+-")
        self.assertNotIn(" ", chg_dir.name)
        self.assertNotIn("：", chg_dir.name)
        self.assertIn("新变更", chg_dir.name)

        # 期间做一次 rename_change，验证 chg-NN 前缀保留
        old_chg_name = chg_dir.name
        chg_id_prefix = old_chg_name.split("-", 2)[0] + "-" + old_chg_name.split("-", 2)[1]
        # 形如 "chg-01"
        self.assertRegex(chg_id_prefix, r"^chg-\d+$")
        rc = rename_change(self.root, chg_id_prefix, "重命名后的 新变更")
        self.assertEqual(rc, 0)
        new_chg_dir = _single_dir(changes_dir)
        self.assertTrue(
            new_chg_dir.name.startswith(f"{chg_id_prefix}-"),
            f"renamed change dir {new_chg_dir.name} must keep {chg_id_prefix}- prefix",
        )
        self.assertNotIn(" ", new_chg_dir.name)
        self.assertNotIn("：", new_chg_dir.name)

        # -----------------------------------------------------------------
        # 4) 连推 next，直到 executing
        # -----------------------------------------------------------------
        # P-1 default-pick C（req-31 chg-01）：planning → ready_for_execution → executing
        # 合并后序列：planning 直接推进到 ready_for_execution（不再经过 plan_review）
        # 注意 ready_for_execution → executing 需要 execute=True
        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)
        self.assertEqual(
            load_simple_yaml(state_path).get("stage"), "ready_for_execution",
            "state yaml stage should be ready_for_execution",
        )

        rc = workflow_next(self.root, execute=True)
        self.assertEqual(rc, 0)
        self.assertEqual(
            load_simple_yaml(state_path).get("stage"), "executing",
            "state yaml stage should be executing",
        )

        # -----------------------------------------------------------------
        # 5) executing → testing
        # -----------------------------------------------------------------
        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)
        self.assertEqual(load_simple_yaml(state_path).get("stage"), "testing")

        # -----------------------------------------------------------------
        # 6) testing 阶段触发一次 regression（AC-04 + AC-01）
        # -----------------------------------------------------------------
        rc = create_regression(self.root, "问题 描述 with spaces")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        reg_id = str(runtime["current_regression"])
        self.assertRegex(reg_id, r"^reg-\d+$", f"current_regression should be pure reg id, got {reg_id}")

        # regression 目录命名 AC-04：reg-NN- 前缀、kebab-case、无空格
        reg_base = req_dir / "regressions"
        self.assertTrue(reg_base.exists(), "regressions base must exist under req_dir")
        reg_dir = _single_dir(reg_base)
        self.assertTrue(
            reg_dir.name.startswith(f"{reg_id}-"),
            f"regression dir {reg_dir.name} must start with {reg_id}-",
        )
        self.assertNotIn(" ", reg_dir.name)
        self.assertIn("问题", reg_dir.name)
        self.assertIn("描述", reg_dir.name)

        # AC-01：--confirm 不得清空 current_regression
        rc = regression_action(self.root, confirm=True)
        self.assertEqual(rc, 0)
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(
            str(runtime["current_regression"]), reg_id,
            "--confirm must NOT clear current_regression (AC-01)",
        )

        # meta.yaml 应标记 status: confirmed
        meta_text = (reg_dir / "meta.yaml").read_text(encoding="utf-8")
        self.assertIn('status: "confirmed"', meta_text)

        # --testing 仍能继续消费 regression，stage 回到 testing
        rc = regression_action(self.root, to_testing=True)
        self.assertEqual(rc, 0)
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(str(runtime["current_regression"]), "",
                         "--testing should clear current_regression")
        self.assertEqual(str(runtime["stage"]), "testing")

        # -----------------------------------------------------------------
        # 7) testing → acceptance → done（AC-03 持续核对）
        # -----------------------------------------------------------------
        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)
        self.assertEqual(load_simple_yaml(state_path).get("stage"), "acceptance")

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)
        state = load_simple_yaml(state_path)
        self.assertEqual(state.get("stage"), "done")
        self.assertEqual(state.get("status"), "done",
                         "推到 done 时 status 应自动写回为 done（AC-03）")

        # runtime 与 state yaml 保持一致
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(str(runtime["stage"]), "done")

        # -----------------------------------------------------------------
        # 8) archive（AC-05：路径无双层 branch）
        # -----------------------------------------------------------------
        rc = archive_requirement(self.root, req_dir.name)
        self.assertEqual(rc, 0)

        archive_root = self.root / "artifacts" / "main" / "archive"
        self.assertTrue(archive_root.exists())
        # AC-05：archive 下**不得**出现 `main/` 子目录
        self.assertFalse(
            (archive_root / "main").exists(),
            "AC-05 failed: archive/main/ subdir found (double branch)",
        )
        # req-28 / chg-03（AC-14）：req-* 归档落到 archive/requirements/<dir>
        archived_dir = archive_root / "requirements" / req_dir.name
        self.assertTrue(
            archived_dir.exists(),
            f"archived directory should sit under archive/requirements/, got contents: "
            f"{[p.name for p in archive_root.rglob('*') if p.is_dir()]}",
        )
        rel = archived_dir.relative_to(self.root).as_posix()
        self.assertEqual(
            rel.count("/main/"),
            1,
            f"archive path {rel} should contain /main/ exactly once (AC-05)",
        )


# ---------------------------------------------------------------------------
# AC-06 静态契约核查（降级为文本断言）
# ---------------------------------------------------------------------------


class DualTrackContractStaticTest(unittest.TestCase):
    """AC-06：对人文档机制的静态契约核查。

    对人文档由各 stage 角色在 agent 实际执行时产出，本 smoke 不模拟 agent 写文，
    降级为 **契约文本存在性** 断言：

    1. `stage-role.md` 含"对人文档输出契约"章节；
    2. 7 个 stage 角色文件（requirement-review / planning / executing / testing /
       acceptance / regression / done）各自含"对人文档输出"条目；
    3. scaffold_v2 镜像与本仓库 roles 目录中上述文件文本完全一致。
    """

    ROLES_DIR = REPO_ROOT / ".workflow" / "context" / "roles"
    MIRROR_DIR = (
        REPO_ROOT
        / "src"
        / "harness_workflow"
        / "assets"
        / "scaffold_v2"
        / ".workflow"
        / "context"
        / "roles"
    )
    STAGE_ROLE_FILES = [
        "requirement-review.md",
        "planning.md",
        "executing.md",
        "testing.md",
        "acceptance.md",
        "regression.md",
        "done.md",
    ]

    def test_stage_role_has_dual_track_contract_section(self) -> None:
        text = (self.ROLES_DIR / "stage-role.md").read_text(encoding="utf-8")
        self.assertIn(
            "对人文档输出契约", text,
            "stage-role.md must contain 对人文档输出契约 section (AC-06 contract outline)",
        )
        # 五项契约必须齐全
        for marker in ["契约 1", "契约 2", "契约 3", "契约 4", "契约 5"]:
            self.assertIn(marker, text, f"stage-role.md missing marker: {marker}")

    def test_each_stage_role_has_dual_track_output_block(self) -> None:
        for fname in self.STAGE_ROLE_FILES:
            path = self.ROLES_DIR / fname
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                "对人文档输出", text,
                f"{fname} must contain 对人文档输出 section (AC-06 hard gate)",
            )

    def test_scaffold_v2_mirror_matches_roles(self) -> None:
        """scaffold_v2 镜像必须与仓库 roles/ 一致，防止 install 后模板漂移。"""
        targets = [
            "base-role.md",
            "stage-role.md",
            *self.STAGE_ROLE_FILES,
        ]
        for fname in targets:
            src_path = self.ROLES_DIR / fname
            mirror_path = self.MIRROR_DIR / fname
            self.assertTrue(src_path.exists(), f"源文件缺失：{src_path}")
            self.assertTrue(mirror_path.exists(), f"scaffold_v2 镜像缺失：{mirror_path}")
            self.assertEqual(
                src_path.read_text(encoding="utf-8"),
                mirror_path.read_text(encoding="utf-8"),
                f"scaffold_v2 镜像与 roles/ 文本不一致：{fname}",
            )


if __name__ == "__main__":
    unittest.main()
