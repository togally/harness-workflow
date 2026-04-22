# Test Evidence — bugfix-3（testing 阶段 TDD 红阶段）

## Change

bugfix-3（pipx 重装后新项目 install/update 生成数据不正确）

## Test Date

2026-04-20

## Test Summary

以 TDD 红 - 绿流程补两条**集成/回归**用例，锁住 `regression/diagnosis.md` 指出的两个根因。本阶段只到"红"（两条用例必须在当前 `workflow_helpers.py` 上 FAIL）；绿阶段由 executing 负责。

- 测试文件：`tests/test_workflow_helpers_update_idempotent.py`
- 运行方式：`PYTHONPATH=src python3 -m pytest tests/test_workflow_helpers_update_idempotent.py -v`
- 不触发真 CLI，只调 helper 层 `init_repo` / `update_repo` + tempdir 隔离 + `_get_git_branch` monkeypatch 固定 `main`。

## Test Cases

### 用例 1（根因 A，主因）

- **测试类名 / 方法**：`UpdateIdempotencyTest::test_unregistered_stale_scaffold_file_is_adopted_by_update`
- **路径**：`tests/test_workflow_helpers_update_idempotent.py::UpdateIdempotencyTest::test_unregistered_stale_scaffold_file_is_adopted_by_update`
- **场景还原**：`init_repo` 建仓 → 把 `.workflow/context/roles/executing.md` 改成"stale 旧内容" + 从 `managed-files.json` 删掉该文件 hash 条目 → 跑 `update_repo`。
- **期望（绿阶段）**：
  1. 文件被刷新到最新 scaffold 模板；
  2. `managed-files.json` 重新登记该文件 hash；
  3. 第二次 `update_repo` 完全幂等（文件内容不变、hash 不变，不再有 `skipped modified`）。
- **红阶段实际结果**：FAIL
  - `update_repo` 输出中明确包含：`- skipped modified .workflow/context/roles/executing.md`（根因 A 路径命中）
  - 断言摘要：
    ```
    AssertionError: '# 角色：开发者\n\n(stale old scaffold body)\n' !=
    '# 角色：开发者\n\n## 角色定义\n你是开发者。你的任务是严格按照 `plan.md` 执行变更，完[2509 chars]新。\n'
    : 根因 A：update_repo 应把存量未登记的 scaffold 文件刷新到最新模板，
    但当前文件仍停留在旧内容（`skipped modified` 分支吞掉了内容同步）。
    文件路径：.workflow/context/roles/executing.md
    ```
  - 失败位置：`tests/test_workflow_helpers_update_idempotent.py:117`（`assertEqual(post_content, latest_template, ...)`）。

### 用例 2（根因 B，次因）

- **测试类名 / 方法**：`UpdateIdempotencyTest::test_experience_index_md_not_cycled_into_legacy_cleanup`
- **路径**：`tests/test_workflow_helpers_update_idempotent.py::UpdateIdempotencyTest::test_experience_index_md_not_cycled_into_legacy_cleanup`
- **场景还原**：`init_repo` → 跑一次 `update_repo`（让 `_refresh_experience_index` 生成 `experience/index.md`）→ 再跑一次 `update_repo`。
- **期望（绿阶段）**：`.workflow/context/backup/legacy-cleanup/.workflow/context/experience/` 下不得出现任何 `index.md-N`（N ≥ 2）副本。允许容忍 0 或 1 份历史备份，但连续两次 update **不得**递增。
- **红阶段实际结果**：FAIL
  - `update_repo` 输出中第二次 update 触发：`- archived legacy .workflow/context/experience/index.md -> .workflow/context/backup/legacy-cleanup/.workflow/context/experience/index.md-2`（根因 B 路径命中）
  - 断言摘要：
    ```
    AssertionError: Lists differ:
    ['.workflow/context/backup/legacy-cleanup/.workflow/context/experience/index.md-2'] != []
    : 根因 B：连续两次 update 不得在 legacy-cleanup 下堆积 experience/index.md-N 副本。
    实际发现：['.workflow/context/backup/legacy-cleanup/.workflow/context/experience/index.md-2']。
    根因：LEGACY_CLEANUP_TARGETS 把活跃再生成的 experience/index.md 列为 legacy，
    每次 update 触发 '搬家 → 重建 → 下次再搬家' 循环，
    `_unique_backup_destination` 会持续追加 -2/-3/... 递增副本。
    ```
  - 失败位置：`tests/test_workflow_helpers_update_idempotent.py:195`（`assertEqual(offending, [])`）。

## Why These Two Cases Suffice to Lock the Root Causes

### 用例 1 对根因 A 的覆盖充分性

- 诊断原文中根因 A 的触发条件是**两个同时满足**："目标文件存在（非首次 create）" + "`managed-files.json` 未登记其 hash"。用例 1 在 fixture 中精确构造这两个条件（init 后手工 pop hash + 写入 stale 内容），且 stale 内容故意与模板不等以进入 `current != content` 分支。
- 断言链路覆盖：
  - 第一层断言"文件必须 == 最新模板"——直接卡住 `skipped modified` 分支吞掉内容同步这条路径；
  - 第二层断言"`managed-files.json` 必须登记 hash"——卡住 `_refresh_managed_state` "只在当前文件已等于模板时写 hash" 这条次生 bug；
  - 第三层断言"第二次 update 完全幂等"——确保修复不是一次性动作，而是进入稳态。
- 因此只要 `_sync_requirement_workflow_managed_files` / `_refresh_managed_state` 任一仍停留在诊断中描述的非幂等行为，本用例都会红。

### 用例 2 对根因 B 的覆盖充分性

- 根因 B 的本质是"`LEGACY_CLEANUP_TARGETS` 与 `_refresh_experience_index` 生成器白名单存在交集"。用例 2 走一次完整的 update 产生 `experience/index.md`，再走一次 update 正好触发"搬家 - 重建 - 再搬家"的第二轮循环，这是该 bug 最早暴露递增副本（`-2`）的最小步数。
- 断言仅允许 0 或 1 份历史备份、禁止任何 `-N`（N ≥ 2）——既能容忍修复方向"一次性把历史副本留在 legacy-cleanup"的合理实现，也能严格禁止"每次 update 都产生新副本"的退化。
- 如果 executing 修复方向是"从 LEGACY_CLEANUP_TARGETS 移除 `experience/index.md`"，用例 2 的 legacy-cleanup 目录会始终为空，天然通过。

## Results

| Check | Result | Notes |
|-------|--------|-------|
| 用例 1 红阶段 FAIL（触发根因 A） | pass | `skipped modified .workflow/context/roles/executing.md` 命中；文件未被同步 |
| 用例 2 红阶段 FAIL（触发根因 B） | pass | 第二次 update 产生 `legacy-cleanup/.../experience/index.md-2` |
| 用例隔离性（tempdir + monkeypatch branch） | pass | 不依赖宿主 git 状态，无副作用回写主仓 |
| 未修改被测代码 / scaffold_v2 / 目标项目 | pass | 仅新增一个测试文件，并在 `.workflow/tools/index/missing-log.yaml` 追加一条 toolsManager 查询未命中记录 |
| 现有测试零回归 | 本阶段不跑全量，留待 executing 绿阶段验证 | 本次只运行两条新用例 |

## Issues Found and Fixed

本阶段不做修复。两条用例的 FAIL 都精准命中诊断中描述的根因路径，输出信息与诊断文的现象、证据、根因行号描述一一对齐，**无虚假红**（已人工核对 `update_repo` 实际 stdout 中确实出现 `skipped modified` 与 `archived legacy ... index.md-2` 字样）。

## Conclusion

- [x] 红阶段完成 —— 两条用例都在当前 `workflow_helpers.py` 上 FAIL，且失败路径与 `regression/diagnosis.md` 描述的根因 A、B 完全一致。
- [ ] 绿阶段 —— 由 executing 修复 `_sync_requirement_workflow_managed_files` / `_refresh_managed_state` 的"adopt-as-managed"分支 + 从 `LEGACY_CLEANUP_TARGETS` 删除 `.workflow/context/experience/index.md`；然后重跑本文件两条用例应 PASS。
