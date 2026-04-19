"""Unit tests for `rename_requirement` / `rename_change` / `rename_bugfix`
及 `create_change` 目录 slug 化（req-26 / chg-02）。

覆盖 AC-02 及延伸：
- rename_* 必须保留 `{id}-` 前缀（req-NN / chg-NN / bugfix-N）；
- rename_requirement / rename_bugfix 必须同步 `.workflow/state/{requirements,bugfixes}/{id}-{slug}.yaml`；
- 若被 rename 的需求是 current_requirement，runtime.yaml 的 `current_requirement`
  与 `active_requirements` 要保持正确（id 不变，重写以保证持久化一致性）；
- `create_change` 目录名必须走 `slugify_preserve_unicode`，不含空格 / 全角冒号。

Helper 层直接调用，不跑 CLI（briefing 硬约束）。
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


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_requirement(
    root: Path,
    req_id: str,
    slug: str,
    title: str,
    *,
    make_current: bool = False,
) -> Path:
    """在工作区中铺一个最小化的 requirement 产出 + state yaml。"""
    req_dir = root / "artifacts" / "main" / "requirements" / f"{req_id}-{slug}"
    _write(
        req_dir / "meta.yaml",
        f'id: "{req_id}"\ntitle: "{title}"\n',
    )
    _write(req_dir / "requirement.md", f"# {title}\n\n## Goal\n...\n")
    _write(
        root / ".workflow" / "state" / "requirements" / f"{req_id}-{slug}.yaml",
        "\n".join(
            [
                f'id: "{req_id}"',
                f'title: "{title}"',
                'stage: "drafting"',
                'status: "active"',
                "",
            ]
        ),
    )
    if make_current:
        runtime_path = root / ".workflow" / "state" / "runtime.yaml"
        runtime_path.write_text(
            "\n".join(
                [
                    f'current_requirement: "{req_id}"',
                    'stage: "drafting"',
                    'conversation_mode: "harness"',
                    f'locked_requirement: "{req_id}"',
                    'locked_stage: "drafting"',
                    'current_regression: ""',
                    "ff_mode: false",
                    "ff_stage_history: []",
                    f"active_requirements:\n  - {req_id}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return req_dir


def _seed_bugfix(root: Path, bugfix_id: str, slug: str, title: str) -> Path:
    bugfix_dir = root / "artifacts" / "main" / "bugfixes" / f"{bugfix_id}-{slug}"
    _write(bugfix_dir / "meta.yaml", f'id: "{bugfix_id}"\ntitle: "{title}"\n')
    _write(bugfix_dir / "bugfix.md", f"# {title}\n")
    _write(
        root / ".workflow" / "state" / "bugfixes" / f"{bugfix_id}-{slug}.yaml",
        "\n".join(
            [
                f'id: "{bugfix_id}"',
                f'title: "{title}"',
                'stage: "drafting"',
                'status: "active"',
                "",
            ]
        ),
    )
    return bugfix_dir


def _seed_change(root: Path, req_dir: Path, chg_id: str, slug: str, title: str) -> Path:
    chg_dir = req_dir / "changes" / f"{chg_id}-{slug}"
    _write(chg_dir / "meta.yaml", f'id: "{chg_id}"\ntitle: "{title}"\n')
    _write(chg_dir / "change.md", f"# {title}\n")
    return chg_dir


class RenameRequirementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-rename-req-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_rename_requirement_preserves_id_prefix(self) -> None:
        from harness_workflow.workflow_helpers import rename_requirement

        _seed_requirement(self.root, "req-07", "old-title", "Old Title")
        rc = rename_requirement(self.root, "req-07", "New Fancy Title")
        self.assertEqual(rc, 0)

        req_base = self.root / "artifacts" / "main" / "requirements"
        dirs = [d.name for d in req_base.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        # id 前缀保留 req-07，slug 化为 new-fancy-title
        self.assertTrue(dirs[0].startswith("req-07-"), f"unexpected dir: {dirs[0]}")
        self.assertIn("new-fancy-title", dirs[0])
        self.assertNotIn(" ", dirs[0])

        # state yaml 改名：旧 yaml 消失，新 yaml 存在
        state_dir = self.root / ".workflow" / "state" / "requirements"
        state_files = [p.name for p in state_dir.iterdir() if p.is_file()]
        self.assertNotIn("req-07-old-title.yaml", state_files)
        self.assertIn(f"{dirs[0]}.yaml", state_files)

    def test_rename_requirement_syncs_runtime(self) -> None:
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            rename_requirement,
        )

        _seed_requirement(
            self.root, "req-09", "legacy-name", "Legacy Name", make_current=True
        )
        rc = rename_requirement(self.root, "req-09", "全新标题：带 空格")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        # id 不变，仍为 req-09（rename 不改 id）
        self.assertEqual(str(runtime["current_requirement"]), "req-09")
        active = runtime.get("active_requirements", [])
        self.assertTrue(any(str(x) == "req-09" for x in active))

        # 目录名新前缀保留，CJK 保留，全角冒号 / 空格被折叠
        req_base = self.root / "artifacts" / "main" / "requirements"
        dirs = [d.name for d in req_base.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        self.assertTrue(dirs[0].startswith("req-09-"))
        self.assertNotIn(" ", dirs[0])
        self.assertNotIn("：", dirs[0])
        self.assertIn("全新标题", dirs[0])


class RenameBugfixTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-rename-bugfix-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_rename_bugfix_preserves_id_prefix_and_state(self) -> None:
        from harness_workflow.workflow_helpers import rename_bugfix

        _seed_bugfix(self.root, "bugfix-3", "broken-login", "Broken Login")
        rc = rename_bugfix(self.root, "bugfix-3", "Login Crash On Safari")
        self.assertEqual(rc, 0)

        base = self.root / "artifacts" / "main" / "bugfixes"
        dirs = [d.name for d in base.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        # id 前缀保留 bugfix-3
        self.assertTrue(dirs[0].startswith("bugfix-3-"), f"unexpected: {dirs[0]}")
        self.assertIn("login-crash-on-safari", dirs[0])
        self.assertNotIn(" ", dirs[0])

        # state yaml 改名
        state_dir = self.root / ".workflow" / "state" / "bugfixes"
        state_files = [p.name for p in state_dir.iterdir() if p.is_file()]
        self.assertNotIn("bugfix-3-broken-login.yaml", state_files)
        self.assertIn(f"{dirs[0]}.yaml", state_files)


class RenameChangeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-rename-change-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_rename_change_preserves_id_prefix(self) -> None:
        from harness_workflow.workflow_helpers import rename_change

        req_dir = _seed_requirement(
            self.root, "req-11", "host-req", "Host Requirement", make_current=True
        )
        _seed_change(self.root, req_dir, "chg-04", "old-change-name", "Old Change Name")

        rc = rename_change(self.root, "chg-04", "重命名：新变更")
        self.assertEqual(rc, 0)

        changes_dir = req_dir / "changes"
        dirs = [d.name for d in changes_dir.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        # chg-04 前缀保留，全角冒号被折叠为 '-'
        self.assertTrue(dirs[0].startswith("chg-04-"), f"unexpected: {dirs[0]}")
        self.assertNotIn(" ", dirs[0])
        self.assertNotIn("：", dirs[0])
        self.assertIn("重命名", dirs[0])


class CreateChangeSlugTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-create-change-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_create_change_directory_uses_slugify(self) -> None:
        from harness_workflow.workflow_helpers import create_change

        _seed_requirement(
            self.root, "req-13", "host-req", "Host Req", make_current=True
        )

        rc = create_change(self.root, "新变更：含 空格 和 冒号")
        self.assertEqual(rc, 0)

        req_dir = self.root / "artifacts" / "main" / "requirements" / "req-13-host-req"
        changes_dir = req_dir / "changes"
        self.assertTrue(changes_dir.exists())
        dirs = [d.name for d in changes_dir.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        name = dirs[0]
        # chg-NN- 前缀保留；空格 / 全角冒号被折叠为 '-'；CJK 保留
        self.assertRegex(name, r"^chg-\d+-")
        self.assertNotIn(" ", name)
        self.assertNotIn("：", name)
        self.assertIn("新变更", name)


if __name__ == "__main__":
    unittest.main()
