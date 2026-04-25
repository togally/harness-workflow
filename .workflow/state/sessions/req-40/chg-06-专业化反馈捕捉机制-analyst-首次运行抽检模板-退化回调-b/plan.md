# Change Plan — chg-06（专业化反馈捕捉机制）

## 1. Development Steps

### Step 1: 创建 / 追加 `.workflow/context/experience/roles/analyst.md`

- 若文件不存在则新建；若存在则追加；
- 写入内容骨架（≤ 80 行）：

```markdown
# 经验：分析师（analyst）

> 溯源：req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））/ chg-06（专业化反馈捕捉机制（analyst 首次运行抽检模板 + 退化回调 B））

## 首次运行抽检模板（req-40）

每次 analyst 承接一个 req 完成 requirement + chg 拆分后，subagent / 用户在 session-memory.md 追加一条抽检记录，字段固定如下：

| 字段 | 说明 | 样例 |
|------|------|------|
| 抽检产物 | 被抽检的产物名（requirement.md / chg-NN/change.md / plan.md / 风险节 / 依赖节） | `req-41/chg-02/plan.md §3` |
| 质量评分 | A（明显优于原两步） / B（持平） / C（明显退化） | `B` |
| 退化点明细 | 若评分 C：列具体缺失或粗糙点，引用产物行号；A / B 可省略 | `依赖分析只有 2 句，原 planning 阶段平均 5 句` |
| 是否触发 regression 回调 B | 是 / 否；"是"即开 reg-NN 回调软合并 | `否` |
| 抽检人 + 时间 + req 范围 | 人名 / 日期 / 涉及 req id | `用户 / 2026-04-25 / req-41` |

## 方向 B 回调触发路径

- 若连续 ≥ 2 个 req 抽检结果为 "C 明显退化"，建议开 reg-NN 走：
  ```
  harness regression --requirement "方向 C 退化，回调软合并 auto-advance 方向 B"
  ```
- regression 阶段诊断师按 reg-01（planning 并入 requirement_review，用户只管需求确认，chg 拆分由 agent 自主）decision.md §2-3 四方向对比表重评估，产出新 decision.md；
- 不自动回滚 req-40 角色合并产物；回滚动作由新 decision.md 决定。

## 首次抽检样本（req-40 自身）

- 抽检产物：TODO — 由 chg-05 dogfood t4 结论回填；
- 质量评分：TODO — 填写 A / B / C；
- 退化点明细：TODO；
- 是否触发 regression 回调 B：TODO；
- 抽检人 + 时间 + req 范围：TODO / chg-05 封存时间 / req-40。
```

### Step 2: 同步 mirror

- `cp .workflow/context/experience/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/analyst.md`；
- 跑 `diff -rq .workflow/context/experience/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/analyst.md` 确认无输出。

### Step 3: 补 session-memory 留痕字段

- 在 `.workflow/state/sessions/req-40/session-memory.md` 追加段 `## analyst 专业化抽检反馈`：
  - 若 chg-05 dogfood t4 结论已可用，回填 5 字段；
  - 若尚未可用，写占位 "## analyst 专业化抽检反馈 — 首次抽检待 chg-05 dogfood 落地后回填"。

### Step 4: 自检 + 交接

- 跑 AC-11 的 grep / diff 断言（见 2.1）；
- 更新 chg-06 `session-memory.md`：记录步骤 + 首次样本填写情况；
- 更新 `artifacts/main/requirements/req-40-.../chg-06-变更简报.md`；
- 按硬门禁二追加 `action-log.md`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `test -f .workflow/context/experience/roles/analyst.md`（文件存在）
- `grep -q "首次运行抽检模板" .workflow/context/experience/roles/analyst.md`
- `grep -q "方向 B 回调触发路径" .workflow/context/experience/roles/analyst.md`
- `grep -q "质量评分" .workflow/context/experience/roles/analyst.md`（5 字段表格至少含"质量评分"）
- `diff -rq .workflow/context/experience/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/analyst.md`（无输出）
- `grep -q "analyst 专业化抽检反馈" .workflow/state/sessions/req-40/session-memory.md`

### 2.2 Manual smoke / integration verification

- 肉眼核对 5 字段清单语义（产物 / 评分 / 退化点 / 回调 / 人时间），确认无冗余字段；
- 对照 AC-11 判据逐条核对；
- 若 chg-05 dogfood 已落地，确认首次抽检样本 5 字段已回填真实值（非 TODO 占位）。

### 2.3 AC Mapping

- AC-11（专业化损失评估） -> Step 1（模板建立）+ Step 2（mirror 同步）+ Step 3（session-memory 留痕）+ 2.1 grep/diff 断言 + 2.2 5 字段核对。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-05（首次抽检样本需要 chg-05 dogfood t4 结论作为输入）；若 chg-05 未产出 t4，chg-06 仍可落地模板骨架，样本字段标 TODO 供后续回填；
- **后置依赖**：无（chg-06 是 DAG 末端节点）；
- **替代路径**：seed default-pick D-2 原为 A（合并进 chg-05），planning 阶段翻转为 B（独立保留）。理由：AC-11 含"触发 regression 回调方向 B"的条件分支逻辑，与 chg-05 单向收束语义不同；独立 chg 便于归档时单独查检抽检模板的有效性；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 强制串行；轻量 chg，预计 1 个 subagent 单通道完成。
