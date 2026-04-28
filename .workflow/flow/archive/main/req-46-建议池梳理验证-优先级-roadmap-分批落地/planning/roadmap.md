# roadmap — req-46 chg 拆分 + 优先级 + 依赖图 + 首批推荐

> 产出：analyst-L1（opus），planning stage
> 来源：req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）
> 依据：sug-audit.md（45 条 sug 验证表 + 10 主题簇 + 默认决策记录）
> 校验语境：截至 d8237fe（archive: req-45（harness next over-chain bug 修复（紧急）） + sug 池积累）

## 1. 优先级模型

四级（与基线 P0/P1/P2/P3 对齐）：

| 级别 | 含义 | 触发条件 |
|-----|-----|---------|
| **P0** | 阻塞 / 数据安全 / 工作流彻底失效 | 多次实证（≥ 2 req 周期）/ 影响所有后续 req 的关键产物 / 安全事故 |
| **P1** | 契约硬化（防回归）/ 影响面广 | 历史漂移 / 契约文字契约已立但 lint 缺 / 状态同步不全 |
| **P2** | 体验优化 / 单点 bug | 单 req 实证 / 影响面有限 |
| **P3** | 极小修 / 注释 / 文档 | followup / 提醒注释 / minor lint |

工作量估算：

| 估算 | 含义 | 大致 token 量 |
|-----|-----|--------------|
| **小** | 单文件 ≤ 50 行改动 + 1~2 个 unit test | ~20-50k |
| **中** | 跨 2~5 文件 + 5~10 个 test + 部分 dogfood | ~50-150k |
| **大** | 跨 5+ 文件 + 端到端 dogfood + runtime hook 改造 | ~150-400k |

## 2. chg 拆分（10 个簇 chg）

> 命名规则：`chg-NN-<主题简短>`（NN 由 harness change 创建时分配）；本 roadmap 列序号仅供讨论，最终 chg-NN 序号由 CLI 实分配。

### chg-1 — over-chain dogfood 复验 + 兜底加固（C-1 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | **P0** |
| **工作量** | 中 |
| **解决 sug** | sug-38（主线，P0）/ sug-09 / sug-12 / sug-26（协同部分，主归 chg-9）/ sug-40 / sug-46 / sug-50 |
| **改动范围** | 1) `tests/` 加 dogfood 实测用例覆盖 verdict stage work-done gate 的 4 路径（first-hop + while loop / 缺产物 / 有产物）; 2) `src/harness_workflow/workflow_helpers.py` 双 gate 健壮性（已落 b64bcd7，本 chg 仅复验 + 加 lint 守护）; 3) 池清理：sug-09 / sug-12 / sug-40 → delete；sug-46 / sug-50 → archive；sug-38 dogfood 绿后 archive |
| **验收点** | AC-1.1 dogfood unit test 覆盖 4 路径全绿；AC-1.2 grep workflow_helpers.py 7548 + 7580 双 gate 仍存在；AC-1.3 池清理 5 条 sug 出池 |
| **前置依赖** | 无（最优先并行）|
| **后置阻塞** | 无（行为底座，已落地仅复验）|

### chg-2 — usage-log runtime 强制接通 + duration/token 口径修正（C-2 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | **P0** |
| **工作量** | **大** |
| **解决 sug** | sug-39（主线，升 P0）/ sug-25（已 applied 出池）/ sug-41（duration 口径）/ sug-42（token 落地）/ sug-53（升 P0 凭证）|
| **改动范围** | 1) Agent 工具返回 hook 接入 record_subagent_usage 的 runtime 强制路径（不只是文字契约）— 可能需要在 harness-manager 派发后由主 agent 的"返回处理"段强制调；2) `record_subagent_usage` entry 加 `dispatch_start_ts` / `return_ts` 字段（sug-41）+ token 6 字段固化（sug-42）；3) `done_efficiency_aggregate` duration 列从 stage_timestamps diff 改为 sum(usage entries.duration_ms)；4) fallback：无 entries 时输出 footer 说明（sug-42）；5) 历史兼容：旧 entries 标 ⚠️；6) 端到端 dogfood：本 chg 自身周期 entries ≥ 派发次数 - 容差 |
| **验收点** | AC-2.1 本 chg 自身周期 usage-log.yaml entries ≥ 6（analyst×2 / executing / testing / acceptance / done）；AC-2.2 done.md §效率与成本 duration 列基于 usage 而非 stage diff；AC-2.3 token 6 字段在新 entries 中均不为 null；AC-2.4 池清理 sug-25 / sug-39 / sug-41 / sug-42 / sug-53 出池 |
| **前置依赖** | 无（数据底座最高优先）|
| **后置阻塞** | chg-3 / chg-4 / chg-5 / chg-6 / chg-7 / chg-8 / chg-9 / chg-10 — 所有 done 阶段六层 State 层校验依赖此通路 |

### chg-3 — apply / rename / suggest CLI 顺修 + migrate 散落 .md（C-3 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | P2 |
| **工作量** | 中 |
| **解决 sug** | sug-08（migrate 散落 .md + 同 id 冲突）/ sug-19（rename --dry-run + 反向引用）/ sug-44（applied 出池）/ sug-45（applied 出池）/ sug-48（rename 同步白名单注释）/ sug-49（dup-of sug-45 出池）|
| **改动范围** | 1) `migrate_requirements._process_source` 扩 .md 单文件迁移 + slug 去冲（sug-08）；2) `harness rename --dry-run` 输出+ 文档反向引用更新（sug-19）；3) `rename_requirement` 末尾加注释列同步白名单字段（sug-48）；4) sug-46 双份清理（live 副本 + archive 副本）；5) 池清理 sug-44 / sug-45 / sug-49 archive |
| **验收点** | AC-3.1 migrate 单 .md 端到端用例；AC-3.2 rename --dry-run 输出 + 不实改文件；AC-3.3 sug-44/-45/-46/-49 出池 |
| **前置依赖** | chg-2（usage-log 数据底座；非强制但收益更高）|
| **后置阻塞** | 无 |

### chg-4 — scaffold_v2 mirror 漂移批量修复 + 自动同步告警（C-4 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | P1 |
| **工作量** | 中 |
| **解决 sug** | sug-15（自动同步告警）/ sug-21（~10 文件历史漂移）|
| **改动范围** | 1) 扫 .workflow/context/ vs src/harness_workflow/assets/scaffold_v2/.workflow/context/ 全量 diff 列出漂移文件；2) 默认行为：harness update / harness install 检测 diff → 告警 + 可选 --auto-sync flag；3) 漂移列表批量同步（experience/ + review-checklist.md 等 ~10 文件）；4) test_scaffold_v2_mirror_matches_roles 扩展为目录全量遍历，不仅 base/stage |
| **验收点** | AC-4.1 全量 diff 测试用例绿；AC-4.2 漂移列表清空（live = mirror）；AC-4.3 池清理 sug-15 / sug-21 出池 |
| **前置依赖** | 无（独立模块）|
| **后置阻塞** | chg-5（部分 lint 路径依赖 mirror 准确）|

### chg-5 — 契约硬门禁 lint 套件（id+title / 路径自检 / 派发话术 / reviewer 抽样）（C-5 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | P1 |
| **工作量** | **大** |
| **解决 sug** | sug-11（路径存在性自检）/ sug-16（session start 自检 E 原则）/ sug-18（Level-2 派发硬门禁）/ sug-22（裸 id lint）/ sug-23（grep lint 自动化）/ sug-27（render_work_item_id 全 stdout 审计）/ sug-33（briefing 话术 lint）/ sug-35（reviewer checklist 扩条目）/ sug-47（change.md §3 字段裸 id 反向豁免）|
| **改动范围** | 1) validate_contract.py 扩 4 类 lint：id+title 首次引用裸 id（sug-22 + sug-23 + sug-47）；requirement.md 路径存在性 ls 自检（sug-11）；briefing 话术 over-instructing grep（sug-33）；Level-2 派发模型一致性自检（sug-18）；2) render_work_item_id 全 CLI stdout 审计（sug-27）：harness status / next / archive / suggest --list；3) reviewer checklist 扩条目（sug-35）；4) base-role / harness-manager session-start 加 confirm E 原则自检条文（sug-16）；5) lint 工具骨架：CI / pre-commit hook / 主 agent 输出前自检 |
| **验收点** | AC-5.1 4 类 lint 端到端用例；AC-5.2 stdout 全路径审计无裸 id；AC-5.3 reviewer checklist 新条目；AC-5.4 池清理 9 条 sug 出池 |
| **前置依赖** | chg-4（mirror 准确，lint 才能正确扫）|
| **后置阻塞** | 无 |

### chg-6 — archive 路径关注点分离 + 双源整合 + bugfix 工件 migrate（C-6 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | P1 |
| **工作量** | **大** |
| **解决 sug** | sug-29（bugfix archive + suggestion archive 同步方向 C）/ sug-30（bugfix 工件回 .workflow/flow/bugfixes/）/ sug-34（migrate_bugfix_layout 覆盖 acceptance/）/ sug-36（legacy archive 双源整合 + harness migrate archive）|
| **改动范围** | 1) 扩 migrate_bugfix_layout 覆盖 acceptance/ checklist.md 等子目录（sug-34）；2) bugfix archive helper 落机器型工件到 .workflow/flow/archive/bugfixes/（sug-29 + sug-30）；3) suggestion archive helper 落位与 req archive 对齐（sug-29）；4) 新增 harness migrate archive 子命令做双源整合（sug-36），默认权威源 artifacts/main/archive/（对人 only）；5) bugfix-1 ~ bugfix-5 历史脏数据清理；6) reviewer checklist 加 bugfix 路径抽样条目；7) repository-layout.md §2/§3 加 bugfix 落位规则 + req-id ≥ 41 起严格执行 |
| **验收点** | AC-6.1 历史 bugfix archive 全部清空 artifacts/main/archive/bugfixes/{机器型}.md；AC-6.2 harness migrate archive 双源整合用例；AC-6.3 池清理 4 条 sug 出池 |
| **前置依赖** | chg-2（usage-log 数据底座）+ chg-5（lint 工具骨架，验收时跑契约扫）|
| **后置阻塞** | 无 |

### chg-7 — testing 红线 + safer dogfood 协议 + commit revert dry-run（C-7 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | **P0**（sug-51 testing git restore 事故是 P0 数据安全）|
| **工作量** | 中 |
| **解决 sug** | sug-31（commit revert dry-run 自动化）/ sug-32（stale 出池）/ sug-51（P0：testing 红线 + tmpdir mock 协议）/ sug-52（dogfood 实跑流程模板）|
| **改动范围** | 1) testing.md 加红线（任何破坏性 git 命令一律禁止 + dogfood 必须 tmpdir mock）— sug-51；2) base-role 硬门禁四例外条款 (i) 数据丢失风险扩展 testing 子条款；3) harness validate --contract testing-no-destructive-git lint（grep testing 阶段 action-log.md 是否含 git restore / git reset --hard / git checkout . / git clean -f / git branch -D）；4) testing.md 经验沉淀新增 dogfood 标准流程模板（tmpdir 工作区 + workflow_next 直调 + stage 落点断言）— sug-52；5) plan.md §测试用例设计 模板加 dogfood TC 必填字段 — sug-52；6) done 阶段 / harness archive 前自动 git revert --dry-run（sug-31）；7) 池清理 sug-31 / sug-32（stale）/ sug-51 / sug-52 出池 |
| **验收点** | AC-7.1 testing-no-destructive-git lint 端到端用例；AC-7.2 dogfood 模板写入 testing.md；AC-7.3 plan.md TC-D-NN dogfood 字段；AC-7.4 git revert --dry-run 输出落 done-report；AC-7.5 池清理 4 条 sug 出池 |
| **前置依赖** | chg-5（lint 骨架）|
| **后置阻塞** | 无（但所有后续 chg 的 testing 验收都依赖此契约）|

### chg-8 — install / update / archive CLI 体验顺修（C-8 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | P2 |
| **工作量** | 小 |
| **解决 sug** | sug-10（install --check）/ sug-14（archive --yes / -y）/ sug-20（tools/harness_update.py alias 化）/ sug-24（install 卡顿）|
| **改动范围** | 1) harness install 支持 --check（与 update --check 对齐）— sug-10；2) harness archive 支持 --yes / -y 非交互 — sug-14；3) tools/harness_update.py 改为 install_repo 的 thin alias / re-export — sug-20；4) install profiling 加进度提示 / 后台化 — sug-24（仅 profile 不实改架构）|
| **验收点** | AC-8.1 install --check 行为；AC-8.2 archive --yes 非交互；AC-8.3 update.py alias 化；AC-8.4 池清理 4 条 sug 出池 |
| **前置依赖** | 无 |
| **后置阻塞** | 无 |

### chg-9 — runtime / enter / archive / next 状态同步统一（C-9 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | P1 |
| **工作量** | 中 |
| **解决 sug** | sug-13（runtime ↔ req yaml stage 同步）/ sug-26（next/archive 联动写 stage_timestamps + stage）/ sug-37（harness enter 同步 runtime stage 到目标 req）|
| **改动范围** | 1) `harness enter` 路径读目标 req state yaml stage 字段写回 runtime；同步 operation_type / operation_target — sug-37；2) `harness archive` 路径联动清 runtime stage / current_requirement 字段 — sug-26；3) atomic 写入或一致性自检（runtime ↔ req yaml stage 不一致时阻断推进）— sug-13；4) test_workflow_state_consistency 端到端用例 |
| **验收点** | AC-9.1 enter 后 runtime.stage = state yaml.stage；AC-9.2 archive 后 runtime 不残留旧 stage；AC-9.3 next 路径 stage_timestamps + stage 字段双写；AC-9.4 池清理 3 条 sug 出池 |
| **前置依赖** | chg-2（usage-log 数据底座，验收时观测 stage 流转）|
| **后置阻塞** | 无 |

### chg-10 — 杂项小修（C-10 簇）

| 字段 | 内容 |
|-----|-----|
| **优先级** | P3 |
| **工作量** | 小 |
| **解决 sug** | sug-08（migrate Path str — 可拆到 chg-3）/ sug-14（archive --yes — 已挪 chg-8）/ sug-16（confirm E — 已挪 chg-5）/ sug-17（stale）/ sug-18（已挪 chg-5）/ sug-28（done_efficiency_aggregate 接受 str root）|
| **改动范围** | 1) `done_efficiency_aggregate` root 参数接受 str 自动 Path 包装（sug-28）；2) 池清理 sug-17 stale 出池（建议 delete）|
| **验收点** | AC-10.1 done_efficiency_aggregate 接受 str；AC-10.2 sug-17 出池 |
| **前置依赖** | chg-2（usage-log 数据底座）|
| **后置阻塞** | 无 |

> **注**：chg-10 做了"残留杂项"集合，绝大部分 sug 已被分流到其他 chg。实际只剩 sug-28 + sug-17 两条。可考虑与 chg-3 / chg-8 合并；本 roadmap 保留独立 chg 编号便于跟踪。

---

## 3. 依赖图（DAG）

```
                                ┌───────────┐
                                │  chg-1    │  P0  over-chain dogfood 复验
                                │ (sug-38)  │  （已落地仅复验）
                                └─────┬─────┘
                                      │ (无后置)
                                      ▼
                                ┌───────────┐
                                │  chg-2    │  P0  usage-log runtime 接通
                                │ (sug-39)  │  （数据底座，最重）
                                └─────┬─────┘
                                      │
                ┌──────────┬──────────┼──────────┬──────────┐
                ▼          ▼          ▼          ▼          ▼
            ┌───────┐ ┌───────┐  ┌───────┐ ┌───────┐ ┌───────┐
            │ chg-3 │ │ chg-4 │  │ chg-9 │ │chg-10 │ │ chg-7 │  P0  testing 红线
            │  P2   │ │  P1   │  │  P1   │ │  P3   │ │       │  （sug-51 数据安全）
            │CLI 顺修│ │mirror │  │runtime│ │ 杂项  │ │       │
            └───────┘ └───┬───┘  │同步   │ └───────┘ └───────┘
                          │      └───────┘
                          ▼
                      ┌───────┐
                      │ chg-5 │  P1  契约 lint 套件
                      │       │  （依赖 mirror 准确）
                      └───┬───┘
                          │
                          ▼
                      ┌───────┐
                      │ chg-6 │  P1  archive 路径整合
                      │       │  （依赖 lint + usage-log）
                      └───────┘

       ┌───────┐
       │ chg-8 │  P2  install/update/archive CLI 体验
       │       │  （独立无依赖）
       └───────┘
```

**关键路径**：chg-2 → chg-4 → chg-5 → chg-6（usage-log 数据底座 + mirror 准确 + lint 工具 + archive 路径）。
**并行路径**：chg-1 / chg-7 / chg-8 / chg-9 / chg-3 可独立并行（chg-1 / chg-7 / chg-8 完全无前置）。

---

## 4. 工作量汇总

| chg | 优先级 | 工作量 | 累计 |
|-----|-------|-------|------|
| chg-1 | P0 | 中 | 中 |
| chg-2 | P0 | 大 | 中+大 |
| chg-7 | P0 | 中 | 中+大+中 |
| chg-3 | P2 | 中 |  |
| chg-4 | P1 | 中 |  |
| chg-5 | P1 | 大 |  |
| chg-6 | P1 | 大 |  |
| chg-8 | P2 | 小 |  |
| chg-9 | P1 | 中 |  |
| chg-10 | P3 | 小 |  |

总量：3 大 / 5 中 / 2 小（合计 ~600~1500k token，单 req 内难以全完成，必须分批）。

---

## 5. 首批 chg 推荐

按"P0 优先 + 先解数据底座 + 一批不超过 3 chg 控制 token"原则，**首批推荐**：

| 序 | chg | 优先级 | 工作量 | 推荐理由 |
|---|-----|-------|-------|---------|
| 1 | **chg-1（over-chain dogfood 复验 + 兜底加固）** | P0 | 中 | 已有代码落地（b64bcd7）；本 chg 仅 dogfood 复验 + 池清理 5 条 sug 出池；快速收口 over-chain 簇 |
| 2 | **chg-2（usage-log runtime 强制接通 + 口径修正）** | P0 | 大 | 数据底座最高优；后续所有 chg 的 done 阶段六层 State 层校验依赖此通路；越早接通收益越大；池清理 5 条 sug 出池 |
| 3 | **chg-7（testing 红线 + safer dogfood + commit revert dry-run）** | P0 | 中 | sug-51 testing git restore 事故是 P0 数据安全；红线 + lint 落地后保护所有后续 testing 阶段；池清理 4 条 sug 出池 |

**首批合计**：3 个 chg / 池清理 14 条 sug（chg-1 出 5 + chg-2 出 5 + chg-7 出 4）/ 工作量 中+大+中。

**预期效果**：
- 池容量从 45 → 31（出 14 条）
- P0 全部清空（3 个 P0 chg 全在首批）
- 数据底座（usage-log）+ 行为底座（over-chain dogfood）+ 安全底座（testing 红线）三大底座一次性落地
- 第二批可平行启动 chg-4 / chg-9 / chg-3（中等工作量）

**第二批推荐**（用户拍板首批后，下一周期）：

| 序 | chg | 优先级 | 工作量 | 推荐理由 |
|---|-----|-------|-------|---------|
| 4 | **chg-4（scaffold_v2 mirror 漂移修复）** | P1 | 中 | 历史漂移影响 lint 准确性；为 chg-5 前置 |
| 5 | **chg-9（runtime / enter / archive / next 状态同步）** | P1 | 中 | 多次实证；与 chg-2 数据底座配合后效果倍增 |
| 6 | **chg-3（apply / rename / suggest CLI 顺修）** | P2 | 中 | 顺手清 sug-44/-45/-46/-49 双份残留 |

**第三批**：chg-5（契约 lint）+ chg-6（archive 路径）+ chg-8（install 体验）+ chg-10（杂项）。chg-5 与 chg-6 体量大，建议各自独立 req 周期。

---

## 6. 池清理计划（chg 落地后批量执行）

| chg | sug delete（stale）| sug archive（applied-out）|
|----|-------------------|--------------------------|
| chg-1 | sug-09 / sug-12 / sug-40 | sug-46 / sug-50（dogfood 复验后）/ sug-38（dogfood 复验后）|
| chg-2 | — | sug-25 / sug-39 / sug-41 / sug-42 / sug-53 |
| chg-3 | — | sug-44 / sug-45 / sug-49 / sug-08 / sug-19 / sug-48（落地后）|
| chg-4 | — | sug-15 / sug-21（落地后）|
| chg-5 | — | sug-11 / sug-16 / sug-18 / sug-22 / sug-23 / sug-27 / sug-33 / sug-35 / sug-47（落地后）|
| chg-6 | — | sug-29 / sug-30 / sug-34 / sug-36（落地后）|
| chg-7 | sug-32 | sug-31 / sug-51 / sug-52（落地后）|
| chg-8 | — | sug-10 / sug-14 / sug-20 / sug-24（落地后）|
| chg-9 | — | sug-13 / sug-26 / sug-37（落地后）|
| chg-10 | sug-17 | sug-28（落地后）|

**stale delete 总计**：5 条（sug-09 / sug-12 / sug-17 / sug-32 / sug-40）
**applied-out archive 总计**：39 条（其余）
**总池容量出池**：~44 条（首批 14 条 + 后续 30 条）— 首批后池剩 ~31 条，全部 chg 落地后池清空。

---

## 7. 默认决策清单（default-pick / planning stage）

承接 requirement_review stage 的 D-1 ~ D-10，本 stage 新增决策：

| 决策点 | 选项 | default-pick | 理由 |
|-------|-----|-------------|-----|
| D-11 raw_artifact validate gate 不绿是否 ABORT | A. 严格 ABORT 不放行 / B. raw_artifact ✓ 后留痕放行（done 文档要求豁免到 done 阶段）/ C. 中断由用户介入 | **B** | analyst.md 硬门禁原文要求 exit 0 但工具自身设计未做 stage 感知（done 阶段产物期望在 requirement_review 即存在不合理）；历史 req-43/-44/-45 同 case 均放行；保留 raw_artifact ✓ 留痕，把工具修复列入 chg-5 lint 套件 |
| D-12 chg 拆分上限 | A. 10 个簇 chg / B. 不拘数量 | **A**（10 个）| 用户期望 5~10 个；按 10 簇定义自然出 10 chg，最契合用户意图 |
| D-13 chg-2（usage-log）排首批 | A. 排首批 / B. 排第二批（待 chg-1 dogfood 复验后再启动）| **A** | 数据底座，影响所有后续 req 的 done 阶段；越早接通收益越大；与 chg-1 完全无依赖可并行 |
| D-14 chg-7（testing 红线）排首批 | A. 排首批（P0 数据安全）/ B. 排第二批（P1 lint 顺修）| **A** | sug-51 是 testing git restore 实证事故，P0 数据安全；不排首批等于把已知红线推迟保护 |
| D-15 sug-46 双份处理 | A. chg-1 顺手清 / B. 独立 chg | **A** | 单点小修，与 over-chain 簇同主题；归 chg-1 顺手收口 |
| D-16 sug-25 出池方式 | A. delete（applied 直删）/ B. archive（保留 applied 历史）| **B** | sug 池契约 6 frontmatter status: applied 应翻转入 archive；保留历史溯源链路（applied_by 已填）|

---

## 8. 风险与限制

- **chg-2 风险**：runtime 强制 hook 改造涉及 Agent 工具返回处理路径，可能与 harness-manager 派发流程耦合度高；建议小步走 + 端到端 dogfood 一边验证一边落地；
- **chg-5 风险**：lint 工具骨架可能有误报；建议先全部 WARN 后转 FAIL，避免误伤合规场景（与 sug-33 实施要点对齐）；
- **chg-6 风险**：archive 路径变更涉及历史脏数据迁移，必须先 dry-run 看影响面；migrate 工具必须可回滚；
- **chg-7 风险**：testing 红线落地需要主 agent 自觉（lint 仅扫 action-log.md 是事后 lint）；建议加 pre-execute 提醒（subagent briefing 注入红线条款 + testing.md 头部加红线 banner）；
- **整体风险**：池清理动作必须等 chg 验收 PASS 后执行，避免 chg 失败但 sug 已删导致追溯断链。

---

## 9. 不在本 roadmap 范围

- 本 roadmap 仅做"chg 拆分 + 优先级 + 依赖图 + 首批推荐"，不涉及具体 chg 的 change.md / plan.md 编写
- chg 工件创建（change.md / plan.md）由用户拍板首批后，主 agent 用 `harness change` 创建
- 跨 repo（Yh-platform）影响仅在 scaffold_v2 mirror 同步范围内（chg-4），不动其他 repo
- 本 roadmap 之后新增的 sug-54+ 不纳入本 req 周期
