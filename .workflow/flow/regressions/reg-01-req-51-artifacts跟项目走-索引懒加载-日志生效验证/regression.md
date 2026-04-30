---
id: reg-01
title: "req-51（项目级规则-经验-工具支持从制品引入）-artifacts跟项目走+索引懒加载+日志生效验证"
created_at: 2026-04-30
operation_type: requirement
stage: regression
diagnostician: "Subagent-L1（regression / opus）"
verdict: "P1=real / P2=partial-real / P3=real"
---

## 问题描述

req-51（项目级规则-经验-工具支持从制品引入）acceptance verdict = PASS / done 后，用户提出 3 点反馈：

1. P1 — 制品仓库的规范目录应该跟项目走而不是跟分支走
2. P2 — 加上索引目录避免一次性加载所有
3. P3 — 做一次测试查看是否生效（例如流程触发后打日志）

## 证据（详 analysis.md）

- **P1**：`_get_git_branch`（workflow_helpers.py line 5750-5764）= git branch 实证；`_SCAFFOLD_V2_MIRROR_WHITELIST` 字面量 `"artifacts/main/project/"`（line 201），不带 `{branch}` 通配；validate_contract.py line 1114-1115 注释也是字面量 main → 多 branch 场景失配。
- **P2**：项目级目录现状仅 `.gitkeep` 占位（空），但 role-loading-protocol Step 7.6 / experience 加载侧未定项目级 index.md，文件级 rglob 全读；tools-manager Step 2.0 已通过 keywords.yaml 天然懒加载（仅 constraints + experience 缺索引）。
- **P3**：`grep "项目级加载\|project-level loading" src/` = 0 命中；`_merge_project_level_files` docstring 自认"不接入 install_repo / update_repo 主流程"；acceptance checklist § 393 自承 AC-08 PetMallPlatform 真实验证"acceptance 不强制拦截"。

## 根因分析

- **P1 根因**：req-51 OQ-1 = B-modified 拍板时把"制品包内管理"理解为 `artifacts/{branch}/project/`，未深究"branch 切换数据可见性"语义；helper 落地时白名单写死 main 字面量，多 branch 场景未覆盖。
- **P2 根因**：实施期项目级目录是新承载层（无存量），acceptance 默认"空占位 + 文档 SOP 即可"；未与全局 `state/experience/index.md` 范式对齐增项目级 index.md。
- **P3 根因**：req-51 实施期 dogfood 选了 fixture-based + helper 单测路径（覆盖 helper 层），未在 src/ helper 加可观测信号；AC-08 主动留作"用户手动验收"，未跟进。

## 结论

- [x] **真实问题**：P1（多 branch 场景项目级数据不可见 + 白名单字面量失配）+ P3（加载行为无可观测信号）
- [x] **部分真实**：P2（索引懒加载）现状未触发，但加载链文档明示"文件级覆盖"等同 rglob，未来文件数 ≥ 10 时确有上下文风险

## 路由决定

**整体路由 = B**（P1 转新 req-52；P2 + P3 入 sug 池）。

- **P1 default-pick = D（双轨：保持 `artifacts/{branch}/project/` + 新增 `artifacts/project/`，三层文件级覆盖）**；fallback = B（直接迁 `artifacts/project/`）。
- **P2 default-pick = A（每子目录加 index.md，纯文档 SOP，零 src/ 改动）**；fallback = C（入 sug 池暂缓）。
- **P3 default-pick = A + B 并行**（helper 加 stderr 加载日志 + dogfood 子进程断言 stderr 命中 + 用户在 PetMallPlatform 真实验证）；fallback = C（入 sug 池暂缓）。

如果用户认为 P1 + P2 + P3 都重要 → 路由 A（开 req-52，三点统一收口）；如果"main 单 branch 够用，3 点都不急" → 路由 C（3 点全入 sug 池）。

## 是否阻塞用户回填

**不阻塞**。证据 + default-pick 已完整，用户拍板路由 A / B / C 即可。

## 测试用例设计

> req 模式（plan.md 由后续 analyst 在 req-52 / sug 处理时补），本节不强制；占位以满足契约。

regression_scope: targeted（仅当转 req-52 时由 analyst 重新评估）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| —（route=B 时由后续 sug / req 承接） | — | — | — | — |
