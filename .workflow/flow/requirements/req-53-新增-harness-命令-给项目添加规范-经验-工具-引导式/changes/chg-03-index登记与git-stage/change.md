---
id: chg-03
title: "index.md 自动登记（按 kind schema 分类追加）+ git auto-stage + 加载链 stderr 活证"
parent: req-53（新增 harness 命令给项目加规范经验工具引导式）
created_at: 2026-04-29
status: pending
depends_on: chg-02
---

## 1. 范围（Scope）

把 chg-02 落地的 `_pad_add` 实现**追加 3 个动作**：

- **index.md 自动登记**：按 kind schema 分类追加新条目到对应 `artifacts/project/{kind 路径}/index.md`：
  - kind=rule → 在 `artifacts/project/constraints/index.md` 表格末追加 `| {scope}/{slug}.md | {title} | {scope} | always | (空) |`
  - kind=experience → 在 `artifacts/project/experience/{scope}/index.md` 表格末追加 `| {slug}.md | {title} | experience-{scope} | always | (空) |`
  - kind=tool → 在 `artifacts/project/tools/index.md`「## 项目级工具清单」段（不存在则创建）末追加 `- {slug}.md — {title}`
- **git auto-stage**：调 `subprocess.run(["git", "add", str(target_relative)])` + `subprocess.run(["git", "add", str(index_relative)])`；失败（非 git repo / 命令缺失）silent skip + stderr 警告，不阻塞 add。
- **stderr 加载链活证**：复用 `_log_project_level_load(root, scope, hits, fallback_used=False)`，输出 `[harness] project-level loaded: N+1 files from artifacts/project/{scope}/（fallback=n/a）`，与 install 主流程同款格式。

stdout 末尾追加一行：`✓ git staged. 提示 git commit -m "feat: 项目级 {kind}-{title}"`。

## 2. 目标（Goal）

- G-01：rule 落位后 `artifacts/project/constraints/index.md` 表格新增一行 `| coding/禁止-api-硬编码.md | 禁止-API-硬编码 | coding | always | (空) |`。
- G-02：experience 落位后 `artifacts/project/experience/stage/index.md` 新增一行（experience 的 index.md 在子目录而非顶层）。
- G-03：tool 落位后 `artifacts/project/tools/index.md`「## 项目级工具清单」段新增一行 `- petmall-deployer.md — petmall-deployer`。
- G-04：3 类落位都 stderr 输出 `[harness] project-level loaded: N+1 files ...` 活证。
- G-05：3 类落位都 `git add` 内容文件 + index.md 文件（git status 显示 staged）。
- G-06：非 git 仓 → silent skip git add，不影响落位。
- G-07：表头不存在时（如 user 删了 index.md 表格）→ 自动补齐表头 `| path | title | scope | when_load | 备注 |`。

## 3. 验收（AC，对齐 requirement.md）

- AC-02（index.md 自动登记）：执行 `pad rule coding "代码风格"` 后 `artifacts/project/constraints/index.md` 表格新增一行（注意 scope 字段写真实 scope 而非 `constraints`，与 OQ-Verdicts 落位决策一致）。
- AC-03（加载链可观测）：命令末尾 stderr 含 `[harness] project-level loaded: N+1 files from artifacts/project/constraints/`。
- AC-09（git tracking 提醒）：stdout 含 `✓ git staged. 提示 git commit -m "feat: 项目级 rule-代码风格"`。
- AC-04（install 不覆盖）：mirror 白名单 + protected-zones 双豁免已就位（`artifacts/project/` 在 `_SCAFFOLD_V2_MIRROR_WHITELIST` 中），新增的 index.md 行不会被 `harness install --force-managed` 覆盖。

## 4. 依赖

- 前置：chg-02（_pad_add 真实落位 + 模板预填）
- 后置：chg-04 在本 chg 落地的 _pad_add 增强后实装 list / interactive

## 5. 范围红线

- 不改 `_log_project_level_load` 函数本身（只调用，复用）
- 不动 `_parse_index_md` / `_load_project_level_index`（向前兼容已有表格 schema）
- experience scope 写入 index.md 时用 `experience-{scope}`（如 `experience-stage`），与 `_load_project_level_index` scope_map 一致
- 不引入新 git 操作（仅 `git add`，不 `git commit` / 不 `git push`）
- 非 git 仓 / git 命令异常 → silent skip，不阻塞
