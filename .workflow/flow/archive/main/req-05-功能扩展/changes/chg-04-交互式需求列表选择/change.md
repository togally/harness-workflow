# Change

## 1. Title
交互式需求列表选择（archive 弹列表/预选，enter 无参弹列表）

## 2. Goal
改造 `harness archive` 和 `harness enter` 命令的交互模式：archive 无论是否传入 req-id 均弹出 done 需求列表（传入时预选），enter 无参数时弹出 active 需求列表；减少输入错误，提升操作可发现性。

## 3. Requirement
- req-05-功能扩展

## 4. Scope
**包含**：
- `src/harness_workflow/cli.py`：`archive` 子命令的 `requirement` 参数改为可选（`nargs="?"`）
- `src/harness_workflow/cli.py`：`enter` 子命令增加可选 `req_id` 位置参数
- `src/harness_workflow/cli.py`：新增 `prompt_requirement_selection(requirements, preselect=None)` 函数，使用 `questionary.select` 实现交互式列表选择
- `src/harness_workflow/core.py`：`archive_requirement()` 调用前在 CLI 层获取并校验 req-id（或在 core 层新增 `list_done_requirements(root)`）
- `src/harness_workflow/core.py`：`enter_workflow()` 无参数时读取 active 需求列表并弹出选择
- 列表格式：`[序号] req-xx 标题（阶段）`，如 `req-05 功能扩展（done）`
- 无可选项时打印明确提示，不弹空列表

**不包含**：
- `harness status`、`harness regression`、`harness requirement` 等其他命令的交互式选择
- 归档完整迁移逻辑（属于 chg-05）

## 5. Acceptance Criteria
- [ ] `harness archive`（无 req-id）弹出 done 需求列表，无 done 需求时打印提示并退出
- [ ] `harness archive req-xx`（已传 req-id）弹出列表且预选中该项，用户确认后执行
- [ ] `harness enter`（无 req-id）弹出 active 需求列表供选择
- [ ] `harness enter req-xx`（已传 req-id）直接进入，不弹列表
- [ ] 列表项格式：`req-xx 标题（阶段）`
- [ ] 非 TTY 环境（CI）下无交互传参时按原有行为执行，不阻塞

## 6. Dependencies
- **前置**：chg-03（archive_requirement 已支持 git branch 默认 folder）
- **后置**：chg-05（归档完整迁移在交互选择完成后叠加到同一函数）
