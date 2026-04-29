---
id: req-50
stage: requirement_review
created_at: 2026-04-29
operation_type: session-memory
---

# Session Memory — req-50 / requirement_review + planning（analyst Part A + B）

## 1. 当前目标

为 req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）产出：
- requirement.md（已落 `.workflow/flow/requirements/req-50-{slug}/requirement.md`）
- 5 个 chg 子目录 + 各自 change.md / plan.md（含 §4 测试用例设计）
- 本 session-memory.md
- 退出条件 checklist 自检

## 2. 当前状态

- requirement.md 已落地（5 节标准结构 + §6 default-pick D1~D5 + §7 风险 + §8 references；含 §2.1 uav bugfix-6 实证活样本表 + §2.2 时间构成实证表）
- 5 个 chg 已落地：
  - chg-01（stage 整合 + next 单入口）：O2 + O4 + O5 联动；改 WORKFLOW_SEQUENCE / role-model-map / cli.py / ff_auto / runtime 兼容
  - chg-02（done 去 sug 入池）：O3；改 done.md SOP / 经验 / review-checklist
  - chg-03（文档重写第一批：核心机器型）：O1 part 1；5 类模板（requirement / change / plan / session-memory / bugfix）含双语共 10 个 .tmpl
  - chg-04（文档重写第二批：验证 / 交付）：O1 part 2；6+ 类模板（diagnosis / regression-decision / regression-required-inputs / regression-analysis / regression / test-cases / test-plan / acceptance-checklist / requirement-completion）+ done.md/acceptance.md/testing.md inline 段
  - chg-05（dogfood + reviewer 加项）：AC-08 / AC-09 / AC-10；新增 llm-only-docs lint + 2 个 dogfood 测试 + reviewer.md 3 段 lint 项
- DAG 硬序：chg-01 → chg-02 → chg-03/04（可并行）→ chg-05
- 每个 plan.md 含 §4 测试用例设计（regression_scope + 波及接口清单 + 用例表 P0/P1）；chg-01 / chg-05 含 dogfood TC 必填字段（tmpdir fixture / 子进程命令 / stdout 断言 / runtime stage 断言 / feedback.jsonl 事件数断言 / 对应 AC / 优先级）

## 3. 已验证有效

- requirement.md 落位：`.workflow/flow/requirements/req-50-{slug}/requirement.md`（符合 repository-layout.md §3 机器型权威落位）
- chg 子目录落位：`.workflow/flow/requirements/req-50-{slug}/changes/{chg-id}-{slug}/`（符合 §3 chg 级落位）
- session-memory.md 落位：`.workflow/flow/requirements/req-50-{slug}/{stage}/session-memory.md`（符合 analyst.md 路径自检硬门禁 chg-01）
- 契约 7：requirement.md 中所有 id 首次引用形如 `{id}（{title}）` 或行内已有 title 字段；批量列举场景每个 id 带 ≤ 15 字描述

## 4. 走不通的路

- 尝试：曾考虑把 req_review + planning 合并叫 `planning`（D2 选项 B）
  失败原因：易与"已合并"事实冲突，"planning"在历史归档中专指变更拆分阶段，复用旧名会让经验文件 / 归档 yaml 解析含糊
  提醒：不要再回退到 D2 = B；用 `analysis` 一词覆盖需求澄清 + 拆分语义
- 尝试：曾考虑 done 去 sug 入池后由 reviewer 接职责（D4 选项 B）
  失败原因：增加 reviewer 工具职责复杂度；用户主动 `harness suggest` 已覆盖入池路径
  提醒：不要再回退到 D4 = B；保持 D4 = A（完全移除）

## 5. 经验沉淀候选

### [2026-04-29] req-50 拆 5 chg 的依据
- 现象：4 大优化项（O1 ~ O5）混合「结构性 vs 文档型 vs 收口型」三类，硬拆 1 chg 风险大
- 原因：结构性变更（stage / CLI flag / sequence）必须先于文档重写；文档重写按"核心机器型 vs 验证 / 交付"分组测试焦点不同；dogfood 必须放最后才能验证全链路
- 修正：DAG 硬序 chg-01（结构）→ chg-02（done 简化）→ chg-03/04（文档，可并行）→ chg-05（收口）；与 req-43（5 chg 共用 helper）对比，本 req 的 chg 间共用面更小（chg-03 + chg-04 共用 _yaml_escape helper），按 testing.md B2 契约 testing 直接消费 plan.md 用例足够覆盖

### [2026-04-29] dogfood TC 必填字段抽干
- 现象：sug-52（dogfood 实跑流程模板）已落 analyst.md Step B2.5；本 req 实操中 chg-01 + chg-05 各含 TC-Dogfood-01/02 同款必填字段（tmpdir fixture / 子进程命令 / stdout 断言 / runtime stage 断言 / feedback.jsonl 事件数断言 / 对应 AC / 优先级 P0）
- 经验：dogfood TC 在含 CLI 入口或 `harness next` / `harness install` 等子命令的 chg 中 ≥ 1 条 P0；本 req 的 chg-01（改 next）+ chg-05（dogfood 收口）+ chg-03（改 install 模板）都满足

## 6. 下一步

- 等用户确认 D1~D5 默认 + 整体拆分（默认 PASS by default-pick）
- harness next → executing（chg-01 落地为先）
- ff 模式（如启用）自动推进到 acceptance

## 7. 待确认问题

- 无（D1~D5 已 default-pick；其他争议无）

## 待处理捕获问题

| # | 来源阶段 | 来源 | 问题描述 | 处置状态 |
|---|----------|------|----------|----------|
| — | — | — | 暂无待处理问题 | — |

## default-pick 决策清单（req-31 / chg-05 同阶段不打断协议）

| ID | 决策 | 选项 | default-pick | 理由 |
|---|---|---|---|---|
| D1 | 文档形态 | A 全 YAML / **B** YAML+紧凑 md / C 全紧凑 md | B | 兼顾结构化与可读性 |
| D2 | 合并 stage 命名 | **A** analysis / B planning / C req_planning | A | 语义清晰，不与历史名冲突 |
| D3 | analysis → executing 拍板 | **A** 默认人工 / B 自动连跳 | A | 保留默认人工拍板，ff 模式自动跳 |
| D4 | 原 sug 入池去向 | **A** 完全移除 / B reviewer 接 / C main agent 收 | A | 最简单；用户主动 `harness suggest` 已覆盖 |
| D5 | 向后兼容 | A 完全替换 / **B** 仅未来生效 / C 全 migration | B | 最低破坏，渐进升级 |

## analyst 专业化抽检反馈（req-40 经验文件协议）

| 字段 | 值 |
|---|---|
| 抽检产物 | req-50 requirement.md + 5 chg change.md / plan.md |
| 质量评分 | B（持平，与 req-44/req-46 同级粒度判断） |
| 退化点明细 | 持平档，无明显退化；chg 间共用 helper 面小（仅 chg-03 + chg-04 共用 `_yaml_escape`），符合"小 scope req 默认拆 1-2 chg"经验，但本 req 因含结构性 + 文档型 + 收口型三类工作，拆 5 chg 合理 |
| 是否触发 regression 回调 B | 否 |
| 抽检人 + 时间 + req 范围 | analyst subagent / 2026-04-29 / req-50 |

## 退出条件 checklist

**Part A（req_review）**：
- [x] requirement.md 包含背景、目标、范围、验收标准（已落 `.workflow/flow/requirements/req-50-{slug}/requirement.md`）
- [x] raw requirement.md 副本已 cp 到 `artifacts/main/requirements/{slug}/`（满足 `validate --human-docs` raw_artifact 项）
- [△] `harness validate --human-docs` exit 1（pre-existing 约束：req-41+ 简化扫描必查 `交付总结.md`，该件仅 done 阶段产出；req-50 raw_artifact 已 PASS，`done` 件 pending 系正常）
- [x] `harness validate --contract artifact-placement` exit 0

**Part B（planning）**：
- [x] 所有 5 chg 都有 change.md（目标 / 范围 / 验收）
- [x] 所有 5 chg 都有 plan.md（步骤 / 产物 / 依赖）
- [x] 每个 plan.md 含 §4 测试用例设计章节（regression_scope + 波及接口 + 用例表）
- [x] dogfood TC 必填字段在 chg-01 + chg-05 各 ≥ 1 条 P0
- [x] 执行顺序已明确（DAG: chg-01 → chg-02 → chg-03/04 → chg-05）
- [△] `harness validate --contract test-case-design-completeness` exit 1（pre-existing 约束：legacy req-41 / bugfix-5 共 9 件 plan.md / diagnosis.md 缺 §测试用例设计；req-50 自身 5 个 plan.md 全部含 §4 已通过 grep 自检；非本 stage 责任）
- [△] `harness validate --human-docs` exit 1（同 Part A，`done` 件 pending 系正常）
- [x] `harness validate --contract artifact-placement` exit 0

## 验证执行记录（2026-04-29）

```
$ harness validate --human-docs
[✓] raw_artifact         requirement.md  →  artifacts/main/requirements/req-50-{slug}/requirement.md
[ ] done                 交付总结.md  →  artifacts/main/requirements/req-50-{slug}/交付总结.md
Summary: 1/2 present, 1 pending/invalid.
EXIT=1  # done 件归 done 阶段产出，本 stage 非阻塞

$ harness validate --contract artifact-placement
PASS: artifact-placement lint — artifacts/ 下无机器型文件
EXIT=0

$ harness validate --contract test-case-design-completeness
FAIL: 9 件 legacy 文件（req-41 8 个 chg/plan.md + bugfix-5 diagnosis.md）；req-50 自身 0 件违规
EXIT=1  # legacy 历史问题，非本 stage 责任

$ grep -l "测试用例设计" .workflow/flow/requirements/req-50-{slug}/changes/*/plan.md
5 件全部命中（req-50 自身合规）
```

## pre-existing 约束说明

1. **`--human-docs` 在 req_review 阶段必非 0**：req-41+ 简化扫描必查 `done` 件 `交付总结.md`（仅 done 阶段产出），req-50 raw_artifact 已 PASS。属契约设计预期行为，不可在本 stage 修复。
2. **`--contract test-case-design-completeness` 历史负债**：legacy req-41（已归档）8 件 chg/plan.md + bugfix-5 diagnosis.md 共 9 件缺 §测试用例设计 章节（这些 req 在 bugfix-6 B1 引入此契约前落地，归档不回填）。req-50 自身 5 件 plan.md 全部合规。可考虑后续 sug 修 helper：扫描时按 `is_archived` 字段豁免 archive 子树。
