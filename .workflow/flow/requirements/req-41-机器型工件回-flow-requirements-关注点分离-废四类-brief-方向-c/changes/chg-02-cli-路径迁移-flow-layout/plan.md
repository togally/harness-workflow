# Change Plan — chg-02（CLI 路径迁移 flow layout）

## 1. Development Steps

### Step 1: 盘点既有 layout 常量与 handler 调用链

- 读取 `src/harness_workflow/workflow_helpers.py` 全文；
- 定位 `LEGACY_REQ_ID_CEILING = 38` / `FLAT_LAYOUT_FROM_REQ_ID = 39` / `_use_flat_layout` 定义位置；
- grep `_use_flat_layout` 所有调用点（预期 ≥ 5 处：`create_requirement` / `create_change` / `create_regression` / `archive_requirement` / path resolver）；
- 产出调用链表到 chg-02 session-memory.md，标注每处是否需加 flow 分支。

### Step 2: 新增 `FLOW_LAYOUT_FROM_REQ_ID` + `_use_flow_layout` helper

- 在 `workflow_helpers.py` `FLAT_LAYOUT_FROM_REQ_ID` 常量下方紧贴新增：
  ```python
  FLOW_LAYOUT_FROM_REQ_ID = 41  # req-41（机器型工件回 flow/requirements）
  ```
- 在 `_use_flat_layout` 函数下方紧贴新增 `_use_flow_layout` helper，与 flat helper 同风格：解析数字部分 ≥ `FLOW_LAYOUT_FROM_REQ_ID` 返回 True，非法 id / None / 空串返回 False；注释明确 `_use_flow_layout(x) → True 蕴含 _use_flat_layout(x) → True`（flow ⊂ flat）。

### Step 3: 改写 create_requirement handler

- 定位 `create_requirement` 函数体；
- 在既有 `_use_flat_layout` 分支之前新增 `_use_flow_layout` 分支：req-id ≥ 41 → `.workflow/flow/requirements/{req-id}-{slug}/requirement.md`；
- 保留既有 flat / legacy 分支不动；
- 确保 artifacts 侧 raw `requirement.md` 副本照常写入（供外部审阅）。

### Step 4: 改写 create_change handler

- 定位 `create_change` 函数体；
- 新增 flow 分支：req-id ≥ 41 → `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/{change.md, plan.md, session-memory.md}`；`regression/required-inputs.md` 同子目录下；
- 保留既有 flat / legacy 分支；
- artifacts 侧 `chg-NN-变更简报.md` 空壳**本 chg 不改**（归属 chg-03（validate_human_docs 重写）validate 精简 + chg-07（dogfood 活证 + scaffold_v2 mirror 收口）dogfood 清理）。

### Step 5: 改写 create_regression handler

- 定位 `create_regression`；
- 新增 flow 分支：req-id ≥ 41 → `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/{regression.md, analysis.md, decision.md, meta.yaml, session-memory.md}`；
- 保留 flat / legacy 分支。

### Step 6: 改写 archive_requirement handler

- 定位 `archive_requirement`；
- 新增 flow 分支：req-id ≥ 41 时用 `shutil.move` 整目录搬 `.workflow/flow/requirements/{req-id}-{slug}/` → `.workflow/flow/archive/{branch}/req-{req-id}-{slug}/`；
- artifacts/ 侧对人产物按现行归档逻辑维持不变；
- 保留 flat / legacy 分支（req-39（对人文档家族契约化）/ req-40（阶段合并与用户介入窄化）仍搬 `.workflow/state/sessions/req-NN/`）。

### Step 7: 扩展 path resolver

- 定位 `resolve_requirement_root` / `resolve_requirement_reference` / `_resolve_target` / `load_requirement_runtime`；
- 每处按 `_use_flow_layout(req_id)` 先判断；为 True 时优先解析 `.workflow/flow/requirements/{req-id}-{slug}/` 路径，找不到再 fallback 到 flat / legacy；
- 明确三分支互斥顺序：flow → flat → legacy。

### Step 8: 新增 pytest 用例

- 新建 `tests/test_use_flow_layout.py`（或并入既有 `tests/test_workflow_helpers.py`）：
  - `test_use_flow_layout_req_40_false`
  - `test_use_flow_layout_req_41_true`
  - `test_use_flow_layout_req_50_true`
  - `test_use_flow_layout_invalid_id_false`（覆盖空 / None / `abc` / `req-abc`）
- 新增 create_* pytest（tempdir fixture）：
  - `test_create_requirement_flow_layout_req_41`：断言 `.workflow/flow/requirements/req-41-{slug}/requirement.md` 存在；
  - `test_create_change_flow_layout_req_41`：断言 `.workflow/flow/requirements/req-41-{slug}/changes/chg-01-{slug}/{change.md,plan.md,session-memory.md}` 存在；
  - `test_create_regression_flow_layout_req_41`：断言 `.workflow/flow/requirements/req-41-{slug}/regressions/reg-01-{slug}/` 子文件齐全；
  - `test_archive_requirement_flow_layout_req_41`：tempdir 创建 req-41（机器型工件回 flow）+ 1 chg + 1 reg，跑 archive 后断言源目录不存在、`archive/{branch}/req-41-{slug}/` 存在、子文件齐全；
- 保留 req-39（对人文档家族契约化）/ req-40（阶段合并与用户介入窄化）既有 create_* / archive 用例断言不动。

### Step 9: 同步 scaffold_v2 mirror + 自检交接

- `workflow_helpers.py` 不在 mirror 中（source 本身是 pypi 包），**无需** mirror 同步；
- 跑 `pytest tests/ -v` 全量绿（本 chg 重点验证用例 + 回归护栏全 PASS）；
- grep `grep -c "FLOW_LAYOUT_FROM_REQ_ID" src/harness_workflow/workflow_helpers.py` ≥ 2（常量定义 + helper 引用）；
- 更新 chg-02 session-memory.md 记录完成步骤 + default-pick 清单。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -q "FLOW_LAYOUT_FROM_REQ_ID = 41" src/harness_workflow/workflow_helpers.py`
- `grep -q "def _use_flow_layout" src/harness_workflow/workflow_helpers.py`
- `pytest tests/ -k "test_use_flow_layout" -v` ≥ 4 PASS
- `pytest tests/ -k "test_create_requirement_flow_layout_req_41 or test_create_change_flow_layout_req_41 or test_create_regression_flow_layout_req_41 or test_archive_requirement_flow_layout_req_41" -v` 全 PASS
- `pytest tests/` 全量绿（回归护栏）

### 2.2 Manual smoke / integration verification

- tempdir init harness 仓库 → `harness requirement "smoke req 41"` 手动触发 → 检查 `.workflow/flow/requirements/req-41-smoke-req-41/requirement.md` 存在；
- `harness change "smoke chg" --requirement req-41` → 检查 `.workflow/flow/requirements/req-41-.../changes/chg-01-smoke-chg/{change.md, plan.md}` 存在；
- `harness archive req-41` → 检查源目录消失、`.workflow/flow/archive/main/req-41-smoke-req-41/` 子文件齐全；
- 对比 tempdir init → `harness requirement "legacy req 40"`（req-40（阶段合并与用户介入窄化））仍落 `.workflow/state/sessions/req-40/`（legacy fallback 不破坏）。

### 2.3 AC Mapping

- AC-03（`FLOW_LAYOUT_FROM_REQ_ID` + `_use_flow_layout`） → Step 2 + Step 8 第一组用例 + 2.1 grep + pytest 断言；
- AC-04（create_* 路径校验） → Step 3 + Step 4 + Step 5 + Step 8 第二组用例 + 2.1 pytest；
- AC-05（archive 路径校验） → Step 6 + Step 8 archive 用例 + 2.1 pytest；
- AC-06（回归不破坏） → Step 7 path resolver 三分支互斥 + 2.1 全量绿 + 2.2 req-40 手动验证。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（repository-layout 契约底座）必须先落地（代码按契约走，避免路径描述漂移）；
- **后置依赖**：chg-07（dogfood + scaffold_v2 mirror 收口）验证 req-41 自身物理路径；chg-03（validate_human_docs 重写删四类 brief）在本 chg 代码路径落位后扫描 req-41 新位；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3~7 可并行（不同 handler 相互独立，建议串行稳妥）→ Step 8 → Step 9；
- **可并行邻居**：chg-03（validate 重写）/ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）/ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）与本 chg 并行（共骨架后 4 路并行）。
