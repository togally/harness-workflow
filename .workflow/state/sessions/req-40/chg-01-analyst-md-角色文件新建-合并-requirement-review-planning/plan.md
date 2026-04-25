# Change Plan — chg-01（analyst.md 角色文件新建）

## 1. Development Steps

### Step 1: 读取并对齐两源角色文件

- 读取 `.workflow/context/roles/requirement-review.md` 全文；
- 读取 `.workflow/context/roles/planning.md` 全文；
- 列出交集（相同硬门禁 / SOP / 对人文档契约 / 经验沉淀）与差集（需求澄清 vs 变更拆分各自独有条款）；
- 产出对齐笔记到 session-memory.md（本步骤不写 analyst.md）。

### Step 2: 起草 analyst.md 骨架（≤ 200 行）

- 文件头：`# 角色：分析师（analyst）` + 引用 `base-role.md` + `stage-role.md` 继承声明；
- 8 个必备章节：
  1. `## 角色定义`（一句话：既做需求澄清也做变更拆分，对应 req_review + planning 两 stage 由同一角色执行）
  2. `## 硬门禁`（继承 base-role 硬门禁一~七 + stage-role Session Start + 契约 1~7；明确列出 req-35（硬门禁六）/ req-37（硬门禁七）/ req-38（批量列举子条款）引用）
  3. `## 标准工作流程（SOP）`：分 Part A（需求澄清）+ Part B（变更拆分）；Step 0 初始化 → Step A1 读取需求上下文 → Step A2 澄清与讨论 → Step A3 编写并确认 `requirement.md` → Step B1 拆分变更 → Step B2 制定执行计划 → Step 4 产出检查 → Step 5 交接
  4. `## 允许的行为`（并集：讨论 + 澄清 + 编写 requirement.md + 拆分变更 + 编写 change.md / plan.md）
  5. `## 禁止的行为`（并集：不写代码 + 不修改 context/roles 下其他文件 + 不跳过需求确认 + 不开始实现 + 不跨 stage 越权）
  6. `## 对人文档输出契约`（并列产出：`需求摘要.md` req 级 + `chg-NN-变更简报.md` change 级，字段模板复用 requirement-review / planning 原模板）
  7. `## 退出条件`（并集：requirement.md AC 完整 + 每个 chg 有 change.md + plan.md + 对人文档齐全 + `harness validate --human-docs` exit 0）
  8. `## 流转规则`（覆盖 req_review → planning → executing 两步流转；含 escape hatch 声明）

### Step 3: 写入 live 文件

- `toolsManager` 推荐写入工具（Write）；
- 执行 `接下来我要执行 写入 analyst.md` / `执行完成，结果是 analyst.md 已落盘`；
- 在 `.workflow/state/action-log.md` 追加一行。

### Step 4: 同步 mirror

- `cp .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`；
- 跑 `diff -rq .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 确认无输出。

### Step 5: 自检 + 交接

- `grep -c "^## " .workflow/context/roles/analyst.md` ≥ 6；
- `grep -E "req-35|req-37|req-38" .workflow/context/roles/analyst.md` 至少 3 处命中；
- `wc -l .workflow/context/roles/analyst.md` ≤ 200；
- grep 扫描裸 id（`(req|chg|sug|bugfix|reg)-[0-9]+` 命中点紧随无 `（...）` / `— ...`）命中数 = 0；
- 更新 chg-01 `session-memory.md`：记录已完成步骤 + default-pick 清单；
- 更新 `artifacts/main/requirements/req-40-.../chg-01-变更简报.md`（按 planning.md 对人文档契约模板，≤ 1 页）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `test -f .workflow/context/roles/analyst.md`（存在性）
- `test -f src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`（mirror 存在性）
- `diff -rq .workflow/context/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 无输出
- `[ $(grep -c "^## " .workflow/context/roles/analyst.md) -ge 6 ]`（章节数）
- `[ $(wc -l < .workflow/context/roles/analyst.md) -le 200 ]`（行数上限）
- `grep -q "base-role.md" .workflow/context/roles/analyst.md && grep -q "stage-role.md" .workflow/context/roles/analyst.md`（继承声明）
- `grep -q "req-35" .workflow/context/roles/analyst.md && grep -q "req-37" .workflow/context/roles/analyst.md && grep -q "req-38" .workflow/context/roles/analyst.md`（硬门禁引用）

### 2.2 Manual smoke / integration verification

- 人工抽读 analyst.md 8 节，确认"两 stage 由同一 analyst 执行"语义明确；
- 人工抽读 SOP Part A / Part B 划分，确认需求澄清与变更拆分职责不重叠；
- 对照 `requirement-review.md` + `planning.md` 退出条件，确认 analyst 退出条件无遗漏；
- 跑 `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" .workflow/context/roles/analyst.md` 肉眼扫一遍，确认每个命中行紧随 `（...）` / `— ...` 描述。

### 2.3 AC Mapping

- AC-1（analyst.md 存在 + 职责完整） -> Step 2 + Step 3 + Step 5 自检 + 2.1 存在性 + 章节数 + 行数断言；
- AC-10（契约 7 + 硬门禁六自证）起点 -> Step 5 grep 裸 id 违规 = 0 + 2.2 肉眼扫；
- AC-9（mirror diff 归零）起点 -> Step 4 + 2.1 diff -rq 断言。

## 3. Dependencies & Execution Order

- **前置依赖**：无（chg-01 是 DAG 根节点）；
- **后置依赖**：chg-02 / chg-03 / chg-04 / chg-05 / chg-06 均依赖本 chg 落地 analyst.md 作为基准；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 → Step 5，强制串行（前一步产物是后一步输入）；
- **不并行**：本 chg 不拆子任务，单一 subagent 单通道执行。
