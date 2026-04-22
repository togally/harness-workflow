---
id: bugfix-3
title: pipx 重装后新项目 install/update 生成数据不正确
created_at: 2026-04-20
---

# Problem Description

pipx 重装后，在历史目标项目（如 `/Users/jiazhiwei/claudeProject/PetMallPlatform`）运行 `harness install` + `harness update`，用户反馈"生成的数据不对"。实测现象：

1. scaffold_v2 新增/改动但目标项目 `managed-files.json` 漏登记 hash 的模板文件（典型：`.workflow/context/roles/{acceptance,done,executing,planning,regression,requirement-review,stage-role,testing}.md`、`.workflow/context/experience/roles/{acceptance,executing,planning,testing}.md`、`.workflow/context/experience/risk/known-risks.md`）每次 update 都被输出 `skipped modified ...`，永远追不上最新模板。
2. `.workflow/context/experience/index.md` 每次 update 被搬到 `.workflow/context/backup/legacy-cleanup/.workflow/context/experience/` 再重建，`_unique_backup_destination` 追加 `-2/-3/...` 递增垃圾副本。
3. 目标项目 `runtime.yaml` / `state/` / `flow/` 未被主仓库数据污染（已诊断证伪，非本次修复范围）。

影响范围：所有"在 harness 某次发布前就已 install 过、scaffold 后续又演进"的历史项目，`harness update` 无法把模板新增章节（如 req-26 "对人文档输出"）带到目标项目，除非用户手工 `--force-managed`；同时 `legacy-cleanup/.workflow/context/experience/index.md*` 磁盘副本持续堆积。

# Root Cause Analysis

- **根因 A（主因）**：`_sync_requirement_workflow_managed_files`（`src/harness_workflow/workflow_helpers.py` L2541-L2593）对"目标文件存在但 `managed-files.json` 未登记 hash"的场景，走 L2587 `skipped modified {relative}` 分支吞掉内容同步；`_refresh_managed_state`（L2140-L2150）只在"当前文件已等于模板"时才写 hash——既然文件不等于模板，hash 永远写不进去，下一次 update 仍然 `skipped modified`，陷入死锁。
- **根因 B（次因）**：`LEGACY_CLEANUP_TARGETS`（L71-L89）把 `Path(".workflow") / "context" / "experience" / "index.md"` 当 legacy 归档，而 `_refresh_experience_index`（L3585）每次 update 又会活跃再生成该文件——形成"搬家 → 重建 → 下次再搬家"循环；`_unique_backup_destination` 产生 `-2/-3/...` 递增副本堆积磁盘。
- 诊断详见 `artifacts/main/bugfixes/bugfix-3-pipx-重装后新项目-install-update-生成数据不正确/regression/diagnosis.md`。

# Fix Scope

**将改**：
- `src/harness_workflow/workflow_helpers.py`：
  - `_sync_requirement_workflow_managed_files`（L2541-L2593）新增"adopt-as-managed"分支；
  - `LEGACY_CLEANUP_TARGETS`（L71-L89）移除 `.workflow/context/experience/index.md` 一条；
- 本 bugfix artifacts 目录文档（`bugfix.md` / `session-memory.md` / `changes/实施说明.md`）；
- `.workflow/state/action-log.md` 顶部追加 executing 阶段条目；
- `.workflow/tools/index/missing-log.yaml` 已追加 executing 工具查询未命中记录（硬门禁一）。

**不改**：
- `tests/test_workflow_helpers_update_idempotent.py`（红用例是真相来源，不得改动）；
- `src/harness_workflow/assets/scaffold_v2/`（scaffold 模板本身无缺陷）；
- 目标项目 `/Users/jiazhiwei/claudeProject/PetMallPlatform` 的任何文件（不清理历史 legacy-cleanup 副本，不在本 bugfix 代码修复范围，留作遗留观察）；
- `_refresh_managed_state`（L2140-L2150）本身的语义不动——只通过在 `_sync_requirement_workflow_managed_files` 层新增 adopt 分支把 hash 提前写到 `refreshed_state`，`_refresh_managed_state` 的"文件等于模板才写 hash"收尾逻辑保持原样（保护用户自定义文件的原语义）；
- `_refresh_experience_index` / `cleanup_legacy_workflow_artifacts` / `_unique_backup_destination` 的逻辑不动，只改清单常量。

# Fix Plan

1. **步骤 1（根因 B，最小改动优先）**：编辑 `src/harness_workflow/workflow_helpers.py` L71-L89，从 `LEGACY_CLEANUP_TARGETS` 列表中删除 `Path(".workflow") / "context" / "experience" / "index.md"` 一行。
   - 预期新行为：`cleanup_legacy_workflow_artifacts` 不再扫到该文件 → `shutil.move` 不触发 → `_unique_backup_destination` 不再生成 `index.md-N`。
   - 不破坏既有语义：同列表其他 legacy 条目（如 `context/experience/business`/`architecture`/`debug` 等）保留；不影响 `_refresh_experience_index` 的重生成。

2. **步骤 2（根因 A，核心修复）**：编辑 `src/harness_workflow/workflow_helpers.py` L2572-L2587，在"文件不等于模板"的分支组里新增 adopt-as-managed 判据。
   - 判据（关键安全带）：`relative not in managed_state`（即 `managed-files.json` 从未登记该 scaffold 文件的 hash）视为"漏登记" → 直接用 scaffold_v2 模板覆盖 + 写 hash 到 `refreshed_state[relative]`，action 记 `adopted {relative}`（check 模式下记 `would adopt {relative}`）。
   - 保护用户自定义：`relative in managed_state` 但 `managed_state[relative] != current_hash`（hash 已登记但与当前文件不匹配）→ 视为"用户真改过"，继续走 L2587 `skipped modified {relative}`，不覆盖。`force_managed=True` 路径保持原 L2578-L2585 行为不变。
   - 分支顺序（原 + 新）：
     - L2574 `current == content` → 记 `current`，写 hash（原逻辑）；
     - L2578 `managed_state.get(relative) == current_hash or force_managed` → 记 `updated` / `overwrote modified`（原逻辑）；
     - **新增**：`relative not in managed_state`（未登记）→ 记 `adopted`，覆盖 + 写 hash；
     - 兜底 L2587 `skipped modified`（仅对"已登记但 hash 不匹配"的用户修改文件）。
   - 为什么这条判据能区分"用户改过"vs"漏登记"：只要 scaffold 曾在某次 install/update 中把该文件落盘，`_refresh_managed_state` 或 `_sync_...`（本修复生效后）就会写 hash；后续用户若手改，hash 条目仍在但值不匹配。因此"完全没有 hash 条目"就是漏登记的充要信号。

3. **步骤 3（内部 dry-run 自检）**：修完后先运行红用例 `PYTHONPATH=src python3 -m pytest tests/test_workflow_helpers_update_idempotent.py -v`，确认 2 passed。
   - 若用例 1 仍红 → 检查 adopt 分支是否真的落到 `refreshed_state` 并被 `_save_managed_state` 写回；
   - 若用例 2 仍红 → 检查 `LEGACY_CLEANUP_TARGETS` 列表是否真的移除。

4. **步骤 4（全量 pytest 零回归）**：`PYTHONPATH=src python3 -m pytest -x --no-header -q`，对比基线（testing 阶段记录：180 tests / 1 pre-existing failure）。
   - 若出现新增 failure：必须修到 0 新增（通常是 "adopted" action 字样被老用例 assertEqual 硬匹配，需在本修复范围内调整判据；若影响面确实超出本 bugfix，停下上报主 agent，不扩大变更）。

5. **步骤 5（手动烟测，不改目标项目）**：
   - `cp -R /Users/jiazhiwei/claudeProject/PetMallPlatform /tmp/petmall-bugfix3-smoke`（只读副本）；
   - `cd /tmp/petmall-bugfix3-smoke && harness update`（editable pipx 跑本仓修复后的代码）；
   - 核对 stdout 无 `skipped modified .../context/roles/*.md`、无 `archived legacy .../experience/index.md`；
   - 核对 `legacy-cleanup/.workflow/context/experience/` 下不再新增 `index.md-N`；
   - 核对 `context/roles/executing.md` 已刷新到最新模板（含 req-26 "对人文档输出"章节）；
   - 用完删 `/tmp/petmall-bugfix3-smoke`。
   - 若烟测发现新 bug：立即停下写入 session-memory，**不在本轮扩大修复范围**。

# Validation Criteria

- [ ] `PYTHONPATH=src python3 -m pytest tests/test_workflow_helpers_update_idempotent.py -v` → 2 passed（两条红用例转绿）。
- [ ] `PYTHONPATH=src python3 -m pytest -x --no-header -q` → 零新增回归（允许容忍 testing 阶段已记录的 1 条 pre-existing failure；新增 failure 必须修到 0）。
- [ ] 手动烟测：`/tmp/petmall-bugfix3-smoke` 临时副本上跑一次 `update_repo`，stdout 不再出现 `skipped modified .workflow/context/roles/*.md` 或 `archived legacy .workflow/context/experience/index.md ...`；`legacy-cleanup/.workflow/context/experience/` 下不再新增 `index.md-N`。
- [ ] 对人文档 `changes/实施说明.md` 已产出（开发者角色契约）。
- [ ] session-memory.md 追加 executing 阶段条目（context_chain 延长到 L1 executing + 步骤逐条 ✅ + 经验候选 ≥ 1 条）。
- [ ] `.workflow/state/action-log.md` 顶部追加 executing 阶段条目。
