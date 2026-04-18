# Session Memory

## 变更：chg-01-修复误清理逻辑

- [x] 步骤1：打开 `src/harness_workflow/core.py`，定位 `LEGACY_CLEANUP_TARGETS`（第 56 行）
- [x] 步骤2：从列表中删除 `Path(".workflow") / "tools",` 这一行
- [x] 步骤3：定位 `_required_dirs()`（第 1957 行），确认返回列表中包含 `root / ".workflow" / "tools"` 和 `root / ".workflow" / "tools" / "catalog"`，已包含，无需补充
- [x] 步骤4：全局搜索 `LEGACY_CLEANUP_TARGETS` 的使用点，确认只有一处清理循环（`cleanup_legacy_workflow_artifacts`，第 2546 行），该循环对目录使用 `_prune_empty_dirs` 后若仍非空则整体 `shutil.move` 到 backup，不递归清理子目录
- [x] 步骤5：语法检查 `python3 -m py_compile src/harness_workflow/core.py`，通过

## 关键决策
- 确认 `_required_dirs()` 中 tools 和 tools/catalog 已存在，无需重复添加

## 遇到的问题
- 无

## 测试通过情况
- 语法检查通过
