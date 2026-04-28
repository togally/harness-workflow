# sug-audit — req-46 建议池梳理验证

> 产出：analyst-L1（opus），requirement_review stage
> 来源：req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）
> 范围：sug-08 ~ sug-53（编号有跳号；sug-43 已转 req-43；sug-46 已 archive）
> 校验语境：截至 d8237fe（archive: req-45（harness next over-chain bug 修复（紧急）） + sug 池积累）

## 校验方法

每条 sug 走以下流程判定：
1. 读 sug.md 内容（含 frontmatter）；
2. grep 当前 src/harness_workflow/ 实现 + recent commits（git log）核对核心断言是否仍真；
3. 比对相关历史 req/chg/bugfix 归档，确认是否被顺手覆盖；
4. 出结论：**live** / **applied-out**（已落地需出池）/ **stale**（已被覆盖需出池）/ **dup-of**（合并到主 sug）。

## 主题簇定义（共 10 簇）

| 簇编号 | 簇名 | 主线 sug | 跟随 sug |
|-------|-----|---------|---------|
| C-1 | over-chain（harness next 越界连跳）| sug-38 | sug-09 / sug-12 / sug-26 / sug-40 / sug-46 / sug-50 |
| C-2 | usage-log 派发链路真接通 | sug-39 | sug-25(applied) / sug-41 / sug-42 / sug-53 |
| C-3 | apply / rename / suggest CLI bug | sug-44 | sug-19 / sug-45 / sug-47 / sug-48 / sug-49 |
| C-4 | scaffold_v2 mirror 漂移 + 自动同步 | sug-15 | sug-21 |
| C-5 | 契约硬门禁 lint（id+title / 路径自检 / 派发话术）| sug-22 | sug-11 / sug-23 / sug-27 / sug-33 / sug-35 |
| C-6 | archive 路径关注点分离 + 双源整合 | sug-30 | sug-29 / sug-34 / sug-36 |
| C-7 | testing 安全 + dogfood 协议 | sug-51 | sug-31 / sug-32 / sug-52 |
| C-8 | harness install / update CLI 体验 | sug-24 | sug-10 / sug-20 |
| C-9 | runtime / enter / archive 状态同步 | sug-37 | sug-13 / sug-26（=C-1 共享）|
| C-10 | 杂项与小修 | — | sug-08 / sug-14 / sug-16 / sug-17 / sug-18 / sug-28 |

> sug-26 同时属于 C-1（next 同步 stage_timestamps）与 C-9（runtime ↔ req yaml 同步），主归 C-9，C-1 协同。

---

## 全量 sug 验证表（45 条）

| sug-id | 创建日期 | 状态判定 | 主题簇 | P 评级 | 简短复现 / 覆盖 | 处理建议 |
|--------|---------|---------|-------|--------|----------------|---------|
| sug-08（migrate requirements 散落 .md + 同 id 冲突）| 2026-04-22 | **live** | C-3 | P2 | `migrate_requirements._process_source` 仅处理 dir，不处理散落 .md。grep 7536 附近代码现状一致 | 进 chg-3-cli-suggest-rename-fix 顺修 |
| sug-09（next acceptance→done 重试两次回退）| 2026-04-22 | **stale**（被 sug-50（gate gap）+ b64bcd7 覆盖语义）/ 或 **dup-of sug-38** | C-1 | P0 | 与 sug-12 / sug-38 / sug-46 / sug-50 同根 over-chain；req-45 chg-01 已修 gate 双插桩 | dup-of sug-38；归并到 chg-1 dogfood 复验后清出 |
| sug-10（install --check 对齐 update --check）| 2026-04-22 | **live** | C-8 | P2 | install 当前无 --check；update 有；与 chg-33 安装/更新职责合并相关 | 进 chg-8-install-update-体验顺修 |
| sug-11（requirement-review 路径存在性自检）| 2026-04-22 | **live** | C-5 | P1 | 当前 analyst.md 仅有 harness validate --human-docs；未对 requirement.md 引用路径做 ls 自检 | 进 chg-5-契约-lint 套件 |
| sug-12（next executing→testing 一次推两格）| 2026-04-22 | **stale**（同根 over-chain，req-45 chg-01 修复双 gate）| C-1 | P0 | 与 sug-09/-38 同根 | dup-of sug-38；并 chg-1 dogfood 复验后清出 |
| sug-13（runtime↔req yaml stage 同步）| 2026-04-22 | **live** | C-9 | P1 | sug-26 二次实证（req-38/40/41）；sug-37 三次实证（bugfix-6 → req-43 enter）；helpers `_sync_stage_to_state_yaml` 已在 next 路径接通但 enter / archive 路径未全覆盖 | 进 chg-9-runtime-state-sync |
| sug-14（archive --yes / -y flag）| 2026-04-22 | **live** | C-10 | P2 | grep code 未见 --yes 选项；体验类小修 | 进 chg-10-杂项小修 |
| sug-15（update 检测 scaffold_v2 mirror diff）| 2026-04-22 | **live** | C-4 | P1 | 与 sug-21 共同根因；现有 test_scaffold_v2_mirror_matches_roles 仅守 base/stage 两文件；其它 ~10 个文件历史漂移仍存在 | 进 chg-4-scaffold-mirror |
| sug-16（主 agent session start 强制 confirm E 原则）| 2026-04-22 | **live**（语义已被 req-31 chg-05 部分覆盖，但文字硬门禁仍有歧义空间）| C-5 | P2 | base-role.md 硬门禁四已写"按默认推进，不打断"；sug-16 担心反向理解；建议加一条 session-start 自检 | 进 chg-5-契约-lint 顺加 |
| sug-17（对人文档字数度量基线不可比）| 2026-04-22 | **stale**（req-31 chg-04 已废四类对人 brief，req-41 进一步精简；字数度量需求消失）| C-10 | P3 | req-31/41 已大改对人文档结构，旧度量上下文不复存在 | **出池**（建议 delete） |
| sug-18（Level-2 opus subagent 派发硬门禁）| 2026-04-22 | **live** | C-5 | P2 | role-model-map.yaml 已对齐 + harness-manager.md 已有派发说明；但"Sonnet subagent 内联跑 opus 角色"反模式无 lint 阻断 | 进 chg-5-契约-lint |
| sug-19（rename req --dry-run + 文档引用更新）| 2026-04-22 | **live** | C-3 | P2 | req-44 chg-02 rename 修了 runtime 三字段同步与 .workflow/flow/ 目录漏改；但 --dry-run / 文档反向引用更新仍未做 | 进 chg-3-cli-suggest-rename-fix |
| sug-20（tools/harness_update.py 退化为 install alias）| 2026-04-23 | **live** | C-8 | P3 | grep 显示当前仍保留 helper 双入口；req-33 chg-01 落地为兼容层 | 进 chg-8 顺修（小） |
| sug-21（scaffold_v2 ~10 文件历史漂移批量修复）| 2026-04-23 | **live** | C-4 | P1 | 与 sug-15 共因；live `.workflow/context/experience/` 与 mirror 不一致；测试只覆盖 base/stage | 进 chg-4-scaffold-mirror |
| sug-22（requirement.md 裸 id lint）| 2026-04-23 | **live** | C-5 | P1 | 契约 7 + 硬门禁六文字契约已立；validate_contract 已有部分 lint，但 requirement.md 首次引用裸 id 阻断 next 仍未实现 | 进 chg-5-契约-lint |
| sug-23（硬门禁六 lint 自动 grep）| 2026-04-23 | **live** | C-5 | P1 | 与 sug-22 同 lint 工具骨架；CI / pre-commit hook 待加 | 进 chg-5-契约-lint |
| sug-24（install 卡顿体验）| 2026-04-24 | **live** | C-8 | P3 | 体验类，profiling 待做；优先级低 | 进 chg-8 顺修 |
| sug-25（record_subagent_usage 派发链路真实接通）| 2026-04-25 | **applied-out**（status: applied，applied_by: req-43 chg-01）| C-2 | — | helper 已加 task_type 参数 + 文字契约；**但运行时链路仍未真接通**（usage-log.yaml 三连 req 缺失，由 sug-39 接续）| **出池**（archive：保留 applied 标记到归档）；后续工作转移到 sug-39 |
| sug-26（next/archive 联动写 stage_timestamps + stage）| 2026-04-25 | **live** | C-9（主） / C-1（协同）| P1 | 与 sug-13 / sug-37 共因；archive 路径未联动 | 进 chg-9-runtime-state-sync |
| sug-27（render_work_item_id 全 stdout 路径审计）| 2026-04-25 | **live** | C-5 | P2 | 部分 CLI 已用 helper；harness status / next / archive / suggest --list stdout 仍有裸 id 缺口 | 进 chg-5-契约-lint |
| sug-28（done_efficiency_aggregate 接受 str root）| 2026-04-25 | **live** | C-10 | P3 | 单点小修 | 进 chg-10-杂项小修 |
| sug-29（bugfix archive + suggestion archive 同步方向 C）| 2026-04-25 | **live**（部分被 bugfix-6 覆盖；机器型 bugfix 路径仍未全统一）| C-6 | P1 | 与 sug-30 同根；bugfix-6 已迁部分；bugfix-1/-2/-3/-4/-5 历史脏数据 + suggestion archive 仍未统一 | 进 chg-6-archive-路径统一 |
| sug-30（bugfix 工件树回 .workflow/flow/bugfixes/）| 2026-04-26 | **live**（部分被 bugfix-6 覆盖；req-id ≥ 41 严格执行已立但实际 CLI 落位 + reviewer checklist 未全做）| C-6 | P1 | 与 sug-29 同根；机器型 bugfix 工件落位与 reviewer 抽样仍欠 | 进 chg-6-archive-路径统一 |
| sug-31（done 后 commit + revert dry-run 自动化）| 2026-04-26 | **live** | C-7 | P2 | bugfix-5 / -6 testing-acceptance 跨 stage 通病；与 sug-51（testing 红线）协同 | 进 chg-7-testing-dogfood |
| sug-32（回 req-43 端到端连跳自证）| 2026-04-26 | **stale**（req-45 已修 over-chain，chg-01 dogfood 落地；req-43 不需回归）| C-7 | P3 | req-43 已 archive，bugfix-5 fix 后行为已变 | **出池**（建议 delete） |
| sug-33（briefing 话术 lint：拦 testing 全量回归 over-instructing）| 2026-04-26 | **live** | C-5 | P2 | bugfix-6 B6 降级；validate_contract.py 待扩规则 4 | 进 chg-5-契约-lint |
| sug-34（bugfix-5 acceptance/checklist.md 残留迁移）| 2026-04-26 | **live**（migrate_bugfix_layout 仍只覆盖 5 类主文件）| C-6 | P2 | 与 sug-29/-30 同根；本身是 followup | 进 chg-6-archive-路径统一 |
| sug-35（reviewer checklist 扩 artifact-placement / test-case-design 两类 lint 条目）| 2026-04-26 | **live** | C-5 | P2 | review-checklist.md 待扩条目 | 进 chg-5-契约-lint |
| sug-36（legacy archive 双源整合 + harness migrate archive）| 2026-04-26 | **live** | C-6 | P2 | CLI stdout 已多次提示但未实现 | 进 chg-6-archive-路径统一 |
| sug-37（harness enter 同步 runtime stage 到目标 req）| 2026-04-26 | **live** | C-9 | P1 | bugfix-6 archive 后 enter req-43 实证；helpers 当前 enter 路径不读 state yaml | 进 chg-9-runtime-state-sync |
| sug-38（next verdict stage 加 work-done gate）| 2026-04-26 | **applied-partial**（req-45 chg-01 已落 gate 双插桩 b64bcd7；但 dogfood 复验仍待跑且 sug-50 已是 fix-after 留痕）| C-1（主线）| P0 | 主线 sug，跟随 sug-09/-12/-40/-46/-50 全部 dup-of | **保留 live 直到 chg-1 dogfood 复验**；复验绿灯后 archive，否则升 P0 紧急 |
| sug-39（chg-01 派发钩子真实接通 record_subagent_usage runtime 强制）| 2026-04-27 | **live**（升 P0：sug-53 三次实证）| C-2（主线）| P0 | sug-25 文字契约 + chg-01 helper 已就位；但运行时钩子仍是文字，主 agent 未真调；usage-log 三连 req 缺失 | 进 chg-2-usage-log-runtime-接通（前置依赖最高优）|
| sug-40（sug-38 修复优先级评估 meta-followup）| 2026-04-27 | **stale**（sug-38 已升 P0 + req-45 chg-01 已落地）| C-1 | P3 | 评估性 followup，本职已在 sug-46 + req-45 落地 | **出池**（建议 delete） |
| sug-41（duration 口径 = subagent 工作时间不含人类等待）| 2026-04-27 | **live** | C-2 | P1 | 依赖 sug-39 接通；done.md §效率与成本 列字段口径需改 | 进 chg-2-usage-log-runtime-接通（chg-2 内子项）|
| sug-42（tokens 真实计算方案 + 下游消费）| 2026-04-27 | **live** | C-2 | P1 | 依赖 sug-39 接通；done_efficiency_aggregate fallback 待补 | 进 chg-2-usage-log-runtime-接通（chg-2 内子项）|
| sug-44（apply 取 sug.title + rename 同步 runtime title）| 2026-04-27 | **applied-out**（req-44 chg-01 + chg-02 已落代码 4374-4378 / rename helper 末尾）| C-3 | — | grep apply_suggestion 4374-4378 已优先取 sug.title；rename 已同步 current_requirement_title 等 | **出池**（applied） |
| sug-45（apply 单 sug 真填 requirement.md + rename 漏 .workflow/flow/ 目录）| 2026-04-27 | **applied-out**（req-44 chg-01/-02 已落 _append_sug_body_to_req_md + rename .workflow/flow/ 目录）| C-3 | — | grep _append_sug_body_to_req_md 已在 4390 / 4607 双路径调用 | **出池**（applied）|
| sug-46（sug-38 升 P0：req-44 二次实证）| 2026-04-27 | **applied-out**（已 archive 到 archive/，且 req-45 chg-01 已实施 gate 修复）| C-1 | — | 已在 archive/ 目录 | **已出池**（archive 已完成，但 .workflow/flow/suggestions/ 仍有同名文件，需核实是否双份）|
| sug-47（change.md §3 Requirement 字段裸 id F-01 followup）| 2026-04-27 | **live** | C-5 | P3 | 模板结构字段；契约 7 反向豁免补丁待加 | 进 chg-5-契约-lint |
| sug-48（rename runtime 同步未来扩字段提醒 F-02 followup）| 2026-04-27 | **live** | C-3 | P3 | 在 workflow_helpers.py 加注释；schema 文档化 | 进 chg-3-cli-suggest-rename-fix |
| sug-49（apply 单 sug 真填 sug.body — 与 sug-45 重述）| 2026-04-27 | **dup-of sug-45**（同问题，时序在 sug-45 之后；req-44 chg-01 已 fix）| C-3 | — | grep 4390 已调用 _append helper | **出池**（dup-of sug-45，applied）|
| sug-50（chg-01 gate gap：第一格修了 while 循环没保护）| 2026-04-27 | **applied-out**（b64bcd7 14:54 已修，gate 同时插桩在 7548 + 7580）| C-1 | — | grep 代码 7548（第一格）+ 7580（while 循环内）双 gate 均存在 | **出池**（已 fix；建议 chg-1 dogfood 复验后正式 archive）|
| sug-51（testing git restore 事故 + tmpdir 红线）| 2026-04-27 | **live**（升 P0）| C-7 | P0 | testing.md 红线 + harness validate testing-no-destructive-git lint 待立 | 进 chg-7-testing-dogfood（最高优在本簇）|
| sug-52（dogfood 实跑流程模板）| 2026-04-27 | **live** | C-7 | P1 | 与 sug-51 协同；testing 经验沉淀模板待补；plan.md §测试用例设计 dogfood TC 字段待加 | 进 chg-7-testing-dogfood |
| sug-53（usage-log 缺失三次实证升 sug-39 P0）| 2026-04-27 | **live**（评估性，并入 sug-39 升 P0 决策）| C-2 | P3 | 三次实证，证据级 | **保留 live**（作 sug-39 升 P0 凭证），chg-2 落地后 archive |

---

## 状态分布

| 判定 | 数量 | 处理 |
|-----|-----|-----|
| live（待入 chg） | 32 | 进 roadmap |
| applied-out（已落地需出池）| 6 | sug-25 / sug-44 / sug-45 / sug-46 / sug-50；sug-38 视 dogfood 复验结果决定 |
| stale（已被覆盖需出池）| 4 | sug-09 / sug-12 / sug-17 / sug-32 / sug-40（实计 5 条；sug-09 / sug-12 同时是 dup-of sug-38，亦计入 dup）|
| dup-of（合并主线）| 2 | sug-49（dup-of sug-45）；sug-09 / sug-12（dup-of sug-38，已 stale 主分类）|

> 总数：45（含 sug-25 即 applied 在池；sug-46 在 archive/ 但仍读出）。
> 输出后建议主 agent 执行 `harness suggest --delete sug-09 / sug-12 / sug-17 / sug-32 / sug-40` + 把 sug-25 archive（已 applied）+ 把 sug-44 / sug-45 / sug-46 / sug-49 / sug-50 archive。具体清池由用户拍板首批 chg 范围后随 chg 落地。

---

## 默认决策记录（default-pick）

本 stage 按 base-role 硬门禁四"同阶段不打断 + 按默认推进 + stage 流转前 batched-report"原则推进，记录如下：

| 决策点 | 选项 | default-pick | 理由 |
|-------|-----|-------------|-----|
| D-1 sug-09 / sug-12 状态判定 | A. dup-of sug-38（stale）/ B. 保留 live | **A** | 同根 over-chain，req-45 chg-01 已修；保留 live 重复登记浪费池容量 |
| D-2 sug-25 是否出池 | A. 保留池中 / B. archive | **B** | frontmatter status: applied + applied_by 已填，按契约 6 应翻转入 archive |
| D-3 sug-50 状态判定 | A. live（未修验证）/ B. applied-out（b64bcd7 已修）/ C. 保留 live 直到 dogfood 复验 | **C** | 代码层 grep 确认双插桩存在（7548 + 7580），但 sug-50 内容是诊断性留痕，建议 chg-1 dogfood 复验确认后 archive，避免静默漏修 |
| D-4 sug-38 状态判定 | A. applied-out / B. live 保留至 dogfood 复验 | **B** | 主线 sug 还在 dogfood 复验前；保留 live + chg-1 收口后再 archive |
| D-5 sug-17 / sug-32 / sug-40 是否 stale | A. stale（建议 delete）/ B. 保留 live | **A** | sug-17 上下文已变（req-31/41 大改对人文档），sug-32 触发条件已不成立（req-45 chg-01 已修），sug-40 是评估性 followup 已在 sug-46 落地 |
| D-6 chg 拆分粒度 | A. 5~10 个簇 chg / B. 30+ 个 sug 1:1 chg | **A** | 用户明确期望 5~10 个簇 chg；按主题簇切粒度合理，依赖关系清晰 |
| D-7 首批 chg 优先级排序 | A. P0 阻塞优先 → P1 契约硬化 → P2 体验 / B. 按主题独立并行 | **A** | usage-log（C-2）与 over-chain dogfood（C-1）是后续所有 chg 的数据底座 + 行为底座，优先级最高；scaffold mirror（C-4）+ archive 路径（C-6）作为契约硬化次之；体验类（C-8/-10）末位 |
| D-8 chg-2 是否最前置 | A. chg-2（usage-log runtime 接通）最前 / B. chg-1（over-chain dogfood 复验）最前 | **A** | usage-log 是 done 阶段六层 State 层校验底座，影响所有后续 req 的 done 阶段；chg-1 是行为底座但已有代码落地仅需复验；先把数据通路接通 |
| D-9 是否产出独立 sug-audit.md | A. 内嵌 session-memory 内 / B. 独立文件挂在 §4 引用 | **B** | 表格 45 行体量较大，独立文件可读性更好且便于复验 |
| D-10 chg 创建工件时机 | A. 本 stage 直接创建 chg 工件 / B. 输出 roadmap 等用户拍板首批后 harness change 创建 | **B** | 任务说明明确"不创建 chg 工件，输出 roadmap 供用户审核" |

---

## 待处理捕获问题

- sug-46 同时存在于 `.workflow/flow/suggestions/sug-46-...md`（live 副本）与 `.workflow/flow/suggestions/archive/sug-46-...md`（archive 副本）；frontmatter 仍 `status: pending`。**建议**：archive 双份其一，由 chg-3 顺修（属 CLI suggest archive 一致性问题，不阻断本 stage）。
- sug-43 已转 req-43，archive 副本存在；池中无残留，行为正确。
- 部分 sug 优先级 frontmatter（如 sug-39 medium）与本 audit 升 P0 的判断不一致；**default-pick = 不回填 frontmatter**（以免触发 sug 文件 churn），仅在 roadmap 中记录新优先级。

