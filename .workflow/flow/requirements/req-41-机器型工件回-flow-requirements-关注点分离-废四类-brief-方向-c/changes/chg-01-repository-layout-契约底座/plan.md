# Change Plan — chg-01（repository-layout 契约底座）

## 1. Development Steps

### Step 1: 读取当前 artifacts-layout.md 全文 + 列改造差异

- 读取 `.workflow/flow/artifacts-layout.md` 全文；
- 列出 §1~§5 现有段落 → 新 `repository-layout.md` §1~§5 的 mapping 表（写到 chg-01 session-memory.md）；
- 识别旧文中需"删"（四类 brief + 耗时与用量报告 + `.workflow/state/requirements/` / `.workflow/state/sessions/` 机器型落位段）、需"改"（机器型落位路径改 flow/requirements/）、需"加"（三大子树总览段 + raw requirement.md artifacts 副本声明 + req-41（机器型工件回 flow）+ 分水岭）三类。

### Step 2: 执行 git mv 重命名

- `git mv .workflow/flow/artifacts-layout.md .workflow/flow/repository-layout.md`；
- `git mv src/harness_workflow/assets/scaffold_v2/.workflow/flow/artifacts-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`；
- 暂不动内容（本步骤只换名不改内容，保 history 清晰）。

### Step 3: 重写 repository-layout.md 内容

- §1 新增"三大子树语义总览"段：
  - `.workflow/state/`：runtime 真·实时数据（`runtime.yaml` / `feedback/feedback.jsonl` / `action-log.md` / `experience/index.md` 等）
  - `.workflow/flow/`：权威工作流工件（`repository-layout.md` 契约 / `requirements/{req-id}-{slug}/` 机器型 / `archive/{branch}/` 归档 / `stages.md` 等）
  - `artifacts/{branch}/`：对人可读签字执行产物（raw `requirement.md` 副本 / `交付总结.md` / `决策汇总.md` / SQL / 部署 / 接入 / runbook / 手册 / 合同附件）
- §2 对人文档白名单：删 `需求摘要.md` / `chg-NN-变更简报.md` / `chg-NN-实施说明.md` / `reg-NN-回归简报.md` / `耗时与用量报告.md` 五行；保留 raw `requirement.md`（artifacts 副本）/ `交付总结.md` / `决策汇总.md` / SQL / 部署 / 接入 / runbook / 手册 / 合同附件；加"raw `requirement.md` artifacts 副本"说明：非流程引擎读写，只为外部审阅；
- §3 机器型落位：
  - `requirement.md` → `.workflow/flow/requirements/{req-id}-{slug}/requirement.md`
  - `change.md` + `plan.md` + `session-memory.md` → `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/`
  - `regression.md` + `analysis.md` + `decision.md` + `meta.yaml` + `session-memory.md` → `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/`
  - `task-context/` / `usage-log.yaml` / req yaml（stage_timestamps）同子树；
- §4 历史存量豁免：req-02（workflow 分包结构修复）~ req-38（api-document-upload 工具闭环）legacy（多层 brief 保留）；req-39（对人文档家族契约化）/ req-40（阶段合并与用户介入窄化）flat layout（仍用 state/sessions/）；req-41+ flow/requirements/（新分水岭）；
- §5 反例核对段微调：加"未触碰 `artifacts/main/requirements/req-02 ~ req-40` 下历史存量四类 brief（git log 分水岭）"；
- 文末"参考"段：引用 req-41 requirement.md §3.1 Scope-共骨架 + §5 DAG。

### Step 4: 同步 scaffold_v2 mirror

- `cp .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`；
- 跑 `diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 确认无输出。

### Step 5: 自检 + 交接

- `test -f .workflow/flow/repository-layout.md` 通过；
- `test ! -f .workflow/flow/artifacts-layout.md` 通过；
- `grep -c "^## " .workflow/flow/repository-layout.md` ≥ 5；
- `grep -E "需求摘要|变更简报|实施说明|回归简报|耗时与用量报告" .workflow/flow/repository-layout.md` 命中数 = 0；
- `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" .workflow/flow/repository-layout.md` 每个命中行人眼核对含 `（...）` / `— ...`；
- 更新 chg-01 session-memory.md：记录完成步骤 + default-pick 清单；
- **不产出 `chg-01-变更简报.md`**（方向 C 本 req 自身就要废止四类 brief，analyst / executing 不自相矛盾地产出；CLI 自动生成的空壳文件在 chg-03（validate_human_docs 重写）落地后由 validate 精简跳过，chg-07（dogfood 活证 + scaffold_v2 mirror 收口）dogfood 统一清理）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `test -f .workflow/flow/repository-layout.md`
- `test ! -f .workflow/flow/artifacts-layout.md`
- `test -f src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`
- `test ! -f src/harness_workflow/assets/scaffold_v2/.workflow/flow/artifacts-layout.md`
- `diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 无输出
- `grep -c "^## " .workflow/flow/repository-layout.md` ≥ 5
- `grep -cE "需求摘要|变更简报|实施说明|回归简报|耗时与用量报告" .workflow/flow/repository-layout.md` = 0
- `grep -q "三大子树" .workflow/flow/repository-layout.md`（§1 总览段落锚点）

### 2.2 Manual smoke / integration verification

- 人工抽读 §1 三大子树总览，确认 state / flow / artifacts 三子树职责清晰无重叠；
- 人工抽读 §2 白名单，确认四类 brief + 耗时报告已删，raw requirement.md + 交付总结 + 决策汇总 + SQL + 部署 + 接入 + runbook + 手册 + 合同附件齐全；
- 人工抽读 §3 机器型落位，确认路径全部指向 `.workflow/flow/requirements/{req-id}-{slug}/`；
- 人工抽读 §4 历史存量豁免段的三段式分水岭（≤38 legacy / 39-40 flat / ≥41 flow）；
- 跑 `git log --follow .workflow/flow/repository-layout.md` 确认 history 贯通到原 `artifacts-layout.md`。

### 2.3 AC Mapping

- AC-01（Scope-共骨架 git mv + §2 重写） → Step 2 + Step 3 + 2.1 存在性 + 章节数断言；
- AC-07（白名单清理起点） → Step 3 §2 重写 + 2.1 grep 四类 brief 命中数 = 0；
- AC-15（scaffold mirror diff 归零起点） → Step 4 + 2.1 `diff -q` 断言；
- AC-14（契约 7 + 硬门禁六自证起点） → Step 5 grep 裸 id 人眼核对。

## 3. Dependencies & Execution Order

- **前置依赖**：无（本 chg 是 req-41 DAG 根节点）；
- **后置依赖**：chg-02（CLI 路径迁移 flow layout）/ chg-03（validate_human_docs 重写删四类 brief）/ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）/ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）均依赖本 chg 的 `repository-layout.md` 作为权威路径源；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 → Step 5 强制串行（git mv 必须先落，内容重写才能在新文件上改）；
- **不并行**：单一 subagent 单通道执行。
