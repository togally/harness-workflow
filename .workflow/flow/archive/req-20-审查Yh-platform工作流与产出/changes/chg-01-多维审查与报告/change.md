# Change

## 1. Title

多维审查与报告：Yh-platform 项目 Harness 工作流与产出审查

## 2. Goal

对目标项目 `/Users/jiazhiwei/IdeaProjects/Yh-platform` 的 req-01 至 req-05 共 5 个需求，从 5 个维度进行全面审查并输出审查报告：
1. 流程是否符合标准（阶段流转、跳过、合规）
2. 是否有经验产出，哪些目前没有经验产出及原因
3. bug 多不多、有没有反思
4. 工具有没有新增
5. 需求结束后是否有制品产生（done-report、session-memory、changes、归档产物等）

## 3. Requirement

- `req-20-审查Yh-platform工作流与产出`

## 4. Scope

### Included
- 审查 req-01 至 req-05 的全部流程记录（state yaml、archive/requirements 目录、state/sessions 目录）
- 审查每个需求的阶段流转完整性（requirement_review / planning / executing / testing / acceptance / done / regression）
- 审查 `.workflow/context/experience/` 下的经验文件更新情况
- 审查 `.workflow/tools/` 下的工具新增或变更情况
- 审查每个需求的制品产出（done-report、session-memory、changes、test-report、acceptance-report、regression/diagnosis 等）
- 输出一份综合审查报告（Markdown），覆盖上述 5 个维度

### Excluded
- 不修改 Yh-platform 项目的任何代码或文档
- 不创建 change.md / plan.md 以外的文件（本变更的报告产物可在 executing 阶段按流程输出到指定位置）
- 不修复 Yh-platform 中发现的问题（仅记录并报告）

## 5. Acceptance Criteria

- [ ] 审查报告覆盖 req-01 至 req-05 全部 5 个需求
- [ ] 报告包含 5 个维度的逐项分析结论
- [ ] 对每个维度给出“整体评价”和“改进建议”
- [ ] 列出发现的问题清单（如有），标注严重程度和关联需求
