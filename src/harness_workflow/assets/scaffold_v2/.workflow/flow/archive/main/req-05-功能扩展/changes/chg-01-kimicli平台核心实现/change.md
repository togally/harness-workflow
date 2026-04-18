# Change

## 1. Title
kimicli 平台核心实现（render_kimi_command_skill + _managed_file_contents）

## 2. Goal
在 `core.py` 中新增 `render_kimi_command_skill()` 函数，生成符合 kimicli 格式（YAML frontmatter + Markdown）的 `.kimi/skills/{command}/SKILL.md`；并在 `_managed_file_contents()` 中为所有 `COMMAND_DEFINITIONS` 生成 kimi skills，使 harness 能够向 kimicli 平台输出托管的 skill 文件。

## 3. Requirement
- req-05-功能扩展

## 4. Scope
**包含**：
- `src/harness_workflow/core.py`：新增 `render_kimi_command_skill(command_name, cli_command, language)` 函数
- `src/harness_workflow/core.py`：`_managed_file_contents()` 中增加 `.kimi/skills/{command_name}/SKILL.md` 条目（每个 COMMAND_DEFINITIONS 条目生成一个）
- kimi skill 文件格式：YAML frontmatter（name / description 字段） + Hard Gate 说明 + 执行规则 Markdown 正文
- 支持中英双语（`normalize_language` 判断）

**不包含**：
- `backup.py` / `get_active_platforms` / `get_platform_file_patterns` 中的 kimi 平台识别（属于 chg-02）
- install 选择列表中加入 kimi（属于 chg-02）
- kimicli Flow Skills（`type: flow`）支持
- 修改 codex / qoder / cc 现有平台逻辑

## 5. Acceptance Criteria
- [ ] `render_kimi_command_skill()` 函数存在于 `core.py`，签名为 `(command_name: str, cli_command: str, language: str) -> str`
- [ ] 输出内容包含合法 YAML frontmatter（`---` 开头，含 `name` 和 `description` 字段）
- [ ] `_managed_file_contents()` 中每个 COMMAND_DEFINITIONS 条目均生成 `.kimi/skills/{name}/SKILL.md`
- [ ] 中文语言模式下生成中文说明，英文模式下生成英文说明
- [ ] Hard Gate 说明引用 `.kimi/skills/harness/SKILL.md` 路径（非 `.codex/skills/harness/SKILL.md`）

## 6. Dependencies
- **前置**：无
- **后置**：chg-02（平台选择与检测需要 kimi 核心实现完成后才能注册平台）
