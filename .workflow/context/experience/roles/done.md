# Done Stage Experience

## 经验：单表 §效率与成本 渲染实操（chg-03 落地后新格式）

### 场景

req-43（交付总结完善）/ chg-03（per-stage 合并到 stage × role × model 单表渲染）落地后，done 阶段交付总结 §效率与成本段从「各阶段耗时分布」+「各阶段 token 分布」两表合并为单表「各阶段切片（stage × role × model × token × tool_uses）」9 列。

### 经验内容

实操要点：

1. **数据来源固定**：单表数据来自 `done_efficiency_aggregate(root, req_id, task_type="req")` 返回的 `stage_role_rows` 字段，9 列字段顺序 = `stage / role / model / input_tokens / output_tokens / cache_read_input_tokens / cache_creation_input_tokens / total_tokens / tool_uses`，**字段顺序不得变更**（变更须走新 req）；
2. **`⚠️ 无数据` 行为约定**：`usage-log.yaml` 不存在或 entries 为空时，helper 返回 `_NO_DATA` 标记 → 渲染层每个 token 列填 `⚠️ 无数据`；**禁编造**任何数值（done.md Step 6.x #6 硬规则）；
3. **stage 维度 vs role 维度的取舍**：单表 (stage, role, model) 三键 group by → 同一 stage 内多 subagent 派发会展开为多行；duration_s 列由 stage_timestamps 推算（next_stage.entered_at − this_stage.entered_at），**不**写入 stage_role_rows，渲染时单独从 `pure_stage_ts`（已修复过滤 `*_exited_at` 键）取；
4. **task_type 路径切换**：req → `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml`；bugfix / sug → `.workflow/state/sessions/{id}/usage-log.yaml`（chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）扩展）；done 角色调 helper 时务必显式传 task_type；
5. **legacy 字段保留**：`role_tokens` / `stage_durations` 字段在 helper 返回值中保留（向后兼容历史归档），新字段是 `stage_role_rows`；旧两表交付总结（如 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ req-42（archive 重定义：对人不挪 + 摘要废止））按旧格式保留不重渲。

### 反例

- usage-log 缺失时编造数值（如填"约 50000"或"基于历史均值"） → 违反 done.md Step 6.x #6 禁编造规则 → reviewer 阻断 done；
- 字段顺序乱改（如把 cache_read 放到 total 后面） → 渲染单表与 done.md 模板契约不一致 → contract test 红；
- 不传 task_type → bugfix / sug 走 req 路径找不到 usage-log → 误判为「无数据」实际是路径错。

### 来源

req-43（交付总结完善）/ chg-03（per-stage 合并到 stage × role × model 单表渲染） — done.md Step 6.x #5 单表渲染契约 + done_efficiency_aggregate stage_role_rows 字段

---

## 经验：bugfix / sug 模板分支实操（chg-04 / chg-05 落地）

### 场景

req-43（交付总结完善）落地后，done 角色（更准确说是 done.md 模板）成为 req / bugfix / sug 三类任务统一对人产出口径的承载点。bugfix 用 done.md `## bugfix 交付总结模板（精简版）` 段；sug 用 `_create_sug_delivery_summary` helper 自动产出 3 段轻量。

### 经验内容

实操要点：

1. **bugfix 模板精简版**：
   - 落位：`artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/bugfix-交付总结.md`；
   - 五段：需求是什么 / 修复了什么 / 修复验证（合并 testing+acceptance）/ 结果是什么 / 后续建议 + § 效率与成本（单表）；
   - **删 chg 段**（bugfix 通常不拆 chg，diagnosis.md 直接驱动）；
   - bugfix 经历的 stage：`regression` / `executing` / `testing` / `acceptance`，单表按此 stage_order 排序；
   - 由 `acceptance` 后置 hook 产出，**不新增 done stage**（D-2 default-pick）；
2. **sug 轻量 3 段（直接处理路径，非转 req）**：
   - 落位：`artifacts/{branch}/suggestions/{sug-id}-{slug}/交付总结.md`；
   - 三段：建议是什么 / 处理结果（含 action: applied / archived / rejected）/ 后续；
   - **无「交付了什么」段**（sug 直接处理通常无独立交付物）；
   - 由 `archive_suggestion` / `harness suggest --apply / --archive / --reject` 触发 `_create_sug_delivery_summary` 自动产出；
   - sug → req 转化路径**豁免**（`status: converted-to-req` 不校验 sug 自身交付总结，由对应 req 的 `交付总结.md` 承载）；
3. **State 层自检扩三类任务**：base-role.md `## done 六层回顾 State 层自检` 已扩 — 按 task_type 读对应 usage-log.yaml + 计 entries 数 ≥ 派发次数 - 容差；done 角色六层回顾 State 层必跑此校验；
4. **validate_human_docs 三类一致**：`harness validate --human-docs` 对 req / bugfix / sug 三类同等扫描（`_collect_bugfix_items` / `_collect_suggestion_items` 函数），缺失即阻断归档。

### 反例

- bugfix 模板照搬 req 模板（含 chg 段） → 与 done.md 精简版契约不一致 → reviewer 阻断；
- sug 走 4 段（多写「交付了什么」） → 与 `_create_sug_delivery_summary` 3 段契约不一致 → contract test 红；
- bugfix usage-log 在 req 路径找 → 永远找不到（路径错） → 误判为无数据。

### 来源

req-43（交付总结完善）/ chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版）） + chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务） — done.md bugfix / sug 分支模板 + `_create_sug_delivery_summary` helper + base-role.md State 层自检扩三类任务
