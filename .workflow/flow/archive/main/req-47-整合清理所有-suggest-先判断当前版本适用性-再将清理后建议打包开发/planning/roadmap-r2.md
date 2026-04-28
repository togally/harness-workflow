# roadmap-r2 — req-47 chg 拆分（增量校准）+ 优先级 + 依赖图 + 首批推荐

> 产出：analyst-L1（opus），planning stage Part B
> 来源：req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）
> 依据：sug-audit-r2.md（39 条复核结论 + 6 条新增 sug 归簇）
> 校验语境：截至 a801820（done: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）testing + acceptance + done）
> 承接：`.workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/roadmap.md`（10 chg round-1 拆分）

---

## 1. req-46 roadmap 剩余 8 chg 的现状校准

req-46 roadmap.md §2 列 10 chg；其中 chg-01（机器型工件路径修复 + 防再犯 lint）+ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）已落地（commit 6406c40 + 171bac8）。

| roadmap chg | round-1 范围 | round-2 现状校准 | 状态 |
|------------|-------------|-----------------|------|
| **chg-1**（over-chain dogfood 复验）| sug-38 主线 + 6 跟随 sug 池清理 | chg-02 已落 _is_stage_work_done 严格化 + 4 路径子进程 dogfood + sug-46/-50 archived；**round-1 chg-1 已被 chg-02 间接吸收**；本轮仅做 sug-38 自身 archive（已在池清理 4.2 完成）| **不再需要新 chg**；C-1 簇收尾完毕 |
| **chg-2**（usage-log runtime 接通 + duration/token 口径）| sug-39 主线 + sug-25 / -41 / -42 / -53 | round-2 新增 sug-59（写读路径漂移）实证：record_subagent_usage 写 state/sessions/，done_efficiency_aggregate 读 flow/requirements/，**两路径不一致**导致即使 entries 完整也读不到；sug-39 钩子接通仍未做 → token 全 0 实证 | **维持 chg-2**；范围 += sug-59；优先级 P0 不变 |
| **chg-3**（apply / rename / suggest CLI 顺修）| sug-08 / -19 / -44 / -45 / -48 / -49 | sug-44 / -45 / -49 已 round-1 applied-out；剩 sug-08 / -19 / -48 = 3 条；sug-46 双份残留已通过本 stage 池清理处理（不归 chg-3）| **维持 chg-3**；范围缩至 3 条 sug |
| **chg-4**（scaffold_v2 mirror 漂移）| sug-15 / -21 | round-2 新增 sug-56（usage-reporter.md 漂移）实证 sug-21 子集；归簇时一并扫除 | **维持 chg-4**；范围 += sug-56（dup-of sug-21 子集）|
| **chg-5**（契约硬门禁 lint 套件）| sug-11 / -16 / -18 / -22 / -23 / -27 / -33 / -35 / -47 | sug-35 已 round-1 applied-out（chg-01 reviewer checklist 已加）→ 移出 chg-5；round-2 新增 sug-54（marker 契约）+ sug-57（partial_* 字段语义化）→ 加入 chg-5 | **维持 chg-5**；范围 = 8 老 - 1 + 2 新 = **9 条**；优先级 P1 不变（工作量大）|
| **chg-6**（archive 路径关注点分离）| sug-29 / -30 / -34 / -36 | round-2 无新增 sug；范围不变 | **维持 chg-6**；4 条 sug；P1 大工作量 |
| **chg-7**（testing 红线 + safer dogfood + commit revert dry-run）| sug-31 / -51 / -52 | round-2 新增 sug-55（dev mode flag）+ sug-58（首批必含承接 marker）；本 chg-7 = **首批必含**；testing.md 已含部分子进程 dogfood 红线（chg-02 落地）但**没有 testing-no-destructive-git lint + 没有 tmpdir mock 红线 + 没有 done 阶段 commit revert dry-run 自动化** | **维持 chg-7**；范围 += sug-55 + sug-58 = **5 条 sug**；首批必含 |
| **chg-8**（install / update / archive CLI 体验）| sug-10 / -14 / -20 / -24 | round-2 无新增；range 不变 | **维持 chg-8**；4 条；P2 小工作量 |
| **chg-9**（runtime / enter / archive / next 状态同步）| sug-13 / -26 / -37 | round-2 无新增；范围不变 | **维持 chg-9**；3 条；P1 中工作量 |
| **chg-10**（杂项小修）| sug-14 / -17 / -28 + 重复 | sug-17 已 round-1 stale；sug-14 已挪 chg-8；剩 sug-28 单点；考虑合 chg-3 或独立小 chg | **降级**；范围缩至 1 条 sug-28；建议合 chg-3 |

### round-2 调整结论

- **C-1 簇收尾**：round-1 chg-1 不再需要新 chg；sug-38 archive 完毕。
- **C-2 簇加 sug-59**：chg-2 范围扩到含写读路径修复（sug-59）。
- **C-4 簇加 sug-56**：dup-of sug-21 子集，归簇时一并扫除。
- **C-5 簇换血**：移出 sug-35（已 applied-out）；加入 sug-54 + sug-57（round-2 新沉淀契约缺口）。
- **C-7 簇加 sug-55 / sug-58**：首批必含（D-7 = A 锁定）；范围扩至 5 条。
- **C-10 降级**：建议合并 chg-3 或独立小 chg；范围仅 sug-28。

---

## 2. 6 条新增 sug 的归簇决定（D-r2-2 ~ D-r2-5）

| sug-id | 归簇 chg | default-pick 依据 | 备注 |
|--------|---------|------------------|------|
| **sug-54**（executing role briefing 应规定 ✅ marker）| **chg-5**（契约 lint）| D-r2-4 = A：marker 兼容性属契约 lint 套件 | 可在 _is_stage_work_done 兼容 [x] / ✓ / DONE 多 marker（实现层）+ executing.md SOP 加 marker 自检（契约层）|
| **sug-55**（chg-02 部署同步契约 dev mode flag HARNESS_DEV_MODE=1）| **chg-7**（testing 红线）| D-r2-3 = B：本质属 testing 阶段 friction + dev mode 关切，归 testing 红线簇最自然，简化依赖图 | 同时实现 acceptance.md 部署同步硬条目豁免 + harness install --check |
| **sug-56**（scaffold_v2 usage-reporter.md 漂移）| **chg-4**（mirror 修复）| D-r2-2 = A：dup-of sug-21 子集，归 sug-21 主线 | sug-21 主修时一并扫除 usage-reporter.md |
| **sug-57**（sug 模板补 partial_* 字段语义化）| **chg-5**（契约 lint）| D-r2-5 = A：契约 6 扩展，归 chg-5 lint 套件 | 配合 partial_* 字段拼写 lint + 契约 6 文档化 |
| **sug-58**（下个 req 优先 chg-7 testing 红线）| **chg-7**（testing 红线）| D-7 = A 锁定：本 req 首批必含；sug-58 内容 = 承接 marker，chg-7 acceptance PASS 后自动 archive | D-r2-8 = A 自动 archive |
| **sug-59**（done_efficiency_aggregate 路径漂移）| **chg-2**（usage-log runtime 接通）| 同根因不同维度（钩子未接通 + 写读路径漂移）；chg-2 一次性修两个维度 | chg-2 plan.md 拆 step 时先修写读路径让数据可读 → 再修钩子让数据更全 |

**小计**：6 条新 sug 全部归簇（4 个不同 chg：chg-2 / chg-4 / chg-5 / chg-7）。

---

## 3. 本 req 完整 chg 列表（校准后）

> 命名规则：本 req 的 chg-NN 序号由 `harness change` CLI 实分配（不一定对齐 req-46 簇编号）；roadmap-r2 表格中的"对应 req-46 簇"列保留簇语义追溯。
> 本 req 首批仅落 1 个 chg（D-4 = A，K = 1，对应 req-46 chg-7 簇）；其余留 roadmap 给下个 req（D-3 = B 留尾，与 req-46 同模式）。
> CLI 实分配：本 req 首批 chg 实际编号 = **chg-01**（对应 req-46 roadmap chg-7 簇）。

| 本 req chg 编号 | 对应 req-46 簇 | 主题 | 优先级 | 工作量 | 含 sug 列表（含数）| 是否首批 |
|---------------|---------------|------|-------|-------|-------------------|---------|
| **chg-01**（CLI 实分配）| **chg-7**（C-7 簇）| testing 红线 + safer dogfood + commit revert dry-run + dev mode flag | **P0**（数据安全）| 中 | sug-31 / sug-51 / sug-52 / sug-55 / sug-58 = **5 条**| **是（首批 K=1）**|
| 留 chg（下 req）| **chg-2**（C-2 簇）| usage-log runtime 接通 + duration/token 口径 + 写读路径漂移修 | P0（数据底座）| 大 | sug-39 / sug-41 / sug-42 / sug-53 / sug-59 = 5 条 | 否（留尾）|
| 留 chg | **chg-3**（C-3 簇）| apply / rename / suggest CLI 顺修 + migrate 散落 .md | P2 | 中 | sug-08 / sug-19 / sug-48（+ sug-28 可合并）= 3-4 条 | 否（留尾）|
| 留 chg | **chg-4**（C-4 簇）| scaffold_v2 mirror 漂移修 + 自动同步告警 | P1 | 中 | sug-15 / sug-21 / sug-56 = 3 条 | 否（留尾）|
| 留 chg | **chg-5**（C-5 簇）| 契约硬门禁 lint 套件（id+title / 路径 / 派发话术 / marker / partial_*）| P1 | 大 | sug-11 / sug-16 / sug-18 / sug-22 / sug-23 / sug-27 / sug-33 / sug-47 / sug-54 / sug-57 = **10 条** | 否（留尾，建议独立 req）|
| 留 chg | **chg-6**（C-6 簇）| archive 路径关注点分离 + 双源整合 + bugfix 工件 migrate | P1 | 大 | sug-29 / sug-30 / sug-34 / sug-36 = 4 条 | 否（留尾，建议独立 req）|
| 留 chg | **chg-8**（C-8 簇）| install / update / archive CLI 体验顺修 | P2 | 小 | sug-10 / sug-14 / sug-20 / sug-24 = 4 条 | 否（留尾）|
| 留 chg | **chg-9**（C-9 簇）| runtime / enter / archive / next 状态同步统一 | P1 | 中 | sug-13 / sug-26 / sug-37 = 3 条 | 否（留尾）|
| 留 chg | **chg-10**（C-10 簇）| 杂项（仅 sug-28）| P3 | 小 | sug-28 = 1 条（建议合 chg-3）| 否（合并候选）|

**总数**：本 req 首批 1 chg（chg-01 = req-46 chg-7 簇）；留尾 8 chg。
**总 sug 覆盖**：首批 5 条 + 留尾 30 条 = 35 条（不计本 stage 4 条池清理 + 1 条 sug-38 archive = 池清理 5 条；不计 sug-53 partial 留 pending）。

---

## 4. 首批 chg 推荐（已锁定）

> D-4 = A + D-7 = A 已锁定首批 K=1，仅承接 chg-7（testing 红线簇）。本节给执行细节。

### 4.1 首批 chg 概览

| chg | 优先级 | 工作量 | 含 sug | 推荐理由 |
|-----|-------|-------|-------|---------|
| **chg-01**（CLI 实分配，对应 req-46 chg-7 簇）| **P0** | 中 | sug-31 / sug-51 / sug-52 / sug-55 / sug-58 = 5 条 | sug-51（testing git restore 事故）是 P0 数据安全；sug-58 是 req-46 done 明确"下个 req 优先承接"承接 marker；本 chg 落地后保护所有后续 testing 阶段；sug-55 dev mode flag 同 chg 落地避免 friction 阻塞落地节奏 |

### 4.2 chg-01 范围预览（落点 = chg.md / plan.md）

**改动范围**（5 大主题）：

1. **testing.md 红线扩展**（sug-51 主线）：在 testing.md 加"任何破坏性 git 命令一律禁止 + dogfood 必须 tmpdir mock"硬红线（base-role 硬门禁四例外条款 (i) testing 子条款）；
2. **testing-no-destructive-git lint**（sug-51 + sug-23 配套）：`harness validate --contract testing-no-destructive-git` 扫 action-log.md 是否含 git restore / git reset --hard / git checkout . / git clean -f / git branch -D；
3. **dogfood 经验沉淀模板**（sug-52 主线）：testing.md 加完整 dogfood 标准流程模板（tmpdir 工作区 + workflow_next 直调 + stage 落点断言）；plan.md §测试用例设计模板加 dogfood TC 必填字段；
4. **done 阶段 commit + revert dry-run 自动化**（sug-31 主线）：done.md 加六层回顾后自动 git revert --dry-run 抽样；harness archive 前自动 dry-run 校验；
5. **dev mode flag**（sug-55）：HARNESS_DEV_MODE=1 环境变量；acceptance.md 部署同步硬条目在 dev mode 下豁免；harness install --check 子命令；
6. **池清理**：sug-31 / sug-51 / sug-52 / sug-55 / sug-58 acceptance PASS 后翻 frontmatter status: archived + applied_by_chg → 物理 archive。

**预期 AC**（≥ 6 条）：
- AC-N1.1：testing-no-destructive-git lint 端到端用例（命中 + 不命中各 ≥ 1 条）
- AC-N1.2：dogfood 模板 grep testing.md 命中 ≥ 1 条
- AC-N1.3：plan.md TC 模板含 dogfood 必填字段
- AC-N1.4：done 阶段 git revert --dry-run 输出落 done-report 或 acceptance-report
- AC-N1.5：HARNESS_DEV_MODE=1 在 acceptance.md 部署同步硬条目下豁免实测
- AC-N1.6：池清理 5 条 sug 出池

### 4.3 chg-01 依赖图（DAG）

```
本 req 周期内：

           ┌──────────────────┐
           │   chg-01 (P0)    │
           │ testing 红线簇   │
           │ (5 sugs)         │
           └────────┬─────────┘
                    │
                    │ chg-01 acceptance PASS
                    ▼
           ┌──────────────────┐
           │ 池清理 5 条 sug  │
           │ + sug-58 自动    │
           │ archive          │
           └──────────────────┘
                    │
                    ▼
              本 req done

留 chg（下个 req 周期，依赖图见 §5）：
chg-2（usage-log）→ chg-3 / chg-4 / chg-9 / chg-10
                  → chg-5（依赖 chg-4 + chg-01）
                  → chg-6（依赖 chg-5 + chg-2）
chg-8 独立无依赖
```

**前置依赖**：无（chg-01 首批，可立即启动）。
**后置阻塞**：本 req 不再排其他 chg；下个 req 的 chg-2 / chg-5 等可承接。

---

## 5. 留尾说明 + 给下个 req 的承接建议

### 5.1 留 8 chg 优先级表（下个 req 承接顺位）

| 顺位 | chg | 优先级 | 工作量 | 推荐理由（给下个 req）|
|------|-----|-------|-------|---------------------|
| 1（最高优）| **chg-2**（usage-log runtime 接通）| **P0** | 大 | 数据底座，影响所有后续 req 的 done 阶段六层 State 层校验；sug-59 写读路径漂移已实证 token 全 0 → 修了再说 |
| 2 | **chg-9**（runtime sync）| P1 | 中 | 多次实证；与 chg-2 数据底座配合后效果倍增 |
| 3 | **chg-4**（scaffold mirror 漂移）| P1 | 中 | 历史漂移影响 lint 准确性；为 chg-5 前置 |
| 4 | **chg-3**（CLI 顺修）| P2 | 中 | 顺手清池 sug-08 / sug-19 / sug-48 + 可合 sug-28 |
| 5 | **chg-8**（install/update 体验）| P2 | 小 | 独立无依赖；可作下个 req"轻量陪跑" |
| 6（独立 req）| **chg-5**（契约 lint 套件）| P1 | 大 | 体量过大（10 条 sug），建议独立 req 周期 |
| 7（独立 req）| **chg-6**（archive 路径整合）| P1 | 大 | 体量过大（4 条 sug + 历史脏数据迁移），建议独立 req 周期 |
| 8（合并候选）| **chg-10**（杂项 sug-28）| P3 | 小 | 单点；建议合 chg-3 或后置随机塞 |

### 5.2 下个 req 推荐节奏（与 req-46 / req-47 同模式）

- **下 req 首批推荐 K = 2**：chg-2（usage-log）+ chg-9（runtime sync）—— 两 chg 同 stage_timestamps / state yaml 数据底座主题，工作量大+中可控
- **下 req 留尾**：chg-3 / chg-4 / chg-8（中 + 中 + 小，留再下个 req 周期）
- **再下个 req 独立**：chg-5（契约 lint 套件）+ chg-6（archive 路径整合）各自独立 req 周期（体量大）

### 5.3 池清理留尾路径

| sug | 留 pending 原因 | 落地节点 |
|-----|----------------|---------|
| sug-39（钩子接通主因）| 本 req 不在首批 | 下个 req chg-2 acceptance PASS 后 archive |
| sug-53（usage-log 缺失，partial）| 主因 sug-39 未接通 | 与 sug-39 同节点 archive |
| 其余 25 条 live sug | 留尾 chg 各自落地后 archive | 见 §3 chg 列表 |

### 5.4 本 req 不动事项

- 不修改 sug 文件 priority frontmatter（避免 churn，与 req-46 同款）
- 不重审 round-1 已结案 11 条 sug（D-1 = A 锁定）
- 不开始 chg-2 / chg-3 / ... 任何留尾 chg 实现（D-3 = B 留尾，下个 req 承接）

---

## 6. 工作量估算

> 与 req-46 roadmap §6 同口径。

| chg | 优先级 | 工作量 | 累计描述 | 是否本 req |
|-----|-------|-------|---------|-----------|
| chg-01（chg-7 簇）| P0 | 中（~50-150k）| 5 sug + 4 跨文件改 + 1 lint 新增 + 子进程 dogfood 5 用例 + 池清理 | **是**（首批）|
| chg-2（usage-log）| P0 | 大（~150-400k）| Agent hook + duration / token 6 字段 + 写读路径修 + 端到端 dogfood | 否 |
| chg-3（CLI 顺修）| P2 | 中（~50-150k）| 3 单点 fix + 用例 | 否 |
| chg-4（mirror 漂移）| P1 | 中（~50-150k）| 11 mirror 文件 + 自动同步告警 + 全量 diff 测试 | 否 |
| chg-5（契约 lint）| P1 | 大（~150-400k）| 10 sug + 4 类 lint 工具骨架 + render_work_item_id 全审计 + reviewer checklist 扩 | 否（独立 req 候选）|
| chg-6（archive 整合）| P1 | 大（~150-400k）| 4 sug + bugfix-1~5 历史迁移 + harness migrate archive 子命令 | 否（独立 req 候选）|
| chg-8（install 体验）| P2 | 小（~20-50k）| 4 sug 单点 fix | 否 |
| chg-9（runtime sync）| P1 | 中（~50-150k）| 3 sug + 状态自检 lint + 端到端用例 | 否 |
| chg-10（杂项）| P3 | 小（~10-30k）| 1 sug 合 chg-3 候选 | 否 |

**本 req 工作量预估**：仅 chg-01 = 中（~50-150k）+ session-memory / 池清理 / sug 翻 frontmatter 等 ~10-30k = **~80-180k token**（单 req 可控）。
**留尾 8 chg 总量**：3 大 + 4 中 + 2 小 = ~700-1700k token —— 与 req-46 roadmap §4 同量级，需 3-4 个 req 周期承接。

---

## 7. round-2 default-pick 决策清单（roadmap 层）

承接 sug-audit-r2 §5 D-r2-1 ~ D-r2-8；本 §列 roadmap 层新增决策。

| 决策点 | 选项 | default-pick | 理由 |
|-------|-----|-------------|-----|
| **D-rm-1（chg-01 是否拆 chg-7a / chg-7b）**| A. 单 chg 5 sug 一次性落 / B. 拆 chg-7a（testing 红线 + lint）+ chg-7b（commit revert + dev mode）| **A**（单 chg）| 5 sug 同根因（testing 阶段安全 + dogfood 协议）；拆开徒增工件量；plan.md §3 通过 step 顺序细分即可 |
| **D-rm-2（chg-3 / chg-10 合并）**| A. 合并（sug-28 进 chg-3）/ B. 独立 chg-10 | **A** | sug-28 单点（done_efficiency_aggregate 接受 str root）属 helper 顺修，与 chg-3（CLI 顺修）主题相近；省一个 chg 编号 |
| **D-rm-3（首批 K 范围确认）**| A. K=1 仅 chg-01（testing 红线）/ B. K=2 加 chg-2（usage-log）| **A** | D-4 = A 已锁定 K=1；本 §再确认；chg-2 大工作量，与 chg-01 一起易超标 |
| **D-rm-4（chg-01 与 chg-2 是否互锁依赖）**| A. 独立可并行 / B. chg-01 必须前置 chg-2 | **A** | testing 红线（chg-01）与 usage-log（chg-2）正交；并行最高效；下个 req 单独承接 chg-2 即可 |

---

## 8. 风险与限制

- **chg-01 风险 1（lint 误报）**：testing-no-destructive-git lint 扫 action-log.md，可能误伤合规场景（如 git revert --dry-run 本身含 git 字符串）。**缓解**：lint 规则白名单：`git revert --dry-run` / `git diff --name-only` / `git log` 等读操作豁免；仅扫破坏性写操作；先 WARN 一轮再切 FAIL。
- **chg-01 风险 2（dogfood 模板与 chg-02 已有红线重叠）**：testing.md 已含子进程 dogfood 红线（chg-02 落地）；本 chg 加 tmpdir mock 红线 + 完整模板可能重复。**缓解**：plan.md §1 step 1 显式核对 testing.md 已有内容，仅补充 sug-51 数据安全维度；不重写 chg-02 已写章节，仅扩展。
- **chg-01 风险 3（dev mode flag 设计盲点）**：HARNESS_DEV_MODE=1 是环境变量，可能与 CI / 自动化场景冲突。**缓解**：默认未设 = 严格模式；明确文档化 dev / prod / ci 三种语义；acceptance.md 文档化适用范围。
- **chg-01 风险 4（commit revert dry-run 影响 done 阶段时长）**：done 阶段加 dry-run 会增加几秒；用户体验微影响。**缓解**：放在 acceptance/ → done 之间执行，不阻塞主流程；输出落 acceptance-report.md。
- **整体风险**：池清理动作必须等 chg-01 acceptance PASS 后执行，避免 chg 失败但 sug 已删导致追溯断链。

---

## 9. 不在本 roadmap 范围

- 留尾 8 chg 的 change.md / plan.md 编写：本 roadmap 仅描述范围 + 优先级 + 依赖；下个 req 承接时再写
- 跨 repo（Yh-platform）影响：本 req 仅本仓库 harness-workflow
- 本 roadmap 之后新增的 sug-60+：不纳入本 req 周期（与 req-46 同款）
- bugfix 紧急 hot fix：不挪进本 req 批次

