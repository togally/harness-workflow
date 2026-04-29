---
id: bugfix-11
title: "PetMallPlatform-artifacts误放机器型流程文档"
created_at: 2026-04-29
operation_type: bugfix
stage: regression
---

## Problem Description

- **Symptom**：用户在 `/Users/jiazhiwei/claudeProject/workspace/PetMallPlatform`（harness 用户仓库）执行 `harness requirement "梳理历史脚本统一使用liquibase管理"`，CLI 把机器型流程文档（`requirement.md` 10891B / `session-memory.md` 10067B / 空 `changes/` 子目录）落到 `artifacts/v1.0.0/requirements/req-01-梳理历史脚本统一使用liquibase管理/`，违反 `repository-layout.md` §1 "三大子树语义总览" 与 §3 "机器型文档权威落位" 契约（`artifacts/{branch}/` 仅装对人产物，机器型必落 `.workflow/flow/requirements/`）。
- **Impact**：
  1. 任何**新启用 harness 的下游用户仓库**第一次执行 `harness requirement` 时，分配的 req-id 必然是 `req-01` ~ `req-10` 数量级（< 39），CLI `create_requirement` 走 legacy 分支，**100% 复发**——这是设计层路径选择策略与"全新仓库"场景的根本失配，影响面 = 所有未来下游用户。
  2. 用户仓库切到新 git branch（如 PetMallPlatform 从 `member` 切到 `v1.0.0`）后，`_next_req_id` 仅扫当前 branch 路径，`max_num` 归零、再次返回 `req-01`，触发同一 legacy 分支；同时与历史归档 req-id 重号，**重号风险**与本 bug 同源。
  3. 当前 PetMallPlatform 仓库 `runtime.yaml` 显示工作流仍在 `req-01 / requirement_review`，下游 stage（planning / executing / 归档）会沿用错误路径继续产文，污染面持续扩大。
- 报告人：用户（在 harness-workflow 仓库以 `harness bugfix` 触发本 bugfix-11）。

## Root Cause Analysis

- **Root cause**：见 `regression/diagnosis.md`。一句话——harness CLI（部署版 0.2.0）`create_requirement` 用 `_use_flow_layout(req_id) / _use_flat_layout(req_id)` 三段式分支判断机器型文档落位，阈值常量 `FLOW_LAYOUT_FROM_REQ_ID = 41` 与 `FLAT_LAYOUT_FROM_REQ_ID = 39` 默认假设 req-id 沿 harness-workflow **自身仓库**的全局 timeline 单调递增；下游用户仓库新建 req 时 `_next_req_id` 必然返回 `req-01..NN`（< 39），强制走 legacy 分支落 `artifacts/{branch}/requirements/{slug}/`，与 req-41+ 的契约面（`repository-layout.md`）正面冲突。
- **Confirmed real issue**：**YES / 真实问题**。证据链完整：1）`PetMallPlatform/.workflow/state/action-log.md` 第一行铁证——`harness requirement "..."` 命令落地 artifacts 路径；2）部署版 `workflow_helpers.py:4773 create_requirement` 源码 else 分支显式 `requirement_dir = root / "artifacts" / branch / "requirements" / dir_name`；3）契约文件 `PetMallPlatform/.workflow/flow/repository-layout.md` 已是 req-41+ 新版，与 CLI 实际行为正面打架。

## Fix Scope

- **Affected files / modules**（候选，由 executing 最终敲定）：
  - `src/harness_workflow/workflow_helpers.py`：`create_requirement` / `_use_flow_layout` / `_use_flat_layout` 三段式判定逻辑；同源问题方法 `create_change` / `create_regression` / `_next_req_id` 是否也要改（连带）。
  - `src/harness_workflow/cli.py`：`harness requirement` / `harness change` / `harness regression` 命令面是否需新增 `--layout-mode` flag（候选方案 B）。
  - `.workflow/flow/repository-layout.md`：§4 "历史存量豁免与三段式分水岭" 段是否需声明"下游用户仓 fresh-install 直接用 flow layout"。
  - 测试：`tests/test_create_requirement_layout.py` 等覆盖三段式分支的测试需补"下游 fresh repo 场景"用例。
- **Out of scope**：
  - **不改 PetMallPlatform 仓库本身**（不挪 artifacts/v1.0.0 下已落地的 req-01 文档；如需 PetMallPlatform 侧手工迁移，由用户后续决定，与本 bugfix 无关）。
  - **不动 harness-workflow 自身仓的 req-02 ~ req-40 历史豁免**（`repository-layout.md §4` 三段式分水岭保留）。
  - 不改 `_next_req_id` 跨 branch 扫描归档的策略（重号风险作为独立 sug 入池，详见 diagnosis.md `## 待处理捕获问题`）。
- **H-E3 扩范围（round-2 expanded）**：bugfix 维度同型病一并修复。
  - `src/harness_workflow/workflow_helpers.py`：删除 `BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID` 常量 + `_use_flow_layout_for_bugfix()` 函数 + `create_bugfix` 中 `use_flow` 条件分支 → 无条件 flow layout。
  - `tests/test_bugfix_layout_v2.py`：整文件 git rm（文件名绑定已废弃函数名）。
  - `tests/test_bugfix_11_flow_layout.py`：新增 `CreateBugfixUnconditionalFlowLayoutTest`（5 TC）+ `DeprecatedSymbolsLintTest` 新增 2 反例断言。

## Fix Plan

**用户选定方向 C**（废弃三段式分水岭，全仓统一走 flow layout）。

### S1: 源码（workflow_helpers.py）

- 删除常量 `FLAT_LAYOUT_FROM_REQ_ID` / `FLOW_LAYOUT_FROM_REQ_ID` / `LEGACY_REQ_ID_CEILING`（含 validate_human_docs.py 内联删除）
- 删除 `_use_flat_layout()` 函数
- **删除 `_use_flow_layout(req_id)` 函数本体**（bugfix-11 round-2 修正：round-1 误改为「恒 True」，round-2 真正删除函数 + 6 处调用改为无条件 flow layout 内联路径）
- `create_requirement` / `create_change` / `create_regression` / `_next_chg_id` / `archive_requirement`：删除三路 if/elif/else 分支，统一走 flow layout

### S2: 契约（repository-layout.md）

- 删除 §4 "历史存量豁免与三段式分水岭"
- §3 表格从三列（legacy/flat/flow）改为单列 flow layout
- 更新前后引用（header / §3.1 / 原 §5→§4 / 原 §6→§5）
- scaffold_v2 mirror 同步

### S3: 存量清理（B2+B3）

- `artifacts/main/regressions/reg-01~05` → `.workflow/flow/archive/main/`
- `artifacts/main/archive/bugfixes/bugfix-1,2,3,4,6` → `.workflow/flow/archive/main/`

### S5: 测试

- `tests/test_use_flow_layout.py`：全量重写（30 TC，100% pass）
- `tests/test_create_requirement_flat.py`：更新为方向C 期望
- 其余受影响 test 文件更新

## Validation Criteria

- **VC-01（核心 round-2 修正）**：`pytest tests/test_bugfix_11_flow_layout.py -v` 18/18 通过，所有 req-id 一律走 flow layout；`test_use_flow_layout.py` 已删除（文件名绑定已废弃函数名）。
- **VC-02**：`pytest tests/` 无新增回归（pre-existing 51 fail 不变，diff = 0 新增；round-2 跑得 715 passed / 51 fail）。
- **VC-03（H-E3 扩范围关键词扩展）**：Lint-1 grep `src/harness_workflow/*.py` 中 `_use_flow_layout\|_use_flat_layout\|FLAT_LAYOUT_FROM_REQ_ID\|FLOW_LAYOUT_FROM_REQ_ID\|LEGACY_REQ_ID_CEILING\|BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID` = 0 命中（字面 grep，现在 `_use_flow_layout_for_bugfix` 也已删除，不存在子串命中问题）。
- **VC-04**：`create_requirement` 对 req-01 / req-38 / req-39 / req-40 全部落 `.workflow/flow/requirements/`，不在 artifacts/ 下建 requirement.md。
- **VC-05（H-E3）**：`create_bugfix` 对 bugfix-1 / bugfix-5 / bugfix-6+ 全部落 `.workflow/flow/bugfixes/`，无条件 flow layout。

**round-2 实际结果**：VC-01 ✓ / VC-02 ✓ / VC-03 ✓（_use_flow_layout 函数真正删除）/ VC-04 ✓（详见 test-evidence.md + session-memory.md round-2 段）。
**round-2 H-E3 扩范围实际结果**：VC-03 扩关键词 ✓ / VC-05 ✓（51 fail 不变，708 passed）。
