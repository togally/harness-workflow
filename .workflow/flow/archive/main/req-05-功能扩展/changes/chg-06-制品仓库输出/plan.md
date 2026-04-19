# 执行计划

## 依赖关系
- **前置依赖**：chg-05（归档目录已包含 sessions/ 和 state.yaml）
- **后置依赖**：无

## 执行步骤

### 步骤 1：了解 requirement.md 章节结构
1. 阅读现有需求的 `requirement.md`（如 req-05），确认章节标题格式（`## 2. Goal`、`## 3. Scope` 等）
2. 确认章节提取的边界条件：章节以 `## ` 开头，到下一个 `## ` 结束

### 步骤 2：新增 _extract_section 辅助函数
1. 在 `core.py` 中新增 `_extract_section(text: str, heading: str) -> str`：
   - 按行扫描，找到 `## {heading}` 开头的行
   - 收集直到下一个 `## ` 或文件结尾的内容
   - 返回章节内容（去除标题行本身），若未找到返回 `""`

### 步骤 3：新增 generate_requirement_artifact 函数
1. 在 `core.py` 中新增 `generate_requirement_artifact(root: Path, archive_target: Path, req_id: str, title: str, git_branch: str) -> Path`：

   **读取 requirement.md**：
   - 路径：`archive_target / "requirement.md"`
   - 提取 Goal、Scope、Acceptance Criteria 章节

   **读取各 change.md**：
   - 扫描 `archive_target / "changes" / "chg-*" / "change.md"`（按目录名排序）
   - 每个 change.md 提取 `## 1. Title` 和 `## 2. Goal`
   - 构造变更列表：`- **{chg-id}** {title}：{goal 第一句}`

   **读取关键决策**：
   - 扫描 `archive_target / "sessions" / "chg-*" / "session-memory.md"`（如有）
   - 提取 `## 关键决策` 或 `## Key Decisions` 章节内容
   - 合并各变更的决策记录

   **读取 design.md**（如有）：
   - 扫描 `archive_target / "sessions" / "chg-*" / "design.md"`
   - 提取摘要段落（前 200 字或首个 `##` 前内容）

   **读取 done-report.md**（如有）：
   - 路径：`archive_target / "sessions" / "done-report.md"`
   - 提取 `## 遗留问题` 或 `## Pending Issues` 章节

   **生成文档**：
   ```markdown
   # {title}

   > req-id: {req_id} | 完成时间: {date.today()} | 分支: {git_branch or "unknown"}

   ## 业务背景
   {Goal 章节内容}

   ## 需求目标
   {Goal 章节内容}  （如 Goal 同时涵盖背景和目标，可合并）

   ## 交付范围
   {Scope 章节内容}

   ## 验收标准
   {Acceptance Criteria 章节内容}

   ## 变更列表
   {变更列表}

   ## 关键设计决策
   {决策内容，如无则省略整节}

   ## 遗留问题与注意事项
   {done-report.md 遗留问题，如无则省略整节}
   ```

2. 输出路径：`root / "artifacts" / "requirements" / f"{req_id}-{title}.md"`
3. 创建 `artifacts/requirements/` 目录（`mkdir(parents=True, exist_ok=True)`）
4. 写入文件，返回输出路径

### 步骤 4：在 archive_requirement 中调用
1. 定位 `archive_requirement()` 末尾（打印归档路径之后）
2. 增加调用（需传入 git_branch，可从已计算的 folder 值反推，或重新读取）：
   ```python
   artifact_path = generate_requirement_artifact(root, target, archived_req_id, title, git_branch)
   print(f"Generated artifact: {artifact_path}")
   ```

## 预期产物
1. `core.py`：`_extract_section()`、`generate_requirement_artifact()` 函数
2. 归档后 `artifacts/requirements/{req-id}-{title}.md` 文件自动生成

## 验证方法
1. 对有完整 sessions 的 req-xx 执行 `harness archive`
2. 确认 `artifacts/requirements/` 目录被创建
3. 打开生成的 `.md` 文件，确认包含：标题元数据、需求目标、变更列表
4. 对缺少 sessions 或 done-report.md 的旧需求执行，确认不报错且生成基础摘要

## 注意事项
1. `_extract_section` 的标题匹配需要灵活处理数字前缀（`## 2. Goal` vs `## Goal`）—— 建议匹配包含关键词的标题行（`if "Goal" in line`）
2. title 在文件名中可能含中文或特殊字符，写入路径时 `mkdir/open` 在 macOS/Linux 均支持 UTF-8 路径
3. git_branch 需在 `archive_requirement` 中传递给此函数，或在函数内部重新调用 `_get_git_branch(root)`（后者更简单，避免参数链路过长）
4. 生成文档时，若某章节内容为空，对应的 `##` 标题也省略（不写空节）
5. `artifacts/` 目录只初始化 `requirements/` 子目录，其余（sql/、api/ 等）用户自行管理，不自动创建
