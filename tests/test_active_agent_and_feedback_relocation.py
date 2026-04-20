"""bugfix-3（新）红用例：install/update 仅刷新当前 active agent + .harness/feedback.jsonl 落层归位。

三条用例分别锁住 `regression/diagnosis.md` §1 / §2 的两条根因：

- **用例 1（问题 1 / 状态层缺 `active_agent` 字段）** — `test_install_agent_persists_active_agent`
  `install_agent(root, agent)` 后 `.workflow/state/platforms.yaml` 必须写入 `active_agent: <agent>`，
  且二次调用可覆盖（`claude → codex`）。

- **用例 2（问题 1 / update_repo 不感知 active agent）** — `test_update_repo_only_refreshes_active_agent`
  当 `active_agent=claude` + `enabled=[codex,qoder,cc,kimi]` 时，`update_repo` 只刷新 `.claude/`
  目录（其它 agent 目录不变动）；`force_all_platforms=True` 时四个 agent 全刷新（escape hatch）。

- **用例 3（问题 2 / FEEDBACK_DIR 常量落位错误）** — `test_feedback_jsonl_writes_under_state_feedback`
  - 3a：新建仓调 `record_feedback_event` 后文件出现在 `.workflow/state/feedback/feedback.jsonl`，`.harness/` 不被创建；
  - 3b：`update_repo` 对旧仓做一次性迁移（旧位置消失 / 新位置内容连续）；
  - 3c：`harness_export_feedback` CLI 从新位置读取聚合正常。

所有用例都只走 helper 层（`install_agent` / `update_repo` / `record_feedback_event`），不跑真 CLI，tempdir 隔离。
红阶段：三条用例都必须 FAIL 在上述根因上；绿阶段由后续 executing 负责。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.backup import read_platforms_config, write_platforms_config  # noqa: E402
from harness_workflow.workflow_helpers import (  # noqa: E402
    FEEDBACK_LOG,
    init_repo,
    install_agent,
    record_feedback_event,
    update_repo,
)


class ActiveAgentPersistenceTest(unittest.TestCase):
    """用例 1（问题 1）：install_agent 必须把 active_agent 写到 platforms.yaml。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-bugfix3-new-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()
        # 固定 branch，避免依赖宿主 git 环境
        self._branch_patcher = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patcher.start()

    def tearDown(self) -> None:
        self._branch_patcher.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_install_agent_persists_active_agent(self) -> None:
        """install_agent(root, 'claude') 后 platforms.yaml 必须有 active_agent=claude；
        再调 install_agent(root, 'codex') 后 active_agent 被覆盖为 codex。

        诊断原文（§1.3）：状态层完全缺失 active_agent 字段，install_agent 不写入 platforms.yaml。
        """
        # 第一次 install：claude
        self.assertEqual(install_agent(self.repo, "claude"), 0)

        config = read_platforms_config(str(self.repo))
        self.assertEqual(
            config.get("active_agent"),
            "claude",
            msg=(
                "问题 1 根因：install_agent 必须把当前选定 agent 写入 platforms.yaml.active_agent，"
                f"但当前字段缺失或不等于 claude，实际读到：{config.get('active_agent')!r}"
            ),
        )

        # 第二次 install：codex，必须覆盖
        self.assertEqual(install_agent(self.repo, "codex"), 0)

        config2 = read_platforms_config(str(self.repo))
        self.assertEqual(
            config2.get("active_agent"),
            "codex",
            msg=(
                "问题 1 根因：二次 install_agent 必须覆盖 active_agent 到新 agent，"
                f"实际读到：{config2.get('active_agent')!r}"
            ),
        )


class UpdateOnlyRefreshesActiveAgentTest(unittest.TestCase):
    """用例 2（问题 1）：update_repo 读 active_agent 后只刷新对应 agent 的 commands/skills 文件。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-bugfix3-new-"))
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

    def _set_active_agent(self, agent: str) -> None:
        """Direct yaml write — 模拟 install_agent 之后的持久化状态。"""
        import yaml

        config_path = self.repo / ".workflow" / "state" / "platforms.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if config_path.exists():
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        data["enabled"] = ["codex", "qoder", "cc", "kimi"]
        data["disabled"] = []
        data["active_agent"] = agent
        config_path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    def _snapshot_managed_files(self) -> dict[str, bool]:
        """采样四个 agent 的 harness-install.md command 文件是否存在。"""
        return {
            ".claude": (self.repo / ".claude" / "commands" / "harness-install.md").exists(),
            ".codex": (self.repo / ".codex" / "skills" / "harness-install" / "SKILL.md").exists(),
            ".qoder": (self.repo / ".qoder" / "commands" / "harness-install.md").exists(),
            ".kimi": (self.repo / ".kimi" / "skills" / "harness-install" / "SKILL.md").exists(),
        }

    def test_update_repo_only_refreshes_active_agent(self) -> None:
        """active_agent=claude + enabled=全四个 → update_repo 只写 .claude/*；
        其它 agent 的 commands/skills 不被创建。`force_all_platforms=True` 恢复旧行为。

        诊断原文（§1.2 D / F）：update_repo 无 --agent 参数；_managed_file_contents
        不论 platforms 配置，16 个 COMMAND_DEFINITIONS × 4 agent 全量写入。
        """
        # Step 1：初始建仓 + 设定 active_agent=claude
        self.assertEqual(init_repo(self.repo, write_agents=True, write_claude=True), 0)
        # init_repo 会写全四个 agent 的 commands — 这是兼容旧行为。
        # 清掉非 claude 的 agent 目录，模拟"全新 install --agent claude"的结果
        for d in [".codex", ".qoder", ".kimi"]:
            target = self.repo / d
            if target.exists():
                shutil.rmtree(target)
        self._set_active_agent("claude")

        # Step 2：update_repo 默认模式（应只刷新 .claude）
        self.assertEqual(update_repo(self.repo, check=False), 0)

        snapshot = self._snapshot_managed_files()
        self.assertTrue(
            snapshot[".claude"],
            msg="active_agent=claude 时，update_repo 必须刷新 .claude/commands/harness-install.md",
        )
        self.assertFalse(
            snapshot[".codex"],
            msg=(
                "问题 1 根因：active_agent=claude 时，update_repo 不得再写 .codex/skills/harness-install/SKILL.md；"
                "当前 _managed_file_contents 无视 active_agent 全量写入。"
            ),
        )
        self.assertFalse(
            snapshot[".qoder"],
            msg="active_agent=claude 时，update_repo 不得再写 .qoder/commands/harness-install.md",
        )
        self.assertFalse(
            snapshot[".kimi"],
            msg="active_agent=claude 时，update_repo 不得再写 .kimi/skills/harness-install/SKILL.md",
        )

        # Step 3：force_all_platforms=True escape hatch 应恢复旧行为（四个 agent 全刷新）
        self.assertEqual(
            update_repo(self.repo, check=False, force_all_platforms=True),
            0,
        )
        snapshot_all = self._snapshot_managed_files()
        self.assertTrue(
            all(snapshot_all.values()),
            msg=(
                "force_all_platforms=True 必须恢复旧行为（四个 agent 全刷新 escape hatch），"
                f"实际：{snapshot_all}"
            ),
        )


class FeedbackRelocationTest(unittest.TestCase):
    """用例 3（问题 2）：feedback.jsonl 必须落在 .workflow/state/feedback/，旧仓自动迁移。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-bugfix3-new-"))
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

    def test_feedback_jsonl_writes_under_state_feedback(self) -> None:
        """覆盖 3a 新仓写新位置 / 3b 旧仓迁移 / 3c export 从新位置读。

        诊断原文（§2.6）：FEEDBACK_DIR = Path('.harness') 常量早于六层架构成型，
        必须改常量 + update_repo 一次性迁移 + harness_export_feedback 同步路径。
        """
        # ---- 3a：新建仓，调 record_feedback_event，文件在新位置且 .harness/ 不被创建 ----
        self.assertEqual(init_repo(self.repo, write_agents=True, write_claude=True), 0)
        record_feedback_event(self.repo, "test_event", {"sample": 1})

        new_log = self.repo / ".workflow" / "state" / "feedback" / "feedback.jsonl"
        old_log = self.repo / ".harness" / "feedback.jsonl"
        self.assertTrue(
            new_log.exists(),
            msg=(
                "问题 2 根因：record_feedback_event 必须写入 .workflow/state/feedback/feedback.jsonl，"
                "但当前仍走 FEEDBACK_DIR=Path('.harness')。"
            ),
        )
        self.assertFalse(
            old_log.exists(),
            msg=(
                "问题 2 根因：新仓不得再创建 .harness/feedback.jsonl，"
                "常量 FEEDBACK_DIR 必须指向 .workflow/state/feedback/。"
            ),
        )
        # 同时锁住模块常量（避免下次回归时只改一处）
        self.assertEqual(
            Path(str(FEEDBACK_LOG)),
            Path(".workflow") / "state" / "feedback" / "feedback.jsonl",
            msg="常量 FEEDBACK_LOG 必须已指向 .workflow/state/feedback/feedback.jsonl",
        )

        # ---- 3b：旧仓预置 .harness/feedback.jsonl + 跑 update_repo 应一次性迁移 ----
        legacy_repo = self.tempdir / "legacy"
        legacy_repo.mkdir()
        self.assertEqual(init_repo(legacy_repo, write_agents=True, write_claude=True), 0)
        # 预置老位置 + 合法 jsonl 一行
        legacy_old = legacy_repo / ".harness" / "feedback.jsonl"
        legacy_old.parent.mkdir(parents=True, exist_ok=True)
        legacy_old.write_text(
            json.dumps({"ts": "2026-04-01T00:00:00+00:00", "event": "legacy", "data": {"n": 1}}) + "\n",
            encoding="utf-8",
        )

        # 新仓的 update_repo 清理一下 init_repo 的"首次 update"残留前，先记录老文件内容
        legacy_content_before = legacy_old.read_text(encoding="utf-8")

        self.assertEqual(update_repo(legacy_repo, check=False), 0)

        legacy_new = legacy_repo / ".workflow" / "state" / "feedback" / "feedback.jsonl"
        self.assertTrue(
            legacy_new.exists(),
            msg=(
                "问题 2 根因：旧仓的 .harness/feedback.jsonl 必须在 update_repo 时一次性迁移到 "
                ".workflow/state/feedback/feedback.jsonl。"
            ),
        )
        self.assertFalse(
            legacy_old.exists(),
            msg=(
                "问题 2 根因：迁移后 .harness/feedback.jsonl 必须已被 shutil.move 掉（不再残留老位置）。"
            ),
        )
        # 数据连续性：老内容必须完整保留在新位置（可能有 update_repo 期间追加的新事件）
        legacy_content_after = legacy_new.read_text(encoding="utf-8")
        self.assertIn(
            legacy_content_before.strip(),
            legacy_content_after,
            msg="迁移后新位置必须包含迁移前老位置的全部内容（数据连续性）",
        )

        # ---- 3c：harness_export_feedback 从新位置读取聚合成功 ----
        export_cmd = [
            sys.executable,
            str(REPO_ROOT / "src" / "harness_workflow" / "tools" / "harness_export_feedback.py"),
            "--root",
            str(legacy_repo),
        ]
        env = {"PYTHONPATH": str(REPO_ROOT / "src")}
        import os

        merged_env = os.environ.copy()
        merged_env.update(env)
        result = subprocess.run(
            export_cmd,
            capture_output=True,
            text=True,
            env=merged_env,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"harness_export_feedback 必须从新位置读成功，stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        summary_path = legacy_repo / "harness-feedback.json"
        self.assertTrue(summary_path.exists(), msg="harness_export_feedback 应生成 harness-feedback.json")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(
            summary["events_total"],
            1,
            msg=(
                "问题 2 根因：harness_export_feedback 必须从 .workflow/state/feedback/feedback.jsonl 读到迁移过来的事件，"
                f"当前 events_total={summary['events_total']}，说明路径没改对。"
            ),
        )


if __name__ == "__main__":
    unittest.main()
