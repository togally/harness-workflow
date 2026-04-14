# chg-06 Session Memory — 制品仓库输出

## 执行状态
- [x] 步骤 1：分析 requirement.md 章节结构
- [x] 步骤 2：新增 _extract_section 辅助函数
- [x] 步骤 3：新增 generate_requirement_artifact 函数
- [x] 步骤 4：在 archive_requirement 末尾调用

## 关键决策
- `_extract_section` 匹配包含 heading 关键词的 `## ` 开头行（兼容数字前缀如 `## 2. Goal`）
- 同时尝试中英文关键词（Goal/目标，Scope/范围，Acceptance/验收）
- git_branch 在 generate_requirement_artifact 内部调用 `_get_git_branch(root)`（避免参数链路传递）
- req_title 从 `req_dir.name` 用 `re.sub(r"^req-\d+-", "", ...)` 提取
- artifact 生成失败用 try/except 捕获，打印 Warning 但不中断归档
- 空章节整体跳过（不输出空的 ## 标题）

## 修改位置
- `src/harness_workflow/core.py`：`_extract_section()`、`generate_requirement_artifact()` 在 list_done_requirements 之前
- `archive_requirement()` 末尾打印前调用 generate_requirement_artifact
