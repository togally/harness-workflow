# Change Plan

## 1. Development Steps

1. 通读 `catalog/` 下所有 `.md` 文件
2. 重点审查 `find-skills.md`：
   - 当前描述：`skillhub find-skills --query ...` 或按 skill 自身定义调用
   - 需要补充：在 Claude Code 中通过 `Skill` 工具调用 `find-skills`
   - 修正 "前提条件" 部分，说明 `find-skills` 作为 skill 需被系统识别
3. 审查其他 catalog 文档的准确性：
   - `bash.md`：确认 "regression 阶段只读命令" 的约束仍然有效
   - `agent.md`：确认 subagent 启动无历史上下文的描述仍然准确
   - `read.md`、`edit.md`、`grep.md`：确认适用/不适用场景无过时信息
4. 对需要修正的文档进行精确编辑

## 2. Verification Steps

1. 逐条检查 `find-skills.md` 的调用方式段落，确认包含 Claude Code `Skill` 调用示例
2. 检查所有被修改过的 catalog 文档，确认无破坏性改动
3. 确认文档中提到的工具行为与当前 Harness Workflow 的约束一致
