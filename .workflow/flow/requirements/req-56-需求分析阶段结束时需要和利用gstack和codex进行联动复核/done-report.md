---
id: req-56
title: "harness requirement 默认调 /office-hours，--fallback 走原生 analyst，产出强制对齐 harness 文档规范"
created_at: 2026-05-10
operation_type: done-report
stage: done
---

# Done Report: req-56-harness requirement 默认调 /office-hours，--fallback 走原生 analyst，产出强制对齐 harness 文档规范

## 基本信息

- **需求 ID**: req-56
- **需求标题**: harness requirement 默认调 /office-hours，--fallback 走原生 analyst，产出强制对齐 harness 文档规范
- **归档日期**: 2026-05-10
- **verdict**: PASS

## 实现时长

- **总时长**: 约 1 天（started_at 2026-05-09 → completed_at 2026-05-10）；实际工时（不含等待 `/harness-next`）约 60 分钟级别
- **executing**: ~25 分钟（08:43 → 09:09 UTC）
- **testing**: ~19 分钟（09:09 → 09:28 UTC）
- **acceptance**: ~16 小时（09:28 2026-05-09 → 01:20 2026-05-10，含用户 idle 等命令）
- **done**: 进行中

> 数据来源：`state/requirements/req-56-*.yaml.stage_timestamps`

---

## 1. 执行摘要

req-56 围绕"`harness requirement` 默认走 gstack `/office-hours` 强映射"做了 3 个 chg 的精准改造：CLI 层加 `--fallback` opt-out + state schema 持久化 + agent 兼容兜底；analyst 角色 Step A1.5 改读字段直跑 + adapter 强制门；4 平台 skill 文档透传 + 双路径 dogfood TC 闭环。结果 26/26 测试 PASS，5 项合规扫描全 CLEAN，acceptance verdict=PASS 0 异议。

## 2. 六层检查结果

### 第一层：Context（上下文层）

- [x] **角色行为检查**：analyst（opus）/ executing（sonnet 子）/ testing（sonnet 子）/ acceptance（sonnet 子）/ done（opus 主）各角色独立性符合预期；testing / acceptance 用独立子 agent 实例（base-role 硬门禁）。
- [x] **经验文件更新**：本轮新增教训按 Step 4 已在下方 §4 留痕；analyst.md / executing.md / testing.md / acceptance.md 经验文件待补（见 §6 改进建议）。
- [x] **上下文完整性**：req-56 工件目录完整（requirement.md / 3 chg / test-report.md / acceptance/checklist.md / acceptance/acceptance-report.md / done-report.md）。

### 第二层：Tools（工具层）

- [x] **工具使用顺畅度**：未发现工具阻塞；harness CLI / pytest / git / Edit / Write 全程顺畅。
- [x] **CLI 工具适配**：`harness validate --human-docs` 在 raw_artifact pending 阶段 by-design exit 1 不是 bug，但 acceptance.md Step 1 字面要求"全 ok"与此惯例略有抽象错位（已记 sug-候选-1）。
- [x] **MCP 工具适配**：本 req 未触及 MCP 工具。

### 第三层：Flow（流程层）

- [x] **阶段流程完整性**：analysis → executing → testing → acceptance → done 全 5 stage 实际执行，无跳过。
- [x] **阶段跳过检查**：无。
- [x] **流程顺畅度**：每个 stage `/harness-next` 推进顺畅；唯一阻塞是 testing → acceptance 时 `harness next` 因 test-report.md 路径错放（在 testing/ 子目录）+ 缺 `## 结论` heading 被 work-done gate 拦截，主 agent 修正后通过（教训：testing 子 agent 落点应明确为 `req-flow-dir/test-report.md` 根目录）。

### 第四层：State（状态层）

- [x] **runtime.yaml 一致性**：`current_requirement: req-56` / `stage: done` / `active_requirements: [bugfix-11, req-56]` 一致；`gstack_status` 完整。
- [x] **需求状态一致性**：`state/requirements/req-56-*.yaml.stage: done` / `status: done` / `completed_at: 2026-05-10` 已与 runtime.yaml 同步（acceptance.md §"acceptance → done 状态同步检查"已隐式满足）。
- [x] **状态记录完整性**：`stage_timestamps` 含 4 个流转点（executing / testing / acceptance / done）；`office_hours_mode` 字段未写入本 req state（因为 chg-01 落地前本 req 已 `harness requirement` 创建，验证陈旧 schema 在新代码下读取兼容性的实证用例 — 工作证据，不是缺陷）。

### 第五层：Evaluation（评估层）

- [x] **testing 独立性**：testing 用独立 sonnet 子 agent，未与 executing 共用实例；test-report.md 含 5 项合规扫描结论。
- [x] **acceptance 独立性**：acceptance 用独立 sonnet 子 agent，签字基于 test-report.md，无重跑测试。
- [x] **评估标准达成**：26/26 TC PASS，5 项合规 CLEAN，AC-01~07 全签字 0 异议。

### 第六层：Constraints（约束层）

- [x] **边界约束触发**：无越界。executing 子 agent 严格在 chg-01 范围内（cli.py / harness_requirement.py / workflow_helpers.py / 测试），未动 chg-02/03 责任。
- [x] **风险扫描更新**：本 req 无新风险类型（沿用 bugfix-11 ordered_keys 同型病防御模板）。
- [x] **约束遵守情况**：硬门禁三（自我介绍）/ 八（项目级加载链 brief）/ 九（subagent 产出独立核查）全程遵守。

## 3. 工具层适配发现

- **CLI 工具发现**：`harness validate --human-docs` 在 stage=analysis/executing/testing/acceptance + raw_artifact pending 时 exit 1 是分阶段设计；shell 用 `2>&1 | tail -5; echo "EXIT=$?"` 模式无法读取真实 exit code（被 tail 的 0 覆盖），**改用 `harness validate ...; echo "REAL EXIT=$?"` 直接拼接**才能拿到正确值。
- **CLI 工具发现**：work-done gate 对 test-report.md / acceptance/checklist.md 要求 `## 结论` 二级标题精确匹配（正则 `(?:^|\n)##\s*§?结论`），`### 判定` 三级标题不算；testing / acceptance 子 agent 落地需注意 heading 层级。

## 4. 经验沉淀情况

新增可泛化教训（待补 experience/）：

1. **shell exit code 拼管道陷阱**：`cmd 2>&1 | tail -N; echo "EXIT=$?"` 报的是 tail 的 exit 不是 cmd 的。executing / testing / acceptance 自检脚本应改为 `cmd; echo "REAL EXIT=$?"` 或 `cmd > /tmp/out 2>&1; rc=$?; cat /tmp/out; echo "EXIT=$rc"`。
2. **work-done gate heading 精确匹配**：`_is_stage_work_done` 对 testing / acceptance 产出要求 `## 结论` 或 `## §结论` 二级标题；`### 判定` 不算。子 agent briefing 应明确"必须含 `## 结论` heading 段"。
3. **test-report.md / acceptance/checklist.md 路径**：testing 产物落 `req-flow-dir/test-report.md`（根目录，**不是** `testing/` 子目录）；acceptance 产物落 `acceptance/checklist.md` + `acceptance/acceptance-report.md`（在子目录）。两者落点不同，子 agent briefing 必须明确。
4. **chg-03 type 路径错估**：plan 阶段对 4 平台 skill 文档落点估错（写"3 mirror skills/"实际是 4 平台 + commands/skills 混合），executing 阶段实施细节修正合规，记入 session-memory 留痕；建议 analyst Step A2 加入"先 grep 实际路径"作 SOP。
5. **跨平台 skill 文档同步靠人工 cp**：4 平台 SKILL.md / commands.md body block 一致性无 lint 防漂移（见 sug-候选-3）。

## 5. 流程完整性评估

- [x] **requirement_review/analysis**：analysis 单 stage（req-50 chg-01 后合并）执行；analyst 在 fallback 模式下手工填实 requirement.md，未触发 office-hours（用户初次 ask 时改了需求方向，进 fallback）。
- [x] **planning**（已合并到 analysis Part B）：3 chg 拆分线性依赖 chg-01 → chg-02 → chg-03，每个 plan.md 含 §4 测试用例设计。
- [x] **executing**：chg-01 派 sonnet 子 agent；chg-02 / chg-03 主 agent 直接（文档层降级允许）。
- [x] **testing**：独立 sonnet 子 agent，26/26 PASS，补 chg-02 / chg-03 缺失 pytest（13 用例）。
- [x] **acceptance**：独立 sonnet 子 agent，verdict=PASS。
- [x] **done**：opus 主 agent 六层回顾。

## 6. 改进建议（→ sug 候选）

| sug 候选 | 内容 | 优先级 |
|---|---|---|
| sug-候选-1 | human-docs AC 措辞修订（acceptance 与实际流程对齐）；同时修订 acceptance.md Step 1 字面"全 ok"与历史惯例 | medium |
| sug-候选-2 | 加 `harness mode --fallback` / `--required` 子命令，跑了 office-hours 中途想转 fallback 时不必 regression | low |
| sug-候选-3 | 加 `harness validate --contract skill-body-consistency` 契约扫描 4 平台 skill body block hash | medium |

详细 sug 文件由本 done 阶段稍后落入 `.workflow/flow/suggestions/`。

## 7. 下一步行动

- **行动 1**：本 done-report 完成后落 sug-候选-1/2/3 入池
- **行动 2**：commit 本 req 全部改动（cli/state/role/skill/test 8 文件 + req 工件目录）
- **行动 3**：archive 前补 commit revert dry-run 抽样（Step 2.5 因 req-56 commit 未落地暂跳过，archive 时补）
- **行动 4**：等用户 `harness archive req-56` 推到 archived 状态

## 报告头部备注

- 数据来源：`state/requirements/req-56-*.yaml.stage_timestamps`、acceptance/checklist.md、test-report.md、3 chg session-memory.md
- 本报告由主 agent（done / opus）独立生成，未派发子 agent
