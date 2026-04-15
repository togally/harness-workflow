# Plan: 修复误清理逻辑

## 执行步骤

1. 打开 `src/harness_workflow/core.py`，定位 `LEGACY_CLEANUP_TARGETS` 定义（约第 56 行）。
2. 从列表中删除 `Path(".workflow") / "tools",` 这一行。
3. 定位 `_required_dirs()` 函数（约第 1957 行），确认返回列表中已包含：
   - `root / ".workflow" / "tools"`
   - `root / ".workflow" / "tools" / "catalog"`
   若缺失则补充。
4. （执行时需确认）全局搜索 `LEGACY_CLEANUP_TARGETS` 的使用点，确认只有一处清理循环，且不会递归清理子目录导致 tools 子目录被误处理。
5. 保存文件，进行快速语法检查（如 `python -m py_compile src/harness_workflow/core.py`）。

## 预期产物

- 修改后的 `src/harness_workflow/core.py`

## 依赖关系

- **无前置依赖**：此变更为根因修复，是后续变更的基础。
- **后置依赖**：chg-02、chg-03、chg-04 均依赖于本变更完成后，才能保证 tools 目录不会再被误清理。
