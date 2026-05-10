---
id: sug-77
title: 加 harness validate --contract skill-body-consistency 扫 4 平台 skill body 同步
status: pending
created_at: 2026-05-10
priority: medium
---

# sug-77：加 harness validate --contract skill-body-consistency 扫 4 平台 skill body 同步

## 现状

req-56（harness requirement 默认调 /office-hours，--fallback 走原生 analyst，产出强制对齐 harness 文档规范）/ chg-03 实施时发现：

- harness 各 agent 平台 skill 文档分布不均（path 不齐）：
  - `.claude/commands/harness-requirement.md`（commands/）
  - `.kimi/skills/harness-requirement/SKILL.md`（skills/）
  - `.qoder/commands/harness-requirement.md`（commands/）
  - `.codex/skills/harness-requirement/SKILL.md`（skills/）

- 4 平台 frontmatter 各异（claude / qoder 用 `description + argument-hint`，kimi / codex 用 `name + description`），整文件无法字节级一致
- chg-03 实施靠**人工 cp 同一份 body block**到 4 平台保持 body 一致；无 lint 防漂移
- testing 阶段补的 `tests/test_chg03_skill_mirror_lint.py` 引入 SHA256 hash 校验作 testing 自补，但仅此一份 testing 文件，未上升到 `harness validate --contract` 全局契约层

## 触发场景

- req-56 / chg-03 / executing：实施细节修正记录"path 错估" + "lint 字节级要求降级为 grep --fallback ≥1"
- testing 自补 SHA256 hash check 是临时方案，长期需契约化

## 评估方案

加 `harness validate --contract skill-body-consistency`：

- 扫 `.claude/commands/` + `.kimi/skills/` + `.qoder/commands/` + `.codex/skills/` 下所有 `harness-*.md` / SKILL.md
- 对每个 skill name（如 `harness-requirement`）按平台聚合，提取 body block（去除 frontmatter）
- 计算 4 平台 body SHA256；任一不同则 FAIL，输出 diff
- 列入 `harness validate --contract all`

## 影响面

- 新文件：`src/harness_workflow/validate_skill_body.py`（约 100-150 行）
- `cli.py` validate 子命令 choices 加 `skill-body-consistency`
- 测试：`tests/test_validate_skill_body_consistency.py`

## 工程量评估

- 1 chg，约 200 行代码 + 测试，约 2 小时工时

## 承载需求

- 触发：req-56 chg-03 implement + testing 阶段
- 承载：中优先级 sug，可与 sug-75 / sug-76 合并成"acceptance & cli 工具补齐"小 req
