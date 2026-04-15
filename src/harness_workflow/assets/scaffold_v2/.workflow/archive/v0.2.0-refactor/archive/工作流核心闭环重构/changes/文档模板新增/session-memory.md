# Session Memory

## 1. Current Goal

- 在 `src/harness_workflow/assets/skill/assets/templates/` 下新增 6 个文档模板文件，并在 `core.py` 的 `_managed_file_contents` 函数中完成注册。

## 2. Current Status

- 已完成。所有模板文件已创建，core.py 注册已完成，验证通过。

## 3. Validated Approaches

- 验证命令：`python3 -c "import sys; sys.path.insert(0, 'src'); from harness_workflow.core import _managed_file_contents; print('OK')"` 输出 OK。
- 新增模板插入位置：`version-memory.md` 注册行之后、`.qoder/commands/harness.md` 之前。

## 4. Failed Paths

- 无。

## 5. Candidate Lessons

```markdown
### 2026-04-11 在 core.py 中注册新模板时的插入位置
- Symptom: 需要在已有 workflow/templates/ 区块末尾追加新条目
- Cause: _managed_file_contents 中 workflow/templates/ 条目集中在 1642-1709 行
- Fix: 在 version-memory.md 行之后、.qoder 行之前插入，保持区块连续性
```

## 6. Next Steps

- change 实现完成，等待 self-test 或进入下一阶段。

## 7. Open Questions

- 无。
