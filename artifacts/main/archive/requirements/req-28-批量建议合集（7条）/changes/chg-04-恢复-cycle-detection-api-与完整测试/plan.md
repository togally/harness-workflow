# Change Plan

## 1. Development Steps

### Step 1：锁定符号清单与语义

- 读 `artifacts/main/bugfixes/bugfix-6-*/diagnosis.md`（或 `实施说明.md`）的"恢复路径"节，取其中列出的符号清单为权威。
- 读 sug-13（如仍在 `.workflow/flow/suggestions/archive/` 下）的"恢复建议"章节对齐。
- 在 session-memory 中记录最终符号列表（6 个或 7 个），planning 模板按 7 个书写，executing 如调整为 6 个须注明差异。

### Step 2：取回历史实现

- 用 `git log --all --full-history -- tests/test_cycle_detection.py src/harness_workflow/cycle_detection.py src/harness_workflow/tools/harness_cycle_detector.py` 定位最后一次含完整实现的 commit。
- 用 `git show <sha>:<path>` 取回旧实现代码，粘回 `src/harness_workflow/cycle_detection.py`（若位置变更，则选择当前代码库实际模块路径，并同步 `__init__.py` 的 re-export）。

### Step 3：适配当前代码结构

- 若历史实现依赖已消失的内部模块（例如已被删的 `state.py` 辅助函数），改用当前等价入口（多数情况下为 `workflow_helpers.py` 中的 runtime 读写函数）。
- 保持函数签名与历史测试一致（这是测试直接复用的前提）。

### Step 4：恢复测试 `tests/test_cycle_detection.py`

- 从同一历史 commit 取回完整测试文件，粘回后直接跑 `pytest tests/test_cycle_detection.py -v`。
- 对失败的用例按报错逐条修（多数为 import 路径、文件路径 fixture）。
- 不允许 xfail / skip，全部走绿。

### Step 5：对外 re-export

- 在 `src/harness_workflow/__init__.py` 补充：
  ```python
  from .cycle_detection import (
      CallChainNode,
      CycleDetector,
      CycleDetectionResult,
      detect_subagent_cycle,
      report_cycle_detection,
      get_cycle_detector,
      reset_cycle_detector,
  )
  ```
- 若 diagnosis.md 最终定为 6 个符号，按最终列表删 1 条。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_cycle_detection.py -v` 全绿，用例数与 `5584656^` 的历史版本一致。
- `python -c "from harness_workflow import CycleDetector, detect_subagent_cycle, report_cycle_detection, get_cycle_detector, reset_cycle_detector, CallChainNode, CycleDetectionResult; print('ok')"` 输出 ok。
- `grep -n "from .cycle_detection import" src/harness_workflow/__init__.py` 非空。

### 2.2 Manual smoke / integration verification

- `python -m pytest tests/ -v -k cycle` 不崩、用例数回升。
- 构造一个最小调用链：Level0 → Level1 → Level0，调用 `detect_subagent_cycle` 返回真；`report_cycle_detection` 输出结构化 dict。

### 2.3 AC Mapping

- AC-13 -> Step 1/2/3/4/5 + 2.1 + 2.2

## 3. Dependencies & Execution Order

- 与 chg-01 / chg-02 / chg-03 文件改动基本不冲突，可在 chg-03 之后立即并行启动。
- 无须等待 chg-05/06/07。
