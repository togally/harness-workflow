# Requirement

## 1. Title

动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入

## 2. Background（为什么做）

- 当前 `harness update` 从 `scaffold_v2/` 同步**静态模板**，不扫描本仓的项目描述文件，导致 `.workflow/context/` 对项目用途 / 技术栈 / 规范"一无所知"
- 当前 harness-manager / CTO 派发 subagent briefing 仅含 role / stage / req-id / title（req-31（批量建议合集（20条））sug-09（briefing 增补 req-id + title）刚加），缺少**按任务内容裁剪的上下文索引**；下游 subagent 仍需盲扫全量 `.workflow/context/index.md`，context 消耗大且命中率低
- 两处 gap 共享底层能力：项目描述扫描器（产出项目 profile）+ 上下文索引构建器（按内容选文件）

## 3. Goal（做完后期望状态）

- `harness update` 扫项目描述文件生成 / 刷新 `.workflow/context/project-profile.md`，下游角色可读
- CTO 派发 subagent 时基于任务内容 + project profile 产出 `task_context_index`（建议清单），写入 briefing
- subagent 按索引最小加载 `.workflow/context/**`，命中即用，未命中回退全量 index
- 每次派发的 `task_context_index` 以只读快照落状态仓（`.workflow/state/sessions/{req-id}/task-context/{stage}-{seq}.md`），归档时随 req 迁入 `artifacts/.../sessions/`，供事后复查与优化迭代

## 4. Scope

### 包含

- `harness update` 新增项目描述扫描步骤：识别 pyproject.toml / package.json / pom.xml / go.mod / Cargo.toml / README / CLAUDE.md / AGENTS.md
- 静态解析提取结构化字段（包名、语言、主要依赖、入口命令、技术栈标签）
- 产出 LLM prompt 模板供主 agent 填充项目用途 / 风格描述（B3 方案）
- 生成 `.workflow/context/project-profile.md`（带 hash 漂移检测）
- harness-manager / CTO 派发 subagent 的 briefing 增加 `task_context_index` 字段（建议清单，≤ 8 条，每条带一行理由）
- 覆盖派发路径：`harness next --execute` + `harness ff --auto` + `regression` 相关派发
- 每次 `harness next --execute` / `ff --auto` / regression 派发后，`task_context_index` 同时落快照到 `.workflow/state/sessions/{req-id}/task-context/{stage}-{seq}.md`，含 frontmatter（req-id / stage / ts / index_count）+ 正文（`{path}: {reason}` 每行一条）
- subagent briefing JSON 含双字段：`task_context_index`（原文列表）+ `task_context_index_file`（快照相对路径）

### 不包含

- 不自动改写 `.workflow/context/experience/**` 或 `platforms.yaml`（留后续 chg 评估）
- 不改造 tools-manager 推荐派发、done 六层回顾派发（留后续 req）
- 不引入 harness CLI 内的 LLM 直接调用（B3：CLI 只产 prompt，LLM 调用由主 agent 执行）
- 不破坏既有用户自定义的 CLAUDE.md / AGENTS.md / SKILL.md（复用 req-31（批量建议合集（20条））sug-14（用户自定义 CLAUDE/AGENTS/SKILL 保护）`_is_user_authored`）
- 不新增 `harness status --context-stats` 或类似 CLI 观测命令（用户直接读快照文件即可）
- 不把 task-context 快照直接写入制品仓 `artifacts/`（快照先落状态仓，归档时走既有 archive 路径迁移）
- 不做热点文件统计 / TopK 分析 / 索引命中率自动报告等功能（留给人工或后续 req）

## 5. Acceptance Criteria

- **AC-01**：本仓 `harness update` 执行后生成 `.workflow/context/project-profile.md`，文件含 ① 项目语言 / 包名 / 主要依赖结构化字段 ② 预留 LLM 用途 / 风格段（或 prompt 占位）③ 生成时间戳
- **AC-02**：`harness update` 二次执行时，若项目描述文件无变化，profile 的 hash 不变；若有变化，stderr 提示"project-profile 已刷新（hash 漂移）"
- **AC-03**：本仓 `harness next --execute`（及 `ff --auto` / regression 派发）打印的 subagent briefing 含 `task_context_index` 字段，非空时每条形如 `{path}: {reason}`，条数 ≤ 8
- **AC-04**：subagent 按索引加载失败（路径不存在）时不报错，回退到 `.workflow/context/index.md` 全量路径（C2 建议清单语义）
- **AC-05**：CLAUDE.md / AGENTS.md 若用户已自定义（hash 非默认模板 hash），`harness update` 跳过覆盖并 stderr 提示（沿用 req-31（批量建议合集（20条））sug-14）
- **AC-06**：新增 / 修改代码覆盖率 ≥ 单元测试红绿各一轮（TDD），无回归；`harness validate --contract all` 得绿
- **AC-07**：每次 `harness next --execute` / `ff --auto` / regression 派发后，`.workflow/state/sessions/{req-id}/task-context/{stage}-{seq}.md` 落盘；frontmatter 至少含 `req_id` / `stage` / `ts` / `index_count` 字段；正文每行等价 briefing 内 `task_context_index` 条目；归档（`harness archive`）时该目录随 req 迁入 `artifacts/.../sessions/`（沿用既有归档路径，无需新迁移代码）

## 6. Risks

- **R1 索引 backfire**：CTO 塞过多索引反致 briefing 膨胀 → 每条索引带理由 + 硬上限 8 条，CLI 校验超限即截断并 warn
- **R2 profile 漂移**：技术栈演进后 profile 失效 → 每次 update 重扫对比 hash，差异时 stderr 提示已刷新
- **R3 用户自定义被覆盖**：复用 req-31（批量建议合集（20条））chg-03（用户自定义保护落地）sug-14 `_is_user_authored`；本 req 不新增保护机制

## 7. Split Rules

- 拟拆 2-3 个 chg（由架构师在 planning 阶段最终定）：
  - chg-01（项目描述扫描器 + project-profile 生成）：项目描述扫描器 + `project-profile.md` 生成（Part A 底座）
  - chg-02（harness update 集成扫描器 + hash 漂移检测）：`harness update` 集成扫描器 + hash 漂移检测 + AC-02/AC-05 兜底
  - chg-03（CTO 派发 briefing 增加 task_context_index）：harness-manager / CTO 派发 briefing 增加 `task_context_index` 字段 + subagent 按索引最小加载（Part B）
- 架构师有权调整拆分粒度；拆分原则：每个 chg 可独立交付 + 独立测试
- 需求完成时填 `completion.md` 并记录本仓 self-serve 启动验证
