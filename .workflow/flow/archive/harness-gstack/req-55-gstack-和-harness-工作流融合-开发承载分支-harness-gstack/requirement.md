---
id: req-55
title: "gstack 和 harness 工作流融合（开发承载分支 harness-gstack）"
created_at: 2026-05-07
operation_type: requirement
stage: analysis
---

## Goal

- 把 gstack（YC YC 风格 / 设计思维风格的工程辅助 skill 集合，MIT 协议，46 个 SKILL.md）作为 harness 工作流的"内置发布资产 + 角色行为契约"融入：harness install 时**自动 vendor 装载**全部 46 个 gstack skill 到 `~/.claude/skills/`（用户在 Claude Code 主对话即可直接 `/<skill-name>` 触发任意 gstack skill），同时把 harness 的角色 SOP 与 gstack 命令做**强映射**——本 req 范围内仅打通"analysis stage / analyst 角色 → /office-hours 命令"一条强映射，作为 gstack-harness 融合的最小可用集（minimum viable integration），后续 req-56 ~ req-59 按 1 角色 → 1 skill 渐进扩展（executing→/investigate / testing→/qa / acceptance→/review / regression→/codex）。
- 关键概念：**装载层全装，融合层渐进**——装载层一次到位（用户拿到 harness 立刻能用任何 gstack skill）；融合层按 req 渐进接入（避免一次性 adapter / role.md 改造工作量爆炸）。
- 用 req-55 自身的 analysis stage 做 dogfood 自适用活证（用户在主对话跑 /office-hours，主题 = req-55 本身；analyst 跑 adapter 把 design doc 重组覆盖本 requirement.md），**用本 req 自身验证本 req 设计的流程是否真能产出 harness 标准 requirement.md**。

## Scope

### Included

1. **chg-01 [chg-01:gstack 内置发布契约]**：vendor 全部 46 个 gstack SKILL.md（含 references / scripts 子资源）+ 顶层共享资源（gstack 仓库 bin/agents/scripts，SKILL.md 运行时依赖）+ MIT LICENSE-gstack + VERSION-gstack（含上游 commit hash + vendor 时间戳） → `src/harness_workflow/assets/gstack-skills/{skill-name}/`（每 skill 一目录）+ `src/harness_workflow/assets/gstack-skills/_shared/{bin,agents,scripts}/`（共享）；改 `install_local_skills` / `install_agent`（agent_kind=claude）加 gstack-skills 推送子流程，把 vendor 全集复制到 `~/.claude/skills/`；其它 agent_kind 跳过 + warn；`runtime.yaml.gstack_status` 字段记录 `installed_skills / vendor_version / last_install / agent_kind_compatible`；vendor 拉取脚本 `scripts/vendor-gstack.sh [skill-name|--all] [commit]`；`--force-gstack` flag 处理装载冲突；仓库根 README "Third-party vendored skills" 节列出全量 vendored skills + MIT 归因。
2. **chg-02 [chg-02:analyst-office-hours 强映射]**：analyst 角色 SOP 注入"调用 /office-hours + adapter 后处理"步骤——只改 `.workflow/context/roles/analyst.md` 一个文件，含触发协议（路径 α：subagent 不能直接调 slash skill，由主 agent / 用户兜底）+ adapter 章节 mapping 表（office-hours 设计文档 → harness requirement.md 章节映射）+ fallback 协议（office-hours 未跑 / gstack 未装 / 主 agent 拒派发 → 走原生 Step A1~A3 + warn）；新增 `.workflow/context/integrations/gstack/role-command-map.yaml`（极简 1 行映射 + 注释说明 req-56~59 渐进扩展计划）+ `.workflow/context/integrations/gstack/README.md`（≤ 50 行调用矩阵 + adapter mapping 压缩版 + 触发悖论说明）。
3. **chg-04 [chg-04:scaffold-v2 镜像]**：把 chg-02 的 analyst.md / role-command-map.yaml / README.md 同步镜像到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/...`；不镜像 vendor 副本（assets/gstack-skills/ 是 harness 仓库自有资产，不入 scaffold）。
4. **chg-05 [chg-05:dogfood 活证]**：用户在主对话跑 `/office-hours`，主题 = req-55 自身；office-hours 产出落 `~/.gstack/projects/{slug}/{user}-harness-gstack-design-{datetime}.md`（gstack 自身 user-level cache，原位保留）；analyst 跑 chg-02 adapter，把 design doc 重组**直接覆盖**本 requirement.md（同时覆盖第 7 轮手工 baseline）；retro 笔记入 `artifacts/project/experience/roles/analyst.md`。

### Excluded

- 一次性接入全部 5 个核心角色映射（推后续 req-56~59 渐进，每 req 接 1 角色）。
- 角色 ↔ gstack 命令一对多 / 多对一 的复杂映射、降级矩阵、备选命令池——本 req 仅"一对一无备选"。
- 契约 lint（chg-06 整体砍掉推后续 req）——本 req 仅打通最小可用集，lint 是稳定后的事。
- gstack 自动 CI 升级 / submodule / subtree 形态——本 req 用 vendor 复制快照 + 手工 vendor 脚本足够。
- 项目级 `.claude/skills/{skill-name}/` 副本——gstack 全局即可，多项目复用一套，不冗余。
- `artifacts/{branch}/.../gstack/` 子树 / 中央索引 / manifest / runs.jsonl / repository-layout 扩段（前 5 轮 Q7 全套设计因第 6 轮用户范式级修正"gstack 路径不需要"整体作废，gstack 产物经 adapter 后**就是** harness 标准 requirement.md，无独立归集路径）。

### 渐进扩展规划（路标，不在本 req 落地）

| req | 接入角色 → skill | 关键产物 |
|---|---|---|
| **req-55（本 req）** | analyst → /office-hours | analyst.md SOP 注入 + adapter / role-command-map.yaml 极简 1 行 |
| req-56 | executing → /investigate | executing.md 注入 + map 加 1 行 |
| req-57 | testing → /qa | testing.md 注入 + map 加 1 行 |
| req-58 | acceptance → /review | acceptance.md 注入 + map 加 1 行 |
| req-59 | regression → /codex | regression.md 注入 + map 加 1 行 |

## Acceptance Criteria

- **AC-01 [AC-01:vendor 全 skill 落盘]**：`src/harness_workflow/assets/gstack-skills/` 下含 46 个 skill 目录（每目录至少 SKILL.md + VERSION-gstack；含 references/ scripts/ 子资源若上游存在；per-skill LICENSE-gstack 在 harness install 推送到 ~/.claude/skills/ 时从 _shared 注入，vendor 副本目录本身不含独立 LICENSE-gstack）+ `_shared/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack}/` 顶层共享资源；`scripts/vendor-gstack.sh --all <commit>` 可一键拉取全集。
- **AC-02 [AC-02:harness install 自动装载]**：在干净项目跑 `harness install --agent claude` 后，`~/.claude/skills/` 下出现全部 46 个 vendored skill（每个含 SKILL.md + LICENSE-gstack）；用户在 Claude Code 主对话能直接 `/<skill-name>` 触发任意 gstack skill；agent_kind ≠ claude 时跳过 + warn 不阻塞 install。
- **AC-03 [AC-03:analyst 强映射文档化]**：`.workflow/context/roles/analyst.md` 在 Step A2 前嵌入"调用 /office-hours"步骤段（含触发协议 / adapter 后处理 SOP / fallback 协议），文档完整可复读；`role-command-map.yaml` 含 1 行 `analyst: [/office-hours]` 映射 + 注释说明渐进扩展规划。
- **AC-04 [AC-04:adapter 后处理 SOP 落地]**：analyst.md 含完整 adapter 章节 mapping 表——office-hours 设计文档（startup / builder mode）的 Problem Statement / Demand Evidence / Constraints / Recommended Approach / Success Criteria / Next Steps / The Assignment 等核心段落，可机械重组到 harness requirement.md 的 Goal / Scope.Included / Scope.Excluded / Acceptance Criteria / Split Rules 五大段；多余段（Premises / Cross-Model Perspective / Open Questions / Distribution Plan / Dependencies / What I noticed / Reviewer Concerns）整体追加为 `## Office Hours Notes` 附加段保留思考价值。
- **AC-05 [AC-05:chg-05 dogfood 自适用活证]**：用户在 Claude Code 主对话跑 `/office-hours`（主题 = "gstack 和 harness 工作流融合"）→ 产出 `~/.gstack/projects/{slug}/{user}-harness-gstack-design-{datetime}.md`；analyst 跑 chg-02 adapter，把 design doc 重组**直接覆盖**本 requirement.md；diff 第 7 轮手工 baseline vs adapter 重组结果，retro 笔记进 `artifacts/project/experience/roles/analyst.md`。
- **AC-06 [AC-06:scaffold_v2 镜像同步]**：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 与 chg-02 改造完全一致；`scaffold_v2/.workflow/context/integrations/gstack/role-command-map.yaml` + `README.md` 与 chg-02 镜像；`harness validate --contract role-stage-continuity` 通过；不镜像 `assets/gstack-skills/` 副本到 scaffold（保持本 req 设计：vendor 资产是 harness 仓库自有）。
- **AC-07 [AC-07:License 归因合规]**：`assets/gstack-skills/_shared/LICENSE-gstack`（gstack MIT 全文复制）+ `_shared/VERSION-gstack`（含上游 https://github.com/.../gstack URL + commit + 版本 + vendor 时间）；推送到 `~/.claude/skills/` 时同步推 LICENSE-gstack 副本；harness 仓库根 README "Third-party vendored skills" 节列出全部 46 个 vendored skills + MIT 归因（YC office-hours / OpenAI codex / qa / review 等核心 skill 单独点名 attribution）。
- **AC-08 [AC-08:runtime.yaml gstack_status 字段]**：`runtime.yaml.gstack_status` 含 `installed_skills: [...]`（已装 skill 名清单）/ `vendor_version: <hash>` / `last_install: <iso8601>` / `agent_kind_compatible: true|false` 四子字段；schema 加入 .workflow 校验；装载失败回退：warn + `runtime.yaml.gstack_run_log` 追加。

## Split Rules

### chg 拆分原则（4 个 chg，编号断号保留 chg-03）

- **chg-01 vendor + 自动装载**（最前置无依赖）：硬产物——vendor 副本目录 + vendor 脚本 + install 推送逻辑 + runtime schema + License 归因 + 仓库根 README 段。装载层全装，是后续所有融合 chg 的物质基础。
- **chg-02 analyst → /office-hours 强映射 + adapter**（依赖 chg-01）：仅改 1 个角色 SOP 文件（analyst.md）+ 新增 1 个映射 yaml + 1 个 README，无代码改动；adapter 是文档化 SOP 不是代码工具——由 analyst 角色按 SOP 手工执行重组。
- **chg-03**（**作废占位**）：原"gstack 产出归集协议"在第 6 轮被用户范式级修正"gstack 路径不需要"整体作废；编号保留断号给后续可能的恢复（若未来 gstack 出 binary / 大文件需归集，可同 chg-03 槽位重启）；本 req 不建立 chg-03 目录。
- **chg-04 scaffold_v2 镜像**（依赖 chg-02）：把 chg-02 的 analyst.md + role-command-map.yaml + README 同步进 scaffold_v2，不镜像 vendor 副本。
- **chg-05 dogfood 活证**（依赖 chg-01 / chg-02 / chg-04）：用 req-55 自身验证 office-hours → adapter → requirement.md 全链路；用户主对话跑 /office-hours，analyst 跑 adapter 重组覆盖本 requirement.md；retro 笔记落 `artifacts/project/experience/roles/analyst.md`。

### 渐进扩展原则（后续 req 套用）

每个后续 req 套用相同 4-chg 模式（**chg-01 vendor + chg-02 角色 SOP 注入 + chg-04 mirror + chg-05 dogfood**），仅范围收窄到本 req 引入的 1 个新角色 → 1 个新 skill 一对一映射；vendor 全集已在 req-55 一次到位，后续 req 的 chg-01 退化为"调 vendor 脚本拉新版本"或"无 vendor 步骤"。

## Office Hours Notes

> **占位说明（第 7 轮 baseline）**：本节为 chg-05 dogfood 跑 /office-hours + adapter 后由 analyst 自动填入；当前为前 6 轮 analyst 深谈的 baseline 手工填实版本。chg-05 落地时 adapter 重组的 design doc 中的 Premises / Cross-Model Perspective / Open Questions / Distribution Plan / Dependencies / What I noticed / Reviewer Concerns 等附加段会**追加**到本节末尾，本说明段保留作为版本演进证据。
>
> **本 req 前 6 轮深谈关键留底**（待 chg-05 dogfood 后用 office-hours 自带 Spec Review Loop 5 维度 + 3 轮迭代 + quality score 替换为机器化记录）：
>
> 1. **范式级修正轨迹**（第 6 轮用户原话"gstack的路径就不需要了啊"推翻前 5 轮 Y / Y' / Y'' / Y''' 全部归集落点候选）：从"gstack 是辅助工具，产物归集独立子树"演进到"gstack 命令直接产出 harness 标准产物，没有独立路径"。
> 2. **触发悖论解决**（subagent 不能派发 slash command）：路径 α default-pick = analyst.md SOP 文档化"提示主 agent / 用户跑 /office-hours，反馈 path 后 analyst 跑 adapter"；analyst = adapter 消费者；主 agent / 用户 = /office-hours 真正调用者。
> 3. **office-hours 意外收益**：自带 Spec Review Loop（5 维度 / 3 轮迭代 / quality score）= harness analysis stage 当前缺失的质量门；adapter 不需要砍 Reviewer Concerns，直接保留追加。
> 4. **Q-B Q8.2 vendor 范围（第 7 轮拍板修正）**：装载层从"仅 office-hours"扩到"全部 47 个 gstack skill"；融合层（角色 SOP 强映射）仍仅 analyst → /office-hours；理由：装载成本不高（47 个 SKILL.md + 共享 bin/scripts，估算总体积约 数 MB～几十 MB 量级，远小于 gstack 全仓库 1.1G 含 .git/build/node_modules）+ 价值高（用户立即能用任何 gstack skill，不必等 harness 增量接入）。
> 5. **vendor 实际依赖性结论**（第 7 轮调研）：`~/.claude/skills/<skill-name>/SKILL.md` 全部为符号链接指向 `~/.claude/skills/gstack/<skill-name>/SKILL.md`；47 skill 目录加起来仅 384 KB（仅符号链接元数据）；SKILL.md 内嵌 `~/.claude/skills/gstack/bin/gstack-{update-check,config,telemetry-log,repo-mode,slug}` 等二进制调用——vendor 需把每个 skill 的 SKILL.md 实体复制 + gstack 仓库顶层 bin/agents/scripts（运行时依赖）一并 vendor 到 `_shared/`。
