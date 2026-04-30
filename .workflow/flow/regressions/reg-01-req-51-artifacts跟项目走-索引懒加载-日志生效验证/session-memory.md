---
id: reg-01
title: "req-51（项目级规则-经验-工具支持从制品引入）-artifacts跟项目走+索引懒加载+日志生效验证"
created_at: 2026-04-30
operation_type: requirement
stage: regression
---

## Current Goal

诊断 req-51 done 后用户提出的 3 点反馈（P1 路径绑 branch vs 项目 / P2 索引懒加载 / P3 流程触发打日志），独立判定真伪 + 给路由决策。

## Context Chain

- Level 0: 主 agent（technical-director / opus）
- Level 1: Subagent-L1（regression / opus）—— 本 subagent，负责 reg-01 诊断 + 路由决策

## Completed Tasks

- [x] 加载角色：runtime.yaml → base-role.md → stage-role.md → regression.md → evaluation/regression.md → experience/roles/regression.md
- [x] 模型自检：role-model-map.yaml `roles.regression.model = "opus"` 与本 subagent Opus 4.7 一致
- [x] 读 reg-01 工作区（4 份模板占位文件 + meta.yaml）
- [x] 读 req-51 关键产出：requirement.md / acceptance/checklist.md / chg-04 dogfood
- [x] 实证 P1：grep `_get_git_branch` 14 处，`_SCAFFOLD_V2_MIRROR_WHITELIST` 字面量 `"artifacts/main/project/"`（workflow_helpers.py line 201），validate_contract.py line 1114-1115 注释 main 字面量
- [x] 实证 P2：role-loading-protocol Step 7.6 / experience 加载侧无项目级 index.md；tools-manager Step 2.0 已通过 keywords.yaml 天然懒加载
- [x] 实证 P3：grep "项目级加载\|project-level loading" src/ = 0 命中；`_merge_project_level_files` docstring 明文"不接入 install_repo / update_repo 主流程"；acceptance checklist § 393 AC-08 自承用户手动验收
- [x] 写 4 份机器型工件：meta.yaml / regression.md / decision.md / session-memory.md

## 真伪判定（汇总）

| 反馈点 | 判定 | 关键证据 |
|--------|------|---------|
| P1 路径绑 branch vs 项目 | **真** | `_get_git_branch` = git branch 实证；白名单字面量 `"artifacts/main/project/"` 多 branch 场景失配；与用户原意"跟项目走"冲突 |
| P2 索引懒加载 | **部分真** | 项目级目录现状空占位未触发，但加载链文档无 index.md → 等同 rglob 全读；YAGNI 视角可缓 |
| P3 流程触发 + 打日志 | **真** | src/ 全无项目级加载日志；helper 不接入 install / update 主流程；AC-08 acceptance 已自承未走 |

## default-pick 决策清单（chg-05 协议）

| ID | 选项 | default-pick | 理由 |
|----|------|--------------|------|
| D-P1 | 路径绑定语义 | **D**（双轨：`artifacts/{branch}/project/` + `artifacts/project/`） | 兼顾 branch 隔离与项目级共享；不破坏 bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）契约；fallback = B（直接迁 `artifacts/project/`） |
| D-P2 | 索引懒加载 | **A**（每子目录加 index.md，纯文档 SOP） | 与全局 `state/experience/index.md` 范式一致；零 src/ 改动；fallback = C（入 sug 池） |
| D-P3 | 流程触发 + 日志 | **A + B 并行**（helper 加 stderr 日志 + 子进程 dogfood 断言 stderr 命中 + 用户 PetMallPlatform 真实验证） | 提升可观测性 + 闭环 AC-08；fallback = C（入 sug 池） |
| D-Route | 整体路由 | **B**（P1 → 开 req-52，P2 + P3 入 sug 池） | P1 涉契约层 + helper 层不可入 sug；P2 / P3 是优化项可入 sug；fallback = A（统一开 req-52）/ C（全入 sug 池） |

均按"同阶段不打断 + default-pick"原则推进，无打断用户事项。

## Validated Approaches

- 三维（契约 / 源代码 / 部署二进制）的契约 + 源代码两维核查覆盖了本次诊断；部署层无需检查（本诊断不动 src/，不影响 deploy）
- grep 字面量 `"artifacts/main/project/"` 是定位"白名单写死"问题的关键 keyword
- `_merge_project_level_files` docstring 自承"不接入 install_repo / update_repo 主流程"是 P3 根因的直接证据

## Failed Paths

- 无失败路径；所有证据一次性 grep + read 命中，无回溯

## Candidate Lessons

- 2026-04-30 req-51 类"加载链项目级覆盖全局"实施时常踩两类暗坑 — Symptom：白名单字面量与 `{branch}` 占位不一致 + 加载行为靠 LLM 自律 vs 代码强证 | Cause：契约文档用通配但 helper 落地写死 main，且 SOP 加载行为未加可观测信号 | Fix：所有路径常量用通配前缀 / 后缀或动态 `_get_git_branch` 生成 + helper 加 stderr 加载日志 + dogfood 子进程断言 stderr 标记
- 2026-04-30 OQ 拍板范围漏覆盖识别模板 — Symptom：req done 后用户提出"哎我当时没考虑到 X 场景"反馈 | Cause：OQ 拍板时未穷举使用场景矩阵（如 branch 切换 / 多 branch 协作） | Fix：analyst 拍板 OQ 前主动列"使用场景矩阵"，default-pick 段落每条带"覆盖场景 / 不覆盖场景"清单

## Next Steps / Open Questions

- Next：本 subagent 写盘后退出；主 agent 据 decision.md 路由 B 推进（开 req-52 或 harness suggest）
- Open：用户是否接受路由 B、是否接受 D-P1（双轨）、是否同意 P2 / P3 暂入 sug 池 —— 由主 agent 在退出诊断后向用户汇报，不在本 subagent 职责内打断

## 待处理捕获问题

- 运行时（subagent harness）拦截了 analysis.md 文件的写盘（"Subagents should return findings as text, not write report files"），而 regression stage 退出条件要求 analysis.md 是机器型必填件——本 subagent 把完整诊断分析（grep 实证 + 真伪判定 + default-pick 候选 + 路由决策）作为汇报正文返回主 agent；主 agent 可视情况由自身或下次 stage 角色补写 analysis.md（内容已在汇报正文 + regression.md / decision.md 中完整覆盖）
- meta.yaml / regression.md / decision.md / session-memory.md 4 份盘已成功写入

## 模型一致性自检

- 期望：role-model-map.yaml `roles.regression.model = "opus"`
- 实际：本 subagent 运行于 Opus 4.7（1M context），与声明一致
