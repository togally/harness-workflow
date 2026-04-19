# Session Memory: chg-03-硬门禁集成

## Stage
executing

## 执行摘要
已完成在三个现有角色文件中植入硬门禁提示。

### 关键动作
- 读取 done.md、planning.md、executing.md
- 在三个文件的"完成前必须检查"列表末尾追加硬门禁检查项
- 验证插入后格式正确，未破坏原有结构

### 修改文件
- `.workflow/context/roles/done.md`：追加 done 阶段回顾触发清单更新的检查项
- `.workflow/context/roles/planning.md`：追加 planning 阶段新制品/新阶段触发清单更新的检查项
- `.workflow/context/roles/executing.md`：追加 executing 阶段新风险/新产出触发清单更新的检查项

## 关键决策
- 硬门禁提示放置于"完成前必须检查"区块，确保每个阶段的 subagent 在退出前都会看到
- 三个角色的提示措辞略有差异，分别对应各自阶段的典型变更触发场景

## 遇到的问题
- 无阻塞问题

## 下一步任务
- 进入 testing 阶段验证三个产物
