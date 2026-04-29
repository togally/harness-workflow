---
req_id: req-50
stage: testing
tester: testing（sonnet）
ts: 2026-04-28T00:00:00+00:00
---

## 1. Current Goal

对 req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）执行 testing stage：分类 33 fail、验证 27 dogfood 用例、端到端验证、5 项合规扫描。

## 2. Context Chain

- Level 0: 主 agent（技术总监）→ testing stage
- Level 1: 测试工程师（testing / sonnet）→ 本 session

## 3. 33 fail 分类结论

| 类别 | 数量 |
|------|------|
| 类 A（req-50 结构性变更预期 breakage） | 21 |
| 类 B（pre-existing，与 req-50 无关） | 12 |
| 类 C（req-50 引入的真 regression bug） | 0 |

**根因总结**：
- 类 A 核心根因：旧测试硬编码了 requirement_review / planning / ready_for_execution 等被 chg-01 删除的 stage 名，以及已废止的 --execute flag。这是预期 breakage，不是 bug。
- 类 B 核心根因：历史文件（sug-25 / sug-35）不存在、req-48 roadmap 未落地（硬门禁八/Step 3.7）、req-45/46 gate 严格化引入的 acceptance work-done 阻断。

## 4. 关键验证结论

- **27 dogfood 用例**：全部 PASS（tests/test_req50_dogfood.py）
- **harness next 单入口**：analysis → executing PASS（无需 --execute）
- **done 不写 sug 池**：PASS
- **LLM-only 模板**：PASS
- **5 项合规扫描**：R1 PASS / revert N/A / 契约 7 PASS / req-29 PASS / req-30 PASS
- **validate --human-docs**：exit 0（1/2，交付总结.md 待 done 阶段产出，正常）
- **validate --contract artifact-placement**：exit 0
- **validate --contract llm-only-docs**：exit 0（via python3 -m harness_workflow.cli，deploy sync 待 pipx reinstall）

## 5. default-pick 决策清单

| 决策 | 推荐 | 理由 |
|------|------|------|
| 33 fail 中类 A 旧测试是否阻塞 acceptance | default-pick 不阻塞 | 这些是已知 expected breakage，chg-01 结构性变更明确删除旧 stage，不是 req-50 引入的 regression |
| validate --contract llm-only-docs 通过 python3 -m，而非 harness 二进制 | default-pick 用 python3 -m | pipx venv 与 src 不同步（deploy 契约，需 pipx reinstall）；src 层验证已 PASS，AC-10 语义满足 |
| test_analyst_role_merge 类 A 还是类 C | default-pick 类 A | chg-01 确实改了 analyst stages，测试期望的"原 requirement-review"注释未加是 test 本身需要更新，不是 reg |

## 6. 待处理捕获问题

- 21 个类 A 旧测试需要后续更新对应测试代码（建议后续新 req 或 sug 处理，不阻塞 req-50）
- pipx venv 与 src 不同步（`harness validate --contract llm-only-docs` 通过 python3 -m 路径，harness 二进制尚无 llm-only-docs 选项）—— 属于 deploy 契约问题，pipx reinstall 后自动修复

## 7. Completed Tasks

- [x] 读取 requirement.md + 所有 change.md
- [x] 读取 executing/session-memory.md
- [x] 运行全量 pytest（739 passed / 33 failed）
- [x] 逐条分类 33 fail（类 A 21 / 类 B 12 / 类 C 0）
- [x] 复跑 tests/test_req50_dogfood.py（27 PASS）
- [x] dogfood 端到端验证（5 维 PASS）
- [x] 5 项合规扫描
- [x] 产出 test-report.md
- [x] 产出 testing/session-memory.md
- [x] harness validate --human-docs exit 0
- [x] harness validate --contract artifact-placement exit 0
- [x] harness validate --contract llm-only-docs exit 0（python3 -m 路径）

## 8. Results

PASS。转 acceptance。
