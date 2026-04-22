---
id: sug-39
title: `tests/` 加 `conftest.py` 注入 sys.path，支持独立文件 pytest 运行
status: pending
created_at: "2026-04-22"
priority: medium
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）testing 阶段发现：

- `pytest -q`（全量）全绿 ✅
- `pytest tests/test_project_scanner.py`（独立文件）在某些 shell 环境下报 `ModuleNotFoundError: harness_workflow`

原因：`tests/` 目录缺 `conftest.py` 注入 `src/` 到 sys.path；全量运行时 pyproject 配置/pytest rootdir 生效，独立文件运行时环境差异触发失败。

# 建议

新建 `tests/conftest.py`：

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
```

覆盖全部独立测试文件运行场景。

# 验收

- `pytest tests/test_project_scanner.py` 独立跑全绿
- `pytest tests/test_task_context_index.py` 独立跑全绿
- `pytest -q` 全量仍 288 passed / 50 skipped 零回归
- TDD 红绿
