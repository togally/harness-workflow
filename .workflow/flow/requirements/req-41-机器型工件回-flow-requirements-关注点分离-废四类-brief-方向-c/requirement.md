# Requirement

## 1. Title

机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）

## 2. Goal

承接 reg-01（artifacts 布局语义复核：需求文档归属 + flow/requirements 应否复用）用户原话——"绝对不应该 requirements 和 change 都跑到制品仓库去"——把工作流机器型工件从 `artifacts/` + `.workflow/state/` 整体回退到 `.workflow/flow/requirements/req-XX/` 子树，让 `.workflow/state/` 回归"runtime 真·实时数据"语义；与此并列，废止四类对人 brief（需求摘要 / 变更简报 / 实施说明 / 回归简报），artifacts 只留 raw `requirement.md` 副本 + 真·对外产物（SQL / 部署 / 接入 / 交付总结 / 决策汇总）；同时把 `record_subagent_usage` 接入主 agent 真实派发链路、把效率字段并进 `交付总结.md`，废止独立的耗时与用量报告。本需求落地后即用 req-41（本需求：机器型工件回 flow + 关注点分离）自身（机器型在 flow/、artifacts 无四类 brief、交付总结含效率段、usage-log 有真实 entries）作 dogfood 活证。

四 scope 概览：**Scope-共骨架**（顶层契约扩管 + 角色去路径化）/ **Scope-C**（机器型工件迁移到 `.workflow/flow/requirements/req-XX/`）/ **Scope-废 brief**（四类对人 brief 删除 + 白名单清理 + validate 重写）/ **Scope-效率字段**（usage 采集硬门禁 + 交付总结模板扩展 + usage-reporter 收窄/废止）。

## 3. Scope

### 3.1 Scope-共骨架（顶层契约扩管 + 角色文件去路径化）

**Included**：
- 把 `.workflow/flow/artifacts-layout.md` **重命名**为 `.workflow/flow/repository-layout.md`（语义升格：从"artifacts 子树语义"扩到"全仓库三大子树语义"），原文件 git mv 保留 history；新文件 §1 总览 + §2 三大子树（`.workflow/state/` / `.workflow/flow/` / `artifacts/`）一次性定义每类文档的唯一权威落位
- `.workflow/state/` 子树语义收窄：只装 runtime 数据（`runtime.yaml` / `feedback/feedback.jsonl` / `action-log.md` / `experience/index.md` 等运行时缓存）；**不再**承载 `requirements/{req-id}/` / `sessions/{req-id}/` 两类机器型工件子树
- `.workflow/flow/requirements/{req-id}-{slug}/` 子树语义重新启用（reg-01 现状盘点为"空"），承载所有 req 周期机器型工件：`requirement.md` / `changes/{chg-id}-{slug}/{change.md, plan.md, session-memory.md}` / `regressions/{reg-id}-{slug}/{regression.md, analysis.md, decision.md, meta.yaml, session-memory.md}` / `task-context/` / `usage-log.yaml` / req yaml（`stage_timestamps`）
- `artifacts/{branch}/requirements/{req-id}-{slug}/` 子树语义收窄：只装"对人可读 / 可签字 / 可执行"产物 —— raw `requirement.md`（authoritative 副本，方便外部审阅，不参与流程引擎读写）+ `交付总结.md` + `决策汇总.md` + SQL / 部署文档 / 接入配置说明 / runbook / 手册 / 合同附件
- 角色文件 `analyst.md` / `executing.md` / `regression.md` / `done.md` / `testing.md` / `acceptance.md` / `usage-reporter.md` 去除硬编码路径段（如 `→ artifacts/{branch}/requirements/{req-id}-{slug}/xxx.md`），改为"产出 `{doc-type}`（落位见 `.workflow/flow/repository-layout.md`）"统一引用契约

**Excluded**：
- 不动 `.workflow/context/` / `.workflow/constraints/` / `.workflow/tools/` 三类子树语义
- 不动归档子树 `.workflow/flow/archive/` / `artifacts/{branch}/archive/` 现状（legacy 豁免延续）

### 3.2 Scope-C（机器型工件迁移：state/ → flow/requirements/）

**Included**：
- 新增常量 `FLOW_LAYOUT_FROM_REQ_ID = 41`（`src/harness_workflow/workflow_helpers.py`）；`LEGACY_REQ_ID_CEILING = 38` 与 `FLAT_LAYOUT_FROM_REQ_ID = 39` 保留不动
- 新增 helper `_use_flow_layout(req_id) -> bool`（req-id ≥ 41 → True），与既有 `_use_flat_layout` 并列；`_use_flow_layout(x) → True` 时 `_use_flat_layout(x)` 同样为 True（flow 层是 flat 层的超集），不互斥
- `create_requirement` / `create_change` / `create_regression` / `archive_requirement` 四个 CLI handler 改写：req-id ≥ 41 时机器型工件全部写入 `.workflow/flow/requirements/{req-id}-{slug}/...`；req-id ∈ [39, 40]（已归档 req-39（对人文档家族契约化）/ 活跃 req-40（阶段合并与用户介入窄化））仍走 state/ legacy fallback；req-id ≤ 38 维持原 legacy 路径
- 配套 helper：`resolve_requirement_root` / `resolve_requirement_reference` / `_resolve_target` / `load_requirement_runtime` 等 path resolver 同步识别新位；`harness archive` 把 `.workflow/flow/requirements/req-XX/` 整体搬到 `.workflow/flow/archive/{branch}/req-XX-{slug}/` 下
- pytest fixture 与 scaffold_v2 mirror 同步常量与新位

**Excluded**：
- 不迁移 req-39 / req-40 已落地的 state/sessions/ 内容（避免破坏归档 + 活证）
- 不动 `.workflow/state/sessions/` 历史目录的物理位置（仅未来新 req 不再写入）
- 不动 `.workflow/state/feedback/` / `runtime.yaml` / `action-log.md` 的位置

### 3.3 Scope-废 brief（删四类对人 brief + 白名单清理 + validate 重写）

**Included**：
- `.workflow/flow/repository-layout.md` §2 对人文档白名单**删除**四行：`需求摘要.md` / `chg-NN-变更简报.md` / `chg-NN-实施说明.md` / `reg-NN-回归简报.md`；保留：raw `requirement.md`（authoritative 副本）/ `交付总结.md` / `决策汇总.md` / SQL / 部署 / 接入 / runbook / 手册 / 合同附件 / 其他对人产物
- `src/harness_workflow/validate_human_docs.py` 重写扫描逻辑（`HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` / `BUGFIX_LEVEL_DOCS` 常量）：req-id ≥ 41 不再校验四类 brief，只校验 raw `requirement.md`（artifacts 副本）+ `交付总结.md`；新增常量 `BRIEF_DEPRECATED_FROM_REQ_ID = 41`
- 角色文件 `analyst.md` / `executing.md` / `regression.md` 的"对人文档产出契约"段删除四类 brief 模板，只保留交付总结模板（移到 `done.md`）；`stage-role.md` 契约 3 表格删除对应行；契约 4 硬门禁同步精简
- `harness validate --human-docs` 行为：对 req-id ∈ [02, 38] 走 legacy（已废扫描，与 req-39（对人文档家族契约化）/ chg-02（对人文档家族契约化·变更 02）一致）；req-id ∈ [39, 40] 维持现行扫描；req-id ≥ 41 走新精简校验（只看 raw + 交付总结 + decision + 真·对外产物）
- `stage-role.md` 契约 4 第三个 bullet（`harness validate --contract all` 自检）维持，但触发的扫描由本 scope 重写后自然精简

**Excluded**：
- **不迁移、不删除**历史存量 brief：`artifacts/main/requirements/req-02 ~ req-40` 下已存在的 `需求摘要.md` / `chg-NN-变更简报.md` / `chg-NN-实施说明.md` / `reg-NN-回归简报.md` 一律原地保留（git log 自带分水岭）
- 不动 `测试结论.md` / `验收摘要.md`（已由 req-31（角色功能优化整合与交互精简）/ chg-04（S-D 对人文档缩减）废止，本 scope 与之并列生效）
- 不重命名"交付总结"或"决策汇总"

### 3.4 Scope-效率字段（usage 采集硬门禁 + 交付总结扩段 + usage-reporter 收窄）

**Included**：
- `.workflow/context/roles/harness-manager.md` §3.6 派发协议 Step 4（处理返回）**升级为硬门禁**：每次 Agent 工具返回后，主 agent **必调** `record_subagent_usage(root, role, model, usage, req_id=..., stage=..., chg_id=..., reg_id=...)`；从 Agent 返回值提取 `usage` 字段（`input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens` / `total_tokens` / `tool_uses` / `duration_ms`）；漏调视为契约违反（done 阶段六层回顾 State 层强校验）
- `done.md` 角色文件交付总结模板 §最小字段模板新增 "## 效率与成本" 段，固定四子字段：
  - 总耗时（s + 人类可读）
  - 总 token（input / output / cache_read / total）
  - 各阶段耗时分布（按 stage 排序，stage / 进入时间 / 耗时秒）
  - 各阶段 token 分布（按 role × model 排序，role / model / total_tokens / tool_uses）
- `done.md` SOP Step 6 加一步"读取 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml` + req yaml `stage_timestamps`，聚合后写入交付总结 §效率与成本"；done subagent（opus）直接做聚合，不再召唤 usage-reporter
- `.workflow/flow/repository-layout.md` §2 对人文档白名单**删除** `耗时与用量报告.md` 这行
- `.workflow/context/roles/usage-reporter.md` **废止**（`git rm` 该角色文件）；同步从 `role-model-map.yaml` 删除 `usage-reporter: "sonnet"` 行；从 `harness-manager.md` 召唤词清单（§3.5.3）删除"生成用量报告 / 耗时报告 / token 消耗报告 / 工作流效率报告"触发词
- 配套 pytest 覆盖：新增 done subagent 模拟测试，断言 §效率与成本段四子字段都从 usage-log.yaml 真实采到（无 ⚠️ 无数据）

**Excluded**：
- 不改 `record_subagent_usage` helper 内部实现（已实现，只接入派发链路）
- 不改 `record_feedback_event` / `feedback.jsonl` 格式
- 不动 stage_timestamps 写入逻辑

## 4. Acceptance Criteria

### AC-01（Scope-共骨架）
`git mv .workflow/flow/artifacts-layout.md .workflow/flow/repository-layout.md` 完成；新文件 §1 总览段一次性列三大子树语义；§2 表格覆盖三大子树每类文档落位（含 raw requirement.md / change.md / plan.md / regression.md / 交付总结.md / 决策汇总.md / SQL / runbook 等）；`grep "artifacts-layout.md" .workflow/ -r` 命中数 = 0（全部改引到 repository-layout.md）。

### AC-02（Scope-共骨架）
`analyst.md` / `executing.md` / `regression.md` / `done.md` / `testing.md` / `acceptance.md` 六个角色文件中 `grep "→ artifacts/" .workflow/context/roles/{file}.md` 命中数 = 0（路径改为引用 repository-layout.md）。

### AC-03（Scope-C）
`src/harness_workflow/workflow_helpers.py` 新增 `FLOW_LAYOUT_FROM_REQ_ID = 41` 常量 + `_use_flow_layout(req_id) -> bool` helper；`pytest tests/ -k "test_use_flow_layout"` 至少 4 条用例通过（req-40（阶段合并用户介入窄化）→ False / req-41（本需求）→ True / req-50（未来虚拟需求）→ True / 非法 id → False）。

### AC-04（Scope-C）
`create_requirement(root, "test-flow-layout", requirement_id="req-41")` dry-run 路径校验：`requirement.md` 落 `.workflow/flow/requirements/req-41-{slug}/requirement.md`；`create_change("req-41", "test")` 落 `.workflow/flow/requirements/req-41-{slug}/changes/{chg-id}-{slug}/{change.md, plan.md}`；`create_regression("req-41", "test")` 落 `.workflow/flow/requirements/req-41-{slug}/regressions/{reg-id}-{slug}/{regression.md, ...}`；artifacts/ 下不再写机器型文件。

### AC-05（Scope-C，归档）
`harness archive req-41` dry-run：`.workflow/flow/requirements/req-41-{slug}/` 整体搬到 `.workflow/flow/archive/{branch}/req-41-{slug}/`；`.workflow/state/sessions/req-41/` 不存在（本 req 不写 state/sessions/）；`artifacts/{branch}/requirements/req-41-{slug}/` 保留对人产物。

### AC-06（Scope-C，回归不破坏）
`pytest tests/` 全量绿（含归档相关用例 / req-39 / req-40 fixture 用例）；`harness archive req-39` / `harness archive req-40` 行为不变（仍按 state/ legacy fallback）。

### AC-07（Scope-废 brief）
`.workflow/flow/repository-layout.md` §2 白名单 `grep -E "需求摘要|变更简报|实施说明|回归简报|耗时与用量报告"` 命中数 = 0；`grep -E "需求摘要|变更简报|实施说明|回归简报"` 在 `analyst.md` / `executing.md` / `regression.md` / `stage-role.md` 中命中数 = 0。

### AC-08（Scope-废 brief，validate 重写）
`src/harness_workflow/validate_human_docs.py` 新增常量 `BRIEF_DEPRECATED_FROM_REQ_ID = 41`；`HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` 删除四类 brief 项；`harness validate --human-docs req-41` 退出码 = 0 时只校验 raw `requirement.md`（artifacts 副本）+ `交付总结.md` 落盘，不报四类 brief missing；`harness validate --human-docs req-39` 仍按 req-39 规则扫描（不破坏既有行为）。

### AC-09（Scope-废 brief，pytest）
新增 pytest 用例 `test_validate_human_docs_brief_deprecated_req_41`：mock 一个 req-41 目录只放 `requirement.md` + `交付总结.md`，断言 validate 返回 exit 0、items 数 = 2、status 全 ok。

### AC-10（Scope-效率字段，硬门禁）
`.workflow/context/roles/harness-manager.md` §3.6 Step 4 段含明确"硬门禁：每次 Agent 工具返回后必调 `record_subagent_usage`"陈述（grep 命中 ≥ 1 次）；done.md Step 6 段含"读取 usage-log.yaml + stage_timestamps，聚合后写入 §效率与成本"陈述（grep 命中 ≥ 1 次）。

### AC-11（Scope-效率字段，模板扩展）
`done.md` 交付总结最小字段模板新增 "## 效率与成本" 段，含四子字段（总耗时 / 总 token / 各阶段耗时 / 各阶段 token）；模板字段顺序固定，不得变更。

### AC-12（Scope-效率字段，usage-reporter 废止）
`.workflow/context/roles/usage-reporter.md` 文件不存在（git rm）；`.workflow/context/role-model-map.yaml` 中 `usage-reporter: "sonnet"` 行不存在；`harness-manager.md` 召唤词清单 grep `生成用量报告|耗时报告|token 消耗报告|工作流效率报告` 命中数 = 0。

### AC-13（dogfood 活证）
本 req-41 自身按新契约产出：(a) 机器型 `requirement.md` / `changes/chg-XX/{change.md, plan.md, session-memory.md}` / `regressions/`（如有）落 `.workflow/flow/requirements/req-41-{slug}/`；(b) artifacts/main/requirements/req-41-{slug}/ 下**没有**四类 brief，只有 raw `requirement.md` 副本 + `交付总结.md`；(c) `.workflow/flow/requirements/req-41-{slug}/usage-log.yaml` 含 ≥ 1 条 subagent_usage 真实 entry；(d) `交付总结.md` §效率与成本段四子字段从 usage-log 真实聚合。

### AC-14（契约 7 + 硬门禁六 + 批量列举子条款自证）
本 req 全部产出文档（requirement.md / change.md / plan.md / repository-layout.md / 角色文件 / 交付总结）首次引用 req / chg / sug / bugfix / reg id 时均带 title 或 ≤ 15 字描述；批量列举场景（如 chg DAG 表）每条带描述，无 `chg-01/02/03` 裸数字扫射形态；`grep -nE "(req\|chg\|sug\|bugfix\|reg)-[0-9]+" .workflow/flow/requirements/req-41-{slug}/ -r` 自检命中行均含 `（...）` 或 `— ...`。

### AC-15（scaffold_v2 mirror 同步）
`src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`（mirror）与 `.workflow/flow/repository-layout.md`（活证）`diff` 输出零行；scaffold_v2 内引用 `artifacts-layout.md` 的旧路径 `grep` 命中数 = 0；`pytest tests/test_scaffold_v2_mirror.py`（或对应测试）绿。

### AC-16（统一精简汇报模板沿用）
本 req 的 analyst / executing / done 等 stage 角色批次汇报均按 stage-role.md 统一精简汇报模板四字段（产出 / 状态 / 开放问题 / 结尾「本阶段已结束。」）；`grep "本阶段已结束" .workflow/state/sessions/req-41/.../session-memory.md`（迁移前）/ `.workflow/flow/requirements/req-41-{slug}/.../session-memory.md`（迁移后）命中数 ≥ 4（覆盖各 stage）。

## 5. Split Rules

### 5.1 拆分原则（按 analyst 权责，自主决定不邀用户）

按 reg-01 用户选方向 C 的"用户只管需求"精神，本 req 拆分由 analyst 自主完成；拆分粒度按"一个 chg 一个收敛验收点 + 一类技术原子修改"原则，让 executing 可单独验证回归；DAG 依赖按"契约先行 → 代码跟上 → 角色去路径化 → 测试 + dogfood 收口"四层组织。

### 5.2 推荐 chg 拆分（共 7 chg）

#### chg-01（repository-layout 契约底座）：git mv + 三大子树 §2 重写

- 内容：`git mv .workflow/flow/artifacts-layout.md .workflow/flow/repository-layout.md`；§1 新增"三大子树语义总览"段；§2 重写白名单（删四类 brief + 删耗时报告 + 加 raw `requirement.md` artifacts 副本声明）；§3 重写"机器型文档迁移位"为"机器型文档权威落位（flow/requirements/）"；§4 / §5 历史存量豁免段同步加"req-39/40 双轨过渡 → req-41+ flow/ 落位"分水岭说明
- 产出：`.workflow/flow/repository-layout.md`（活证）；不改任何角色文件 / CLI 代码
- 依赖：无（DAG 根）

#### chg-02（CLI 路径迁移）：FLOW_LAYOUT_FROM_REQ_ID + create_/archive_ 改写

- 内容：`workflow_helpers.py` 新增 `FLOW_LAYOUT_FROM_REQ_ID = 41` + `_use_flow_layout` helper；改写 `create_requirement` / `create_change` / `create_regression` / `archive_requirement`，req-id ≥ 41 走 flow/requirements/ 路径；req-id ∈ [39, 40] 维持 state/ legacy；req-id ≤ 38 维持原 legacy；同步 `resolve_requirement_root` / `_resolve_target` 等 path resolver；新增 4+ 条 pytest 用例覆盖 `_use_flow_layout` 与 `create_*` 路径校验
- 产出：`src/harness_workflow/workflow_helpers.py` diff + `tests/test_use_flow_layout.py`（或并入既有 fixture 文件）
- 依赖：chg-01（契约先落地，代码按契约走）

#### chg-03（validate_human_docs 重写）：白名单清理

- 内容：`validate_human_docs.py` 新增 `BRIEF_DEPRECATED_FROM_REQ_ID = 41` 常量；`HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` / `BUGFIX_LEVEL_DOCS` 删四类 brief 项；`_collect_req_items` 加分支：req-id ≥ 41 走新精简扫描（raw `requirement.md` artifacts 副本 + `交付总结.md` 必查，其余可选）；新增 `test_validate_human_docs_brief_deprecated_req_41` 用例 + 不破坏 req-39 既有用例
- 产出：`src/harness_workflow/validate_human_docs.py` diff + 测试
- 依赖：chg-01（白名单是契约的代码化）

#### chg-04（角色去路径化 + brief 删除 + usage-reporter 废止）：角色文件去路径化 + 删四类 brief 模板

- 内容：`analyst.md` / `executing.md` / `regression.md` / `testing.md` / `acceptance.md` / `done.md` 六文件 grep `→ artifacts/` 全部改为"产出 `{doc-type}`（落位见 repository-layout.md）"；`analyst.md` / `executing.md` / `regression.md` 删四类 brief 模板段；`stage-role.md` 契约 3 表格删四行 + 契约 4 硬门禁同步精简；`role-model-map.yaml` 删 `usage-reporter` 行；`git rm .workflow/context/roles/usage-reporter.md`
- 产出：六角色文件 diff + `stage-role.md` diff + `role-model-map.yaml` diff + `usage-reporter.md` 删除
- 依赖：chg-01（路径引用先有权威源）

#### chg-05（done 交付总结扩效率与成本段）：done.md 模板扩 §效率与成本 + Step 6 聚合逻辑

- 内容：`done.md` 最小字段模板新增 "## 效率与成本"段（四子字段 + 字段顺序固定）；SOP Step 6 加聚合逻辑（读 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml` + req yaml `stage_timestamps`，按 stage / role × model 聚合写入交付总结）；删除 done.md 旧的"召唤 usage-reporter"残留陈述；新增 done subagent pytest 模拟用例
- 产出：`done.md` diff + 测试
- 依赖：chg-01（路径引用）+ chg-04（usage-reporter 废止前提）

#### chg-06（harness-manager Step 4 派发硬门禁）：§3.6 Step 4 升级硬门禁 + 召唤词清理

- 内容：`harness-manager.md` §3.6 Step 4（处理返回）段升级为硬门禁陈述："每次 Agent 工具返回后必调 `record_subagent_usage(...)`"，含字段 mapping 示例；删除 §3.5.3 召唤词清单中"生成用量报告 / 耗时报告 / token 消耗报告 / 工作流效率报告"四词；新增 base-role 自检规则（done 阶段六层回顾 State 层 grep `record_subagent_usage` 调用次数 ≥ 派发次数 - 容差）
- 产出：`harness-manager.md` diff
- 依赖：chg-04（usage-reporter 废止前提）

#### chg-07（dogfood 活证 + scaffold_v2 mirror 收口）：端到端 dogfood + mirror diff 归零

- 内容：本 req-41 自身落地 dogfood —— (a) 验证 `.workflow/flow/requirements/req-41-{slug}/` 下机器型工件齐全（requirement.md / changes/chg-01..chg-07/ / usage-log.yaml）；(b) 验证 `artifacts/main/requirements/req-41-{slug}/` 下只有 raw `requirement.md` 副本 + `交付总结.md`，无四类 brief；(c) 同步 scaffold_v2 mirror（`src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`）与活证 diff = 0；(d) 跑 `harness validate --human-docs req-41` 退出码 = 0；(e) 跑 `pytest tests/` 全量绿；(f) 契约 7 + 硬门禁六 + 批量列举子条款自检（grep 命中行核对）；done 阶段写交付总结 §效率与成本段从真实 usage-log 聚合
- 产出：dogfood 收口报告（写入 session-memory）+ scaffold_v2 mirror diff + 交付总结
- 依赖：chg-01..chg-06 全部完成（DAG 收口）

### 5.3 DAG 依赖图

```
chg-01（契约底座）
   ├─→ chg-02（CLI 路径迁移）
   ├─→ chg-03（validate 重写）
   ├─→ chg-04（角色去路径化 + brief 删除 + usage-reporter 废止）
   │       ├─→ chg-05（done 交付总结扩段）
   │       └─→ chg-06（harness-manager Step 4 硬门禁）
   └─（共骨架前置）
                    ↓
              chg-07（dogfood + scaffold_v2 + 收口）
```

并行度：chg-02 / chg-03 / chg-04 可并行（共骨架后）；chg-05 / chg-06 必须等 chg-04 完成；chg-07 等全部完成。

### 5.4 反向豁免：用户 escape hatch

若用户说"我要自拆"/"我自己拆"/"让我自己拆"/"我拆 chg"四个触发词之一，本 5.2/5.3 推荐拆分降级为"参考方案"，由用户重新指定拆分边界（base-role 硬门禁 + stage-role 流转点豁免子条款 default-pick HM-1 escape hatch）。

### 5.5 完成判据

本 req 完成 → 填 `completion.md` + 验证项目启动（`pytest tests/` 全绿 + `harness validate --human-docs req-41` exit 0 + dogfood 自证通过）。
