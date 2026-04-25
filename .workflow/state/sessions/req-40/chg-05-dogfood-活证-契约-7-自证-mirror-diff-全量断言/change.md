# Change

## 1. Title

dogfood 活证 + 契约 7 自证 + mirror diff 全量断言

## 2. Goal

- 用 req-40 自己的后续运行过程作为方向 C 的首次活证（dogfood），即在 chg-01 ~ chg-04 全部落地后启动一次完整 analyst 路径（requirement → chg 拆分 → change + plan 全集），在 session-memory.md 留痕关键节点；同时跑契约 7 自检扫 req-40 scope 内所有 `.md` 文档 0 违规；并跑跨文件 mirror diff 全量断言归零，作为 req-40 落地的最终封存证据。

## 3. Requirement

- `req-40`（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

## 4. Scope

### Included

- **dogfood 活证**：
  - 在 chg-01 ~ chg-04 executing 全部落地后，模拟新 req（或以 req-40 executing 阶段的残余动作）跑一次 analyst 单角色双 stage 流程：analyst 在 requirement_review 产出 requirement 澄清 → harness next → analyst 同一会话续跑 planning 产 chg 拆分 + change.md + plan.md；
  - 可选路径 A：在 req-40 executing 阶段由 analyst 承接 chg-05 自身的剩余动作作为活证（最小闭环）；
  - 可选路径 B：新建一个演示性 req（不入归档）跑完整 analyst 一轮，产物只用于活证，不入产品；
  - default-pick DF-1 = A（最小闭环，不污染归档，req-40 自身执行足以验证）；
  - `.workflow/state/sessions/req-40/session-memory.md` 追加"dogfood 活证节点清单"：开始时间 / analyst 角色身份自报 / requirement_review PASS 时间 / planning 自动推进时间 / ready_for_execution 时间 / batched-report 样本引用。
- **契约 7 自证**：
  - 跑 `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" artifacts/main/requirements/req-40-*/ --include="*.md" -r` 扫所有命中行；
  - 人工 / 工具核对每个命中行紧随 `（...）` / `— ...` 描述 或 行内已有 title 字段；
  - 跑 `harness validate --contract 7`（若 CLI 可用）或等价 grep lint 脚本；
  - 期望：req-40 scope 内所有 `.md` 命中 0 违规（包含 chg-01~chg-06 的 change.md + plan.md + 各变更简报 + requirement.md + session-memory.md）；
- **mirror diff 全量断言**：
  - `diff -rq .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`
  - `diff -rq .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`
  - `diff -rq .workflow/context/roles/directors/technical-director.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/directors/technical-director.md`
  - `diff -rq .workflow/context/roles/stage-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`
  - `diff -rq .workflow/context/index.md src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md`
  - `diff -rq .workflow/context/role-model-map.yaml src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml`
  - `diff -rq .workflow/flow/stages.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/stages.md`（stages.md 不动，兜底断言）
  - 期望：全部无输出。
- 涉及文件路径：
  - 读取：req-40 scope 内所有 .md（`.workflow/state/sessions/req-40/` + `artifacts/main/requirements/req-40-.../`）
  - 写入：`.workflow/state/sessions/req-40/session-memory.md`（追加 dogfood 节点 + 自证报告）+ `artifacts/main/requirements/req-40-.../chg-05-变更简报.md`

### Excluded

- **不改** 规约层文件（analyst.md / harness-manager.md / technical-director.md / stage-role.md / index.md / role-model-map.yaml 等已由 chg-01~chg-03 落地，本 chg 只读 + 验证）；
- **不新增** pytest（归属 chg-04）；
- **不写** 专业化反馈抽检模板（归属 chg-06）；
- **不触发** regression 回调方向 B（若 dogfood 发现明显退化则作为"证据输入"交给 chg-06，但本 chg 不自动触发 regression）。

## 5. Acceptance

- Covers requirement.md **AC-8**（dogfood 活证）：
  - `.workflow/state/sessions/req-40/session-memory.md` 含"dogfood 活证节点清单"段，至少 5 个关键时间节点留痕；
  - analyst 角色身份自报文本在 session-memory 中有原文引用（形如 `我是分析师（analyst / opus），接下来我将...`）；
  - default-pick 清单（若触发）完整留痕。
- Covers requirement.md **AC-9**（scaffold_v2 mirror 跨文件 diff 归零）：
  - 7 条 `diff -rq` 全部无输出；
  - 若有输出则 ABORT 并在 session-memory 留痕未同步文件。
- Covers requirement.md **AC-10**（契约 7 + 硬门禁六自证）：
  - req-40 scope 内所有 .md 文档 grep `(req|chg|sug|bugfix|reg)-[0-9]+` 命中行经核对后，0 条违反"首次引用带 title / 批量列举带描述"；
  - 无 `chg-01 / 02 / 03` 或 `req-40~45` 裸扫射形态。

## 6. Risks

- **风险 1：dogfood 路径 A 与 req-40 executing 阶段流程交叠，可能导致 session-memory 职责混淆**。缓解：在 session-memory.md 明确新增段落 "## dogfood 活证节点清单（chg-05 封存）"，与 executing / planning / 其他 stage 区块互不干扰。
- **风险 2：契约 7 自检发现历史 req 引用的 title 与最新 state yaml 中 title 不一致**。缓解：AC-10 只对 req-40 scope 内（新增 / 修改）的引用生效，不回溯历史（契约 7 fallback 条款）；legacy 裸 id 明示不在本 chg scope。
- **风险 3：mirror diff 在 chg-01~chg-03 executing 未全部收紧前执行会误报**。缓解：default-pick D-1 = B 串行确保 chg-05 在 chg-03 mirror sync 完成后启动；本 chg Step 1 先复查三 chg executing 产物。
- **风险 4：dogfood 发现方向 C 明显退化（chg 拆分粒度粗 / 缺依赖）**。缓解：本 chg 只收集证据，不回滚；证据交由 chg-06 专业化反馈捕捉模板归因；若用户要求回调方向 B 则走 `harness regression` 新开 reg-02。
- **风险 5：harness validate --contract 7 CLI 不存在或接口变化**。缓解：fallback 到 `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+"` + 手工核对；若 `harness validate --contract all` 可用则优先。
