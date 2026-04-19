# Change: 清理旧系统残留文件

## 背景

验收时发现大量旧系统残留文件/目录未清理，包括空目录和旧文件。

## 目标

清理所有旧系统残留，保持目录结构整洁。

## 变更范围

删除以下空目录：
- `workflow/versions/active/`
- `workflow/decisions/`
- `workflow/runbooks/`
- `workflow/context/experience/architecture/`
- `workflow/context/experience/business/`
- `workflow/context/experience/debug/`
- `workflow/state/experience/constraints/`
- `workflow/state/experience/context/`
- `workflow/state/experience/evaluation/`
- `workflow/state/experience/flow/`
- `workflow/state/experience/state/`
- `workflow/state/experience/tools/`

删除以下旧文件：
- `workflow/memory/constitution.md`
- `workflow/memory/` 目录（清空后）

## 验收标准

- `find workflow/ -type d -empty` 无结果（空目录全部删除）
- `workflow/memory/` 目录不存在
- `workflow/decisions/` 目录不存在
- `workflow/runbooks/` 目录不存在
- `workflow/versions/active/` 目录不存在
