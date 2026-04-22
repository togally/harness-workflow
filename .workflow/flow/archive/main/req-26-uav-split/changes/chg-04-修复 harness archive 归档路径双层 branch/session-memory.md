# Session Memory

## 1. Current Goal

- Describe the current goal for this change.

## 2. Current Status

- Summarize what is already done.

## 3. Validated Approaches

- Record commands, checks, or decisions that already worked.

## 4. Failed Paths

- Attempt:
- Failure reason:
- Reminder: do not retry this blindly unless assumptions change.

## 5. Candidate Lessons

```markdown
### [date] [summary]
- Symptom:
- Cause:
- Fix:
```

## 6. Next Steps

- Add the next actions here.

## 7. Open Questions

- Add unresolved questions here.

## 执行记录

### 2026-04-19 — chg-04 executing（Subagent-L1 开发者）

**目标**：修 `harness archive` 归档路径双层 branch（覆盖 AC-05）。

**Bug 活证定位**：
- `resolve_archive_root(root)` 在 primary 形态返回 `artifacts/{branch}/archive`（L4219-L4244），branch 段已经烙在路径里。
- `archive_requirement(root, requirement_name, folder)`（原 L4335-L4351）在末尾仍按 `folder = _get_git_branch(root)` 再拼一层 → primary 形态下产出 `artifacts/main/archive/main/req-xx/`（双层 main）。
- legacy 形态 `.workflow/flow/archive` 不含 branch，恰好拼一层 → 历史仓看起来单层，掩盖了 bug。

**改动**（src/harness_workflow/workflow_helpers.py, L4335-L4370）：
- ✅ 新增内联 `_archive_base_already_has_branch(base, branch)`：判断 primary 形态（`base.parent.name == branch and base.name == "archive"`）。
- ✅ 分支处理：`folder == current_branch and primary` → 折叠；否则保留原 `archive_base / folder` 路径语义。
- ✅ 历史双层目录零迁移零清洗（AC-05 Excluded）。

**测试**（tests/test_archive_path.py）：
- ✅ `test_archive_path_no_double_branch`：断言归档落到 `artifacts/main/archive/req-99-.../`，`/main/` 段只出现 1 次，`archive/main/` 不存在。
- ✅ `test_archive_path_preserves_legacy`：预置 `archive/main/req-88-legacy/MARKER.txt`，执行新归档后脏目录与标记原封不动、新归档落单层。
- ✅ `python3 -m unittest tests.test_archive_path -v` → 2/2 OK（0.226s）。
- ✅ 全量 `unittest discover tests` → failures=3 errors=3，与 chg-03 基线一致，零回归。

**Plan 步骤追踪**：
- Step 1 ✅ 定位完成
- Step 2 ✅ 路径拼接修复
- Step 3 ⏭ 跳过历史查找回落（无只读查找调用方，超 chg 边界）
- Step 4 ✅ 2 个单测
- Step 5 ⏭ 经验沉淀候选已记入本文件，待 done 阶段统一沉淀

**候选经验**：
```
### 2026-04-19 双形态路径根的双拼陷阱
- Symptom: `archive_requirement` 在 primary 路径（含 branch）+ legacy 路径（不含 branch）两种形态下，用同一套拼接逻辑补 folder，primary 形态双层。
- Cause: `resolve_*_root` 返回值的形态差异被调用方忽略，靠 legacy 历史"碰巧单层"掩盖。
- Fix: 调用方引入形态判定（父目录是否已是 branch），按形态折叠拼接；修 bug 时优先看路径根函数的 primary/legacy 分支是否已含目标段。
```

**对人文档**：`实施说明.md` 已在同目录产出（字段完整）。
