---
id: req-53
title: "新增-harness-命令-给项目添加规范-经验-工具-引导式"
created_at: 2026-04-30
operation_type: requirement
stage: analysis
---

## Background

### 用户原话

> 「可以开发一个命令专门给项目增加规范经验工具」

### 现状盘点

req-51（项目级规则-经验-工具支持从制品引入）/ req-52（硬编码 main 路径全面去除-跟项目走-索引懒加载-流程日志验证）/ bugfix-13（install 时自动创建 artifacts/project 骨架与索引模板）已立稳**项目级机器型文档承载层**：

- 主路径 `artifacts/project/{constraints,experience,tools}/`（无 branch 维度，跟项目走，所有 git branch 共享读）
- `experience/` 下分 `roles / tool / risk / regression / stage` 五子目录
- 6 份 `index.md` 模板（constraints / tools / experience-{roles,tool,risk,regression,stage}）由 `_bootstrap_project_skeleton` 在 `harness install` / `harness update` 时幂等拷贝
- `_merge_project_level_files` 已接入 install 主流程，stderr 输出 `[harness] project-level loaded: N files from artifacts/project/{scope}/（fallback=...）` 可观测信号
- 加载链上层：`role-loading-protocol.md` Step 7.6 / 7.6.1（索引懒加载）+ `tools-manager.md` Step 2.0 项目级覆盖全局合并

承载层（"地皮"+ "门牌"+ "邮差"）已就位，但**入口缺失**——目前 user / AI 想往 `artifacts/project/` 添加东西时，没有命令封装，必须手动 `vim` + 手动改 index.md + 手动 `git add`。

### 实测痛点（用户在另一 session 暴露）

1. **AI 自己发明路径**：曾尝试落 `artifacts/standards/coding/`（不是规范定义的 `artifacts/project/constraints/`）；目录命名对 AI 不够直觉，加载链直接失效（写到一个不在加载链扫描范围内的目录）。
2. **加完规范没有自动登记到 index.md**：内容文件存在但 `index.md` 未追加新行 → 索引懒加载（`_load_project_level_index`）扫不到 → agent 加载链对该文件**完全不可见**。
3. **没有强制提醒 git commit**：`artifacts/` 已 git tracked，但 user 加完文件忘 `git add` + commit → 切 branch / 跨设备拉代码时新加的规范丢失，团队协作失效。

三点叠加 → "我加了规范但 AI 没读到" 投诉路径。

### 用户想要的

**一条 harness 命令**封装"加规范 / 加经验 / 加工具"全套：给 user / AI 一个明确的入口，落位自动正确（不发明路径）+ index.md 自动登记（保加载链）+ git tracking 提醒（保团队同步）。形态参考 `harness suggest` / `harness requirement` / `harness bugfix` —— 这三条命令都是"创建机器型工件 + 进流程"的统一模式，本 req 借鉴该形态扩展到"项目级承载层维护"语义。

## Goal

给 harness 增加**项目级承载层维护命令**，让 user / AI 用一条命令就能正确添加规范 / 经验 / 工具到 `artifacts/project/`，避免发明路径 + 漏登记 + 漏 commit 三类已知陷阱。

可度量预期：

1. **G-01 落位 100% 正确**：跑一次命令 → 文件 100% 落到 `artifacts/project/{constraints,experience/{roles,tool,risk,regression,stage},tools}/{slug}.md`，不出现 `artifacts/standards/` 之类发明路径。
2. **G-02 index.md 自动登记**：新建文件后 `index.md` 自动追加一行（含 `path / title / scope / when_load`），加载链 `_load_project_level_index` 立即可见。
3. **G-03 模板预填**：新建文件含 frontmatter（`tool_id` / `keywords` / `scope` 等按 scope 区分）+ 占位段（`## 用途` / `## 内容` / 等），user 仅需填业务文字。
4. **G-04 加载链可观测**：命令执行末尾 stderr 输出一行 `[harness] project-level loaded: N+1 files from artifacts/project/{scope}/`，让 user 看到"刚加的会被 agent 加载"的活证。
5. **G-05 git tracking 提醒**：命令成功后 stdout 提示 user `git add artifacts/project/{...}.md && git commit`（或按 OQ-5 决策直接 stage 后再提示 commit）。
6. **G-06 AI 在新会话能 read 到内容**：新会话加载 role-loading-protocol Step 7.6 时，新增的规范 / 经验 / 工具按 `when_load` 解析后正常合并到 agent 上下文（端到端活证）。

## Scope

### In scope（必须包含）

- **CLI 入口形态**（OQ-1 决策）：
  - **default-pick = 候选 C**：统一命令 `harness project-add <kind> [<scope>] <title>`，`kind ∈ {rule, experience, tool}`，`scope` 仅在 `kind=experience` 时有意义（取 `roles / tool / risk / regression / stage` 之一）。
  - 候选 A：`harness rule <type> <title>`（type 含 coding / business / security）—— 不够覆盖 experience / tool 三大类。
  - 候选 B：三命令分立 `harness add-rule` / `harness add-experience` / `harness add-tool` —— 命令面铺得宽，CLI 学习成本高。
  - 选 C 的理由：覆盖三大 kind + 与 `harness requirement` / `harness bugfix` 同一"动词 + 名词"句式 + 对应 `_bootstrap_project_skeleton` 已分好的三大类 1:1 映射。

- **子命令覆盖**（OQ-2 决策）：v1 仅含 `add`（默认隐式动词，即 `harness project-add`）+ `list`（必备，调试加载链时高频）；`remove` / `show` / `move` 推迟到 v2。

- **interactive / non-interactive 双模**（OQ-3 决策）：默认接受位置参数 `harness project-add <kind> [<scope>] <title>`；当 user 不带参数（`harness project-add`）时进入 questionary 引导（与 `harness suggest` 走 `--title` 必填同款 prompt 风格）。

- **落位逻辑**：按 `kind` + `scope` 自动算路径——
  - `kind=rule` → `artifacts/project/constraints/{slug}.md`
  - `kind=tool` → `artifacts/project/tools/{slug}.md`
  - `kind=experience scope=roles` → `artifacts/project/experience/roles/{slug}.md`
  - `kind=experience scope=tool` → `artifacts/project/experience/tool/{slug}.md`
  - `kind=experience scope={risk,regression,stage}` → 同款规则
  - slug 由 title 经 `_slugify` helper 转换（已在 cli.py 复用）。

- **index.md 自动登记**：新建文件后追加一行到对应子目录 index.md 的 markdown 表格（`| path | title | scope | when_load | 备注 |`），`when_load` 按 OQ-4 决策给默认值（`always` 或按 kind 区分）；表头若不存在则补齐。

- **模板预填**：每个 kind 各自一份 `.tmpl` 模板（落 `src/harness_workflow/assets/templates/project-add/{kind}.md.tmpl`），渲染时填 title / created_at / scope / `tool_id`（仅 tool）等 frontmatter 字段 + 占位段。

- **git tracking 提醒 / 自动 stage**（OQ-5 决策）：命令成功后**不直接 commit**（不可逆 / 越权），但 stdout 提示 `git add` + `git commit -m` 命令模板；OQ-5 决策决定是否 `git add` 自动 stage（vs 仅提示）。

- **加载链可观测**：命令末尾调一次 `_log_project_level_load(root, scope_for_this_kind, hits=N+1, fallback_used=False)` → stderr 输出活证，与 install 主流程同款格式。

- **slash command 同步**：新增 `.claude/commands/harness-project-add.md`，与 `harness-suggest.md` 同款 hard gate 模板。

### Out of scope（明确不做）

- **不做"标准引擎"**：不解析规范条文 / 不做 lint / 不做"该规范是否被代码遵守"自动检查；本 req 仅做承载层维护工具，规范执行靠 agent 加载链 + 人工 review。
- **不动现有 `install_repo` / `_merge_project_level_files` / `_bootstrap_project_skeleton` 主流程**：仅在 cli.py 扩 `subparsers.add_parser("project-add", ...)` 入口 + 新增 helper `_create_project_artifact(...)`。
- **不改 `artifacts/project/*` 路径规范**：路径表已 req-52 chg-01 立稳，本 req 严格复用，禁止再发明 `artifacts/standards/` 之类路径。
- **v1 不含 remove / show / move 子命令**：复杂度溢出，留 v2。
- **v1 不做 git auto-commit**：不可逆 / 改 user 工作树状态，最多 `git add`（OQ-5 决策）。
- **不动 PetMallPlatform / PetMallAdmin / uav 仓**：本 req 修复面只在 harness-workflow 仓内（与 bugfix-11 红线一致）。
- **不引入 `_use_*_layout*` / `*_LAYOUT_FROM_*` 命名**：bugfix-11 红线延续。

### § OQ Verdicts（关键决策点 default-pick + 一句话理由）

| OQ id | 决策点 | default-pick | 理由 |
|------|-------|------------|------|
| OQ-1 | 命令形态选择（A / B / C 三候选） | **C：`harness project-add <kind> [<scope>] <title>`** | 覆盖三大 kind + 复用 `harness requirement` 句式 + 与 `_bootstrap_project_skeleton` 三大类 1:1 映射 |
| OQ-2 | v1 子命令覆盖范围（add / list / remove / show / move） | **add + list 二选项** | add 必备；list 调试加载链时高频；remove / show / move 推迟 v2 控复杂度 |
| OQ-3 | 是否支持 interactive 模式（无参数 questionary 引导） | **支持，默认开启** | 与 `harness suggest --title` 必填同款风格；user 忘记参数时不报错而是引导 |
| OQ-4 | index.md 中 `when_load` 字段默认值 | **always** | 项目级规则 / 经验 / 工具默认全场景加载，user 改为 `on-stage:executing` / `on-keyword:lint` 须显式声明（兼容 schema） |
| OQ-5 | 是否自动 `git add` stage 新文件（vs 仅打印提醒） | **自动 `git add` + 打印 `git commit` 提示，不自动 commit** | `git add` 可逆（user 可 `git restore --staged`）；commit 不可逆需用户决策；同时降低"忘 git add"漏 commit 风险 |

> 每条 OQ 用户若有异议，可在用户确认轮一次性 batched 反馈；analyst 按硬门禁四同阶段不打断原则按 default-pick 推进 Phase 2。

## Acceptance Criteria

- **AC-01（落位正确）**：`harness project-add rule "代码风格"` 后，`artifacts/project/constraints/代码风格.md` 文件存在；包含 frontmatter（`title / created_at / scope: constraints / when_load: always`）+ `## 内容` 占位段。
- **AC-02（index.md 自动登记）**：执行 AC-01 后，`artifacts/project/constraints/index.md` 表格新增一行 `| 代码风格.md | 代码风格 | constraints | always | (空) |`；表头若缺失则同时补齐。
- **AC-03（加载链可观测）**：AC-01 命令执行末尾 stderr 含一行 `[harness] project-level loaded: N+1 files from artifacts/project/constraints/（fallback=n/a）`，N 为执行前文件数。
- **AC-04（install 不覆盖）**：执行 AC-01 后，跑 `harness install --force-managed`，新加的 `代码风格.md` + `index.md` 表格新行**不被覆盖**（mirror 白名单 + protected-zones 双豁免，与 OQ-4 一致）。
- **AC-05（lint 通过）**：执行 AC-01 后，跑 `harness validate --contract user-write-protected-zones` exit code = 0。
- **AC-06（list 子命令）**：跑 `harness project-add list` → stdout 列出 `artifacts/project/{constraints,experience/*,tools}/` 下所有已登记文件（按 kind / scope 分组，按 6 份 index.md 解析结果汇总）。
- **AC-07（fresh repo dogfood）**：在空仓 `git init` + `harness install` 后，跑 `harness project-add experience tool "apifox-用法"` → 文件落 `artifacts/project/experience/tool/apifox-用法.md` + `artifacts/project/experience/tool/index.md` 自动追加 + `harness install --check` 不报错。
- **AC-08（interactive 模式）**：裸跑 `harness project-add` 进入 questionary 引导，依次问 kind（select）/ scope（仅 kind=experience 时）/ title（input）→ 三步答完后落地行为与位置参数一致。
- **AC-09（git tracking 提醒）**：AC-01 命令成功后 stdout 含 `git add artifacts/project/constraints/代码风格.md` + `git commit -m "feat: 项目级规范-代码风格"` 两行提示；按 OQ-5 决策实际已 `git add`，user 仅需 `git commit`。
- **AC-10（PetMallPlatform 真实仓自验）**：在 PetMallPlatform 仓（其 `artifacts/project/` 已被 req-52 / bugfix-13 自动 bootstrap 出来）跑 `harness project-add tool "petmall-deploy"` → 路径正确 + index.md 登记 + `git status` 显示已 staged + agent 在新会话 read 到。

## Split Rules

- 拆 chg 由 analyst 自主完成（base-role 硬门禁四同阶段不打断；req-40 方向 C analyst 合并规约）。
- 推荐拆分形态（仅供 Phase 2 参考，不在 Phase 1 锁死）：
  - chg-01：`harness project-add` CLI 子命令骨架（argparse + 入口分发）+ `_create_project_artifact` helper
  - chg-02：模板系统（3 份 `.tmpl` + 渲染 helper）+ index.md 自动登记 helper
  - chg-03：interactive 模式（questionary 引导）+ list 子命令
  - chg-04：git tracking（auto stage）+ 加载链 stderr 活证 + slash command 同步
  - chg-05：dogfood + 真实仓自验 + 文档同步（README / WORKFLOW.md 入口）
- 每 chg 独立可交付（单测 + dogfood 闭环）；执行顺序 chg-01 → chg-02 → chg-03 → chg-04 → chg-05。

---

## OQ Verdicts（用户 2026-04-30 拍板，锁定）

| # | 决策 | 用户拍板 |
|---|------|---------|
| **OQ-0**（命令名） | `harness pad <kind> [scope] <title>` | **pad**（短命令，全名 project-add 仍可作 alias） |
| **OQ-1** 命令形态 | C 统一 + kind 顶层固定 3 个：`rule` / `experience` / `tool` | A |
| **OQ-2** v1 子命令 | `add`（默认）+ `list` | A |
| **OQ-3** interactive | 默认开启（无参数 → questionary 引导） | A |
| **OQ-4** index.md when_load 默认 | `always` | A |
| **OQ-5** git tracking | 自动 `git add` + 提示 commit | A |

### kind / scope 枚举（**固定枚举，user 不能发明**）

**`rule` scope = 5 个**（落 `artifacts/project/constraints/{scope}/{slug}.md`）：
- `coding` — 命名 / 格式 / 注释 / 错误处理
- `architecture` — 模块分层 / 依赖方向 / 边界划分
- `api` — REST / RPC / 协议 / 错误码
- `database` — 建模 / 索引 / 迁移 / 命名
- `security` — 鉴权 / 注入防护 / 加密 / 数据脱敏

**`experience` scope = 5 个**（落 `artifacts/project/experience/{scope}/{slug}.md`，沿用 req-51/52 既有）：
- `roles` / `stage` / `regression` / `risk` / `tool`

**`tool` 不分 scope**（直接落 `artifacts/project/tools/{slug}.md`）。

### 命令使用样例（最终形态）

```bash
# add 规则
harness pad rule coding "禁止-API-硬编码"
harness pad rule security "JWT-token-必须-RS256"

# add 经验
harness pad experience stage "executing-阶段虚报教训"
harness pad experience regression "走偏根因抽样模板"

# add 工具
harness pad tool "petmall-mcp-deployer"

# list 已有
harness pad list

# 无参数：interactive
harness pad
# → questionary：选 kind → 选 scope（如 kind=rule/experience）→ 输 title
```

### 反非法 lint（同步落地，用户输错时给出建议）

- 跑 `harness pad rule standards "..."` （`standards` 非合法 scope）→ ABORT + 提示「rule scope 必须是 coding/architecture/api/database/security 之一」
- 跑 `harness pad foo bar "..."` （非合法 kind）→ ABORT + 提示「kind 必须是 rule/experience/tool 之一」

### 范围红线

- 修复面 limited 在 harness-workflow 仓
- 不动 PetMallPlatform / PetMallAdmin / uav 等用户仓
- 不破 req-51/52/bugfix-13 已立 `artifacts/project/{constraints,experience,tools}/` 路径标准
- artifacts/project/constraints/ 下增加 `{scope}/` 子目录但不破 index.md 加载链（index.md 自动按 scope 分组登记）
