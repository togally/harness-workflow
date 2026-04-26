---
id: bugfix-5
title: 同角色跨 stage 自动续跑硬门禁
created_at: 2026-04-25
---

# 问题描述

**一句话总结**：契约层（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））规定"同一角色覆盖的相邻 stage 之间默认静默自动连跑、不暴露'是否进 {下一 stage}'决策点"，但实现层（stages.md / workflow_helpers.py / harness validate）无任何代码 / lint 强制，主 agent 在 `requirement_review → planning` 流转点仍向用户暴露决策点，违反契约。

**根因**：角色→stage 的"覆盖关系"无单一权威源，三处文档分散记录，CLI 无法读、reviewer 无法 lint。

**详见**：`regression/diagnosis.md`（含三处契约原文行号 + 三处实现层缺失证据）。

**用户方向硬约束**：规则必须**通用化**——不是 `requirement_review → planning` 单一特例，而是"任何同一角色覆盖的所有 stage，中间全部自动跑，不让用户在中间停。用户只在角色边界看一次"；stage 与 role 是多对多关系，权威源应挂在 role 侧。

# 根因分析

详见 `regression/diagnosis.md` §三、根因（L1 表象 + L2 中层 + 一句根本）。

# 修复范围

**涉及文件**：

- 单一权威源：`.workflow/context/role-model-map.yaml`（schema 扩展）。
- CLI 实现：`src/harness_workflow/workflow_helpers.py`（`workflow_next` 自动连跳逻辑 + helper）、`src/harness_workflow/cli.py`（`harness validate` 子命令扩规则）。
- 文档同步（三处镜像）：`.workflow/context/index.md`、`.workflow/flow/stages.md`、各 role md（analyst.md / executing.md / regression.md 等所有覆盖 stage 的角色文件）。
- scaffold_v2 mirror 同步：`src/harness_workflow/assets/scaffold_v2/.workflow/context/`、`.../flow/`（与 `.workflow/` 子树双写）。

**显式 out-of-scope**：

- **不动 stage 业务定义本身**（stages.md 各 stage 的进入条件 / 退出条件 / 必须产出维持原文，仅加"覆盖角色"反向引用块）。
- **不改 role 业务行为**（analyst.md / executing.md 等角色 SOP 段维持原文，仅在"角色定义"段补一行"覆盖 stage：[...]"）。
- **不动 stage 流转图**（`.workflow/flow/stages.md` 的箭头流转图维持原文）。
- **不重复 req-40 已落地的 analyst 角色合并**（req-40 已合并 requirement-review + planning → analyst，本 bugfix 仅补"自动连跳"代码门禁，不重新拆角色）。

# 修复方案

按"**角色→stage 单一权威源 + 三处吃这一份**"组织，5 个修复点闭环。

**acceptance 后 scope 扩展（追加修复点 6）**：原 5 修复点仅覆盖"同角色"特例（充分非必要条件）；用户在 acceptance 后指出"acceptance→done 这一步应该也是自动的"，触发根因再深化（详见 `regression/diagnosis.md §根因再深化`）—— 真根因是"**任何无用户决策点的 stage 转换都没有代码强制**"。**追加修复点 6（verdict-driven 自动跳）**，把同角色 while 循环扩展为"无用户决策点 while 循环"，覆盖 acceptance / regression 等 verdict-driven 路由，6 修复点闭环。

## 修复点 1：单一权威源（schema 扩展）

扩 `.workflow/context/role-model-map.yaml`，给每个 role 加 `stages: [stage_name, ...]` 字段。**default-pick D-1 = A**：选"扩 yaml 内嵌 stages"而非"新建 role-stage-map.yaml"，理由：紧凑、迁移成本最小、与现有 yaml 加载链路（`load_role_model_map` 等 helper）一次性吃到 stages。

**新 schema（示例）**：

```yaml
version: 2  # 从 1 升 2，触发 helper 兼容分支
default: "sonnet"

roles:
  # ---- 开放型 ----
  harness-manager:
    model: "opus"
    stages: []                                 # 辅助角色，不覆盖 business stage
  analyst:
    model: "opus"
    stages: ["requirement_review", "planning"] # req-40 角色合并落地
  regression:
    model: "opus"
    stages: ["regression"]
  done:
    model: "opus"
    stages: ["done"]
  technical-director:
    model: "opus"
    stages: []                                 # Director，跨 stage 编排不绑定具体 stage
  project-reporter:
    model: "opus"
    stages: []                                 # 辅助角色

  # ---- 执行型 ----
  executing:
    model: "sonnet"
    stages: ["executing"]
  testing:
    model: "sonnet"
    stages: ["testing"]
  acceptance:
    model: "sonnet"
    stages: ["acceptance"]
  tools-manager:
    model: "sonnet"
    stages: []                                 # 辅助角色
  reviewer:
    model: "sonnet"
    stages: []                                 # 辅助角色

  # ---- legacy alias（req-40 兼容历史归档）----
  requirement-review:
    model: "opus"
    stages: ["requirement_review"]             # alias，遇到旧调用回落 analyst
    alias_of: "analyst"
  planning:
    model: "opus"
    stages: ["planning"]
    alias_of: "analyst"
```

**向后兼容层**（必备，不能直接破坏 v1）：

- 加载 helper（如 `load_role_model_map`）识别 `version: 1` 简写形式（`roles.{role}: "model_name"`）→ 视为 `{model: ..., stages: [legacy_default_for_role]}`，其中 `legacy_default_for_role` 按当前 role 名直查 stage（与 role 同名的 stage，未命中给空数组）；
- `version: 2` 走新 schema 直读；
- 写入端（如未来若 `harness install` 需要刷新 yaml）一律按 v2 写出。

**变更行为锚点**：本修复点 = 单一权威源建立，后续 4 个修复点都从此读。

## 修复点 2：CLI 自动连跳（workflow_next 逻辑）

改 `src/harness_workflow/workflow_helpers.py` `workflow_next()`（行 6800-6895）：从权威 yaml 读"当前 stage 的角色"，若下一 stage 同角色，**自动连跳**直到角色边界（即 `next_role ≠ current_role`），单次 `harness next` 内一次性翻完。

**新增 helper**（放在 `workflow_helpers.py` 现有 `load_role_model_map` 附近）：

```python
def _get_role_for_stage(stage: str, role_stage_map: dict) -> str | None:
    """反查 stage 对应的 role；命中多个返回 'analyst' 等非 alias 主角色，alias 角色降级。

    fallback：未命中（如 ready_for_execution 这类无角色直接覆盖的桥接 stage）→ 返回 None，
    workflow_next 视为"角色边界"，正常逐格翻。
    """
    candidates = [
        role_name
        for role_name, role_def in role_stage_map.get("roles", {}).items()
        if stage in role_def.get("stages", [])
        and not role_def.get("alias_of")  # 跳过 legacy alias
    ]
    return candidates[0] if candidates else None
```

**`workflow_next` 主循环改造**（在行 6849 `next_stage = sequence[idx + 1]` 之后插入连跳逻辑）：

```python
# 单一权威源驱动的同角色跨 stage 自动连跳（bugfix-5（同角色跨 stage 自动续跑硬门禁））
role_stage_map = load_role_model_map(root)  # 已存在的 helper，bugfix-5 仅扩其消费方
current_role = _get_role_for_stage(current_stage, role_stage_map)
if current_role is not None and routed_stage_from_reg is None:
    # reg 路由命中场景不参与连跳（路由本身就是跨角色边界跳转）
    while idx + 1 < len(sequence):
        candidate_stage = sequence[idx + 1]
        candidate_role = _get_role_for_stage(candidate_stage, role_stage_map)
        if candidate_role != current_role:
            break  # 角色边界，停在 candidate_stage
        # 同角色，吃掉这一格
        idx += 1
        next_stage = candidate_stage
        # 每跳一格都补：stage_entered_at 时间戳更新 + state yaml 双写 + record_feedback_event
        # 不能批量记一条覆盖中间格，否则 done 阶段六层回顾 stage_timestamps 数据丢失
        _emit_intermediate_stage_advance(
            root, runtime, operation_type, operation_target,
            from_stage=current_stage, to_stage=next_stage,
        )
        current_stage = next_stage
```

**关键不变量（必须遵守）**：

- 每跳一格都写 `stage_entered_at`、同步 state yaml（调 `_sync_stage_to_state_yaml`）、`record_feedback_event(stage_advance / stage_duration)`；**不**批量合并记一条覆盖中间格（否则 done 阶段六层回顾 stage_timestamps 数据丢失）；
- 连跳过程中不调 `extract_suggestions_from_done_report`（仅终态 next_stage == done 时调，逻辑维持现状）；
- reg 路由命中（`routed_stage_from_reg is not None`）时**不参与连跳**——路由本就是跨角色边界跳转，连跳会与路由语义冲突；
- `ready_for_execution` 这类无角色直接覆盖的桥接 stage，`_get_role_for_stage` 返回 None，被视为"角色边界"，自动停止连跳（与 `--execute` flag 现有语义一致）。

## 修复点 3：话术 lint（harness validate 扩规则）

扩 `src/harness_workflow/cli.py` `harness validate` 子命令，加 `--contract role-stage-continuity` 规则：

**实现位置**：`src/harness_workflow/cli.py` 现有 `harness validate` 子命令分支（参考既有 `--contract all` / `--contract regression` 的实现风格）。

**规则逻辑**：

1. 读 `.workflow/state/runtime.yaml` 取当前 stage、当前角色（通过 `_get_role_for_stage`）；
2. 取当前 session-memory.md（`.workflow/flow/{requirements|bugfixes}/{id}/session-memory.md`）+ 最近一次 batched-report 输出（如 action-log.md 末段）作为 lint 输入文本；
3. 正则匹配：`r"是否进(入|到)?\s*(planning|executing|testing|acceptance|done|requirement_review|regression)"`；
4. **判定**：命中且匹配的目标 stage_name 与 current_stage 同一角色（`_get_role_for_stage(target_stage) == _get_role_for_stage(current_stage)`）→ FAIL，stdout 打印命中行 + 行号 + 违反契约引用（stage-role.md:39 / technical-director.md:165 / harness-manager.md:342）；
5. 命中但跨角色边界 → PASS（合规决策点，本就该向用户拍板）。

**调用入口**：

- `harness validate --contract role-stage-continuity`：单契约调用；
- `harness validate --contract all`：聚合契约组里追加一项 `role-stage-continuity`；
- reviewer 角色 checklist（`.workflow/context/roles/reviewer.md`）的 SOP "执行" 段加一条 "执行 `harness validate --contract role-stage-continuity` 得绿"。

**自检 false positive 防御**：

- 正则只匹配中文"是否进入 / 是否进 / 是否进到"，不匹配英文 "Is it ready to enter ..." / "ready for ..."（避免误伤外部产出）；
- 若 session-memory.md 含 markdown 引用块（`> ` 行）原样引用历史话术（如本 diagnosis.md 自身），允许 `<!-- lint:ignore role-stage-continuity -->` 行内豁免标记，避免 lint 自反。

## 修复点 4：三处文档镜像同步

权威源是修复点 1 的 yaml，文档侧三处只做"镜像 + 反向引用"，均标注"以 role-model-map.yaml 为准"：

**4a. `.workflow/context/index.md` 角色索引表**：

- 在"Stage 执行角色"表中加一列 `stages`，镜像 yaml；
- 表头下方加一行 footnote：`> stages 列以 .workflow/context/role-model-map.yaml 为准；本表为镜像展示，冲突以 yaml 为准。`

**4b. `.workflow/flow/stages.md` 各 stage 定义**：

- 在每个 stage 定义块（如 `### requirement_review`）现有 "**角色**" 行之后加一行 `**覆盖角色**`：从 yaml 反向查询（如 `requirement_review` → `analyst`）；
- 文件头部 footnote：`> 本文件 stage 与角色对应关系以 .workflow/context/role-model-map.yaml 为准；本文件为反向引用展示。`

**4c. 各 role md 角色定义段**：

- 在 `analyst.md` / `executing.md` / `testing.md` / `acceptance.md` / `regression.md` / `done.md` 的 `## 角色定义` 段补一行：`覆盖 stage：[stage1, stage2, ...]`（从 yaml 镜像）；
- 同段末加 footnote：`> 覆盖 stage 列表以 .workflow/context/role-model-map.yaml 为准。`

**4d. reviewer checklist 加 lint 项**：

- `.workflow/context/roles/reviewer.md` checklist 段加一条："三处镜像（index.md 角色表 stages 列 / stages.md 覆盖角色行 / role md 覆盖 stage 行）与 role-model-map.yaml 一致" → 触发 reviewer 用 `diff` / 手工核对。

## 修复点 5：scaffold_v2 mirror 同步（硬门禁）

按 `.workflow/context/roles/harness-manager.md` 既有"硬门禁五（scaffold_v2 mirror 双写）"约定，所有 `.workflow/context/` 与 `.workflow/flow/` 的改动必须**同 commit** 同步到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/` 与 `.../flow/` 子树，否则 reviewer / done 阶段 FAIL。

**同步清单**：

- `src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml`（修复点 1 schema 升级）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md`（修复点 4a 镜像列）
- `src/harness_workflow/assets/scaffold_v2/.workflow/flow/stages.md`（修复点 4b 反向引用）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/{analyst,executing,testing,acceptance,regression,done,reviewer}.md`（修复点 4c + 4d）

**自检命令**（executing 阶段实现完后必跑）：

```bash
diff -rq .workflow/context/ src/harness_workflow/assets/scaffold_v2/.workflow/context/
diff -rq .workflow/flow/ src/harness_workflow/assets/scaffold_v2/.workflow/flow/
# 期望：仅 stage / suggestions 等运行态文件 differ；context + role md + role-model-map.yaml + stages.md 全 identical
```

## 修复点 6：verdict-driven 自动跳（scope 扩展，acceptance 后追加）

> **追加触发**：acceptance PASS-with-followup 后用户原话"acceptance→done这一步应该也是自动的吧"，详见 `regression/diagnosis.md §根因再深化（acceptance 后 scope 扩展）`。
> **核心思路**：把修复点 2 的"**同角色** while 循环"扩展为"**没有用户决策点** while 循环"——同角色是用户决策点边界的**充分非必要**条件，真正应建模的是 stage 出口的**决策类型**。

### 6.1 数据建模：stage_policies 字段

在 `.workflow/context/role-model-map.yaml` 顶层增加 `stage_policies` 字段，声明每个 stage 的"出口决策类型"。**default-pick D-7 = A**：选"内嵌同 yaml 顶层字段"而非"拆出 stage-policy.yaml"，理由与修复点 1 D-1 一致——单一权威源 / 紧凑 / 一次加载 / 不增加文件。

**新增 schema**（追加在现有 `roles:` 字段之下，version 仍为 2）：

```yaml
# bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6 扩展：
# 声明每个 stage 的"出口决策类型"，驱动 workflow_next "无用户决策点" 自动连跳。
# exit_decision 取值（default-pick D-8 = A）：
#   user      —— 需要用户对内容拍板（如 planning → ready_for_execution 待用户拍板需求 + 拆分）
#   auto      —— 角色自决，无需用户介入（如 requirement_review → planning，analyst 自主推进）
#   explicit  —— 需 CLI 显式 flag（如 ready_for_execution → executing 需 --execute）
#   verdict   —— 路由由 verdict 字段（PASS / FAIL）已定，用户无新决策（如 acceptance → done / regression）
#   terminal  —— 终局，无下游（done）
stage_policies:
  requirement_review:
    exit_decision: auto      # analyst 自决推进到 planning
  planning:
    exit_decision: user      # 需用户对需求 + 拆分一次拍板
  ready_for_execution:
    exit_decision: explicit  # 需 harness next --execute 显式确认
  executing:
    exit_decision: auto      # executing 完成态自动转 testing（无显式 gate；testing 内部决定 verdict）
  testing:
    exit_decision: auto      # 见 default-pick D-6 = A：暂不按 verdict 自动跳，沿用既有"完成即转下一格"
  acceptance:
    exit_decision: verdict   # PASS → done / FAIL → regression，路由由 verdict 已定
  regression:
    exit_decision: verdict   # diagnosis.md 路由（confirm/reject）已定下一 stage
  done:
    exit_decision: terminal  # 终局
```

**bugfix sequence 补充**（与 BUGFIX_SEQUENCE / SUGGESTION_SEQUENCE 共用）：bugfix / suggestion 流程的 acceptance / testing / regression / done 共享上述策略，无需另立 stage_policies 子表。

### 6.2 CLI 行为：workflow_next 主体扩 while 条件

改 `src/harness_workflow/workflow_helpers.py` `workflow_next()`（行 6985 附近的同角色 while 循环）：

**新增 helper**（放在 `_get_role_for_stage` 附近）：

```python
def _get_exit_decision(stage: str, role_stage_yaml: dict) -> str:
    """从权威 yaml 读 stage 的 exit_decision。

    bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6：
    - 命中 stage_policies.{stage}.exit_decision → 直接返回。
    - 未命中（yaml 未声明 / 桥接 stage 如 ready_for_execution 缺字段）→ 默认返回 'user'，
      保守起见把未知 stage 视为"需用户拍板"，避免误自动跳。
    """
    policies = role_stage_yaml.get("stage_policies", {})
    if not isinstance(policies, dict):
        return "user"
    stage_policy = policies.get(stage, {})
    if not isinstance(stage_policy, dict):
        return "user"
    return str(stage_policy.get("exit_decision", "user"))
```

**`workflow_next` while 主体改造**（在修复点 2 的同角色 while 之后，扩展条件）：

```python
# bugfix-5 修复点 6：verdict-driven / auto-driven 连跳（scope 扩展）
# 原 while 仅"同角色" → 扩为"同角色 OR exit_decision in {auto, verdict, terminal_routed}"
# routed_stage_from_reg 命中场景仍不参与（路由本就是跨边界跳转）
# explicit / user 类型出口必须停下，保留显式 gate
AUTO_JUMP_DECISIONS = {"auto", "verdict"}  # terminal 单独处理（done 终局，无下游）

while walk_idx >= 0 and walk_idx + 1 < len(sequence):
    candidate = sequence[walk_idx + 1]
    candidate_role = _get_role_for_stage(candidate, role_stage_map)
    current_exit = _get_exit_decision(from_s, role_stage_yaml_raw)

    same_role = (candidate_role == current_role_for_advance and current_role_for_advance is not None)
    no_user_decision = current_exit in AUTO_JUMP_DECISIONS

    if not (same_role or no_user_decision):
        break  # 用户决策点 / 显式 gate / 终局 → 停下

    _write_stage_transition(from_s, candidate, prev_iso)
    from_s = candidate
    prev_iso = str(runtime.get("stage_entered_at", ""))
    walk_idx += 1
    next_stage = candidate
```

**关键不变量（与修复点 2 不变量并列生效，必须遵守）**：

- 每跳一格仍写 `stage_entered_at` + state yaml + `record_feedback_event(stage_advance / stage_duration)`，**不**批量合并；
- `exit_decision = explicit`（如 `ready_for_execution`）→ 沿用现有 `--execute` flag 检查路径，**不**自动跳过；
- `exit_decision = user`（如 `planning`）→ 停下等用户拍板，**不**自动跳；
- `exit_decision = terminal`（done）→ 已由 `current_stage == "done": SystemExit("Workflow is already complete.")` 拦截，无需额外处理；
- `exit_decision = verdict` 触发自动跳时，verdict 字段读取来源（**default-pick D-9 = A**）：优先 acceptance-report.md / regression/diagnosis.md frontmatter `verdict: PASS|FAIL` 字段；fallback 到正则匹配文件正文 `## 结论` / `## 验收结论` 段的 `PASS / FAIL` 关键词；两路均未命中 → 视为 verdict 未拍板，停下等待人工补字段（不强制自动跳）。
- reg 路由命中（`routed_stage_from_reg is not None`）仍优先于 verdict-driven，逻辑不变。

### 6.3 影响文件清单

- `.workflow/context/role-model-map.yaml`：顶层加 `stage_policies` 字段（修复点 6.1）；
- `src/harness_workflow/workflow_helpers.py`：新增 `_get_exit_decision` helper + `workflow_next` while 主体扩条件（修复点 6.2）；
- `src/harness_workflow/cli.py`：`harness validate --contract role-stage-continuity`（修复点 3）lint 规则**扩展判定**——"是否进入 {下一 stage}" 形式在 `exit_decision != user` 的 stage 出口处也要 FAIL（不只同角色边界），共享 `_get_exit_decision`；
- 三处文档镜像（修复点 4）：
  - `.workflow/context/index.md`：角色索引表下方追加一段简短说明 `> stage_policies 见 .workflow/context/role-model-map.yaml 顶层字段，CLI 自动连跳 / harness validate lint 共享同一权威源`；
  - `.workflow/flow/stages.md`：每个 stage 定义块在"覆盖角色"行之后追加 `**出口决策**：{exit_decision_value}` 行（镜像 yaml 字段）；
  - 各 role md：在 SOP 退出 / 流转规则段视情况补一行说明（具体落点由 executing 决定，本 bugfix 不强约束行号）；
- `src/harness_workflow/assets/scaffold_v2/.workflow/`：所有 live 改动同 commit 同步到 mirror 子树（硬门禁五）；
- `.workflow/context/roles/reviewer.md` review-checklist：在原 `role-stage-continuity lint` 检查项之下加一条 "stage_policies 字段与 workflow_next while 行为一致性抽样"。

### 6.4 回滚方式

修复点 6 独立可回滚：

- 移除 yaml 中 `stage_policies` 顶层字段 → `_get_exit_decision` 默认全返 `user` → while 退化为只同角色连跳（修复点 2 行为）；
- 注释 while 主体 `no_user_decision` 分支即可彻底回退。

完整 bugfix-5 回滚仍按 §回滚方式 `git revert <bugfix-5 合并 commit>` 一次性回退所有 6 修复点。

# 验证清单（对应 testing 阶段）

| 用例 | 输入 | 预期输出 |
|------|------|----------|
| **A. 同角色连跳** | runtime.yaml stage = `requirement_review`，operation_type = `requirement`；跑 `harness next` | state 应**一次性**翻到 `planning`（或更远，若 analyst 在 yaml 中覆盖更多 stage）；stdout 打印两条 `Workflow advanced to ...`（每跳一格一条）；feedback-events 含两条 stage_advance 事件；stage_timestamps 含两个时间戳（不是只一个） |
| **B. 话术 lint 命中** | 写 mock session-memory.md 含 "是否进入 planning？" 行，runtime.yaml stage = `requirement_review`；跑 `harness validate --contract role-stage-continuity` | exit code = 1 (FAIL)；stdout 打印命中行号 + 文件路径 + 引用 stage-role.md:39 契约；同句若改"是否进入 testing"（跨角色边界）→ exit code = 0 (PASS) |
| **C. 动态映射生效（回退验证）** | role-model-map.yaml 把 analyst 的 `stages` 字段改为单 stage `["requirement_review"]`；跑 `harness next`（stage = requirement_review） | state 翻到 `planning` 后**停止连跳**（因为 planning 不再属于 analyst 覆盖范围）；证明逻辑读权威 yaml 而非硬编码 |
| **D. scaffold_v2 mirror 零 diff** | `diff -rq .workflow/context/ src/harness_workflow/assets/scaffold_v2/.workflow/context/`、`diff -rq .workflow/flow/ src/harness_workflow/assets/scaffold_v2/.workflow/flow/` | 输出仅运行态文件 differ；`role-model-map.yaml` / `index.md` / `stages.md` / 所有 role md 全 identical |
| **G. acceptance→done 自动跳（修复点 6 / verdict-driven）** | mock runtime.yaml stage = `acceptance`，operation_type = `bugfix`，构造 acceptance-report.md frontmatter `verdict: PASS`；跑 `workflow_next`（execute=False） | state 应**一次性**翻到 `done`（不停在 acceptance）；stdout 含 `Workflow advanced to done`；feedback-events 含 `stage_advance: acceptance → done`；state yaml `stage_timestamps` 含 `done` 字段（独立时间戳，不与 acceptance 合并） |
| **H. acceptance→regression 自动跳（修复点 6 / FAIL 路由）** | mock runtime.yaml stage = `acceptance`，acceptance-report.md frontmatter `verdict: FAIL`，构造 acceptance 决策落盘 `next_stage: regression`；跑 `workflow_next` | state 应翻到 `regression`（按 verdict 路由）；执行 verdict 抽样 grep 验证 `_get_exit_decision("acceptance", ...)` 返回 `verdict`；stdout 含 `Workflow advanced to regression` |
| **I. executing→testing 仍需 --execute（修复点 6 / explicit gate 保留）** | mock runtime.yaml stage = `executing`，无 `--execute` flag；跑 `workflow_next(execute=False)` | 行为按既有 `ready_for_execution` 显式 gate 路径不变；executing 出口若 yaml 标 `auto`（按 D-6 = A 默认），则可正常推 testing 一格，但**不**继续越过 testing 自动跳到 acceptance（testing exit_decision = auto + testing 完成态语义模糊，default-pick D-6 = A 不参与下游连跳）；构造对照：把 ready_for_execution 作为 current_stage 跑 `workflow_next(execute=False)`，应触发 `SystemExit("Workflow is ready_for_execution. Run \`harness next --execute\`...")` —— 显式 gate 保留 |

**附加验证**（非阻塞，建议）：

- 用例 E（向后兼容）：临时把 yaml 改回 v1 简写形式（`roles.{role}: "model_name"`），跑 `harness next`，应**回退到原"逐格翻"**行为，不抛错；证明 v1 兼容层有效。
- 用例 F（reg 路由不受影响）：构造 `current_regression` 非空 + `decision.md` 路由 → testing 场景，跑 `harness next`，应直接跳 testing，**不参与连跳**；证明 reg 路由优先级未被破坏。
- 用例 J（stage_policies 缺字段降级）：临时移除 yaml `stage_policies` 顶层字段，跑用例 G —— `_get_exit_decision` 默认返回 `user`，acceptance 出口被视为用户决策点，**不**自动跳到 done，停在 acceptance；证明缺字段降级语义安全（保守不误自动）。

# 回滚方式

每个修复点独立可回滚：

- 修复点 1（yaml schema）：保留 `version: 1` 兼容分支，把 yaml 回退到 v1 即可；
- 修复点 2（workflow_next 连跳）：把新 while 循环段注释掉即可，回退到行 6849 原始 `next_stage = sequence[idx + 1]` 行为；
- 修复点 3（harness validate 规则）：移除 `--contract role-stage-continuity` 分支即可；
- 修复点 4（文档镜像）：文档不影响运行时，git revert 即可；
- 修复点 5（scaffold mirror）：随 1-4 一同 revert。
- 修复点 6（verdict-driven 自动跳）：移除 yaml `stage_policies` 字段 + 注释 while 主体 `no_user_decision` 分支即可；详见 §修复点 6 §6.4。

**最坏情况**：`git revert <bugfix-5 合并 commit>` 整个 chg；**不需要数据迁移 / 状态文件清洗**（runtime.yaml schema 未变）。

# 后续 / 后置任务

- **req-43（交付总结完善）挂起**：本 bugfix-5 完成后，主 agent 应回到 req-43 的 `requirement_review → planning` 流转点，**直接验证连跳逻辑**：跑一次 `harness next` 应一次性翻到 planning（不应再出现"是否进 planning"决策点）；若验证通过，记一笔到 req-43 session-memory.md 作为 bugfix-5 的端到端自证。
- **suggest 池候选**（非本 bugfix 范围，登记到后续 sug）：若未来需要"角色覆盖 ≥ 3 stage"场景（如 testing+acceptance+done 由同一角色承载），本 bugfix 的 while 循环天然支持，无需再改代码；但 stages.md 流转图箭头需更新（视觉对应）。
- **经验沉淀**：`.workflow/context/experience/roles/regression.md` 追加一条"契约层 vs 实现层失配"诊断模板（看到 role md 写"默认静默"但 stages.md / workflow_helpers.py 无对应代码 = 必查根本根因）。
