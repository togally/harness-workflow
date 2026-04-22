# Regression Diagnosis

## Issue

`harness suggest --apply <id>` 若建议正文为单行长句且含 `/`（或 `harness requirement "<含 / 的 title>"` 直接触发），需求工作区目录会被拆成多级嵌套，同时污染 `.workflow/state/requirements/` 与 `runtime.yaml`。（原 reg-01 已 cancel，归档备份在 `/tmp/reg-01-backup/`，已转本 bugfix。）

## Root Cause Analysis

两处缺陷组合触发（代码均在 `src/harness_workflow/workflow_helpers.py`）：

1. **`apply_suggestion` L3100-3103**：
   ```python
   body = target.read_text(encoding="utf-8").split("---", 2)[-1].strip()
   title = body.splitlines()[0].strip() if body else suggest_id
   result = create_requirement(root, title)
   ```
   - `splitlines()[0]` 对无换行的单行建议等于整段；无长度上限。
2. **`create_requirement` L3275/L3290**（关键）：
   ```python
   dir_name = f"{req_num_id}-{requirement_title}"
   requirement_dir = root / "artifacts" / branch / "requirements" / dir_name
   state_file = root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
   ```
   - 直接拼 raw title 到 Path，**未调 `slugify_preserve_unicode`**、无长度上限。title 含 `/` → Path 自动按分隔符拆成嵌套目录。
3. **`create_bugfix` L3337/L3375** 同款缺陷，但当前案例未触发（因本 bugfix 标题手工避开了 `/`）。
4. **附加缺口**：`apply_suggestion` 成功后 sug 文件仅改 frontmatter，未搬到 `flow/suggestions/archive/`，与 sug-06 等历史归档惯例不一致。

对比（已正确使用 `slugify_preserve_unicode` 的函数）：`create_change`（L3453）、`create_regression`（L3505）、`rename_requirement/change/bugfix`（L3783/L3864/L3908）。`create_requirement` + `create_bugfix` 是继承链中的两个漏补点。

## Routing Direction

- [x] Real issue → proceed to fix（已在本 bugfix 内继续）
- [ ] False positive → revert to previous stage

## Required Inputs

- 无需人工外部输入。根因与修复点明确，全部为 CLI 源码改动 + 已补的回归清理动作。

## Context Already Rolled Back

在进入 bugfix-3 前已执行：
- 删除 `artifacts/main/requirements/req-30-清理 .workflow/` 与 `.workflow/state/requirements/req-30-清理 .workflow/`（两处 3 级脏嵌套）
- `runtime.yaml` 回退为 pre-apply 状态（`current_requirement=""`, `stage=done`, `active_requirements=[]`, `operation_target=req-29`），随后由 `harness bugfix` 切换至 bugfix-3
- `sug-08` frontmatter `applied` → `pending`
- reg-01 原 4 份诊断文档备份于 `/tmp/reg-01-backup/`
