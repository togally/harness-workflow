# Testing Stage 规则

## 0. 测试范围默认 targeted（B3）

> bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） B3 落地。

### 默认范围

testing 阶段默认执行 **targeted 回归**：
- `plan.md §4. 测试用例设计`（req 模式）或 `regression/diagnosis.md §测试用例设计`（bugfix 模式）中明确列出的用例；
- Step 2.75 合规扫描：`git diff --name-only` 命中文件相关测试（default-pick P-5 = A，保守范围）。

### 全量回归触发条件（任一即可）

满足以下任一条件时，testing 方可跑全量回归：

1. `plan.md §4. 测试用例设计` 段头标记 `regression_scope: full`；
2. `regression/diagnosis.md §测试用例设计` 段头标记 `regression_scope: full`；
3. acceptance / done 阶段主 agent 显式触发（非 testing 自发）；
4. 用户在 briefing 中**显式写明** "跑全量回归"（仅当含明确用户指令时）。

### 禁止行为

- **禁止**主 agent 在 briefing 中**默认要求** testing 跑全量（未经触发条件约束 = over-instructing）；
- testing subagent 自发跑 `pytest tests/ -x` 全量 = 违反 targeted 默认原则，须在 test-report.md 标注触发条件来源。

## 核心要求
- 测试工程师必须是独立 subagent，不得是执行过 executing 阶段的 agent
- 测试标准来自 `requirement.md` 的验收标准以及 `plan.md / diagnosis.md §测试用例设计`（B2），不得自行降低
- 测试记录必须客观，不带开发者视角的解释

## 测试活动

### 1. 测试用例设计
- 基于 requirement.md 验收标准逐条设计测试用例
- 每条验收标准至少对应一个测试用例
- 包含正向用例（期望通过）和边界用例（边缘场景）

### 2. 测试计划产出
- 测试范围：覆盖哪些功能模块
- 测试方法：自动化 / 手动操作 / 日志验证
- 通过标准：每个用例的 pass/fail 判定条件

### 3. 执行测试
- 按测试计划逐条执行
- 记录每个用例的实际结果
- 失败用例必须记录：期望值、实际值、复现步骤

## 测试记录格式

```markdown
## 测试结果

| 用例 | 验收标准 | 结果 | 备注 |
|------|---------|------|------|
| TC-01 | ... | ✅ 通过 / ❌ 失败 | |
```

## R1 越界 / revert 抽样 / 契约 7 合规 / req-29 映射 / req-30 透出（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-03（S-C testing/acceptance 职责边界精简）吸收自 acceptance 加分维度）

> 溯源：req-31 / chg-03；本章节把原 acceptance 的加分维度吸收进 testing，使 testing 成为技术验证 + 合规扫描的权威终点。`test-report.md` 覆盖以下五项扫描。

### 1. R1 越界核查

- 对比本 req 的 R1 豁免范围（由 `requirement.md §4.3` 明示）与实际 git diff（`git diff --name-only <base>..HEAD`）。
- 命中 `src/` / `tests/` 但不在豁免清单内的文件即视为越界，在 `test-report.md` 标记 FAIL。
- 默认扫描范围 = `git diff` 命中文件（req-31 / chg-03 default-pick P-5 = A）。

### 2. revert 抽样

- 对本 req 所有 chg 的 commit sha，随机抽样 ≥ 1 个执行 `git revert --no-commit <sha>` dry-run，确认冲突 = 0。
- 发现 conflict 不阻断 testing，但必须在 `test-report.md` 写入"revert 抽样发现冲突"并建议 regression。

### 3. 契约 7 合规扫描

- `grep -rnE "(req|chg|sug|bugfix|reg)-[0-9]+" artifacts/{branch}/requirements/{req-id}-{slug}/ --include=*.md` 对首次命中行逐一核查是否含 `（{title}）`；失败即 FAIL。
- 缺失一般源于新建文档遗漏，testing 可请求 executing 回补；修复后重扫即可。

### 4. req-29（角色→模型映射）映射回归

- 验证 `.workflow/context/role-model-map.yaml` 未被本 req 误改（对比 `git log -- .workflow/context/role-model-map.yaml`，新 commit 应为零）。
- 抽样两个 role 的 subagent 派发记录，确认 briefing `model` 字段符合 yaml 映射。

### 5. req-30（用户面 model 透出）回归

- 抽样本 req 产出的 session-memory / action-log，grep `派发 .+\((Opus|Sonnet)` 至少 1 行；
- 抽样自我介绍段，grep `（.+ / (opus|sonnet)）` 至少 1 行。

### 输出要求

- 上述 5 项整合进 `test-report.md`，每项显式标注 PASS / FAIL；testing 阶段退出条件 = 5 项全 PASS + 原 AC 测试全通过。

## 完成条件
- 全部用例通过 → `harness next` → `acceptance`
- 有用例失败 → `harness regression "<失败描述>"` → 诊断后路由
