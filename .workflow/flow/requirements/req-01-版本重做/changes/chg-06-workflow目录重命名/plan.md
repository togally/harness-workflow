# Plan: chg-06 workflow 目录重命名为 .workflow/

## 执行顺序说明

必须先改 Python 源码（Step 1-3），再重命名物理目录（Step 4），
再更新所有 Markdown/模板（Step 5-7），最后验证（Step 8）。
Step 4 之后 `harness` CLI 将立即使用新路径，顺序不可颠倒。

---

### Step 1 — core.py：路径常量替换

目标：将 `core.py` 中所有 `Path("workflow")` 改为 `Path(".workflow")`

- 全量替换：`Path("workflow")` → `Path(".workflow")`（约 22 处，含 LEGACY_CLEANUP_TARGETS 列表）
- 同步更新 `STATE_RUNTIME_PATH`、`LEGACY_WORKFLOW_RUNTIME_PATH`、`LEGACY_CLEANUP_ROOT`
- 同步更新 `SCAFFOLD_V2_ROOT` 下游所有路径（若有硬编码）
- 更新 `required` 检查列表（`install_repo` 中校验目录存在的逻辑）

验证：`grep -c 'Path("workflow")' src/harness_.workflow/core.py` 输出 0

### Step 2 — backup.py：路径常量替换

- `BACKUP_BASE = ".workflow/context/backup"` → `".workflow/context/backup"`
- `PLATFORMS_FILE = ".workflow/state/platforms.yaml"` → `".workflow/state/platforms.yaml"`

验证：`grep '.workflow/' src/harness_.workflow/backup.py` 输出空

### Step 3 — core.py：新增两段逻辑

**3a. `update_repo()` 迁移逻辑**（在函数入口早期执行）：
```python
# 向后兼容迁移：.workflow/ → .workflow/
old_dir = root / "workflow"
new_dir = root / ".workflow"
if old_dir.exists() and not new_dir.exists():
    old_dir.rename(new_dir)
    print(f"Migrated {old_dir} → {new_dir}")
```

**3b. `install_repo()` .gitignore 规则**（在写入文件后追加）：
- 读取 `root / ".gitignore"`（不存在则创建）
- 若文件中不含 `!.workflow/`，则追加：
  ```
  # harness workflow directory (must not be ignored)
  !.workflow/
  ```

验证：单元测试覆盖迁移逻辑 + .gitignore 写入

### Step 4 — 物理目录重命名

```bash
git mv .workflow/ .workflow/
```

验证：`git status` 显示 `renamed: .workflow/... → .workflow/...`，不显示 untracked

### Step 5 — Scaffold 目录重命名 + 内部引用更新

- 将 `src/harness_.workflow/assets/scaffold_v2/.workflow/` 整体移动为 `scaffold_v2/.workflow/`
- 扫描 scaffold_v2 内部文件，替换 `.workflow/` → `.workflow/`（若有）

验证：`ls src/harness_.workflow/assets/scaffold_v2/` 只见 `.workflow/`，不见 `.workflow/`

### Step 6 — 模板文件批量替换（四份：src + 三端 skill assets）

替换范围：
- `src/harness_.workflow/assets/skill/assets/templates/*.tmpl`（17 个含引用文件）
- `.qoder/skills/harness/assets/templates/*.tmpl`
- `.claude/skills/harness/assets/templates/*.tmpl`
- `.codex/skills/harness/assets/templates/*.tmpl`

替换内容：`.workflow/` → `.workflow/`（路径引用）

验证：`grep -r '.workflow/' src/.../templates/` 输出空（排除含 "workflow" 词的非路径文本）

### Step 7 — Markdown 文件批量替换

7a. **根目录文档**（`WORKFLOW.md`、`AGENTS.md`、`CLAUDE.md`）：
- `.workflow/context/index.md` → `.workflow/context/index.md`
- `.workflow/state/runtime.yaml` → `.workflow/state/runtime.yaml`
- `.workflow/constraints/boundaries.md` → `.workflow/constraints/boundaries.md`
- 其余所有 `.workflow/` 路径引用

7b. **Slash command 文件（三端，~56 个）**：
- Hard Gate 中：`.workflow/context/index.md` → `.workflow/context/index.md`
- Hard Gate 中：`.workflow/state/runtime.yaml` → `.workflow/state/runtime.yaml`

7c. **SKILL.md（三端）**：
- `.qoder/skills/harness/SKILL.md`、`.claude/skills/harness/SKILL.md`、`.codex/skills/harness/SKILL.md`
- 同上路径替换

7d. **辅助脚本**：
- `src/harness_.workflow/assets/skill/scripts/analyze_repo.py`
- `src/harness_.workflow/assets/skill/scripts/lint_harness_repo.py`

验证：`grep -r '".workflow/' .qoder/ .claude/ .codex/ WORKFLOW.md AGENTS.md CLAUDE.md` 输出空

### Step 8 — 测试验证

```bash
cd /Users/jiazhiwei/claudeProject/harness-workflow
python -m pytest src/harness_.workflow/assets/skill/tests/test_harness_cli.py -v
```

- 若有路径断言失败：更新 test_harness_cli.py 中的 `.workflow/` → `.workflow/`
- 全部通过后完成

## 产物清单
- 修改：`src/harness_.workflow/core.py`
- 修改：`src/harness_.workflow/backup.py`
- 修改：`src/harness_.workflow/assets/skill/tests/test_harness_cli.py`
- 修改：`src/harness_.workflow/assets/skill/scripts/analyze_repo.py`
- 修改：`src/harness_.workflow/assets/skill/scripts/lint_harness_repo.py`
- 移动：`scaffold_v2/.workflow/` → `scaffold_v2/.workflow/`
- 修改：17 个模板文件（四份 × 位置）
- 修改：~56 个 slash command 文件 + 3 个 SKILL.md
- 修改：`WORKFLOW.md`、`AGENTS.md`、`CLAUDE.md`
- git mv：`.workflow/` → `.workflow/`

## 依赖
- 无前置变更依赖
- Step 1-3 必须在 Step 4 之前完成
- Step 5-7 可在 Step 4 之后任意顺序执行
