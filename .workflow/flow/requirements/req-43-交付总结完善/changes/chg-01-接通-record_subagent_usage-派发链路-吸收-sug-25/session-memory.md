# Session Memory — chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））

## executing stage ✅

### 实现摘要

- `record_subagent_usage` 加 `task_type: str = "req"` kw-only 参数（默认向后兼容）；entry 新增 `task_type: {task_type}` 字段。
- `feedback.jsonl` payload 同步加 `"task_type": task_type`。
- null-safety：`(usage or {}).get(key, 0)` 防止 usage 字段缺失导致 KeyError。
- `harness-manager.md` §3.6 Step 4 派发钩子从纯文字契约升级为可观测执行步骤：每次派发后必须在 session-memory.md 留痕 `record_subagent_usage called: {role} / {model} / task_type={task_type} / ts={iso}`。
- sug-25 frontmatter `status: pending → applied`，`applied_at: 2026-04-26`。
- scaffold_v2 mirror 同步：harness-manager.md + base-role.md（diff = 0）。

### 测试结果

- 新增测试文件：`tests/test_req43_chg01.py`（9 条）
- 全部通过：9/9 ✅
- 关键覆盖：task_type=req/bugfix/sug、noop 路径、schema 字段、feedback.jsonl、mirror 同步、sug-25 status

### 遇到的问题 / 解法

- 无阻塞问题。null-safety fix 属预防性改动（usage 字段缺失时旧代码 KeyError）。

### 候选教训

- `record_subagent_usage` null-safety：usage 字段可能为 None，`(usage or {}).get(key, 0)` 是防御性写法。
