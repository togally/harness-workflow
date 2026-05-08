---
id: reg-01
title: "chg-01/02/04（代码改动被 git reset 抹掉）"
parent_requirement: req-55（gstack 和 harness 工作流融合（开发承载分支 harness-gstack））
created_at: 2026-05-08
operation_type: regression
stage: regression
---

## 1. Current Goal

诊断 req-55（gstack 和 harness 工作流融合（开发承载分支 harness-gstack）） 周期内 git reset --hard 抹掉 chg-01 / chg-02 / chg-04 tracked 文件改动的事故，确定根因 + 给路由决策。

## 2. Context Chain

- Level 0：用户 → /harness-archive req-55 触发 revert dry-run FAIL → 用户选 A → /harness-regression
- Level 0.5：主 agent / harness-manager
- Level 1（本派发）：regression（regression / Opus 4.7）

## 3. 角色加载链自检（role-loading-protocol Step 0~7.6.1）

- [x] Step 1：runtime.yaml 已读（current_requirement=req-54，但实际诊断对象是 req-55——CLI 已被 reset 回 req-54 状态）
- [x] Step 2~6：base-role.md / stage-role.md / regression.md 完整读取
- [x] Step 7：evaluation/regression.md 评估标准已读
- [x] Step 7.5：本 subagent 运行于 opus，与 role-model-map.yaml 声明一致（briefing expected_model=opus）
- [x] Step 7.6 项目级覆盖：扫 `artifacts/project/{constraints,experience,tools}/` —— 6 个 index.md 模板骨架，真实命中数 = 0（chg-05 已预埋的 retro 模板段在 `experience/roles/analyst.md` 是新增 untracked 文件，作为占位段不阻塞 regression）
- [x] Step 7.6.1：scope=experience-regression / experience-stage 命中 0

## 4. Completed Tasks

- [x] 独立核查事故现场（6 项命令全部命中主 agent 报告的"丢失"状态）
- [x] 锁定根因 = 外部 `git reset --hard` 命令（基于 `.git/ORIG_HEAD` 副产物 + harness CLI 代码层无 reset 调用 + hook 全 sample 三角验证）
- [x] 评估恢复可能性（dangling commit 不含丢失代码 / session-memory 不含完整 patch / change.md+plan.md 仅含契约 → tracked 改动彻底丢失）
- [x] 评估影响范围（chg-01/02/04 部分丢失 / chg-05 未受影响 / test-report 已与现实脱节 / runtime 已回退）
- [x] 写 decision.md（路由 = confirm；承载需求 = req-55；后续动作清单 8 项）

## 5. Validated Approaches

- **reflog 时间戳 + ORIG_HEAD 时间戳交叉验证**是定位 git reset 触发源的金标准——任何 `git reset` 命令都会写 ORIG_HEAD，时间戳与 reflog 该次 reset 完全同步
- **`grep -rn "subprocess.*git" --include="*.py"` 排查整个 src/** 是确认 CLI 代码层是否含 git 操作的高效方法
- **`git fsck --lost-found` + dangling commit 时序对比**用于评估"reset 前是否曾 commit 中间状态" → 结果"无中间 commit" → 进一步确认无法从 git 对象恢复
- **untracked 文件状态 (261 个) 与 tracked 文件状态 (HEAD 一致)** 的反差是判断 reset --hard 性质（vs revert / stash）的辅助证据
- **change.md + plan.md + session-memory.md 三件套作为重做契约依据**：即使代码丢失，契约 + 测试用例 + 落点路径完整保留，重做工作量可控

## 6. Failed Paths

- ~~**最初推测：archive 的 revert dry-run 是触发源**~~——核对 `_revert_dry_run_self_check` 实现后否定：dry-run 只跑 `git revert --no-commit -n` + `git checkout -- .` + `git revert --abort`，**不写 ORIG_HEAD**；与 reflog `reset: moving to HEAD` 模式不符。
- ~~**怀疑某 subagent / hook 触发**~~——`grep` 全 src/ 无 reset 调用 + `.git/hooks/` 全 sample → 排除。

## 7. Candidate Lessons

- 2026-05-08 git reset --hard 在多 agent 工作流中是数据丢失的高危反模式 — Symptom：tracked 文件改动被一次性抹掉 / untracked 保留 / runtime 状态回退 | Cause：用户或 agent 在 archive revert dry-run 失败 / executing 写盘失败 / 工作树脏的场景下反射性跑 `git reset --hard HEAD` 试图"清掉重来"，无意中销毁同会话内已写到 tracked 路径的有效改动 | Fix：(a) 在 base-role 加硬门禁"Bash 跑 git reset / git checkout -- . / git restore 类命令前必须用户显式确认"；(b) 在 archive revert dry-run FAIL 时改用 `git stash` 而非 `git checkout -- .`；(c) chg / req executing 阶段每完成一个 step 自动 commit 中间状态（小 commit + squash 在 archive 时合并），让 git 对象库提供 reset 兜底
- 2026-05-08 testing / acceptance 通过 ≠ tracked 改动安全 — Symptom：test-report.md / acceptance/checklist.md 全 PASS，但若实施期间发生 reset，已 PASS 的报告会与现实脱节 | Cause：reset 后 working tree 回到 HEAD，但 untracked 报告文件保留——形成"报告 PASS / 实现已丢失"的虚假 archive 入口 | Fix：archive 前置 hash 校验——用 acceptance 阶段写入的"被覆盖文件 SHA1 列表"vs 当前 working tree SHA1 比对，不一致即阻塞 archive 并要求重跑 testing

## 8. Next Steps / Open Questions

- 主 agent 决策：路由 confirm 后如何处理 reg-01 的"路径错挂在 req-54"问题——建议在 chg-06 落地完成时统一 mv 到 req-55 下；或保留在 req-54 下作为"事故周期内 CLI 视角错位的 audit trail"。
- Open question：是否应在 base-role 直接加硬门禁，把 `git reset` / `git checkout -- .` / `git restore` 这类危险命令列为"派 subagent 运行 Bash 时禁止使用"？需评估对正常 git 工作流的副作用 → 落到独立 sug。
- Open question：archive 的 revert dry-run 流程是否应改为 `git stash push -k -u` + 试 revert + `git stash pop`，避免用户在 dry-run FAIL 后反射性跑 reset？→ 落到独立 sug（不阻塞本路由）。

## 9. default-pick 决策清单（同阶段不打断原则 / chg-05 协议）

- 无（regression 是诊断性 stage，本次诊断未出现需要 default-pick 推进的争议点）

## 10. 上下文消耗评估

- 文件读取：约 18 次（base-role/stage-role/regression role + evaluation + runtime + req-55 元数据 5+ 份 + 关键 src/ 文件 1 份）
- 工具调用：约 25 次（Read / Bash 混合）
- 大文件读取：1 次（session-memory.md 105KB 仅读前 120 行；workflow_helpers.py 仅读 6420-6550 130 行）
- 预估上下文消耗：中等（~30%~40%），未触发 70% 维护阈值
