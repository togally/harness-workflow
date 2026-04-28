---
id: bugfix-9
title: force-managed 透传修复 + user-write 门禁误报修复
created_at: 2026-04-28
---

# Problem Description

PetMall 用户实测 `harness install --force-managed` 暴露两个 bugfix-8 后遗症：

**Bug A — `--force-managed` 透传断链**
- 现象：`install_repo` 入口 stderr 打印 `force_managed received: True`，但内部 sync 调用仍输出 `[update_repo] skipping user-modified file ... (force_managed=False)`，用户改过的文件未被 `--force-managed` 强制覆盖。
- 触发条件：`harness install --force-managed`（`force_skill=False` 路径），目标项目含用户手改的 managed 文件。
- 影响范围：`install_repo` 的 `not force_skill` 分支（即 `harness install` 而非 `harness update`）。

**Bug B — user-write-protected-zones 把 skill 工具产出误报 269 个野文件**
- 现象：`[user-write-protected-zones] ABORT: 269 violation(s)` 含 `.claude/skills/harness/SKILL.md` 等完全由 `install_local_skills()` 产出的文件。
- 触发条件：用户项目（非 dev repo）执行 `harness install`，`check_user_write_protected_zones` 扫描 `.claude/skills/` 等目录。
- 影响范围：所有以用户项目模式运行 `harness install` / `harness validate --contract user-write-protected-zones` 的场景。

# Root Cause Analysis

**Bug A 根因（chg-03 of bugfix-8 暴露但未真修）**：
`install_repo` 在 `not force_skill` 分支（line ~3847）调用 `init_repo(root, write_agents=..., write_claude=...)`，但 `init_repo` 签名不含 `force_managed` 参数，内部硬编码 `force_managed=False` 调用 `_sync_requirement_workflow_managed_files`。此调用发生在 bugfix-7 / chg-02 的 `tool_version` 失配检测（line ~3884）之前，因此即便 `install_repo` 入口收到 `force_managed=True`，`init_repo` 这一路的 sync 仍走 `False`，触发 `skipping user-modified` 分支。

**Bug B 根因（chg-04 of bugfix-8 设计缺陷）**：
`check_user_write_protected_zones` 的 `protected_zones` 列表包含 `.claude/skills`、`.claude/commands`、`.codex/skills`、`.codex/commands`、`.kimi/skills`、`.kimi/commands`、`.qoder/skills`、`.qoder/commands`。这些目录是 `install_local_skills()` 的纯工具产出，不在 scaffold_v2 mirror（`include_agents=False`），不在 `managed-files.json`（只跟踪 `.workflow/`），也不在 `_SCAFFOLD_V2_MIRROR_WHITELIST`，因此三级豁免全部失效，所有 skill/commands 文件均被误报为野文件。

# Fix Scope

**chg-01（init_repo force_managed 透传修复）**：
- 修改 `src/harness_workflow/workflow_helpers.py`：`init_repo` 新增 `force_managed: bool = False` 参数，向 `_sync_requirement_workflow_managed_files` 透传。
- `install_repo` 内对 `init_repo` 的调用改为 `init_repo(..., force_managed=force_managed)`。
- `harness_init.py` 与 `install_agent` 内的 `init_repo` 调用保持默认值 `False`（初始化场景无需强制覆盖）。

**chg-02（user-write-protected-zones 移除 skill/commands 扫描列表）**：
- 修改 `src/harness_workflow/validate_contract.py`：`check_user_write_protected_zones` 的 `protected_zones` 只保留 `.workflow`，移除所有 `.{agent}/skills` / `.{agent}/commands` 条目。

**范围外**：managed_state 登记 skill 文件路径（备选方案，复杂度高，降级为 sug 池）。

# Fix Plan

1. `workflow_helpers.py::init_repo` 新增 `force_managed: bool = False` 参数并透传（已实施）
2. `workflow_helpers.py::install_repo` 内 `init_repo(...)` 调用加 `force_managed=force_managed`（已实施）
3. `validate_contract.py::check_user_write_protected_zones` `protected_zones` 只保留 `.workflow`（已实施）
4. 新增 bugfix-9 回归测试（TC-A1 / TC-A2 / TC-B1 / TC-B2）
5. dogfood 本仓 `harness install --check --force-managed` 验证 force_managed=True 全链路
6. 模拟 user project 跑 user-write-protected-zones 验证 chg-02 不误报

# Validation Criteria

- TC-A1：`init_repo(root, ..., force_managed=True)` 调用链——`_sync_requirement_workflow_managed_files` 收到 `force_managed=True`，用户改过的 managed 文件被正确覆盖（不出现 `skipping user-modified` stderr）
- TC-A2：grep `workflow_helpers.py` 所有 `init_repo(` call site 确认不存在硬编码 `force_managed=False`（install_repo 的调用改对，init 类调用保留默认）
- TC-B1：tmpdir user project（无 `src/`、无 `pyproject.toml::name=harness-workflow`）+ 含 `.claude/skills/harness/SKILL.md`（工具产出）→ `check_user_write_protected_zones` exit 0（不报 violation）
- TC-B2：tmpdir user project + 在 `.workflow/context/roles/my-custom.md` 写野文件 → `check_user_write_protected_zones` ABORT exit 1（仍能拦真野文件）
- dogfood 本仓 `harness install --check --force-managed` 全程 `force_managed=True`，无 `force_managed=False` skip 误打印
- 本仓 `harness validate --contract user-write-protected-zones` exit 0（dev mode 豁免）
- 全量 pytest 0 新增 fail
