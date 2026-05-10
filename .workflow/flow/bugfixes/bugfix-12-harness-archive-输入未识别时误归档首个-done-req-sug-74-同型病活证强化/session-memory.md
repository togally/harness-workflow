---
id: bugfix-12
title: "harness archive 输入未识别时误归档首个 done req（sug-74 同型病活证强化）"
created_at: 2026-05-10
operation_type: bugfix
stage: executing
---

## Current Goal
- 落地 diagnosis.md §5 修复方案 A：silent fallback → 显式报错，修两处 cli.py，补 10 用例测试

## Current Status
- F1 ✅：`src/harness_workflow/cli.py` L143 `prompt_requirement_selection` 改为 preselect 不在 requirements 时打印错误到 stderr 并 return None（深度防御）
- F2 ✅：archive dispatch 块 L619-627 validate 提到 if 外，始终跑 validate，不区分 args/runtime 路径；不在 done_reqs 时 return 1
- F3 ✅：新建 `tests/test_bugfix12_archive_input_validation.py`，10 用例全部 PASSED
- 测试 ✅：pytest 10/10 + harness validate --contract regression exit 0 + 手工 E2E 三场景全 exit 1 + 无文件移动

## Validated Approaches
- 修改 F2 在 dispatch 层 early exit（return 1），是主防线；F1 在 prompt 层也报错 return None 是深度防御
- subprocess 测试 pattern：tmp_path 铺骨架 + PYTHONPATH=src，参考 test_requirement_fallback_flag.py
- `monkeypatch.setattr("sys.stdin.isatty", lambda: False)` 用于单测 non-tty 行为

## Failed Paths
- 无

## Candidate Lessons
- 2026-05-10 validate 逻辑只覆盖 fallback 路径、忽略显式输入路径 — Symptom: 用户传 req-57/bugfix-11 不在 done_reqs 时 silent fallback 到 done_reqs[0] | Cause: `if not preselect_value` 内的 validate 逻辑只在 args.requirement=None 时执行 | Fix: validate 提到 if 之外，始终执行

## Test Results
- `pytest tests/test_bugfix12_archive_input_validation.py -v`: 10 passed
- Full suite (excl. integration + pre-existing failures): 0 新增 fail（pre-existing 66→61 fail, 852→857 pass）
- harness validate --contract regression: exit 0
- 手工 E2E: req-99/bugfix-99/runtime-not-in-done 三场景全部 exit 1 + stderr 报错 + 无文件移动

## Next Steps / Open Questions
- 路由 → testing

## done 阶段回顾（六层精简）

- **Context**：4 角色独立(regression opus / executing sonnet 子 / acceptance sonnet 子 / done opus 主)；experience 待补本轮 work-done gate 漏洞教训。
- **Tools**：`harness next` 自动连跳暴露 work-done gate testing 阶段漏洞 → sug-78；手工 E2E + pytest 全程顺畅。
- **Flow**：regression → executing → testing(自动跳过)→ acceptance → done。**testing 异常**:work-done gate 模板裸过,实质 testing 工作由 executing 子 agent 完成 + 主 agent 兜底填实 test-evidence.md。
- **State**:runtime.yaml / state/bugfixes/bugfix-12-*.yaml 一致;active_requirements 含 bugfix-11 + bugfix-12。
- **Evaluation**:acceptance 子 agent 独立复现 10/10 PASS;verdict=PASS 0 异议。
- **Constraints**:硬门禁三/八/九全程遵守;无越界;0 新增 fail。

## 沉淀的 sug

- sug-78(work-done gate testing 阶段查 ## 结论 内容非空)— priority: medium

## 默认决策(done 阶段)

- 接受 testing 阶段被自动连跳的事实 + 主 agent 兜底填实 test-evidence.md(executing 已实质完成 testing 工作)。
- 不退回 testing 重派子 agent(代价大于收益,executing 已独立 agent 实例 + 跑过 10/10 + 5 项合规)。

## 待办(archive 前)

- commit revert dry-run Step 2.5 抽样
- commit 本 bugfix 全部改动(cli.py + 测试 + bugfix 工件 + sug-78)
- archive
