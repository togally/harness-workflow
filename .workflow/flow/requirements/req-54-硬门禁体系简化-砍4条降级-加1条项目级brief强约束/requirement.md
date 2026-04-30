---
id: req-54
title: "硬门禁体系简化-砍4条降级-加1条项目级brief强约束"
created_at: 2026-04-30
operation_type: requirement
stage: analysis
---

## Background

### 用户原话与判断

用户在本会话实战 + survey 后拍板「按这个方案做」：

- **必保留 8 条硬门禁**：全局 1（runtime 必读）/ 全局 3（current_requirement 缺失停止）/ base 三（角色自我介绍）/ 四（同阶段不打断）/ 五（跨 repo scaffold mirror，挂 harness-manager.md）/ 六（对人汇报 ID 必带描述）/ 七（周转汇报不列选项）/ 九（subagent 产出独立核查）。
- **降级 4 条硬门禁**：全局 2（节点任务必派 subagent）/ 全局 4（conversation_mode: harness 锁定节点）/ base 一（工具委派 toolsManager）/ base 二（操作说明 + action-log）。
- **新增 1 条 base 八**：subagent dispatch briefing 模板必须显式注入「项目级加载链提示」段（Step 7.6 + 7.6.1 + boilerplate 段落），让 subagent 加载链按规范命中 `artifacts/project/`。

总数 8 - 4 + 4 - 1 + 1 + 1 ≈ 9（基本持平），每条都有真实威慑。

### 实战观察（6 周期累计实证）

bugfix-11 / req-51 / req-52 / bugfix-12 / req-53 / bugfix-13 周期累计观察：

1. **被频繁破坏的 4 条**（无人响应 = 通胀失效）：
   - 全局 2（节点任务必派 subagent）：req-51 / req-52 / bugfix-13 周期内主 agent 多次直接改文件（rationale：路径调整 / 状态修复 / 微调一行；派 subagent 反而更慢）；
   - 全局 4（conversation_mode: harness 锁定）：实测 conversation_mode 从未真正影响 stage 推进决策，与 active_requirements / current_requirement 双轨重叠；
   - base 一（toolsManager 必委派）：常规 read / edit 都没有匹配工具，强制委派只是空跑；toolsManager 真正发挥价值仅在新工具 / 跨 repo / API 集成几类；
   - base 二（操作说明 + action-log）：常规 read / edit 操作之前都喊一句「接下来我要执行 X」+ action-log 追加 → 噪音过多，action-log.md 已超 3000 行不可读；真正有价值的是 stage 流转 / rollback / CLI 异常 / 派 subagent 等少数事件。
2. **项目级承载层**（req-51 / req-52 / bugfix-13）已立住地皮 + 门牌 + 邮差，但**靠 LLM 自觉**遵守 role-loading-protocol Step 7.6 / 7.6.1；本会话用 PetMallPlatform marker `<<<PETMALL_EXPERIENCE_LOADED_OK>>>` 实证：subagent 不主动声明命中数 → 加载链是否生效完全黑盒；brief 不强提示有失效风险。
3. **硬门禁数量虚增 → "硬度"通胀**：当 12 条硬门禁有 4 条几乎天天在被技术性违反、从来没人喊停时，剩下的真硬门禁（如硬门禁九 subagent 虚报核查、硬门禁五 mirror 同步）也会被视为可商量；硬门禁失去威慑边际效用递减。

### 用户想要的

砍掉 4 条已"通胀"的硬门禁（降级为指导原则，不删整段，保留作历史追溯），新增 1 条 base 八约束 subagent dispatch briefing 必须显式 brief 项目级加载链；总数持平但每条都是"违反 = 灾难"级真威慑。

## Goal

简化 Harness 硬门禁体系，让每条剩下的硬门禁都有**真实威慑**（违反 = 灾难性后果），同时补上现有项目级承载层（req-51 / req-52 / bugfix-13）的"事前 brief 强约束"短板，与硬门禁九（subagent 产出独立核查）形成「事前 brief / 事后核查」配对闭环。

可度量预期：

1. **G-01 硬门禁通胀清理**：WORKFLOW.md 全局硬门禁段从 4 条砍到 2 条（仅剩 1 / 3）；base-role.md 硬门禁清单同步去掉一 / 二（保留段落作"已降级"段标注）。
2. **G-02 硬度恢复**：剩余 8 条硬门禁中无一条在过去 6 周期内被技术性违反（保留 = 真硬度）。
3. **G-03 项目级加载链 brief 强约束**：base-role.md 新增硬门禁八，subagent dispatch briefing 模板必须显式注入「项目级加载链提示」boilerplate；harness-manager.md §3.6 派发协议引用本硬门禁，dogfood 自证。
4. **G-04 与硬门禁九形成闭环**：硬门禁八（事前 brief）+ 硬门禁九（事后核查）首尾相接，让"项目级承载层"从"靠 LLM 自觉"升级到"brief 强提示 + 核查兜底"。
5. **G-05 fresh repo 不破契约**：跑 `harness install --force-managed` 后 `harness validate --contract all` 全 PASS，无 contract 因硬门禁改动而 break。
6. **G-06 自证（dogfood）**：本 req 自身 done 阶段交付总结作为硬门禁八实证——主 agent 派发 subagent 时 brief 必含项目级加载链段（自证）。

## Scope

### In scope（必须包含，拍板锁定决策）

**砍 / 降级 4 条**（保留段落作"已降级"段标注，方便历史追溯；不删整段）：

| 现行编号 | 现行内容（关键词） | 降级方向 | 落位 |
|---------|-----------------|---------|------|
| **全局 2** | 节点任务必派 subagent，主 agent 不直接动代码 / 项目文件 | 降级为「重大改动必派；微调（单文件 / 状态文件 / 文档）主 agent 可直接做」**指导原则**；从 WORKFLOW.md 全局硬门禁段移除 | WORKFLOW.md 头部 |
| **全局 4** | conversation_mode: harness 锁定当前节点，不得漂移到其他需求或阶段 | 合并到状态机文档（`.workflow/flow/stages.md` 之类）作"会话模式语义说明"；从 WORKFLOW.md 全局硬门禁段移除 | WORKFLOW.md 头部 |
| **base 一** | 工具优先（必委派 toolsManager） | 改"新工具 / 跨 repo / API 集成必派；常规 IO 不必"；段标题改为 **「## 工具委派指导原则（原硬门禁一降级）」** + 文末注 reasons | base-role.md §硬门禁一段 |
| **base 二** | 操作说明 + action-log | 改"stage 流转 / rollback / CLI 异常 / 派 subagent 必记；常规 read / edit 不记"；段标题改为 **「## 操作日志指导原则（原硬门禁二降级）」** + 文末注 reasons | base-role.md §硬门禁二段 |

**新增 1 条 base 八**（拟稿见下方）：

> **硬门禁八：subagent dispatch briefing 必含项目级加载链提示**
>
> 适用范围：所有派发 subagent 的上级角色（含 harness-manager / technical-director / 各 stage 主控者 / 主 agent）。
>
> 硬规则：派发 subagent 时构建的 briefing **必须**显式注入「项目级加载链提示」段，包含以下三块内容：
>
> 1. role-loading-protocol.md Step 7.6 / 7.6.1 的字面引用（项目级承载路径 + 加载顺序 + 命中后自检要求）；
> 2. boilerplate 一句话：「subagent 加载完角色文件后，必须按 Step 7.6 / 7.6.1 加载 `artifacts/project/{constraints,experience,tools}/`，并在首条输出追加项目级命中数自检」；
> 3. 当前任务相关的 scope 提示（`scope ∈ {constraints, experience-roles, experience-tool, experience-risk, experience-regression, experience-stage}`）。
>
> 违规判定：上级派发的 briefing 中**未含**「项目级加载链」字面段 → 上级硬门禁八违反，与硬门禁九（subagent 产出独立核查）配对成立。
>
> 沉淀来源：req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）；与 req-51 / req-52 / bugfix-13 项目级承载层立柱配套。

**保留不动 8 条**：全局 1（runtime 必读）/ 全局 3（current_requirement 缺失停止）/ base 三（自我介绍）/ 四（同阶段不打断）/ 五（mirror 同步）/ 六（对人汇报 ID 带描述）/ 七（周转不列选项）/ 九（subagent 独立核查）。

### Out of scope（明确不做）

- **不做**：不动 src/ 实现源码、不动测试用例除新增 req-54 防回归 lint、不破 req-51 / req-52 / bugfix-11 / bugfix-12 / bugfix-13 / req-53 已立的项目级承载层 + dogfood 闭环。
- **不动**：PetMallPlatform / PetMallAdmin / uav 等用户仓（修复面只在 harness-workflow 仓内，与 bugfix-11 红线一致）。
- **不引入**：`_use_*_layout*` / `*_LAYOUT_FROM_*` 命名（bugfix-11 红线延续）。
- **不删整段**：砍 4 条只是"降级文字"，base-role.md 原硬门禁一 / 二整段保留作"已降级"段落，方便历史追溯；只改段标题 + 文末注 reasons + 从硬门禁清单总览中移除。
- **不重写 stages.md**：全局 4 conversation_mode 语义合并到 stages.md / state-machine 描述，但 stages.md 主体不重写（仅新增一段说明）。
- **不调 harness next** / **不修 runtime.yaml** / **不派发更下层 subagent**（analyst 角色禁区）。
- **不引入新 yaml schema**（硬门禁八 brief 模板用 markdown 字面段，不引入新数据结构）。

## Acceptance Criteria

- **AC-01（全局硬门禁砍 2 条）**：WORKFLOW.md 全局硬门禁段从 4 条砍到 2 条（仅剩硬门禁一 runtime 必读 + 硬门禁三 current_requirement 缺失停止；编号保持原 1 / 3 不重排）；新增加注脚说明全局 2 / 全局 4 已降级为指导原则；grep `^## 全局硬门禁` 后正文 `^[0-9]+\.` 命中 2 行（不是 4 行）。
- **AC-02（base 一降级）**：base-role.md 「## 硬门禁一：工具优先」整段标题改为 「## 工具委派指导原则（原硬门禁一降级）」，段尾追加 reasons 段（≥ 3 行 rationale + 来源 req-54）；硬门禁清单总览（`## 硬门禁清单`）从「硬门禁一：工具优先」一行移除（保留其他 6 条）。
- **AC-03（base 二降级）**：base-role.md 「## 硬门禁二：操作说明与日志」整段标题改为 「## 操作日志指导原则（原硬门禁二降级）」，段尾追加 reasons 段（≥ 3 行 rationale + 来源 req-54）；硬门禁清单总览从「硬门禁二：操作说明与日志」一行移除。
- **AC-04（base 八新增）**：base-role.md 在硬门禁九段之**前**新增「## 硬门禁八：subagent dispatch briefing 必含项目级加载链提示」整段（以拟稿 Scope 段落形态）；硬门禁清单总览补「硬门禁八：subagent dispatch briefing 必含项目级加载链提示」一行；段内必含 role-loading-protocol Step 7.6 / 7.6.1 引用 + boilerplate 字面 + scope 枚举；落位 base-role.md 现「硬门禁九」段之上（编号紧邻 7 → 8 → 9）。
- **AC-05（harness-manager.md §3.6 引用）**：harness-manager.md §3.6「派发 Subagent」 派发协议小节内显式增加一段「按硬门禁八 brief 项目级加载链」子条款，落 §3.6 末尾或 「派发协议」「构建 briefing」之后；包含 boilerplate 字面 + 引用 base-role.md 硬门禁八 + 引用 role-loading-protocol Step 7.6 / 7.6.1。
- **AC-06（stage-role.md 同步硬门禁清单编号）**：stage-role.md 不动其他段；仅同步 base-role 硬门禁清单编号变化（`继承自 base-role 的执行清单` 表 / Session Start 约定段中"硬门禁一"/"硬门禁二"任何编号引用同步降级——改为引用「工具委派指导原则」/「操作日志指导原则」或注明 「原硬门禁一/二降级」）。
- **AC-07（scaffold_v2 mirror 同步）**：4 文件同步到镜像（硬门禁五配套保护）：
  - `src/harness_workflow/assets/scaffold_v2/.workflow/...`（路径前缀，下同）`/WORKFLOW.md`
  - `/.workflow/context/roles/base-role.md`
  - `/.workflow/context/roles/harness-manager.md`
  - `/.workflow/context/roles/stage-role.md`
  - 跑 `diff -rq <live> <mirror>` 4 文件全 silent。
- **AC-08（dogfood 自证）**：本 req-54 自身的 done 阶段交付总结作为「硬门禁八实证」——主 agent 在派发本 req 各 stage subagent 时（含本 Phase 1+2+3 派发自身），briefing 必含项目级加载链段；done 阶段交付总结记录为「硬门禁八 dogfood 自证（含 N 次派发，N ≥ 1，每次 brief 均含项目级加载链字面段）」。
- **AC-09（防回归 lint）**：`tests/test_req54_hard_gate_simplify.py` 覆盖：
  - TC-01：grep WORKFLOW.md 全局硬门禁段，断言 ≤ 2 条编号行；
  - TC-02：grep base-role.md，断言「## 硬门禁一」标题已改为「## 工具委派指导原则」+ 「## 硬门禁二」标题已改为「## 操作日志指导原则」；
  - TC-03：grep base-role.md，断言「## 硬门禁八」段落存在 + 段内含 boilerplate 字面 + Step 7.6 / 7.6.1 字面；
  - TC-04：grep harness-manager.md §3.6 块内含「硬门禁八」字面引用；
  - TC-05：4 mirror 文件 diff -q 全 silent（subprocess 调用 diff，断言 returncode == 0）；
  - TC-06：dogfood——subprocess 跑 `harness install --force-managed`（tmp dir）然后 `harness validate --contract all` exit 0。
- **AC-10（fresh repo dogfood 全契约 PASS）**：fresh git init + harness install --force-managed 后，跑 `harness validate --contract all`（含 artifact-placement / user-write-protected-zones / triggers / 7 等所有契约）全 exit 0；无新 contract 因本 req 改动 break；test_req54_hard_gate_simplify.py 中 TC-Dogfood-01 覆盖此场景。

## Split Rules

由 analyst 自主拆分（base-role 硬门禁四同阶段不打断；req-40 方向 C analyst 合并规约）。本 req 拆 3 chg 线性依赖：

- **chg-01**：文档层降级 + 新增 + mirror 同步（WORKFLOW.md / base-role.md / harness-manager.md / stage-role.md 四 live 文件 + 四 scaffold_v2 mirror 文件，**8 文件改动**，全文字 / 无 src 改动）；
- **chg-02**：dispatch briefing 模板落地 + dogfood（harness-manager.md §3.6 派发协议补「项目级加载链 boilerplate 段」字面模板 + 给主 agent 派发 helper（如有）补强；本会话主 agent 后续派发都按硬门禁八 brief 自动注入，dogfood 自证）；
- **chg-03**：测试 + 防回归 lint（`tests/test_req54_hard_gate_simplify.py` 覆盖 AC-09 + dogfood AC-10，≥ 6 TC）；

执行顺序：chg-01 → chg-02 → chg-03（chg-02 引用 chg-01 落地的 base 八条款；chg-03 lint chg-01 + chg-02 落地结果）。

---

## OQ Verdicts（用户 2026-04-30 拍板，锁定，本 Phase 1 不需重新走 OQ）

| # | 决策点 | 用户拍板 |
|---|------|---------|
| OQ-1 | 是否砍全局 2 / 4 + base 一 / 二 共 4 条降级？ | 是（按 Scope 锁定决策表） |
| OQ-2 | 是否新增 base 八 subagent dispatch briefing 强约束？ | 是（拟稿见 Scope） |
| OQ-3 | 砍法是"删整段"还是"降级文字 + 段标题改 + 保留段落"？ | **降级文字 + 段标题改 + 保留段落**（方便历史追溯） |
| OQ-4 | 硬门禁清单总览（`## 硬门禁清单`）是否需要把降级 2 条移除？ | 是（移除即"硬门禁数量"减 2，与降级语义一致） |
| OQ-5 | 全局 4（conversation_mode 锁定）合并到哪里？ | `.workflow/flow/stages.md` 之类的"状态机文档"（不重写主体，仅新增一段说明） |
| OQ-6 | 硬门禁八编号位置（base-role.md 内）？ | 紧邻硬门禁九之前（7 → 8 → 9 编号连续） |
| OQ-7 | dogfood 自证落点？ | done 阶段交付总结记录"硬门禁八 dogfood 自证"行（不新增独立工件） |

### 范围红线（不改面）

- 修复面 limited 在 harness-workflow 仓
- 不动 PetMallPlatform / PetMallAdmin / uav 等用户仓
- 不破 req-51 / req-52 / bugfix-11 / bugfix-12 / bugfix-13 / req-53 已立内容
- 不引入 `_use_*_layout*` / `*_LAYOUT_FROM_*` 命名（bugfix-11 红线延续）
- 砍 4 条只是降级文字，不删 base-role.md 整段（保留作"已降级"段落）
- 不引入新 yaml schema（硬门禁八 brief 模板用 markdown 字面段）
