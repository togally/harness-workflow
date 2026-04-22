---
id: bugfix-3
title: install 在空仓自动 init
created_at: 2026-04-19
parent_requirement: req-25
related_p0: P0-01
---

# Problem Description

在一个刚 `git init` 的空仓（没有 `.workflow/`）中执行 `harness install` 或 `harness install --agent <agent>`，被拒绝并退出 1：

```
Harness workspace is missing. Run `harness install` or `harness init` first.
Missing: <root>/.workflow, <root>/.workflow/context
```

错误信息自相矛盾：提示运行 `harness install`，而用户执行的正是该命令。README（第 50 行）和 `src/harness_workflow/skills/harness/SKILL.md` 都把 `harness install` 描述为"Initialize repository and install harness skill"——install 应当是单一入口，在空仓也应能直接使用。

**影响**：新用户第一次 clone 空仓后按 README 指引运行 `harness install`，会被立即挡住，必须先发现/阅读 `harness init` 才能继续，严重破坏 onboarding 语义。

# Root Cause Analysis

调用链：
1. `cli.py:279-286` CLI `install` 子命令 → `_run_tool_script("harness_install.py", ...)`
2. `tools/harness_install.py:23` → `install_agent(root, args.agent)`
3. `workflow_helpers.py:4382`（修复前）→ 开头硬调用 `ensure_harness_root(root)`
4. `workflow_helpers.py:2144-2148` `ensure_harness_root()` 发现 `.workflow/` 缺失 → `raise SystemExit(...)`

`install_agent()` 把 "requires .workflow to exist" 这个本应只保护下游命令（requirement/change/status 等）的前置条件，错误地加在了 install 入口本身。

另外：`install_repo()` 虽然末尾会调 `init_repo()`，但 CLI 转发路径并未使用它——所以 fix 必须落在 `install_agent()`，不能只改 `install_repo()`。

# Fix Scope

- **修改文件**：`src/harness_workflow/workflow_helpers.py`
- **修改行号**：`4382-4400`（`install_agent()` 函数头）
- **修改方式**：把 `ensure_harness_root(root)` 替换为条件分支：
  - 如 `.workflow/` 或 `.workflow/context` 缺失 → stdout 打印 `No .workflow/ found, running harness init first...`，调用 `init_repo(root, write_agents=..., write_claude=...)`，再 `ensure_config(root)`；
  - 否则 → 保留原行为 `ensure_harness_root(root)`。
- **out of scope**：
  - `ensure_harness_root()` 自身不改（其他命令仍以它作为 guard）。
  - 不改 `runtime.yaml`。
  - 不改模板种子泄漏作者 `req-25` 状态的独立问题（已记录在 derivative findings）。

# Fix Plan

1. 在 `install_agent()` 开头用 `workflow_dir = root / ".workflow"` 与 `workflow_context_dir = workflow_dir / "context"` 做显式探测。
2. 两者任一缺失时：
   - 打印 `No .workflow/ found, running harness init first...`
   - 调用 `init_repo(root, write_agents=(agent in ("codex","qoder","kimi")), write_claude=(agent=="claude"))`
   - 调用 `ensure_config(root)` 保证后续 helper 的 config 假设成立
3. 否则（已存在）：调用 `ensure_harness_root(root)` 维持原 guard 语义。
4. 后续 skill 模板扫描、复制、CLAUDE.md/AGENTS.md bootstrap 逻辑不动。

# Validation Criteria

5 个测试场景全部 PASS：
1. 空仓 `git init`
2. `harness install --agent claude` 自动 init（打印提示，exit 0，`.workflow/` 与 `.claude/skills/harness/` 存在）
3. `harness status` 正常输出
4. `harness requirement "smoke test"` 成功创建 req-01
5. 在已存在 `.workflow/` 的仓再跑 `harness install`，`runtime.yaml` 与 `req-01-smoke test.yaml` md5 不变（无状态损坏）

详见 `test-evidence.md`。

# Validation Result

- [x] 5/5 PASS — 验证通过
- 测试时间：2026-04-19
- 测试脚本：inline（bash），见 `test-evidence.md`
