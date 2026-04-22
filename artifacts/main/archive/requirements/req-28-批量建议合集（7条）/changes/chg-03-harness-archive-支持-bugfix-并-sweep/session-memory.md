# Session Memory

## 1. Current Goal

- chg-03：让 `harness archive` 识别 bugfix，归档到 `artifacts/{branch}/archive/bugfixes/`；新增 `--force-done` 开关以 sweep 历史活跃 bugfix；主 agent 后续 sweep bugfix-3/4/5/6。

## 2. Current Status

- ✅ `list_done_requirements` 同时扫 requirements + bugfixes（带 `kind` 标签）。
- ✅ `archive_requirement` 按 id 前缀路由到 `archive/requirements/` 或 `archive/bugfixes/`；bugfix 分支独立走 state/bugfixes + 跳过 sessions/artifact。
- ✅ 新增 `resolve_bugfix_root(root)` helper。
- ✅ CLI（cli.py + tools/harness_archive.py）加 `--force-done`，`--force-done + id` 可跳过交互。
- ✅ `tests/test_archive_bugfix.py` 4 条全绿；`test_archive_path.py` / `test_smoke_req26.py` 已对齐新路径，全仓 97 tests 全过。
- ✅ 对人文档 `实施说明.md` 已产出。
- 🚫 未执行 sweep bugfix-3/4/5/6（briefing 硬约束：由主 agent 执行）。

## 3. Validated Approaches

- `--force-done` 而非 `--sweep-bugfixes` 子命令：实现面更小，CLI 形态与现有 archive 对齐。
- 归档 bugfix 时仅"精确 id 匹配"清空 `current_requirement`，避免 sweep 把主 req-28 一并切走。
- 单测用 monkey-patch `_get_git_branch` 固定为 `main`，tempdir 隔离，避免真实 git 状态干扰。
- 按 briefing"写一条测跑一条"节奏，4 条单测逐个写逐个跑，没有批量翻车。

## 4. Failed Paths

- Attempt：最初只加 bugfix 分支未改 requirements 分支，导致归档路径没有统一加 `requirements/` 前缀。
- Failure reason：briefing + change.md 明确新布局是 `archive/requirements/<dir>` + `archive/bugfixes/<dir>`。
- Fix：统一为 `archive_subdir` 机制，requirement / bugfix 都加一层 subdir；同步更新既有 `test_archive_path.py` + `test_smoke_req26.py` 对路径的断言（原本预期 `archive/req-xx` 直接落）。
- Reminder：改共享路径约定时必须同步全仓单测。

## 5. Candidate Lessons

```markdown
### 2026-04-19 归档根目录布局变更波及旧 smoke 测试
- Symptom: chg-03 改动 `archive_requirement` 加了 `requirements/` 子目录后，`test_smoke_req26.test_full_lifecycle_smoke` 与 `test_archive_path.*` 立即红。
- Cause: 旧测试断言 `archive_root / req_dir.name` 直接存在，未考虑 id 前缀分流后引入的子目录层。
- Fix: 一并更新断言为 `archive_root / "requirements" / req_dir.name`，保持 AC-05（无双层 branch）主张不变。
```

## 6. Next Steps

- 主 agent 在 chg-03 完成后，逐个执行 `harness archive --force-done bugfix-{3,4,5,6}`；跑完后 `harness status` 确认 `active_requirements` 仅剩 req-28。

## 7. Open Questions

- 归档 bugfix 的 artifact 摘要生成（若未来需要）是否另起一轮处理？当前刻意跳过。
