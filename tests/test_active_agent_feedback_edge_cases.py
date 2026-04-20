"""bugfix-3（新）边界用例补强（testing Subagent-L1 独立复核新增）。

本文件由 testing 阶段 Subagent-L1 在独立复核 executing 3 条红用例
（`tests/test_active_agent_and_feedback_relocation.py`）后补充，覆盖 executing
未锁定但仍然属于 bugfix.md Validation Criteria 语义范围的三条边界行为：

- **E1（bugfix.md VC#3 / compat mode）** — `test_update_repo_compat_mode_warning_when_active_agent_missing`
  旧仓没有 `active_agent` 字段时：stdout 必须打印 "active agent not set; refreshing enabled set (compat mode)"
  警告 + 实际走 `enabled[]` 回退（四个 agent 目录都会被 install_local_skills / _managed_file_contents 刷新）。
  锁定诊断 §1.2 F "缺 active_agent 时 warning + 兼容模式" 这条 CLI 合约。

- **E2（bugfix.md VC#5 / 数据安全）** — `test_feedback_migration_does_not_overwrite_existing_new_path`
  `.harness/feedback.jsonl`（legacy，3 行）+ `.workflow/state/feedback/feedback.jsonl`
  （new，2 行）同时存在时，`update_repo` 必须**拒绝迁移**（守住 `if old.exists() and not new.exists()`
  的条件），新位置文件内容保持 2 行原样，legacy 位置保留（下次人工合并）。
  锁定 workflow_helpers.py:3001 迁移分支的防覆盖断言——若有人将条件误改为 `or` 或拆分成
  overwrite 语义，2 行数据会被 3 行覆盖，本用例会 FAIL。

- **E3（bugfix.md VC#3 / 一次性覆盖语义）** — `test_update_repo_agent_override_is_one_shot_not_persisted`
  CLI `--agent X`（`update_repo(..., agent_override="codex")`）对已经持久化
  `active_agent=claude` 的仓库做一次性覆盖：本次刷新 `.codex/`，但不得修改 platforms.yaml
  中的 `active_agent` 字段（仍为 claude）。锁定 "一次性覆盖不持久化" 语义，防退化成
  "执行即 install"。

所有用例都只走 helper 层，tempdir 隔离，不触达 PetMall 主仓。
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml  # noqa: E402

from harness_workflow.backup import read_platforms_config  # noqa: E402
from harness_workflow.workflow_helpers import (  # noqa: E402
    FEEDBACK_LOG,
    LEGACY_FEEDBACK_LOG,
    init_repo,
    install_agent,
    update_repo,
)


class _BaseTempRepo(unittest.TestCase):
    """共享 tempdir + branch mock。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-bugfix3-edge-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()
        self._branch_patcher = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patcher.start()

    def tearDown(self) -> None:
        self._branch_patcher.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)


class CompatModeWarningTest(_BaseTempRepo):
    """E1：active_agent 缺失时必须打 warning + 走 enabled[] 回退。"""

    def test_update_repo_compat_mode_warning_when_active_agent_missing(self) -> None:
        """init_repo 后人工删掉 active_agent（模拟旧仓），update_repo 必须：
        - stdout 打印 "active agent not set; refreshing enabled set (compat mode)"
        - 实际走全 agent 刷新路径（.codex / .claude / .qoder 都要被写入 commands）
        """
        self.assertEqual(init_repo(self.repo, write_agents=True, write_claude=True), 0)
        # init_repo 不写 active_agent，但我们显式确保字段不存在（防未来默认值）
        platforms_path = self.repo / ".workflow" / "state" / "platforms.yaml"
        data = yaml.safe_load(platforms_path.read_text(encoding="utf-8")) or {}
        data.pop("active_agent", None)
        # 保留 enabled=[codex,qoder,cc,kimi]（init_repo 的默认值）
        platforms_path.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        self.assertIsNone(data.get("active_agent"))  # 前置条件

        # 清掉 init 期间可能创建的 agent 目录，便于断言 compat mode 把它们重建
        for d in [".claude", ".codex", ".qoder", ".kimi"]:
            target = self.repo / d
            if target.exists():
                shutil.rmtree(target)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = update_repo(self.repo, check=False)
        self.assertEqual(rc, 0)
        stdout = buf.getvalue()

        # 断言 1：stdout 必须含 compat warning
        self.assertIn(
            "active agent not set; refreshing enabled set (compat mode)",
            stdout,
            msg=(
                "E1 根因：active_agent 缺失时 update_repo 必须打 compat mode warning，"
                "否则用户无法察觉自己处在兼容模式、未收敛到单 agent。"
            ),
        )

        # 断言 2：实际刷新走 enabled[] 旧路径（.codex / .claude / .qoder 都有 commands）
        self.assertTrue(
            (self.repo / ".codex" / "skills" / "harness-install" / "SKILL.md").exists(),
            msg="E1：compat mode 下 .codex skills 应被刷新（走 enabled[] 旧行为）",
        )
        self.assertTrue(
            (self.repo / ".claude" / "commands" / "harness-install.md").exists(),
            msg="E1：compat mode 下 .claude commands 应被刷新",
        )
        self.assertTrue(
            (self.repo / ".qoder" / "commands" / "harness-install.md").exists(),
            msg="E1：compat mode 下 .qoder commands 应被刷新",
        )


class FeedbackMigrationNoOverwriteTest(_BaseTempRepo):
    """E2：legacy + new 同时存在时，update_repo 必须拒绝迁移（防数据丢失）。"""

    def test_feedback_migration_does_not_overwrite_existing_new_path(self) -> None:
        """场景：旧仓残留 .harness/feedback.jsonl（3 行），同时新位置
        .workflow/state/feedback/feedback.jsonl 已经有 2 行数据（例如前一次 update
        迁移过、随后又有新事件写入）。此时 update_repo 再跑一次：
        - 新位置内容保持 2 行不变（不被 3 行覆盖）
        - 旧位置保留（留给人工合并/清理，而非静默删）
        - 不应报错
        """
        self.assertEqual(init_repo(self.repo, write_agents=True, write_claude=True), 0)

        # 准备 legacy 3 行
        legacy_log = self.repo / LEGACY_FEEDBACK_LOG
        legacy_log.parent.mkdir(parents=True, exist_ok=True)
        legacy_lines = [
            json.dumps({"ts": "2026-04-01T00:00:00+00:00", "event": "legacy_a"}),
            json.dumps({"ts": "2026-04-02T00:00:00+00:00", "event": "legacy_b"}),
            json.dumps({"ts": "2026-04-03T00:00:00+00:00", "event": "legacy_c"}),
        ]
        legacy_log.write_text("\n".join(legacy_lines) + "\n", encoding="utf-8")

        # 准备 new 2 行（注意：init_repo 本身会触发 record_feedback_event，所以这里用覆盖写
        # 的方式重置 new 位置为确定的 2 行）
        new_log = self.repo / FEEDBACK_LOG
        new_log.parent.mkdir(parents=True, exist_ok=True)
        new_lines = [
            json.dumps({"ts": "2026-04-10T00:00:00+00:00", "event": "new_x"}),
            json.dumps({"ts": "2026-04-11T00:00:00+00:00", "event": "new_y"}),
        ]
        new_log.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        new_content_before = new_log.read_text(encoding="utf-8")

        # 跑 update_repo（不带 force）
        self.assertEqual(update_repo(self.repo, check=False), 0)

        # 断言 1：新位置内容保持 2 行事件（可能被 update_repo 期间的新事件追加，但前 2 行必须
        # 完整保留在开头、legacy 的 3 行必须**不存在**于新位置）
        new_content_after = new_log.read_text(encoding="utf-8")
        self.assertTrue(
            new_content_after.startswith(new_content_before),
            msg=(
                "E2 根因：legacy + new 同时存在时，update_repo 不得用 legacy 覆盖新位置；"
                "新位置前 2 行必须保持原样（可能之后有追加事件，但头部内容不变）。"
            ),
        )
        self.assertNotIn(
            "legacy_a",
            new_content_after,
            msg=(
                "E2 根因：legacy 事件 'legacy_a' 绝不能出现在新位置文件中，"
                "否则说明迁移逻辑在 new 已存在时仍强行覆盖/合并，破坏数据一致性。"
            ),
        )
        self.assertNotIn("legacy_b", new_content_after)
        self.assertNotIn("legacy_c", new_content_after)

        # 断言 2：legacy 位置保留（不静默删除），由用户人工处理
        self.assertTrue(
            legacy_log.exists(),
            msg=(
                "E2 根因：当 new 已存在时，update_repo 不应静默删除 legacy .harness/feedback.jsonl，"
                "而应保留以供用户人工合并。"
            ),
        )
        # legacy 内容未被改动
        self.assertEqual(
            legacy_log.read_text(encoding="utf-8"),
            "\n".join(legacy_lines) + "\n",
            msg="E2：legacy 位置内容在 update 期间不得被改动",
        )


class AgentOverrideOneShotTest(_BaseTempRepo):
    """E3：--agent X（agent_override）一次性覆盖但不改 active_agent 字段。

    注意：本用例不清理 `.codex/` 等目录，因为 `.codex/harness/managed-files.json`
    是 harness 自身的受管状态位置（见 `workflow_helpers.py:HARNESS_DIR`），
    清掉 `.codex` 会同时抹掉 managed-files.json，触发 `adopt` 分支覆盖 platforms.yaml，
    那是另一个独立的边界风险（见 session-memory 衍生问题 DI-01），非本用例所测。
    """

    def test_update_repo_agent_override_is_one_shot_not_persisted(self) -> None:
        """场景：install_agent 持久化 active_agent=claude；随后 CLI 传
        `--agent codex`（helper 层 `agent_override="codex"`）跑一次 update。
        - 本次应刷新 .codex/skills/harness（不是 .claude）
        - platforms.yaml.active_agent 必须仍为 "claude"（不被 override 污染持久化状态）
        - 下次无参数 update 应继续按 active_agent=claude 只走 .claude 路径
        """
        # 初始化 + install claude → 持久化 active_agent=claude
        self.assertEqual(install_agent(self.repo, "claude"), 0)
        initial = read_platforms_config(str(self.repo))
        self.assertEqual(initial.get("active_agent"), "claude")  # 前置条件

        # 关键：不清理 .codex（它含 managed-files.json，属于 harness 内部状态而非 codex agent）
        # 一次性覆盖到 codex
        self.assertEqual(
            update_repo(self.repo, check=False, agent_override="codex"),
            0,
        )

        # 断言 1：本次 update 写了 .codex skills
        self.assertTrue(
            (self.repo / ".codex" / "skills" / "harness-install" / "SKILL.md").exists(),
            msg=(
                "E3 根因：agent_override='codex' 本次 update 必须刷新 .codex/skills/harness-install/SKILL.md；"
                "若不存在则说明 agent_override 未生效。"
            ),
        )

        # 断言 2：平台配置的 active_agent 仍为 claude（不被 override 持久化）
        after = read_platforms_config(str(self.repo))
        self.assertEqual(
            after.get("active_agent"),
            "claude",
            msg=(
                "E3 根因：agent_override 是一次性覆盖，不应写入 platforms.yaml.active_agent；"
                f"实际读到 active_agent={after.get('active_agent')!r}，说明 override 被错误持久化。"
            ),
        )

        # 断言 3：再跑一次无参数 update，应按持久化的 active_agent=claude 刷新 .claude
        self.assertEqual(update_repo(self.repo, check=False), 0)
        self.assertTrue(
            (self.repo / ".claude" / "commands" / "harness-install.md").exists(),
            msg="E3：无参数 update 应按持久化的 active_agent=claude 刷新 .claude",
        )


if __name__ == "__main__":
    unittest.main()
