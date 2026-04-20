"""bugfix-3 回归用例：`harness update` 对存量 scaffold + legacy 归档循环的幂等性。

两条用例分别锁住 `artifacts/main/bugfixes/bugfix-3-.../regression/diagnosis.md` 指出的两个根因：

- **用例 1（根因 A）** — `_sync_requirement_workflow_managed_files` + `_refresh_managed_state`
  对"存量文件、未登记 hash"的处理不幂等：`skipped modified` 分支吞掉内容同步，
  `_refresh_managed_state` 又只在"当前文件已等于模板"时才写入 hash，导致老项目永远拿不到
  scaffold_v2 的新增章节。
- **用例 2（根因 B）** — `LEGACY_CLEANUP_TARGETS` 把活跃再生成的
  `.workflow/context/experience/index.md` 当 legacy 归档，每次 update 都循环搬家，
  `_unique_backup_destination` 会持续追加 ``-2/-3/...`` 堆积垃圾。

两条用例都只走 helper 层（`init_repo` / `update_repo`），不跑真 CLI，tempdir 隔离。
红阶段：两条用例都必须 FAIL 在上述根因上；绿阶段由后续 executing 负责。
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

from harness_workflow.workflow_helpers import (  # noqa: E402
    LEGACY_CLEANUP_ROOT,
    MANAGED_STATE_PATH,
    _load_managed_state,
    _managed_file_contents,
    init_repo,
    update_repo,
)


class UpdateIdempotencyTest(unittest.TestCase):
    """bugfix-3 红阶段：update 对"存量未登记 scaffold"与"活跃 index.md"的幂等性。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-bugfix3-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()
        # 固定 branch 为 main，避免依赖宿主 git 环境（_required_dirs 会走到
        # `artifacts/{branch}/requirements`，若 git 解析失败兜底 "main"，显式固定更稳）。
        self._branch_patcher = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patcher.start()

    def tearDown(self) -> None:
        self._branch_patcher.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 根因 A：存量 scaffold 文件未登记 hash 时，update 无法把内容带到最新模板
    # ------------------------------------------------------------------
    def test_unregistered_stale_scaffold_file_is_adopted_by_update(self) -> None:
        """用例 1（根因 A）：scaffold 存量文件未登记 hash → update 后必须到最新模板并补录 hash。

        场景还原：
        1. `init_repo` 正常建仓，目标项目得到 scaffold_v2 最新模板 + managed-files.json 全量 hash。
        2. 人为把 `.workflow/context/roles/executing.md` 改成"旧版本"（删掉一段），
           并把 `managed-files.json` 中该文件的 hash 条目删掉 —— 完整复现"历史 pipx 装过的
           旧版目标项目在 scaffold 演进后留下的状态"。
        3. 跑一次 `update_repo(check=False)`，期望：
           - 文件内容被刷新到最新 scaffold 模板；
           - `managed-files.json` 重新登记了该文件 hash；
           - 再跑一次 update 不再输出 "skipped modified"（完全幂等）。

        诊断原文：`skipped modified {relative}` 分支吞掉内容同步，`_refresh_managed_state`
        只在"当前文件已等于模板"时才写 hash → 第二次 update 仍然 skipped modified。
        """
        # Step 1：正常建仓，拿到基线 scaffold 全量内容
        self.assertEqual(init_repo(self.repo, write_agents=True, write_claude=True), 0)

        target_rel = Path(".workflow") / "context" / "roles" / "executing.md"
        target_path = self.repo / target_rel
        self.assertTrue(target_path.exists(), "init_repo 应已落盘 executing.md")

        # 取 scaffold 最新内容（用例自己持有，用于后续断言）
        managed_contents = _managed_file_contents(
            self.repo,
            language="english",
            include_agents=True,
            include_claude=True,
        )
        latest_template = managed_contents[target_rel.as_posix()]

        # Step 2：模拟"存量旧 scaffold"——把内容改短，并清掉 managed-files.json 里的 hash 条目
        stale_content = latest_template.split("\n\n", 1)[0] + "\n\n(stale old scaffold body)\n"
        self.assertNotEqual(stale_content, latest_template, "stale 内容必须与模板不同")
        target_path.write_text(stale_content, encoding="utf-8")

        managed_state_path = self.repo / MANAGED_STATE_PATH
        state = json.loads(managed_state_path.read_text(encoding="utf-8"))
        removed = state["managed_files"].pop(target_rel.as_posix(), None)
        self.assertIsNotNone(
            removed,
            "初始 managed-files.json 应包含 executing.md；若未包含则测试前提失效",
        )
        managed_state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # Step 3：运行 update
        self.assertEqual(update_repo(self.repo, check=False), 0)

        # 断言 3a：文件必须到达最新 scaffold 模板（根因 A 会导致 stale 内容被保留）
        post_content = target_path.read_text(encoding="utf-8")
        self.assertEqual(
            post_content,
            latest_template,
            msg=(
                "根因 A：update_repo 应把存量未登记的 scaffold 文件刷新到最新模板，"
                "但当前文件仍停留在旧内容（`skipped modified` 分支吞掉了内容同步）。"
                f"文件路径：{target_rel.as_posix()}"
            ),
        )

        # 断言 3b：managed-files.json 必须重新登记该文件 hash
        state_after = _load_managed_state(self.repo)
        self.assertIn(
            target_rel.as_posix(),
            state_after,
            msg=(
                "根因 A：update 后 managed-files.json 必须登记该文件 hash，"
                "否则下一次 update 仍会判为 skipped modified，永远追不上模板。"
            ),
        )

        # 断言 3c：第二次 update 必须完全幂等（不得再出现 skipped modified <该文件>）
        # 通过第二次运行后 managed-files.json 哈希稳定 + 文件内容仍等于模板来侧证。
        self.assertEqual(update_repo(self.repo, check=False), 0)
        self.assertEqual(
            target_path.read_text(encoding="utf-8"),
            latest_template,
            "第二次 update 不得回退文件内容",
        )
        state_final = _load_managed_state(self.repo)
        self.assertEqual(
            state_final.get(target_rel.as_posix()),
            state_after.get(target_rel.as_posix()),
            "第二次 update 后 hash 应保持不变（完全幂等）",
        )

    # ------------------------------------------------------------------
    # 根因 B：experience/index.md 是活跃生成的，不得每次 update 都被当 legacy 归档
    # ------------------------------------------------------------------
    def test_experience_index_md_not_cycled_into_legacy_cleanup(self) -> None:
        """用例 2（根因 B）：连续两次 update，experience/index.md 不得堆积 legacy 副本。

        场景还原：
        1. `init_repo` + 一次 `update_repo` → 产生活跃的
           `.workflow/context/experience/index.md`（由 `_refresh_experience_index` 生成）。
        2. 再跑一次 `update_repo`。
        3. 期望：`.workflow/context/backup/legacy-cleanup/.workflow/context/experience/`
           下**不得**出现 `index.md-2`/`index.md-N` 递增堆积。

        诊断原文：`cleanup_legacy_workflow_artifacts` 把 `experience/index.md` 列入
        `LEGACY_CLEANUP_TARGETS`，每次 update 都会"搬家 → 重建 → 下次再搬家"；
        `_unique_backup_destination` 产生 -2/-3/... 递增副本。
        """
        self.assertEqual(init_repo(self.repo, write_agents=True, write_claude=True), 0)

        # 第一次 update：让 _refresh_experience_index 把 index.md 生成出来
        self.assertEqual(update_repo(self.repo, check=False), 0)
        exp_index = self.repo / ".workflow" / "context" / "experience" / "index.md"
        # 第一次 update 后 legacy-cleanup 下可能尚未产生副本，也可能有 1 份历史备份（可容忍）
        legacy_exp_dir = self.repo / LEGACY_CLEANUP_ROOT / ".workflow" / "context" / "experience"

        # 第二次 update：关键断言窗口
        self.assertEqual(update_repo(self.repo, check=False), 0)

        self.assertTrue(
            exp_index.exists(),
            "update 后 experience/index.md 必须仍然存在（由 _refresh_experience_index 生成）",
        )

        # 断言：legacy-cleanup 下不得出现 index.md-2 / index.md-3 / ... 递增堆积
        offending = []
        if legacy_exp_dir.exists():
            for child in legacy_exp_dir.iterdir():
                name = child.name
                # 容忍 index.md（首次备份），但 index.md-2 及后续均视为循环归档的铁证
                if name.startswith("index.md-"):
                    offending.append(child.relative_to(self.repo).as_posix())

        self.assertEqual(
            offending,
            [],
            msg=(
                "根因 B：连续两次 update 不得在 legacy-cleanup 下堆积 experience/index.md-N 副本。"
                f"实际发现：{offending}。"
                "根因：LEGACY_CLEANUP_TARGETS 把活跃再生成的 experience/index.md 列为 legacy，"
                "每次 update 触发 '搬家 → 重建 → 下次再搬家' 循环，"
                "`_unique_backup_destination` 会持续追加 -2/-3/... 递增副本。"
            ),
        )


if __name__ == "__main__":
    unittest.main()
