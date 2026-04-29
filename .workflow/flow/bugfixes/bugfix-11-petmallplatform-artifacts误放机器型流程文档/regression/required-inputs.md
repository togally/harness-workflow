# Regression Required Inputs

When compilation fails, startup fails, or user-supplied data is required before the investigation can continue, the AI must fill out this file first and only then ask the human to complete it.
If startup logs, compile output, test failures, or stack traces are already available locally, the AI should collect and analyze them first instead of asking the human for those local artifacts.

## 1. Current Problem

- **Issue summary**：`harness requirement` 在下游用户仓（PetMallPlatform，git branch=v1.0.0）落机器型 `requirement.md` / `session-memory.md` / 空 `changes/` 子目录到 `artifacts/v1.0.0/requirements/req-01-梳理历史脚本统一使用liquibase管理/`，违反 `repository-layout.md` §1 / §3 契约。根因 = CLI `create_requirement` 三段式分水岭（数字阈值 `req-id < 39 / 39..40 / ≥ 41`）对下游 fresh repo 100% 命中 legacy 分支。
- **Related regression**：bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）regression stage 本身。
- **Linked change**：尚未拆分 chg（bugfix 流程不走 chg 拆分；executing 阶段直接按 diagnosis.md §Fix Plan 实施，参见 `regression/diagnosis.md` §测试用例设计）。

## 2. Required Human Inputs

| Item | Required | Notes |
| --- | --- | --- |
| **Q1：fix 方向选择** | **yes** | diagnosis.md §Fix Plan 给了 A / B / C 三方向，default-pick = A（`_is_fresh_downstream_repo` helper 优先走 flow layout）。请用户确认 A，或选 B（新增 `--layout-mode` flag）/ C（废弃三段式分水岭）。 |
| **Q2：PetMallPlatform 现场处置** | **yes** | 现 `artifacts/v1.0.0/requirements/req-01-.../requirement.md` (10891B) + `session-memory.md` (10067B) + 空 `changes/` 已落地。修源码后 PetMallPlatform 这次的 req-01 文档是否要 manual fix 移到 `.workflow/flow/`？还是保留原状（视为活体 bug 证据）由用户后续手工处理？default-pick = 保留原状不动（bugfix-11 范围聚焦"修源码不让再发生"，PetMallPlatform 单仓回填属用户决策）。 |
| **Q3：重号风险纳入面** | **no（default-pick = 否，另起 sug）** | `_next_req_id` 跨 branch 不扫归档导致重号风险，是同根因连带问题。default-pick = 不纳入本 bugfix-11 范围（避免 scope 二次扩展），由 done 阶段或主 agent 转入 sug 池。如用户要求一并修，bugfix-11 改 chg 拆分（不推荐）。 |
| **Q4：其他下游仓自检面** | **maybe** | 用户是否在过去几天对 PetMallPlatform 之外的其他仓（含已归档历史仓）执行过 `harness requirement` 创建新 req？决定是否要在 sug 池追加"已落档下游仓批量自检 runbook"。default-pick = 由用户回忆后告知，本 bugfix 不强求。 |
| Configuration | no | 不需要 env vars / config / secrets。 |
| Test data | no | 用 tmp dir 模拟 fresh repo 即可；参考 diagnosis.md §测试用例设计 TC-01..12。 |
| Account details | no | 无外部账号需求。 |
| External dependency details | no | 无第三方依赖。 |

## 3. Human Response Section

- **Q1 fix 方向**：**方向 C（废弃三段式分水岭 + 删历史豁免）**。
  - 用户原话：「不需要豁免历史不符合要求直接删除」+「不要动非本仓库内容」。
  - 落地范围（仅 harness-workflow 自身仓）：
    - **源码层**：删 `src/harness_workflow/workflow_helpers.py::_use_flow_layout` / `_use_flat_layout` / `FLAT_LAYOUT_FROM_REQ_ID` / `FLOW_LAYOUT_FROM_REQ_ID` 常量；`create_requirement` / `create_change` / `create_regression` 三段式分支砍干净，全部一律走 `.workflow/flow/requirements/{req-id}-{slug}/...` flow layout（无 fallback 分支）。
    - **契约层**：`.workflow/flow/repository-layout.md` §4「历史存量豁免与三段式分水岭」整段删除；同步清理本文件其余处对「三段式 / req-39/40 fallback / req-02 ~ req-40 豁免」的引用。
    - **存量清理 B2**：删除 `artifacts/main/regressions/reg-{01..05}/` 下机器型残留（5 目录 / 含 session-memory.md 等），机器型权威路径迁到 `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/`（若对应 req-id 已归档则迁到 `.workflow/flow/archive/main/`）。
    - **存量清理 B3**：删除 `artifacts/main/archive/bugfixes/bugfix-{1,2,3,4,6}/` 下机器型残留（session-memory.md / change.md / plan.md / change_review.md 等），bugfix 机器型权威路径走 `.workflow/flow/bugfixes/{bugfix-id}-{slug}/`（已归档的迁 `.workflow/flow/archive/main/`），artifacts/.../bugfixes/{slug}/ 仅保留对人产物（README / 交付总结.md 等）。
    - **scaffold_v2 mirror**：所有上述源码 / 契约改动同步 `src/harness_workflow/assets/scaffold_v2/.workflow/...` 镜像（硬门禁五）。
- **Q2 PetMallPlatform 现场处置**：**不动**（用户原话「不要动非本仓库内容」；跨仓操作不在 bugfix-11 范围；用户后续如需自行迁移可手工 mv 或等 sug 池里的「下游仓自检 runbook」）。
- **Q3 重号风险（_next_req_id 跨 branch 扫归档）**：**否，另起 sug**（default-pick）。修源码 fix 方向 C 后下游仓 req-id 仍从 1 起、与其他 branch 视角下归档可能重号——这是同根因连带问题，归 sug 池由 done 阶段或主 agent 入池。
- **Q4 其他下游仓自检**：**待用户回忆告知**（default-pick）；如需要批量自检 runbook，由 done 阶段建议或独立 sug 池入池。
- Configuration：N/A
- Test data：N/A
- Account details：N/A
- External dependency details：N/A

### 范围红线（用户明确）

- **不得修改 PetMallPlatform 任何文件**（含 `artifacts/v1.0.0/requirements/req-01-.../` 内所有内容、`.workflow/state/` 内所有内容）；bugfix-11 全部改动落 `/Users/jiazhiwei/claudeProject/workspace/harness-workflow/` 仓内。
- **不再保留任何"req-id < 41 兼容分支"**；executing 拒绝任何形如 `if req_id < 41` / `if FLAT_LAYOUT_FROM_REQ_ID` / `legacy fallback` 的回填代码（diagnosis.md §测试用例设计 TC-04 / TC-09 / TC-11 用作回归底盘 + 反例验证）。

## 4. Next Step

- 用户回填 Q1~Q4 后，主 agent / harness-manager 调 `harness regression --confirm` 推进至 executing。
- executing subagent 读取本 `required-inputs.md` 与 `regression/diagnosis.md` §Fix Plan / §测试用例设计，按用户回填的方向产出 plan 与代码改动。
- 若用户 Q1 不选 A（选 B / C），executing 在 plan.md 记录新方向、重写测试用例覆盖面，再实施。
