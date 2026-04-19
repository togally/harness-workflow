# 执行计划

## 依赖关系
- **前置依赖**：chg-01（render_kimi_command_skill 已实现）
- **后置依赖**：无

## 执行步骤

### 步骤 1：更新 backup.py 平台配置
1. 打开 `src/harness_workflow/backup.py`
2. 在 `PLATFORM_CONFIGS` 字典（第 16 行）中增加 kimi 条目：
   ```python
   "kimi": {
       "source": ".kimi/skills/harness/SKILL.md",
       "backup_dir": "kimi",
   }
   ```
3. 将 `ALL_PLATFORMS = ["codex", "qoder", "cc"]`（第 35 行）改为 `ALL_PLATFORMS = ["codex", "qoder", "cc", "kimi"]`
4. 在 `get_platform_file_patterns()` 的 `patterns` 字典（第 216 行）中增加：
   ```python
   "kimi": [
       ".kimi/skills/",
   ],
   ```

### 步骤 2：更新 cli.py 平台选择 UI
1. 打开 `src/harness_workflow/cli.py`
2. 在 `prompt_platform_selection()` 的 `choices` 列表（第 48 行）中增加第四个选项：
   ```python
   {
       "name": "kimi (.kimi/skills/harness/SKILL.md)",
       "value": "kimi",
       "checked": current_platforms is None or "kimi" in (current_platforms or [])
   },
   ```
3. 将非交互模式降级返回值（第 46 行）从 `["codex", "qoder", "cc"]` 改为 `["codex", "qoder", "cc", "kimi"]`

### 步骤 3：更新 core.py install_repo 默认列表
1. 定位 `install_repo()` 中新安装默认选择（第 2629 行）：
   ```python
   selected = ["codex", "qoder", "cc"]
   print("\nNew installation: enabling all platforms (codex, qoder, cc)")
   ```
2. 改为：
   ```python
   selected = ["codex", "qoder", "cc", "kimi"]
   print("\nNew installation: enabling all platforms (codex, qoder, cc, kimi)")
   ```
3. 同时更新回退默认值（第 2636 行）的相同列表

### 步骤 4：更新 render_agent_command Hard Gate 说明
1. 定位 `render_agent_command()` 函数（第 292 行）
2. 在中文和英文版的 Hard Gate 说明中，找到读取主 harness skill 的路径说明，增加 `.kimi/skills/harness/SKILL.md` 检查路径
3. 确保说明格式与现有 `.codex/skills/harness/SKILL.md` 引用保持一致

## 预期产物
1. `backup.py`：`PLATFORM_CONFIGS`、`ALL_PLATFORMS`、`get_platform_file_patterns` 均包含 kimi
2. `cli.py`：`prompt_platform_selection` 展示 kimi 选项
3. `core.py`：新安装默认启用 4 个平台，Hard Gate 包含 kimi 路径

## 验证方法
1. `python -c "from harness_workflow.backup import get_active_platforms, ALL_PLATFORMS; print(ALL_PLATFORMS)"` 输出包含 `"kimi"`
2. `python -c "from harness_workflow.backup import get_platform_file_patterns; print(get_platform_file_patterns('kimi'))"` 输出 `['.kimi/skills/']`
3. 在新 git 仓库执行 `harness install`，确认终端提示包含 kimi 平台，且默认勾选
4. 安装完成后检查 `.kimi/skills/` 目录已创建，各命令的 SKILL.md 存在

## 注意事项
1. `PLATFORM_CONFIGS["kimi"]["source"]` 的路径用于检测平台是否激活（`get_active_platforms`），必须与 chg-01 生成的 skill 文件路径匹配：`.kimi/skills/harness/SKILL.md`
2. backup/restore 逻辑通过 `PLATFORM_CONFIGS` 自动支持，只需添加 kimi 条目即可
3. `sync_platforms_state` 基于 `ALL_PLATFORMS` 和 `PLATFORM_CONFIGS` 工作，增加 kimi 后无需额外修改该函数
4. `render_agent_command` 的 Hard Gate 说明属于托管文件内容，修改后需 `harness update` 才能刷新已安装仓库的文件
