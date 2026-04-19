# Change Plan

## 1. Development Steps

1. 设计工具能力类型分类：
   - **读写型**：Read, Write, Edit, NotebookEdit（直接操作文件内容）
   - **执行型**：Bash（运行命令、编译、测试、Git 操作）
   - **搜索型**：Grep, Glob, WebSearch（查找文件/内容/网络信息）
   - **协调型**：Agent, Skill（派发 subagent、调用 skill）
   - **上下文管理型**：`/compact`, `/clear`, 新开 agent
2. 重构 `stage-tools.md` 各 stage：
   - **requirement_review / planning**：禁止执行型（Bash）、禁止读写型操作项目代码文件；推荐协调型、读写型（文档）
   - **executing**：无禁止（除基本原则外）；推荐执行型、读写型、搜索型
   - **testing**：禁止读写型（不得修改被测内容）；推荐执行型、搜索型、协调型
   - **acceptance**：禁止执行型、禁止读写型；推荐搜索型、协调型
   - **regression**：禁止读写型（确认问题前不得修复），执行型仅限只读命令；推荐搜索型、协调型
3. 在文件开头补充"新增工具默认规则"段落
4. 保留上下文管理通用规则和各 stage 的上下文管理建议

## 2. Verification Steps

1. 检查每个 stage 的"禁止"列表是否与重构前语义等价
   - requirement_review/planning：仍禁止 Bash、禁止写代码文件 ✓
   - testing：仍禁止 Write/Edit ✓
   - acceptance：仍禁止 Write/Edit/Bash ✓
   - regression：仍禁止 Write/Edit、Bash 只读 ✓
2. 检查文件开头是否有明确的"新增工具默认规则"
3. 检查文档结构是否清晰：能力类型定义 → 默认规则 → 各 stage 约束 → 上下文管理规则
