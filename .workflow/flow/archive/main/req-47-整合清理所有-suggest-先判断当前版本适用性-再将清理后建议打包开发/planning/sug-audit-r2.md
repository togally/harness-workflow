# sug-audit-r2 — req-47 建议池复核（round 2，承接 req-46）

> 产出：analyst-L1（opus），planning stage Part B
> 来源：req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）
> 范围：req-46 audit 标 live 的 33 条 + req-46 done 阶段新沉淀的 6 条 = 39 条
> 校验语境：截至 a801820（done: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）testing + acceptance + done）
> 承接：`.workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/sug-audit.md`（45 条 round 1）

## 0. 复核方法

每条 sug 在 round-1 判定基础上，吸收 chg-01（机器型工件路径修复 + 防再犯 lint）+ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）+ acceptance/done 实战发现的 6 条新 sug 后**重新判定**：

1. 读 sug.md 内容（含 frontmatter）；
2. grep 当前 `src/harness_workflow/` + `.workflow/` + recent commits（chg-01 6406c40 / chg-02 171bac8 / done a801820）核对核心断言是否仍真；
3. 比对 round-1 主题簇（C-1 ~ C-10）+ 新 sug 归簇决定；
4. 出结论：**live**（仍未落地，待入 chg）/ **stale**（语义已被覆盖需出池）/ **applied-out**（已落地需出池）/ **dup-of**（合并到主线）/ **merge-into-chg-N**（继承 round-1 簇标识）。

> D-1 = A 已锁定：本表**不**复核 round-1 已结案 11 条（sug-09 / -12 / -17 / -25 / -32 / -40 / -44 / -45 / -46 / -49 / -50），仅在尾部"清理执行清单"对池清理动作做物理处理。

## 1. 复核全量表（39 条）

> 列说明：r2 判定 = 本轮判定；r1 判定 = round-1 audit 行号引用；增量校准依据 = chg-01 / chg-02 落地点 / 新 sug 关联。

### 1.1 已 round-1 判 live、本轮复核维持 live（待入 chg-N）

| sug-id | r1 判定 | r2 判定 | 主题簇 | r2 增量校准依据 | 归簇 chg |
|--------|--------|--------|-------|----------------|---------|
| sug-08（migrate 散落 .md + 同 id 冲突） | live | **live** | C-3 | round-1 后无新落地；migrate_requirements._process_source 仍只处理 dir | chg-3-cli-suggest-rename-fix |
| sug-10（install --check 对齐 update --check） | live | **live** | C-8 | round-1 后无新落地；install 仍无 --check | chg-8-install-update 体验顺修 |
| sug-11（requirement_review 路径存在性自检） | live | **live** | C-5 | analyst.md 仍仅 harness validate --human-docs；裸 ls 未做 | chg-5-契约-lint |
| sug-13（runtime ↔ req yaml stage 同步） | live | **live** | C-9 | _sync_stage_to_state_yaml 在 next 接通；enter / archive 路径未全覆盖 | chg-9-runtime-state-sync |
| sug-14（archive --yes / -y flag） | live | **live** | C-10 | 体验类小修，未改 | chg-10-杂项小修（或合 chg-8） |
| sug-15（update 检测 scaffold_v2 mirror diff 自动同步或告警） | live | **live** | C-4 | 与 sug-21 共因；test_scaffold_v2_mirror_matches_roles 仍仅守 base/stage 两文件 | chg-4-scaffold-mirror |
| sug-16（session start 强制 confirm E 原则） | live | **live** | C-5 | base-role 硬门禁四已写"按默认推进"，但 confirm E 自检未明示 | chg-5-契约-lint（或裁去并入 chg-7 testing 红线） |
| sug-18（Level-2 opus subagent 派发硬门禁） | live | **live** | C-5 | role-model-map.yaml + harness-manager.md 已对齐；lint 阻断未实现 | chg-5-契约-lint |
| sug-19（rename --dry-run + 文档反向引用更新） | live | **live** | C-3 | req-44 chg-02 修了 runtime / .workflow/flow/ 同步；--dry-run 与反向引用仍未做 | chg-3-cli-suggest-rename-fix |
| sug-20（tools/harness_update.py alias 化） | live | **live** | C-8 | helper 双入口仍存；req-33 chg-01 已落兼容层但未 alias 化 | chg-8-install-update 体验顺修 |
| sug-21（scaffold_v2 ~10 文件历史漂移批量修复） | live | **live** | C-4 | mirror diff 实战发现新增 sug-56（usage-reporter.md drift），实证 sug-21 持续真问题 | chg-4-scaffold-mirror |
| sug-22（requirement.md 裸 id lint） | live | **live** | C-5 | 契约 7 + 硬门禁六文字契约已立；validate_contract.py 部分 lint 已落但 requirement.md 首次裸 id 阻断未做 | chg-5-契约-lint |
| sug-23（硬门禁六 lint 自动 grep） | live | **live** | C-5 | 与 sug-22 同 lint 工具骨架；CI / pre-commit hook 仍缺 | chg-5-契约-lint |
| sug-24（install 卡顿体验） | live | **live** | C-8 | 体验类，profiling 未做 | chg-8-install-update 体验顺修 |
| sug-26（next/archive 联动 stage_timestamps + stage） | live | **live** | C-9 | archive 路径仍未联动 stage 字段写回 | chg-9-runtime-state-sync |
| sug-27（render_work_item_id 全 stdout 路径审计） | live | **live** | C-5 | 部分 CLI 用 helper；status / next / archive / suggest --list stdout 仍有裸 id | chg-5-契约-lint |
| sug-28（done_efficiency_aggregate 接受 str root） | live | **live** | C-10 | 单点小修未做 | chg-10-杂项小修 |
| sug-29（bugfix archive + suggestion archive 同步方向 C） | live | **live** | C-6 | bugfix-6 部分覆盖；bugfix-1~5 历史 + suggestion archive 仍未统一 | chg-6-archive-路径统一 |
| sug-30（bugfix 工件回 .workflow/flow/bugfixes/） | live | **live** | C-6 | repository-layout §3.2 已立；CLI 落位 + reviewer checklist 抽样仍欠 | chg-6-archive-路径统一 |
| sug-31（done 后 commit + revert dry-run 自动化） | live | **live** | C-7 | testing 阶段已有 revert 抽样（testing.md §R1 越界 / revert 抽样），但 done 阶段自动化未做 | **chg-7-testing-红线**（同根因合并） |
| sug-33（briefing 话术 lint 拦 testing over-instructing） | live | **live** | C-5 | bugfix-6 B6 降级；validate_contract.py 待扩规则 4 | chg-5-契约-lint |
| sug-34（migrate_bugfix_layout 覆盖 acceptance/） | live | **live** | C-6 | helper 仍只覆盖 5 类主文件 | chg-6-archive-路径统一 |
| sug-36（legacy archive 双源整合 + harness migrate archive） | live | **live** | C-6 | CLI stdout 多次提示但未实现 | chg-6-archive-路径统一 |
| sug-37（harness enter 同步 runtime stage 到目标 req） | live | **live** | C-9 | bugfix-6 archive 后 enter req-43 实证；helpers enter 路径不读 state yaml | chg-9-runtime-state-sync |
| sug-41（duration 口径 = subagent 工作时间不含人类等待） | live | **live** | C-2 | 依赖 sug-39 接通；req-46 交付总结已显证（duration = entries 累加，不是 stage 跨度）| chg-2-usage-log-runtime-接通（chg-2 内子项）|
| sug-42（tokens 真实计算方案 + 下游消费） | live | **live** | C-2 | 依赖 sug-39 接通；req-46 交付总结已实证 input/output/cache_* 全 0；fallback 待补 | chg-2-usage-log-runtime-接通（chg-2 内子项）|
| sug-47（change.md §3 Requirement 字段裸 id F-01 followup） | live | **live** | C-5 | 模板字段；契约 7 反向豁免补丁未加 | chg-5-契约-lint |
| sug-48（rename runtime 同步未来扩字段提醒 F-02 followup） | live | **live** | C-3 | workflow_helpers.py 注释 + schema 文档化未做 | chg-3-cli-suggest-rename-fix |

**小计**：28 条维持 live。

### 1.2 已 round-1 判 live，本轮**升 P0** + 显证（重点关注）

| sug-id | r1 判定 | r2 判定 | 主题簇 | r2 增量校准依据（实战显证）| 归簇 chg |
|--------|--------|--------|-------|------------------------------|---------|
| sug-39（chg-01 派发钩子真实接通 record_subagent_usage） | live（升 P0）| **live**（已 P0）| C-2 | req-46 交付总结 §效率与成本实证：input/output/cache_read/cache_creation 全 0，total_tokens 单字段有效 = 钩子未真接通；usage-log.yaml 9 entries 有数据但 token payload 丢失 | chg-2-usage-log-runtime-接通（前置依赖最高优）|
| sug-38（next verdict stage work-done gate） | applied-partial（dogfood 复验前）| **applied-out**（chg-02 已落地真修 + 子进程 dogfood）| C-1 | chg-02 commit 171bac8 已落 _is_stage_work_done executing 严格化（grep workflow_helpers.py 7438-7460 = 双 gate + 严格化）+ tests/test_workflow_next_subprocess.py 4 路径 = round-2 确认已 fix | **出池 archive**（chg-02 已 archive sug-46/-50；sug-38 主线本轮 archive） |
| sug-51（testing git restore 事故 + tmpdir 红线）| live（P0）| **live**（已 P0）| C-7 | testing.md 已有"子进程 dogfood 红线"（chg-02 落地）但**没有**"任何破坏性 git 命令一律禁止 + dogfood 必须 tmpdir mock"红线，也没有 testing-no-destructive-git lint；本 sug 真正核心仍未做 | **chg-7-testing-红线**（首批必含）|
| sug-52（dogfood 实跑流程模板）| live | **live** | C-7 | testing.md §子进程 dogfood 红线（chg-02 落地）已含部分模板（4 路径 fixture / wrapper），但 plan.md §测试用例设计 dogfood TC 必填字段 + testing.md 经验沉淀完整模板未做 | **chg-7-testing-红线**（合并 sug-51）|
| sug-53（usage-log 缺失三次实证 — 升 sug-39 P0 凭证）| live（partial archived）| **live（partial）**| C-2 | frontmatter 含 partial_promoted_to_chg: chg-02 + partial_archive_note；剩余主因（sug-39 钩子未接通）未落地 = 仍 live；req-46 done 实证 token 全 0 = 三次实证升四次 | chg-2-usage-log-runtime-接通（partial 部分留存至 chg-2 落地）|

**小计**：5 条；其中 sug-38 转 **applied-out 出池**，sug-39 / -51 / -52 / -53 维持 live（高优）。

### 1.3 round-1 后**新沉淀** 6 条（首次复核）

| sug-id | r2 判定 | 主题簇 | r2 校准依据 | 归簇 chg |
|--------|--------|-------|-------------|---------|
| sug-54（executing role briefing 应规定 ✅ marker）| **live** | C-5（契约 lint 簇）| chg-01 executing 现场 work-done gate 期望 ✅，executing role 用 [x] 导致两次 next 误判；属契约文字契约缺口 | **chg-5-契约-lint**（marker 自检条文）或独立小 chg；本轮归 chg-5 |
| sug-55（chg-02 部署同步契约 dev mode flag HARNESS_DEV_MODE=1）| **live** | 跨 C-2/C-7 | chg-02 R2 风险条款已声明开发态 pipx 重装 friction；env flag 未实现；与 testing 流程紧密相关 | **跨簇 default-pick = chg-7-testing-红线**（同样关注 testing 阶段开发态友好；与 chg-2 数据底座非强耦合，归 chg-7 简化依赖图）|
| sug-56（scaffold_v2 usage-reporter.md 漂移）| **live**（dup-of sug-21 子集）| C-4 | sug-21（mirror 漂移）的具体子项；本身实证 sug-21 真存在；归 sug-21 主线即可 | **chg-4-scaffold-mirror**（dup-of sug-21 子集，归簇时一并扫除）|
| sug-57（sug 模板补 partial_* 三字段语义化）| **live** | C-5（契约 lint 簇）| req-46 acceptance 引入 partial_promoted_to_chg / partial_archived_at / partial_archive_note 三字段，契约 6 仅列 5 必填字段；扩展字段白名单 + lint 校验缺 | **chg-5-契约-lint** |
| sug-58（下个 req 优先 chg-7 testing 红线 — high）| **live**（已拍板 D-7 = A 必含）| C-7 | req-46 交付总结明确"下个 req 优先承接 chg-7"；本 req 即"下个 req"；D-4 / D-7 已锁定首批必含 | **chg-7-testing-红线**（首批必含主线 sug 之一）|
| sug-59（done_efficiency_aggregate 路径漂移 — high）| **live** | C-2 | req-46 done 实证：record_subagent_usage 写 .workflow/state/sessions/，done_efficiency_aggregate 读 .workflow/flow/requirements/；写读路径不一致；与 sug-39 钩子接通是同根因不同维度 | **chg-2-usage-log-runtime-接通**（与 sug-39 主线合并，同 chg 内一次性修写读路径）|

**小计**：6 条；全部 live；其中 sug-58 / sug-59 标 P0/high。

### 1.4 round-1 后被 chg-01 / chg-02 顺手覆盖 / 翻转（独立列出）

| sug-id | r1 判定 | r2 判定 | 主题簇 | 翻转依据 | 后续动作 |
|--------|--------|--------|-------|---------|---------|
| sug-35（reviewer checklist 扩 artifact-placement / test-case-design）| live | **applied-out** | C-5 | chg-01 落地已加 reviewer checklist 反向抽样条目（applied_by_chg: chg-01）；frontmatter 已 archived 但 live 目录残留 | **池清理**（移到 archive/）|
| sug-46（sug-38 升 P0：req-44 二次实证）| applied-out | **applied-out** | C-1 | chg-02 落地真修 + sug-46 frontmatter 已 archived（applied_at: 2026-04-28）；live + archive 各一份 = 双份残留 | **池清理**（删 live 副本，保留 archive）|
| sug-50（chg-01 gate gap 实为部署 gap）| applied-out | **applied-out** | C-1 | chg-02 真修 + sug-50 frontmatter 已 archived；live 残留 | **池清理**（移到 archive/）|

**小计**：3 条已 applied-out 但 live 残留（池清理动作）。

### 1.5 sug-25 翻转滞留（D-6 = B 独立快速出池）

| sug-id | r1 判定 | r2 判定 | 翻转依据 | 后续动作 |
|--------|--------|--------|---------|---------|
| sug-25（record_subagent_usage 派发链路接通）| applied-out（round-1 已结案）| **applied-out**（D-1 = A 不重判）| frontmatter status: applied + applied_by 已填（req-43 chg-01）；live 残留 | **池清理**（移到 archive/，D-6 = B 独立快速出池，不算复核工作）|

**小计**：1 条。

---

## 2. 复核结果汇总（39 条全量）

| 判定 | 数量 | 占比 |
|-----|-----|-----|
| **live**（待入 chg）| **34** | 87% |
| **applied-out**（已落地需出池）| **4** | 10%（sug-35 / sug-38 / sug-46 / sug-50；sug-25 计入 1.5 翻转滞留单独处理）|
| **stale**（已被覆盖需出池）| **0** | — |
| **dup-of**（合并主线）| **1** | 3%（sug-56 dup-of sug-21 子集，仍计 live 但归 sug-21 主线归簇）|

> 与 round-1 差异：
> - sug-38 由 applied-partial → applied-out（chg-02 已 dogfood 复验，无需保留 live）；
> - sug-35 由 live → applied-out（chg-01 已落 reviewer checklist）；
> - sug-39 由 live → live (P0)（升 P0 已在 round-1 完成；本轮再次实证 token 全 0）；
> - 6 条新 sug 全部纳入归簇；
> - 0 条 stale —— round-1 已把 5 条 stale（sug-09 / sug-12 / sug-17 / sug-32 / sug-40）结案，本轮范围内无新 stale。

---

## 3. 归簇分布（10 簇 + 新增动议）

| 簇 | round-1 sug | round-2 新增 sug | 本轮 chg 编号（与 req-46 roadmap 同步）|
|---|------------|------------------|-------------------------------------|
| **C-1**（over-chain）| sug-38（applied-out 出池）| — | chg-1（已落地 chg-02，本 req 仅做池清理；不再开新 chg）|
| **C-2**（usage-log 派发链路）| sug-39 / sug-41 / sug-42 / sug-53 | sug-59 | **chg-2**（usage-log runtime 接通 + 写读路径修复，含 sug-59）|
| **C-3**（apply / rename / suggest CLI bug）| sug-08 / sug-19 / sug-48 | — | **chg-3**（CLI 顺修；sug-44 / sug-45 / sug-49 已 round-1 applied-out）|
| **C-4**（scaffold_v2 mirror 漂移）| sug-15 / sug-21 | sug-56（dup-of sug-21 子集）| **chg-4**（mirror 修复，含 sug-56 子项）|
| **C-5**（契约硬门禁 lint）| sug-11 / sug-16 / sug-18 / sug-22 / sug-23 / sug-27 / sug-33 / sug-47 | sug-54（marker 契约）/ sug-57（partial_* 字段语义化）| **chg-5**（契约 lint 套件，含 sug-54 / sug-57）；sug-35 已 applied-out |
| **C-6**（archive 路径关注点分离）| sug-29 / sug-30 / sug-34 / sug-36 | — | **chg-6**（archive 路径统一）|
| **C-7**（testing 安全 + dogfood 协议）| sug-31 / sug-51 / sug-52 | sug-55（dev mode flag）/ sug-58（首批必含主线）| **chg-7**（testing 红线，含 sug-31 / -51 / -52 / -55 / -58 = 5 条）|
| **C-8**（install / update CLI 体验）| sug-10 / sug-20 / sug-24 | — | **chg-8**（install/update 体验，含 sug-14 archive --yes，与 chg-10 杂项合并）|
| **C-9**（runtime / enter / archive 状态同步）| sug-13 / sug-26 / sug-37 | — | **chg-9**（runtime sync）|
| **C-10**（杂项与小修）| sug-14 / sug-28 | — | **chg-10**（杂项；sug-14 已挪 chg-8 / sug-28 single-point；可考虑合 chg-3 或独立）|

> sug-46 / sug-50 / sug-25 翻转滞留 → 池清理动作不归任何 chg。
> sug-35 已 applied-out（chg-01 已吸收）→ 池清理动作。

---

## 4. 池清理执行清单（AC-02 落地数据）

> D-5 = A（archive）+ D-6 = B（独立快速出池）锁定。

### 4.1 翻转滞留 + 双份残留（独立快速出池，D-6）

| sug-id | 现状 | 动作 | 验证命令 |
|--------|------|------|----------|
| sug-25 | live 副本 + frontmatter `status: applied` | `mv` live 副本到 `archive/`（不删 frontmatter，applied_by 保留）| `ls .workflow/flow/suggestions/sug-25-*` 应不存在；`ls .workflow/flow/suggestions/archive/sug-25-*` 应存在 |
| sug-35 | live 副本 + frontmatter `status: archived` + `applied_by_chg: chg-01` | `mv` live 副本到 `archive/` | `ls .workflow/flow/suggestions/sug-35-*` 应不存在 |
| sug-46 | **双份残留**：live + archive 各一份；live frontmatter `status: archived` + `applied_at: 2026-04-28` + `linked_regression: reg-02` + `promoted_to_chg: chg-02`；archive 副本 frontmatter `status: applied`（旧版本）| 删除 live 副本（保留 archive 副本，但 archive 副本 frontmatter `status: applied` 应同步更新为 `archived` 以匹配语义；或保留旧版本作 round-1 applied 留痕）—— **default-pick = 删除 live + 保留 archive 现状**（archive 副本 status: applied 是 round-1 applied 历史，sug-46 round-2 真正 archive 由 chg-02 acceptance 后翻转，linked_regression / promoted_to_chg 在 live 副本完整，删 live 直接出池语义正确）| `ls .workflow/flow/suggestions/sug-46-*` 应不存在；`ls .workflow/flow/suggestions/archive/sug-46-*` 应存在 |
| sug-50 | live 副本 + frontmatter `status: archived` + `applied_at: 2026-04-28` + `linked_regression: reg-02` + `promoted_to_chg: chg-02` | `mv` live 副本到 `archive/` | `ls .workflow/flow/suggestions/sug-50-*` 应不存在 |

**小计**：4 条物理动作（3 mv + 1 delete）。

### 4.2 新判 applied-out（chg-01 / chg-02 已吸收）

| sug-id | 现状 | 动作 | 验证 |
|--------|------|------|------|
| sug-38（next verdict gate）| live；frontmatter `status: pending` `priority: high`；sug-46 / -50 已 promoted 到 chg-02 acceptance archived | 翻 frontmatter `status: archived` + 加 `applied_by_chg: chg-02` + 加 `applied_at: 2026-04-28` → `mv` 到 `archive/` | `ls .workflow/flow/suggestions/sug-38-*` 不存在 |

**小计**：1 条 frontmatter 翻转 + 物理 archive。

### 4.3 partial archive（保留 partial 字段，主因留 pending）

| sug-id | 现状 | 动作 | 验证 |
|--------|------|------|------|
| sug-53（usage-log 缺失）| live；frontmatter 含 `partial_promoted_to_chg: chg-02` + `partial_archived_at: 2026-04-28` + `partial_archive_note: ...` | **保留 live**（主因 sug-39 钩子未接通仍 live；over-chain 副作用部分已通过 partial_* 字段标识 archived）；不动 | live 副本仍存在；保留至 chg-2-usage-log 落地后正式 archive |

**小计**：0 条物理动作（保留 partial 状态）。

### 4.4 池容量数字

| 阶段 | live 池 | archive 池 | total |
|------|--------|-----------|------|
| **本 stage 入口（req-47 接手时）**| 51 | 9 | 60 |
| **本 stage 出口（4.1 + 4.2 执行后）**| 51 - 5 = **46** | 9 + 4 = **13**（sug-46 双份合并不增加 archive 数）| 59 |
| **首批 chg-7 落地后（≥ 5 条 sug 出池）**| 46 - 5 = **41** | 13 + 5 = **18** | 59 |

> live 池减少 5 条（sug-25 / sug-35 / sug-46 删 live / sug-50 / sug-38）；archive 池实际增加 4 条（sug-46 已有同 id，仅 mv 不重复）。
> 首批 chg-7 落地后预期出池 5 条（sug-31 / sug-51 / sug-52 / sug-55 / sug-58）—— 详细见 chg-7 落地后 acceptance 清池。

---

## 5. round-2 default-pick 决策清单

> 承接 round-1 D-1 ~ D-10 + req-47 req_review D-1 ~ D-11；本 stage planning Part B 新增决策。

| 决策点 | 选项 | default-pick | 理由 |
|-------|-----|-------------|-----|
| **D-r2-1（sug-38 archive 时机）**| A. 立即 archive（chg-02 已落地）/ B. 等用户拍板 chg-7 后 | **A** | chg-02 已 acceptance PASS + done；sug-38 主线已被 sug-46/-50 archive 间接覆盖；保留 live 无价值 |
| **D-r2-2（sug-56 是否独立处理）**| A. dup-of sug-21（一同进 chg-4）/ B. 独立 chg | **A** | 单点子项，sug-21 主线归 chg-4，归 sug-21 子项最自然；不增加 chg 数 |
| **D-r2-3（sug-55 dev mode flag 归簇）**| A. chg-2（与 deploy 契约同主题）/ B. chg-7（与 testing dogfood 同 stage）/ C. 独立小 chg | **B**（chg-7）| sug-55 关切是"开发态 testing/部署阶段 friction"，本质属 testing 阶段红线 + dogfood 协议子集；归 chg-7 简化依赖图；与 chg-2 数据底座非强耦合 |
| **D-r2-4（sug-54 marker 契约归簇）**| A. chg-5（契约 lint）/ B. chg-7（testing 红线）/ C. 独立 | **A**（chg-5）| sug-54 属 executing role briefing 文字契约 + work-done gate marker 兼容性；归 chg-5 契约 lint 套件最自然 |
| **D-r2-5（sug-57 partial_* 字段语义化归簇）**| A. chg-5（契约 lint）/ B. 独立 | **A**（chg-5）| sug 模板字段属契约 6 扩展，归 chg-5 |
| **D-r2-6（sug-46 双份残留处理）**| A. 删 live 留 archive 现状（旧 status: applied）/ B. 删 live + 同步更新 archive frontmatter 到 round-2 字段 | **A**（删 live 留 archive 现状）| archive 副本 status: applied 是 round-1 applied 留痕，sug-46 真正 round-2 archive 由 live 副本承载（含 linked_regression / promoted_to_chg 完整字段）；删 live 副本即可（live 副本是物理冗余）；archive 副本旧 status 留作历史归档语义 |
| **D-r2-7（partial archive 是否扩 sug 池语义）**| A. 沿用 sug-53 partial_* 字段（待 chg-5 lint 化）/ B. 改强归 archived | **A**（partial）| sug-53 over-chain 副作用部分确属 archived 语义，主因（sug-39 钩子）未接通；partial_* 字段已表达精确语义；改强归 archived 会失主因追溯；sug-57 已捕捉此模式扩契约 6 |
| **D-r2-8（chg-7 范围是否含 sug-58 自承接 marker）**| A. chg-7 acceptance PASS 后自动 archive sug-58 / B. 不动（sug-58 内容已被 chg-7 实现完成自然 obsolete）| **A** | sug-58 是承接 marker，chg-7 acceptance PASS = 承接完成；自动 archive 保持池清洁 |

---

## 6. 待处理捕获问题

- **sug-46 archive 副本 frontmatter 不一致**：archive 副本旧 `status: applied`（round-1 applied 留痕）vs live 副本 `status: archived`（round-2 chg-02 落地）；D-r2-6 选 A 保留现状，但语义略乱。**建议**：chg-5（契约 lint 套件）落地时加一条"archive/ 下 sug 文件 frontmatter status 不一致 lint"；本 req 不阻塞。
- **partial_* 字段尚无 lint 校验**：sug-53 / sug-57 共同信号；chg-5 契约 lint 套件需含 partial_* 字段名拼写校验 + 含义文档化（写到契约 6）；本 req chg-5 不在首批，留 roadmap-r2 §5 留尾说明。
- **chg-7 范围细节**（sug-31 / -51 / -52 / -55 / -58 五合一）：粒度大，可能 chg-7a / chg-7b 二次拆分；保留给 chg-7 plan.md §3 处理（plan.md 不再二次拆 chg，仅描述执行顺序）。
- **chg-2 / chg-9 顺序**（sug-59 写读路径漂移 vs sug-39 钩子接通）：两 sug 同 chg-2 内子项，chg-2 plan.md 拆 step 时需要明确顺序（先修写读路径让数据可读 → 再修钩子让数据更全）；本 req chg-2 不在首批，留下个 req 拍。

