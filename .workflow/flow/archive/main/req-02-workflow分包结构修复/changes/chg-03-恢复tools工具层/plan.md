# chg-03 执行计划

## 依赖
无（建议先于 chg-04）

## 步骤

### Step 1：读取 backup 源文件
逐一读取 `.workflow/context/backup/legacy-cleanup/workflow/tools/` 下所有文件。

### Step 2：创建目录结构
Bash: `mkdir -p .workflow/tools/catalog`

### Step 3：迁移文件
- index.md、maintenance.md、stage-tools.md（无路径更新）
- selection-guide.md（更新 `workflow/` → `.workflow/` 路径引用）
- catalog/ 下所有文件

### Step 4：更新角色文件 `## 可用工具` 小节
逐一读取再编辑 6 个角色文件，将内联白名单替换为引用 `tools/stage-tools.md` 的一行说明。

## 产物
- `.workflow/tools/`（完整目录）
- 6 个角色文件（`## 可用工具` 已更新）
