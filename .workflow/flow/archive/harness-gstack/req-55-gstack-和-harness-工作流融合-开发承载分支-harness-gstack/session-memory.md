# Session Memory — req-55（gstack 和 harness 工作流融合）

## 1. Current Goal

为 req-55（gstack 和 harness 工作流融合（开发承载分支 harness-gstack））完成 analysis stage：
- 与用户深谈，把 requirement.md 的 Goal / Scope / Acceptance Criteria 填实
- 按 analyst 职责拆 changes（chg-NN），每个独立可交付，写 change.md + plan.md
- 完成后按 stage_policies analysis = user 停下，等用户拍板

## 2. Context Chain

- Level 0: 用户 → /harness-requirement
- Level 0.5: 主 agent / harness-manager（创建 req-55 骨架、切到 harness-gstack 分支）
- Level 1: analyst（本派发，opus，本会话）

## 3. 角色加载链自检（role-loading-protocol Step 0~7.6.1）

- [x] Step 1: runtime.yaml 已读（current_requirement=req-55, stage=analysis, conversation_mode=open）
- [x] Step 2: WORKFLOW.md / .workflow/tools/index.md / project-overview.md 已读
- [x] Step 3: 在 .workflow/context/index.md 确认 role=analyst
- [x] Step 4-6: base-role.md → stage-role.md → analyst.md 已读
- [x] Step 7: 经验文件 .workflow/context/experience/roles/analyst.md 已读；风险文件 constraints/risk.md 已读；repository-layout.md 已读
- [x] Step 7.5 模型一致性自检：briefing 期望 = opus，实际运行 model 由 runtime 注入；本派发 briefing 显式指定 expected_model=opus，与 role-model-map.yaml `roles.analyst.model = opus` 一致
- [x] Step 7.6 项目级覆盖：扫 artifacts/project/{constraints,experience,tools}/
  - constraints: index.md（含 1 真实条目 `coding/测试-rule.md`，但该文件不存在 → 静默跳过；其余 1 行示例占位）
  - experience/{roles,risk,tool,regression,stage}: 5 个 index.md 全为示例占位，无真实条目命中
  - tools: index.md 无 catalog 条目
  - 真实命中数 = 0（仅 6 个 index.md 模板骨架，无实际可加载条目）
- [x] Step 7.6.1 索引懒加载：scope=experience-roles → 命中 0；scope=constraints → 命中 0（"测试-rule.md" 文件不存在，本不应在 index 中标 always，留作后续 sug 修整目标）

## 4. 用户已对齐的关键决策（来自主 agent 派发说明 + 用户对 Q1~Q5 回应 + 第 3 轮 Q7 修正 + 第 5 轮 Q7.2 落点精确修正 + 第 6 轮范式级概念修正）

| 项 | 已对齐内容 |
|---|---|
| 题目 | "gstack 和 harness 工作流融合（开发承载分支 harness-gstack）" |
| 承载分支 | `harness-gstack`（已 checkout） |
| 题目原话 | "切换分支harness-gstack，改分支作用主要是开发gstack和harness流程融合" |
| **Q1 融合方向** | **方向 a 强化版**：角色 ↔ gstack 命令的"强映射"——某角色在执行时直接就是调用 gstack 的某个命令（不是"提示推荐"，而是"角色 = gstack 命令 / gstack 命令组合"） |
| **新增前置约束（用户提点 1）** | 必须保障执行 harness 的 agent 已装 gstack——融合落地的前置条件是 gstack 安装契约 |
| ~~新增产出约束（用户提点 3，第 3 轮精确修正）~~ | **第 6 轮已作废**：原"gstack 产物 = 制品需归集 artifacts/" 命题被用户范式级修正推翻；gstack 产物**就是**对应 stage 的标准产物（requirement.md / change.md / plan.md），**没有独立归集路径** |
| ~~Q7.2 落点精确修正（用户第 5 轮原话）~~ | **第 6 轮已作废**：原讨论"落点在 artifacts/{branch}/.../gstack/" 整体作废；产物直接落 `.workflow/flow/requirements/{req-id}/requirement.md` 现有标准位置 |
| **第 6 轮范式级概念修正（用户原话）** | "gstack的路径就不需要了啊，它生成的就是需求文档，后续的步骤就要根据这个阶段的需求文档来生成了"——**推翻** Y / Y' / Y'' / Y''' 全部候选；不需要任何独立 gstack/ 子目录；office-hours 的输出 = harness 工作流的**标准产物 requirement.md** 本身；下游 stage（executing/testing/acceptance）依赖的就是这个 requirement.md |

### 4.5 第 6 轮用户原话留底（范式级概念修正）

> "gstack的路径就不需要了啊，它生成的就是需求文档，后续的步骤就要根据这个阶段的需求文档来生成了"

主 agent 解析（已被 analyst 吸收）：

| 用户表述 | 落地约束 |
|---|---|
| "gstack 的路径就不需要了" | **推翻** Y''' / Y'' / Y'——根本不需要 `gstack/` 子目录或任何独立归集路径 |
| "它生成的就是需求文档" | **关键概念转变**：office-hours 的输出 = harness 工作流的**标准产物**（requirement.md），不是辅助/参考文档 |
| "后续的步骤就要根据这个阶段的需求文档来生成了" | 工作流的下游 stage（executing/testing/acceptance）依赖的就是这个 requirement.md；gstack 产物就是 requirement.md 本身 |

**根本范式转变**：

| 旧设计（前 5 轮） | 新设计（第 6 轮用户本轮） |
|---|---|
| gstack 是"辅助工具"，产物归集到独立子树 | gstack 命令**直接产出**工作流标准产物（requirement.md / change.md / plan.md） |
| 角色 SOP = 调 gstack + 把 gstack 产物归集 + analyst 自己再写 requirement.md | 角色 SOP = 调 gstack → gstack 产物**就是**该 stage 的标准产物（含必要的 adapter 后处理） |
| 需要 `artifacts/{branch}/requirements/.../gstack/{chg}/{skill}-{ts}/` + manifest + index + runs.jsonl | **不需要**，产物直接落 `.workflow/flow/requirements/{req-id}/requirement.md` 现有标准位置 |
| Q7 整套（双写 / 落点 / 归集协议 / 中央索引 / repository-layout 扩段）成立 | **Q7 整套作废 / 退化为 trivial**：无独立归集路径，无中央索引，无 layout 扩段 |
| chg-03 = gstack 产出归集协议 | **chg-03 砍掉 / 合并到 chg-02**（adapter 后处理并入 chg-02 强映射） |

### 4.4 第 5 轮用户原话留底（Q7.2 落点精确修正）

> "qc制品跟对人文档放在一起，也就是和分支和需求有关"

主 agent 解析（已被 analyst 吸收）：

| 用户表述 | 对前轮决策的影响 |
|---|---|
| "制品跟对人文档放在一起" | 按 repository-layout.md §2，对人文档落 `artifacts/{branch}/requirements/{req-id}-{slug}/`；用户要 gstack 制品**与对人文档同处一层 / 兄弟级别** |
| "和分支和需求有关" | 路径必须**含 branch + req-id**（甚至 chg-id），即 **branch-aware + req-aware**；**不是**项目级集中归集 |
| 间接含义 | **推翻** 第 3 轮 Q7.2 候选 X（`artifacts/project/integrations/gstack/runs/{req-id}/{chg-id}/...`）——错把 gstack 制品归入项目级机器型集成元数据 |
| 间接含义 | 倾向第 3 轮一度被拒的候选 Y 方向（按 branch + req 归属），但需要解决其 layout §3.1 (i) 「扁平无 changes/ 子目录」的契约扩段问题 |
| 与 req-52 "跟项目走"原则的协调 | 不矛盾：`artifacts/project/` 跟项目走（管 constraints/experience/tools 项目级机器型）；`artifacts/{branch}/` 跟 branch + req 走（管 branch + req 级对人产物）；gstack 制品归后者 |

### 4.3 第 4 轮用户原话留底（范围收窄 + 内置 gstack）

> （A）"咱们一步步融入吧，这次先融入需要将需求分析改为调用 office-hours 命令"
> （B）"还有就是 gstack 能不能内置其某个版本的，harness install 的时候自动给对应的 agent 装载"

主 agent 解析（已被 analyst 吸收）：

| 用户语义 | 对前轮决策的影响 |
|---|---|
| "一步步融入" | 推翻 Q2.1 = 核心 5 角色 → 渐进分批：本 req 仅做 analyst → /office-hours 一条强映射；后续 req-56 / req-57 各扩 1~2 条（executing→/investigate；testing→/qa；acceptance→/review；regression→/codex） |
| "需求分析改为调用 office-hours" | analysis stage = analyst 角色 SOP 内嵌"调用 /office-hours"步骤；映射粒度收窄到"一对一"，无备选无降级矩阵（最小可用集） |
| "gstack 能不能内置其某个版本" | Q6 升级为 Q8：从"检测 + 引导用户自装"升级为"harness 主动 vendor + 自动装载"——把 gstack（或子集）当作 harness 自身的内置资产 |
| "harness install 的时候自动给对应的 agent 装载" | 装载时机 = harness install / install --agent；装载目标 = 与 harness skill 同样的 `~/.claude/skills/{skill-name}/` 全局目录（与现有 install_agent 机制类比） |

新增 dogfood 活证（用户没明说但是 implicit）：用 req-55 自身的 analysis 跑过一次 /office-hours，把产出归集到 `artifacts/project/integrations/gstack/runs/req-55/...`——这是闭环验证。

### 4.1 第 3 轮用户原话留底（Q7 精确修正）

> "gstack产物多是文档，需要放到制品仓库所属的文件夹汇总"

主 agent 解析（已被 analyst 吸收）：

| 原话片段 | 对 Q7 的影响 |
|---|---|
| "gstack 产物多是文档" | 性质判定：plan / design / qa 报告 / context-save 是 markdown / yaml / 文本 → 属"制品（artifacts）"性质（对人可读），非元数据 |
| "放到制品仓库" | **关键约束**：落点必须在 `artifacts/` 子树（与 repository-layout §1 子树语义匹配："对人可读签字执行产物"）；**禁落** `.workflow/flow/`（后者是工作流引擎元数据） |
| "所属的文件夹" | 暗示按归属层级管理（按 req-id / chg-id / 按 project 项目级归集需在 default-pick 中给候选并比选） |
| "汇总" | 暗示要有"集中归集索引"——不仅"放进去"，还要"可被检索 / 可见全貌"（manifest.json / index.md 类索引文件） |

### 4.1 用户原话留底

> "我觉得我们要先沟通一下融合思路。1.要保障用户所用agent装了gstack 2.我们可以给角色直接映射到对应的gstack命令上，这个角色在执行的时候就是使用gstack的某个命令，然后是否要控制下gstack的产出，产出放在哪里"

### 4.2 主 agent 解析（已被 analyst 吸收）

- 用户先沟通"融合思路" → 拒绝 default-pick d，要求重新讨论方向
- 提点 1（agent 装 gstack）→ 新议题 Q6（gstack 安装前置契约）
- 提点 2（角色 = gstack 命令）→ Q1 锁定为方向 a 强化版（极致映射，不是提示）
- 提点 3（产出控制 + 落点）→ 新议题 Q7（gstack 产出归集契约）

## 5. 关键背景调研（与用户开口前）

### 5.1 gstack 是什么

- 用户全局 ~/.claude/skills 下 ≥ 47 个 SKILL.md 风格 skill 集合（来自全局 CLAUDE.md 列表 + 本机文件系统验证）
- gstack 仓库 clone 在 `~/.claude/skills/gstack/`（含 AGENTS.md / SKILL.md.tmpl / bin/gstack-* 工具链）
- 主要 capability 大类：
  1. **Plan-mode reviews**：office-hours / plan-ceo-review / plan-eng-review / plan-design-review / plan-devex-review / autoplan / design-consultation
  2. **Implementation + review**：review / codex / investigate / design-review / design-shotgun / design-html / qa / qa-only / scrape / skillify
  3. **Release + deploy**：ship / land-and-deploy / canary / landing-report / document-release / setup-deploy / gstack-upgrade
  4. **Operational + memory**：context-save / context-restore / learn / retro / health / benchmark / cso / setup-gbrain / sync-gbrain
  5. **Browser + agent**：browse / open-gstack-browser / setup-browser-cookies / pair-agent
  6. **Safety + scoping**：careful / freeze / guard / unfreeze / make-pdf
- 触发方式：Claude Code 内 `/skill-name`，每个 skill 是一个独立 SKILL.md preamble
- 无统一 CLI 入口（`gstack` / `gs` 命令未注册，`bin/gstack-*` 是 skill 内部 helper）

### 5.2 harness 是什么（本仓库）

- 本仓库即是 harness-workflow 系统
- 当前工作流：5-stage（analysis → executing → testing → acceptance → done）+ regression 旁路
- 当前角色：analyst / executing / testing / acceptance / regression / done / harness-manager / tools-manager / reviewer / project-reporter / technical-director
- CLI 入口：harness install / update / status / validate / next / ff / requirement / change / bugfix / archive / rename / migrate / suggest / regression / feedback / pad / language / enter / exit / tool-search / tool-rate / init
- 关键资源：.workflow/state/runtime.yaml / .workflow/flow/requirements/ / artifacts/project/ / src/harness_workflow/skills/harness/SKILL.md（被 harness install 推送到 ~/.claude/skills/harness/SKILL.md）

### 5.3 当前两侧入口已经"擦边并存"

- 用户的 ~/.claude/skills/ 下已经同时存在 gstack/ 与 harness/ 两套 skill
- 但二者各自独立运行：gstack 走 `/skill-name` 内嵌 skill prompt；harness 通过 `/harness-xxx` 触发并进入 .workflow/ 状态机；二者无桥接、无公共上下文，融合点尚未定义

### 5.4 第 4 轮 gstack vendor 可行性调研（Q8 准备）

| 维度 | 调研结论 | 引用 |
|---|---|---|
| **gstack 仓库形态** | git clone @ `~/.claude/skills/gstack/`；remote=`https://github.com/garrytan/gstack.git`；HEAD `c7aefc1 v1.26.5.0`（**无 git tag**——tag --list 空）；版本号在 `VERSION` 文件 = `1.26.5.0` | `git -C ~/.claude/skills/gstack/ remote -v` / `git tag --list` / `cat VERSION` |
| **gstack 总规模** | 1.1G / 13938 文件 / 465 个 SKILL.md；其中 node_modules 719M、.git 7.8M——**核心源文件 ≈ 374M**（含 docs / lib / 47 个 skill 子目录 / bin/ 工具链） | `du -sh ~/.claude/skills/gstack/` |
| **office-hours 单 skill 体积** | `~/.claude/skills/gstack/office-hours/` = 164K（仅 SKILL.md 2050 行 + SKILL.md.tmpl 943 行）——**极小，可直接 vendor 一份副本** | `du -sh ~/.claude/skills/gstack/office-hours/` |
| **License** | **MIT**（Garry Tan 2026）——**允许 vendor / fork / redistribute**，需保留 copyright + permission notice | `~/.claude/skills/gstack/LICENSE` |
| **跨 agent 兼容** | gstack AGENTS.md 第一句：「Skills live in `.agents/skills/` (or `~/.claude/skills/gstack/` on Claude Code）」——**主要面向 Claude Code**；触发方式为 `/skill-name`（slash command），**强依赖 Claude Code 的 skill 加载机制**；Codex / Kimi / Qoder 是否能解析 gstack SKILL.md frontmatter（preamble-tier / triggers / gbrain）尚未在 gstack 文档明示——保守判断**仅 Claude Code 必启用 gstack 装载**（其他 agent 暂走 fallback 原生 SOP） | `~/.claude/skills/gstack/AGENTS.md` 第 9 行 |
| **harness 现有 install 机制** | install_agent / install_local_skills 把 `assets/skill/`（即本仓库 `src/harness_workflow/assets/skill/`）整棵复制到 `.{agent}/skills/harness/`；`SKILL_ROOT = PACKAGE_ROOT/assets/skill`；`_copy_tree` 递归复制；force=True 时先 rmtree——**已有"vendor 一份资产 + 推到目标 agent 目录"的成熟管线**，gstack vendor 完全可复用此模式 | `workflow_helpers.py` L38 / L2516 / L2535 / L7935 |
| **office-hours skill 在用户机的状态** | `~/.claude/skills/office-hours/` 目录存在但**空**（0B）——而 `~/.claude/skills/gstack/office-hours/SKILL.md` 才是真源；说明 gstack 安装时是把每个 skill 从 `gstack/{skill}/` 拷贝到 `~/.claude/skills/{skill}/`（用户机上拷贝失败 / 软链断了），意味着**harness 自己 vendor 一份直接推到 `~/.claude/skills/office-hours/SKILL.md` 是合理路径**，绕开 gstack 自身的安装步骤 | `ls ~/.claude/skills/office-hours/` |
| **vendor 路径建议** | `src/harness_workflow/assets/gstack-skills/office-hours/SKILL.md`（new）+ `LICENSE-gstack`（贴 gstack MIT 全文 + 引用）+ `VERSION-gstack`（记 vendor 来源 commit `c7aefc1` / 版本 `1.26.5.0` / vendor 时间）；harness install 时类比 `_copy_tree(SKILL_ROOT, target)` 加一段 `_copy_tree(GSTACK_SKILLS_ROOT/{name}, ~/.claude/skills/{name}/)` | 综合上述 |
| **版本锁定方式对比** | (a) **复制快照 + VERSION-gstack 文件**（最简，不引 git submodule，不污染依赖；升级 = 重跑 vendor 脚本拉新快照覆盖 + 更新 VERSION）；(b) git submodule（依赖外部仓库；可控但增加 clone 复杂度 + 强行锚 commit）；(c) git subtree（介于 a/b 之间，merge 合并 gstack 上游，复杂）——**推荐 a（复制快照）**：harness 自己已有 assets 模式，gstack-skills 当作 vendored 资产管理即可 | 综合 |
| **范围（vendor 多少 skill）** | (a) 仅 office-hours（本 req 只用这一个，体积 164K，极小）—— **推荐 a**；(b) 一次 vendor 全 47 个（374M，仓库膨胀严重，且大部分本 req 不用）；(c) 增量扩（每 req 增加一个映射时同步 vendor 对应 skill）—— a + c 组合：本 req vendor 1 个，后续 req 各加 1~2 个 | 综合 |

**Q8 default-pick 候选合成**（基于上述调研）：

- 内置形态：**vendor 复制快照**（路径 `src/harness_workflow/assets/gstack-skills/{skill-name}/`，含 SKILL.md / LICENSE-gstack / VERSION-gstack）
- 装载时机：**harness install / harness install --agent**（复用现有 install_agent 管线，加一段 gstack-skills 推送）
- 装载目标：**全局 `~/.claude/skills/{skill-name}/`**（与 gstack 自身的目录布局一致，避免双轨；项目内 vendor 副本仅在 harness 仓库自身存在，不推到目标项目目录）
- 跨 agent 处理：**仅 Claude Code 启用**（agent_kind=claude 时跑装载步骤；codex / kimi / qoder 跳过 + warn "gstack 仅 Claude Code 启用"——不阻塞）
- 范围：**仅 vendor 本 req 用到的 skill**（本 req = 仅 office-hours；后续 req 增量扩；不一次性 vendor 全 47 个）
- License 合规：vendor 副本根目录贴 gstack MIT 原文 + 在 LICENSE-gstack 头部加 vendor 来源声明（commit / 版本 / 时间 / upstream URL）

**与 Q6 的关系**：Q8 落地后 Q6（安装前置契约）**大幅简化**——
- Q6.1 检测时机：harness install 主动装载，无需"检测"——退化为"install 时同步推送"
- Q6.2 检测失败处理：装载失败时记 warn + state log（与 Q7.4 失败回退共用 sink）
- Q6.3 跨 agent：与 Q8 的"仅 Claude Code 启用"对齐
- Q6.4 检测产物落点：仍 runtime.yaml `gstack_status: {installed_skills: [...], vendor_version, last_install}`，但语义从"检测结果"变为"vendor 装载结果"

### 5.5 第 6 轮 /office-hours 输出格式 vs harness requirement.md 模板对齐调研

**office-hours SKILL.md 关键事实**（来源：`~/.claude/skills/gstack/office-hours/SKILL.md` Phase 5 / 第 1525~1662 行）：

| 维度 | 调研结论 | 引用 |
|---|---|---|
| **输出落盘位置** | `~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md`（注意：**不在仓库内**，落用户主目录 `~/.gstack/`，相当于 gstack 自身的 user-level cache） | SKILL.md L1543 |
| **设计文档命名约定** | `{user}-{branch}-design-{datetime}.md`，设计血脉链通过 `Supersedes:` 字段链接同分支前一版本 | SKILL.md L1539~1541 |
| **输出格式** | Markdown，含 frontmatter 风格头部（`# Design: {title}` / `Generated by` / `Branch:` / `Repo:` / `Status: DRAFT` / `Mode: Startup\|Builder` / `Supersedes:`）+ 多段 markdown 章节 | SKILL.md L1550~1609（startup mode）/ L1611~1662（builder mode） |
| **startup mode 章节** | Problem Statement / Demand Evidence / Status Quo / Target User & Narrowest Wedge / Constraints / Premises / Cross-Model Perspective / Approaches Considered / Recommended Approach / Open Questions / Success Criteria / Distribution Plan / Dependencies / The Assignment / What I noticed about how you think | SKILL.md L1560~1609 |
| **builder mode 章节** | Problem Statement / What Makes This Cool / Constraints / Premises / Cross-Model Perspective / Approaches Considered / Recommended Approach / Open Questions / Success Criteria / Distribution Plan / Next Steps / What I noticed about how you think | SKILL.md L1623~1662 |
| **Spec Review Loop**（Phase 5 后） | office-hours 自带"派发 reviewer subagent + 5 维度评审 + 最多 3 轮迭代 + 收敛保护"机制；产出 quality score 1-10 + Reviewer Concerns 段（若有） | SKILL.md L1666~1729 |
| **触发方式** | Claude Code 内 `/office-hours` slash command（必须用户在主对话调用；**subagent 不可派发触发**——slash skill 是用户面入口） | SKILL.md L1148 (skill invocation during plan mode) + 整体 design |
| **HARD GATE** | "Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action. Your only output is a design document." | SKILL.md L798 |

**harness requirement.md 标准模板**（来源：req-55/requirement.md，本仓库 `harness requirement` 命令生成）：

```markdown
---
id: req-XX
title: "..."
created_at: 2026-...
operation_type: requirement
stage: {{STAGE}}
---

## Goal
- Core problem this requirement solves
- Capability delivered to users / system

## Scope
- Included: describe covered functionality
- Excluded: explicitly out of scope

## Acceptance Criteria
- AC-01: {{Fill in a verifiable criterion}}
- AC-02:

## Split Rules
- Break into independently deliverable changes; each change covers one unit
- After completion fill completion.md and record startup test passing
```

**对齐分析（章节级 mapping）**：

| harness requirement.md 章节 | office-hours 设计文档对应章节 | 对齐度 |
|---|---|---|
| frontmatter `id` / `title` / `created_at` / `operation_type` / `stage` | office-hours 头部 `# Design: {title}` / `Generated by ... on {date}` / `Branch:` / `Repo:` / `Status:` / `Mode:` / `Supersedes:` | **格式不同**：harness 用 yaml frontmatter；office-hours 用 markdown header 列表；需 adapter 重组 |
| `## Goal`（核心问题 + 交付能力 2 条） | startup: `## Problem Statement` + `## Demand Evidence` + `## Target User & Narrowest Wedge`；builder: `## Problem Statement` + `## What Makes This Cool` | **语义贴合但章节切分不同**：office-hours 输出更细化；adapter 需"汇总成 Goal 2 条" |
| `## Scope`（Included / Excluded） | startup: `## Constraints` + `## Recommended Approach`；builder: `## Constraints` + `## Recommended Approach` | **语义部分重合但缺少 Excluded 显式段**；adapter 需从 Approaches Considered 中提炼 Excluded |
| `## Acceptance Criteria`（AC-01 / AC-02 verifiable） | `## Success Criteria`（measurable criteria from Phase 2A） | **强对齐**：office-hours `Success Criteria` 直接映射 AC；adapter 仅需将自由列表转 AC-01/AC-02 编号 |
| `## Split Rules`（拆 chg 独立交付） | startup: `## The Assignment`（一条具体下一步）；builder: `## Next Steps`（具体 build 任务） | **方向对但粒度不同**：office-hours 给"一条具体行动 / 1-2-3 任务序列"；harness 要"独立可交付 chg 拆分规则" → adapter 需把 Next Steps 转为 chg 拆分原则 |
| 无对应 | `## Premises` / `## Cross-Model Perspective` / `## Open Questions` / `## Distribution Plan` / `## Dependencies` / `## What I noticed about how you think` | **office-hours 多余段**：不在 harness requirement.md 模板内；adapter 的处理策略：(a) 整体追加到 requirement.md 末尾作为 "## Office Hours Notes"附加段（保留思考价值）；或 (b) 仅保留 Open Questions / Dependencies 转入 Scope/Split Rules，丢弃 Premises / Cross-Model Perspective / What I noticed |

**结论**：

1. office-hours 输出 ≠ 直接落 requirement.md，**必须经 adapter 后处理**：(i) 路径迁移（`~/.gstack/projects/{slug}/...` → `.workflow/flow/requirements/{req-id}/requirement.md`，可能保留原位副本作 design lineage 链）；(ii) 章节重组（office-hours 12+ 段 → harness 4 段 Goal/Scope/Acceptance Criteria/Split Rules）；(iii) frontmatter 重写（`# Design: ...` 头部 → yaml frontmatter id/title/created_at/operation_type/stage）；(iv) 编号化（自由列表 → AC-01/AC-02）
2. adapter 复杂度 = **中等**：章节大部分有语义对应，但需要章节合并/拆分；frontmatter 互转无难度；office-hours 的多余段（Premises / Cross-Model / What I noticed）需决策保留还是丢弃
3. **office-hours 自带 Spec Review Loop**（5 维度 + 3 轮迭代 + quality score）= harness 当前 analysis stage 缺失的质量门——**意外收益**，可作为本 req 的隐性增值（adapter 不需要砍 Reviewer Concerns，直接保留追加到 requirement.md 末尾或 sug 池）
4. **触发悖论**：office-hours 是 user-facing slash skill（`/office-hours`），需用户在主对话触发；subagent **不能**派发 slash command；这意味着"analyst → /office-hours 强映射" 的实操路径只有两种：
   - **路径 α**：analyst.md SOP 改为"提示主 agent / 用户跑 `/office-hours`，然后把输出 path 反馈给 analyst 做 adapter"——本质上 analyst 是消费者，主 agent 是 /office-hours 的真正调用者
   - **路径 β**：analyst 自己内联实现 office-hours 等价的 6 forcing questions（不调 gstack skill，仅复用其方法论）——但这就违反"强映射 = 角色就是调 gstack 命令"语义
   - **default-pick：路径 α**（保留 gstack 强映射语义；analyst 文档化"提示主 agent 触发 /office-hours"，并提供 adapter 步骤把 `~/.gstack/projects/...-design-...md` 重组到 `.workflow/flow/requirements/{req-id}/requirement.md`）
5. office-hours 落盘 `~/.gstack/projects/` 是 user-level cache，与 harness 仓库无关——**保留原位，不需要移动 / 双写**，但 adapter 后产生的 requirement.md 落 `.workflow/flow/` 后，**原位 design doc 自动成为"上游证据 / lineage 留底"**，无需 harness 主动管理（gstack 自己有 design-doc-history 索引机制）

## 6. 待与用户深谈的开放问题（一次性批量化提出）

> 第 4 轮用户两条指令（A 范围收窄到"仅 analyst → /office-hours" + B 内置 gstack）使本节大幅重排：
> - Q1 已结案（方向 a 强化版）
> - Q2~Q5 在收窄到"1 角色 / 1 命令"后退化为 trivial-default（无需用户拍板，下文标记 [trivial-default]）
> - Q6 被 Q8 吸收 / 简化（下文 Q6 标记 [收窄简化]）
> - ~~Q7 第 3 轮重审版基本仍生效~~ → **第 6 轮已作废**：用户范式级修正"gstack 路径就不需要了，它生成的就是需求文档"——Q7 整套（Q7.1 双写 / Q7.2 落点 / Q7.3 三件套 / Q7.4 失败回退 + repository-layout 扩段 + 中央索引 + manifest）**整体作废**；产物直接落 `.workflow/flow/requirements/{req-id}/requirement.md`；前 5 轮决策保留在 §8.B 修正记录中作版本演进留底
> - **Q8 是第 4 轮新增、唯一仍需用户拍板的核心议题**
> - **Q-D（第 6 轮新增）**：dogfood 活证策略（候选 P / Q / R 三选一），核心拍板项

### 已结案

- ~~Q1（融合方向）~~ → **方向 a 强化版（角色↔gstack 命令强映射）**

### 第 4 轮收窄后 trivial-default（无需用户拍板，仅留底）

- **Q2 [trivial-default]** 角色映射设计：Q2.1=**仅 analyst 1 个角色**（用户明示"先融入"）；Q2.2=**1 主命令 office-hours，无备选**（最小可用集）；Q2.3=**强引导**（analyst.md SOP 内嵌"调用 /office-hours"步骤；非硬绑定，仍允许用户 escape）；Q2.4=**fallback 原生 SOP + warn**（gstack 装载失败 / Claude Code 之外 agent → 直接走原生 analyst Step A1~A3，记 warn 不阻塞）
- **Q3 [trivial-default]** 验收边界：**极简化版选项 2**——交付（i）chg-02 改 analyst.md 1 个文件；（ii）chg-05 dogfood 活证（用 req-55 自身的 analysis 跑过 1 次 /office-hours）；不上 lint（推到下一个 req）；不一次镜像 5 个角色（仅 analyst 一个）
- **Q4 [trivial-default]** 作用范围：必触及——`.workflow/context/roles/analyst.md`（注入"调用 /office-hours"段 + fallback）；`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`（scaffold mirror 同步）；新增 `src/harness_workflow/assets/gstack-skills/office-hours/`（vendor 副本）；新增 `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/role-command-map.yaml`（极简映射表，仅 1 行 analyst→office-hours）；不动 role-model-map.yaml；不一次性改其他 4 个角色 role.md
- **Q5 [trivial-default]** 产出形态：**形态 B 简化版**——`.workflow/context/integrations/gstack/role-command-map.yaml`（1 行映射）+ `.workflow/context/integrations/gstack/README.md`（极简调用矩阵 + 渐进式扩展说明，约 30~50 行人读）；不出 catalog 卡片（C 形态推到后续 req）
- **Q6 [收窄简化]** 安装前置契约：被 Q8 吸收——
  - Q6.1 检测时机 → 装载时机：**harness install 同步推送**（不再"检测"）
  - Q6.2 失败处理：**装载失败 = warn + runtime.yaml.gstack_run_log 记录**（与 Q7.4 共用）
  - Q6.3 agent 范围：**仅 Claude Code 启用 vendor 装载**（Q8 已合）
  - Q6.4 状态落点：**runtime.yaml `gstack_status: {installed_skills, vendor_version, last_install}`**（语义从检测结果改为装载结果）

### 重审版（仍待用户拍板的核心议题）

- Q2-重审：**角色↔gstack 命令映射表的设计**（方向 a 强化版下的核心产物）
  - 子问题 Q2.1：哪些 harness 角色需要映射？（11 个角色全部 / 仅核心 5 个 analyst+executing+testing+acceptance+regression / 仅 2~3 个试点？）
  - 子问题 Q2.2：每个角色映射几条 gstack 命令？（1 主命令；1 主 + 多备选；多命令组合菜单？）
  - 子问题 Q2.3：映射是"硬绑定（角色启动即调）"还是"软引导（角色提示 + 用户拍板调）"？用户原话"角色在执行的时候就是使用 gstack 的某个命令"——倾向"硬绑定 / 强引导"
  - 子问题 Q2.4：映射缺失 / gstack 命令报错时的回退策略？（fallback 到 harness 原生 SOP / 阻塞要求人工 / 静默降级？）

- Q3-重审：**验收边界（方向 a 强化版下）**
  - 选项 1（最小硬）：交付《角色↔gstack 命令映射表》文档 + 至少 1 个角色（建议 analyst 或 executing）的 role.md 改造为"调用 gstack 命令"形态
  - 选项 2（中等硬）：选项 1 + 在 harness-gstack 分支上完成 1 次 dogfood 跑（用某个 chg 走 analyst→executing→testing 的 gstack 强映射 SOP）
  - 选项 3（强硬）：选项 2 + 加契约 lint（启动时检测 gstack 已装 + 角色映射表 schema lint + 产出归集路径校验）
  - 选项 4（旗舰）：选项 3 + scaffold_v2 模板镜像（让 harness install 一键把 gstack 强映射推给新项目）

- Q4-重审：**作用范围（方向 a 强化版下）**
  - 几乎注定要触及（用户已明示"角色直接映射"）：
    - `.workflow/context/roles/{analyst,executing,testing,acceptance,regression}.md`（注入 gstack 命令调用契约段）
    - 新增 `.workflow/context/integrations/gstack/role-command-map.yaml`（映射表 / single source of truth）
    - `src/harness_workflow/skills/harness/SKILL.md`（加入"前置：检测 gstack 已安装"段 + Q6 安装契约）
  - 选择性触及（默认推荐触及，节省后续工作）：
    - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`（让新项目继承）
    - `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/`（镜像映射表）
  - 暂不触及（除非 Q3 选选项 4）：
    - `role-model-map.yaml`（gstack 命令本身不在 model map 范围）
    - lint 校验（除非 Q3 ≥ 选项 3）

- Q5-重审：**承载产出形态（方向 a 强化版下，明确"映射表 + 归集协议"两类硬产物落点）**
  - 形态 A：单文件 `.workflow/context/integrations/gstack/role-command-map.yaml`（最简，全 yaml；新项目镜像）
  - 形态 B：A + `.workflow/context/integrations/gstack/README.md`（人读说明 + 调用矩阵）
  - 形态 C：B + `artifacts/project/tools/catalog/gstack-{name}.md`（每个被映射的 gstack 命令一份目录卡，供 tools-manager 复用）
  - 形态 D：C + 在 `src/harness_workflow/skills/harness/SKILL.md` 顶层加"gstack 集成"小节（外部 agent 入门即看到）
  - **default-pick 重审**：B（最小硬产物 + 人读路标），可经 chg 增量升级到 C / D

- Q6-新增：**gstack 安装前置契约**（来自用户提点 1）
  - 子问题 Q6.1：**检测时机**——
    - a. `harness install` 时一次性检测（轻，但跨项目运行漏检）
    - b. 每次进入 stage（`harness next` / 角色加载链 Step 0）时检测（重，强保障）
    - c. 仅在角色实际要调 gstack 命令时检测（懒，但异常发生在执行中）
    - default-pick：**a + c 组合**（install 时主检测 + 角色调用前补检；不在 next 时反复检测，性能/噪音双优化）
  - 子问题 Q6.2：**检测失败处理**——
    - a. 强阻塞（gstack 未装 → harness 拒启）
    - b. 优雅降级（gstack 未装 → 角色 fallback 到 harness 原生 SOP，记 warning）
    - c. 引导自动安装（提示用户跑 `pip install gstack` 或对应安装命令，不强制）
    - default-pick：**c → b 兜底**（先引导，安装失败才降级；不强阻塞，避免 harness 单独使用场景被打断）
  - 子问题 Q6.3：**支持的 agent 范围**——
    - 已知现状：gstack 主要面向 Claude Code（slash skill 形态依赖 ~/.claude/skills/）；Codex / Kimi / Qoder 通过适配层接入 harness，但是否能装 gstack 有疑问
    - a. 仅 Claude Code 必装；其他 agent 走 harness 原生 SOP（务实，最快落地）
    - b. 全 agent 必装（理想，但 gstack 本身可能不支持非 Claude agent → 需先调研 gstack 跨 agent 兼容性）
    - c. 按 agent 分级映射表（Claude Code 全映射；Codex 部分映射；Kimi/Qoder 仅 fallback 原生）
    - default-pick：**a（仅 Claude Code 必装）+ runtime.yaml `agent_kind` 字段已有**，根据 agent 类型决定是否启用 gstack 映射；后续 sug 池补 c 的细化
  - 子问题 Q6.4：**检测产物落点**——
    - a. `runtime.yaml` 加 `gstack_status: {installed, version, last_checked, agent_kind_compatible}` 字段
    - b. `artifacts/project/project-overview.md` 加节
    - c. 新增 `.workflow/state/gstack-status.yaml`
    - default-pick：**a（runtime.yaml 加字段）**——单一 state 源原则；project-overview 是项目档案非运行态

- ~~Q7-重审（第 3 轮用户精确修正后）：**gstack 产出归集契约**~~ **【第 6 轮整段作废】**
  - **作废理由**：第 6 轮用户原话「gstack的路径就不需要了啊，它生成的就是需求文档，后续的步骤就要根据这个阶段的需求文档来生成了」——gstack 产物**就是**该 stage 的标准产物（requirement.md），**没有独立归集路径**；Q7 整套（Q7.1 双写 / Q7.2 落点 Y''' / Q7.3 三件套 + 中央索引 / Q7.4 失败回退 + repository-layout §2 / §3.1 (i) 扩段 + manifest.json + .gitkeep + runs.jsonl）**整体作废**
  - **新结论**：office-hours 输出（落原位 `~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md`）经 adapter 后处理（章节重组 + frontmatter 重写 + AC 编号化 + 多余段处理）后，**直接落** `.workflow/flow/requirements/{req-id}/requirement.md`（现有标准位置，stage_policies analysis 所属产物）；原位 design doc 作为"上游证据 / lineage 留底"由 gstack 自身管理，harness 不主动归集
  - **adapter 工作量**：见 §5.5 表格——章节大部分有语义对应（Goal ← Problem Statement+Demand Evidence；Acceptance Criteria ← Success Criteria 强对齐；Split Rules ← Next Steps；Scope ← Constraints+Recommended Approach）；office-hours 多余段（Premises / Cross-Model Perspective / Open Questions / Distribution Plan / Dependencies / What I noticed）默认追加到 requirement.md 末尾作"## Office Hours Notes"附加段，保留思考价值（adapter 设计细节由 chg-02 落地时定）
  - **前 5 轮 Q7 决策日志**：保留在 §8.B 修正记录（第 2~5 轮）作版本演进留底，**不删除**以保历史可追溯性
  - **历史快照（仅留版本演进证据，不再生效）**：
    - 第 3 轮 Q7.2 default-pick = 候选 X（`artifacts/project/integrations/gstack/`，项目级集中）—— 第 5 轮被推翻
    - 第 5 轮 Q7.2 default-pick = 候选 Y'''（`artifacts/{branch}/requirements/{req-id}-{slug}/gstack/`，gstack 兄弟目录 + req 内中央索引）—— 第 6 轮被推翻
    - 第 6 轮 Q7 整体作废 → 退化为 trivial（产物直接落标准 requirement.md 位置）

- ~~Q7（旧版本，已作废，仅保留章节锚点供 §8.B 引用）~~：**gstack 产出归集契约（第 3 轮起的所有版本）**
  - 第 3 轮用户原话（已被第 6 轮新约束 superseded）："gstack产物多是文档，需要放到制品仓库所属的文件夹汇总"
  - 三大约束：(1) 必须在 `artifacts/` 子树；(2) 按归属层级（req / chg / project）；(3) 要"汇总"（集中归集 + 索引）
  - 与 repository-layout 契约对齐：`artifacts/{branch_or_project}/` 子树定义为"对人可读签字执行产物"——gstack 文档型产物（plan / design / qa-report）天然契合此语义
  - 与 §2.1 项目级机器型豁免对比：项目级豁免**仅限** `constraints/experience/tools/` 三类；gstack 产物**不**走豁免通道，走"对人产物 / 按需"白名单兜底（§2 末行"其他对人产物"）

  - 子问题 Q7.1-重审：**是否拦截 gstack 产出**（落实"放到制品仓库"约束）
    - a. ~~不拦截（gstack 产出留原位）~~ → **拒绝**：用户明示"放到制品仓库"，原位放着不可能"汇总"
    - b. **拦截 + 重定向**（harness 在调 gstack 后把产出**移**到 artifacts/ 归集点；gstack 原位无副本）
    - c. **双写**（gstack 原位保留 + artifacts/ 归集点复制一份；前者保障 gstack 自身约定，后者保障 harness 可检索）
    - **default-pick 重审**：**c（双写）**——理由：(1) gstack 部分 skill 依赖原位产物（如 context-save → context-restore 复用，~/.gstack/ 自身缓存），强制移动会破坏 gstack 内部链路；(2) 用户要"汇总到制品仓库"——双写恰好满足"原位 gstack 链路不破 + harness 仓库归集可见"；(3) 复制成本低（多为小 markdown），运维代价可接受
    - 备选：若 gstack 产物体积大 / 频次高（如 design-shotgun 出 N 张大图），可在 chg 计划中按 skill 粒度降级为 b（拦截重定向）；先 c default，按需 b

  - 子问题 Q7.2-第 5 轮重审（用户精确修正后）：**归集落点**（落实"和分支和需求有关 / 跟对人文档放在一起"约束）
    - **第 3 轮选定的候选 X 已被用户推翻**——X 落 `artifacts/project/integrations/gstack/`（项目级集中、无 branch 维度、跟项目走），与用户"和分支和需求有关 / 制品跟对人文档放在一起"语义直接矛盾。
    - 第 5 轮三个候选（全部含 branch + req-id，全部在 `artifacts/{branch}/requirements/{req-id}-{slug}/` 子树下）：
      - **候选 Y'**（候选 Y 的修订版，含 chg 二级目录）：
        ```
        artifacts/{branch}/requirements/{req-id}-{slug}/gstack-runs/{chg-id}-{slug}/{skill}-{ts}/
        例：artifacts/harness-gstack/requirements/req-55-.../gstack-runs/chg-05-dogfood/office-hours-2026-05-07T14-00/
        ```
        - 优点：跟分支走 + 跟需求走 + 内部按 chg 分层
        - 待解决：layout §3.1 (i) 扁平契约要求 req 目录无 changes/ 子目录；引入 gstack-runs/ 子目录需扩段说明
      - **候选 Y''**（最扁平，与对人文档同层平铺，靠文件名前缀区分）：
        ```
        artifacts/{branch}/requirements/{req-id}-{slug}/{chg-id}-{slug}-{skill}-{ts}/
        例：artifacts/harness-gstack/requirements/req-55-.../chg-05-dogfood-office-hours-2026-05-07T14-00/
        ```
        - 优点：完全与对人文档同层，不引入子目录
        - 缺点：req 目录被大量 gstack 跑次填充（可能 N×M 个目录），与 §2 白名单对人文档（`requirement.md` / `交付总结.md` / `决策汇总.md` 等）混杂；每次跑都要在 req 顶层冒一个新目录，可读性 / 索引边界严重崩坏
      - **候选 Y'''**（gstack 兄弟目录 + 内部按 chg + skill 分层 + req 内中央索引）：
        ```
        artifacts/{branch}/requirements/{req-id}-{slug}/
          ├── requirement.md                 # 对人产物（白名单）
          ├── 交付总结.md                     # 对人产物（白名单）
          ├── 决策汇总.md                     # 对人产物（白名单）
          └── gstack/                         # gstack 制品兄弟目录（layout §2 白名单需扩段）
              ├── index.md                    # 本 req 内 gstack 调用人读汇总表
              ├── runs.jsonl                  # 本 req 内 gstack 调用机器读追加日志
              └── {chg-id}-{slug}/
                  └── {skill}-{ts}/
                      ├── manifest.json
                      ├── README.md
                      └── {关键产出}.md / .yaml
        例：artifacts/harness-gstack/requirements/req-55-.../gstack/chg-05-dogfood/office-hours-2026-05-07T14-00/
        ```
        - 优点：(1) 与对人文档同处 req 目录、平级兄弟（"放在一起"语义最贴近）；(2) gstack/ 单层子目录把 gstack 制品圈在自己命名空间内，不污染对人文档命名空间；(3) 内部按 chg + skill 双层分层，多 chg 多 skill 时归属清晰；(4) req 内中央索引（gstack/index.md + runs.jsonl）天然落 gstack/ 子树根，不需要全局索引文件；(5) 跨 req 全局视图由聚合命令扫描所有 `artifacts/*/requirements/*/gstack/runs.jsonl` 实现，不需要落实物中央索引
        - 待解决：layout §3.1 (i) 扁平契约扩段——允许 `gstack/` 单层子目录作为对人产物的附属归集区
    - **比选维度复核**：

      | 维度 | Y' | Y'' | Y''' |
      |---|---|---|---|
      | "放在一起"语义 | 子目录嵌入，二跳 | 同层最贴近 | 同处 req 目录、兄弟级别（贴近度仅次于 Y''） |
      | layout §3.1 (i) 扁平契约影响 | 引入 gstack-runs/ + chg/skill/ts 三层，破坏最重 | 不破坏目录结构，但 req 目录被大量平铺跑次填充 | 引入 gstack/ 单层子目录，扩段成本最轻 |
      | 多 chg 多 skill 可读性 | 高（按 chg + skill 双层分） | 极差（文件名碰撞 + 顶层视图混乱） | 高（gstack/ 内部按 chg + skill 双层分） |
      | 中央索引（"汇总"语义）落点 | gstack-runs/ 内 index.md，与 req 顶层无缝对接较难 | 与对人文档混在一起，索引边界不清 | gstack/index.md + gstack/runs.jsonl 天然落 gstack/ 子树根，边界清晰 |
      | 与 §2 白名单的关系 | 需扩白名单允许 gstack-runs/ 整子目录 | 需扩白名单允许大量 `{chg}-{skill}-{ts}/` 跑次目录平铺 | 需扩白名单允许 gstack/ 单层子目录（最小扩面） |
      | 跨 req 全局视图 | 需聚合脚本扫所有 req 目录 gstack-runs/ | 需聚合脚本扫所有 req 目录顶层 | 需聚合脚本扫所有 req 目录的 gstack/ 子树（最规整） |

    - **default-pick 重审 = 候选 Y'''**（gstack 兄弟目录 + 内部按 chg + skill 分层 + req 内中央索引）——理由：
      1. 用户"放在一起"语义满足（同处 req 目录、兄弟级别）+ "和分支和需求有关"满足（路径含 branch + req-id + chg-id）
      2. layout §3.1 (i) 扁平契约扩段成本最轻（只新增 gstack/ 单层子目录作为附属归集区）
      3. gstack 制品自有命名空间（gstack/ 子树根），不污染对人文档（requirement.md / 交付总结.md / 决策汇总.md）命名空间
      4. req 内中央索引（gstack/index.md + runs.jsonl）落 gstack/ 子树根天然成立，"汇总"语义在 req 内一处达成
      5. 跨 req 全局视图由 `harness gstack-index` 命令（后续 sug）聚合扫描实现，不需要落实物中央索引文件——避免双层一致性维护
      6. 与 req-52 "项目级跟项目走"原则不冲突——本路径管 branch + req 级对人产物，与 `artifacts/project/` 项目级机器型不同语义层

    - **与第 3 轮拒绝 Y 的理由如何被 Y''' 解决**：
      - 第 3 轮拒理 1："Y 在 §3.1 (i) 扁平契约下需 changes/ 子目录"——Y''' 不引入 changes/，而是 gstack/{chg-id}/{skill}/{ts}/，与 changes/ 无关；扩段开 gstack/ 一个口
      - 第 3 轮拒理 2："Y 跨 req 视图缺失需另作中央索引"——Y''' 在 req 内 gstack/ 子树根落 index.md + runs.jsonl，跨 req 由聚合命令兜底，不需要顶层中央索引文件
      - 第 3 轮拒理 3："Y 不汇总"——Y''' 通过 req 内 gstack/index.md + 跨 req 聚合命令双层兜底，"汇总"语义通过工具而非实物文件达成

    - **chg-03 关键产物表更新方向**（落到 §8.A 内）：
      - (1) repository-layout §2 白名单扩段：允许 `artifacts/{branch}/requirements/{req-id}-{slug}/gstack/` 作为"对人产物附属归集区"白名单第 N+1 类（精确措辞由 chg-03 起草）
      - (2) repository-layout §3.1 (i) 扁平契约扩段：明确 gstack/ 是 req 目录下唯一允许的对人产物子目录（与 §2 白名单扩段联动）
      - (3) 归集目录骨架：`artifacts/{branch}/requirements/{req-id}-{slug}/gstack/{chg-id}-{slug}/{skill}-{ts}/`（含 manifest.json + 关键产出复制 + README）
      - (4) req 内中央索引：`artifacts/{branch}/requirements/{req-id}-{slug}/gstack/index.md`（人读汇总表）+ `gstack/runs.jsonl`（机器读追加日志）
      - (5) 双写规则：analyst 调 /office-hours 后 copy 关键产出到归集点，gstack 原位（`~/.gstack/projects/{repo_slug}/...`）不动
      - (6) scaffold_v2 mirror 校验：`artifacts/{branch}/` 不在 `_SCAFFOLD_V2_MIRROR_WHITELIST` 内，自动豁免 mirror 覆盖（与项目级 `artifacts/project/` 豁免不同机制——前者按 branch 结构天然不入 mirror）
      - (7) 失败回退：warn + `runtime.yaml.gstack_run_log` 追加（不变）
      - (8) 归集点 `.gitkeep` 防 setuptools dot-file ignore（不变，参考 bugfix-13 round-4 教训）
      - (9) **跨 req 全局视图**：本 req 不落实物，记入后续 sug 池——`harness gstack-index --all-req` 命令聚合扫描所有 `artifacts/*/requirements/*/gstack/runs.jsonl` 输出全局表

  - 子问题 Q7.3-重审：**归集内容 + 索引契约**（落实"汇总"约束）
    - 每次 gstack 调用产出三件套（落 X 候选目录 `artifacts/project/integrations/gstack/runs/{req-id}/{chg-id}/{skill}-{ts}/`）：
      1. `manifest.json`：调用元数据（skill 名 / 调用角色 / 调用时间戳 / 退出码 / harness req-id / chg-id / stage / 原位路径指针 / 产物清单 + 摘要哈希）
      2. **关键产出复制**（plan-*.md / design-*.md / qa-report-*.md / context-save-*.md 等核心 markdown / yaml）
      3. `README.md`（≤ 50 行人读说明，含"为什么调这次 gstack / 关键结论摘要 / 原位路径")
    - **顶层中央索引**：`artifacts/project/integrations/gstack/index.md`（人读汇总表）+ `artifacts/project/integrations/gstack/runs.jsonl`（机器读追加日志）
      - index.md 表头：`req | chg | stage | role | skill | timestamp | 退出码 | manifest 路径 | 一句话摘要`
      - runs.jsonl 每行 = 一次调用 manifest 摘要的 jsonl 追加（便于工具脚本聚合）
    - **default-pick 重审**：上述三件套 + 顶层中央索引（取代原 default-pick "b 关键产出复制"）——理由：用户"汇总"约束直接驱动需要中央索引文件，不能仅靠目录结构
    - 备选轻量化：仅 manifest.json + 关键产出复制（不出 README + 不出顶层 index.md），靠目录结构隐式汇总——若用户觉得太重，可在拍板时降级

  - 子问题 Q7.4-重审：**归集失败回退**（保持原 default-pick c，理由更新）
    - a. 静默 warn，不阻塞 stage 推进
    - b. 记录到 `.workflow/state/runtime.yaml.gstack_run_log` 待人工复核
    - c. a + b
    - **default-pick 重审**：**保留 c（静默 warn + state log 记录）**——理由更新：(1) 与 Q7.1 c 双写策略一致：归集失败时 gstack 原位产物仍在，harness 端只是少一份镜像，不破坏可恢复性；(2) state log 记录后可由人工或后续工具脚本补归集；(3) 不打断 stage 推进，符合"flexible 集成"基调
    - 与原 default-pick 差异：原版基于 Q7.1=a（不拦截）下"归集 = 复制"；本版基于 Q7.1=c（双写）下"归集失败 = 复制失败、原位仍在"——回退语义更柔和，c 仍是最优选

- **Q8-新增（核心拍板项）**：**gstack 内置发布 + harness install 自动装载契约**（来自第 4 轮用户指令 B）
  - 子问题 Q8.1：**vendor 形态**
    - a. **复制快照**（路径 `src/harness_workflow/assets/gstack-skills/{skill-name}/`，含 SKILL.md + LICENSE-gstack + VERSION-gstack 三件套；vendor 时间 + 来源 commit + 来源版本写入 VERSION-gstack）
    - b. git submodule（依赖外部仓库 + clone 复杂度上升 + 强行锚 commit）
    - c. git subtree（merge 上游变更复杂）
    - **default-pick：a（复制快照）**——理由：harness 已有 `assets/skill/` 复制管线，gstack-skills 当作 vendored 资产管理对称；不引入 submodule clone 复杂度；MIT 允许 vendor；升级 = 重跑 vendor 脚本拉新快照覆盖（独立 chg 处理）
  - 子问题 Q8.2：**vendor 范围**
    - a. **仅本 req 用到的 skill**（本 req = 仅 office-hours；后续 req 增量扩 → req-56 加 /investigate；req-57 加 /qa；…）
    - b. 一次 vendor 全 47 个（374M 核心源；harness 仓库膨胀 + 大部分本 req 不用 + 升级 / 同步成本高）
    - c. vendor 一个"核心子集"（如 office-hours / investigate / qa / review / codex 5 个，对应主 5 角色映射）—— 介于 a/b
    - **default-pick：a（仅 office-hours）**——理由：用户明示"一步步融入"；最小可用集 / 最小仓库膨胀 / 最小 license & upstream 同步面；后续 req 按需扩
  - 子问题 Q8.3：**装载时机**
    - a. **harness install / install --agent 同步装载**（与 install_agent 主流程并列，agent_kind=claude 时执行）
    - b. 独立子命令 `harness install --gstack`（拆分入口）
    - c. harness update --force-managed 时同步
    - **default-pick：a（install / install --agent 同步）**——理由：用户原话"harness install 的时候自动给对应的 agent 装载"，明示绑 install；与 reg-02 chg-07 "install 是同步契约唯一真入口"契约一致；不另开命令面
  - 子问题 Q8.4：**装载目标**
    - a. **全局 `~/.claude/skills/{skill-name}/`**（与 gstack 自身布局一致；推送 SKILL.md 单文件）
    - b. 项目内 `.claude/skills/{skill-name}/`（每个项目重复一份；与 harness skill 现有 `.{agent}/skills/harness/` 项目级布局对称）
    - c. 双轨 a + b（兜底但冗余）
    - **default-pick：a（全局）**——理由：(1) gstack 自身就是全局 skill（`/skill-name` 注册全局生效），项目级副本不会更"近"；(2) 多项目场景下全局装载只装一次；(3) 与 harness skill 项目级是不同语义（harness 必须随项目走的状态机；gstack 是命名 skill，全局即可）；(4) 装载冲突时（用户已自装 gstack 全套）→ 检测 `~/.claude/skills/{name}/SKILL.md` 文件存在且 hash 不同 → warn + 由 `--force-gstack` flag 决定覆盖与否
  - 子问题 Q8.5：**vendor 版本升级**
    - a. **新增独立 chg / sug**（手工 vendor 脚本 `scripts/vendor-gstack.sh skill-name [commit]` 拉取 + 更新 LICENSE-gstack / VERSION-gstack）
    - b. 自动 CI 同步（开销大，本 req 不上）
    - c. 不主动升级，仅 vendor 一次锁死
    - **default-pick：a（手工 vendor 脚本）**——理由：本 req 范围内不上 CI；手工脚本足以覆盖单 skill 升级；后续 req 增量 vendor 时复用同一脚本
  - 子问题 Q8.6：**License & 归因合规**
    - 必做：(1) vendor 副本根目录 `LICENSE-gstack` 全文复制 gstack MIT；(2) `VERSION-gstack` 头部加 vendor 来源声明（upstream URL / commit / version / vendor 时间）；(3) harness 仓库根 LICENSE / README 加一节"Third-party vendored skills"列出 gstack-skills 引用 + MIT 归因；(4) 推送到 `~/.claude/skills/{name}/` 时同步推 LICENSE-gstack 副本
    - **default-pick：上述 4 条全做**（无可选项；MIT 强制要求保留 copyright + permission notice）
  - 子问题 Q8.7：**与 Q6 的关系**（合并）
    - Q6（安装前置契约）在 Q8 落地后基本被吸收：检测时机 → 装载时机；检测失败 → 装载失败 warn；agent 范围 → 仅 Claude Code 启用；状态落点仍 runtime.yaml `gstack_status` 字段（语义从检测结果改为装载结果）
    - **default-pick：Q6 子项全部并入 Q8 / chg-01**，不再单独成 chg

- **Q-D（第 6 轮新增）**：**dogfood 自适用悖论的解法**
  - **悖论描述**：本 req-55 的 analysis stage 已经走了 5 轮 analyst 深谈，requirement.md 仍是 template（未填实）；如果让本 req 的 analyst 改用 /office-hours 跑一遍 → 但 /office-hours 是 user-facing slash skill（需用户在主对话中 `/office-hours` 触发），**不能由 subagent 派发触发**（参 §5.5 触发悖论 + 路径 α default-pick）
  - **候选方案**：
    - **候选 P（最稳）**：本 req-55 chg-05 dogfood 改为「用一个**新的 sample req**（如 `req-temp-demo` / `req-56` 或专用 dogfood req）演示 office-hours → requirement.md 流程」，本 req 自身的 requirement.md 仍由 analyst 手工填实（前 5 轮深谈结论 + 第 6 轮 adapter 调研直接落地）；优点：风险最低，不阻塞本 req 收尾；缺点：dogfood 不是"自适用"——丧失"用 req-55 自身验证 req-55 产出"的纯度
    - **候选 Q（最简）**：本 req-55 不做 dogfood 活证（chg-05 砍掉），dogfood 推到 req-56（开第 2 个角色映射 executing→/investigate 时一并验证 office-hours 路径）；优点：本 req 完全聚焦"打通最小可用契约"，不引活证压力；缺点：本 req 验收边界缺一个端到端证据 → Q3 验收边界倒退到选项 1（最小硬，仅文档 + 1 个 role.md 改造）
    - **候选 R（最纯活证 / 自适用）**：让用户在拍板后**手动**在 Claude Code 主对话跑 `/office-hours`（主题 = req-55 本身的需求），把输出 path 反馈给 analyst → analyst 跑 adapter 把 `~/.gstack/projects/...-design-...md` 重组到 `.workflow/flow/requirements/req-55-.../requirement.md`；优点：(i) 真自适用活证（用 req-55 自身验证 req-55 流程）；(ii) 同时把 requirement.md 从 template 状态填实——一举两得；(iii) 暴露 adapter 真实工作量供 chg-02 落地参考；缺点：需用户配合（不是 analyst 单方面可完成）；时序约束：需用户在 Q-A/Q-B/Q-D 拍板后**追加一次 /office-hours 对话**，本 req analysis stage 才能完整收尾
  - **default-pick：候选 R**——理由：(1) 用户范式级修正（"gstack 产物 = 标准产物"）的最直接证据 = 本 req 自身用这套流程产出 requirement.md；(2) 候选 P 风险确实最低但牺牲 dogfood 自适用纯度，与用户"先融入" + "本 req 是融合的开荒 req"的语义不匹配；(3) 候选 Q 砍掉 dogfood 在范围最窄但验收边界倒退；(4) 候选 R 唯一缺点"需用户配合一次主对话调用"在用户已表达"我们要先沟通融合思路"的开放对话节奏下并不构成阻力——本 req 本来就是用户与 analyst 多轮深谈推进的
  - **备选**：若用户拒绝候选 R（不愿额外配合一次 /office-hours 对话），降级到候选 P（用新 sample req 演示）；候选 Q 仅作为最终保底（本 req 不上 dogfood）

## 7. 待处理捕获问题

- artifacts/project/constraints/index.md 把 `coding/测试-rule.md` 列为 always 加载，但该文件不存在 → 加载链 fallback 静默，但 index 应清理；非本 req 范围，待 sug 池补
- artifacts/project/{experience,tools}/ 6 个 index.md 全为模板占位，下游用户尚未填实

## 8. default-pick 决策清单（第 6 轮范式级修正后）

| 议题 | 状态 | 拍板内容 / default-pick 推荐 |
|---|---|---|
| **Q-A 范围收窄** | **第 7 轮已结案** | **接受 default-pick**：本 req 仅 analyst → /office-hours 一条强映射；后续 req-56~59 渐进扩展（executing→/investigate / testing→/qa / acceptance→/review / regression→/codex） |
| **Q-B Q8 内置发布契约（含 Q8.2 第 7 轮修正）** | **第 7 轮已结案** | **接受 default-pick + Q8.2 修正**：Q8.2 vendor 范围从"仅 office-hours"扩到"全部 47 个 gstack skill"；其余 6 子项（Q8.1 复制快照 / Q8.3 install 同步装载 / Q8.4 全局 ~/.claude/skills/ / Q8.5 手工 vendor 脚本 / Q8.6 MIT 4 项归因 / Q8.7 Q6 并入）保持 default-pick |
| **Q-D dogfood 活证策略** | **第 7 轮已结案** | **接受 default-pick = 候选 R**：用户主对话跑 /office-hours → analyst adapter 重组 design doc 覆盖本 req requirement.md；备选 P / 保底 Q |
| Q1 融合方向 | **已结案** | 方向 a 强化版（角色↔gstack 命令强映射）—— 用户原话："角色在执行的时候就是使用 gstack 的某个命令" |
| Q2 角色映射设计 | **trivial-default**（收窄后无需拍板） | Q2.1=**仅 analyst 1 角色** / Q2.2=**1 主命令 office-hours，无备选** / Q2.3=**强引导**（SOP 内嵌调用步骤，仍允许 escape）/ Q2.4=**fallback 原生 + warn** |
| Q3 验收边界 | **trivial-default**（收窄后无需拍板，但因 Q-D 选择动态调整） | Q-D=R → 验收 = chg-02 改 analyst.md（含 adapter）+ chg-05 dogfood 活证（自适用）；Q-D=P → chg-05 改用新 sample req；Q-D=Q → chg-05 砍掉，验收倒退到选项 1 |
| Q4 作用范围 | **trivial-default**（收窄后无需拍板） | analyst.md（项目 + scaffold_v2 mirror）+ assets/gstack-skills/office-hours/（vendor 副本）+ integrations/gstack/role-command-map.yaml（极简 1 行映射）；不动 role-model-map / 不上 lint |
| Q5 产出形态 | **trivial-default**（收窄后无需拍板） | **形态 B 简化版**：1 行 yaml 映射 + README 调用矩阵（≤ 50 行）；不出 catalog 卡片 |
| Q6 安装前置契约 | **被 Q8 吸收，trivial-default** | Q6 全部并入 Q8 / chg-01；状态落点仍 runtime.yaml `gstack_status` 字段（语义改为装载结果） |
| ~~Q7 产出归集契约~~ | **第 6 轮整体作废，trivial** | 用户范式级修正"gstack 产物 = 标准产物 requirement.md"——无独立归集路径，无中央索引，无 layout 扩段；产物经 adapter 后处理后**直接落** `.workflow/flow/requirements/{req-id}/requirement.md`；前 5 轮 Q7 全套决策（候选 X / Y' / Y'' / Y'''）保留在 §8.B 修正记录作版本演进留底 |
| **Q8 gstack 内置发布**（核心拍板项之一） | **第 7 轮已结案（含 Q8.2 修正）** | Q8.1=**a 复制快照** / **Q8.2=b 全部 47 skill**（第 7 轮用户修正：装载层全装；融合层仍仅 office-hours）/ Q8.3=**a harness install 同步装载** / Q8.4=**a 全局 `~/.claude/skills/{name}/`** / Q8.5=**a 手工 vendor 脚本** / Q8.6=**MIT 4 项归因全做** / Q8.7=Q6 全部并入 Q8 / chg-01 |
| **Q-D dogfood 活证策略**（第 6 轮新增核心拍板项） | **第 7 轮已结案** | **接受 default-pick = 候选 R**（最纯活证 / 自适用）：用户拍板后手动跑 `/office-hours` → analyst 跑 adapter 把 design doc 重组到本 req requirement.md；备选降级 P；保底 Q |

## 8.A chg 拆分骨架（第 6 轮范式修正后 — 4 个 chg，chg-03 砍掉）

> 第 6 轮范式级修正后 chg 骨架重排：原 chg-03（gstack 产出归集协议）**整体砍掉**——用户明示"gstack 路径不需要"，归集协议无目标对象。chg-02 扩展为"analyst → /office-hours 强映射 + adapter 后处理"。chg 编号**保留断号**（chg-04 / chg-05 不重命名），给后续 req 留兼容；chg-03 槽位作"已作废占位"，change.md 写明作废理由 + 引用 §8.B 第 6 轮修正。
> 待用户拍板 Q-A / Q-B / Q-D 后正式落 change.md + plan.md。

| chg 编号 | 候选标题（≤15 字描述） | 关键产物 | 依赖 |
|---|---|---|---|
| chg-01 | gstack 内置发布契约（vendor 全 47 skill + 自动装载，**第 7 轮 Q8.2 扩范围**） | (1) `src/harness_workflow/assets/gstack-skills/{skill-name}/...` **每 skill 一目录（47 个）**含 SKILL.md + 子资源 references/ scripts/（若上游存在）+ `_shared/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack}` 顶层共享；(2) `scripts/vendor-gstack.sh [skill-name|--all] [commit]`（先单 skill 形态，再 `--all`；自动写 VERSION-gstack）；(3) `install_local_skills` / `install_agent` 加 gstack-skills 推送子流程：agent_kind=claude → `_copy_tree(GSTACK_SKILLS_ROOT, ~/.claude/skills/)` **全 47 个 skill 推送 + `_shared/` → `~/.claude/skills/gstack/{bin,agents,scripts}/`**（与 SKILL.md 内嵌硬编码路径一致）；其它 agent 跳过 + warn；(4) `runtime.yaml` 加 `gstack_status: {installed_skills, vendor_version, last_install, agent_kind_compatible}` 字段（schema + 写入逻辑）；(5) 装载失败回退：warn + `runtime.yaml.gstack_run_log` 追加；(6) 仓库根 README "Third-party vendored skills" 节列出**全 47 个**vendored skills + MIT 归因；(7) `--force-gstack` flag 处理装载冲突（已存在不同 hash 的 SKILL.md → 不覆盖默认 warn；带 flag 才覆盖） | 无（最前置；Q6 整体并入） |
| chg-02 | analyst → /office-hours 强映射 + adapter 后处理（**第 6 轮扩展**） | (a) **强映射文档**：改 1 个文件 `.workflow/context/roles/analyst.md`：在 Step A2 前插入"调用 /office-hours + 后处理"步骤——分两段：(i) 触发提示（提示主 agent 在主对话跑 `/office-hours`，传入本 req 主题；subagent 不能直接调 slash skill，由主 agent 兜底，参 §5.5 路径 α）；(ii) **adapter 后处理**（接到 office-hours 输出 path `~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md` 后，按 §5.5 章节 mapping 表把 startup/builder mode 设计文档**重组**到 `.workflow/flow/requirements/{req-id}/requirement.md`：frontmatter 重写 → yaml id/title/created_at/operation_type/stage；Goal ← Problem Statement+Demand Evidence 汇总 2 条；Scope.Included ← Constraints+Recommended Approach 提炼；Scope.Excluded ← Approaches Considered 中"未选"的方向；Acceptance Criteria ← Success Criteria 编号化为 AC-01/02/...；Split Rules ← Next Steps / The Assignment 转为 chg 拆分原则；多余段 Premises / Cross-Model Perspective / Open Questions / Distribution Plan / Dependencies / What I noticed / Reviewer Concerns 整体追加到 requirement.md 末尾作 `## Office Hours Notes` 附加段保留思考价值）；(iii) fallback：office-hours 未跑 / gstack 未装 / 主 agent 拒派发 → analyst 走原生 Step A1~A3 + warn；(b) **极简映射表**：新增 `.workflow/context/integrations/gstack/role-command-map.yaml`（极简 1 行映射 + 注释说明渐进扩展）；(c) **README**：新增 `.workflow/context/integrations/gstack/README.md`（≤ 50 行调用矩阵 + adapter 章节 mapping 表压缩版 + 渐进式扩展规划） | chg-01 |
| ~~chg-03~~ | ~~gstack 产出归集协议~~ | **【第 6 轮整体作废】** 用户范式级修正"gstack 路径不需要"——无归集对象；本 chg 砍掉，编号保留断号留兼容；adapter 后处理（原 chg-03 子项之一）已并入 chg-02 (a)(ii) | （N/A） |
| chg-04 | scaffold_v2 镜像（极简化） | (1) `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md`（与 chg-02 (a) 改造同步）；(2) `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/role-command-map.yaml` + `README.md`（与 chg-02 (b)(c) 镜像）；(3) `_SCAFFOLD_V2_MIRROR_WHITELIST` 校验：本 chg 不在 `artifacts/project/` 子树落地（与 chg-03 砍掉一致），无新增 mirror 豁免项；不镜像 vendor 副本（assets/gstack-skills/ 是 harness 仓库自有资产，不入 scaffold） | chg-02 |
| chg-05 | dogfood 活证（用 req-55 自身验证；按 Q-D 候选选择动态调整） | **Q-D=R（default）**：(i) 用户在主对话跑 `/office-hours`，主题 = req-55 本身的需求（"gstack 和 harness 工作流融合"）；(ii) office-hours 产出落 `~/.gstack/projects/{slug}/{user}-harness-gstack-design-{datetime}.md`（gstack 自身的 user-level cache，原位保留）；(iii) analyst 跑 chg-02 (a)(ii) adapter，把 design doc 重组**直接覆盖**本 req 的 `.workflow/flow/requirements/req-55-gstack-和-harness-工作流融合-开发承载分支-harness-gstack/requirement.md`（同时填实当前 template 状态的 requirement.md，一举两得）；(iv) retro 笔记入 `artifacts/project/experience/roles/analyst.md`（"调 /office-hours 的姿势 / adapter 章节 mapping 实操细节 / fallback 触发场景 / 多余段处理选择" 四点）。**Q-D=P 备选**：用新 sample req 演示，本 req 的 requirement.md 仍由 analyst 手工填实（前 5 轮深谈 + 第 6 轮 adapter 调研直接落地）。**Q-D=Q 保底**：chg-05 砍掉，验收倒退到选项 1 | chg-01 / chg-02 / chg-04 |

**已取消**：
- 原 chg-06（契约 lint）—— 推到下一个 req（待 chg-01~05 落地稳定后再加 lint）
- ~~chg-03~~（gstack 产出归集协议）—— **第 6 轮整体作废**，用户范式级修正"gstack 路径不需要"使本 chg 失去归集对象；adapter 后处理子项已并入 chg-02

**编号断号说明**：chg-03 槽位**保留作废占位**（不重命名 chg-04→chg-03 / chg-05→chg-04），理由：(i) 与已写入前 5 轮 session-memory 的 chg 编号引用兼容（避免 §8.B 修正记录中的 chg-03 引用悬挂）；(ii) 给后续可能恢复 gstack 制品归集协议留一个稳定锚点（若未来 gstack 又出 binary / 大文件类产物，可用同 chg-03 槽位重启）

**对前一会话的修正**：
- 原 chg-01（gstack 安装前置契约）→ 升级为"内置发布契约"（vendor + 自动装载，吸收 Q6）
- 原 chg-02（核心 5 角色 role.md 注入）→ 收窄到"仅 analyst 1 个文件 + 1 行映射 yaml"，**第 6 轮再次扩展**为"含 adapter 后处理"（吸收原 chg-03 的 adapter 子项）
- 原 chg-04（scaffold_v2 镜像 5 角色）→ 收窄到"仅 analyst.md + 1 行 yaml + README"
- 原 chg-05（dogfood 跑 5 角色）→ 收窄到"仅 analyst → /office-hours 一次活证"，**第 6 轮再次细化**为按 Q-D 候选选择（R / P / Q）动态调整
- 原 chg-06（lint）→ 整体砍掉推后续 req
- **第 5 轮 Q7.2 落点修正**：chg-03 落点从 `artifacts/project/integrations/gstack/runs/{req}/{chg}/{skill}-{ts}/` 改为 `artifacts/{branch}/requirements/{req-id}-{slug}/gstack/{chg-id}-{slug}/{skill}-{ts}/`；中央索引落 req 内 gstack/ 子树根；layout 扩段对象从 §2.1 项目级豁免改为 §2 白名单 + §3.1 (i) 扁平契约双扩段；chg-05 dogfood 落点同步更新
- **第 6 轮范式修正**：chg-03 整体作废（用户原话"gstack 路径不需要"）；chg-02 扩展含 adapter；chg-05 落点改为标准 requirement.md 位置（不再落 gstack/ 子树）；chg 总数 5 → 4（编号保留断号）

## 8.B 已对前一会话推演的修正

- **第 2 轮**：方向 a 强化版下保留主体，但将"融合契约底座"拆为 chg-01（安装契约）+ chg-02（映射表）+ chg-03（归集协议）三件硬产物
- **第 3 轮 Q7 修正**：chg-03 范围扩大——加 repository-layout §2 / §2.1 扩段 + 顶层 index.md / runs.jsonl 中央索引 + .gitkeep 防 setuptools dot-file ignore
- **第 4 轮 范围收窄 + Q8**：
  - chg-01 升级为"内置发布契约"（vendor 复制快照 + harness install 自动装载 + LICENSE 归因）—— 吸收 Q6
  - chg-02 收窄到"仅 analyst.md 1 个文件 + 1 行 yaml 映射 + ≤50 行 README"
  - chg-04 收窄到"仅 analyst.md + 1 行 yaml + README" 镜像（不镜像 vendor 副本）
  - chg-05 收窄到"仅 analyst → /office-hours 一次活证"
  - chg-06（lint）整体砍掉推后续 req
  - Q2~Q5 退化为 trivial-default（无需用户拍板）；Q6 被 Q8 吸收；**仅 Q7 + Q8 是核心拍板项**

- **第 5 轮（本轮）Q7.2 落点精确修正 + 误判纠正**：
  - **关键纠正**：第 3 轮 Q7.2 选定的候选 X = `artifacts/project/integrations/gstack/runs/{req-id}/{chg-id}/{skill}-{ts}/`（项目级集中、无 branch 维度）**被用户原话推翻**：
    - 用户原话：「qc制品跟对人文档放在一起，也就是和分支和需求有关」
    - 用户语义：制品须 **branch-aware + req-aware**，与对人文档同处 `artifacts/{branch}/requirements/{req-id}-{slug}/` 子树
    - 第 3 轮误判根因：把 gstack 制品当作"项目级集成元数据"归入 `artifacts/project/integrations/`（该路径的语义层是项目级机器型 + 跟项目走，与"对人产物 + 跟 branch + req 走"语义相反）；用户本轮明示后纠正为"对人产物附属归集区"
  - **第 5 轮 default-pick 重审 = 候选 Y'''**（gstack 兄弟目录）：
    ```
    artifacts/{branch}/requirements/{req-id}-{slug}/gstack/{chg-id}-{slug}/{skill}-{ts}/
    + req 内中央索引：artifacts/{branch}/requirements/{req-id}-{slug}/gstack/index.md + runs.jsonl
    ```
    比选过 Y'（含 gstack-runs/ 嵌套子目录）/ Y''（最扁平、文件名前缀区分）/ Y'''（gstack 兄弟目录），Y''' 在"放在一起"语义、扁平契约扩段成本、多 chg 多 skill 可读性、中央索引落点四个维度综合最优
  - **chg-03 关键产物表更新**：
    - layout 扩段对象从 §2.1 项目级豁免（错）→ §2 白名单 + §3.1 (i) 扁平契约双扩段
    - 归集目录骨架落点从 `artifacts/project/integrations/gstack/runs/{req}/{chg}/{skill}-{ts}/` → `artifacts/{branch}/requirements/{req-id}-{slug}/gstack/{chg-id}-{slug}/{skill}-{ts}/`
    - 中央索引落点从顶层 `artifacts/project/integrations/gstack/index.md` → req 内 `artifacts/{branch}/requirements/{req-id}-{slug}/gstack/index.md`
    - 跨 req 全局视图后置：本 req 不落实物全局索引，记入后续 sug 池（`harness gstack-index --all-req` 命令）
    - mirror 豁免理由变更：从"`artifacts/project/` 在 mirror 白名单"→"`artifacts/{branch}/` 整子树天然不在 mirror 白名单（scaffold_v2 mirror 仅含项目模板骨架）"
  - **chg-05 dogfood 落点同步更新**：从 `artifacts/project/integrations/gstack/runs/req-55/chg-05/office-hours-{ts}/` → `artifacts/harness-gstack/requirements/req-55-.../gstack/chg-05-dogfood/office-hours-{ts}/`
  - **与 req-52 "跟项目走"原则的协调说明**（防止再次误判）：
    - `artifacts/project/` 跟项目走 = 管 constraints/experience/tools 项目级机器型文档（不跟 branch / 不跟 req）
    - `artifacts/{branch}/requirements/{req-id}-{slug}/` 跟 branch + req 走 = 管 branch + req 级对人产物
    - gstack 制品（plan / design / qa-report / context-save）= 对人产物，归后者，**不**归前者
    - 两条路径不矛盾，分管不同语义层；本误判源于忽视 gstack 制品"对人产物"性质（用户第 3 轮已明示过）
  - **Q-A / Q-B 仍未明确表态**（用户至今未对范围收窄 + Q8 内置发布契约 7 子项明确同意 / 否认），本轮单一开口问把 Q-A / Q-B / 修正后 Q-C 一次性问清楚

- **第 6 轮（本轮）范式级概念修正 + 误判根因留底**：
  - **关键修正**：第 5 轮选定的候选 Y'''（gstack 兄弟目录 `artifacts/{branch}/requirements/{req-id}-{slug}/gstack/`）**被用户原话整体推翻**：
    - 用户原话：「gstack的路径就不需要了啊，它生成的就是需求文档，后续的步骤就要根据这个阶段的需求文档来生成了」
    - 用户语义：(i) gstack 不需要任何独立路径；(ii) gstack 产物 = harness 工作流的标准产物（requirement.md）本身；(iii) 下游 stage 依赖的就是 requirement.md
    - **范式级转变**：从"gstack 是辅助工具，产物归集到独立子树"→"gstack 命令直接产出工作流标准产物，没有独立路径"
  - **前 5 轮误判根因（贯穿第 2~5 轮的连续误判）**：
    - 第 2 轮：把"角色 = gstack 命令"理解为"角色调用 gstack + 自己再写 harness 标准产物"——双产物模型，从一开始就埋下"两路并行"的设计偏差
    - 第 3 轮：用户提出"gstack 产物多是文档，需放制品仓库汇总"——analyst 进一步把 gstack 产物当作"需要归集的辅助制品"（错把"汇总"理解为"集中归集到独立子树"，而非"产物本身就是工作流标准产物"）
    - 第 4 轮：范围收窄到"仅 analyst → /office-hours"后，仍保留 chg-03（归集协议）作为核心拍板项
    - 第 5 轮：精确修正落点从 `artifacts/project/integrations/gstack/`（项目级）→ `artifacts/{branch}/.../gstack/`（branch+req 级），但仍保留独立 gstack/ 子目录的设计——**未触及"是否需要独立路径"的根本问题**
    - 第 6 轮：用户直接说出"gstack 的路径就不需要了"——一句话把前 5 轮的双产物 / 归集 / 落点 / 中央索引 / layout 扩段全部推翻，回到最简形态：**gstack 产物经 adapter 后**就是** harness 标准产物**
  - **第 6 轮 default-pick 重审**：
    - **Q7 整体作废**：无独立归集路径 / 无中央索引 / 无 manifest / 无 runs.jsonl / 无 .gitkeep / 无 layout 扩段
    - **chg-03 砍掉**（编号保留断号）：原归集协议失去对象；adapter 后处理子项并入 chg-02
    - **chg-02 扩展**：从"仅改 analyst.md 1 个文件"扩展为"analyst.md 改造（含 adapter 后处理段）+ role-command-map.yaml + README"
    - **chg-05 dogfood 落点更新**：从 `artifacts/{branch}/.../gstack/chg-05-dogfood/...`（Y''' 落点）→ 标准 `.workflow/flow/requirements/req-55-.../requirement.md`（直接覆盖本 req 的 template requirement.md）
    - **新增 Q-D dogfood 活证策略**：候选 R（最纯活证 / 自适用）= 用户主对话跑 /office-hours → analyst adapter 重组 design doc 到本 req 的 requirement.md（同时填实 template 状态）
  - **office-hours 输出格式 vs harness requirement.md 模板调研**（详见 §5.5）：
    - office-hours 输出落 `~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md`（user-level cache，不在仓库内）
    - 章节大部分有语义对应（Goal ← Problem Statement+Demand Evidence；Acceptance Criteria ← Success Criteria 强对齐；Split Rules ← Next Steps；Scope ← Constraints+Recommended Approach）
    - 多余段（Premises / Cross-Model Perspective / Open Questions / Distribution Plan / Dependencies / What I noticed / Reviewer Concerns）默认追加到 requirement.md 末尾作 `## Office Hours Notes` 附加段
    - frontmatter 互转无难度（`# Design: ...` 头部 → yaml id/title/created_at/operation_type/stage）
    - **意外收益**：office-hours 自带 Spec Review Loop（5 维度 + 3 轮迭代 + quality score）= harness analysis stage 当前缺失的质量门
  - **触发悖论解决**（详见 §5.5 路径 α default-pick）：
    - subagent 不能派发 slash command（`/office-hours`）
    - 路径 α default：analyst.md SOP 文档化"提示主 agent / 用户跑 /office-hours，反馈 path 后 analyst 跑 adapter"
    - analyst = adapter 消费者；主 agent / 用户 = /office-hours 真正调用者
  - **Q-A / Q-B 仍未明确表态**（用户至今未对范围收窄 + Q8 内置发布契约 7 子项明确同意 / 否认）；本轮新增 Q-D 同样需要拍板；单一开口问 ≤ 3 条把 Q-A / Q-B / Q-D 一次性问清楚（Q-C / Q7 已作废，不再问）

## 8.B.第 8 轮 chg-05 候选 R → P 修正（用户洞察驱动）

> 触发：用户在 executing stage 第三轮派发后（chg-04 完成报告后）抛出问题"那我是不是不应该用 /office-hours 而是应该用 harness-requirement"——一句话点破 chg-05 候选 R 的设计 bug。

### 用户洞察的本质

候选 R（用 req-55 自适用 dogfood）让用户**手动**在主对话跑 `/office-hours` 然后反馈 path 给 analyst。这条路径：

| 步骤 | 候选 R（错） | 真融合机制（chg-02 设计） |
|---|---|---|
| 入口 | 用户主动跑 `/office-hours` | 用户调 `/harness-requirement` |
| 触发链 | 跳过 harness-manager / 跳过 analyst Step A1.5 主动检测 / 跳过主动提示 | 完整链：harness-manager 派发 analyst → analyst 检测 gstack_status → analyst 主动提示用户 → 用户响应跑 office-hours |
| 验证范围 | 只验证 office-hours + adapter 函数本身 | 验证融合机制的端到端"自动触发"语义 |

候选 R 是把 office-hours **抽出来手测**，不是验证融合机制。第 7 轮 analyst 评估"候选 R 最纯活证"是错的——纯活证恰恰是 P 而不是 R。

### 修正动作

- **chg-05 change.md / plan.md 第 8 轮重写**（主 agent 直接修，按 base-role 硬门禁三降级"文档微调可直接做"）：
  - default-pick = 候选 P（用下一个真实 `/harness-requirement` 触发的 req-56+ 端到端兑现）
  - 第 7 轮的"R 三级降级到 P 到 Q"链废弃；P 上位为 default，Q 作为唯一保底（如 chg-01/02 入口链根本不可触发 → enter regression 修源头）
  - "sample req" 措辞已废弃——P 用任何下一个真实 req 都同样有效，"sample" 限定无意义
- **chg-05 落地形态变化**：
  - req-55 周期内：仅做 deferred 承诺 + retro 模板段预埋（在 `artifacts/project/experience/roles/analyst.md` 末尾追加占位段）+ scaffold_v2 mirror
  - 真活证由下一个真实 req 触发时由其 analyst 自动兑现（回填 retro 四点 + 在 chg-05 session-memory 追加触发证据条目）
- **第 7 轮版本保留**：git history 可查（commit 标记 "chg-05 v1 候选 R"），不删除作为版本演进留底

### 影响范围

- chg-05 change.md / plan.md 已重写 ✓
- chg-01/02/04 已落地产物**不受影响**：vendor / SKILL.md 推送 / analyst.md Step A1.5 / role-command-map / scaffold_v2 mirror 全保留——这些恰恰是候选 P 真活证要验证的产物
- requirement.md baseline 不变（第 7 轮 analyst 手工填）
- 不需 enter regression：本质是设计认知 bug 文档级修正，不涉及代码改动

### 第 7 轮误判根因

第 7 轮 analyst 评估三候选时把"自适用纯度最大"等同于"信号最纯"，忽视了"自适用绕过入口 = 跳过主动触发链 = 没验证融合机制"的核心矛盾。第 8 轮用户视角一句话还原本质：**入口决定验证语义**——融合机制要验证"用户用 `/harness-requirement` 时整套链自然跑通"，而非"用户手动调 office-hours 时 adapter 函数能跑"。

## 9. 完成 / 进展状态

- [x] 角色加载链 + 项目级覆盖加载完成（首次会话；本续跑会话不重做）
- [x] 现状调研完成（gstack / harness 两侧 skill 分布 + CLI / 入口比对）
- [x] 与用户开口 Q1~Q5（首会话）
- [x] 用户回应已吸收（Q1 锁定方向 a 强化版 + 新增 Q6 / Q7）
- [x] Q2~Q5 default-pick 在方向 a 强化版下重审完成
- [x] chg 拆分骨架重排预演（chg-01~05 + 条件 chg-06）
- [x] 第 2 轮：Q2~Q7 重审版 + chg 骨架已批量化抛给用户
- [x] 第 3 轮：吸收用户对 Q7 的精确修正——"放到制品仓库所属的文件夹汇总"；Q7.1~Q7.4 重做（双写 + 候选 X + 三件套 + 中央索引 + c 兜底）；chg-03 关键产物表更新
- [x] 第 4 轮：吸收用户两条指令——(A) 一步步融入仅 analyst → /office-hours；(B) gstack 内置 + harness install 自动装载
- [x] 第 5 轮（前会话）：吸收用户对 Q7.2 落点的精确修正——"qc制品跟对人文档放在一起，也就是和分支和需求有关"；推翻第 3 轮候选 X（项目级集中），改选候选 Y'''（gstack 兄弟目录，落 `artifacts/{branch}/requirements/{req-id}-{slug}/gstack/`）；chg-03 / chg-05 落点更新；layout 扩段对象改为 §2 白名单 + §3.1 (i) 扁平契约双扩段
- [x] **第 6 轮（本会话）：吸收用户范式级概念修正——"gstack 路径不需要了，它生成的就是需求文档"**；推翻 Y / Y' / Y'' / Y''' 全部候选；Q7 整体作废；chg-03 砍掉（编号保留断号）；chg-02 扩展含 adapter；chg-05 dogfood 落点改为标准 requirement.md 位置；新增 Q-D dogfood 活证策略（R / P / Q 三选一）
- [x] gstack vendor 可行性调研：MIT 允许 vendor / 1.1G 总规模但 office-hours 仅 164K / 现 install_agent 复制管线可复用 / 仅 Claude Code 启用
- [x] **第 6 轮 office-hours 输出格式调研**：落盘路径 `~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md`；startup/builder 双 mode 模板；与 harness requirement.md 章节级 mapping 表已绘（Success Criteria ← AC 强对齐 / Problem Statement+Demand Evidence ← Goal / Constraints+Recommended Approach ← Scope / Next Steps ← Split Rules）；多余段 6+ 个追加到 `## Office Hours Notes`；自带 Spec Review Loop 5 维度 + 3 轮迭代
- [x] §6 Q2~Q7 重排：Q2~Q5 退化为 trivial-default；Q6 被 Q8 吸收；**Q7 第 6 轮整体作废**
- [x] §6 Q8 新增完成（7 个子问题 + default-pick 全给）
- [x] **§6 Q-D（第 6 轮）新增完成**（候选 R / P / Q 三选一，default=R 最纯自适用活证）
- [x] §8 决策清单第 6 轮重排（核心拍板项 = Q-A / Q-B / Q-D；Q7 / Q-C 已作废）
- [x] §8.A chg 骨架第 6 轮重排：4 个 chg（chg-01 vendor+装载 / chg-02 改造+adapter / ~~chg-03 砍掉~~ / chg-04 镜像 / chg-05 dogfood）；编号保留断号
- [x] **第 7 轮（本会话）：用户拍板 Q-A / Q-B / Q-D 全部接受 default-pick + Q8.2 vendor 范围修正（全 47 skill）**
- [x] **第 7 轮 vendor 真实体积 + 依赖性调研**（详见 §4.7）：47 SKILL.md / 384KB 仅 symlink；vendor 必须含 _shared/{bin,agents,scripts}（SKILL.md 内嵌硬编码路径）；估算实体 vendor 后总体积数 MB ~ 几十 MB 量级
- [x] **第 7 轮 requirement.md 手工 baseline 填实**（含 frontmatter stage="analysis" + Goal + Scope + 8 条 AC + Split Rules + Office Hours Notes 占位段）
- [x] **第 7 轮 4 个 chg 的 change.md + plan.md 全部落地**（chg-01 / chg-02 / chg-04 / chg-05；chg-03 不建目录保留断号）
- [ ] **当前等用户对完整 analysis 产出做最终拍板**（requirement.md baseline + 4 个 chg change.md/plan.md）
- [ ] 拍板通过 → harness next 转 executing stage 分发各 chg 给 dev / executing 角色
- [ ] **chg-05 dogfood 活证（候选 R）执行**：用户主对话跑 /office-hours → analyst adapter 重组 → 覆盖第 7 轮 baseline；retro 笔记落 analyst 经验文件

## 10. 续跑会话留底

### 10.1 第 2 轮（前一会话）

- 模型自检 Step 7.5：briefing expected_model=opus；本 subagent 实际运行 model=opus，与 role-model-map.yaml 一致
- 项目级加载链自检（硬门禁八）：artifacts/project/{constraints,experience,tools}/ 真实命中数 = 0（仅 6 个 index.md 模板骨架）
- 续跑动作：吸收用户三点 → 锁定 Q1=方向 a 强化版 → 重审 Q2~Q5 default-pick → 新增 Q6/Q7 → 重排 chg 骨架 → 一次性批量化抛 Q2~Q7

### 10.3 第 4 轮（本会话）

- 模型自检 Step 7.5：briefing expected_model=opus；本 subagent 实际运行 model=opus，与 role-model-map.yaml 一致
- 项目级加载链自检（硬门禁八）：与前三会话一致，真实命中数 = 0
- 续跑动作：
  1. 读 session-memory.md 完整恢复上下文（不重做现状摸底）
  2. 调研 gstack vendor 可行性（License / 仓库形态 / 单 skill 体积 / 跨 agent / 现 install_agent 机制）
  3. 吸收用户两条指令：(A) 一步步融入仅 analyst → /office-hours；(B) gstack 内置 + harness install 自动装载
  4. §4 加 4.3 段第 4 轮用户原话留底
  5. §5 加 5.4 段 gstack vendor 可行性调研结论 + Q8 default-pick 候选合成 + Q6 退化说明
  6. §6 重排：Q2~Q5 标记 trivial-default（无需拍板）；Q6 被 Q8 吸收（trivial）；Q7 第 3 轮版本仍生效（核心拍板项之一）；新增 Q8（7 子项 + default-pick 全给，核心拍板项之二）
  7. §8 决策清单按收窄重排
  8. §8.A chg 骨架极简化（5 chg；chg-06 砍掉）
  9. §8.B 加第 4 轮修正记录
  10. 单一开口问 ≤ 3 条核心：（A）范围收窄确认；（B）Q8 default-pick 是否接受；（C）Q7 + chg 骨架一并接受
- 关键决定 / 偏离：
  - Q8.4 装载目标 = **全局 ~/.claude/skills/{name}/**（与 gstack 自身布局一致；harness skill 项目级是不同语义，不强行对称）
  - Q8.2 vendor 范围 = **仅本 req 的 office-hours**（不一次性 vendor 全 47；后续 req 增量扩）
  - chg-06 lint 整体砍掉：本 req 仅"打通最小可用集"，lint 是后续稳定后的事
  - chg-04 不镜像 vendor 副本（assets/gstack-skills/ 是 harness 仓库自有资产，不入 scaffold——scaffold_v2 拿到的是 harness 自身的 install_local_skills 推送结果，无需镜像 vendor 源）
  - dogfood 活证（chg-05）落 req-55 自身 = 用 office-hours 反向校验本需求质量，闭环验证（用户 implicit 暗示但未明说，analyst 自主选择）

### 10.4 第 5 轮（本会话）

- 模型自检 Step 7.5：briefing expected_model=opus；本 subagent 实际运行 model=opus，与 role-model-map.yaml 一致
- 项目级加载链自检（硬门禁八）：与前四会话一致，真实命中数 = 0（artifacts/project/{constraints,experience,tools}/ 仅 6 个模板骨架 index.md，无实际可加载条目）
- 续跑动作：
  1. 读 session-memory.md 完整恢复上下文（不重做现状摸底）
  2. 读 `.workflow/flow/repository-layout.md` §1 / §2 / §2.1 / §3 / §3.1 复核（确认 `artifacts/{branch}/requirements/{req-id}-{slug}/` = 对人产物扁平目录、§2.1 项目级豁免仅 3 类、§3.1 (i) 扁平契约要求 req 目录无 changes/ 子目录）
  3. 吸收用户 Q7.2 落点精确修正：「qc制品跟对人文档放在一起，也就是和分支和需求有关」
  4. **推翻**第 3 轮 Q7.2 选定的候选 X（`artifacts/project/integrations/gstack/`）——用户明示 branch-aware + req-aware
  5. 设计候选 Y' / Y'' / Y''' 三方案 + 比选六维度（"放在一起"语义 / 扁平契约影响 / 多 chg 多 skill 可读性 / 中央索引落点 / 与 §2 白名单关系 / 跨 req 全局视图）→ default-pick = Y'''
  6. 更新 §4.4 第 5 轮用户原话留底 + 主 agent 解析
  7. 重写 §6 Q7.2 段（第 5 轮重审版）+ 标注第 3 轮拒绝 Y 的理由如何被 Y''' 解决
  8. 更新 §8 决策清单 Q7.2 行（落点 + 中央索引）
  9. 更新 §8.A chg-03 关键产物表（落点 + layout 扩段对象 + mirror 豁免理由 + 跨 req 全局视图后置）+ chg-05 dogfood 落点同步
  10. 更新 §8.B 加第 5 轮修正记录（关键纠正 + Y''' default-pick 比选结果 + 与 req-52 "跟项目走"原则的协调说明）
  11. 单一开口问 ≤ 3 条：(A) 范围收窄确认 / (B) Q8 内置发布契约 7 子项 / (C) Q7 第 5 轮修正版（Y''' 落点）一并拍板
- 关键决定 / 偏离：
  - **Q7.2 = 候选 Y'''**：`artifacts/{branch}/requirements/{req-id}-{slug}/gstack/{chg-id}-{slug}/{skill}-{ts}/`（gstack 兄弟目录）
  - **req 内中央索引**：`artifacts/{branch}/requirements/{req-id}-{slug}/gstack/index.md` + `gstack/runs.jsonl`（落 gstack/ 子树根，不再落顶层项目级路径）
  - **跨 req 全局视图后置**：本 req 不落实物全局索引，记入后续 sug 池（`harness gstack-index --all-req` 命令聚合扫描所有 `artifacts/*/requirements/*/gstack/runs.jsonl`）
  - **layout 扩段对象变更**：从 §2.1 项目级豁免（错）→ §2 白名单 + §3.1 (i) 扁平契约双扩段（正）
  - **第 3 轮误判根因留底**：把 gstack 制品归"项目级集成元数据"，错把对人产物当机器型；第 3 轮用户已明示"gstack 产物多是文档（对人）"，但 analyst 在 Q7.2 候选 X 选择中未把"对人产物"语义贯彻到底，落到了项目级机器型路径——本轮纠正
  - **Q-A / Q-B 仍未明确表态**：用户至今未对(A) 范围收窄 (仅 analyst → /office-hours) + (B) Q8 内置发布契约 7 子项 default-pick 表态；本轮单一开口问把 Q-A / Q-B / 修正后 Q-C 一次性问清楚

### 10.2 第 3 轮（前一会话）

- 模型自检 Step 7.5：briefing expected_model=opus；本 subagent 实际运行 model=opus，与 role-model-map.yaml 一致
- 项目级加载链自检（硬门禁八）：与前两会话一致，真实命中数 = 0
- 续跑动作：
  1. 读 session-memory.md 恢复上下文（不重做现状摸底）
  2. 读 `.workflow/flow/repository-layout.md`（实际位置）复核 artifacts/ 子树语义 + §2.1 项目级豁免边界 + §3 机器型权威落位
  3. 吸收用户对 Q7 的精确修正："gstack产物多是文档，需要放到制品仓库所属的文件夹汇总"
  4. Q7.1：a → c 双写（拒绝"不拦截"，避免破坏 gstack 内部链路如 context-save/restore）
  5. Q7.2：候选 X = `artifacts/project/integrations/gstack/runs/{req-id}/{chg-id}/{skill}-{ts}/`（项目级集中 + 内部按 req/chg 分层；与 req-52 跟项目走 / scaffold_v2 mirror 豁免一致）
  6. Q7.3：三件套（manifest.json + 关键产出复制 + README）+ 顶层 `index.md` 中央索引 + `runs.jsonl` 机器追加日志（落实"汇总"语义）
  7. Q7.4：保留 c（双写 + warn + state log），理由更新为"双写下原位仍在，回退柔和"
  8. chg-03 关键产物表大幅扩展（含 repository-layout §2/§2.1 扩段子事项 + .gitkeep 防 setuptools dot-file ignore，参考 bugfix-13 round-4）
  9. 单一开口问 Q2~Q6 是否接受 default-pick（用户至今未对 Q2~Q6 表态）+ Q7 重审完成版同步报告
- 关键决定 / 偏离：
  - 候选 X 落点 `artifacts/project/integrations/` 不在 repository-layout §2.1 现有 3 类豁免内（constraints / experience / tools）——chg-03 必须**先**做契约扩段（§2 末行"其他对人产物"扩展 或 §2.1 第 4 类豁免新增），才能落实归集目录；这点已在 chg-03 关键产物 (1) 中明示
  - Q7.2 候选 Y 被 default-pick 拒绝：`artifacts/{branch}/requirements/{req-id}/changes/` 在 §3.1 (i) 是扁平目录无 changes/ 子目录，强加 gstack-runs/ 会破坏 layout 契约；且"汇总"语义在 Y 下需另作中央索引
  - 候选 Z 被 default-pick 拒绝：双层落点引入一致性维护成本，单层 X + 中央索引已足

### 10.5 第 6 轮（本会话）

- 模型自检 Step 7.5：briefing expected_model=opus；本 subagent 实际运行 model=opus，与 role-model-map.yaml 一致
- 项目级加载链自检（硬门禁八）：与前五会话一致，真实命中数 = 0（artifacts/project/{constraints,experience,tools}/ 仅 6 个模板骨架 index.md，无实际可加载条目）
- 续跑动作：
  1. 读 session-memory.md 完整恢复上下文（前 5 轮已落地）（不重做现状摸底）
  2. **调研 /office-hours 输出格式 vs harness requirement.md 模板对齐**——读 `~/.claude/skills/gstack/office-hours/SKILL.md` Phase 5（L1525~1662）：output 落 `~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md`（user-level cache，不在仓库内）；startup/builder 双 mode 模板 12+ 段；自带 Spec Review Loop 5 维度 + 3 轮迭代 + quality score
  3. 读 req-55/requirement.md 当前状态：仍是 template（`stage: {{STAGE}}` 占位 + Goal/Scope/AC/Split Rules 全是 template 提示文本）
  4. 吸收用户范式级概念修正：「gstack的路径就不需要了啊，它生成的就是需求文档，后续的步骤就要根据这个阶段的需求文档来生成了」
  5. **整体推翻** Y / Y' / Y'' / Y''' 全部候选 + Q7 整套（Q7.1 双写 / Q7.2 落点 / Q7.3 三件套 + 中央索引 / Q7.4 失败回退 + repository-layout 扩段 + manifest + .gitkeep + runs.jsonl）
  6. 设计章节级 mapping 表（§5.5）：Goal ← Problem Statement+Demand Evidence；Acceptance Criteria ← Success Criteria（强对齐）；Split Rules ← Next Steps / The Assignment；Scope ← Constraints+Recommended Approach；多余段（Premises / Cross-Model / Open Questions / Distribution Plan / Dependencies / What I noticed / Reviewer Concerns）→ `## Office Hours Notes` 附加段
  7. 处理触发悖论（subagent 不能派发 slash command）：default-pick 路径 α = analyst.md SOP 文档化"提示主 agent / 用户跑 /office-hours，反馈 path 后 analyst 跑 adapter"
  8. 设计 Q-D dogfood 活证策略三候选：
     - 候选 P（最稳，新 sample req 演示，本 req 手工填实 requirement.md）
     - 候选 Q（最简，砍 chg-05，验收倒退选项 1）
     - 候选 R（最纯活证 / 自适用，用户主对话跑 /office-hours + analyst adapter 重组到本 req requirement.md）
     - default-pick = R（理由：用户范式修正的最直接证据 = 本 req 自身用这套流程产出 requirement.md；自适用纯度最高；adapter 真实工作量暴露给 chg-02 落地参考；同时填实 template 状态的 requirement.md，一举两得）
  9. 更新 §4.5 第 6 轮用户原话留底 + 主 agent 解析 + 范式转变对照表
  10. 新增 §5.5 第 6 轮 office-hours 输出格式调研（含章节级 mapping 表 + adapter 复杂度评估 + 触发悖论 default-pick 路径 α）
  11. 重写 §6 Q7 整段（标记整体作废 + 列前 5 轮历史快照供版本演进证据）+ 新增 Q-D（候选 R / P / Q + default-pick）
  12. 更新 §8 决策清单（Q7 行改为整体作废 trivial；新增 Q-D 行 default=R）
  13. 更新 §8.A chg 骨架（chg-03 砍掉作废占位 + chg-02 扩展含 adapter 后处理段 + chg-05 落点改为标准 requirement.md 位置 + 编号保留断号说明 + 第 6 轮范式修正记录）
  14. 更新 §8.B 加第 6 轮修正记录（关键修正 + 前 5 轮误判根因贯穿留底 + 第 6 轮 default-pick 重审 + office-hours 调研结论 + 触发悖论解决 + Q-A/Q-B 仍待表态）
  15. 单一开口问 ≤ 3 条：Q-A 范围收窄 / Q-B Q8 内置发布契约 7 子项 / Q-D dogfood 活证策略 R/P/Q 三选一
- 关键决定 / 偏离：
  - **Q7 整体作废**：从"独立归集协议"退化为 trivial（产物直接落标准 requirement.md 位置）
  - **chg-03 砍掉**（编号保留断号，给后续可能的恢复留稳定锚点 + 与 §8.B 修正记录中的 chg-03 引用兼容）
  - **chg-02 扩展含 adapter 后处理段**（吸收原 chg-03 的 adapter 子项；adapter 章节 mapping 表见 §5.5）
  - **chg-05 dogfood 落点改为标准 requirement.md 位置**（不再落 gstack/ 子树；Q-D=R 时直接覆盖本 req template 状态的 requirement.md）
  - **Q-D default-pick = R**（最纯活证 / 自适用），理由：用户范式修正的最直接证据 + 一举两得（活证 + 填实 template）+ adapter 工作量暴露
  - **触发悖论 default-pick = 路径 α**：保留"角色 = 调 gstack 命令"语义；analyst 文档化"提示主 agent + 跑 adapter"，主 agent / 用户兜底 slash command 调用
  - **office-hours 自带 Spec Review Loop 是意外收益**：5 维度 + 3 轮迭代 + quality score = harness 当前 analysis stage 缺失的质量门；adapter 不需要砍 Reviewer Concerns，直接保留追加到 requirement.md 末尾
  - **保留所有历史决策版本演进留底**（前 5 轮 Q7 决策日志在 §6 Q7 段历史快照 + §8.B 修正记录第 2~5 轮均完整保留），不删除以保历史可追溯性

### 10.6 第 7 轮（本会话，最终落地轮）

- 模型自检 Step 7.5：briefing expected_model=opus；本 subagent 实际运行 model=opus，与 role-model-map.yaml 一致
- 项目级加载链自检（硬门禁八）：与前六会话一致，真实命中数 = 0（artifacts/project/{constraints,experience,tools}/ 仅 6 个模板骨架 index.md）
- 续跑动作：
  1. 读 session-memory.md 完整恢复上下文（前 6 轮已落地）
  2. **第 7 轮 vendor 体积 + 依赖性调研**：执行 `ls -d ~/.claude/skills/*/`、`find ~/.claude/skills/ -name SKILL.md`、`du -sh`、抽样 SKILL.md 内嵌路径调用——确认 47 SKILL.md / 仅 symlink 384KB / vendor 必须含 _shared/{bin,agents,scripts}
  3. 吸收用户拍板：Q-A / Q-D 接受 default；Q-B 整体接受 + Q8.2 vendor 范围修正（仅 office-hours → 全 47）
  4. 引入"装载层全装 / 融合层渐进"关键概念分离
  5. 落地 9 个产物文件：
     - `requirement.md` 手工 baseline 填实（含 8 条 AC / 4 chg 拆分 / 渐进扩展规划 / Office Hours Notes 占位段）
     - chg-01 change.md + plan.md（vendor 全 47 + 装载推送 + License 4 项归因 + runtime schema + 测试）
     - chg-02 change.md + plan.md（analyst.md Step A1.5 三段 + role-command-map.yaml + README）
     - chg-04 change.md + plan.md（scaffold_v2 镜像 + mirror 校验 + 契约校验）
     - chg-05 change.md + plan.md（候选 R 执行流程 + 降级路径 P / Q + retro 四点）
  6. 更新 session-memory：§4.6 第 7 轮拍板留底 / §4.7 vendor 调研结论 / §6 状态结案 / §8 default-pick 决策表 Q-A/B/D 行 / §8.A chg-01 关键产物表（vendor 全 47）/ §8.B 第 7 轮拍板记录 / §9 进展状态 / §10.6 第 7 轮续跑留底
  7. 完成后停下，等用户对完整 analysis 产出（requirement.md + 4 chg change.md/plan.md）做最终拍板
- 关键决定 / 偏离：
  - **Q8.2 vendor 范围 = 全 47 skill**（用户第 7 轮修正，从"仅 office-hours"扩展）
  - **vendor 副本路径设计**：每 skill 一目录 `assets/gstack-skills/{name}/...` + 顶层共享 `_shared/{bin,agents,scripts}`（SKILL.md 内嵌硬编码路径要求）
  - **装载层 / 融合层分离**：装载一次到位（用户立即能用任意 gstack skill），融合渐进（避免 adapter 工作量爆炸）
  - **chg-03 不建目录**（保留断号；编号给后续可能恢复留稳定锚点）
  - **9 个产物文件全部落地**：要求 8~12 个工具调用内完成，本轮实际 ≈ 12 次 Write/Edit + 4 次 Bash（调研）+ 2 次 Read（恢复上下文 + 模板复核）

- **第 7 轮（本会话）用户拍板 + Q-B Q8.2 vendor 范围修正 + 落地 9 个文件**：
  - 用户原话：「qb 装载gstack所有命令 只是暂时只在harness中接入office-hours用来产生requirement.md 其他的都接受」
  - **拍板结果**：Q-A / Q-D 接受 default-pick；Q-B 整体接受 + Q8.2 vendor 范围修正（从"仅 office-hours"扩到"全部 47 个 gstack skill"）
  - **关键概念分离（用户新引入）**：装载层全装（用户主对话能直接 /<skill-name> 触发任意 gstack skill）vs 融合层渐进（角色 SOP 强映射仍仅 analyst → /office-hours，后续 req-56~59 各扩 1）
  - **第 7 轮调研结论**：47 SKILL.md / 仅 symlink 384KB；vendor 必须含 _shared/{bin,agents,scripts}（SKILL.md 内嵌 ~/.claude/skills/gstack/bin/gstack-* 硬编码调用）；vendor 体积估算数 MB~几十 MB 量级
  - **第 7 轮落地的 9 个文件**：
    - `requirement.md`（手工 baseline 填实，frontmatter stage=analysis + Goal + Scope + 8 条 AC + Split Rules + Office Hours Notes 占位段）
    - `chg-01-gstack-内置发布契约/{change.md,plan.md}`（vendor 全 47 + 装载推送 + License + runtime schema + 单元 / 集成测试）
    - `chg-02-analyst-office-hours-强映射/{change.md,plan.md}`（analyst.md 注入 Step A1.5 三段：触发协议 + adapter mapping + fallback；role-command-map.yaml 1 行；README ≤ 50 行）
    - `chg-04-scaffold-v2-镜像/{change.md,plan.md}`（scaffold_v2 镜像 chg-02 三个文件；不镜像 vendor 副本；mirror 校验 + 契约校验）
    - `chg-05-dogfood-活证/{change.md,plan.md}`（候选 R 执行流程：用户主对话跑 /office-hours → analyst adapter 重组覆盖 baseline → retro 四点入 analyst 经验文件）

### 4.6 第 7 轮（本会话）用户拍板留底 + Q-B Q8.2 修正

> 用户原话：「qb 装载gstack所有命令 只是暂时只在harness中接入office-hours用来产生requirement.md 其他的都接受」

主 agent 解析 + 本 analyst 吸收：

| 项 | 拍板结果 |
|---|---|
| Q-A 范围收窄（仅 analyst → /office-hours，其他 4 角色推后续 req-56~59） | **接受 default-pick** |
| Q-D dogfood 活证（候选 R：用户主对话跑 /office-hours → analyst adapter 重组 requirement.md） | **接受 default-pick** |
| Q-B 整体（Q8 七子项 + chg 骨架 + chg-03 砍掉断号保留） | **接受**，**但 Q8.2 vendor 范围修正** |
| Q8.2 vendor 范围修正 | 从"仅 office-hours"扩到"全部 gstack skill（约 47 个 SKILL.md）"——装载层全装好，融合接入层仍仅 analyst → /office-hours |

**关键概念分离（用户第 7 轮新引入）**：

| 层 | 范围 | 推进策略 |
|---|---|---|
| **装载层**（chg-01 vendor + harness install 自动推送） | **全部** gstack skill（用户在 Claude Code 里能直接 `/<skill-name>` 触发任意 gstack skill） | 一次到位 |
| **融合层**（chg-02 角色 SOP 强映射） | **仅** analyst → /office-hours 一条；后续 req 各扩 1 角色 → 1 skill | 渐进扩展（req-56~59） |

**理由（用户决策合理性）**：
- 装载层全装"成本不高"——47 个 SKILL.md（每个仅几 KB～几十 KB）+ 顶层 bin/agents/scripts 共享资源，估算总体积数 MB～几十 MB（远小于 gstack 全仓库 1.1G 含 .git/build/node_modules）
- 装载层全装"价值高"——用户在主对话立即可用任意 gstack skill（不必等 harness 增量接入）
- 融合层渐进——避免一次性接入全部 skill 的 adapter 工作量爆炸；adapter mapping 表须按 skill 设计，不可机械复用

### 4.7 第 7 轮 vendor 实际体积 + 依赖性调研结论

执行的调研命令：
- `ls -d ~/.claude/skills/*/ | wc -l` → **48** 个顶层目录（含 `gstack` 仓库本身）
- `find ~/.claude/skills/ -maxdepth 2 -name SKILL.md | wc -l` → **47** 个 SKILL.md
- `du -sh ~/.claude/skills/` → **1.1G**（但这 1.1G **就是** `~/.claude/skills/gstack/` 仓库整 clone，含 .git / node_modules / build）
- 排除 gstack 仓库本身后 47 个独立 skill 目录总和 = **384 KB**（仅符号链接元数据）

**关键发现 1（vendor 真实体积）**：
- `~/.claude/skills/<skill-name>/SKILL.md` 全部是**符号链接**指向 `~/.claude/skills/gstack/<skill-name>/SKILL.md`
- 47 skill 加起来 384 KB（仅 symlink）；每个 SKILL.md 实体在 `gstack/<skill-name>/SKILL.md`
- vendor 时需把每个 SKILL.md 复制为**实体文件**到 `src/harness_workflow/assets/gstack-skills/{skill-name}/`
- 估算 vendor 后体积：47 个 SKILL.md（每个 5~50KB）+ 部分 skill 的 references/ scripts/ 子资源 + 顶层 bin/agents/scripts 共享 → 总约 **数 MB ~ 几十 MB 量级**

**关键发现 2（依赖性 — vendor 必须含共享资源）**：
- 抽样 office-hours/SKILL.md 内嵌 `~/.claude/skills/gstack/bin/gstack-{update-check,config,telemetry-log,repo-mode,slug}` 等绝对路径调用
- 多个 SKILL.md 共用这套二进制；vendor 单纯复制 SKILL.md **不够**，必须把 gstack 仓库顶层 `bin/agents/scripts/` 一并 vendor 到 `_shared/`，并推送到 `~/.claude/skills/gstack/{bin,agents,scripts}/` 路径（与 SKILL.md 内嵌硬编码路径一致）
- 抽样 `office-hours/`, `qa/`, `codex/` 这三个 skill 目录在 `~/.claude/skills/{name}/` 下**没有** references/ scripts/ 子目录（仅 SKILL.md 一个 symlink）；但 gstack 仓库顶层下的源文件是否有同 skill 的 references / scripts，需 vendor 脚本运行时确认（保守起见复制整个 skill 目录）

**关键发现 3（vendor 副本路径设计）**：
- 每 skill 一目录：`src/harness_workflow/assets/gstack-skills/{skill-name}/SKILL.md` + `references/` + `scripts/`（若存在）+ `LICENSE-gstack` + `VERSION-gstack`
- 顶层共享：`src/harness_workflow/assets/gstack-skills/_shared/{bin,agents,scripts}/` + `_shared/LICENSE-gstack` + `_shared/VERSION-gstack`
- 装载推送：`_shared/{bin,agents,scripts}/` → `~/.claude/skills/gstack/{bin,agents,scripts}/`（与 SKILL.md 硬编码路径一致）；每个 skill 目录 → `~/.claude/skills/<skill-name>/`
  - **Q-A / Q-B 仍未明确表态**：用户至今未对范围收窄 + Q8 内置发布契约 7 子项明确同意 / 否认；本轮新增 Q-D 同样需要拍板；单一开口问 Q-A / Q-B / Q-D 三条一次性问清楚（Q-C / Q7 已作废，不再问）
