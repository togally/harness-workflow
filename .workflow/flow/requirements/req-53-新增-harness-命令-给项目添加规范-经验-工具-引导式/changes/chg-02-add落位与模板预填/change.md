---
id: chg-02
title: "_pad_add 真实落位 + 三份 .tmpl 模板预填 + write_if_missing 不覆盖"
parent: req-53（新增 harness 命令给项目加规范经验工具引导式）
created_at: 2026-04-29
status: pending
depends_on: chg-01
---

## 1. 范围（Scope）

把 chg-01 落地的 `_pad_add` stub 替换为**真实落位逻辑**：

- 按 `kind` + `scope` 解析路径（kind=rule → `artifacts/project/constraints/{scope}/{slug}.md`，kind=experience → `artifacts/project/experience/{scope}/{slug}.md`，kind=tool → `artifacts/project/tools/{slug}.md`）
- slug 由 title 经 `_path_slug` helper 转换（已在 workflow_helpers.py:2545 复用）
- 渲染对应 kind 的 `.tmpl` 模板（含 frontmatter + 占位段）
- 调 `write_if_missing` 写盘（不覆盖已存在文件，与 `_bootstrap_project_skeleton` 同款幂等）
- 落位成功后输出 `[harness pad] added {relative_path} ✓`，exit code = 0

本 chg **不**做 index.md 自动登记（chg-03 做）+ git add stage（chg-03 做）+ stderr 加载链活证（chg-03 做）。本 chg **只**保证「文件落到正确位置 + 模板预填 + 不覆盖」。

## 2. 目标（Goal）

- G-01：`harness pad rule coding "禁止-API-硬编码"` → 文件落 `artifacts/project/constraints/coding/禁止-api-硬编码.md`，含 frontmatter（id / kind / scope / title / created_at / when_load: always）+ 占位段（`## 内容` / `## 适用范围` / `## 例外`）。
- G-02：`harness pad experience stage "executing-虚报教训"` → 文件落 `artifacts/project/experience/stage/executing-虚报教训.md`。
- G-03：`harness pad tool "petmall-deployer"` → 文件落 `artifacts/project/tools/petmall-deployer.md`，frontmatter 含 `tool_id / keywords / scope: tools`。
- G-04：重复 `harness pad rule coding "禁止-API-硬编码"` → write_if_missing 跳过 + stderr 提示 `已存在，跳过`，exit code = 0（幂等）。
- G-05：constraints/{scope}/ 子目录不存在时自动 mkdir。

## 3. 验收（AC，对齐 requirement.md）

- AC-01（落位正确）部分：文件落到 `artifacts/project/constraints/coding/{slug}.md`，含 frontmatter + `## 内容` 占位段。
- AC-07（fresh repo dogfood）部分：在新仓 `harness install` 后，`harness pad experience tool "apifox-用法"` 文件正确落位。
- AC-04（install 不覆盖）部分：本 chg 落地的文件路径在 `_SCAFFOLD_V2_MIRROR_WHITELIST` 已豁免（`artifacts/project/`），`harness install --force-managed` 不覆盖。

## 4. 依赖

- 前置：chg-01（CLI dispatch + PAD_KINDS 常量 + stub helper）
- 后置：chg-03 在本 chg 落地的 `_pad_add` 中追加 index.md 登记 + git stage 调用

## 5. 范围红线

- 不动 `install_repo` / `_merge_project_level_files` 主流程
- 不引入新路径（严格按 requirement.md OQ-Verdicts 决策的路径表）
- 不动 PetMallPlatform / PetMallAdmin / uav 仓
- 模板 `.tmpl` 落 `src/harness_workflow/assets/templates/project-add/{kind}.md.tmpl`，不复用 `project-skeleton/`（语义不同）
