# chg-01 session-memory

## 执行步骤

| Step | 描述 | 状态 |
|------|------|------|
| Step 1 | F3: workflow_helpers.py create_requirement 签名增参 fallback + office_hours_mode 计算逻辑 + save_simple_yaml dict + ordered_keys | ✅ |
| Step 2 | F2: harness_requirement.py argparse 加 --fallback + 透传 fallback=args.fallback | ✅ |
| Step 3 | F1: cli.py req_parser 加 --fallback + dispatch 块透传 cmd_args.append("--fallback") | ✅ |
| Step 4 | F4: tests/installer/test_requirement_fallback_flag.py 10 用例（P0×7 含 Dogfood + P1×3） | ✅ |
| Step 5.1 | pipx install --force 后端到端真活（--fallback → office_hours_mode: "fallback"；无 flag + compat=true → required） | ✅ |
| Step 5.2 | pytest tests/installer/test_requirement_fallback_flag.py -v → 10 passed | ✅ |
| Step 5.3 | harness validate --contract artifact-placement → exit 0 | ✅ |
| Step 5.4 | harness validate --human-docs → exit 0（主 agent 独立核查更正；子 agent 误判为 exit 1） | ✅ |

## 关键决策点

1. **save_simple_yaml 字符串带引号**：`_render_yaml_scalar` 对字符串加双引号，状态文件中写成 `office_hours_mode: "fallback"`。测试断言改为 `load_simple_yaml` 读回后对比值（`== "fallback"`），不用 `in state_text` 形式。这样更健壮，绕过引号格式依赖。

2. **subprocess 测试 PYTHONPATH**：`sys.executable` 指向 python3.14 但模块未安装到全局，通过设置 `PYTHONPATH=REPO_ROOT/src` 环境变量解决（与 test_req52_e2e_log.py 同模式）。

3. **bugfix-11 B2 前车之鉴遵守**：`office_hours_mode` 同时出现在 dict 和 ordered_keys 两处，`grep -c '"office_hours_mode"'` = 2，满足 AC-04。

## 预存回归说明

运行 `pytest tests/ -x --ignore=tests/integration ...` 时出现多条失败，均为预存问题（test_create_trivial.py、test_suggest_apply_trivial.py 等 ImportError；test_harness_next_pending_gate 等 stage 兼容问题）。这些与 chg-01 改动无关，已通过 git stash 验证。

## 待处理捕获问题

- 无（主 agent 独立核查：human-docs 实测 exit 0；子 agent 误报已更正）
