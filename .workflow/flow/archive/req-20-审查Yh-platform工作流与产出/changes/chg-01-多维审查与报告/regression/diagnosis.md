# Regression Diagnosis: req-20 审查报告遗漏制品仓库检查

## 触发来源
用户在 req-20 完成后提出质疑："我记得我们完成需求之后应该要有制品仓库？为什么没有输出了？你为什么没有审查到？"

## 问题描述
req-20 的审查报告在"维度五：制品完整性"中，仅审查了 `.workflow/` 内部的流程文档产物（requirement.md、change.md、plan.md、session-memory.md、done-report.md、regression/diagnosis.md、归档产物等），**完全没有检查 Harness 工作流规范中定义的 `artifacts/requirements/` 制品仓库目录**。

根据 harness-workflow 项目 req-05（功能扩展）的规范，`harness archive` 命令应在项目根目录的 `artifacts/requirements/` 下自动生成需求摘要文档（`{req-id}-{title}.md`），聚合 requirement.md、change.md、session-memory.md、done-report.md 等内容，供未参与过该需求的开发者快速接手。

## 根因分析
1. **审查范围定义过窄**：req-20 的 change.md 和 plan.md 将"制品"定义为".workflow 内部的文档产物"，未明确将根目录 `artifacts/` 纳入审查范围。
2. **审查执行时的路径扫描遗漏**：executing 阶段的 subagent 在扫描 Yh-platform 的产出时，使用了 `find .workflow/...` 和检查 archive/requirements 的思路，但没有检查项目根目录的 `artifacts/`。
3. **版本基线未确认**：未先确认 Yh-platform 使用的 Harness 工作流版本是否包含"制品仓库"功能（该功能在当前 harness-workflow 的 req-05 功能扩展中引入，但 Yh-platform 可能未同步此版本）。

## 实地检查结果
- `/Users/jiazhiwei/IdeaProjects/Yh-platform/artifacts/`：**不存在**
- Yh-platform 的 req-01 ~ req-05 归档后，根目录下均未生成 `artifacts/requirements/{req-id}-{title}.md`

## 问题分类
**审查遗漏 / 实现缺失** — 双重问题：
1. req-20 审查报告漏检了制品仓库这一重要维度；
2. Yh-platform 项目实际也未产出 artifacts/ 制品仓库（可能因为使用的是旧版 Harness 或未启用该功能）。

## 路由决定
路由到 `executing` 阶段，任务：
1. 修正 `review-report.md`，在"维度五：制品完整性"中补充 `artifacts/requirements/` 的检查结果
2. 更新 `session-memory.md` 记录此 regression
3. 如有必要，修正 `done-report.md` 的对应章节

## 修复记录（2026-04-15）

1. **修正 review-report.md**：
   - 在 req-01 ~ req-05 的"维度五：制品完整性"清单中，每条增加 `artifacts/requirements/` 行，状态均为"否 / 未找到"
   - 在"缺失/评价"段落中补充说明"根目录未生成 artifacts/requirements/ 制品仓库摘要"
   - 在"存在的问题"中新增第 6 点："制品仓库（artifacts/requirements/）完全缺失"
   - 在"改进建议"中新增第 7 点："补齐制品仓库（artifacts/requirements/）输出"
   - 修正最终结论中遗漏的"14 个 OSD 字段"为"13 个"

2. **更新 session-memory.md**：
   - 新增"Regression 阶段结果"区块，记录用户触发原因、问题确认、根因分析和修正动作

3. **更新 done-report.md**：
   - 在"流程完整性评估"中补充 regression 后修正说明
   - 在"改进建议"中新增"将 artifacts/requirements/ 制品仓库纳入 done 阶段六层回顾检查的必检项"

4. **新增 suggest 文件**：
   - `suggest-05-mandatory-artifacts-check.md`

5. **状态更新**：
   - `runtime.yaml` 从 `regression` 重新推进到 `done`

**修复完成，审查报告已更新。**
