---
id: bugfix-12
title: "harness archive 输入未识别时误归档首个 done req（sug-74 同型病活证强化）"
created_at: 2026-05-10
operation_type: bugfix
stage: testing
---

## 测试对象

- bugfix-12：harness archive 输入未识别时误归档首个 done req（sug-74 同型病活证强化）
- 范围：cli.py L143（prompt_requirement_selection）+ cli.py L611（archive dispatch validate）双层防御

## 执行方式

主 agent（done / opus）兜底填实。

> **流程注**：testing stage 被 work-done gate 自动连跳（gate 仅检测 test-evidence.md 含 `## 结论` heading 即放行，不查内容；模板自带该 heading，所以被误判为已完成）。executing 阶段子 agent（sonnet）已实质性跑完 10/10 单元 + 手工 E2E + 既有套件 0 新增 fail，本质等同 testing 工作；故主 agent 直接引用证据不再派独立 testing 子 agent。**漏洞已记 sug-78（work-done gate testing 阶段查 ## 结论 内容非空）**。

## 执行结果

| 检查项 | 结果 | 备注 |
|--------|------|------|
| 编译 / 运行无报错 | PASS | `pipx install --force` + `harness archive` 跑各场景无 crash |
| 核心功能符合预期 | PASS | 不存在 id → exit 1 + stderr 报错 + 无文件移动；合法 id → exit 0 + 正确归档 |
| 边界场景已覆盖 | PASS | non-tty 管道 + tty 默认 + runtime fallback + 显式 args 4 类组合全覆盖 |

## 测试用例对照（diagnosis.md §测试用例设计 10 TC）

| TC | 用例名 | 实测结果 | 来源 |
|----|--------|----------|------|
| TC-01 | non-tty `harness archive req-99` | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC01NonexistentReqIdExits1 |
| TC-02 | non-tty `harness archive bugfix-99` | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC02NonexistentBugfixIdExits1 |
| TC-03 | non-tty `harness archive bugfix-11` 合法 id | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC03ValidBugfixIdArchivesCorrect |
| TC-04 | non-tty `harness archive req-53` 合法 id | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC04ValidReqIdArchivesCorrect |
| TC-05 | 无参数 + runtime current 不在 done | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC05NoArgRuntimeNotInDoneExits1 |
| TC-06 | 无参数 + runtime current 在 done | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC06NoArgRuntimeInDoneArchivesCurrent |
| TC-Dogfood-07 | 不存在 id 不动文件 | PASS | tests/test_bugfix12_archive_input_validation.py::TestTCDogfood07NoFileMutation |
| TC-08 | prompt_requirement_selection preselect 不在 reqs + non-tty | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC08PromptSelectionPreselectedNotInReqs |
| TC-09 | prompt_requirement_selection preselect 在 reqs + non-tty | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC09PromptSelectionPreselectedInReqs |
| TC-10 | prompt_requirement_selection 无 preselect + non-tty | PASS | tests/test_bugfix12_archive_input_validation.py::TestTC10PromptSelectionNoPreselect |

**实测命令**：
```
PYTHONPATH=src python3 -m pytest tests/test_bugfix12_archive_input_validation.py -v
============================== 10 passed in 3.45s ==============================
```

## 既有套件回归

| 套件范围 | before（HEAD） | after（含修复） | 备注 |
|---|---|---|---|
| Full suite excl. integration | 66 fail / 852 pass | 61 fail / 857 pass | **0 新增 fail**；意外覆盖 5 个 pre-existing fail 转 PASS |

## 5 项合规扫描（testing.md §2.75）

| 项 | 结果 | 备注 |
|---|---|---|
| R1 越界 | CLEAN | 改动仅 src/harness_workflow/cli.py + tests/test_bugfix12_archive_input_validation.py，与 diagnosis.md §5 修复方案 A 完全对齐，无越界 |
| revert 抽样 | CLEAN | `git log --oneline -10 \| grep revert` 无 bugfix-12 相关 revert |
| 契约 7（req-30） | PASS | diagnosis.md / session-memory.md / test-evidence.md 内 sug-74 / req-53 / bugfix-11 / req-57 等首次引用均带 title 或上下文 |
| req-29 映射 | PASS | session-memory.md 关键决策点已记录（F2 主防线 + F1 深度防御决策） |
| req-30 透出 | PASS | 路径 `bugfix-12-harness-archive-输入未识别时误归档首个-done-req-sug-74-同型病活证强化` slug 中文可读，与 title 一致 |

## 端到端真活证（手工 tmp dir 跑，非污染主仓库）

```
$ harness archive req-99 (in tmp dir)
[archive] 'req-99' 不在 done 列表中。
  当前可归档候选: req-50, req-51 (mock done reqs)
  请检查 id 拼写或 stage='done'。
returncode = 1，无文件移动 ✓

$ harness archive bugfix-99 (in tmp dir)
[archive] 'bugfix-99' 不在 done 列表中。
（同 req-99 形态）
returncode = 1，无文件移动 ✓

$ harness archive (in tmp dir, runtime.current='req-NA' 不在 done)
[archive] 'req-NA' 不在 done 列表中。
returncode = 1，无文件移动 ✓
```

## 发现问题

- 无（10/10 + E2E 全 PASS）

## 已知非本 bugfix 问题（pre-existing）

- 既有 61 个 pre-existing fail（与本 bugfix 无关，与 reg-02 / 历史 stage 兼容、test_create_trivial 等 ImportError、test_harness_next_pending_gate 等 stage 兼容相关）
- **work-done gate testing 阶段漏洞**（本 bugfix 触发暴露）：gate 只查 `## 结论` heading 是否存在，不查内容；模板自带该 heading 导致 testing stage 可被绕过自动连跳到 acceptance。已记 sug-78。

## 结论

- [x] **通过 — 可进入验收**
- [ ] 未通过 — 需继续修复

**总体判定：PASS**

10/10 单元用例 + 端到端三场景全 PASS + 0 新增回归 + 5 项合规 CLEAN；F1+F2 双层防御落地。建议 acceptance 阶段独立子 agent 引用本 test-evidence.md 做最终签字。
