# Test Evidence — bugfix-3 (install 在空仓自动 init)

## Change Under Test
`src/harness_workflow/workflow_helpers.py:4372-4400` — `install_agent()` 现在会在 `.workflow/` 或 `.workflow/context` 不存在时，打印 `No .workflow/ found, running harness init first...` 并自动调用 `init_repo()`，再走原 skill 安装逻辑。

## Test Environment
- Date: 2026-04-19
- Python package: `harness-workflow==0.1.0`（editable install from `/Users/jiazhiwei/IdeaProjects/harness-workflow`，pipx venv `python3.14`）
- Test root: `/tmp/harness-bugfix3-fresh-1776571095`（空仓，`git init`）
- Test root #2: `/tmp/harness-init-baseline-1776571130`（基线 `harness init` 对照）

## Results Matrix

| # | Scenario | Command | Expected | Actual | Exit Code | Verdict |
|---|----------|---------|----------|--------|-----------|---------|
| T1 | 准备空仓 | `mkdir /tmp/harness-bugfix3-fresh-<ts> && cd ... && git init -q` | 仓库创建成功，无 `.workflow/` | 仓库只有 `.git/`，无 `.workflow/` | 0 | PASS |
| T2 | 空仓运行 install | `harness install --agent claude` | 自动 init，打印 "No .workflow/ found, running harness init first..."，复制 skill，写入 CLAUDE.md bootstrap | 输出包含 `No .workflow/ found, running harness init first...`、`Installed harness skill to .claude/skills/harness`、`Bootstrap already present in CLAUDE.md`（本轮 CLAUDE.md 来自 init 创建的 bootstrap）；`.workflow/state/runtime.yaml` 存在，`.claude/skills/harness/SKILL.md` 存在 | 0 | PASS |
| T3 | 安装后查 status | `harness status` | 正常输出 runtime 字段 | 输出 `current_requirement: req-25` / `stage: done` / `active_requirements: req-25`（注：模板种子带了作者自身 req-25 状态，属已知遗留问题，非本 fix 引入） | 0 | PASS |
| T4 | 创建 smoke requirement | `harness requirement "smoke test"` | 成功创建 req-01 | 输出 `Requirement workspace: .../artifacts/main/requirements/req-01-smoke test`、`created .workflow/state/requirements/req-01-smoke test.yaml`；目录与 yaml 实际存在 | 0 | PASS |
| T5 | 在已存在 `.workflow/` 的仓再跑 install | `harness install --agent claude`（第二次） | 不破坏现有状态（runtime.yaml、requirements/*.yaml 不变） | md5 对比：`runtime.yaml` 前后 `a756a9898175c2b8df4550ef6df9f59b` 相同；`req-01-smoke test.yaml` 前后 `77de117b7a6d2fc7f228fba9b677a921` 相同；stdout 仅报告 skill 文件的 modify/安装，未经过 auto-init 分支 | 0 | PASS |

## Raw Log Excerpts

### T2（关键标记）
```
$ harness install --agent claude
No .workflow/ found, running harness init first...
Created files:
- .../.workflow/context/...
- .../.workflow/state/runtime.yaml
...
Changes detected:
  [add] SKILL.md
  [add] agent/claude.md
  ...
Installed harness skill to .claude/skills/harness
Bootstrap already present in CLAUDE.md
EXIT=0
```

### T3
```
$ harness status
current_requirement: req-25
stage: done
conversation_mode: open
locked_requirement: (none)
locked_stage: (none)
current_regression: (none)
active_requirements: req-25
EXIT=0
```

### T4
```
$ harness requirement "smoke test"
Requirement workspace: /private/tmp/harness-bugfix3-fresh-1776571095/artifacts/main/requirements/req-01-smoke test
- created .../artifacts/main/requirements/req-01-smoke test/requirement.md
- created .workflow/state/requirements/req-01-smoke test.yaml
EXIT=0
```

### T5
```
md5_runtime_before=a756a9898175c2b8df4550ef6df9f59b
md5_req01_before=77de117b7a6d2fc7f228fba9b677a921
$ harness install --agent claude      # 2nd run, .workflow/ already exists
Changes detected:
  [modify] agent/claude.md
  [modify] agent/codex.md
  [modify] agent/kimi.md
Installed harness skill to .claude/skills/harness
Bootstrap already present in CLAUDE.md
md5_runtime_after=a756a9898175c2b8df4550ef6df9f59b
md5_req01_after=77de117b7a6d2fc7f228fba9b677a921
T5 STATE PRESERVED: OK
EXIT=0
```

## Conclusion
- [x] 5/5 PASS — bugfix-3 acceptance criteria satisfied
- 原 bug（empty repo `harness install` → `SystemExit(1)`）已修复：empty repo 下 `harness install --agent claude` 返回 0 并完成完整初始化 + skill 安装。
- 对已初始化仓库无副作用（T5 md5 一致）。

## Derivative Findings (Not Fixed Here)
- **模板种子泄漏作者状态**：`init_repo()` → `_sync_requirement_workflow_managed_files()` 把作者仓的 `runtime.yaml`（含 `req-25`）复制到新仓。属独立的 template hygiene 问题，已记入 session-memory，未在本 bugfix 范围修复。
