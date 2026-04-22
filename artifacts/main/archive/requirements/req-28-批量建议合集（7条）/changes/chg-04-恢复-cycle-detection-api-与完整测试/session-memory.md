# Session Memory

## 1. Current Goal

- req-28 / chg-04：把 cycle-detection 对外 API 从 smoke 恢复为完整 7 符号集，并让 `tests/test_cycle_detection.py` 从 1 条 smoke 恢复到覆盖面与 `5584656^` 对齐的完整用例集，覆盖 AC-13。

## 2. Current Status

- [x] Step 1 锁定符号清单：以 bugfix-6 `diagnosis.md` + `5584656^:tests/test_cycle_detection.py` 对齐，确定 7 个符号（briefing 清单与 diagnosis 一致）。
- [x] Step 2 取回历史实现：`git show 5584656^:tests/test_cycle_detection.py > /tmp/cycle_test_original.py`，400 行；生产 `cycle_detection.py` 历史已丢失，采用按历史测试签名反推实现。
- [x] Step 3 适配当前代码结构：新建 `src/harness_workflow/cycle_detection.py`，不依赖已废弃的 `harness_workflow.core`；判定依据 `agent_id` 重复。
- [x] Step 4 恢复测试：24 用例全绿，较历史 ~21 用例有增强（新增 dict 链兼容 / 单例 get-reset / no-cycle noop / 同 role 不同 agent_id）。
- [x] Step 5 对外 re-export：`src/harness_workflow/__init__.py` 与 `src/harness_workflow/tools/harness_cycle_detector.py` 双路径导出。

## 3. Validated Approaches

- `python3 -m unittest tests.test_cycle_detection -v` → 24 passed。
- `python3 -m unittest discover tests` → Ran 120 tests, OK (skipped=36)，较基线 97 +23。
- `python3 -c "from harness_workflow import CallChainNode, CycleDetector, ...; print('ok')"` → ok。
- `python3 -c "from harness_workflow.tools.harness_cycle_detector import CallChainNode"` → ok。

## 4. Failed Paths

- Attempt: 无；单次通过。
- Failure reason: —
- Reminder: —

## 5. Candidate Lessons

```markdown
### 2026-04-19 恢复被裁剪的生产 API 时要优先参考原始测试而非 briefing 描述
- Symptom: briefing 描述 `CycleDetector.enter/exit/detect` / 判定依据 `role` 重复；原测试实际 API 是 `add_node` / `pop` / `clear`，判定依据 `agent_id` 重复。
- Cause: briefing 是二手描述，历史测试是一手权威。
- Fix: 永远先 `git show <commit>^:<path>` 拉原测试，再反推 API；按历史测试签名实现才能保证一次过。
```

## 6. Next Steps

- 进入 testing 阶段，由独立测试工程师复核覆盖面与 AC-13 对应关系。
- 考虑后续把 `harness_cycle_detector` CLI 的 in-memory JSON chain 逻辑也迁到 `cycle_detection.CycleDetector`，避免两份判定实现（留给后续 sug）。

## 7. Open Questions

- 是否需要把 `CycleDetector` 做成线程安全？当前单线程 subagent 调度下不需要，若未来并发派发再加锁。
