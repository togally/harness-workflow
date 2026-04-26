# Session Memory — req-43（交付总结完善）/ requirement_review stage

## 1. 自我介绍 + 模型自检（Step 7.5）

我是分析师（analyst / opus），承接 req-43（交付总结完善）的 requirement_review stage 需求澄清环节。

**模型一致性自检（Step 7.5）**：当前 runtime 不直接暴露 model self-introspection；按降级路径处理 —— briefing 内 `expected_model: opus`（Opus 4.7），与 `.workflow/context/role-model-map.yaml` 中 `roles.analyst: opus` 一致。本 subagent 未能自检 model 一致性，briefing 期望 = opus（Opus 4.7），按"未自检"留痕，不阻塞。

## 2. 用户原话（中文一字不差）

> 1.bug 和 需求 以及 建议 都需要出局交付总结，简单来说只要是任务就要总总结
> 2.交付总结内的每个阶段token使用量 和 部分时间是没有统计到的

（推测："出局" = "输出"；"总总结" = "总结"。）

## 3. 我的解读（背景 / 用户痛点 / 边界判断）

### 3.1 背景

用户在 req-42（archive 重定义：对人不挪 + 摘要废止） 完成后，连续观察到 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 与 req-42 的 `交付总结.md §效率与成本` 段大量出现 `⚠️ 无数据` / 仅 1 条 entry 的情况，并意识到 bugfix-1 ~ bugfix-4 完成时根本没有等价的对人交付总结。两件事一起触发本 req。

### 3.2 用户痛点（两个独立但相关）

- **痛点 A（覆盖面）**：只有 req 走 done 阶段的六层回顾 + 交付总结产出；bugfix 收尾后只剩零散 `bugfix.md` / `test-evidence.md`，sug 直接处理路径甚至连零散文档都没有。任务完成无法一屏对人交代。
- **痛点 B（统计完备性）**：交付总结模板 §效率与成本段有「按 role × model」的 token 表 + 「各阶段耗时」表，但**未按 stage 切片**呈现 token；时间字段也有缺漏（runtime 与 req yaml `stage_timestamps` 不同步、testing/acceptance/done 阶段 `entered_at` 漏写）。

### 3.3 边界判断

我做了以下边界判断（写入 requirement.md §3.1/§3.2）：

- **范围内**：三类任务级工作项（req / bugfix / sug）的对人交付总结、per-stage token 切片、per-stage 时间字段、stage 流转点联动、归档对接、State 层校验扩展。
- **范围外**：非任务级总结、`record_subagent_usage` 自身接通（属 sug-25（record_subagent_usage 派发链路真实接通），是隐含前置）、跨项目/跨仓库聚合、token 衍生指标、done 六层回顾流程改造、branch 命名规约、CLI 入口设计是否新增显式 done 命令。
- **数据通路原则**：消费已有数据，**不**重复采集；sug-25 是隐含前置依赖，本 req 假设其在本 req 启动时已落地或并行落地（若未落地，第一个 chg 可能需吸收 sug-25 的内容）。

## 4. 写入 requirement.md 的内容摘要 + 关键边界判断

### 4.1 写入摘要

- **§1.5 Background**：3 段记录现状（什么有 / 什么缺）+ 用户原话原文 + 触发原因；列出 req-41 / req-42 实证 `⚠️ 无数据` 行号。
- **§2 Goal**：3 条 bullet —— 任务级覆盖统一 / per-stage 字段补齐 / 数据通路不重复采集。
- **§3 Scope IN**：4 大块（任务覆盖面 / 统计字段 per-stage 维度 / 数据通路对接 / bugfix-sug 数据通路 / 归档对接 / State 层校验扩展）。
- **§3 Scope OUT**：7 条（非任务级 / record_subagent_usage 自身 / 跨项目聚合 / 衍生指标 / 六层回顾流程 / branch 规约 / CLI 入口设计）。
- **§4 Acceptance Criteria**：7 条 AC，覆盖任务级覆盖完整 / per-stage token 字段齐全 / per-stage 时间字段齐全 / 数据通路只消费不重采 / State 层校验不退化 / stage 流转点联动写齐 / 归档对接三类一致。
- **§5 Split Rules**：保留模板原则 + 4 条本 req 专属拆分提示（按统计字段维度切 / 按任务类型切 / 按 State 层校验切 / sug-25 数据通路前置）。

### 4.2 关键边界判断（已在 requirement.md 内显式标注，但此处汇总以便后续 chg 拆分参考）

- **判断 1（sug 是否产出交付总结）**：默认 sug 直接处理路径（不转 req）需要轻量交付总结；sug → req 转化路径由对应 req 的 done 产出（不重复）。详见 OQ-1。
- **判断 2（bugfix 是否走 done 阶段）**：默认复用 req 的 done 模板但精简字段（删 chg 列举段、合并 testing+acceptance 段），不另起新阶段。详见 OQ-2。
- **判断 3（token 字段完整性）**：默认仅落原始字段（input/output/cache_read/cache_creation/total + tool_uses + duration_ms），cache 命中率 / 单价 / 人时折算等衍生指标不在本 req 范围。详见 OQ-3。
- **判断 4（per-stage 表插入位置）**：默认新增「按 stage × role × model 切片」单表替换或增补现有「按 role × model 聚合」表；保留还是替换详见 OQ-4。
- **判断 5（usage-log entry 中 bugfix-id 字段）**：默认复用既有 `req_id` 字段携带 `bugfix-id`（CLI helper 兼容），不新增 schema 字段。详见 OQ-5。

## 5. Open Questions（仍需用户确认的边界）

> 每条形如 `- {问题}。default-pick: {选项}。理由：{一句话}。`

- **Q1（OQ-1，sug 是否产出交付总结）**：sug 是否要"独立产出"交付总结，还是仅 sug → req 转化后由对应 req 的 done 产出？**default-pick**：**B（仅转化后由 req 产出 + sug 直接处理路径产出"轻量版"交付总结，落 `artifacts/{branch}/suggestions/sug-NN-{slug}/交付总结.md`，模板压到三段：建议是什么 / 处理结果 / 后续）**。理由：sug 直接处理（如 `--apply` / `--reject` / `--archive`）是任务级动作但成本/复杂度远小于 req，需要对人交代但不应套用 req 重模板；纯转化路径由 req 兜底，不重复。
- **Q2（OQ-2，bugfix 是否走 done 阶段）**：bugfix 是否走 req 同款 done 阶段六层回顾，还是另开"bugfix 收尾"轻量模板？**default-pick**：**B（复用 done 阶段六层回顾框架但精简模板字段——删"chg 列举"段，合并 testing+acceptance 段为"修复验证"段；模板路径独立 `bugfix-交付总结.md` 但字段顺序与 req 模板一致以利对比）**。理由：bugfix 通常无 chg 拆分、testing/acceptance 已合并，强行复用 req 模板会出现大片空字段；轻量化更合实情，但保留六层回顾保证 State 层校验复用。
- **Q3（OQ-3，token 字段是否含衍生指标）**：交付总结的 token 表是否包含 cache 命中率 / 单价折算 / 人时换算等衍生指标？**default-pick**：**A（仅落原始字段：input/output/cache_read/cache_creation/total + tool_uses + duration_ms。衍生指标在渲染层按需计算或走后续独立 req）**。理由：原始字段是事实，衍生指标依赖单价 / 折算系数（会随时间变化），写死在交付总结里会很快过时；保留原始字段未来任何衍生口径都可重算。
- **Q4（OQ-4，per-stage 表与 role × model 表关系）**：新增「按 stage 切片」表是**替换**现有「按 role × model 聚合」表，还是**并列**两表？**default-pick**：**B（合并为单表「stage × role × model × token × tool_uses」，stage 列做主键，按 stage 排序）**。理由：两表数据同源（usage-log entries），分两表呈现造成阅读冗余；合并为单表既满足"按 stage 看"也满足"按 role × model 聚合看"（用户自行 group by 阅读），表头一致便于 helper 实现。
- **Q5（OQ-5，bugfix usage-log 字段如何携带 bugfix-id）**：`record_subagent_usage` 现有签名 `req_id=..., chg_id=..., reg_id=...` 无 `bugfix_id`，bugfix 周期内调用如何归类？**default-pick**：**A（复用 `req_id` 字段携带 `bugfix-id` 字符串，新增 `task_type` 字段 = "req" | "bugfix" | "sug" 区分；helper 改 1 行参数兼容；不破坏既有 entries 历史数据）**。理由：新增 `bugfix_id` 字段会动 schema、现有 helper / 校验逻辑全部要改；复用 `req_id` + `task_type` 字段是最小改动且兼容历史。

## 6. 待处理捕获问题（职责外）

- 无（本 stage 无超出 analyst 职责的捕获问题）。

## 7. default-pick 决策清单（本 stage 内按默认推进的争议点）

> 同阶段不打断硬门禁四 + stage-role.md 约定，stage 内争议按 default-pick 推进、stage 流转前 batched-report。

- 本 stage 所有 5 个争议点（OQ-1 ~ OQ-5）均**未**按 default-pick 静默推进，全部以 Open Questions 形式上交用户在 stage 流转前确认（避免 chg 拆分阶段返工）。

## 8. analyst 专业化抽检反馈（首次运行抽检模板）

- **抽检产物**：req-43（交付总结完善）/ requirement.md（§1.5 / §2 / §3 / §4 / §5 五段）+ 本 session-memory.md。
- **质量评分**：B（持平）。
- **退化点明细**：（持平档）背景段引用了 req-41 / req-42 实证行号增强可信度；OQ 给出 5 条 default-pick + 理由；AC 7 条均可断言。无明显退化点。
- **是否触发 regression 回调 B**：否。
- **抽检人 + 时间 + req 范围**：subagent-self / 2026-04-25 / req-43。

---

## planning stage

### 0. 自我介绍 + 模型自检（Step 7.5）

我是分析师（analyst / opus），承接 req-43（交付总结完善）的 planning stage chg 拆分 + plan.md 大纲起草任务。

**模型一致性自检（Step 7.5）**：runtime 不暴露 model self-introspection；按降级路径处理 —— briefing 内 `expected_model: opus`（Opus 4.7），与 `.workflow/context/role-model-map.yaml` 中 `roles.analyst: opus` 一致。本 subagent 未能自检 model 一致性，briefing 期望 = opus（Opus 4.7），按"未自检"留痕，不阻塞。

### 1. 用户已确认决策（5 条 default-pick 全部锁定，作为已定决策落本 stage）

requirement_review stage 5 个 OQ 用户已隐式确认（通过 /harness-next 推进）：

- **OQ-1**：sug 直接处理路径产出"轻量版"3 段交付总结（建议是什么 / 处理结果 / 后续）；sug→req 转化路径不重复出。
- **OQ-2**：bugfix 复用 done 六层回顾框架但精简模板——删 chg 段、合并 testing+acceptance 为「修复验证」段；独立文件名 `bugfix-交付总结.md`，字段顺序与 req 模板一致以利对比。
- **OQ-3**：token 表只落原始字段（input/output/cache_read/cache_creation/total + tool_uses + duration_ms），不含 cache 命中率 / 单价 / 人时等衍生指标。
- **OQ-4**：「按 stage 切片」与「按 role × model 聚合」**合并为单表** stage × role × model × token × tool_uses，stage 列做主键。
- **OQ-5**：复用既有 `req_id` 字段携带 bugfix-id 字符串，新增 `task_type=req/bugfix/sug` 字段区分；`record_subagent_usage` helper 改 1 行参数兼容；不动既有 schema 主体。

### 2. 拆分原则陈述

按 **requirement.md §5 split rules** 给出的「按统计字段维度切」与「按任务类型切」两条主线**叠加**「数据通路前置依赖」一条辅线拆分：

- **维度 1（统计字段）**：per-stage token 聚合 = 纯渲染层（动 `done_efficiency_aggregate` helper） vs. per-stage 时间补齐 = 动 CLI 流转点（`harness next` / `harness archive` 的 stage_timestamps 写入逻辑），互不阻塞，独立成两个 chg。
- **维度 2（任务类型）**：req（既有路径只扩字段）+ bugfix（新增 `bugfix-交付总结.md` 全套路径）+ sug（轻量版 3 段产出 + 归档对接）三条任务级路径互相独立——req 改最小（仅模板换表）、bugfix 改最大（新文件名 + done 路径整套接入）、sug 中等（新文件 + `harness suggest --apply / --archive` 钩子）。
- **辅线（数据通路前置）**：sug-25（record_subagent_usage 派发链路真实接通） 是隐含前置依赖；本 stage 调研确认 sug-25 仍处 `pending`（`.workflow/flow/suggestions/sug-25-record-subagent-usage.md` frontmatter `status: pending`），未落地。**default-pick：第一个 chg 吸收 sug-25** —— 没有真实 entries 写入，所有后续 chg 的渲染 / 校验 / 字段都将拿不到数据反复打空，先把派发链路真接通才有意义。
- **State 层校验扩展（base-role.md `## done 六层回顾 State 层自检`）**：纯文档契约改写，无代码动，并入最后一个收口 chg。

### 3. chg 列表（共 5 条 chg）

| chg | 一句话目标 | 覆盖 AC | 依赖 | 估算粒度 |
|-----|-----------|--------|------|--------|
| **chg-01（record_subagent_usage 派发链路接通 + 端到端 dogfood）** | 吸收 sug-25：把 `record_subagent_usage` 在 harness-manager Step 4 的文字硬门禁真接通到主 agent / harness-manager 的 Agent 工具返回钩子，新增 `task_type` 参数 + `req_id` 携带 bugfix-id/sug-id；端到端 dogfood 自证 entries 数 ≥ 派发次数 - 容差 | AC-04（数据通路只消费不重采，前置）/ AC-05（State 层校验不退化，前置） | 无（最前置） | **大** |
| **chg-02（per-stage 时间字段补齐：流转点联动写齐 entered_at + exited_at）** | 改 `update_state_yaml_stage` / `archive_requirement` 等 stage 流转写入点：写 new_stage.entered_at 时同时写 prev_stage.exited_at；新增 pytest 覆盖跳跃流转 + runtime↔req yaml 同步双反例 | AC-03 / AC-06 | chg-01（需采集真接通才能验数据完备性） | **中** |
| **chg-03（per-stage token 聚合：done_efficiency_aggregate helper 扩 stage 维度 + 单表渲染）** | `done_efficiency_aggregate` 新增 stage 维度 group by；`done.md` 模板把「各阶段耗时分布」+「各阶段 token 分布」合并为单表 `stage × role × model × input/output/cache_read/cache_creation/total × tool_uses`（OQ-4）；helper 单测覆盖 entries 缺失/部分缺失/全齐 三 fixture | AC-02 / AC-04 | chg-01（无 entries 渲染恒空） | **中** |
| **chg-04（bugfix 引入 `bugfix-交付总结.md` 全路径）** | 新增 done 等价收尾路径（bugfix 流程目前只走 `regression → executing → testing → acceptance`，acceptance 后无 done）；模板字段比照 req 模板但删 chg 段、合并 testing+acceptance 为「修复验证」段（OQ-2）；落位 `artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/bugfix-交付总结.md`；`harness validate --human-docs` 校验扩 bugfix；`repository-layout.md` §2 白名单加 `bugfix-交付总结.md` | AC-01（bugfix 维度）/ AC-07（bugfix 维度） | chg-01 + chg-03（复用渲染 helper） | **大** |
| **chg-05（sug 轻量交付总结 + State 层契约扩三类任务 + 收口）** | sug 直接处理路径（`harness suggest --apply` 不转 req 时 / `--archive` / `--reject`）产出 3 段轻量 `交付总结.md`，落 `artifacts/{branch}/suggestions/sug-NN-{slug}/交付总结.md`（OQ-1）；扩 `repository-layout.md` §2 白名单 + 新增 `artifacts/{branch}/suggestions/` 子树定义；改写 `base-role.md ## done 六层回顾 State 层自检` 把「req 维度」扩到三类任务（req/bugfix/sug）；`harness validate --human-docs` 三类同等校验；scaffold_v2 mirror 同步 + dogfood 收口 | AC-01（sug 维度 + 完整覆盖）/ AC-05（State 层扩展）/ AC-07（sug 维度 + 三类一致） | chg-01 + chg-04（复用 bugfix 路径模式） | **中** |

### 4. 拆分图（依赖关系 ASCII）

```
                           chg-01（派发链路接通 + dogfood）
                                │
                       ┌────────┴────────┐
                       │                 │
                       ▼                 ▼
      chg-02（时间补齐）        chg-03（token 单表渲染）
       (CLI 流转点)              (helper + 模板)
                       │                 │
                       └────────┬────────┘
                                │
                                ▼
              chg-04（bugfix-交付总结.md 全路径）
                                │
                                ▼
   chg-05（sug 轻量 + State 层扩三类 + scaffold mirror 收口）
```

执行顺序：`chg-01 → (chg-02 || chg-03 并行) → chg-04 → chg-05`。

### 5. chg-01 plan 大纲

#### 目标
吸收 sug-25（record_subagent_usage 派发链路真实接通）：把 chg-08（req-41） 已立的「Agent 工具返回必调 helper」文字硬门禁**真接通**到运行时钩子；新增 `task_type` 参数让 helper 能区分 req/bugfix/sug；自身周期 dogfood 自证 usage-log entries 数 ≥ 派发次数 - 容差。这是后续所有 chg 的前置数据底座。

#### 影响文件列表
- `src/harness_workflow/workflow_helpers.py`：`record_subagent_usage` 函数签名加 `task_type: str = "req"` 参数（OQ-5）；usage-log entry 新增 `task_type` 字段；保持向后兼容（默认 "req"）。
- `.workflow/context/roles/harness-manager.md` §3.6 Step 4：派发钩子真接通——把"Agent 工具返回后 必调 record_subagent_usage" 从纯文字契约升级为可观测的执行步骤（指令 agent 返回后立即调 helper，并在 session-memory.md 留痕）。
- `.workflow/context/roles/base-role.md` `## done 六层回顾 State 层自检`：保持文字契约不变，但允许 chg-05 后续扩三类任务时复用同一接通逻辑。
- `tests/test_record_subagent_usage.py`（新增）：覆盖 task_type 默认 / req / bugfix / sug 四 fixture + entries 写入 schema 校验。
- `.workflow/flow/suggestions/sug-25-record-subagent-usage.md`：`status: pending → applied`（`harness suggest --archive` 落地）。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` + `base-role.md`：scaffold mirror 同步（硬门禁五）。

#### 实施步骤
1. 改 `record_subagent_usage` helper 签名加 `task_type` 参数 + entry 字段，写最小单测（5 条 case）。
2. 改 `harness-manager.md` Step 4 把派发钩子从纯文字契约升级为带「session-memory 留痕」的可观测步骤（每次派发后主 agent 必须在自己的 session-memory.md 写一行 `record_subagent_usage called: {role} / {model} / ts`）。
3. 端到端 dogfood：本 chg 自身 executing / testing / acceptance / done 四 stage 派发后自检 usage-log.yaml 是否真有 entries（chg-01 完成时 entries 数应 ≥ 4）。
4. scaffold_v2 mirror 同步（`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 下 harness-manager.md + base-role.md 与本仓库 `.workflow/context/roles/` 同名文件 diff = 0）。
5. `harness suggest --archive sug-25` 把 sug-25 翻 `status: applied`。
6. `harness validate --human-docs` exit 0 + `pytest tests/` 全绿。

#### 验证方式
- AC-04（数据通路只消费不重采）的"helper 单测覆盖 entries 缺失/部分缺失/全齐"先在 chg-01 立底座（chg-03 再扩 stage 维度）；本 chg pytest 至少 5 条新用例。
- AC-05（State 层校验不退化）的"req 维度自检不退化"：chg-01 自身完成时本 req（req-43）的 usage-log.yaml entries 数 ≥ 主 agent 实际派发次数 - 容差。
- 端到端活证：`grep -c "^- ts:" .workflow/flow/requirements/req-43-交付总结完善/usage-log.yaml ≥ 4`。

#### 回滚方式
`git revert` chg-01 的所有 commit（helper 改动 + scaffold mirror + sug 状态翻转）；usage-log.yaml 文件无需删除（追加模式，旧 entries 兼容）。

#### scaffold_v2 mirror 同步范围
`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` + `base-role.md` 两份与本仓库 `.workflow/context/roles/` 同名文件保持 diff = 0（按 harness-manager.md 硬门禁五）。`workflow_helpers.py` 不在 scaffold mirror 范围（CLI 源码非 scaffold）。

#### 契约 7（id + title）注意点
- chg-01 的 change.md / plan.md 首次引用 req-43（交付总结完善）/ chg-01（record_subagent_usage 派发链路接通 + 端到端 dogfood）/ sug-25（record_subagent_usage 派发链路真实接通）/ chg-08（硬门禁六扩 TaskList + 进度条 + stdout + 提交信息）必带 title。
- 提交信息：`fix: chg-01（record_subagent_usage 派发链路接通 + 端到端 dogfood）...` 必带 ≤ 15 字描述。

### 6. chg-02 plan 大纲

#### 目标
解决 AC-06：`harness next` / `harness archive` 等 stage 流转 CLI 入口在写 `stage_timestamps[new_stage].entered_at` 时**同时**写 `stage_timestamps[prev_stage].exited_at`；解决 req-41 实测遗留点 (b)（runtime 与 req yaml `stage` 字段不同步、testing/acceptance/done 的 entered_at 漏写）。

#### 影响文件列表
- `src/harness_workflow/workflow_helpers.py::update_state_yaml_stage`（line ~5380-5435）：当前只在 `_STAGE_TIMESTAMP_WHITELIST` 内写 `existing[new_stage] = now`，需要新增 prev_stage exited_at 写入逻辑（从 runtime.yaml 或调用方传入读 prev_stage）。
- `src/harness_workflow/workflow_helpers.py::archive_requirement`（line ~5990）：归档时若 `stage` 还停在非 done，先补齐流转链上漏写的 entered_at + exited_at。
- `src/harness_workflow/cli.py`：`harness next` / `harness archive` 命令路径在调 `update_state_yaml_stage` 时多传一个 `prev_stage` 参数。
- `tests/test_stage_timestamps.py`（新增）：覆盖「跳跃流转」（如直接从 planning 跳 done） + 「runtime 与 req yaml 同步」两个反例。
- 不动 scaffold_v2 mirror（纯 CLI 源码）。

#### 实施步骤
1. 改 `update_state_yaml_stage` 签名加可选 `prev_stage: str | None = None`；写 new_stage.entered_at 时若 prev_stage 非空且 stage_timestamps[prev_stage] 已有 entered_at，写 stage_timestamps[prev_stage].exited_at = now（新 schema：从 `{stage: entered_at_str}` 升级到 `{stage: {entered_at, exited_at}}` 或同级新增 `{stage}_exited_at` 键——选后者避免破坏向后兼容）。
2. CLI 层：`harness next` / `harness archive` 路径调 update_state_yaml_stage 前先从 runtime.yaml 读当前 stage 作为 prev_stage 传入。
3. archive_requirement：归档前扫 stage_timestamps，若 done.entered_at 缺失补当前时间作 done.entered_at + 上一 stage.exited_at。
4. pytest 反例覆盖：跳跃流转、runtime↔req yaml 不同步两 case。
5. `harness validate --human-docs` exit 0 + `pytest tests/` 全绿。

#### 验证方式
- AC-03：跑本 req（req-43）端到端，检查最终 req yaml 的 stage_timestamps 含所有经历过 stage 的 entered_at + exited_at。
- AC-06：新增 pytest case 覆盖跳跃流转 + runtime↔req yaml 同步两反例。
- 反向自证：grep req-43 自身的 `stage_timestamps`，每个 stage 都有 entered_at；最后一 stage 的 exited_at 至少有任务完成时间替代。

#### 回滚方式
`git revert` chg-02 的所有 commit；旧 schema（`{stage: entered_at_str}`）天然向后兼容，不需要数据迁移。

#### scaffold_v2 mirror 同步范围
无（纯 CLI 源码，不进 scaffold）。

#### 契约 7（id + title）注意点
chg-02 的 change.md / plan.md 首次引用 req-43（交付总结完善）/ chg-02（per-stage 时间字段补齐：流转点联动写齐 entered_at + exited_at）/ AC-06 必带描述；提交信息 `feat: chg-02（per-stage 时间字段补齐：流转点联动写齐 entered_at + exited_at）`。

### 7. chg-03 plan 大纲

#### 目标
解决 AC-02：`done_efficiency_aggregate` helper 扩 stage 维度聚合；`done.md` 模板把「各阶段耗时分布」+「各阶段 token 分布」**合并为单表**（OQ-4），列固定为 `stage / role / model / input_tokens / output_tokens / cache_read_input_tokens / cache_creation_input_tokens / total_tokens / tool_uses`，按 stage 排序。

#### 影响文件列表
- `src/harness_workflow/workflow_helpers.py::done_efficiency_aggregate`（line 2794-2965）：返回值新增 `stage_role_rows: list[dict]` 字段，按 stage × role × model group by；保留 `role_tokens` / `stage_durations` 字段（向后兼容，但 done.md 模板渲染不再用）。
- `.workflow/context/roles/done.md` `## 对人文档输出` 模板（line 100-149）：删除「各阶段耗时分布」+「各阶段 token 分布」两表，新增单表「各阶段切片（stage × role × model × token × tool_uses）」；字段顺序固定。
- `tests/test_done_efficiency_aggregate.py`（新增 / 扩）：覆盖 stage 维度聚合的 entries 缺失/部分缺失/全齐 三 fixture。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`：scaffold mirror 同步。
- `src/harness_workflow/assets/templates/`（如有 done 模板渲染相关 .tmpl 文件需同步检查）。

#### 实施步骤
1. 改 `done_efficiency_aggregate` 加 stage 维度 group by 逻辑：以 entry.stage 作为 key，按 (stage, role, model) 三键 group by，聚合 token 七字段。
2. 输出新字段 `stage_role_rows: list[{stage, role, model, input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens, total_tokens, tool_uses}]`，按 stage_order + total_tokens desc 排序。
3. 改 `done.md` 模板：删两表，新单表；字段顺序按 OQ-4 / AC-02 固定；保留「总耗时」「总 token」两段不动。
4. 新增 / 扩 pytest（test_done_efficiency_aggregate.py）至少 6 条 case 覆盖 entries 缺失/部分缺失/全齐 × stage 切片维度。
5. scaffold mirror 同步 `done.md`。
6. `harness validate --human-docs` exit 0 + `pytest tests/` 全绿。

#### 验证方式
- AC-02：本 req 自身 done 阶段产出的「交付总结.md」§效率与成本段必含单表，每经历过的 stage 至少 1 行非空。
- AC-04 helper 单测：「entries 缺失/部分缺失/全齐」三 fixture 全过。
- 反向自证：跑 helper 输入 req-43 自身的 usage-log.yaml（chg-01 真接通后），返回的 stage_role_rows 至少含 planning/executing/testing/acceptance/done 五 stage 行。

#### 回滚方式
`git revert` chg-03 的所有 commit；旧 done.md 模板与 helper 旧返回字段（`stage_durations` + `role_tokens`）保留向后兼容，可单独回滚 done.md 模板而不动 helper。

#### scaffold_v2 mirror 同步范围
`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` 与 `.workflow/context/roles/done.md` diff = 0。

#### 契约 7（id + title）注意点
chg-03 的 change.md / plan.md 首次引用 req-43（交付总结完善）/ chg-03（per-stage token 聚合：done_efficiency_aggregate helper 扩 stage 维度 + 单表渲染）/ chg-05（done.md 交付总结模板扩 §效率与成本）（req-41 历史 chg）必带描述。

### 8. chg-04 plan 大纲

#### 目标
解决 AC-01 / AC-07 的 bugfix 维度：bugfix 完成时新增 `bugfix-交付总结.md` 全套对人产物路径；模板复用 req done 框架但精简（删 chg 段、合并 testing+acceptance 为「修复验证」段，OQ-2）；`harness validate --human-docs` 校验扩 bugfix 维度。bugfix 流程现在是 `regression → executing → testing → acceptance`，无 done stage——本 chg 决定是否新增 done stage 还是把交付总结产出绑在 acceptance 后置 hook（default-pick：绑在 acceptance 完成后由主 agent 直接产出，不新增 stage，避免 bugfix 流程结构变动）。

#### 影响文件列表
- `.workflow/flow/repository-layout.md` §2 白名单：新增 `bugfix-交付总结.md` 类型行；§3 落位约定 `artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/bugfix-交付总结.md`。
- `.workflow/flow/stages.md` `## Bugfix 快速流转图`：补 acceptance 完成后由主 agent 产出 `bugfix-交付总结.md` 的说明（不改流转图）。
- `.workflow/context/roles/done.md` 或新增 `.workflow/context/roles/bugfix-done.md`：bugfix 收尾模板段（最小字段 + 「修复验证」合并段）；default-pick：扩 done.md 而非新文件，复用六层回顾框架（done.md 内分 req / bugfix 两模板分支）。
- `src/harness_workflow/workflow_helpers.py`：新增 `bugfix_done_efficiency_aggregate` 或复用 `done_efficiency_aggregate`（chg-03 helper 已 stage 切片，复用即可，仅 entries 路径换为 `.workflow/flow/bugfixes/{bugfix-id}-{slug}/usage-log.yaml`，但实测本仓库无此路径——bugfix usage-log 落位需新决定，default-pick 落到 `.workflow/state/sessions/bugfix-{id}/usage-log.yaml` 与 chg-01 task_type=bugfix 配套）。
- `src/harness_workflow/workflow_helpers.py::validate_human_docs`：bugfix 维度校验扩——`bugfix-交付总结.md` 缺失阻断 acceptance → 完成判定 / `harness archive`。
- `tests/test_bugfix_delivery_summary.py`（新增）：覆盖 bugfix 完成时 `bugfix-交付总结.md` 产出 + `harness validate --human-docs` 阻断校验。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` + `.workflow/flow/repository-layout.md` + `.workflow/flow/stages.md`：scaffold mirror 同步。

#### 实施步骤
1. `repository-layout.md` §2 白名单加 `bugfix-交付总结.md`；§3 落位定义 `artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/bugfix-交付总结.md`。
2. `done.md` 模板段加 bugfix 分支：保留六层回顾 + 总耗时 + 总 token + stage × role × model 单表；删「chg 段」，合并 testing+acceptance 为「修复验证」段。
3. helper：复用 `done_efficiency_aggregate`，新增可选参数 `task_type="bugfix"` 切换 entries 读取路径（与 chg-01 task_type 配套）。
4. `validate_human_docs` 加 bugfix 维度扫描——若 bugfix-id 已 acceptance pass 但缺 `bugfix-交付总结.md`，exit ≠ 0。
5. 新增 pytest 至少 4 条 case：bugfix-交付总结.md 产出 / 缺失阻断 / stage × role × model 单表渲染 / 「修复验证」合并段。
6. scaffold mirror 同步 + `harness validate --human-docs` exit 0 + `pytest tests/` 全绿。

#### 验证方式
- AC-01（bugfix 维度）：跑历史 bugfix-1/2/3/4 dogfood（手工补交付总结） 或下一个新 bugfix 端到端验证。
- AC-07（bugfix 维度）：`harness archive` 对 bugfix 类型与 req 类型同等校验，缺 `bugfix-交付总结.md` 阻断。
- 反向自证：用 chg-01 真接通的 bugfix usage-log（若 chg-04 期间内有新 bugfix）跑 helper，返回 stage 切片表非空。

#### 回滚方式
`git revert` chg-04 的所有 commit；historic bugfix-1~4 的归档目录不做回填（豁免，与 req-41 legacy fallback 一致）。

#### scaffold_v2 mirror 同步范围
`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/flow/stages.md` 与本仓库同名文件 diff = 0。

#### 契约 7（id + title）注意点
chg-04 的 change.md / plan.md 首次引用 req-43（交付总结完善）/ chg-04（bugfix 引入 bugfix-交付总结.md 全路径）/ bugfix-1（harness update --check 等 flag 被角色触发吞了）/ bugfix-4（harness install 升级清理：旧 layout / .bak / schema 不一致）必带描述。

### 9. chg-05 plan 大纲

#### 目标
sug 直接处理路径产出 3 段轻量交付总结（OQ-1）+ State 层契约扩三类任务（base-role.md `## done 六层回顾 State 层自检`）+ scaffold_v2 mirror 收口 + 整 req dogfood 自证。AC-01 / AC-05 / AC-07 全部覆盖完整收口。

#### 影响文件列表
- `.workflow/flow/repository-layout.md` §2 白名单：新增 `sug 交付总结.md`（轻量版）类型行；§3 新增 `artifacts/{branch}/suggestions/sug-NN-{slug}/` 子树落位定义。
- `src/harness_workflow/workflow_helpers.py::create_suggestion / suggest_apply / suggest_archive`：sug `--apply`（不转 req 直接处理） / `--archive` / `--reject` 路径触发产出 `artifacts/{branch}/suggestions/sug-NN-{slug}/交付总结.md`（轻量 3 段：建议是什么 / 处理结果 / 后续）。
- `src/harness_workflow/workflow_helpers.py::validate_human_docs`：sug 维度校验扩——sug 已 applied/archived/rejected 但缺交付总结 → exit ≠ 0（豁免：sug→req 转化路径由 req 兜底，无需独立产出）。
- `.workflow/context/roles/base-role.md` `## done 六层回顾 State 层自检`：把「读取 .workflow/state/sessions/{req-id}/usage-log.yaml」改写为「按 task_type 读 req/bugfix/sug 三类 usage-log.yaml」；State 层校验从「req 维度」扩到三类任务。
- `.workflow/context/roles/done.md`：扩说明文字补"三类任务级 usage-log entries 数 ≥ 派发次数 - 容差"。
- `tests/test_suggestion_delivery_summary.py`（新增）：覆盖 sug `--apply` 不转 req / `--archive` / `--reject` 三场景产出轻量交付总结 + 校验阻断。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` + `done.md` + `.workflow/flow/repository-layout.md`：scaffold mirror 同步。
- `done-report.md` 改进建议提取：req-43 自身 done 阶段做整 req 三类活证 dogfood。

#### 实施步骤
1. `repository-layout.md` §2 白名单 + §3 落位 `artifacts/{branch}/suggestions/sug-NN-{slug}/交付总结.md`。
2. `create_suggestion` / `suggest_apply` / `suggest_archive` helper 在状态翻转后自动产出轻量 3 段交付总结模板（template 内嵌）。
3. `validate_human_docs` 加 sug 维度扫描。
4. `base-role.md` `## done 六层回顾 State 层自检` 改写从 req 维度扩到三类任务（按 task_type 读 entries）。
5. 新增 pytest 至少 5 条 case：sug `--apply` 直接处理产出 / sug→req 转化不重复 / sug `--archive` 产出 / sug `--reject` 产出 / 校验阻断。
6. scaffold mirror 同步（base-role.md + done.md + repository-layout.md）+ `harness validate --human-docs` exit 0 + `pytest tests/` 全绿。
7. 整 req dogfood：req-43 完成时三类（req-43 本身 + bugfix-NN 若有 + sug-NN 若有）的交付总结全产出，State 层校验全过。

#### 验证方式
- AC-01（完整覆盖）：req-43 完成时三类任务级工作项的「交付总结.md」/「bugfix-交付总结.md」/「sug 交付总结.md」全产出，`harness validate --human-docs` 三类同等校验全过。
- AC-05（State 层不退化）：base-role.md 文字契约 + 自检脚本扩三类任务后，本 req 三类校验全过。
- AC-07（三类一致）：`harness archive` 对 req / bugfix / sug 三类任务的对人 folder 处理一致——原位保留 + 机器型迁 `.workflow/flow/archive/`（沿用 req-42 契约）。

#### 回滚方式
`git revert` chg-05 的所有 commit；historic sug 不做回填（与 req-41/42 legacy fallback 一致）。

#### scaffold_v2 mirror 同步范围
`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` + `done.md` + `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 与本仓库同名文件 diff = 0。

#### 契约 7（id + title）注意点
chg-05 的 change.md / plan.md 首次引用 req-43（交付总结完善）/ chg-05（sug 轻量交付总结 + State 层契约扩三类任务 + 收口）/ sug-25（record_subagent_usage 派发链路真实接通）/ req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ req-42（archive 重定义：对人不挪 + 摘要废止）必带描述。

### 10. 风险登记（5 条）

| 风险 | 描述 | 缓解方案 |
|------|------|---------|
| **R-1（chg-01 接通后历史 reg 路径回归）** | `record_subagent_usage` 派发链路真接通后，可能在已归档 req 路径（req-02 ~ req-40 走 state-flat / legacy）触发新校验失败 | helper 内 `if req_id 不在活跃需求范围则 noop`；done 六层回顾 State 层自检对历史归档 req 豁免追溯（与 req-41 legacy fallback 一致） |
| **R-2（chg-02 schema 升级破坏既有 stage_timestamps）** | 从 `{stage: entered_at_str}` 升级到含 exited_at 后，已归档 req yaml 旧 schema 不兼容 | 选 fallback 兼容方案：新增 `{stage}_exited_at` 同级键而非嵌套字典；helper 同时读两种 schema |
| **R-3（chg-03 done.md 模板改变影响 reg 路径已归档 req）** | done.md 模板「各阶段耗时分布」+「各阶段 token 分布」两表改为单表后，若有人重跑历史 req 的 done 阶段（regression 重新触发）模板渲染差异 | 模板字段顺序固定不变，只是表合并；旧两字段在 helper 返回值保留作向后兼容；done.md 加注「req-43+ 起统一单表，req-41/42 历史交付总结按旧两表保留不重渲」 |
| **R-4（chg-04 bugfix 流程无 done stage 增加复杂度）** | bugfix 流程当前是 `regression → executing → testing → acceptance` 无 done，强加交付总结产出可能要求新 stage 或 acceptance 后置 hook | default-pick：不新增 stage，由主 agent 在 acceptance pass 后直接产出 `bugfix-交付总结.md`（绑在 `harness archive` 前的 pre-hook）；保留 bugfix 流转图不动 |
| **R-5（chg-05 sug 直接处理路径文档膨胀）** | sug 轻量化交付总结若每条 sug 都强产出，suggestions 子树文档会快速膨胀 | 模板压到 3 段 ≤ 1/3 页；sug→req 转化路径不重复出（OQ-1 已确认）；只对 `--apply` 不转 req / `--archive` / `--reject` 三类产出，pending 状态不产出 |

### 11. requirement.md 修正建议（不直接改）

requirement.md 经审视无事实错误，无需修正。AC 7 条均与现有契约兼容；split rules 与本 stage 拆分一致。

### 12. planning stage 抽检反馈

- **抽检产物**：req-43（交付总结完善）/ planning stage chg 拆分（5 条 chg）+ 5 份 plan.md 大纲 + 5 条风险 + 拆分图 + 抽检反馈 = 本 session-memory.md `## planning stage` 全段。
- **质量评分**：B（持平）。
- **退化点明细**：（持平档）拆分原则有 3 条主辅线明示（统计字段 / 任务类型 / 数据通路前置）；chg 列表 5 条带 AC 覆盖矩阵 + 依赖 + 估算粒度三列；每个 chg 大纲 6 项齐全；scaffold_v2 mirror 同步范围明示（chg-01 / chg-03 / chg-04 / chg-05 共 5 个 mirror 文件）；OQ-1 ~ OQ-5 五条 default-pick 全部锁定到 chg 大纲对应字段（OQ-1 → chg-05 / OQ-2 → chg-04 / OQ-3 → chg-03 模板字段 / OQ-4 → chg-03 单表 / OQ-5 → chg-01 task_type 参数）；契约 7 与硬门禁六描述要求逐 chg 标注。无明显退化点。
- **是否触发 regression 回调 B**：否。
- **抽检人 + 时间 + req 范围**：subagent-self / 2026-04-25 / req-43。

### 13. default-pick 决策清单（本 stage 内按默认推进的争议点）

> 同阶段不打断硬门禁四 + stage-role.md 约定，stage 内争议按 default-pick 推进、stage 流转前 batched-report。

- **D-1（sug-25 是否吸收进 chg-01）**：default-pick = A（吸收）。理由：sug-25 仍 pending 且是后续 4 chg 的数据底座，不接通则数据恒空，所有渲染验证全失效；并入第一 chg 最小化阻塞。
- **D-2（chg-04 bugfix 是否新增 done stage）**：default-pick = B（不新增 stage，绑 acceptance 后置 hook 由主 agent 产出）。理由：bugfix 流程结构变动需大改 stages.md / runtime 流转，风险大且非必要；后置 hook 模式与 req-42 archive 复用同样的 helper 路径。
- **D-3（chg-04 bugfix done 模板独立文件 vs. 扩 done.md）**：default-pick = B（扩 done.md 内 req/bugfix 两分支模板，不另起新 role.md 文件）。理由：复用六层回顾框架 + 同一 helper 减小维护面；独立文件会复制大量字段定义。
- **D-4（chg-02 stage_timestamps schema 升级方式）**：default-pick = B（同级新增 `{stage}_exited_at` 键，不嵌套字典）。理由：保持向后兼容，已归档 req yaml 旧 schema 不破坏；helper 读取逻辑改 1 行。
- **D-5（chg-03 单表替换两表 vs. 并列两表）**：default-pick = A（替换两表为单表，OQ-4 已确认）。理由：用户已确认 OQ-4，单表既支持「按 stage 看」也支持「按 role × model 看」（用户自行 group by 阅读），表头一致便于 helper 实现。

### 14. 待处理捕获问题（职责外）

- 无（本 stage 无超出 analyst 职责的捕获问题）。

### 15. 给主 agent 的关键确认点（≤ 1 条）

- **拆分提案是否同意**：5 个 chg、依赖关系 chg-01 → (chg-02 || chg-03) → chg-04 → chg-05、chg-01 吸收 sug-25。是否按本拆分调 `harness change` 5 次创建 chg 目录。

---

## executing stage ✅

### 0. 自我介绍 + 模型自检（Step 7.5）

我是 Subagent-L1（executing 角色，claude-sonnet-4-6），承接 req-43（交付总结完善）的 executing stage 端到端实现任务。

**模型一致性自检**：expected_model = sonnet（Sonnet 4.6），role-model-map.yaml 中 `roles.executing: sonnet`，一致 ✅。

### 1. 实现总览（5 chg 全部完成）

| chg | 状态 | 测试 | 核心产出 |
|-----|------|------|---------|
| chg-01（接通 record_subagent_usage 派发链路） | ✅ | 9/9 | task_type 参数、harness-manager 留痕、sug-25 applied、mirror |
| chg-02（补齐 stage 时间戳） | ✅ | 7/7 | _sync_stage_to_state_yaml prev_stage、_backfill_done_timestamps |
| chg-03（per-stage 单表渲染） | ✅ | 8/8 | stage_role_rows、done.md 单表模板、test_done_subagent 契约同步 |
| chg-04（bugfix-交付总结.md） | ✅ | 9/9 | BUGFIX_LEVEL_DOCS、done.md bugfix 精简模板、repo-layout 白名单 |
| chg-05（sug 轻量交付总结 + State 扩三类） | ✅ | 10/10 | _create_sug_delivery_summary、_collect_suggestion_items、base-role 三类任务 |

**新增测试：43 条，全部通过 ✅**

### 2. 全回归结果

```
2 failed（pre-existing）, 577 passed, 52 skipped in 72.76s
```

- 新增失败：0（chg-03 导致的 test_done_subagent 契约差异已在 executing stage 内修复）
- 预存失败：test_smoke_req28（readme hint）+ test_smoke_req29（human docs checklist）——与本 req 无关

### 3. scaffold_v2 mirror 同步（5 文件，diff = 0）

| 文件 | chg |
|------|-----|
| harness-manager.md | chg-01 |
| base-role.md | chg-01 + chg-05 |
| done.md | chg-03 + chg-04 + chg-05 |
| repository-layout.md | chg-04 + chg-05 |

### 4. 关键边界判断（executing stage 内）

- **test_done_subagent 契约同步**：原断言四段（两旧表名）vs 新单表，属测试契约升级而非功能退化。测试更新后语义等价 ✅。
- **_collect_suggestion_items**：只检 `交付总结.md`（sug 轻量版），不套用 req 级全字段校验 ✅。
- **sug→req 转化路径豁免**：`apply_suggestion` 不调 `_create_sug_delivery_summary`（由对应 req done 阶段兜底）✅。

### 5. 给主 agent 的汇报（≤ 280 字）

req-43（交付总结完善）executing stage 完成：5 chg 端到端实现，43 条新测试全过，全回归 577 passed / 2 pre-existing fail。主要产出：① chg-01 record_subagent_usage 接 task_type + sug-25 applied；② chg-02 stage timestamps 补 entered_at/exited_at；③ chg-03 done_efficiency_aggregate 加 stage_role_rows 单表 + done.md 模板更新；④ chg-04 bugfix-交付总结.md 全路径 + validate_human_docs 扩 bugfix 维度；⑤ chg-05 sug 3 段轻量交付总结 + State 层扩三类任务。scaffold_v2 mirror 4 文件 diff=0。

---

## planning stage（plan.md 落地）

### 0. 自我介绍 + 模型自检（Step 7.5）

我是分析师（analyst / opus），承接 req-43（交付总结完善）的 planning stage 续跑任务——为 5 个 chg 各填 plan.md（覆盖空模板，含 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 新契约要求的 §测试用例设计 段）。

**模型一致性自检（Step 7.5）**：runtime 不暴露 model self-introspection；按降级路径处理 —— briefing 内 `expected_model: opus`（Opus 4.7），与 `.workflow/context/role-model-map.yaml` 中 `roles.analyst: opus` 一致。本 subagent 未能自检 model 一致性，briefing 期望 = opus（Opus 4.7），按"未自检"留痕，不阻塞。

### 1. 5 份 plan.md 落地状态

| chg | plan.md 路径 | 六段齐 | §测试用例数 | 核心改动面 |
|-----|------------|-------|------------|-----------|
| chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25）） | `.workflow/flow/requirements/req-43-交付总结完善/changes/chg-01-接通-record_subagent_usage-派发链路-吸收-sug-25/plan.md` | ✅ | 8 | helper 加 task_type + harness-manager.md §3.6 Step 4 升级可观测留痕 |
| chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳） | `.../chg-02-.../plan.md` | ✅ | 7 | _sync_stage_to_state_yaml 加 prev_stage 参数 + schema 同级新增 `{stage}_exited_at` |
| chg-03（per-stage 合并到 stage × role × model 单表渲染） | `.../chg-03-.../plan.md` | ✅ | 8 | done_efficiency_aggregate 加 stage_role_rows + done.md 模板单表 |
| chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版）） | `.../chg-04-.../plan.md` | ✅ | 8 | repository-layout.md §2/§3.2/§5 + done.md bugfix 分支 + helper task_type="bugfix" 路径 |
| chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务） | `.../chg-05-.../plan.md` | ✅ | 8 | sug 子树 + create_suggestion 状态翻转钩子 + base-role.md State 层扩三类 |

**§测试用例总数 = 39 条**（远超完成判据 ≥ 25 阈值），P0 = 24 / P1 = 13 / P2 = 2。

### 2. 关键边界判断（plan.md 落地阶段新增 / 锁定）

- **B-1（chg-02 schema 升级走 D-4 同级键）**：`stage_timestamps` 同级新增 `{stage}_exited_at` 键（如 `planning_exited_at`），不嵌套字典；保持 helper 读取逻辑改最少（单行）+ 历史归档 req yaml 旧 schema 不破坏。
- **B-2（chg-04 bugfix 不新增 done stage，绑 acceptance 后置 hook）**：D-2 default-pick 锁定；bugfix 流转图（`regression → executing → testing → acceptance`）不动，由主 agent 在 acceptance pass 后绑 `harness archive` pre-hook 直接产出 `bugfix-交付总结.md`。
- **B-3（chg-04 bugfix 模板复用 done.md 内分支，不另起新 role.md）**：D-3 default-pick 锁定；扩 done.md `## 对人文档输出` 段加 bugfix 分支（保留六层回顾框架 + 复用 chg-03 单表 + 删 chg 段 + 合并 testing+acceptance 为「修复验证」段）。
- **B-4（chg-05 sug → req 转化路径不重复产出）**：OQ-1 兜底语义——sug → req 转化路径由对应 req 的 done 阶段交付总结兜底；frontmatter `status: converted-to-req` 标识下豁免 sug 自身 `交付总结.md` 校验。
- **B-5（scaffold_v2 mirror 范围明示，五大 mirror 文件总览）**：chg-01 改 2 文件（harness-manager.md + base-role.md）；chg-02 不动 mirror（CLI 源码）；chg-03 改 1 文件（done.md）；chg-04 改 2 文件（done.md + repository-layout.md）；chg-05 改 3 文件（base-role.md + done.md + repository-layout.md）。done.md / base-role.md / repository-layout.md 跨 chg 反复改写，**chg 间需顺序合并并按依赖落地**（chg-03 改 done.md 模板段 → chg-04 加 bugfix 分支 → chg-05 加 State 层扩三类文字），避免 mirror diff 冲突。
- **B-6（regression_scope 全部 targeted）**：5 个 chg 均按 default targeted 标记，无破坏面广到需 full 回归的 chg；testing 阶段按各 plan §测试用例设计直接消费即可。

### 3. planning stage 抽检反馈（与首次抽检对照）

- **抽检产物**：5 份 plan.md（六段齐：目标 / 影响文件列表 / 实施步骤 / 测试用例设计 / 验证方式 / 回滚方式 + scaffold mirror + 契约 7）+ 本段 session-memory 追加。
- **对照首次抽检**：首次抽检（§12）评分 B（持平），主要落地 chg 拆分大纲；本次为 plan.md 落地阶段，**评分 A（提升）**，理由：
  - **§测试用例设计段**全 5 chg 落齐，每条用例含用例名 / 输入 / 期望 / 对应 AC / 优先级 5 字段（bugfix-6 新契约硬要求满足）；
  - 用例数 39 条远超 ≥ 25 阈值（chg-01 / chg-03 / chg-04 / chg-05 各 8 条；chg-02 7 条，与"chg-02 / chg-05 偏少"预期相反——chg-02 反而比偏少多 2 条，因 stage_timestamps 反例覆盖面广）；
  - 影响文件列表精确到 line 号 / 函数名（如 `_sync_stage_to_state_yaml(line 5406-5471)` / `done_efficiency_aggregate(line 2797-2965)` / `validate_human_docs._collect_bugfix_items(line 373)`），testing 阶段可直接 grep 落点；
  - 6 条边界判断（B-1 ~ B-6）显式锁定，无悬念决策遗留。
- **退化点明细**：（提升档）每个 plan.md 自包含、testing 直接消费；scaffold mirror 范围按 chg 明示且跨 chg 顺序明示（B-5）；契约 7 注意点逐 chg 落首次引用 id+title 与提交信息样本。无明显退化点。
- **是否触发 regression 回调 B**：否。
- **抽检人 + 时间 + req 范围**：subagent-self / 2026-04-25 / req-43 planning stage 续跑。

### 4. default-pick 决策清单（本次续跑内按默认推进的争议点）

- 无新增 default-pick 决策。本次续跑严格执行用户已锁定的 5 条 OQ default-pick + 5 条 D-X（D-1 ~ D-5），plan.md 直接落地未引入新争议。

### 5. 待处理捕获问题（职责外）

- 无（本次续跑无超出 analyst 职责的捕获问题）。

### 6. 给主 agent 的关键确认点（≤ 1 条）

- **5 份 plan.md 是否同意**：六段齐、§测试用例设计段共 39 条用例、5 大 mirror 文件按 chg 归并（B-5 跨 chg 顺序）。是否同意推进 `harness next` 让 analyst 完成 planning stage 退出（user 拍板点）。

### 7. ✅ 完成判据自检

- [x] 5 份 plan.md 六段齐（含 §测试用例设计）—— 5/5 覆盖 ✅
- [x] §测试用例设计 总用例数 ≥ 25 —— 实际 39 条 ✅
- [x] session-memory `## planning stage（plan.md 落地）` 段含抽检反馈 —— 本段 §3 ✅
- [x] 给主 agent 的最终消息 ≤ 280 字 —— 见汇报 ✅


