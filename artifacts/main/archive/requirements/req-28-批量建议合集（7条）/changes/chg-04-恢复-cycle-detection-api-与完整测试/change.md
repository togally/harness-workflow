# Change

## 1. Title

恢复 cycle-detection API 符号与完整测试用例

## 2. Goal

- 把 `harness_workflow` 模块对外导出的 cycle-detection 符号从 smoke 状态恢复为完整 API（以 sug-13 / bugfix-6 `diagnosis.md` 列出的符号集为准；需求文档同时提到 6 个与 7 个两种说法——最终以 diagnosis.md 为权威），让 `tests/test_cycle_detection.py` 从当前 1 条 smoke 恢复为完整用例集。

## 3. Requirement

- `req-28`

## 4. Scope

### Included

- 在 `src/harness_workflow/tools/harness_cycle_detector.py`（若存在）或新建 `src/harness_workflow/cycle_detection.py` 中导出以下符号：
  - `CallChainNode`
  - `CycleDetector`
  - `CycleDetectionResult`
  - `detect_subagent_cycle`
  - `report_cycle_detection`
  - `get_cycle_detector`
  - `reset_cycle_detector`
  （7 个符号；若 diagnosis.md 最终以 6 个为准，则按 diagnosis.md 为准，本 change 实施前在 executing 阶段再对齐。）
- 在 `src/harness_workflow/__init__.py` 或等价入口文件中 re-export 上述符号。
- 恢复 `tests/test_cycle_detection.py` 的完整用例（参考 git log 在 commit `5584656^` 之前的历史内容，或 bugfix-6 `实施说明.md` / `diagnosis.md` 的"恢复路径"节）。
- 验证所有恢复的测试全部通过。

### Excluded

- 不新增 cycle-detection 的业务扩展（例如阈值调优、新增检测算法等），仅恢复已丢失符号与测试。
- 不改其他 subagent 调度模块的行为。

## 5. Acceptance

- Covers requirement.md **AC-13**：模块导出的 cycle-detection 符号齐备、基本语义正确；`tests/test_cycle_detection.py` 完整用例全部通过。

## 6. Risks

- 风险 A：diagnosis.md 的"恢复路径"节与 git 历史代码有出入 → 缓解：以 diagnosis.md 为主，git 历史为辅；executing 阶段把差异记入 session-memory 并逐项裁决。
- 风险 B：恢复的符号与 `harness_workflow` 现有公开 API 存在命名冲突 → 缓解：先 `grep -n "CycleDetector\|call_chain" src/harness_workflow/` 检查重名；有则在 executing 阶段停下来沟通。
- 风险 C：老测试用例用了已移除的内部依赖 → 缓解：执行时按失败用例逐项修到 import 层，同步更新 sug-13 / bugfix-6 诊断文档里的"恢复清单"。
