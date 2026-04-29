---
id: req-50
title: 现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口
created_at: 2026-04-29
operation_type: requirement
slug: 现有流程优化-文档-llm-only-重写-stage-整合-done-去-sug-入池-next-单入口
---

# Requirement

## 1. Title

现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口

## 2. Goal

优化现有 3 流程（requirement / bugfix / suggest）的文档形态、stage 编排、done 职责与 next 入口，将工作流"为人解释"惯性扭转为"为 LLM 服务"形态，降低单 req / bugfix 的文档书写与流转开销。**不新增任何新通道 / 新命令**（这是本 req 与 req-49 废弃方向的硬区分）。

### 2.1 实证活样本（uav bugfix-6）

- 路径：`/Users/jiazhiwei/claudeProject/uav/.workflow/flow/bugfixes/bugfix-6-事件时间允许负值-人工提报放宽飞行记录校验/`
- 实际改动：1 行代码（`event_time` 校验放宽）
- 实际产出：约 44KB 文档（bugfix.md / diagnosis.md / session-memory.md / test-evidence.md / acceptance-report.md / 交付总结.md / regression/required-inputs.md 等）
- 实际耗时：3+ 小时
- 用户预估：30 分钟
- **超支倍数：6 倍**

### 2.2 时间构成实证

| 耗时项 | 占比 |
|---|---|
| 文档书写（含"对人解释"段落，如背景 / 历史 / 用户原话引用 / 修订说明） | ~50% |
| subagent 角色加载（base-role + stage-role + 自身 role.md + 经验文件） | ~25% |
| 主 agent dispatch brief 编写（含上下文链 / task-context-index 等） | ~10% |
| 协议 / 合规扫描（harness validate / contract / 契约 7 自检） | ~10% |
| 实际代码 edit + 测试 | ~5% |

### 2.3 优化策略总览

针对 2.2 五项耗时项，本 req 攻 1（文档书写）+ 3（dispatch brief 含的 stage 链路）；不动 2（角色加载）和 4（合规扫描），它们是流程保障，不可精简。

| 优化项 | 简称 | 攻击对象 | 预期收益 |
|---|---|---|---|
| O1 | 文档 LLM-only 重写 | 文档书写"对人解释"段 | 文档体量降 50-70%，书写时间降 60% |
| O2 | stage 整合（req_review + planning 合并 → analysis） | 多余 stage 切换 | 1 次 stage 切换开销节省 |
| O3 | done 去 sug 入池 | done 阶段被强制扫改进点写 sug | done 耗时降 20-30% |
| O4 | next 单入口（去 --execute flag） | CLI 双入口认知开销 | 单 req 1 次 user 拍板（统一在 analysis → executing）|
| O5 | 删 ready_for_execution 空 stage | 空跑 stage（与 O4 配套） | stage 序列减 1 |

## 3. Scope

### 3.1 In（必须做）

**O1 文档 LLM-only 重写**（覆盖现有 3 流程所有文档模板）：

- 模板对象：`bugfix.md` / `requirement.md` / `change.md` / `plan.md` / `session-memory.md` / `test-evidence.md` / `acceptance-report.md` / `交付总结.md` / `bugfix-交付总结.md` / `diagnosis.md` / `回归-decision.md` / `acceptance-checklist.md` 等。
- 改造方向：YAML frontmatter（结构化字段）+ 紧凑 markdown（prose 用 bullet）。
- 删除内容：所有"对人解释"段落，包括「背景」「历史」「用户原话引用」「修订说明」「为什么这么设计」「设计理念」。
- 保留内容：变更前后状态、验证证据、流转决策、AC 映射、id+title 引用契约。

**O2 + O5 stage 整合**：

- 合并 `requirement_review` + `planning` → 单一 `analysis` stage（两 stage 已是同 analyst 角色 Part A/B，正式合并）。
- 删除 `ready_for_execution` 空 stage（O5，与 O4 配套）。
- `regression` + `executing`、`testing` + `acceptance` 不合并（用户拍板范围不含）。

**O3 done 阶段去 sug 入池**：

- `done.md` 删除「Step 6: 输出回顾报告与建议转 suggest 池」中的 sug 入池职责。
- `done.md` 退出条件删除「`done-report.md` 中的改进建议已提取（如有）」。
- 用户保留主动通过 `harness suggest "<text>"` 入池的能力。

**O4 去掉 `next --execute` flag**：

- `harness next` 单一入口覆盖所有 stage 流转。
- `analysis → executing` 由 `stage_pending_user_action="confirm-execution"` 控制（D3 = A），用户单次 `harness next` 推进。
- ff 模式下自动跳。

### 3.2 Out（明确不做）

- **不新增 trivial 通道**（这是 req-49 废弃方向，已 stash）。
- **不动角色加载链**（base-role + stage-role + 自身 role.md + 经验文件保留，流程保障）。
- **不动 sug 池 schema 本身**（frontmatter 字段 / 状态机不变）。
- **不动 suggest 流程**（suggestion / apply / done 三 stage 不变；只是 done 不再主动入池）。
- **不动 regression / executing / testing / acceptance 四 stage**（不合并、不重写流程）。
- **不动 PetMall / uav / PetMallPlatform2 任何项目代码**（read-only）。
- **不动 `.workflow/state/` runtime schema**（runtime.yaml 字段不增不减；`stage_pending_user_action` 已存在）。

## 4. Acceptance Criteria

| AC | 关联 | 验收口径 |
|---|---|---|
| AC-01 | O1 | 12+ 模板文件全部改造为 YAML frontmatter + 紧凑 markdown 形态；grep `## .*背景\|## .*历史\|## .*修订说明\|## .*用户原话` 全部为 0 |
| AC-02 | O1 | 每个新模板含必填 frontmatter 字段（id / title / created_at / operation_type / slug），紧凑段不超过原模板 50% 体量（行数下降 ≥ 50%）|
| AC-03 | O2 | `WORKFLOW_SEQUENCE` 不再含 `requirement_review` 与 `planning` 两项，改为单一 `analysis`；CLI / role-model-map.yaml / stage-role.md / analyst.md 引用同步更新 |
| AC-04 | O2 + O5 | `WORKFLOW_SEQUENCE` 不再含 `ready_for_execution`；`stage_policies` 删除该 key；CLI 全文 grep `ready_for_execution` 命中 = 0（除 legacy 兼容路径）|
| AC-05 | O3 | `done.md` Step 6 不再含「sug 入池」职责；退出条件不再含「改进建议已提取」；done subagent SOP 调整后不主动创建 sug 文件；`harness suggest --create` CLI 入口仍可用 |
| AC-06 | O4 | `cli.py` 移除 `next_parser.add_argument("--execute", ...)` 与对应 `if args.execute` 分支；`workflow_helpers.py` 移除 `if current_stage == "ready_for_execution" and not execute` 分支；`harness next --execute` 调用时报 unknown flag |
| AC-07 | O4 | `analysis → executing` 流转点在 `role-model-map.yaml` `stage_policies.analysis.exit_decision = user`（D3 = A 默认人工拍板）；ff 模式下 `ff_auto.py` 自动跳过该 user 拍板 |
| AC-08 | O1 + O5 | 端到端 dogfood：tmpdir 中执行完整 5-stage requirement（analysis → executing → testing → acceptance → done），所有产出文档采用新 LLM-only 模板，零 ready_for_execution stage，单次 `harness next` 推进 |
| AC-09 | O1 | reviewer.md / review-checklist.md 增补 lint：「新加 / 修改文档模板必须 LLM-only」「新加 stage 必须自检是否能合并」 |
| AC-10 | 全 | `harness validate --human-docs` exit 0；`harness validate --contract artifact-placement` exit 0；`harness validate --contract test-case-design-completeness` exit 0；新增 lint `harness validate --contract llm-only-docs`（chg-05 落地）exit 0 |
| AC-11 | O1 | 向后兼容（D5 = B）：旧 req（req-02 ~ req-49）/ bugfix（bugfix-1 ~ bugfix-N）的归档文档不被新模板覆盖；新模板只对 req-id ≥ 50 / bugfix-id ≥ next 严格生效 |

## 5. Split Rules（chg 拆分指引）

按"结构性变更先行 + 文档重写并行 + dogfood 收口"原则拆 5 个 chg，DAG 硬序如下：

```
chg-01（stage 整合 + next 单入口）
   ↓
chg-02（done 去 sug 入池）
   ↓
chg-03（文档 LLM-only 重写第一批：核心机器型）  ←─ 可与 chg-04 并行
chg-04（文档 LLM-only 重写第二批：验证 / 交付）
   ↓
chg-05（dogfood + reviewer 加项收口）
```

**拆分理由**：

- **chg-01 先行**：O2 + O4 + O5 是结构性变更（CLI sequence / stage_policies / role-model-map），是 chg-02 ~ chg-05 的语义底座；其他 chg 引用 stage 名称必须先确定 `analysis` 单一名。
- **chg-02 紧随**：O3 改动面小（仅 done.md + done subagent SOP），独立提交便于 git revert 颗粒度。
- **chg-03 + chg-04 文档重写**：拆 2 chg 是因为 12+ 模板按"机器型"vs"验证 / 交付"分组测试焦点不同（机器型靠结构化 lint，验证 / 交付靠 e2e dogfood）；plan 按硬序 03 → 04 但实操可并行。
- **chg-05 收口**：唯一含 dogfood e2e 的 chg，验证全链路；reviewer.md 加项放此 chg 是因为 lint 规则需基于 chg-01 ~ chg-04 全部落地后写得清楚。

**关键设计决策**（详见 §6）：

- D1（文档形态）= B（YAML frontmatter + 紧凑 markdown）
- D2（合并 stage 命名）= A（`analysis`）
- D3（用户拍板时机）= A（`analysis` 末尾 `stage_pending_user_action="confirm-execution"`）
- D4（原 sug 入池去向）= A（完全移除）
- D5（向后兼容策略）= B（仅对 req-id ≥ 50 / bugfix-id ≥ next 严格生效）

## 6. Default-pick 决策记录

| ID | 争议点 | 选项 | default-pick | 理由 |
|---|---|---|---|---|
| D1 | 文档形态：全 YAML / YAML+紧凑 md / 全紧凑 md | A / **B** / C | B | YAML frontmatter 放 metadata（LLM 直读）+ 紧凑 markdown 放 prose（bullet）兼顾结构化与可读性，避免全 YAML 牺牲表达力 |
| D2 | req_review + planning 合并后命名：analysis / planning / req_planning | **A** / B / C | A `analysis` | 「analysis」语义覆盖需求澄清 + 变更拆分两阶段动作；`planning` 复用旧名易与"已合并"事实冲突；`req_planning` 啰嗦 |
| D3 | analysis → executing 拍板时机：默认人工拍板 / 自动连跳 | **A** / B | A | 保留默认人工拍板（与现 planning → ready_for_execution 一致语义），ff 模式自动跳；避免用户失去对 plan.md 终审权 |
| D4 | done 去 sug 入池后原职责去向：完全移除 / reviewer 接 / main agent 自由收集 | **A** / B / C | A | 完全移除最简单；用户主动 `harness suggest` 已覆盖入池路径；reviewer 接职责会复杂化 lint 工具职责 |
| D5 | 向后兼容：完全替换 / 仅未来生效 / 全 migration | A / **B** / C | B | 仅对 req-id ≥ 50 / bugfix-id ≥ next 严格生效，旧已 archive 不动；最低破坏，渐进升级 |

## 7. Risks

| 风险 | 缓解 |
|---|---|
| O2 合并 stage 后归档历史 req（含 `requirement_review` / `planning` 时间戳）兼容 | role-model-map.yaml 保留 legacy alias `requirement-review` / `planning` 作 alias_of analysis；归档 yaml `stage_timestamps` 旧字段不动 |
| O4 移除 `--execute` flag 后用户老脚本/经验失效 | CLI 报 `unknown flag` 错误同时 stderr 提示「`--execute` 已废止，使用 `harness next` 即可」；release notes 高亮 |
| O1 文档重写破坏 reviewer 经验 | chg-05 同步更新 reviewer.md / review-checklist.md，明确「新模板必须 LLM-only」lint 规则 |
| dogfood e2e（chg-05）失败暴露隐藏 bug | 失败即 regression，不阻塞 chg-01 ~ chg-04 落地，但阻塞本 req 进入 done |

## 8. References

- 用户拍板 4 大优化项（O1 ~ O5）：本 req-50（现有流程优化）briefing。
- uav bugfix-6（事件时间允许负值）实证活样本：`/Users/jiazhiwei/claudeProject/uav/.workflow/flow/bugfixes/bugfix-6-事件时间允许负值-人工提报放宽飞行记录校验/`。
- req-49（trivial 通道方案）废弃 stash：本 req 区分点。
- req-40（阶段合并与用户介入窄化）/ chg-01：requirement_review + planning 角色已合并到 analyst.md（本 req-50 在 stage 层正式合并，是 req-40 的延续）。
- req-41（机器型工件回 flow/requirements）/ chg-01：repository-layout.md 三大子树契约，本 req 不动布局。
- req-31（角色功能优化整合与交互精简）/ chg-04：testing / acceptance 对人 brief 已废止，本 req 沿用方向。
