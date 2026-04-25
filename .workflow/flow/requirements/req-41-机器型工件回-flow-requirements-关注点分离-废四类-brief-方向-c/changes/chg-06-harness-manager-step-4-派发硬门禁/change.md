# Change

## 1. Title

harness-manager §3.6 Step 4 派发硬门禁 + 召唤词清理

## 2. Goal

- `harness-manager.md` §3.6 派发协议 Step 4（处理返回）升级为硬门禁："每次 Agent 工具返回后，主 agent 必调 `record_subagent_usage(root, role, model, usage, req_id=..., stage=..., chg_id=..., reg_id=...)`"，含从 Agent 返回值提取字段的 mapping 示例（input_tokens / output_tokens / cache_read_input_tokens / cache_creation_input_tokens / total_tokens / tool_uses / duration_ms）；删除 §3.5.3 召唤词清单中"生成用量报告 / 耗时报告 / token 消耗报告 / 工作流效率报告"四条；新增 base-role 级自检规则（done 六层回顾 State 层 grep `record_subagent_usage` 调用次数 ≥ 派发次数 - 容差）。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- `.workflow/context/roles/harness-manager.md`：
  - §3.6 派发协议 Step 4（处理返回）升级为硬门禁陈述，至少含：
    - 明示条款："每次 Agent 工具返回后，主 agent **必调** `record_subagent_usage(root, role, model, usage, req_id=..., stage=..., chg_id=..., reg_id=...)`；漏调视为契约违反（done 六层回顾 State 层强校验）"；
    - 字段 mapping 示例代码块：从 Agent 返回值 `response.usage` 提取各字段 → 传入 helper；
    - 异常降级路径：若 Agent 返回无 usage 字段（mock / test），`record_subagent_usage` 按 `usage=None` 写 stub entry（不硬失败）；
  - §3.5.3 召唤词清单删除四触发词：`生成用量报告` / `耗时报告` / `token 消耗报告` / `工作流效率报告`；
  - 其他召唤词维持不动；
- `.workflow/context/roles/base-role.md`：
  - 在 done 六层回顾 State 层（若既有段存在）或经验沉淀段添加自检规则："State 层 grep `record_subagent_usage` 调用次数应 ≥ 本 req 派发 Agent 次数 - 容差（容差 = 失败派发次数 + 降级 stub 次数）"；
  - 保留既有硬门禁六 / 七 / 契约 7 不动；
- 同步 mirror：
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`；
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`；
- 涉及文件：
  - live：`.workflow/context/roles/harness-manager.md` / `.workflow/context/roles/base-role.md`
  - mirror：同上两文件在 scaffold_v2 对应路径

### Excluded

- **不改** `record_subagent_usage` helper 内部实现（已实现，Excluded 明文声明）；
- **不改** CLI 代码（归属 chg-02（CLI 路径迁移 flow layout））；
- **不动** `validate_human_docs.py`（归属 chg-03（validate_human_docs 重写删四类 brief））；
- **不改** 其他角色文件的"对人文档产出契约"（归属 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止））；
- **不改** `done.md` 交付总结模板 / Step 6 聚合（归属 chg-05（done 交付总结扩效率与成本段））；
- **不扩** 硬门禁六文字覆盖面（归属 chg-08（硬门禁六扩 TaskList + stdout + 提交信息））；
- **不动** `record_feedback_event` / `feedback.jsonl` 格式；
- **不动** `stage_timestamps` 写入逻辑。

## 5. Acceptance

- Covers requirement.md **AC-10**（harness-manager Step 4 硬门禁陈述）：
  - `grep -q "record_subagent_usage" .workflow/context/roles/harness-manager.md` 命中 ≥ 1 次；
  - `grep -q "硬门禁" .workflow/context/roles/harness-manager.md` §3.6 附近至少 1 次；
  - `grep -q "每次 Agent" .workflow/context/roles/harness-manager.md` 或语义等价陈述命中；
- Covers requirement.md **AC-12**（usage-reporter 召唤词清理）：
  - `grep -cE "生成用量报告|耗时报告|token 消耗报告|工作流效率报告" .workflow/context/roles/harness-manager.md` 命中数 = 0；
- Covers requirement.md **AC-15**（scaffold_v2 mirror 同步）：
  - `diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` 无输出；
  - `diff -q .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` 无输出；
- Covers requirement.md **AC-13 (c)**（usage-log 真实 entries）起点：
  - 本 chg 落地后，chg-07（dogfood 活证 + scaffold_v2 mirror 收口）dogfood 跑 req-41（机器型工件回 flow）自身 → `.workflow/flow/requirements/req-41-{slug}/usage-log.yaml` 存在 ≥ 1 条真实 entry；
- Covers requirement.md **AC-06**（回归不破坏）：
  - `pytest tests/` 全量绿。

## 6. Risks

- **风险 1：主 agent 实际派发链路代码可能不在 harness-manager.md 文档管辖范围（文档是规约，实际是 Claude runtime）**。缓解：本 chg 的硬门禁是"文档契约层面"约束，落地靠主 agent（technical-director / harness-manager 加载者）遵守；pytest 无法强校验 LLM 行为，改由 dogfood 跑完看 usage-log.yaml 是否真 ≥ 1 条 entry 作事实层验证；done 六层回顾 grep 作补充。
- **风险 2：Step 4 硬门禁文字与既有 Step 4 表述冲突**。缓解：executing 先读现有 §3.6 Step 4 全文，按 "升级" 语义而非"替换"保留上下文；明确新硬门禁在 Step 4 子条款位置叠加，不破坏既有 Step 1-3 / Step 5-7 流程。
- **风险 3：base-role.md 自检规则与现有硬门禁（六 / 七）冲突**。缓解：新规则单独成段，标注 "并列生效"；不改硬门禁六 / 七 任何文字；grep 验证 base-role.md 硬门禁六 / 七 段落 diff 只限定新增区域。
- **风险 4：召唤词清理漏删留残**。缓解：`grep -cE "生成用量报告|耗时报告|token 消耗报告|工作流效率报告"` 断言命中数 = 0；执行中每删一词立即 grep 复查。
