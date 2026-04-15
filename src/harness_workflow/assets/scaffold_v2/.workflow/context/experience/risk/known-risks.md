# Known Risks and Mitigations

## 风险一：tools/ 目录迁移后路径丢失

### 场景
req-02/chg-03 恢复 tools/ 工具层时，备份源路径已随 chg-04（context/backup → archive）迁移。

### 风险内容
如果 chg-03 和 chg-04 顺序调换，tools/ 的备份源 `context/backup/` 在 chg-04 完成后变成 `archive/`。
先找路径再做迁移；执行多个目录迁移变更时要注意彼此的依赖顺序。

### 缓解
- 任务开始前列出所有受影响路径
- 平行变更中若有路径依赖，应标记为串行执行

### 来源
req-02/chg-03 tools/ 迁移，实际备份位置 archive/legacy-cleanup/workflow/tools/

---

## 风险二：Edit 工具在未读取文件时拒绝写入

### 场景
req-02/chg-03 批量更新 6 个角色文件时，对未 Read 过的文件调用 Edit 工具失败。

### 风险内容
Edit 工具强制要求在同一会话中先 Read 目标文件，否则报 "file not read" 错误。
批量编辑多文件时，必须先并行 Read 所有目标文件，再做 Edit。

### 缓解
- 批量编辑前：一次并行 Read 所有目标文件
- Write 工具用于创建新文件或完整重写，Edit 用于局部修改

### 来源
req-02/chg-03 角色文件批量更新
