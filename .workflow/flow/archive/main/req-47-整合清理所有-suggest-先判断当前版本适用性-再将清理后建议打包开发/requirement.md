# Requirement

## 1. Title

整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发

## 2. Goal

承接 req-46（建议池梳理验证 + 优先级 roadmap + 分批落地，已 done）的成果，针对当前 `.workflow/flow/suggestions/` 池继续推进"复核 → 清理 → 打包 → 落地"闭环：

- **复核当前版本适用性**：把 req-46 audit 表中标 live 的 31 条 + req-46 done 阶段新增的 6 条（sug-54 ~ sug-59）共 **37 条 sug**，吸收 chg-01（机器型工件路径修复 + 防再犯 lint）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）落地后的代码 / 文字契约现状，逐条重新判定 live / stale / applied-out / dup-of；并对池中 4 条已翻 frontmatter（sug-25 applied / sug-35 archived / sug-46 archived / sug-50 archived）但仍残留 live 目录的"翻转滞留"做出池处理；
- **整合清理出池**：对复核后 stale / applied-out / dup-of 的 sug，按契约 6 翻 frontmatter + 物理移到 archive/，让池容量回到"pending = 待办"的语义；
- **将清理后建议打包开发**：以 req-46 roadmap 剩余 8 chg（chg-3 / chg-4 / chg-5 / chg-6 / chg-7 / chg-8 / chg-9 / chg-10）为基础底盘，结合复核后存活的 sug + 6 条新增 sug（sug-54 ~ sug-59）做增量校准（合并 / 拆分 / 新增 chg），形成本 req 周期的"打包开发批次"；
- **首批落地 + 留尾承接**：本 req 周期不强求把所有存活 sug 一次性打完；按"首批 K 个 chg 落地 + 其余留 roadmap 给下个 req"模式，与 req-46 同节奏，避免单 req 过载。

核心问题：
- req-46 成果是"分析 + 首批 2 chg"，**剩余 8 chg / 31 条 pending sug 未落地**，roadmap 优先级与依赖关系仍有效，但已过 chg-01 / chg-02 落地节点，部分 sug 需要重新校准（特别是 over-chain 簇 / usage-log 簇 / 路径修复簇等已被 chg-01 / chg-02 部分吸收的部分）；
- 池中 sug-54 ~ sug-59 是 req-46 done 阶段新沉淀的"实战副产物"，**未进入 req-46 roadmap**，需要本 req 决定纳入哪个 chg；
- sug-58（下个 req 优先 chg-7 testing 红线，high）在 req-46 交付总结中明确标注"下个 req 优先承接"，本 req 必须就此给出明确决策；
- 池中 sug-25 / sug-35 / sug-46 / sug-50 翻转滞留（frontmatter 已是 applied/archived 但 live 目录仍有副本），违反 sug 池语义，需要顺手清理。

## 3. Scope

### 3.1 In Scope

**A. 复核范围**：
- req-46 audit 标 live 的 31 条 sug：sug-08 / sug-10 / sug-11 / sug-13 / sug-14 / sug-15 / sug-16 / sug-18 / sug-19 / sug-20 / sug-21 / sug-22 / sug-23 / sug-24 / sug-26 / sug-27 / sug-28 / sug-29 / sug-30 / sug-31 / sug-33 / sug-34 / sug-36 / sug-37 / sug-38 / sug-39 / sug-41 / sug-42 / sug-47 / sug-48 / sug-51 / sug-52 / sug-53（实际 33 条；以池现存为准复核）
- req-46 done 新沉淀的 6 条：sug-54（executing role briefing ✅ marker）/ sug-55（chg-02 deploy 契约 dev mode flag）/ sug-56（scaffold_v2 usage-reporter.md 漂移）/ sug-57（sug 模板 partial 字段语义化）/ sug-58（下个 req 优先 chg-7 testing 红线，high）/ sug-59（done_efficiency_aggregate 路径漂移，high）
- 池中 4 条 frontmatter 已翻但 live 目录残留的 sug：sug-25 / sug-35 / sug-46 / sug-50（仅做出池物理动作，不重判状态）

**B. 整合清理动作**：
- 复核出 stale / applied-out / dup-of 的 sug → 翻 frontmatter status（pending → archived / applied）+ 用 `harness suggest --archive` / `--delete` 物理移出 live 目录
- 翻转滞留的 4 条 sug → 直接物理移到 `.workflow/flow/suggestions/archive/`，无需重判
- sug-46 双份残留（live + archive 各一份）→ 删除 live 副本

**C. 打包开发**（从 chg 拆分到首批落地）：
- 以 req-46 roadmap.md §2 的 8 个剩余 chg（chg-3 ~ chg-10）为底盘，结合复核结果做**增量校准**（含 6 条新增 sug 的归簇）
- 排出本 req 的"首批 K 个 chg"（推荐 P0 / 数据安全 优先：chg-7 testing 红线 + chg-2 usage-log runtime + chg-9 runtime sync 是候选）
- 首批 chg 走完整 planning → executing → testing → acceptance → done 路径
- 其余 chg 留给后续 req 周期承接（在本 req 的 roadmap 中明确标注"留尾"）

### 3.2 Out Scope

- **本 req 周期之后新增的 sug**（如 sug-60+）不纳入本 req 范围，避免无限滚动（与 req-46 §3.2 同款约束）
- **roadmap 剩余 8 chg 全部落地**：体量过大（合计 3 大 / 5 中 / 2 小，~600~1500k token），单 req 不可能完成；本 req 只承接首批
- **跨 repo 影响**（如 Yh-platform）：仅在本仓库 .workflow/context/ + scaffold_v2 mirror 同步范围内处理
- **bugfix 周期触发的 hot fix**（如新发现 P0 bug 走 harness bugfix 路径）：不挪进本 req 的批次
- **sug.md frontmatter 优先级回填**：避免 sug 文件 churn，复核后的优先级仅落本 req 的 audit / roadmap，不动 sug 文件本身（与 req-46 同款约束）
- **req-46 audit 已标 stale / applied-out / dup-of 的 11 条 sug 重审**：sug-09 / sug-12 / sug-17 / sug-25 / sug-32 / sug-40 / sug-44 / sug-45 / sug-46 / sug-49 / sug-50（D-1 = A 已确定，本 req 仅做出池物理动作不重判）

## 4. Acceptance Criteria

- **AC-01：复核完整性** — 产出 `sug-audit-r2.md`（r2 = round 2，承接 req-46 sug-audit），覆盖 33 条 live + 6 条新增 = 39 条 sug 全量复核结论（live / stale / applied-out / dup-of / merge-into-chg-N），每条有依据（引用 chg-01 / chg-02 落地点 / 代码行号 / commit sha / req-46 audit 行号），无"待评估"占位。

- **AC-02：清理动作落地** — 池清理执行清单产出，包含两类动作：
  - 翻转滞留 4 条（sug-25 / sug-35 / sug-46 / sug-50）+ sug-46 双份残留 → 物理出池（移到 archive/，删除 live 目录副本）
  - 复核新判 stale / applied-out / dup-of 的 sug → 翻 frontmatter + archive
  - 清理后池容量数字明确（预期 51 → ≤ 25）

- **AC-03：打包开发批次** — 产出 `roadmap-r2.md`，含：
  - req-46 roadmap 剩余 8 chg 的现状校准（哪些 chg 因 chg-01 / chg-02 已变化、哪些 sug 已被吸收）
  - 6 条新增 sug 的归簇决定（进哪个既有 chg / 新设 chg / 不进 chg 直接 archive）
  - 首批 chg 推荐（≥ 1 个，≤ 3 个）+ 推荐理由 + 依赖图
  - 留尾说明：本 req 不落的 chg 列出 + 给下个 req 的承接建议

- **AC-04：首批 chg 落地完成** — 用户对首批 chg 范围拍板后，主 agent 用 `harness change` 创建 chg 工件，走完整 planning → executing → testing → acceptance → done 流程；首批所有 chg 的 AC 全 PASS。

- **AC-05：硬门禁与契约** — 本 req 周期所有产出（`requirement.md` / `sug-audit-r2.md` / `roadmap-r2.md` / `change.md` × N / `plan.md` × N）落位见 `.workflow/flow/repository-layout.md` §3（机器型必落 `.workflow/flow/requirements/req-47-{slug}/`）；`harness validate --human-docs` exit 0 + `harness validate --contract artifact-placement` exit 0 在每 stage 流转前均通过；契约 7（id+title 首次引用）+ 硬门禁六（对人汇报 ≤ 15 字描述）+ 硬门禁七（周转汇报不列选项）全周期遵守。

## 5. Split Rules

本 req 的 chg 拆分以 req-46 roadmap.md §2 的 10 簇结构为底盘，做增量校准；新 chg 命名沿用 req-46 簇编号（chg-3 ~ chg-10）+ 新增 chg（如有）按 CLI 实分配序号。

粒度规则（继承 req-46 §5）：
- **同根因** sug 必须合并到一个 chg（如 testing 红线簇 sug-51 / sug-52 / sug-58 / sug-31 进 chg-7）
- **同代码触点** sug 优先合并（如 apply / rename / suggest CLI 在同 helper 文件，进 chg-3）
- **数据底座 / 行为底座** chg 优先级最高（chg-2 usage-log runtime + sug-59 路径漂移合并）
- **契约硬化 lint** 集中到一个 chg（chg-5），避免 lint 工具骨架重复实现
- **新增 sug 归簇**（sug-54 ~ sug-59）按主题落入既有 chg 或新设 chg
- **首批控制**：本 req 首批 chg 数 ≤ 3（与 req-46 同上限），保证单 req 周期可控
- **留尾**：本 req 不落的 chg 在 `roadmap-r2.md` 中明确给下个 req 的承接建议

完整 chg 拆分见 `.workflow/flow/requirements/req-47-整合清理所有-suggest-先判断当前版本适用性-再将清理后建议打包开发/planning/roadmap-r2.md`（planning stage 产出）。
