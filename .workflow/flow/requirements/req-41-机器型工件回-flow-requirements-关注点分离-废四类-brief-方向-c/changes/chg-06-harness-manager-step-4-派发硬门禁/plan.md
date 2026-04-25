# Change Plan — chg-06（harness-manager §3.6 Step 4 派发硬门禁）

## 1. Development Steps

### Step 1: 读取 harness-manager.md + base-role.md 相关段

- 读取 `.workflow/context/roles/harness-manager.md` 全文，定位：
  - §3.5.3 召唤词清单（含四条要删除的触发词）；
  - §3.6 派发协议 Step 4（处理返回）段；
- 读取 `.workflow/context/roles/base-role.md`，定位 "经验沉淀规则" / done 六层回顾相关段（若存在）或最靠后的硬门禁段，作为新增自检规则落位候选；
- 读取 `src/harness_workflow/workflow_helpers.py` 中 `record_subagent_usage` 签名与 usage 字段结构；
- 产出清单到 chg-06 session-memory.md。

### Step 2: 升级 harness-manager.md §3.6 Step 4 为硬门禁

- 在 Step 4（处理返回）段首新增明示条款：
  ```markdown
  > **硬门禁（req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ chg-06（harness-manager Step 4 派发硬门禁））**：
  > 每次 Agent 工具返回后，主 agent **必调** `record_subagent_usage(root, role, model, usage, req_id=..., stage=..., chg_id=..., reg_id=...)`；
  > 漏调视为契约违反（done 六层回顾 State 层强校验）。
  ```
- 紧随加字段 mapping 示例（Python 伪码）：
  ```python
  # 从 Agent 工具返回值提取 usage（Claude API 格式）：
  usage = {
      "input_tokens": response.usage.input_tokens,
      "output_tokens": response.usage.output_tokens,
      "cache_read_input_tokens": response.usage.cache_read_input_tokens or 0,
      "cache_creation_input_tokens": response.usage.cache_creation_input_tokens or 0,
      "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
      "tool_uses": len([b for b in response.content if b.type == "tool_use"]),
      "duration_ms": elapsed_ms,
  }
  record_subagent_usage(
      root,
      role=dispatched_role,      # 如 "analyst" / "executing"
      model=dispatched_model,    # 如 "opus" / "sonnet"
      usage=usage,
      req_id=current_req_id,
      stage=current_stage,
      chg_id=current_chg_id,     # 可为 None
      reg_id=current_reg_id,     # 可为 None
  )
  ```
- 异常降级：若 Agent 返回无 `usage` 字段（mock / test），helper 按 `usage=None` 写 stub entry（记录 role / model / timestamp，token 字段空）；
- 保留既有 Step 4 其他陈述（若有 error handling / retry 逻辑不动）。

### Step 3: 删除 §3.5.3 四条召唤词

- 定位 §3.5.3 召唤词清单段；
- 删除四行触发词：
  - `生成用量报告`
  - `耗时报告`
  - `token 消耗报告`
  - `工作流效率报告`
- 若清单整段因此缩短到 0 项，保留段标题 + 说明"（usage-reporter 角色已于 req-41（机器型工件回 flow + 废四类 brief）废止）"；
- 其他召唤词维持不动（如 `生成项目现状报告` → project-reporter 仍保留）。

### Step 4: base-role.md 新增自检规则段

- 在 base-role.md "经验沉淀规则" 段**之后** / "硬门禁七" 段**之前**（或追加到 "经验沉淀规则" 段末尾）新增独立一节：
  ```markdown
  ## done 六层回顾 State 层自检（req-41（机器型工件回 flow/requirements）/ chg-06（harness-manager Step 4 派发硬门禁））

  > 溯源：req-41 / chg-06；与既有硬门禁六 / 七、契约 7 并列生效，不替代。

  done 阶段六层回顾 State 层 grep 校验：
  - 读取 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml` 计 subagent_usage entries 数；
  - 读取 session-memory 树计主 agent 派发 Agent 工具次数；
  - 断言 `entries 数 ≥ 派发次数 - 容差`（容差 = 失败派发次数 + 降级 stub 次数）；
  - 不满足时 done 报告本 req "usage 采集不完整"，列缺失派发清单。
  ```
- 不改现有硬门禁六 / 七 / 契约 7 任何文字；
- 保留段与段之间空行结构。

### Step 5: 同步 scaffold_v2 mirror

- `cp .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`；
- `cp .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`；
- `diff -q` 两组零输出。

### Step 6: 自检 + 交接

- `grep -c "record_subagent_usage" .workflow/context/roles/harness-manager.md` ≥ 2（硬门禁陈述 + 字段 mapping 示例）；
- `grep -cE "生成用量报告|耗时报告|token 消耗报告|工作流效率报告" .workflow/context/roles/harness-manager.md` 命中数 = 0；
- `grep -q "State 层自检" .workflow/context/roles/base-role.md`；
- `diff -q` mirror 零输出；
- `pytest tests/` 全量绿；
- 更新 chg-06 session-memory.md。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `[ $(grep -c "record_subagent_usage" .workflow/context/roles/harness-manager.md) -ge 2 ]`
- `grep -q "硬门禁.*record_subagent_usage\|每次 Agent.*record_subagent_usage" .workflow/context/roles/harness-manager.md`
- `[ $(grep -cE "生成用量报告|耗时报告|token 消耗报告|工作流效率报告" .workflow/context/roles/harness-manager.md) -eq 0 ]`
- `grep -q "req-41.*chg-06" .workflow/context/roles/base-role.md`（自检规则溯源）
- `diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`（零输出）
- `diff -q .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`（零输出）
- `pytest tests/`（全量绿）

### 2.2 Manual smoke / integration verification

- 人工抽读 harness-manager.md §3.6 Step 4 新硬门禁段，确认 "每次 Agent 工具返回 → `record_subagent_usage`" 语义明确、字段 mapping 示例完整；
- 人工抽读 §3.5.3 召唤词清单，确认四条触发词已删；
- 人工抽读 base-role.md 新增自检段，确认与既有硬门禁六 / 七 / 契约 7 并列无冲突；
- dogfood 端到端：chg-07（dogfood 活证 + scaffold_v2 mirror 收口）跑 req-41（机器型工件回 flow）自身 → 读 `.workflow/flow/requirements/req-41-{slug}/usage-log.yaml` ≥ 1 条真实 entry（不是 stub）。

### 2.3 AC Mapping

- AC-10（harness-manager Step 4 硬门禁陈述） → Step 2 + 2.1 grep；
- AC-12（usage-reporter 召唤词清理） → Step 3 + 2.1 grep 四词命中 = 0；
- AC-15（scaffold_v2 mirror 同步） → Step 5 + 2.1 diff；
- AC-13 (c) 起点（usage-log ≥ 1 真实 entry） → Step 2 硬门禁落地 + chg-07 dogfood 端到端验证；
- AC-06（回归不破坏） → 2.1 pytest 全量绿。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（repository-layout 契约底座）+ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）；chg-04 先行确保 usage-reporter 文件与 role-model-map 已清；
- **可并行邻居**：chg-05（done 交付总结扩效率与成本段）（都依赖 chg-04）；
- **后置依赖**：chg-07（dogfood + scaffold_v2 mirror 收口）做 usage-log ≥ 1 真实 entry 的事实层验证；
- **本 chg 内部顺序**：Step 1 读取 → Step 2 Step 4 硬门禁升级 → Step 3 召唤词清理 → Step 4 base-role 自检段 → Step 5 mirror → Step 6 自检；可并行（Step 2/Step 3/Step 4 文件耦合度低），但建议串行避免 diff 冲突。
