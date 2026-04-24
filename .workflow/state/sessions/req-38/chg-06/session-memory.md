# Session Memory — chg-06（硬门禁六 + 契约 7 批量列举子条款补丁） / planning

## 1. Current Goal

- 为 chg-06（硬门禁六 + 契约 7 批量列举子条款补丁）填充 plan.md，覆盖 reg-01（对人汇报批量列举 id 缺 title 不可读） decision.md 给出的路径 A（base-role.md S-A）+ 路径 B（stage-role.md S-B）双补丁。
- 同步落 scaffold_v2 mirror（共 4 份 .md）。
- 不实际修改 base-role.md / stage-role.md（交给 executing），不派发下层 subagent，不 commit。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）→ planning stage 派发
- Level 1: 架构师（planning / opus）→ 本 session，仅产出 plan.md + session-memory.md

## 3. Completed Tasks

- [x] 读取 runtime.yaml / base-role.md / stage-role.md / planning.md / role-model-map.yaml / reg-01 decision.md / reg-01 analysis.md / chg-06 change.md + plan.md（空模板）
- [x] grep 锚定 base-role.md 第 110 行（硬门禁六例外条款）+ stage-role.md 第 257 行（契约 7 "裸 id = 违规"）
- [x] grep 验证 scaffold_v2 mirror 行号与 live 一致（base-role 第 110 行 / stage-role 第 257 行）
- [x] 撰写 plan.md（§1 6 步 + §2 三段验证 + §3 依赖与执行顺序）
- [x] 落本 session-memory.md

## 4. Results

### 产出文件

- `artifacts/main/requirements/req-38-.../changes/chg-06-硬门禁六-契约-7-批量列举子条款补丁/plan.md`（覆写空模板，6 步 dev + 3 段验证 + 依赖顺序）
- `.workflow/state/sessions/req-38/chg-06/session-memory.md`（本文件，新建）

### 关键决策

| 决策点 | 选项 | default-pick | 理由 |
|--------|------|-------------|------|
| P-1: S-A 文字插入位置 | A. 例外条款之后 / B. 例外条款之前 / C. 触发场景段之后 | **A** | 例外条款是"豁免"，新子条款是"反向收紧"，紧跟例外条款顺序最自然；与 reg-01 analysis 路径 A 落点一致 |
| P-2: S-B 文字插入位置 | A. "裸 id = 违规"之后 / B. "同上下文后续可简写"之后 / C. 校验方式段内 | **A** | "裸 id = 违规"是契约 7 最强约束，新反向豁免条款与之并列最易被检索；与 reg-01 analysis 路径 B 落点一致 |
| P-3: S-A / S-B 是否同一 commit | A. 同一 commit / B. 分两 commit | **A** | 两段文字逻辑同源（都覆盖批量列举场景），分 commit 易出现 mirror 漂移（参考 5669a69 历史） |
| P-4: mirror 同步是否纳入本 chg | A. 纳入 Step 5 / B. 留给后续 chg | **A** | mirror 漂移是 CLI sug-12 / sug-13 复发型回归源头（bugfix-3 已修），本 chg 起就同步避免再犯 |
| P-5: 是否新增 AC | A. 不新增（reg 衍生补丁）/ B. 新增 AC-N+1 | **A** | reg-01 decision § 3 明确"路径 A + B 并列交付"已是 AC，再新增 req-38 AC 反而稀释 req-38 主线（api-document-upload 闭环） |
| P-6: 路径 C（lint CLI）是否本 chg 范围 | A. 排除（独立 sug）/ B. 纳入 | **A** | reg-01 decision § 3 已明确"sug 候选不阻塞本 chg"；保持本 chg 仅 .md 改动、最小可逆 |
| P-7: 反向豁免条款触发场景枚举数量 | A. 4 类（DAG / 收束 / 索引 / 进度）/ B. 兜底"密集展示场景"一句话 | **A** | reg-01 decision § 2 显式列了 4 类，逐条枚举可读性 + 反向 grep 检测命中率均高于兜底句 |

### default-pick 决策清单（汇报字段 3 用）

7 条 default-pick 全部 = A 严格范围（无 B/C 外溢）；无开放问题留给主 agent 决策。

## 5. Next Steps

- 主 agent 收到本 batched-report 后，按 default-pick 推进 stage 流转到 executing（chg-06 实施）。
- executing 阶段（开发者 / sonnet）按 plan.md Step 1-6 顺序执行，不重读 reg-01 analysis（plan.md 已嵌入根因摘要）。
- 不需要 testing 介入新增测试（仅 .md 文字改动，pytest 全量回归即覆盖）；contract 自检由现有 `harness validate --contract all` 兜底。

## 6. 待处理捕获问题

- 无。

## 7. 上下文消耗评估

- 本 session 读取文件 8 份（runtime.yaml / base-role.md / stage-role.md / planning.md / role-model-map.yaml / reg-01 decision.md / reg-01 analysis.md / chg-06 change.md + plan.md 模板），grep 4 次，写入 2 份。
- 估算 ≤ 30% 上下文占用，远低于 70% 评估阈值，无需 /compact。

---

# Session Memory — chg-06（硬门禁六 + 契约 7 批量列举子条款补丁） / executing

## 1. Current Goal

- 按 chg-06（硬门禁六 + 契约 7 批量列举子条款补丁） plan.md Step 1-6 执行：S-A（base-role.md 批量列举子条款）+ S-B（stage-role.md 反向豁免条款）+ scaffold_v2 mirror 同步 + 自证。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）→ executing stage 派发
- Level 1: 开发者（executing / sonnet）→ 本 session，承接 chg-06 实施

## 3. Completed Tasks

- [x] Step 1: 锚定 base-role.md 第 110 行（例外条款后、与契约 7 的关系前）
- [x] Step 2: 插入"批量列举子条款"（≤ 5 行 md，含正例/反例）至 live base-role.md
- [x] Step 3: 锚定 stage-role.md 第 257 行（"裸 id = 违规"后、校验方式前）
- [x] Step 4: 插入"id 密集展示反向豁免条款"（≤ 5 行 + 4 子项）至 live stage-role.md
- [x] Step 5: scaffold_v2 mirror 同步（base-role.md + stage-role.md 两份 mirror 逐字一致）
- [x] Step 6: grep 自证（4 处均命中）+ diff 自证（live/mirror 完全一致，exit 0）+ pytest 自证（341 passed, 53 skipped，零回归）

## 4. Results

### 产出文件

- `.workflow/context/roles/base-role.md`（新增批量列举子条款段，第 112 行起）
- `.workflow/context/roles/stage-role.md`（新增 id 密集展示反向豁免条款段，第 258 行起）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`（mirror 同步）
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`（mirror 同步）
- `artifacts/main/requirements/req-38-.../changes/chg-06-.../实施说明.md`（对人文档）

### 验证输出

```
grep base-role.md "批量列举子条款": 行 112 命中（live）, 行 112 命中（mirror）
grep stage-role.md "id 密集展示反向豁免条款": 行 258 命中（live）, 行 258 命中（mirror）
diff base-role.md: IDENTICAL (exit 0)
diff stage-role.md: IDENTICAL (exit 0)
pytest: 341 passed, 53 skipped in 72.51s — 零回归
```

### 烟测结论（§2.2）

- 假 batched-report `本 stage 完成 chg-01 / 02 / 03 / 04 / 05。` → 按 base-role.md 硬门禁六批量列举子条款判 **FAIL**（裸数字扫射），按 stage-role.md 契约 7 反向豁免条款亦判 **FAIL**（密集展示场景豁免不生效）。
- 同一 id 重复豁免回归：`先看 chg-01，然后 chg-01 又出现一次` → 例外条款仍 **PASS**（未受反向条款误伤）。

### default-pick 决策清单

- 无新 default-pick 争议（执行型 stage，直接按 plan.md 步骤落地）。

## 5. 待处理捕获问题

- 无。

## 6. 上下文消耗评估

- 读取文件 9 份（runtime.yaml / base-role.md / stage-role.md / executing.md / role-model-map.yaml / plan.md / decision.md / mirror 两份局部读取），grep 8 次，写入 4 份文件 + session-memory。
- 估算 ≤ 40% 上下文占用，低于 70% 评估阈值，无需 /compact。
