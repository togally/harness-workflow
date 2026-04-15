# Change

## 1. Title
制品仓库 artifacts/requirements/ 输出

## 2. Goal
归档时在根目录 `artifacts/requirements/` 下自动生成需求摘要文档 `{req-id}-{title}.md`，聚合 requirement.md、各 change.md、session-memory.md、done-report.md 等内容，让未参与过该需求的开发者能快速了解业务背景、目标、实现决策并接手后续开发。

## 3. Requirement
- req-05-功能扩展

## 4. Scope
**包含**：
- `src/harness_workflow/core.py`：新增 `generate_requirement_artifact(root, archive_target, req_id, title, git_branch)` 函数
- 读取来源（从归档目录读取，因 chg-05 已完成迁移）：
  - `{archive_target}/requirement.md`：提取 Goal、Scope、Acceptance Criteria 章节
  - `{archive_target}/changes/chg-*/change.md`：提取各变更标题和 Goal
  - `{archive_target}/sessions/chg-*/session-memory.md`（如有）：提取关键决策
  - `{archive_target}/sessions/done-report.md`（如有）：提取遗留问题
  - `{archive_target}/sessions/chg-*/design.md`（如有）：摘要核心设计
- 输出：`{root}/artifacts/requirements/{req-id}-{title}.md`
- `artifacts/requirements/` 目录在首次运行时自动创建
- `src/harness_workflow/core.py`：`archive_requirement()` 在迁移完成后调用 `generate_requirement_artifact()`

**不包含**：
- `artifacts/` 下其他子目录的创建或管理
- 对 requirement.md 格式的验证（按存在的章节提取，缺失章节省略）
- 修改 chg-01 到 chg-05 已实现的功能

## 5. Acceptance Criteria
- [ ] 归档后 `artifacts/requirements/{req-id}-{title}.md` 被创建
- [ ] 文档包含：业务背景/需求目标（来自 requirement.md Goal）、交付范围（Scope）、验收标准（Acceptance Criteria）
- [ ] 文档包含变更列表（各 chg-xx 标题 + Goal 一句话说明）
- [ ] 文档包含关键设计决策（来自 session-memory.md 的决策记录，如有）
- [ ] 文档包含遗留问题（来自 done-report.md，如有；无则省略该章节）
- [ ] 文档头部元数据：`req-id: {req-id} | 完成时间: {date} | 分支: {git-branch}`
- [ ] `artifacts/requirements/` 目录在首次归档时自动创建
- [ ] 来源文件不存在时对应章节优雅省略，不报错

## 6. Dependencies
- **前置**：chg-05（归档目录结构已包含 sessions/ 和 state.yaml，可从归档目录读取完整信息）
- **后置**：无
