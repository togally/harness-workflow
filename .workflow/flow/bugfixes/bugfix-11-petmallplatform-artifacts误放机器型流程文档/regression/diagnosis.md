---
id: bugfix-11
title: "PetMallPlatform-artifacts误放机器型流程文档"
created_at: 2026-04-29
operation_type: bugfix
stage: regression
---

## 问题描述

用户在 PetMallPlatform 仓（`/Users/jiazhiwei/claudeProject/workspace/PetMallPlatform`，git branch = `v1.0.0`）执行 `harness requirement "梳理历史脚本统一使用liquibase管理"` 后，机器型流程文档（`requirement.md` / `session-memory.md` / 空 `changes/` 子目录）落到 `artifacts/v1.0.0/requirements/req-01-梳理历史脚本统一使用liquibase管理/`，不在权威机器型路径 `.workflow/flow/requirements/{req-id}-{slug}/`，违反 `.workflow/flow/repository-layout.md` §1 "三大子树语义总览" 与 §3 "机器型文档权威落位" 契约。

## 证据

### 现场复核（独立 ls / read，不盲信主 agent 初步证据）

1. **artifacts/ 误放铁证**：
   ```
   artifacts/v1.0.0/requirements/req-01-梳理历史脚本统一使用liquibase管理/
   ├── requirement.md       (11047B, mtime 2026-04-29 17:45 — analyst 写入)
   ├── session-memory.md    (10067B, mtime 2026-04-29 17:34)
   └── changes/             (空目录, mtime 2026-04-29 17:27)
   ```

2. **`.workflow/flow/requirements/` 真空**：`ls /Users/jiazhiwei/claudeProject/workspace/PetMallPlatform/.workflow/flow/requirements/` → 空目录（应为权威路径但未被使用）。

3. **`.workflow/state/requirements/` 仅 yaml**：`req-01-梳理历史脚本统一使用liquibase管理.yaml`（id/title/stage/status/created_at），meta 在 state、正文 md 在 artifacts，**两路径分离**。

4. **runtime.yaml 不是空的（修正主 agent 初步证据 #3）**：
   ```yaml
   operation_type: "requirement"
   operation_target: "req-01"
   current_requirement: "req-01"
   current_requirement_title: "梳理历史脚本统一使用liquibase管理"
   stage: "requirement_review"   # legacy stage（非 req-50+ 新 5-stage 的 analysis）
   active_requirements: [req-01]
   ```
   工作流仍在 requirement_review 活跃中。

5. **action-log.md 第一行铁证（CLI 直接所为）**：
   ```
   ## 2026-04-29T09:35:12Z harness-manager: dispatch analyst for req-01
   - 命令: harness requirement "梳理历史脚本同意使用liquibase管理"
   - 结果: 成功（artifacts/v1.0.0/requirements/req-01-梳理历史脚本同意使用liquibase管理/{requirement.md,session-memory.md} 已落地；runtime stage=requirement_review）
   ```
   **CLI 0.2.0 在执行 `harness requirement` 时主动产文到 artifacts 路径**，非用户手放、非 agent 跨职。

6. **平台版本验证**：
   - `harness --version` → `harness-workflow 0.2.0`，`pipx` 安装路径 `~/.local/pipx/venvs/harness-workflow/lib/python3.14/site-packages/harness_workflow/`，site-packages mtime 2026-04-29 16:48（与 harness-workflow src commit `c12010f` 同日）。
   - 部署版 ≈ src 当前版（无三维失配 / 部署 gap）。

7. **PetMallPlatform 历史背景（与主 agent 初步证据 #4 关联）**：
   - `platforms.yaml` 仅声明 `[codex, qoder, cc, kimi]`（这些是 mirror 平台，不是 git branch）。
   - 仓库内 git branch 实际是 `v1.0.0`（`git branch --show-current` 输出），`_get_git_branch` 据此返回 `"v1.0.0"`，决定 `requirement_dir = artifacts/v1.0.0/requirements/{slug}/`。
   - 仓库**不是 fresh repo**——历史归档存在多个 req（`artifacts/member/archive/requirements/req-04..07`、`artifacts/app_interface/archive/requirements/req-09..10`），但都在**其他 branch 视角**的 archive 子树下。
   - 当前是用户从 `member` 切到新 git branch `v1.0.0` 后第一次执行 `harness requirement`。

### 源码层根因证据（部署版 = src 当前版）

`workflow_helpers.py:4773 create_requirement`（部署版 0.2.0）：

```python
def create_requirement(root, name, requirement_id=None, title=None) -> int:
    req_num_id = requirement_id.strip() if requirement_id else _next_req_id(root)  # → "req-01"
    branch = _get_git_branch(root) or "main"                                       # → "v1.0.0"
    requirement_dir = root / "artifacts" / branch / "requirements" / dir_name      # → artifacts/v1.0.0/requirements/req-01-.../

    if _use_flow_layout(req_num_id):           # req_num_id="req-01" → 1 < 41 → False
        ...
    elif _use_flat_layout(req_num_id):         # 1 < 39 → False
        ...
    else:
        # Legacy 分支（req-id <= 38）：保持旧 requirement.md + changes/ 子目录结构
        write_if_missing(requirement_dir / "requirement.md", ...)   # 落 artifacts/v1.0.0/...
        (requirement_dir / "changes").mkdir(parents=True, exist_ok=True)
```

**关键常量**（`workflow_helpers.py:84-86`）：
```python
FLAT_LAYOUT_FROM_REQ_ID = 39    # req-39 起 state-flat
FLOW_LAYOUT_FROM_REQ_ID = 41    # req-41 起 flow layout
```

`_next_req_id(root)`（`workflow_helpers.py:4130`）扫描以下目录取 `max_num + 1`：
1. `.workflow/state/requirements/`
2. `.workflow/flow/requirements/`
3. `resolve_requirement_root(root)` → `artifacts/v1.0.0/requirements/`
4. `artifacts/v1.0.0/archive/requirements/`（不存在）
5. `.workflow/flow/archive/main/`（不存在）

**关键**：扫描路径完全以**当前 git branch (`v1.0.0`)** 为前缀。PetMallPlatform 历史 req 都归档在 `artifacts/member/archive/...` / `artifacts/app_interface/archive/...`，不在扫描覆盖面内 → `max_num = 0` → 返回 `req-01`。

## 根因分析

### L1 表象

`harness requirement` 落地的机器型 `requirement.md` / `session-memory.md` 在 `artifacts/v1.0.0/...`，违反 `repository-layout.md` 契约（contract）。

### L2 中层

`create_requirement` 源码用 `_use_flow_layout(req_id)` / `_use_flat_layout(req_id)` 三段式分支（数字阈值 41 / 39 / else）决定机器型路径，分支判据**只看 req-id 数字大小**，**不看仓库实质语境**（是不是下游 fresh-install 仓 / 是不是新 branch 起步 / `.workflow/flow/` 是否已被使用）。

`_next_req_id` 给下游 fresh repo（或新 branch 视角下扫不到归档的仓）返回的 req-id 数字必然 ≤ 当前归档 max + 1，对全新启用场景而言就是 `req-01..NN`，**100% 落入 legacy 分支**。

### L3 一句根本

**契约（repository-layout req-41+ 新规）已迁移、CLI 路径选择策略仍按 harness-workflow 自身仓 timeline 分水岭**——三段式分水岭 (`req-id < 39 → legacy artifacts / 39..40 → state-flat / ≥ 41 → flow`) 隐含假设 "req-id 在 harness-workflow 自身仓全局递增"，对**任何下游用户仓**（无论 fresh 还是切新 branch）都不成立，导致 100% 命中 legacy 分支误落 artifacts。

### 候选假设逐条验证

- **H1（命中）**：harness CLI 部署版仍按老路径写——**实证为真**，但更准确表述是 "CLI 按 req-id 数字阈值走三段式，下游用户仓 req-id 必然 < 39 → legacy"，本质是设计层假设错位，不是"CLI 没切到新位"。
- **H2（部分命中）**：v1.0.0 是仓库的 git branch（被 `_get_git_branch` 解析），不在 `platforms.yaml` 注册——属实，但 `platforms.yaml` 与 `_get_git_branch` 解耦（`platforms.yaml` 用于 mirror scaffold 平台清单，git branch 走 git 命令独立解析），`platforms.yaml` 没注册 v1.0.0 **不是误放路径的根因**，是另一个独立小问题（`platforms.yaml` 与 `_get_git_branch` 是否要打通由 sug 入池）。
- **H3（排除）**：用户 / 某个 agent 手放——`action-log.md` 显示是 `harness requirement` 命令所为，文件 mtime（17:32 ~ 17:45）与 CLI 调用时刻吻合，无人为复制痕迹。
- **H4（部分命中）**：仓库**不是从 0 起**——确实有历史 req（在其他 branch 归档），但**根因不是迁移遗留**——而是 `_next_req_id` 扫描以当前 branch (`v1.0.0`) 为前缀，扫不到其他 branch 归档，所以视角内仍是"全新空仓"。这放大了 H1 的根因影响面（不仅 fresh repo，"切新 branch 起步" 也触发）。

### 影响范围

- **不仅 PetMallPlatform 单仓——所有用 harness 的下游项目都中招**：
  - **场景 A（绝对 100% 复发）**：任何全新启用 harness 的仓（`harness install` 后第一次 `harness requirement`），分配的 req-id 必然 ≤ 历史 max + 1，对 fresh 仓即 `req-01..10` 数量级，全部 < 39，必落 legacy artifacts 路径。
  - **场景 B（高频复发）**：用户切新 git branch 起步开发（如本次 PetMallPlatform 从 `member` 切 `v1.0.0`），`_next_req_id` 扫不到其他 branch 归档，视角内 "max = 0"，分配 `req-01`，触发同根因。
  - **场景 C（顺带病）**：与历史归档 req-id 重号——切 branch 起步时 req-01 重号，破坏全局 req-id 单调性，影响 reviewer / 跨需求引用 / sug 关联。这是同根因的另一面。
- **harness-workflow 自身仓不受影响**：自身仓内 req-id 全局递增到 50+，新 req 自然走 flow layout。
- **bugfix-11 在 harness-workflow 仓修源码 + 契约即可全量解决**，无需用户在 PetMallPlatform 侧做迁移（除非用户主动选择回填）。

## 结论

- [x] **真实问题**（confirmed real issue）
- [ ] 误判

## 路由决定

- **路由建议**：`confirm` → executing 写源码修复（在 harness-workflow 仓改 `src/harness_workflow/workflow_helpers.py::create_requirement` + 同源 `create_change` / `create_regression` 路径选择逻辑、补 `tests/`、按需扩展 `repository-layout.md` §4）。
- **问题类型**：实现层根因（设计假设与下游场景失配）兼契约层补充（repository-layout.md §4 是否需要"下游 fresh repo 直走 flow layout"显式条款）。
- **目标阶段**：bugfix 模式 → executing。
- **`harness regression --confirm`** 后由 harness-manager 在 bugfix 流程下推进 executing。

## 需要人工提供的信息

- 详见 `regression/required-inputs.md`。
- **核心 4 条**：
  1. 是否同意 fix 方向 A（`create_requirement` 加 `_is_fresh_downstream_repo` helper 优先走 flow layout）？或选 B/C？
  2. PetMallPlatform 现场误放的 req-01 文档要不要 manual fix（手工 mv 到 `.workflow/flow/requirements/`）？还是保留原状视为活体证据 + 用户后续自行处置？
  3. `_next_req_id` 跨 branch 扫归档（修复"重号风险"）是否纳入本 bugfix-11 修复面？还是另起 sug？（**default-pick = 另起 sug**：本 bugfix 范围聚焦"误放路径"，"重号"是同源连带，但展开会扩范围）。
  4. 用户是否还在过去几天内在其他下游仓（除 PetMallPlatform）执行过 `harness requirement`？需用户回忆，决定是否要在 sug 入池一条 "已落档下游仓批量自检 runbook"。

## 测试用例设计

> regression_scope: targeted
> 波及接口清单（手工分析 + 设计候选）：
> - `src/harness_workflow/workflow_helpers.py::create_requirement`（核心修复点）
> - `src/harness_workflow/workflow_helpers.py::_use_flow_layout` / `_use_flat_layout`（判定函数，可能需新增 `_is_fresh_downstream_repo` helper）
> - `src/harness_workflow/workflow_helpers.py::_next_req_id`（连带：是否扩展 cross-branch 归档扫描）
> - `src/harness_workflow/workflow_helpers.py::create_change`（同源：chg 在 fresh repo 也面临同样路径选择问题）
> - `src/harness_workflow/workflow_helpers.py::create_regression`（同源：reg 同样问题）
> - `tests/test_create_requirement_layout.py`（既有，新增 fresh-repo 用例）
> - `.workflow/flow/repository-layout.md` §4（候选契约面调整）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | 临时 fresh repo（git init + harness install），执行 `harness requirement "test-fresh"` | `requirement.md` 落 `.workflow/flow/requirements/req-01-test-fresh/`；`artifacts/main/requirements/req-01-test-fresh/` 仅占位（无 requirement.md / session-memory.md / changes/ 子目录） | VC-01 | P0 |
| TC-02 | 同 TC-01 但执行后立即 `harness change "test-chg"` | `change.md` / `plan.md` 落 `.workflow/flow/requirements/req-01-test-fresh/changes/chg-01-test-chg/` | VC-01 | P0 |
| TC-03 | 同 TC-01 但触发 `harness regression "test-reg"` | `regression.md` / 文件落 `.workflow/flow/requirements/req-01-test-fresh/regressions/reg-01-test-reg/` | VC-01 | P0 |
| TC-04 | 已存在 req-39 / req-40 / req-41 + 三段式分水岭归档的 harness-workflow 自身仓，执行 `harness requirement "dogfood-self-{ts}"` | 新 req-id 自动 ≥ 51（max+1），走 flow layout；既有 req-02..40 历史路径**不动** | VC-04 | P0 |
| TC-05 | git 切到新 branch（如 `release-1.0`）后，在 PetMallPlatform 类型仓（已有其他 branch 历史 req 归档）执行 `harness requirement "test-newbranch"` | 路径选择策略不依赖 branch 视角下 `_next_req_id` 数字，机器型仍落 `.workflow/flow/requirements/`；保留 `_next_req_id` 是否跨 branch 扫归档作为 OQ-3 决策 | VC-01 + OQ-3 | P0 |
| TC-06 | `pytest tests/test_create_requirement_layout.py -v` | 全部既有用例 PASS（无回归） | VC-02 | P0 |
| TC-07 | `pytest tests/ -v` | 全 suite PASS | VC-02 | P0 |
| TC-08 | `harness validate --contract repository-layout` 在 TC-01 修复后场景跑 | 0 violation | VC-03 | P0 |
| TC-09 | dogfood：`harness requirement "dogfood-bugfix-11-{ts}"` 在 harness-workflow 自身仓，确认本次修复**不破坏自身仓行为** | runtime.yaml 工作流可正常推进；req 落 flow/requirements/ | VC-04 | P0 |
| TC-10 | （可选 / 选 B 时）`harness requirement --layout-mode flow "explicit-flow"` 在任意仓 | 强制走 flow layout，绕过自动判定 | VC-01（B 方向） | P1 |
| TC-11 | （边界）调用方传 `requirement_id="req-99"` 但仓库非 fresh，验证 `_use_flow_layout("req-99") = True` 不被新增 helper 误改返回 False | True 不变 | VC-02 | P1 |
| TC-12 | （边界）调用方传 `requirement_id="req-05"` 在 fresh repo（手工指定 id），验证 `_is_fresh_downstream_repo` helper 命中后仍走 flow layout（fresh 信号优先于 req-id 数字阈值） | 走 flow layout | VC-01 | P1 |

`harness validate --contract test-case-design-completeness` 应在 testing/executing 进入前跑通。

## 待处理捕获问题（职责外，由主 agent 决策入 sug 池）

1. **重号风险（连带）**：`_next_req_id` 仅扫当前 branch 视角的 archive 路径，跨 branch 起步时 req-id 重号。建议入 sug 池（default-pick = OQ-3 另起 sug）。
2. **`platforms.yaml` 与 `_get_git_branch` 关系**：`platforms.yaml` 列的是 mirror 平台清单，`_get_git_branch` 走 git 命令解析仓库 branch，二者完全解耦——但用户体感会混淆"v1.0.0 是不是 platform"。建议在 `harness install` / `harness status` 透出说明，或入 sug 池。
3. **PetMallPlatform 现场回填**：是否提供 `harness migrate downstream-fresh-repo` 命令一键把已落 artifacts/ 的机器型文档迁回 `.workflow/flow/`？建议入 sug 池作为修复后的可选 follow-up（不阻塞本 bugfix）。
