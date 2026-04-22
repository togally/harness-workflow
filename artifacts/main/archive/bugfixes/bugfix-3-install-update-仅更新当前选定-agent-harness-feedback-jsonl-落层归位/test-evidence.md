# Test Evidence — bugfix-3

## 用例覆盖对照 bugfix.md#Validation Criteria

| AC | 用例来源 | 用例名 | 覆盖证据 |
|---|---|---|---|
| #1 `install_agent` 持久化 active_agent | executing 原红 | `test_install_agent_persists_active_agent` | PASSED（1.49s 全集合） |
| #2 `update_repo` 默认只刷新 active_agent 目录 | executing 原红 | `test_update_repo_only_refreshes_active_agent` | PASSED + 烟测 `.codex/.qoder/.kimi` mtime 未变 |
| #3 `feedback.jsonl` 写到 `.workflow/state/feedback/` + 旧仓迁移 + 消费者读新位置 | executing 原红 | `test_feedback_jsonl_writes_under_state_feedback` | PASSED + 烟测旧 `.harness/` rmdir + 新文件 3748 bytes 数据连续 |
| #4 全量 pytest 零新增回归 | 全量 | — | 152 passed / 1 pre-existing |
| #5 烟测端到端 | 手动 | 6 步 | 逐条 ✓ 见测试结论.md |

## 边界用例补强（testing 阶段新增 3 条）

| 风险点 | 新增用例 | 覆盖的边界 |
|---|---|---|
| 老仓 compat mode | `test_update_repo_compat_mode_warning_when_active_agent_missing` | `active_agent` 缺失 → warning + 回退 `enabled[]`，不破坏老仓 |
| 迁移数据丢失 | `test_feedback_migration_does_not_overwrite_existing_new_path` | 新位置已有数据时拒绝 move，打 warning |
| 一次性 flag | `test_update_repo_agent_override_is_one_shot_not_persisted` | `--agent X` 覆盖当次 run，不写回 platforms.yaml |

## 覆盖充分性论证
- executing 3 条 + testing 3 条 = **6 条**用例锁死"双修复 + 兼容 + 迁移 + flag"四维度
- 烟测补足"端到端行为可观测"（mtime / 目录存在性 / CLI stdout）
- 全量 pytest 认证"不破坏既有测试集合"
- 结论：覆盖充分，可推进 acceptance

## Conclusion
- [x] Pass — ready for acceptance
- [ ] Fail — requires further work
