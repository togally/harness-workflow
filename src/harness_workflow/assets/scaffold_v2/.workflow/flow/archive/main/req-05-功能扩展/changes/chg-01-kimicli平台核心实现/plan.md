# 执行计划

## 依赖关系
- **前置依赖**：无
- **后置依赖**：chg-02（平台选择与检测更新）

## 执行步骤

### 步骤 1：分析 render_codex_command_skill 格式
1. 阅读 `core.py` 第 378 行起的 `render_codex_command_skill()` 函数，理解 codex skill 的 YAML frontmatter + Markdown 结构
2. 确认 `command_specific_guidance()` 函数的调用方式和返回格式
3. 确认中英双语切换逻辑（`normalize_language(language) == "cn"`）

### 步骤 2：新增 render_kimi_command_skill 函数
1. 在 `core.py` 中，紧邻 `render_codex_command_skill()` 之后（约第 450 行之后），新增 `render_kimi_command_skill(command_name: str, cli_command: str, language: str) -> str` 函数
2. 函数结构：
   - YAML frontmatter：`---` / `name: {command_name}` / `description: "{描述}"` / `---`
   - Markdown 正文：Hard Gate 说明（引用 `.kimi/skills/harness/SKILL.md`，而非 `.codex/skills/harness/SKILL.md`）
   - 执行规则：与 codex skill 格式相同，但平台路径改为 `.kimi/skills/harness/SKILL.md`
3. 中文模式下生成中文版说明，英文模式下生成英文版说明
4. 调用 `command_specific_guidance(command_name, language)` 补充命令特定说明（与 codex skill 保持一致）

### 步骤 3：更新 _managed_file_contents 函数
1. 定位 `_managed_file_contents()` 函数（第 1944 行）
2. 在 for 循环内（第 1953-1959 行），紧接 `.codex/skills/{name}/SKILL.md` 条目之后，增加：
   ```python
   managed[f".kimi/skills/{command['name']}/SKILL.md"] = render_kimi_command_skill(
       command["name"], command["cli"], language
   )
   ```

## 预期产物
1. `core.py` 新增 `render_kimi_command_skill()` 函数（约 50-70 行）
2. `_managed_file_contents()` 中每个命令对应 `.kimi/skills/{name}/SKILL.md` 条目

## 验证方法
1. 运行 `python -c "from harness_workflow.core import render_kimi_command_skill; print(render_kimi_command_skill('harness', 'harness enter', 'cn'))"` 确认输出包含合法 YAML frontmatter
2. 检查输出的 `---` 开头和 `name:`、`description:` 字段
3. 检查 Hard Gate 说明中引用的是 `.kimi/skills/harness/SKILL.md` 而非 `.codex/` 路径
4. 用 `harness install --root /tmp/test-kimi` 测试（需 chg-02 完成后才能完整验证）

## 注意事项
1. kimi skill 格式参考 kimicli 官方文档：YAML frontmatter 在文件顶部，`name` 和 `description` 是必填字段
2. Hard Gate 中的主 skill 路径从 `.codex/skills/harness/SKILL.md` 改为 `.kimi/skills/harness/SKILL.md`
3. `command_specific_guidance()` 函数直接复用，不修改其实现
4. 不修改 `render_codex_command_skill()` 和现有 codex/qoder/cc 相关逻辑
