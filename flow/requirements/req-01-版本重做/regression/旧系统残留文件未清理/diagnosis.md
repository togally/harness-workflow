## 问题描述

验收时发现大量旧系统残留文件/目录未清理。

## 证据

**空目录残留（旧系统）：**
- `workflow/versions/active/`（新系统已用 `flow/requirements/`）
- `workflow/decisions/`（新系统无此结构）
- `workflow/runbooks/`（新系统无此结构）
- `workflow/context/experience/architecture/`（空）
- `workflow/context/experience/business/`（空）
- `workflow/context/experience/debug/`（空）

**空目录残留（新系统误建）：**
- `workflow/state/experience/constraints/`（应为 `workflow/constraints/`）
- `workflow/state/experience/context/`（应为 `workflow/context/`）
- `workflow/state/experience/evaluation/`（应为 `workflow/evaluation/`）
- `workflow/state/experience/flow/`（应为 `workflow/flow/`）
- `workflow/state/experience/state/`（误嵌套）
- `workflow/state/experience/tools/`（应为 `workflow/tools/`）

**旧文件残留：**
- `workflow/memory/constitution.md`（旧版内容，新系统已有 `state/constitution.md`）
- `workflow/memory/` 目录本身

## 根因分析

Chg-07（新版系统构建）创建了 `workflow/state/experience/` 下的空子目录（可能是测试或手动操作误建），未清理旧系统的 `versions/active/`、`decisions/`、`runbooks/` 等目录，也未清理 `memory/constitution.md`。

## 结论

- [x] 真实问题

## 路由决定

- 问题类型：实现/测试（清理遗漏）
- 目标阶段：executing（作为新 change 实现）

## 需要人工提供的信息

无，根因明确，清理清单已确定。
