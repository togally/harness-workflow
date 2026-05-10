---
id: chg-03
title: "skill 文档（claude/kimi/qoder）透传 --fallback 用法 + 双路径 dogfood TC"
created_at: 2026-05-09
operation_type: change
requirement_id: "req-56"
---

# Change

## 1. Title

skill 文档（claude / kimi / qoder）透传 --fallback 用法 + 双路径 dogfood TC

## 2. Goal

- 把 chg-01 落地的 `--fallback` 用法 + chg-02 的 Step A1.5 行为差异在用户可见的 skill 文档（`.claude` / `.kimi` / `.qoder` 三套 harness-requirement skill 镜像）写清楚。
- 加 dogfood 集成 TC 覆盖 fallback 路径与 office-hours 路径的端到端 requirement.md 落盘检查（路径 + frontmatter 5 字段 + 4 章节齐全）。

## 3. Requirement

- `req-56`

## 4. Scope

### Included

- `.claude/skills/harness-requirement/SKILL.md`：在 ARGUMENTS 段下方追加"## --fallback 标志说明"段（≤ 30 行）。
- `.kimi/skills/harness-requirement/SKILL.md` + `.qoder/skills/harness-requirement/SKILL.md`：与 .claude 1:1 镜像。
- `tests/integration/test_req56_fallback_dogfood.py`（新增 ~150 行）：
  - TC-01：fallback 路径端到端：subprocess `harness requirement "X" --fallback` → 断言 state.yaml.office_hours_mode=fallback / requirement.md 落 `.workflow/flow/requirements/req-{id}-{slug}/` / frontmatter 5 字段 / 4 章节齐全（grep `^## Goal` / `^## Scope` / `^## Acceptance Criteria` / `^## Split Rules` 各命中 1）
  - TC-02：office-hours 路径端到端（mock /office-hours 不存在 → 走 escape 子分支 → 与 fallback 同效果，但 state.yaml.office_hours_mode 保持 required 作 lineage 留底）
  - TC-03：harness validate --human-docs / --contract artifact-placement 双绿断言

### Excluded

- 不改 CLI（chg-01 负责）
- 不改 analyst.md（chg-02 负责）
- 不引入新 lint 契约（既有 artifact-placement / human-docs 已覆盖）

## 5. Acceptance

- 覆盖 requirement.md 的 **AC-05（dogfood 部分）/ AC-07（双路径产出格式对齐）**：
  - .claude / .kimi / .qoder 三镜像 skill 文档 grep `--fallback` 各命中 ≥ 1
  - tests/integration/test_req56_fallback_dogfood.py 3 用例全 PASS
  - 端到端 requirement.md 路径 + frontmatter + 章节核验通过

## 6. Risks

- **risk-1 三镜像漂移**（bugfix 历史前车之鉴）：缓解 = chg-03 实施时一次 cp 三份 + grep 自检三份内容字节级一致。
- **risk-2 office-hours 路径无法在测试里端到端跑**（/office-hours 是 Claude Code skill，pytest 子进程跑不到）：缓解 = mock 该 skill"不可用"路径，覆盖 escape 子分支；office-hours 真路径靠 chg-05 dogfood 候选 P 在真实使用时兑现（非本 chg）。
- **risk-3 跨平台 skill 文档增量失同步**：缓解 = 加一行 grep 三镜像内容同 hash 的轻量 lint，未来加入 contract（本 chg 不引契约，记 sug）。
