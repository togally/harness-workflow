# Plan: chg-02

## Steps

1. 读取当前 `context/roles/done.md`
2. 在 "输出规范建议" 或 "报告内容结构" 部分增加"实现时长"条目
3. 设计 `done-report.md` 头部时长区块格式：
   ```markdown
   ## Implementation Duration

   - **Total**: {x}h {y}m
   - **requirement_review**: {x}h {y}m
   - **planning**: {x}h {y}m
   - **executing**: {x}h {y}m
   - **testing**: {x}h {y}m
   - **acceptance**: {x}h {y}m
   - **done**: {x}h {y}m
   ```
4. 说明时长数据来源：`state/requirements/{id}.yaml` 中的 `started_at`、`completed_at`、`stage_timestamps`
5. 说明降级展示：缺失阶段显示 "N/A"
6. 可选：在 `testing.md` 和 `acceptance.md` 中补充报告头部也可包含"截至当前已用时长"的说明
7. 检查所有模板的一致性

## Artifacts

- 更新后的 `.workflow/context/roles/done.md`
- 可选更新的 `.workflow/context/roles/testing.md` 和 `.workflow/context/roles/acceptance.md`

## Dependencies

- 依赖 chg-01 的数据采集方案
