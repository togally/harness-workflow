---
id: chg-01
title: "CLI 入口 harness pad 子命令骨架 + kind/scope 枚举常量 + 反非法 lint"
parent: req-53（新增 harness 命令给项目加规范经验工具引导式）
created_at: 2026-04-29
status: pending
---

## 1. 范围（Scope）

新增 `harness pad` 子命令的 **CLI 入口骨架**：argparse 注册 + dispatch + 三类位置参数解析 + 非法 kind / scope 时 ABORT 并输出可读建议。配套常量 `PAD_KINDS` 集中定义在 `workflow_helpers.py` 顶层，供 chg-02/03/04 复用。本 chg **只**完成 CLI 解析层，落地 helper（`_pad_add` / `_pad_list` / `_pad_interactive`）以 stub 形式存在并 `return 0`，不做真实落位 / 模板渲染 / index 登记 / git stage —— 这些在 chg-02 ~ chg-04 逐步接入。

## 2. 目标（Goal）

- G-01：`harness pad rule coding "禁止-API-硬编码"` exit code = 0，stdout 含 `[harness pad] (stub) parsed kind=rule scope=coding title=...`。
- G-02：`harness pad foo bar "..."` 非法 kind → exit code ≠ 0 + stderr 含「kind 必须是 rule/experience/tool 之一」。
- G-03：`harness pad rule standards "..."` 非法 scope → exit code ≠ 0 + stderr 含「rule scope 必须是 coding/architecture/api/database/security 之一」。
- G-04：`harness pad list` exit code = 0（dispatch 到 `_pad_list` stub）。
- G-05：`harness pad`（裸跑）exit code = 0（dispatch 到 `_pad_interactive` stub）。

## 3. 验收（AC，对齐 requirement.md）

- AC-01 部分（CLI 路径解析）：`harness pad rule "代码风格"` 不报 argparse 错误（参数被正确解析）。
- AC-08 前置（interactive 入口）：`harness pad` 无参数走 interactive 分支（本 chg 仅 dispatch 到 stub，questionary 实装在 chg-04）。
- 反非法 lint：本 chg 落地的两条 ABORT 路径（非法 kind / 非法 scope）即 requirement.md「反非法 lint」段两条样例的可执行支撑。

## 4. 依赖

- 无前置（本 chg 是 chg-02/03/04 的入口骨架）
- 后置：chg-02 在本 chg 注册的 dispatch 上接入真实 `_pad_add`

## 5. 范围红线（与 requirement.md 一致）

- 不动 PetMallPlatform / PetMallAdmin / uav 仓
- 不引入 `_use_*_layout*` / `*_LAYOUT_FROM_*` 命名
- 不动 `install_repo` / `_merge_project_level_files` / `_bootstrap_project_skeleton` 主流程
- 不破现有 `artifacts/project/*` 路径标准
