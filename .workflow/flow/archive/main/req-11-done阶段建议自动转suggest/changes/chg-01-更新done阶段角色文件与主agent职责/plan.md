# Plan: chg-01

## Steps

1. 读取当前 `done.md`
2. 在"完成前必须检查"或"输出规范建议"部分增加：
   - `done-report.md` 中的改进建议已提取为 suggest 文件（如存在）
3. 在"经验沉淀验证步骤"之后增加"建议转 suggest 验证步骤"
4. 读取 `WORKFLOW.md`
5. 在"done 阶段行为"中补充：主 agent 负责在保存 done-report 后调用建议提取逻辑
6. 保存修改

## Artifacts

- 更新后的 `.workflow/context/roles/done.md`
- 更新后的 `.workflow/WORKFLOW.md`

## Dependencies

- 无
