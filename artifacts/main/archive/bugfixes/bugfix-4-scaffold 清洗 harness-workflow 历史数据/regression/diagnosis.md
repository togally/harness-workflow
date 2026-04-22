# Regression Diagnosis — bugfix-4

## Issue
`harness install` / `harness init` 把本仓（harness-workflow）自身的历史数据泄漏到用户新仓。空仓初始化后 `.workflow/state/runtime.yaml` 直接出现 `current_requirement: req-25`、`active_requirements: [req-25]`，`.workflow/state/sessions/`、`.workflow/flow/archive/`、`.workflow/flow/suggestions/archive/`、`.workflow/flow/requirements/req-25-.../`、`.workflow/state/requirements/req-*.yaml` 等混入作者仓实际内容。

## Routing Direction
- [x] Real issue → proceed to fix (regression → executing → testing)

## Root Cause Analysis

### 触发链
1. `harness install` → `install_repo()` → `init_repo()` → `_sync_requirement_workflow_managed_files()` → `_managed_file_contents()` → `_scaffold_v2_file_contents()`
2. `_scaffold_v2_file_contents()` 遍历 `src/harness_workflow/assets/scaffold_v2/` 下所有文件，把每个文件的内容以 `{相对路径: 原文}` 灌入 managed 字典，然后 `_sync_requirement_workflow_managed_files()` 逐条写入目标仓。
3. 当前过滤只排除 `"/requirements/"` 和以 `"requirements/"` 开头的路径（注释目标是隔离 harness 自身的需求目录），但未过滤：
   - `.workflow/state/runtime.yaml`（本仓运行时状态，带 `req-25` 具体 ID）
   - `.workflow/state/sessions/req-02..req-11/*`（本仓会话历史）
   - `.workflow/state/requirements/req-*.yaml[.bak]`（本仓需求状态索引）
   - `.workflow/flow/archive/main/req-01..req-22/*`（本仓归档）
   - `.workflow/flow/archive/req-20-.../`（归档历史）
   - `.workflow/flow/requirements/req-25-.../`（当前活跃需求目录）
   - `.workflow/flow/suggestions/archive/sug-01..sug-07*.md`（本仓建议池）
   - `.workflow/archive/legacy-cleanup/*`、`.workflow/archive/v0.1.0-*`、`.workflow/archive/v0.2.0-*`、`.workflow/archive/qoder`（旧版本归档）
   - `.workflow/context/backup/legacy-cleanup/*`（旧版本上下文备份）
   - `.workflow/state/action-log.md`（本仓动作日志，带 req-24 chg-05/06 记录）
4. `_sync_requirement_workflow_managed_files()` 第 2545 行在 managed 写入后执行 `save_requirement_runtime(root, load_requirement_runtime(root))`，load 出来的是刚被复制的污染文件，所以即便 `DEFAULT_STATE_RUNTIME` 定义了空初始值，污染内容仍被原样写回。
5. `OPTIONAL_EMPTY_DIRS = [Path(".workflow") / "flow" / "archive"]` 在 `cleanup_legacy_workflow_artifacts()` 中会尝试"清空旧 archive"，但 scaffold 里已经带着一堆实文件，剪枝失败，反而看起来像"作者仓 legacy 路径也应该在新仓创建"。

### 污染文件清单（统计）

按 scaffold_v2 下二级目录粗粒度统计（共 903 个文件）：

| 路径 | 文件数 | 性质 |
|------|--------|------|
| `.workflow/flow/archive/main/req-01..req-22/**` | ~382 | 作者仓历史归档（req-01..req-22 的 requirement.md、done-report.md、plan.md、session-memory 等） |
| `.workflow/flow/archive/req-20-审查Yh-platform.../**` | 1 | 额外归档 |
| `.workflow/archive/legacy-cleanup/**` | 127 | 旧系统残留备份（flow/requirements/req-01 历史 + workflow/context/hooks 旧版） |
| `.workflow/archive/v0.1.0-self-optimization/**` | 80 | 旧版本重构归档 |
| `.workflow/archive/v0.2.0-refactor/**` | 67 | 旧版本重构归档 |
| `.workflow/archive/qoder` | 1 | 单文件，旧 qoder 配置历史 |
| `.workflow/state/sessions/req-02..req-11/**` | 60 | 作者仓会话记录（含 done-report、session-memory、validation-report） |
| `.workflow/context/backup/legacy-cleanup/**` | 57 | 旧 tools 备份（tools-3/4/5 等） |
| `.workflow/flow/requirements/req-25-.../**` | 29 | 当前活跃需求（requirement.md、changes、regression 等） |
| `.workflow/state/requirements/req-*.yaml[.bak]` | 20 | 作者仓需求索引（req-02..req-25） |
| `.workflow/flow/suggestions/archive/sug-01..sug-07*.md` | 7 | 已落地的建议历史（sug-01 ~ sug-07） |
| `.workflow/state/runtime.yaml` | 1 | **关键污染**：`current_requirement: req-25`、`stage: done`、`active_requirements: [req-25]` |
| `.workflow/state/action-log.md` | 1 | 本仓 req-24 操作日志 |
| `.workflow/state/platforms.yaml` | 1 | **保留**：平台列表 (codex/qoder/cc/kimi) 属于合法默认值 |
| `.workflow/state/experience/index.md` | 1 | **保留**：经验索引通用规则 |

合计约 833 个"本仓特有"文件需要清除；其余 ~70 个文件（模板/规则/工具目录 骨架）为合法 scaffold。

### runtime.yaml 初始值（符合 `DEFAULT_STATE_RUNTIME`）

```yaml
current_requirement: ""
stage: ""
conversation_mode: "open"
locked_requirement: ""
locked_stage: ""
current_regression: ""
ff_mode: false
ff_stage_history: []
active_requirements: []
```

（依照 `workflow_helpers.py:55-67` 的 DEFAULT_STATE_RUNTIME + 346-363 行 ordered_keys。`operation_type` / `operation_target` 字段虽在 DEFAULT_STATE_RUNTIME 中，但 ordered_keys 未列出；主仓既有 runtime.yaml 也未写入这两个字段，保持与主仓一致。）

### OPTIONAL_EMPTY_DIRS legacy 路径

当前 `workflow_helpers.py:88-90`:
```python
OPTIONAL_EMPTY_DIRS = [
    Path(".workflow") / "flow" / "archive",
]
```

说明：`.workflow/flow/archive` 在新系统已被 `artifacts/{branch}/archive` 或 `.workflow/flow/requirements` + `.workflow/state/requirements` 取代；它是 legacy 路径，不应在新仓主动创建。cleanup_legacy_workflow_artifacts 里虽然会"尝试剪空"，但 `_required_dirs` 并没有创建它；OPTIONAL_EMPTY_DIRS 的语义是"如果已存在且空则删除"。当前 scaffold 污染后它被实体目录+文件填满，所以剪不掉。清洗 scaffold 后该语义即可正确工作。

为了彻底阻止新仓出现空 `.workflow/flow/archive`，建议 **保留** `OPTIONAL_EMPTY_DIRS` 本身以向后兼容老仓，**但从 scaffold_v2 中删除 `.workflow/flow/archive/` 整棵树**；这样：
- 老仓升级时，cleanup_legacy_workflow_artifacts 仍会尝试剪空旧 archive；
- 新仓 init 时，scaffold 不再复制任何 flow/archive 内容，OPTIONAL_EMPTY_DIRS 只会观察到"路径不存在"，不创建。

## 修复策略

### Step A — 清洗 `src/harness_workflow/assets/scaffold_v2/` 的污染文件

| 动作 | 目标 |
|------|------|
| 重置文件内容 | `.workflow/state/runtime.yaml` → 写入初始值（与 DEFAULT_STATE_RUNTIME 一致） |
| 清空文件内容 | `.workflow/state/action-log.md` → 保留骨架标题 `# Action Log\n` |
| 删除整棵子树 | `.workflow/state/sessions/req-*`（保留空目录 sessions/ 本身） |
| 删除整棵子树 | `.workflow/state/requirements/` 下所有 `req-*.yaml` 和 `.bak` |
| 删除整棵子树 | `.workflow/flow/archive/` |
| 删除整棵子树 | `.workflow/flow/requirements/req-*` |
| 删除整棵子树 | `.workflow/flow/suggestions/archive/` 下所有 sug-*.md |
| 删除整棵子树 | `.workflow/archive/legacy-cleanup/` |
| 删除整棵子树 | `.workflow/archive/v0.1.0-self-optimization/` |
| 删除整棵子树 | `.workflow/archive/v0.2.0-refactor/` |
| 删除文件 | `.workflow/archive/qoder` |
| 删除整棵子树 | `.workflow/context/backup/legacy-cleanup/` |

保留（验证为合法 scaffold 骨架）：
- `.workflow/state/runtime.yaml`（重写为初始值）
- `.workflow/state/platforms.yaml`
- `.workflow/state/action-log.md`（清空只留标题）
- `.workflow/state/experience/index.md`
- `.workflow/flow/stages.md`
- `.workflow/flow/suggestions/`（空目录骨架）
- `.workflow/context/**`（除 backup/legacy-cleanup 外）
- `.workflow/constraints/*.md`
- `.workflow/evaluation/*.md`
- `.workflow/tools/**`
- `CLAUDE.md`, `WORKFLOW.md`, `README.md`

### Step B — `OPTIONAL_EMPTY_DIRS` 处理

**保持现状**（保留 `.workflow/flow/archive` 作为老仓兼容剪枝目标），不从列表中删除；因为 scaffold 中这棵树已删，新仓 init 不会再创建该目录。

### Step C — 是否需要改 `_scaffold_v2_file_contents` 过滤规则？

当前只排除 `/requirements/` 的路径过滤，主要是"不复制 requirements 业务目录"。清洗后的 scaffold 已无污染文件，但作为"防御性"加固，可以追加过滤规则（可选，低优先级），例如排除：
- `flow/archive/`、`archive/legacy-cleanup/`、`archive/v*`、`state/sessions/`、`state/requirements/req-*`

**本次 bugfix 先走"静态清洗 scaffold_v2"路径**，因为：
1. 清洗是最直接最低复杂度的做法；
2. 代码层加防御需要在 `_scaffold_v2_file_contents` 重写匹配逻辑，耦合更深，风险更高；
3. 后续若有同类回归，建议作为独立 suggestion（"加一层 scaffold 防污染过滤"）沉淀。

## Required Inputs
无。所有初始值和删除范围可由 DEFAULT_STATE_RUNTIME 与 bugfix 诊断自推导。
