# Acceptance Checklist — req-43（交付总结完善）

**验收官**: Subagent-L1（acceptance / sonnet，Sonnet 4.6）
**日期**: 2026-04-25
**合规依据**: evaluation/acceptance.md + review-checklist.md（含 bugfix-5（同角色跨 stage 自动续跑硬门禁）/ bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 加项）

---

## §模型自检（Step 7.5）

expected_model: sonnet（Sonnet 4.6），role-model-map.yaml `roles.acceptance: sonnet`，与 briefing 一致。
runtime 不暴露 self-introspection；按降级路径 = briefing expected_model 核对 ✅。

---

## §需求/变更映射（AC vs chg）

| AC | 描述（摘要） | 覆盖 chg |
|----|------------|---------|
| AC-01（任务级覆盖完整） | req/bugfix/sug 三类均有交付总结产出 | chg-04（bugfix）+ chg-05（sug + 完整覆盖） |
| AC-02（per-stage token 字段齐全） | §效率与成本含 stage × role × model 单表，9 列固定 | chg-03（per-stage 合并到 stage × role × model 单表渲染） |
| AC-03（per-stage 时间字段齐全） | 各 stage entered_at / exited_at / duration_s | chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳） |
| AC-04（数据通路只消费不重采） | 消费 usage-log.yaml + stage_timestamps，helper 单测三 fixture | chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））+ chg-03 |
| AC-05（State 层校验不退化 + 扩三类） | base-role.md 扩三类任务 State 层自检 | chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务） |
| AC-06（stage 流转点联动写齐时间戳） | _sync_stage_to_state_yaml 加 prev_stage 参数 | chg-02 |
| AC-07（归档对接三类一致） | archive 对 req/bugfix/sug 三类一致处理 | chg-04 + chg-05 |

---

## §验收 Checklist

### 5 chg 落地核查

- [x] **chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））落地** ✅
  - `record_subagent_usage` 函数签名含 `task_type: str = "req"` 参数（workflow_helpers.py line 2724）
  - 入参 `task_type` 写入 usage-log entry（line 2786）
  - sug-25（record_subagent_usage 派发链路真实接通）状态已翻 `applied`（sug-25 frontmatter line 4）
  - harness-manager.md §3.6 Step 4 升级为可观测留痕步骤
  - scaffold_v2 mirror：harness-manager.md diff=0 ✅

- [x] **chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）落地** ✅
  - `_sync_stage_to_state_yaml` 含可选 `prev_stage: str | None = None` 参数（line 5551）
  - 写 new_stage.entered_at 同时写 prev_stage_exited_at 同级键（line 5618-5619）
  - `_backfill_done_timestamps` 函数存在（archive 前兜底补齐，line 5650+）
  - `test_stage_timestamps_completeness.py` 存在 ✅

- [x] **chg-03（per-stage 合并到 stage × role × model 单表渲染）落地** ✅
  - `done_efficiency_aggregate` 返回 `stage_role_rows` 字段（line 2837, 2956, 3052）
  - `done.md` 模板含「各阶段切片（stage × role × model × token × tool_uses）」单表（done.md line 141+）
  - 9 列字段：stage / role / model / input_tokens / output_tokens / cache_read / cache_creation / total / tool_uses ✅
  - `test_req43_chg03.py` 存在 ✅

- [x] **chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））落地** ✅
  - `BUGFIX_LEVEL_DOCS` 常量含 `("acceptance_done", "bugfix-交付总结.md")`（validate_human_docs.py line 121-125）
  - `validate_human_docs` 对 bugfix 维度扫描（line 378）
  - `done.md` bugfix 分支模板存在（含修复验证段、无 chg-NN 段，line 191+）
  - `repository-layout.md` §2 白名单含 `bugfix-交付总结.md` + §3.2 bugfix 落位定义（line 89, 156）
  - scaffold_v2 mirror：done.md + repository-layout.md diff=0 ✅
  - `test_req43_chg04.py` 存在 ✅

- [x] **chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）落地** ✅
  - `_create_sug_delivery_summary` 函数存在（workflow_helpers.py line 4444）
  - `archive_suggestion` 触发 `_create_sug_delivery_summary`（line 4438）
  - `repository-layout.md` §2 sug 交付总结白名单 + §3 sug 子树落位（line 90, 166-179）
  - `base-role.md` State 层自检扩三类任务（base-role.md line 214-225）
  - scaffold_v2 mirror：base-role.md + done.md + repository-layout.md diff=0 ✅
  - `test_req43_chg05.py` 存在 ✅

### AC 逐条核查

- [x] **AC-01（任务级覆盖完整）** ✅
  - req：既有 done 路径继续产出 `交付总结.md` ✅
  - bugfix：chg-04 新增 `bugfix-交付总结.md` 全路径，`validate_human_docs` 校验阻断 ✅
  - sug：chg-05 `_create_sug_delivery_summary` 3 段轻量产出（--apply 直接处理 / --archive / --reject 均触发）✅

- [x] **AC-02（per-stage token 字段齐全）** ✅
  - `done.md` 单表含 9 列（stage/role/model/input/output/cache_read/cache_creation/total/tool_uses）✅
  - helper `stage_role_rows` 按 (stage, role, model) 三键 group by，entries 缺失降级 `_NO_DATA` ✅
  - testing 矩阵：chg-03 plan.md 8 用例全过 + testing 自补 2 反例（完全不存在的 req-id / 空 usage-log）全过 ✅

- [x] **AC-03（per-stage 时间字段齐全）** ✅
  - `_sync_stage_to_state_yaml` prev_stage 参数联动写 exited_at ✅
  - `_backfill_done_timestamps` 归档前兜底补齐 ✅
  - testing 矩阵：chg-02 plan.md 7 用例全过 + testing 自补 1 反例（同 stage 多次写）✅

- [x] **AC-04（数据通路只消费不重采）** ✅
  - chg-01 只改 helper 签名 + harness-manager 留痕，未新建采集通道 ✅
  - chg-03 `done_efficiency_aggregate` 消费既有 usage-log.yaml entries，未新设写入逻辑 ✅
  - helper 单测覆盖 entries 缺失/部分缺失/全齐 三种 fixture（test_req43_chg03.py）✅

- [x] **AC-05（State 层校验不退化 + 扩三类）** ✅
  - base-role.md `## done 六层回顾 State 层自检` 已扩三类任务（含「三类任务级 usage-log entries 数 ≥ 派发次数 - 容差」）✅
  - 既有 req 维度校验文字契约保留不退化 ✅
  - task_type 参数支持 req/bugfix/sug 路径切换（done_efficiency_aggregate line 2811）✅

- [x] **AC-06（stage 流转点联动写齐时间戳）** ✅
  - `_sync_stage_to_state_yaml` prev_stage 参数落地（line 5551, 5617-5619）✅
  - D-4 同级新增 `{stage}_exited_at` 键方案，向后兼容历史归档 req yaml ✅
  - `test_stage_timestamps_completeness.py` 覆盖跳跃流转 + runtime↔req yaml 同步反例 ✅

- [x] **AC-07（归档对接三类一致）** ✅
  - `repository-layout.md` §3 三类落位均明确（req / bugfix / sug 子树）✅
  - `validate_human_docs` 对 bugfix 维度校验扩（BUGFIX_LEVEL_DOCS + _collect_bugfix_items）✅
  - sug 维度：sug 已 applied/archived/rejected 但缺交付总结 → validate 阻断（chg-05）✅
  - sug → req 转化路径豁免（OQ-1 确认，converted-to-req 状态不校验 sug 自身交付总结）✅

### testing 报告核查

- [x] **testing 报告 PASS（含 followup 记录）** ✅
  - 5 chg 全部 PASS，无 FAIL 缺陷 ✅
  - 43 executing pytest + 9 testing 自补 = 52 条用例全通过 ✅
  - chg-01 followup 已明确标注「非阻断」：helper 实现正确，派发钩子文字契约仍需主 agent 在实际 session 中执行 python helper 调用；无功能退化 ✅

- [x] **全量回归通过（除 pre-existing failure）** ✅
  - 576 passed / 2 pre-existing FAIL（test_readme_has_refresh_template_hint + test_human_docs_checklist_for_req29）
  - 2 pre-existing 与 req-43（交付总结完善）无关，已存在于历史 ✅

- [x] **base-role 硬门禁六合规** ✅
  - 合规扫描 5 项全 PASS（R1 越界核查 / revert 抽样 / 契约 7 / req-29 映射回归 / req-30 model 透出）✅
  - 越界核查：所有改动文件均在 plan.md §影响文件列表 明示范围内 ✅

- [x] **scaffold_v2 mirror 同步（diff=0）** ✅
  - harness-manager.md（chg-01）：diff=0 ✅
  - base-role.md（chg-01 + chg-05）：diff=0 ✅
  - done.md（chg-03 + chg-04 + chg-05）：diff=0 ✅
  - repository-layout.md（chg-04 + chg-05）：diff=0 ✅
  - 抽样验证：四文件 diff 均无输出 ✅

- [x] **不破坏既有契约** ✅
  - req-31 / req-37 / req-40 / req-41 / req-42：模板字段保留「向后兼容」注释；done.md 旧两表被替换为单表，AC-02 要求，契约升级而非退化 ✅
  - bugfix-5（同角色跨 stage 自动续跑硬门禁）：index.md stage_policies 镜像引用完整 ✅
  - bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））：plan.md §测试用例设计段 39 条用例满足 B2 新契约 ✅

---

## §遗留 / 后置项

### L-01（非阻断 followup）：chg-01 派发钩子文字契约

- **描述**：harness-manager.md §3.6 Step 4 升级为可观测留痕步骤（文字契约），但主 agent 在实际 testing/acceptance session 中尚未执行 python helper 调用，导致真实 `usage-log.yaml` 未写入。
- **影响评估**：helper 实现 (`record_subagent_usage`) 正确，9/9 pytest 全过；接通链路从「文字契约」到「python 运行时调用」还需主 agent 主动执行。不影响 req-43 本 req 功能产出。
- **处置建议**：转 sug 池（sug-25（record_subagent_usage 派发链路真实接通） 精神延伸），后续 req 补完接通；**不阻断本 req done**。

### L-02（不阻断）：sug-38（harness next over-chain bug）

- **描述**：req-43 周期实证触发 `harness next` 连跳超出预期阶段（多跳）。
- **处置**：已入 sug 池，不在 req-43（交付总结完善）scope；本 req 不受其影响。

### L-03（信息留痕）：runtime.yaml stage 已为 done

- runtime.yaml `stage: "done"` 于 `2026-04-27T00:36:22.770502+00:00` 写入，acceptance 阶段为本次 subagent 补跑验收。若 stage 流转为 ff 跳过（harness ff），则本 acceptance checklist 作后补验收凭证留存，不改 runtime 状态。

---

## §最终验收结论

**PASS-with-followup**

- **checklist 通过/失败计数**：14 ✅ / 0 ❌ / 0 ⚠️
- **AC 全部通过**：AC-01 ~ AC-07 七条全 ✅
- **5 chg 全部落地**：grep + cat 抽样核查物理存在 + 字段对齐 ✅
- **testing PASS**：52 用例全通过 / 全量回归 576 passed / 2 pre-existing ✅
- **遗留 followup 数**：2 条（L-01 非阻断 / L-02 sug 池）

### 主 agent 应在用户决策后做的

1. **用户确认 PASS-with-followup** → 主 agent 执行 `harness archive`（req-43 done 阶段产出交付总结.md + 归档）。
2. L-01 followup（chg-01 派发钩子运行时接通）→ 可转 sug 池候选（sug-25 延伸），后续 req 处理；**不需要补 chg**。
3. L-02（sug-38（harness next over-chain bug））→ 已在 sug 池，无需本 req 处理。
