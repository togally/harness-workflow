# Change

## 1. Title
平台选择与检测更新（install 列表 + get_active_platforms + Hard Gate）

## 2. Goal
将 kimi 平台注册到整个平台生命周期管理体系中：`install_repo` 默认选项加入 kimi、`prompt_platform_selection` 展示 kimi 选项、`get_active_platforms` 识别 `.kimi/skills/` 目录、`get_platform_file_patterns` 返回 kimi 文件模式、`sync_platforms_state` 支持 kimi 的 backup/restore；同时在 `render_agent_command` Hard Gate 说明中增加 `.kimi/skills/harness/SKILL.md` 检查路径。

## 3. Requirement
- req-05-功能扩展

## 4. Scope
**包含**：
- `src/harness_workflow/backup.py`：`PLATFORM_CONFIGS` 字典增加 `kimi` 条目（`source: .kimi/skills/harness/SKILL.md`，`backup_dir: kimi`）
- `src/harness_workflow/backup.py`：`ALL_PLATFORMS` 列表加入 `"kimi"`
- `src/harness_workflow/backup.py`：`get_platform_file_patterns()` 的 `patterns` 字典增加 `"kimi": [".kimi/skills/"]`
- `src/harness_workflow/cli.py`：`prompt_platform_selection()` 的 `choices` 列表增加 kimi 选项（`name: "kimi (.kimi/skills/)"`, `value: "kimi"`, 默认 checked）
- `src/harness_workflow/core.py`：`install_repo()` 中新安装默认列表 `["codex", "qoder", "cc"]` 改为 `["codex", "qoder", "cc", "kimi"]`
- `src/harness_workflow/core.py`：`render_agent_command()` 中 Hard Gate 说明增加 `.kimi/skills/harness/SKILL.md` 检查路径

**不包含**：
- `render_kimi_command_skill()` 函数实现（属于 chg-01）
- `_managed_file_contents()` 中生成 kimi 文件（属于 chg-01）
- 修改 codex / qoder / cc 现有平台逻辑

## 5. Acceptance Criteria
- [ ] `ALL_PLATFORMS` 包含 `"kimi"`
- [ ] `PLATFORM_CONFIGS["kimi"]` 存在且 `source` 为 `.kimi/skills/harness/SKILL.md`
- [ ] `get_active_platforms()` 在 `.kimi/skills/harness/SKILL.md` 存在时返回 `kimi: True`
- [ ] `get_platform_file_patterns("kimi")` 返回 `[".kimi/skills/"]`
- [ ] `prompt_platform_selection()` 展示 kimi 选项且默认勾选
- [ ] 新仓库 `harness install` 默认启用 4 个平台（codex / qoder / cc / kimi）
- [ ] `render_agent_command()` Hard Gate 说明中包含 `.kimi/skills/harness/SKILL.md`

## 6. Dependencies
- **前置**：chg-01（render_kimi_command_skill 必须已实现，才能使生成动作有效）
- **后置**：无
