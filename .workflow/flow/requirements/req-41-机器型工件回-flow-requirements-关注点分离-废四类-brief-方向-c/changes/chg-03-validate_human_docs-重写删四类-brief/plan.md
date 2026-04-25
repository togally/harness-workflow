# Change Plan — chg-03（validate_human_docs 重写删四类 brief）

## 1. Development Steps

### Step 1: 读取 validate_human_docs.py 全文 + 列现有常量结构

- 读取 `src/harness_workflow/validate_human_docs.py` 全文；
- 定位 `HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` / `BUGFIX_LEVEL_DOCS` 常量定义（若存在结构变体如 dict / list / set，记录形式）；
- 定位 `_collect_req_items` / 主扫描函数 / CLI 入口；
- 产出常量结构 + 调用链表到 chg-03 session-memory.md。

### Step 2: 新增常量 BRIEF_DEPRECATED_FROM_REQ_ID

- 方案 A（推荐，default-pick）：直接 import `FLOW_LAYOUT_FROM_REQ_ID` from `workflow_helpers`，在 `validate_human_docs.py` 头部额外定义 `BRIEF_DEPRECATED_FROM_REQ_ID = 41`（与 FLOW_LAYOUT 同值但语义独立，为未来解耦留口）；
- 方案 B（fallback）：在 `workflow_helpers.py` 统一定义后 import（若 chg-02（CLI 路径迁移）已同文件新增 FLOW_LAYOUT，本 chg 就 import 不重复）；
- 注释明确："req-id ≥ BRIEF_DEPRECATED_FROM_REQ_ID 时四类 brief 不再列入白名单扫描"。

### Step 3: 重写白名单常量

- `HUMAN_DOC_CONTRACT`（若是中心化字典结构）：
  - 删除 `需求摘要.md` 项 / `chg-NN-变更简报.md` 项 / `chg-NN-实施说明.md` 项 / `reg-NN-回归简报.md` 项 / `耗时与用量报告.md` 项；
  - 保留 raw `requirement.md`（artifacts 副本，req 级必查）/ `交付总结.md`（req 级必查）；
- `REQ_LEVEL_DOCS`：保留 `requirement.md` + `交付总结.md`（+ 可选 `决策汇总.md`）；
- `CHANGE_LEVEL_DOCS`：**删空**或标 deprecated（chg 级不再有对人文档强制项）；
- `BUGFIX_LEVEL_DOCS`：删 `修复说明.md` 若与四类 brief 等同；保留 bugfix 对人产物（若有）；按 req-41（机器型工件回 flow）requirement.md §3.3 Scope-废 brief 明文声明执行。

### Step 4: 扫描入口加三分支

- 定位主扫描函数入口（如 `validate_requirement_human_docs(req_id, ...)`）；
- 按 req-id 走三分支：
  - `req_id_num >= BRIEF_DEPRECATED_FROM_REQ_ID` → 新精简扫描：只查 raw `requirement.md` + `交付总结.md` 落盘 / 字段 / 契约 7 自检；
  - `req_id_num in [FLAT_LAYOUT_FROM_REQ_ID, BRIEF_DEPRECATED_FROM_REQ_ID - 1]`（即 39-40）→ 维持现行扫描（四类 brief 全查）；
  - `req_id_num <= LEGACY_REQ_ID_CEILING`（即 ≤ 38）→ 维持 legacy 废扫描（多层路径豁免）；
- 每分支对应独立函数（或 branch 内部用 match/case），避免单函数 if/elif 树过长。

### Step 5: 扩展 pytest

- 新增 `tests/test_validate_human_docs.py`（或扩既有文件）：
  - `test_validate_human_docs_brief_deprecated_req_41`：pytest tempdir 建 `artifacts/main/requirements/req-41-smoke/requirement.md` + `交付总结.md`；调 validate 入口；断言 exit 0、items 数 = 2、每项 status = ok；
  - `test_validate_human_docs_req_41_missing_delivery_summary`：mock req-41 目录只放 `requirement.md`（缺 `交付总结.md`），断言 exit != 0 + items[1].status = missing；
  - `test_validate_human_docs_req_41_ignores_brief_stubs`：mock req-41 目录额外放 `chg-01-变更简报.md` 空壳（CLI 自动生成的残留），断言 validate 静默忽略（不报期望项也不报额外错）；
  - `test_validate_human_docs_req_39_unchanged`：mock req-39（对人文档家族契约化）目录按现行规则扫描（四类 brief 全查），断言行为不变；
  - `test_validate_human_docs_req_38_legacy`：mock req-38（api-document-upload 工具闭环）目录，断言走 legacy 废扫描路径。

### Step 6: 自检 + 交接

- `grep -q "BRIEF_DEPRECATED_FROM_REQ_ID = 41" src/harness_workflow/validate_human_docs.py`；
- `pytest tests/ -k "test_validate_human_docs" -v` 全 PASS；
- `pytest tests/` 全量绿（回归护栏）；
- 更新 chg-03 session-memory.md 记录完成步骤 + default-pick 清单（含 D-A "方案 A 本地常量 vs 方案 B workflow_helpers 中心化" 选 A 的理由）；
- 产出文档 ≤ 1 屏内读完。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `grep -q "BRIEF_DEPRECATED_FROM_REQ_ID = 41" src/harness_workflow/validate_human_docs.py`
- 常量结构 grep：`grep -c '"需求摘要"\|"变更简报"\|"实施说明"\|"回归简报"\|"耗时与用量报告"' src/harness_workflow/validate_human_docs.py` 接近 0（若保留在注释 / deprecation marker 中可豁免，但不得出现在活跃白名单 dict / list 中）
- `pytest tests/ -k "test_validate_human_docs_brief_deprecated_req_41" -v` PASS
- `pytest tests/ -k "test_validate_human_docs_req_41_missing_delivery_summary" -v` PASS
- `pytest tests/ -k "test_validate_human_docs_req_41_ignores_brief_stubs" -v` PASS
- `pytest tests/ -k "test_validate_human_docs_req_39_unchanged" -v` PASS
- `pytest tests/` 全量绿

### 2.2 Manual smoke / integration verification

- tempdir 建 `artifacts/main/requirements/req-41-smoke/{requirement.md, 交付总结.md}` → 跑 `harness validate --human-docs req-41` → exit 0，输出只列 2 条 ok；
- tempdir 额外放 `chg-01-变更简报.md`（空壳）→ 再跑，输出仍只列 raw + 交付总结 2 条 ok，不报空壳缺 / 空壳多；
- tempdir 建 `artifacts/main/requirements/req-39-smoke/` 按 req-39 现行要求放全 → 跑 validate req-39 → 行为与 git HEAD 基线一致（diff 输出对比）；
- tempdir 故意缺 `交付总结.md` → `harness validate --human-docs req-41` → exit != 0 + 明确报 `交付总结.md` missing。

### 2.3 AC Mapping

- AC-08（validate 重写） → Step 2 + Step 3 + Step 4 + 2.1 grep + pytest；
- AC-09（pytest brief deprecated） → Step 5 用例 + 2.1 pytest；
- AC-06（回归不破坏） → Step 4 三分支 + Step 5 req-39/38 pytest + 2.1 全量绿。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（repository-layout 契约底座）必须先落地（白名单是契约的代码化，契约先行）；
- **可并行邻居**：chg-02（CLI 路径迁移 flow layout）/ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）/ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）共骨架后并行；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 强制串行（常量先定、白名单后改、扫描入口跟随、最后测试收口）；
- **后置依赖**：chg-07（dogfood + scaffold_v2 mirror 收口）会跑 `harness validate --human-docs req-41` exit 0 作为 dogfood 活证的一部分。
