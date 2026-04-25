# Regression Intake — reg-01（artifacts 布局语义复核：需求文档归属 + .workflow/flow/requirements 应否复用）

> 隶属：req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））
> 触发时间：2026-04-24 acceptance stage 后期
> 诊断师：regression / opus（subagent level 1）
> 主 agent：technical-director / opus

## 1. Issue Title

artifacts 布局语义复核：需求文档归属 + `.workflow/flow/requirements` 应否复用

## 2. Reported Concern（用户原话）

> "为什么任务中没有在 `.workflow/flow/requirements` 中，而是在制品仓库汇总，制品仓库肯定得有需求文档，但是绝对不是那个给人看的处理过的，绝对不应该 requirements 和 change 都跑到制品仓库去了"

### 关键断言三条

1. **位置认知错位**：用户期待"任务/需求工件"住在 `.workflow/flow/requirements/`，而非 `artifacts/`。
2. **artifacts 语义判断**：artifacts 该有需求文档（raw），但**不是**"给人看的处理过的"（即**不是 `需求摘要.md`**）。
3. **双重落位反对**：`requirements` 与 `changes` 两类**都跑到 artifacts**，用户认为违反分工。

## 3. Current Behavior（现状盘点）

### 3.1 目录实况（req-40 活跃样本）

| 位置 | 文件清单 | 契约（artifacts-layout.md）期望 | 差异判定 |
|------|---------|------------------------------|---------|
| `artifacts/main/requirements/req-40-.../` | `requirement.md` / `acceptance-report.md` / `chg-01..06-变更简报.md` / `chg-01..06-实施说明.md` / `reg-01-回归简报.md` / `changes/`（空目录残留） | 只装对人文档（`需求摘要.md` / `chg-NN-变更简报.md` / `reg-NN-回归简报.md` / `chg-NN-实施说明.md` / `交付总结.md` 等） | **违约 3 处**：①`requirement.md`（机器型）不应在 artifacts ②`acceptance-report.md`（机器型）不应在 artifacts ③`changes/` 空子目录（扁平规约不该建） |
| `artifacts/main/requirements/req-40-.../需求摘要.md` | **缺失** | 必须产出 | **违约 1 处**：analyst 未落盘 |
| `.workflow/state/requirements/req-40/` | 只有 `testing-report.md` | `requirement.md` / `testing-report.md` / `acceptance-report.md` | **违约 2 处**：`requirement.md` + `acceptance-report.md` 未落到此处 |
| `.workflow/state/sessions/req-40/` | `chg-01..06/` + `regressions/reg-01-.../` + `acceptance/` + `testing/` + `session-memory.md` + `task-context/` | 同等结构 | **符合契约** |
| `.workflow/state/sessions/req-40/regressions/reg-01-.../` | `regression.md` / `analysis.md` / `decision.md` / `meta.yaml` / `session-memory.md` | 同等 | **符合契约** |
| `.workflow/flow/requirements/` | **空**（仅 `.` / `..`） | 新规废弃，req-39+ 不应再用 | **符合契约** |
| `.workflow/flow/archive/req-20-审查Yh-platform工作流与产出/` | 历史遗留目录（不在 `main/` 分支层下） | 新规应全部搬到 `.workflow/flow/archive/main/` | **历史遗留**（req-20 时代旧布局痕迹，存量豁免） |
| `.workflow/flow/archive/main/` | 29 个 legacy req 目录（req-01..req-24 系列） | 旧规保留 | **legacy 豁免** |
| `artifacts/main/archive/requirements/req-39-.../` | 归档 req-39：`需求摘要.md` + `完成回顾.md` + `chg-XX-变更简报.md` + `chg-XX-实施说明.md` + `acceptance-report.md`（机器型错位） + `state.yaml`（机器型错位） + `sessions/` / `regressions/`（机器型错位） | 归档后机器型文档不应留在 artifacts 下 | **违约** —— 归档路径 `archive_requirement` 把 state 也一并搬到 artifacts/archive，未按契约分离 |

### 3.2 历史存量（豁免）

- `.workflow/flow/archive/main/req-01..req-24` 共 29 目录：req-02 ~ req-24 时代布局（`flow/archive/main/{req-id}/` 下同时放 `requirement.md` + `changes/` + `done-report.md`）。**legacy 豁免**（artifacts-layout.md §5）。
- `artifacts/main/archive/requirements/req-28..req-39` 共 13 目录：req-28 ~ req-38 时代布局（artifacts 里含 `需求摘要.md` + `changes/` + `requirement.md` + `acceptance-report.md`）。其中 req-38 为"混合过渡期样本"，req-39 是"新规首发"但归档时错位了机器型文档。

### 3.3 CLI 行为校验（`src/harness_workflow/workflow_helpers.py`）

- `create_requirement`（line 4174-4253）：req-id ≥ 39 时 `requirement.md` 写到 `.workflow/state/requirements/{req-id}/`，artifacts/ 只建空目录。**代码实现与契约一致**。
- `create_change`（line 4389-4455）：req-id ≥ 39 时 `change.md` / `plan.md` 写到 `.workflow/state/sessions/{req-id}/{chg-id}/`，artifacts/ 仅落 `chg-NN-变更简报.md` placeholder。**代码实现与契约一致**。
- `create_regression`（line 4458-4547）：flat 分支下机器型文档落 `.workflow/state/sessions/{req-id}/regressions/{reg-id}/`，对人文档 placeholder 落 artifacts/ 扁平根。**代码实现与契约一致**。

**结论**：artifacts-layout.md + CLI 两侧**契约本身与用户心智模型对齐**（机器型去 state，对人文档去 artifacts），**但执行出现偏差**——req-40 的 `requirement.md` 和 `acceptance-report.md` 并非通过 `create_requirement` 写入（否则应落 state）而是被手工写到 artifacts/，`需求摘要.md` 未产出。

## 4. Expected Outcome（用户期望，双解读）

**解读 A（激进）**：artifacts 只保留**原始 requirement.md + 真·对外文档**（SQL/部署/接入配置/交付总结），**废止 `需求摘要.md` / `变更简报.md` / `实施说明.md` / `回归简报.md` 四类对人 brief**（都是"给人看的处理过的"冗余）。

**解读 B（温和）**：artifacts 保留对人文档和 raw 需求，但"给人看的处理过的"特指现行分层命名（摘要 / 简报 / 说明）带来的冗余感；真正反对的是**机器型 `requirement.md` / `acceptance-report.md` 错位到 artifacts**，而非反对所有 brief。

## 5. Next Step

见 `analysis.md` §4（候选方向）+ `decision.md`（路由建议）。
