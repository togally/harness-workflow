# Regression Diagnosis — bugfix-3

## Issue
在一个刚 `git init` 的空仓（没有 `.workflow/` 目录）中执行 `harness install`（或 `harness install --agent claude`）被拒绝，返回 exit code 1 并打印

> `Harness workspace is missing. Run 'harness install' or 'harness init' first. Missing: <root>/.workflow, <root>/.workflow/context`

错误信息自相矛盾：提示运行 `harness install`，而当前执行的正是 `harness install`。违反 `README.md` 第 50 行（`harness install   # installs skill files for Claude Code / Codex / Qoder / kimicli`）与 `src/harness_workflow/skills/harness/SKILL.md` 第 36 行（`harness install` 的语义为 "Initialize repository and install harness skill"）。

关联：parent requirement `req-25`，P0-01（空仓 `harness install` 被拒）。

## Reproduction

```
TMP=/tmp/harness-bug-verify-$(date +%s)
mkdir -p "$TMP" && cd "$TMP"
git init -q
harness install --agent claude
# -> exit 1, "Harness workspace is missing. Run 'harness install' or 'harness init' first."
```

实测输出（2026-04-19）：

```
Harness workspace is missing. Run `harness install` or `harness init` first.
Missing: /private/tmp/harness-bug-verify-1776571041/.workflow,
         /private/tmp/harness-bug-verify-1776571041/.workflow/context
EXIT=1
```

## Expected Behavior

空仓执行 `harness install`（或 `harness install --agent <agent>`）时，应：
1. 检测 `.workflow/` 不存在；
2. 自动执行 `init` 的初始化逻辑（创建 `.workflow/` 目录骨架、上下文、state 文件等）；
3. 继续完成原本的 install 工作（复制 skill 文件、写入 CLAUDE.md/AGENTS.md bootstrap）；
4. 返回 exit 0。

## Actual Behavior

在第 1 步之前就因硬校验 `ensure_harness_root()` 立即 `SystemExit` 退出，跳过所有安装逻辑。

## Root Cause

调用链（CLI → tool script → helper）：

1. `src/harness_workflow/cli.py:279-286` — `install` 子命令通过 `_run_tool_script("harness_install.py", ...)` 转发。
2. `src/harness_workflow/tools/harness_install.py:23` — tool 脚本调用 `install_agent(root, args.agent)`。
3. `src/harness_workflow/workflow_helpers.py:4372-4382` — `install_agent()` 第一行就是 `ensure_harness_root(root)`。
4. `src/harness_workflow/workflow_helpers.py:2144-2148` — `ensure_harness_root()` 检测 `.workflow/` 与 `.workflow/context` 是否存在，缺失则 `raise SystemExit(...)`。

**根因精确定位**：`src/harness_workflow/workflow_helpers.py:4382` — `install_agent()` 在 skill 模板复制前硬性调用 `ensure_harness_root()`，对空仓必然失败。该校验本应只保护需要已初始化仓库的命令（requirement/change/status 等），不应在 install 入口设置。

注意：`install_repo()`（workflow_helpers.py:2698）本身并无此 bug（末尾会调 `init_repo()`），但它在当前 CLI 转发路径上未被调用；CLI 实际走的是 `install_agent()`，所以 fix 必须落在 `install_agent()`。

## Fix Plan

采用 **方案 A 的 install_agent 变体**：在 `install_agent()` 起始处，若检测到 `.workflow/` 或 `.workflow/context` 缺失，先自动调用 `init_repo()`，然后再做原有的 skill 安装工作。

具体步骤：
1. `src/harness_workflow/workflow_helpers.py:4382` — 将 `ensure_harness_root(root)` 替换为"缺失则自动 init"的逻辑：
   - 判定 `.workflow` 或 `.workflow/context` 是否缺失；
   - 缺失时 stdout 打印 `No .workflow/ found, running harness init first...`；
   - 调用 `init_repo(root, write_agents=(agent in ("codex","qoder","kimi")), write_claude=(agent=="claude"))`；
   - 然后调用 `ensure_config(root)` 保持后续假设；
   - 已存在时保持原语义，调用 `ensure_harness_root(root)`。
2. 不修改 `ensure_harness_root()` 本身（它在其他命令中作为 guard 仍需保留）。
3. 不修改 `runtime.yaml`。
4. 不修改已存在 `.workflow/` 仓的行为（`.workflow/` 已在时走 ensure_harness_root 老路径 → 与旧行为一致）。

## Routing Direction
- [x] Real issue → proceed to fix
- [ ] False positive → revert to previous stage

路由：实现问题 → executing。

## Required Inputs
无。诊断可由代码自证，无需人工补充。
