# chg-04 迁移 context/backup/ 目录

## 目标

将 `context/backup/` 移至 `.workflow/archive/`，使 `context/` 只包含知识内容，不包含历史存档。

## 范围

### 操作
- 移动 `.workflow/context/backup/` → `.workflow/archive/`
- 检查是否有文件引用了 `context/backup/` 路径，如有则更新

### 不修改
- archive 目录内的文件内容
- 其他任何文件（除非有路径引用需要更新）

## 验收标准

- [ ] `.workflow/context/backup/` 不存在
- [ ] `.workflow/archive/` 已创建，内容与原 `context/backup/` 一致
- [ ] 项目中无悬空的 `context/backup/` 路径引用
