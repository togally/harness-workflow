# Requirement

## 1. Title

交付总结完善

## 1.5 Background

**用户原话（中文一字不差）**：

> 1.bug 和 需求 以及 建议 都需要出局交付总结，简单来说只要是任务就要总总结
> 2.交付总结内的每个阶段token使用量 和 部分时间是没有统计到的

（推测："出局" = "输出"；"总总结" = "总结"。）

**现状（什么有）**：

- req（需求）：done 阶段会产出 `artifacts/{branch}/requirements/{req-id}-{slug}/交付总结.md`，含「需求是什么 / 交付了什么 / 结果是什么 / 后续建议 / §效率与成本」五段，§效率与成本由 `done.md` Step 6.x 聚合 `usage-log.yaml` + `stage_timestamps`。
- 数据通路：`harness-manager.md` §3.6 Step 4 已立硬门禁——主 agent 每次 Agent 工具返回必调 `record_subagent_usage(root, role, model, usage, req_id, stage, chg_id, reg_id)`，写入 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml`，字段含 input/output/cache_read/cache_creation/total_tokens + tool_uses + duration_ms。
- 兜底：done 六层回顾 State 层强校验「usage-log entries 数 ≥ 派发次数 - 容差」（base-role.md `## done 六层回顾 State 层自检`）。

**现状（什么缺）**：

- **bugfix（bug）**：只产出 `bugfix.md` / `test-evidence.md` / `test-report.md` / `session-memory.md`，**没有**等价的「交付总结」对人产物，bugfix 完成后用户无法一屏看到「修了啥 / 影响面 / 残留 / 效率成本」。
- **sug（建议）**：sug 通过 `harness suggest --apply` 转化为 req 或独立处理，本身**没有**交付总结产出口径；sug 直接处理（非转 req）路径完全无对人产出。
- **统计完备性缺口**：
  - **per-stage token 缺**：`done.md §效率与成本` 模板已有「各阶段 token 分布」表（role × model × total_tokens × tool_uses），但**未按 stage 聚合**——现行 `done_efficiency_aggregate` 只按 role × model 维度聚合，丢失「stage 维度」切片。req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ req-42（archive 重定义：对人不挪 + 摘要废止）两份交付总结实测均出现 `⚠️ 无数据` / 仅 1 条 entry 的情况，反证消费侧（渲染层）即便有数据也未按 stage 切。
  - **部分 stage 时间缺**：req-41 自身 `stage_timestamps` 缺 testing / acceptance / done 三个 stage 的 `entered_at`（见 req-41 交付总结 line 53-59 实证），runtime.yaml 已切 done 但 req yaml `stage` 字段还停 `executing`；`harness next` / `harness archive` 流转点未联动写齐 stage_timestamps。

**触发原因**：用户在 req-42（archive 重定义：对人不挪 + 摘要废止） 完成后明确提出，要求对人交付总结的「任务覆盖面」与「统计字段完备性」两个维度同时补齐。

## 2. Goal

- **任务级交付总结统一产出**：req / bugfix / sug 三类任务级工作项**完成时**全部按统一对人模板产出「交付总结」，字段口径一致。
- **per-stage 统计字段补齐**：交付总结的「§效率与成本」段必须呈现**所有 stage** 的 token 使用量（input/output/cache_read/cache_creation/total + tool_uses + duration_ms 至少 token 维度齐全）+ **所有 stage** 的时间统计（entered_at / exited_at / duration_s），不得有 stage 缺漏。
- **数据通路不重复采集**：消费已有 `record_subagent_usage` + `stage_timestamps` 数据，**不**新设采集通道；sug-25（record_subagent_usage 派发链路真实接通） 是前置依赖，本 req 假设其落地或与本 req 并行落地。

## 3. Scope

### 3.1 IN（范围内）

- **任务覆盖面**：
  - req 完成（done 阶段）继续产出 `交付总结.md`（既有不动）。
  - **bugfix 完成**新增产出对应「交付总结」对人产物（落位与文件名见 §3.1.4）。
  - **sug 完成**：纳入"sug 直接处理（不转 req）"路径的交付总结产出（详见 OQ-1，default-pick 倾向轻量化）。
- **统计字段（per-stage 维度）**：
  - 交付总结 §效率与成本段新增「按 stage 切片」表，列：stage / entered_at / exited_at / duration_s / 该 stage 内调用的 role × model × total_tokens × tool_uses 聚合行。
  - 现有「按 role × model 聚合」表保留（不破坏既有契约）。
  - 字段顺序固定，新表插入位置统一在「各阶段耗时分布」之后、「各阶段 token 分布（role × model）」之前或合并为单表（见 OQ-4）。
- **数据通路对接**：
  - 消费侧（渲染层）：扩展 `done_efficiency_aggregate` helper 增加 stage 维度聚合，按 `usage-log.yaml` entries 的 `stage` 字段 group by。
  - 时间字段补齐：`harness next` / `harness archive` / 任何引发 stage 流转的 CLI 入口必须联动写 `stage_timestamps[stage].entered_at` 与 `stage_timestamps[prev_stage].exited_at`，不得只写其一。
- **bugfix / sug 数据通路**：
  - bugfix 周期内 subagent 调用同样必调 `record_subagent_usage`，新增 `bugfix_id` 字段或复用 `req_id` 字段携带 bugfix-id（见 OQ-5），写入 `.workflow/flow/bugfixes/{bugfix-id}-{slug}/usage-log.yaml` 或既有 bugfix 工件目录。
  - sug 直接处理路径同上（若 OQ-1 决定产出）。
- **归档对接**：
  - 三类任务交付总结落位到对应 archive 子树（req → `artifacts/{branch}/archive/requirements/...`、bugfix → `artifacts/{branch}/archive/bugfixes/...`、sug → 见 OQ-1）。
  - `harness archive` 或等价归档命令对三类任务一致：对人 folder 原位保留、机器型工件迁 `.workflow/flow/archive/`（沿用 req-42（archive 重定义：对人不挪 + 摘要废止） 契约）。
- **State 层校验扩展**：
  - done 六层回顾 State 层自检从「req 维度」扩到三类任务，bugfix / sug 完成时同样校验「usage-log entries 数 ≥ 派发次数 - 容差」+「stage_timestamps 完整」。

### 3.2 OUT（范围外）

- **非任务级工作项的总结**：单条建议（未升格为任务）、临时讨论、experience 沉淀、动作日志（action-log.md）等不在本需求覆盖范围。
- **`record_subagent_usage` 自身的运行时接通**：属 sug-25（record_subagent_usage 派发链路真实接通） 范围；本 req 只对接消费侧，不重复修主 agent 派发链路。
- **跨项目 / 跨仓库统计聚合**：跨多个 repo 的 token / 时间统计、跨 req 横向对比报表、用量计费导出等不在本需求范围。
- **token 衍生指标计算**：cache 命中率、单位 token 成本、人时折算等衍生指标（见 OQ-3，默认仅落原始字段，衍生指标走渲染层或后续独立 req）。
- **done 阶段六层回顾流程本身的改造**：本 req 只在既有六层回顾框架内补字段，不改回顾流程结构、不动其他五层。
- **branch 命名规约 / artifacts 子树重构**：沿用 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） / req-42（archive 重定义：对人不挪 + 摘要废止） 已立的契约。
- **CLI 入口设计**：是否新增 `harness bugfix --done` / `harness suggest --done` 等显式收尾命令（见 OQ-2，default-pick 复用现有 done 阶段或归档命令的 pre-hook）。

## 4. Acceptance Criteria

- **AC-01（任务级覆盖完整）**：req（需求） / bugfix（bug） / sug（建议）三类任务级工作项，**完成时**全部能在 `artifacts/{branch}/{task-type}/{task-id}-{slug}/` 下找到对应「交付总结.md」文件，字段非空、模板一致。`harness validate --human-docs` 对三类任务同等校验，缺失即阻断归档推进。
- **AC-02（per-stage token 字段齐全）**：每份交付总结的「§效率与成本」段必须含「按 stage 切片」表，列至少包含 `stage` / `role` / `model` / `input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens` / `total_tokens` / `tool_uses`；每个该任务实际经历过的 stage 至少有 1 行（无数据按 `⚠️ 无数据` 标，禁止编造）。
- **AC-03（per-stage 时间字段齐全）**：每份交付总结含「各阶段耗时分布」表，列 `stage` / `entered_at` / `exited_at` / `duration_s`；任务实际经历过的所有 stage 至少有 `entered_at` 字段非空（最后一个 stage 的 `exited_at` 可由"任务完成时刻"替代）；缺漏即视为 AC-03 FAIL。
- **AC-04（数据通路只消费不重采）**：consume 既有 `record_subagent_usage` 写入的 `usage-log.yaml` 与既有 `stage_timestamps`，**不**在交付总结生成路径新建采集逻辑；helper 单测覆盖「entries 缺失/部分缺失/全齐」三种 fixture 输入。
- **AC-05（State 层校验不退化）**：done 六层回顾 State 层既有强校验（usage-log entries 数 ≥ 派发次数 - 容差）继续生效，并扩展到 bugfix / sug 两类任务；本 req 自身完成时三类校验全过。
- **AC-06（stage 流转点联动写齐时间戳）**：`harness next` / `harness archive` / 任何引发 stage 流转的 CLI 入口在落 `stage_timestamps[new_stage].entered_at` 时**同时**落 `stage_timestamps[prev_stage].exited_at`；新增 pytest 用例覆盖「跳跃流转」与「runtime 与 req yaml 同步」两个反例（参考 req-41 交付总结遗留点 (b)）。
- **AC-07（归档对接三类一致）**：`harness archive` 对 req / bugfix / sug 三类任务的「交付总结.md」处理一致——对人 folder 原位保留、机器型工件迁 `.workflow/flow/archive/{branch}/`；归档前的 `harness validate --human-docs` 对三类任务同等扫描，缺失阻断归档。

## 5. Split Rules

- 将需求拆分为可独立交付的变更（chg）。
- 每个 chg 覆盖一个清晰的交付单元。
- 需求完成时填写 `completion.md` 并记录项目启动验证成功。

**本 req 专属拆分提示**（仅供 analyst Part B 参考，本 stage 不拆 chg）：

- **按统计字段维度切**：可独立切 chg 处理「per-stage token 聚合（消费侧渲染）」与「per-stage 时间字段补齐（CLI 流转点联动）」两件事（前者纯渲染层、后者动 CLI），互不阻塞。
- **按任务类型切**：可独立切 chg 处理「bugfix 引入交付总结」与「sug 引入交付总结」两件事（bugfix 已有完整 done 等价路径，sug 需先决定 OQ-1）；req 既有路径只扩字段不重构。
- **按 State 层校验切**：扩展 base-role.md `## done 六层回顾 State 层自检` 到三类任务的契约改写可独立成 chg（纯文档契约，无代码动）。
- **数据通路前置**：sug-25（record_subagent_usage 派发链路真实接通） 是本 req 的隐含前置依赖；若 sug-25 在本 req 启动时未落地，本 req chg 拆分需明示「假设 sug-25 落地后端到端可用」或将 sug-25 内容并入本 req 第一个 chg。
