# Session Memory — req-38（api-document-upload 工具闭环）/ chg-03（runtime pending 字段 + next/status gate）

## 1. Current Goal

chg-03（runtime pending 字段 + next/status gate）实现：新增 `stage_pending_user_action` 字段、pending gate、status 展示、pytest 覆盖。

## 2. Context Chain

- Level 0: main agent → executing
- Level 1: Subagent (Sonnet) → chg-03 实现

## 3. Completed Tasks

- [x] Step 1: `workflow_helpers.py` runtime 字段白名单扩展（ordered_keys 追加 `stage_pending_user_action`）
- [x] Step 1 附加: `save_simple_yaml` 支持 None → YAML null；`_parse_simple_yaml_scalar` 支持 null 字面量 → None
- [x] Step 1 附加: `load_simple_yaml` 扩展支持两层嵌套 dict（`details.provider`）
- [x] Step 2: `workflow_next` pending gate（`_render_key_details` + pending 检查，退出码 3）
- [x] Step 3: `workflow_status` pending 行输出
- [x] Step 4: `.workflow/tools/protocols/mcp-precheck.md` 阶段 2 / 阶段 3 细化（写入/清空字段指令、ISO 时间戳格式说明）
- [x] Step 5: pytest 用例新增（11 条，全绿）
- [x] Step 6: scaffold_v2 mirror 同步（diff 无输出）
- [x] Step 7: 自检（全量 pytest 338 passed / 39 skipped，零回归）

## 4. Results

### 文件改动清单

| 文件 | 说明 |
|------|------|
| `src/harness_workflow/workflow_helpers.py` | 白名单扩展 + pending gate（`_render_key_details` + `workflow_next` gate） + status 输出 + save_simple_yaml null + load_simple_yaml 两层嵌套 + _parse_simple_yaml_scalar null 支持 |
| `.workflow/tools/protocols/mcp-precheck.md` | 阶段 2/3 细化：写入/清空 `stage_pending_user_action` 的具体指令 + ISO 时间戳格式 |
| `src/harness_workflow/assets/scaffold_v2/.workflow/tools/protocols/mcp-precheck.md` | mirror 同步 |
| `tests/test_harness_next_pending_gate.py` | 新增 5 条 pending gate 测试（AC-5/AC-6）|
| `tests/test_harness_status_pending_line.py` | 新增 3 条 status pending 行测试 |
| `tests/test_mcp_precheck_recovery_clears_pending.py` | 新增 3 条 precheck recovery 测试 |

### AC-5 自证 stdout

```
# harness next（pending 非空）
stage 正在等待 mcp_register（provider=apifox），请完成用户动作后再次 harness next
EXIT_CODE=3

# harness status（pending 非空）
...
Pending User Action: mcp_register(provider=apifox)
EXIT_CODE=0
```

### AC-6 自证 stdout

```
# harness status（pending 清空为 null）
...
Pending User Action: None
EXIT_CODE=0
```

### 模型自检降级留痕

- expected_model: sonnet；实际运行模型：claude-sonnet-4-6（符合 expected，无降级）

### pytest 结果

```
新增用例（-k "pending or precheck"）: 11 passed
全量 pytest: 338 passed, 39 skipped, 0 failed
```

### default-pick 决策

无争议默认决策。架构决策一处：
- pending gate 实现在 `workflow_helpers.py`（`workflow_next`/`workflow_status`）而非 `cli.py`，与现有架构一致（`cli.py` 仅做路由和转发），不在 `cli.py` 引用 `stage_pending_user_action`。

## 5. Next Steps

（subagent 不推进 stage，不给后续动作）
