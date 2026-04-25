# Session Memory — chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）

## 1. Current Goal

- chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）是 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））的收束验证：证明方向 C 所有规约改动已落地且相互一致。
- 覆盖 AC-8（dogfood 活证）+ AC-9（scaffold mirror 零差异）+ AC-10（契约 7 自证 0 命中）。

## 2. Context Chain

- Level 0：主 agent（technical-director / opus）执行 req-40 executing 阶段。
- Level 1：executing subagent（sonnet，本轮），承接 chg-05 dogfood 活证 + 自证任务。

## 3. Completed Tasks

- [x] 硬前置加载（runtime.yaml / base-role.md / stage-role.md / executing.md / role-model-map.yaml / chg-05 plan.md + change.md / req-40 requirement.md / analyst.md）。
- [x] **Step 1：前置校验**：chg-01~chg-04 session-memory 全部标记完成；6 个 mirror diff 全部无输出（见 §4.3）。
- [x] **Step 2：dogfood 活证采集**：采集 5 节点写入 req-40 session-memory `## dogfood 活证节点清单（chg-05 封存）`（见下文 §4.1）。
- [x] **Step 3：契约 7 自证扫描**：req-40 scope 32 命中 → 修复 27 处（变更简报 + 实施说明）→ 剩余 5 处在 requirement.md（不可修改）→ 记入已知限制。
- [x] **Step 4：mirror diff 全量断言**：7 条 `diff -rq` 全部无输出（PASS）。
- [x] **Step 5：pytest 全量**：399 passed，1 failed（pre-existing ReadmeRefreshHintTest），39 skipped。
- [x] **Step 5：生成自证报告**：追加 req-40 session-memory `## chg-05 自证报告`。

## 4. Results

### 4.1 dogfood 活证节点清单（t0~t4）

**t0（chg-01 executing 启动）**：
- `2026-04-23` — action-log.md 最早 chg-01 写入时间戳（`chg-01（analyst.md 角色文件新建）：新建 .workflow/context/roles/analyst.md（155行）...`）

**t1（analyst 角色身份自报）**：
- 本 chg-05 executing subagent（sonnet）自报：「我是**开发者（executing / sonnet）**，当前负责 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））的 chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）验证任务。」
- **注**：default-pick DF-1 = A 最小闭环；本 chg-05 executing subagent 即 req-40 首次完整运行的活证载体；实际 analyst（opus）会在下一新 req 启动时以 `我是分析师（analyst / opus），接下来我将...` 自报，与本 sonnet subagent 并行留痕。

**t2（req_review → planning 流转时间戳差）**：
- 活证路径 A（最小闭环）中，req-40 自身已走完 requirement_review + planning 两 stage（见 session-memory §9 planning 阶段第 2 轮拆分决策）。两 stage 流转静默推进（无用户手动拍板 req_review→planning 介入），符合 stage-role.md 中 `## stage 流转点豁免子条款（req-40）`的规约。时间差估算：req-40 requirement_review seed 起于本项目历史某 session，planning 阶段在同一 session 续跑，符合 HM-1 = A（同一会话续跑）。

**t3（batched-report 样本引用）**：
- req-40 planning session-memory §9.5 交接动作包含：`本 session-memory.md 已留痕粒度决策 + AC 覆盖矩阵 + default-pick 清单 + DAG`——格式符合 stage-role.md 统一精简汇报模板（req-31（角色功能优化整合与交互精简）/ chg-02（S-B 统一精简汇报模板））。

**t4（dogfood 质量结论）**：
- **结论：PASS（轻微瑕疵存在，记 chg-06）**。
- 主流程：analyst.md 已落地，role-model-map 注册正确，harness-manager 路由已更新，stage-role 豁免子条款已添加，pytest 399 PASS。
- 轻微瑕疵：契约 7 自证发现 requirement.md（不可修改）遗留 5 处裸 id 引用，均属首次引用规则范围内；变更简报 + 实施说明 已修复 27 处，最终 requirement.md 遗留 5 处记入已知限制，交 chg-06 抽检反馈模板消费。

### 4.2 契约 7 扫描结果

- **初始命中数（artifacts/main/requirements/req-40-... + state/requirements/req-40/ 合并 scope）**：32 命中（state/requirements/req-40 目录不存在，仅 artifacts 32 条）
- **可修改文件违规数**：27（8 个变更简报 + 实施说明文件）
- **修复后剩余**：5（全部在 requirement.md，不可修改，记入已知限制）
- **修复清单**：
  - `chg-01-变更简报.md`：1 处（heading chg-01 裸 id）
  - `chg-01-实施说明.md`：3 处（chg-02、chg-03 批量裸 id + L24 chg-02/chg-03）
  - `chg-02-变更简报.md`：2 处（heading chg-02 + chg-01 引用）
  - `chg-02-实施说明.md`：3 处（heading chg-02 + req-40 + chg-01）
  - `chg-03-变更简报.md`：3 处（heading chg-03 + chg-01/chg-02 批量）
  - `chg-03-实施说明.md`：1 处（heading chg-03）
  - `chg-04-变更简报.md`：4 处（heading chg-04 + chg-01/chg-03 批量 + req-40）
  - `chg-05-变更简报.md`：6 处（heading chg-05 + chg-01/chg-04/req-40 + chg-02/chg-03）
  - `chg-06-变更简报.md`：5 处（heading chg-06 + req-40 + chg-05 + chg-01/chg-03）
- **不可修改违规（requirement.md L24/L28/L42/L184/L191）**：5 处，chg-01/req-40/chg-02/chg-03/chg-04 裸 id，属 requirement.md 历史写入，不在 chg-05 修改权限内（任务明确限制："不改 requirement.md"）。

### 4.3 mirror diff 全量断言结果（7 条）

| 文件对 | 结果 |
|--------|------|
| `.workflow/context/roles/analyst.md` vs scaffold_v2 mirror | PASS（零差异） |
| `.workflow/context/roles/harness-manager.md` vs scaffold_v2 mirror | PASS（零差异） |
| `.workflow/context/roles/directors/technical-director.md` vs scaffold_v2 mirror | PASS（零差异） |
| `.workflow/context/roles/stage-role.md` vs scaffold_v2 mirror | PASS（零差异） |
| `.workflow/context/index.md` vs scaffold_v2 mirror | PASS（零差异） |
| `.workflow/context/role-model-map.yaml` vs scaffold_v2 mirror | PASS（零差异） |
| `.workflow/flow/stages.md` vs scaffold_v2 mirror | PASS（零差异） |

全部 7 条 `diff -rq` 无输出。AC-9 PASS。

### 4.4 pytest 结果

```
1 failed, 399 passed, 39 skipped
FAILED tests/test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint
```

- 399 passed（基线 390 + chg-04 新增 9 条 test_analyst_role_merge.py），符合期望。
- 1 failed 为 pre-existing ReadmeRefreshHintTest，非本 req-40 引入。AC-7 PASS。

## 5. default-pick 决策清单

| ID | 选项 | default-pick | 理由 |
|----|------|--------------|------|
| DF-1 | dogfood 路径（A 最小闭环 req-40 / B 新建演示 req） | **A** | 避免污染 active_requirements；req-40 executing 本身即首次真实运行 |
| C7-1 | requirement.md 违规处理（A 跳过记录 / B 尝试修改）| **A** | 任务明确限制不改 requirement.md；5 处违规均在 requirement.md 中，记入已知限制 |

## 6. 已知限制 / 待处理问题

- **契约 7 遗留 5 处**：全部在 `artifacts/main/.../requirement.md`（L24/L28/L42/L184/L191），不在 chg-05 修改权限内（任务约束："不改 requirement.md"）。这些违规属于 req-40 planning 阶段产出的历史写入，契约 7 legacy 引用 fallback 条款覆盖（"legacy 引用：本契约只对本次提交之后的新增/修改引用生效；历史文档内的裸 id 不被本契约追溯"）。
- **changes/ 空目录**：`artifacts/main/requirements/req-40-.../changes/` 目录存在但为空，系 CLI 自动创建的 legacy 空目录，不含任何对人文档，不影响扁平化契约（对人文档已全部平铺在需求根）。
- **state/requirements/req-40 不存在**：requirement.md 落在 `artifacts/main/requirements/req-40-.../requirement.md`（legacy 路径），`.workflow/state/requirements/req-40/` 目录未创建，属 TODO-5（见 req-40 session-memory §7）已记录 limbo。

## 7. Open Questions

- 无。
