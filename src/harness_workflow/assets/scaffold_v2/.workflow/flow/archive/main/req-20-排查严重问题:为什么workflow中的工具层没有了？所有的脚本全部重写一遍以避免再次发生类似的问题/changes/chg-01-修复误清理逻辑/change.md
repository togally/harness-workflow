# Change: 修复误清理逻辑

## 变更目标

修复 `src/harness_workflow/core.py` 中 `LEGACY_CLEANUP_TARGETS` 错误地将 `.workflow/tools/` 列为旧系统残留目录的问题，确保 `harness update` 执行清理时不会将 tools 目录归档到 backup 中。同时确认 `_required_dirs()` 已正确包含 `.workflow/tools/` 和 `.workflow/tools/catalog/`。

## 范围

### 包含
- 修改 `src/harness_workflow/core.py`：
  - 从 `LEGACY_CLEANUP_TARGETS` 列表中移除 `Path(".workflow") / "tools"`
  - 检查并确认 `_required_dirs()` 包含 `root / ".workflow" / "tools"` 和 `root / ".workflow" / "tools" / "catalog"`

### 不包含
- 不修改任何其他清理逻辑或 scaffold 同步逻辑
- 不重建或恢复 tools 目录内容（由 chg-02 和 chg-03 负责）
- 不添加或修改测试用例（由 chg-04 负责）

## 验收标准

- [ ] `LEGACY_CLEANUP_TARGETS` 中不再包含 `Path(".workflow") / "tools"` 及任何 tools 子路径
- [ ] `_required_dirs()` 返回的列表中同时包含 `.workflow/tools` 和 `.workflow/tools/catalog`
- [ ] 单独审查 core.py 中涉及目录清理/归档的其他代码，确认没有遗漏对 tools 目录的误处理
