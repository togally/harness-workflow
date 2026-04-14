# chg-04 执行计划

## 依赖
依赖 chg-03（tools/ 内容已从 backup 迁移完成后再移动目录）

## 步骤

### Step 1：扫描路径引用
Grep 搜索 `context/backup` 在整个 `.workflow/` 中的引用，记录位置。

### Step 2：执行目录移动
Bash: `mv .workflow/context/backup .workflow/archive`

### Step 3：更新路径引用（如有）
根据 Step 1 结果，编辑相关文件中的路径。

### Step 4：验证
- `ls .workflow/archive/` 确认内容完整
- `ls .workflow/context/` 确认 backup 已不存在

## 产物
- `.workflow/archive/`（含原 backup 内容）
- `.workflow/context/backup/` 已删除
