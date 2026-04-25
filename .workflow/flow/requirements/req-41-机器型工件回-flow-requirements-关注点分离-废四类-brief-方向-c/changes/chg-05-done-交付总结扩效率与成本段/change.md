# Change

## 1. Title

done 交付总结扩 §效率与成本 + Step 6 聚合逻辑

## 2. Goal

- `done.md` 交付总结最小字段模板新增 "## 效率与成本"段（固定四子字段：总耗时 / 总 token / 各阶段耗时分布 / 各阶段 token 分布）；SOP Step 6 加"读取 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml` + req yaml `stage_timestamps`，聚合后写入交付总结 §效率与成本"陈述；删除旧的"召唤 usage-reporter"残留陈述；配套新增 done subagent pytest 模拟用例。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- `.workflow/context/roles/done.md`：
  - 交付总结最小字段模板新增 `## 效率与成本` 段，含固定四子字段（顺序不得变更）：
    - `### 总耗时`：秒数 + 人类可读（如 `1234 s（约 20 分钟）`）；
    - `### 总 token`：`input_tokens` / `output_tokens` / `cache_read_input_tokens` / `total_tokens` 四列；
    - `### 各阶段耗时分布`：表格 `stage | entered_at | duration_s`（按 stage 时序排序）；
    - `### 各阶段 token 分布`：表格 `role | model | total_tokens | tool_uses`（按 total_tokens 降序）；
  - SOP Step 6 新增聚合陈述："读取 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml`（含 subagent_usage entries）+ req yaml `stage_timestamps`，按 stage 与 role × model 聚合；结果写入交付总结 §效率与成本段四子字段；若 usage-log 为空则四子字段标 `⚠️ 无数据`（禁止编造）"；
  - 删除原"召唤 usage-reporter"/"生成耗时与用量报告"陈述（若存在）；
- 同步 mirror：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`；
- pytest 新增：
  - `test_done_delivery_summary_efficiency_section`：mock done 角色 + mock `.workflow/flow/requirements/req-XX/usage-log.yaml`（含 ≥ 2 条 subagent_usage entries）+ mock req yaml `stage_timestamps`（含 ≥ 3 stage），触发 done 聚合逻辑，断言产出的 `交付总结.md` 内 §效率与成本段四子字段全填、字段顺序正确、值与 mock 源可追溯；
  - `test_done_delivery_summary_empty_usage_log`：mock usage-log 为空，断言四子字段标 `⚠️ 无数据`；
  - `test_done_delivery_summary_field_order_fixed`：断言字段顺序不变（总耗时 → 总 token → 各阶段耗时 → 各阶段 token）；
- 涉及文件：
  - `.workflow/context/roles/done.md`
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`（mirror）
  - `tests/test_done_subagent.py`（新或扩既有）

### Excluded

- **不动** `.workflow/flow/repository-layout.md`（归属 chg-01（repository-layout 契约底座））；
- **不改** CLI 代码（归属 chg-02（CLI 路径迁移 flow layout））；
- **不改** `validate_human_docs.py`（归属 chg-03（validate_human_docs 重写删四类 brief））；
- **不动** `record_subagent_usage` 内部实现（已实现，chg-06（harness-manager Step 4 派发硬门禁）接入派发链路）；
- **不去除** done.md 其他段（如六层回顾段落）；
- **不改** `harness-manager.md`（归属 chg-06）；
- **不扩** base-role 硬门禁六（归属 chg-08（硬门禁六扩 TaskList + stdout + 提交信息））。

## 5. Acceptance

- Covers requirement.md **AC-10**（效率字段硬门禁陈述，done.md 部分）：
  - `grep -q "读取.*usage-log.yaml.*stage_timestamps" .workflow/context/roles/done.md` 或语义等价陈述命中 ≥ 1 次；
  - `grep -q "效率与成本" .workflow/context/roles/done.md` 命中 ≥ 1 次。
- Covers requirement.md **AC-11**（模板扩展）：
  - `done.md` 含 "## 效率与成本" 段；
  - 段内四子字段按顺序出现：`### 总耗时` / `### 总 token` / `### 各阶段耗时分布` / `### 各阶段 token 分布`；
  - 字段顺序 grep 验证：`awk '/^### (总耗时|总 token|各阶段耗时分布|各阶段 token 分布)/{print NR,$0}'` 四行顺序稳定。
- Covers requirement.md **AC-13 (d)**（dogfood §效率与成本从真实 usage-log 聚合）起点：
  - pytest 用例覆盖聚合逻辑；dogfood 活证由 chg-07（dogfood + scaffold_v2 mirror 收口）做端到端验证。
- Covers requirement.md **AC-15**（scaffold_v2 mirror 同步）：
  - `diff -q .workflow/context/roles/done.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` 无输出。
- Covers requirement.md **AC-06**（回归不破坏）：
  - `pytest tests/` 全量绿，含既有 done 阶段用例。

## 6. Risks

- **风险 1：usage-log.yaml 格式若在 chg-06（harness-manager Step 4 派发硬门禁）接入派发链路后略有变化，聚合逻辑提前按旧格式写会错**。缓解：chg-05（done 交付总结扩效率与成本段）依赖 chg-04（usage-reporter 废止前提）但不依赖 chg-06；本 chg 按现有 `record_subagent_usage` 实际写出的 yaml 格式读；pytest mock 用真实 helper 写一批 entries 再触发 done 聚合，避免手写虚构格式。
- **风险 2：四子字段顺序若被后续需求悄悄调整会破坏契约**。缓解：AC-11 明文锁字段顺序；pytest `test_done_delivery_summary_field_order_fixed` 专测顺序；若未来需改，走新 req。
- **风险 3：done subagent pytest 依赖 `record_subagent_usage` 真实写入可能与 chg-06 发生耦合**。缓解：本 chg 只测 done 聚合的"读 + 格式化"逻辑，写入部分用 pytest fixture 手动填真实格式 yaml；与 chg-06 的派发链路硬门禁无时序依赖。
- **风险 4：mock usage-log 为空时 "⚠️ 无数据" 标记若被后续自动化工具误清洗**。缓解：done.md 文字明确禁止编造；pytest `test_done_delivery_summary_empty_usage_log` 断言"⚠️ 无数据"字样落盘。
