---
id: req-56
title: "harness requirement 默认调 /office-hours，--fallback 走原生 analyst，产出强制对齐 harness 文档规范"
created_at: 2026-05-09
operation_type: requirement
stage: analysis
---

## Goal

- 把 `harness requirement` 入口默认行为切到 gstack `/office-hours` 强映射，降低 analyst 每次手工 offer 选择带来的对话往返成本，让"默认即最佳路径"。
- 提供 `--fallback` 显式 opt-out 标志，保留原生 analyst Step A2 路径作 escape，避免小需求被 office-hours 重型流程压死。
- 强制两条路径的最终 requirement.md 在路径、frontmatter、章节结构上 100% 对齐 harness 文档规范，`/office-hours` 产出的 design doc 仅作 lineage 留底。

## Scope

### Included

- **CLI**：`harness requirement` 加 `--fallback` 参数（argparse），落地到 req-state.yaml 字段 `office_hours_mode: required | fallback`。
- **状态 schema**：`.workflow/state/requirements/req-{id}-{slug}.yaml` 新增顶层 `office_hours_mode` 字段；老历史 req（无该字段）按 `required` 兼容，不破坏 archived req。
- **环境兜底**：CLI 检测 `runtime.yaml.gstack_status.agent_kind_compatible`；为 `false` 时即使无 flag 也自动 fallback，stdout 打印 `[gstack] agent 不兼容，本 req 自动 fallback 模式` 警告。
- **analyst 改造**：`.workflow/context/roles/analyst.md` Step A1.5 改读 `office_hours_mode` 字段直跑，删 offer 选择句式；保留场景 3 escape（用户/主 agent 显式拒派发时打印 warn 转 fallback，不阻塞）。
- **adapter SOP 强制不绕过**：office-hours 产出的 design doc（原位 `~/.gstack/projects/{slug}/...md`）仅作 lineage 留底；最终 requirement.md 必须按 Step A1.5.adapter 段映射表重组覆盖到 `.workflow/flow/requirements/req-{id}-{slug}/requirement.md`，frontmatter（id / title / created_at / operation_type / stage）+ 章节（Goal / Scope / Acceptance Criteria / Split Rules）与 `.workflow/flow/repository-layout.md` §3 + `assets/templates/requirement.md.tmpl` 完全一致。
- **skill 透传**：`.claude/skills/harness-requirement/SKILL.md` + 等价 `.kimi` / `.qoder` 镜像同步 `--fallback` 用法说明。
- **测试**：单元（CLI argparse + state schema 读写）+ 集成（fallback / office-hours 双路径 dogfood）+ 契约（artifact-placement / human-docs 复用既有 lint）。

### Excluded

- `/office-hours` skill 自身行为不改（只是从被动 offer 改为默认调用）。
- 其他 stage 角色（executing / testing / acceptance / regression / done）→ gstack 强映射不在本 req（chg-05 deferred 候选 P 路径仍由后续 req 兑现）。
- gstack vendor 版本升级 / 新 skill 引入不在本 req。
- "joint review 联动复核"老题目作废，如确需另立 req（与本次方向无承接）。
- `/office-hours` design doc 自动归档到 harness artifacts 不在本 req（`~/.gstack/` 原位即 lineage 已足够）。

## Acceptance Criteria

- **AC-01**：`harness requirement "X"`（无 flag）→ req-state.yaml 含 `office_hours_mode: required`；analyst 进入 Step A1.5 不再 offer 选择，直接 batched-report 让用户跑 `/office-hours`。
- **AC-02**：`harness requirement "X" --fallback` → req-state.yaml 含 `office_hours_mode: fallback`；analyst 跳过 path α 直接 Step A2，stdout 含 `[mode] fallback` 提示。
- **AC-03**：`gstack_status.agent_kind_compatible == false` 时，即使无 flag 也自动 fallback，CLI stdout 含 `[gstack] agent 不兼容` 警告字样；req-state.yaml `office_hours_mode: fallback`。
- **AC-04**：老历史 req（state 文件无 `office_hours_mode` 字段）兼容：默认按 `required` 跑，不破坏 archived req；契约 lint 不报错。
- **AC-05**：`tests/installer/` 加单元 + `tests/integration/` 加 dogfood TC，覆盖 4 种 (flag × 兼容性) 组合：(无 flag, true) / (无 flag, false) / (--fallback, true) / (--fallback, false)。
- **AC-06**：`harness validate --human-docs` exit 0；`harness validate --contract artifact-placement` exit 0。
- **AC-07**：两条路径（fallback / office-hours）的最终 `requirement.md` 必须满足：
  - 路径：`.workflow/flow/requirements/req-{id}-{slug}/requirement.md`
  - frontmatter 5 字段齐全（id / title / created_at / operation_type / stage）
  - 章节齐全（Goal / Scope / Acceptance Criteria / Split Rules）
  - `harness validate --human-docs` exit 0
  - `harness validate --contract artifact-placement` exit 0

  对 office-hours 路径，验证发生在 adapter 重组完成后、Step A1.5 退出前；
  对 fallback 路径，验证发生在 Step A3 末尾；两条路径走同一道 validate 关卡。

## Split Rules

按"CLI/状态 → 角色协议 → skill/测试" 自下而上拆 3 chg，依赖严格线性：

- **chg-01（CLI + state schema + 兼容性兜底）**：
  - `harness requirement` argparse 加 `--fallback`
  - req-state.yaml 写入 `office_hours_mode: required | fallback`
  - 检测 `gstack_status.agent_kind_compatible == false` 时自动 fallback + stdout 警告
  - 老历史 req 兼容（缺字段按 required 解读）
  - 单元测试：4 种组合 + 老 req 兼容场景

- **chg-02（analyst.md Step A1.5 改造 + adapter 强制门）**：
  - 改 `.workflow/context/roles/analyst.md` Step A1.5：读 `office_hours_mode` 字段直跑，删 offer 选择句式
  - 保留场景 3 escape（拒派发时 warn 转 fallback）
  - **强化 adapter SOP**：段映射表标"必经"，加退出门"`harness validate --contract artifact-placement` exit 0 才能离开 Step A1.5"
  - 不允许"office-hours design doc 直接当 requirement.md 用"绕道
  - 依赖 chg-01 字段已落地

- **chg-03（skill 文档透传 + dogfood TC）**：
  - `.claude/skills/harness-requirement/SKILL.md` + `.kimi` / `.qoder` 镜像加 `--fallback` 用法说明
  - 集成测试 dogfood TC：跑 fallback 路径产出 + 跑 office-hours 路径产出（mock /office-hours）后断言 requirement.md 落对路径 + 含 5 字段 frontmatter + 4 章节
  - 依赖 chg-01 / chg-02 已落地

执行顺序：chg-01 → chg-02 → chg-03（严格线性）。
