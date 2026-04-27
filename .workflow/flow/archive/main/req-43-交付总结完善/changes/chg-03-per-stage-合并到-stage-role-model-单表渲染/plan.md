# Change Plan — chg-03（per-stage 合并到 stage × role × model 单表渲染）

> 所属 req：req-43（交付总结完善）；前置依赖：chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））（无 entries 渲染恒空）；可与 chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳） 并行。

## §目标

解决 AC-02 + OQ-4：扩 `done_efficiency_aggregate` helper 增加 stage 维度 group by；done.md `## 对人文档输出` 模板把「各阶段耗时分布」+「各阶段 token 分布」**合并为单表**「stage × role × model × token × tool_uses」（OQ-4 用户已确认 default-pick B），列固定为 `stage / role / model / input_tokens / output_tokens / cache_read_input_tokens / cache_creation_input_tokens / total_tokens / tool_uses`，按 stage_order + total_tokens desc 排序；保留旧返回字段（`role_tokens` / `stage_durations`）向后兼容供历史归档 req 重渲。

## §影响文件列表

- `src/harness_workflow/workflow_helpers.py::done_efficiency_aggregate`（line 2797-2965）：返回 dict 新增 `stage_role_rows: list[dict]` 字段，按 (stage, role, model) 三键 group by 聚合 token 七字段；保留 `role_tokens` / `stage_durations` 字段（向后兼容标记 `# legacy 字段，req-43+ 模板不再渲染`）；新增 `_NO_DATA` 占位逻辑覆盖单表场景。
- `.workflow/context/roles/done.md` `## 对人文档输出` 最小字段模板（line 100-152）：删除「各阶段耗时分布」+「各阶段 token 分布」两表，新增单表「各阶段切片（stage × role × model × token × tool_uses）」（9 列）；新增模板说明文字「req-43+ 起统一单表，req-41 / req-42 历史交付总结按旧两表保留不重渲」。
- `tests/test_done_efficiency_aggregate.py`（**新增 / 扩**）：覆盖 stage 维度聚合的 entries 缺失 / 部分缺失 / 全齐 三 fixture × stage 切片维度 ≥ 6 case。
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`：scaffold mirror 同步。
- `src/harness_workflow/assets/templates/`：检查是否有 `.tmpl` 文件渲染 done 交付总结模板（如 regression-decision.md.tmpl 类似），若有则同步。

## §实施步骤

1. 改 `done_efficiency_aggregate` helper：新增 stage 维度 group by 逻辑，以 entry.stage 作为 key，按 (stage, role, model) 三键 group by；聚合 token 七字段（input/output/cache_read/cache_creation/total_tokens + tool_uses + duration_ms）。
2. 输出新字段 `stage_role_rows: list[{stage, role, model, input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens, total_tokens, tool_uses}]`，按预定义 stage_order（requirement_review / planning / ready_for_execution / executing / testing / acceptance / regression / done）+ total_tokens desc 二级排序；entries 缺失时返回 `[{"stage": s, "role": _NO_DATA, ...} for s in known_stages]` 兜底。
3. 改 `done.md` `## 对人文档输出` 模板：删两表段，新单表段「各阶段切片（stage × role × model × token × tool_uses）」9 列；保留「总耗时」「总 token」两段不动；模板说明加「req-43+ 起统一单表」注脚。
4. 写 / 扩 pytest `tests/test_done_efficiency_aggregate.py` ≥ 6 case：stage_role_rows 全齐 / 单 stage 缺失 / 单 entry 缺 stage 字段 / multi-role 同 stage 多行聚合 / role 重复同 stage 累加 / 历史 req 旧 schema 兼容（无 task_type 字段）。
5. scaffold mirror 同步 `done.md`：`diff src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md .workflow/context/roles/done.md` exit 0。
6. 反向自证：用 chg-01 真接通后 req-43 自身的 usage-log.yaml 跑 helper，返回的 stage_role_rows 至少含 planning / executing / testing / acceptance / done 五 stage 行（无数据格按 `⚠️ 无数据` 占位）。
7. 收口：`harness validate --human-docs` exit 0 + `pytest tests/` 全绿（基线 + 6 条新 case）。

## §测试用例设计

> regression_scope: targeted（helper 扩字段 + 模板改写，旧字段保留向后兼容）
> 波及接口清单（git diff --name-only 预估 + 人工补全）：
> - `src/harness_workflow/workflow_helpers.py::done_efficiency_aggregate`
> - `.workflow/context/roles/done.md`（对人文档输出模板段）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 stage_role_rows 全齐 | usage-log 含 5 stage × 3 role 共 15 entries | 返回 stage_role_rows 含 ≥ 15 行；按 stage_order 排序；每行 9 列齐全 | AC-02 | P0 |
| TC-02 单 stage 缺失 | usage-log 缺 testing 阶段 entries | testing 行不出现 / 或按 _NO_DATA 占位（按实现选）；其它 stage 正常 | AC-02 / AC-04 | P0 |
| TC-03 entries 全空 | usage-log.yaml 不存在或为空 | stage_role_rows 返回 _NO_DATA 占位行（不抛异常） | AC-02 / AC-04 | P0 |
| TC-04 multi-role 同 stage 聚合 | executing stage 含 sonnet × 2 role + opus × 1 role 三 entries | executing 出 3 行（按 (stage, role, model) 唯一）；token 不重复累加 | AC-02 | P0 |
| TC-05 同 (stage, role, model) 多 entry 累加 | executing × executing × sonnet 共 5 entries | 聚合为 1 行；total_tokens / tool_uses 是 5 entries 之和 | AC-02 | P0 |
| TC-06 历史 req 旧 schema 兼容 | usage-log entries 无 task_type 字段（chg-01 前历史数据） | helper 不抛异常；按默认 task_type="req" 处理；stage_role_rows 仍生成 | AC-04 | P1 |
| TC-07 done.md 模板单表渲染 | 跑 req-43 自身 done 阶段输出 `交付总结.md` | §效率与成本段含单表（9 列）+ 总耗时段 + 总 token 段；不含旧两表 | AC-02 | P0 |
| TC-08 scaffold mirror 同步 | `diff scaffold_v2/.workflow/context/roles/done.md .workflow/context/roles/done.md` | exit 0（无 diff） | AC-04（前置） | P1 |

## §验证方式

- **AC-02（per-stage token 字段齐全）**：TC-01 / TC-04 / TC-05 / TC-07；req-43 自身 done 阶段产出的「交付总结.md」§效率与成本段必含单表，每经历过的 stage 至少 1 行非空（无数据按 `⚠️ 无数据` 占位）。
- **AC-04（数据通路只消费不重采）**：TC-02 / TC-03 / TC-06 helper 单测覆盖「entries 缺失 / 部分缺失 / 全齐」三 fixture 全过。
- pytest：`pytest tests/test_done_efficiency_aggregate.py -v` 全绿 + 基线不退化。
- 反向自证：跑 helper 输入 req-43 真实 usage-log.yaml，stage_role_rows 至少含 5 stage。

## §回滚方式

`git revert` chg-03（per-stage 合并到 stage × role × model 单表渲染） 的所有 commit；旧返回字段 `role_tokens` / `stage_durations` 已保留向后兼容，可单独回滚 done.md 模板而不动 helper（解耦回滚）。

## §scaffold_v2 mirror 同步范围

按 harness-manager.md 硬门禁五：
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md` ↔ `.workflow/context/roles/done.md`（diff 应 = 0）

`workflow_helpers.py` + `tests/` 不在 mirror 范围。

## §契约 7 注意点

- 本 plan.md 首次引用工作项 id 已带 title：req-43（交付总结完善）/ chg-03（per-stage 合并到 stage × role × model 单表渲染）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））/ chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）/ chg-05（done.md 交付总结模板扩 §效率与成本）（属 req-41 历史 chg）/ req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ req-42（archive 重定义：对人不挪 + 摘要废止）。
- 提交信息须形如：`feat: chg-03（per-stage 合并到 stage × role × model 单表渲染）helper + done.md 模板` —— 带 ≤ 15 字描述（硬门禁六）。
