---
id: bugfix-4
title: scaffold 清洗 harness-workflow 历史数据
created_at: 2026-04-19
---

# Problem Description

`harness install` / `harness init` 在空仓（未带 `.workflow/` 历史的新仓）执行后，生成的 `.workflow/state/runtime.yaml` 直接携带本仓（harness-workflow）当前的真实状态 `current_requirement: req-25`、`stage: done`、`active_requirements: [req-25]`；`.workflow/state/sessions/` 混入 req-02~req-11 的会话记录；`.workflow/flow/archive/`、`.workflow/flow/requirements/req-25-...`、`.workflow/flow/suggestions/archive/sug-0X.md`、`.workflow/archive/{legacy-cleanup,v0.1.0-...,v0.2.0-...,qoder}`、`.workflow/state/requirements/req-*.yaml` 等目录携带本仓的历史归档和状态索引。`OPTIONAL_EMPTY_DIRS` 中的 legacy 路径 `.workflow/flow/archive` 因 scaffold 里已有实体文件，cleanup_legacy_workflow_artifacts 剪空失败，最终仍以作者仓历史形态呈现。

**影响范围**：任何通过 `harness install` 初始化的新仓都会继承作者仓的进行中需求、历史会话、建议池和归档，严重破坏新仓的干净初始状态，也让用户无法区分"我刚 init"和"有人把作者仓拷进来了"。

# Root Cause Analysis

触发链：
`harness install` → `install_repo()` → `init_repo()` → `_sync_requirement_workflow_managed_files()` → `_managed_file_contents()` → `_scaffold_v2_file_contents()`。

`_scaffold_v2_file_contents()`（`workflow_helpers.py:366-382`）遍历 `src/harness_workflow/assets/scaffold_v2/` 下所有文件，把内容以 `{相对路径: 原文}` 灌入 managed 字典再逐条写入目标仓；过滤规则仅排除 `"/requirements/"` 路径（针对作者仓的需求目录），未过滤 `state/runtime.yaml`、`state/sessions/*`、`state/requirements/*.yaml`、`flow/archive/**`、`flow/requirements/req-25-*`、`flow/suggestions/archive/sug-*.md`、`archive/**`、`state/action-log.md`、`context/backup/**` 等承载本仓进行中业务数据的文件。

`_sync_requirement_workflow_managed_files()` 在写入完成后调用 `save_requirement_runtime(root, load_requirement_runtime(root))`（line 2545），load 的是刚被复制的污染 `runtime.yaml`，再次写回时虽然会与 `DEFAULT_STATE_RUNTIME` 合并，但由于 load 已含作者仓真实字段，合并结果仍是污染内容。

根因：**scaffold_v2 目录在历次"同步最新 .workflow/ 模板"操作（req-07、req-08 等）中，被误当作主仓 mirror 全量拷贝，把作者仓的运行时状态、会话、需求、归档、建议一并纳入 scaffold 包**。真正 clean slate 所需的是"模板骨架 + 空状态"，而不是"当前活跃仓的完整快照"。

# Fix Scope

**静态资产清洗（不改 Python 代码）**：

- `src/harness_workflow/assets/scaffold_v2/.workflow/state/runtime.yaml`：重写为 `DEFAULT_STATE_RUNTIME` 等价初始值
- `src/harness_workflow/assets/scaffold_v2/.workflow/state/action-log.md`：清空，仅保留 `# Action Log` 标题
- 删除整棵子树：
  - `.workflow/state/sessions/req-02..req-11/` 共 10 个目录及其全部文件
  - `.workflow/state/requirements/` 下 20 个 `req-*.yaml` / `.bak` 文件
  - `.workflow/flow/archive/`（含 `main/` 下 30+ 个历史需求归档和 `req-20-...` 独立归档）
  - `.workflow/flow/requirements/req-25-harness 完全由 harness-manager 角色托管/`
  - `.workflow/flow/suggestions/archive/sug-01..sug-07.md`
  - `.workflow/archive/legacy-cleanup/` `.workflow/archive/v0.1.0-self-optimization/` `.workflow/archive/v0.2.0-refactor/`、`.workflow/archive/qoder` 文件
  - `.workflow/context/backup/legacy-cleanup/`

**不在本次 bugfix 范围**：
- `_scaffold_v2_file_contents()` 过滤规则加固（作为独立 suggestion 记录，避免改动耦合面过大）
- `OPTIONAL_EMPTY_DIRS` 调整（当前 `.workflow/flow/archive` 用于老仓 legacy 剪空，保持原样）
- scaffold 同步机制的 CI 防护（lint 已有 `_check_scaffold_v2_sync`，只校验 `stages.md/WORKFLOW.md/CLAUDE.md` 3 个文件，不检查污染）

# Fix Plan

1. 重置 `scaffold_v2/.workflow/state/runtime.yaml` 为 9 个初始字段（字段顺序与 `save_requirement_runtime` 的 `ordered_keys` 一致）
2. 重置 `scaffold_v2/.workflow/state/action-log.md` 为只含标题行
3. `rm -rf` 上述列出的污染子树（一次性批量，保留父目录作为空骨架）
4. 验证：
   - `_scaffold_v2_file_contents()` 返回文件数从 ~800+ 降到 72
   - scaffold 下无 `req-25`、`req-XX` 命名的目录/文件
   - 空仓 `harness install --agent claude` 后 `.workflow/state/runtime.yaml` 为初始值
5. 回归验证主仓 `harness status` 仍能读取 `bugfix-4/regression`

# Validation Criteria

1. **runtime 初始值**：新仓 `runtime.yaml` 9 个字段均为初始值，无 `req-25` / `bugfix-X` 残留
2. **无污染目录**：`.workflow/state/sessions/` / `.workflow/state/requirements/` / `.workflow/flow/requirements/` 均为空；`.workflow/flow/archive/` / `.workflow/archive/` / `.workflow/context/backup/` 均不存在或为空
3. **无历史建议**：`.workflow/flow/suggestions/` 不存在或无 `sug-XX`
4. **smoke 创建可用**：`harness requirement "smoke"` 成功创建 req-01，runtime 正确更新
5. **主仓未受影响**：清洗后 `harness status` 在主仓仍能读取 bugfix-4/regression 等真实状态
6. **代码未回退**：`workflow_helpers.py` 能 py_compile；现有 pytest 无 regression

全部达成，见 `test-evidence.md`。
