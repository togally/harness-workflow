# Change: chg-06 workflow 目录重命名为 .workflow/

## 关联需求
req-01 — 版本重做，AC-8

## 变更描述
将工作流目录从 `.workflow/` 重命名为 `.workflow/`，遵循 dotfile 约定。
同步更新全部 Python 源码、模板、slash command 文件及文档中的路径引用。
提供向后兼容迁移：`harness update` 自动检测并迁移旧目录。

## 变更范围

**Python 源码：**
- `src/harness_.workflow/core.py`：所有 `Path("workflow")` → `Path(".workflow")`
- `src/harness_.workflow/backup.py`：`BACKUP_BASE`、`PLATFORMS_FILE` 常量更新
- `core.py` `update_repo()`：增加迁移逻辑（.workflow/ → .workflow/）
- `core.py` `install_repo()`：写入 `.gitignore` `!.workflow/` 规则
- `src/harness_.workflow/assets/skill/tests/test_harness_cli.py`：路径断言更新
- `src/harness_.workflow/assets/skill/scripts/`：analyze_repo.py / lint_harness_repo.py 路径引用更新

**Scaffold：**
- `src/harness_.workflow/assets/scaffold_v2/.workflow/` 目录 → `scaffold_v2/.workflow/`
- scaffold_v2 内部文件中的 `.workflow/` 引用更新

**模板文件（src）：**
- `src/harness_.workflow/assets/skill/assets/templates/` 中 17 个含 `.workflow/` 引用的文件

**Slash command 文件（三端）：**
- `.qoder/commands/*.md`、`.claude/commands/*.md`、`.codex/skills/harness-*/SKILL.md`
- Hard Gate 路径：`.workflow/context/index.md` → `.workflow/context/index.md`
- Hard Gate 路径：`.workflow/state/runtime.yaml` → `.workflow/state/runtime.yaml`

**SKILL.md（三端）：**
- `.qoder/skills/harness/SKILL.md`、`.claude/skills/harness/SKILL.md`、`.codex/skills/harness/SKILL.md`

**根目录文档：**
- `WORKFLOW.md`、`AGENTS.md`、`CLAUDE.md`

**三端 skill assets 模板（同步）：**
- `.qoder/skills/harness/assets/templates/` 同上 17 个
- `.claude/skills/harness/assets/templates/` 同上
- `.codex/skills/harness/assets/templates/` 同上

**当前仓库物理目录：**
- `git mv .workflow/ .workflow/`（保留 git 历史）

## 验收条件
- [ ] 物理目录已重命名，`git status` 显示 rename 而非 delete+add
- [ ] `harness status` 可正常读取 `.workflow/state/runtime.yaml`
- [ ] `harness install` 在新仓库创建 `.workflow/` 而非 `.workflow/`
- [ ] `harness install` 写入 `.gitignore` 的 `!.workflow/` 规则
- [ ] `harness update` 对含 `.workflow/` 的旧仓库自动迁移到 `.workflow/`
- [ ] 现有测试套件全部通过
- [ ] 三端 slash command 文件 Hard Gate 路径已更新
