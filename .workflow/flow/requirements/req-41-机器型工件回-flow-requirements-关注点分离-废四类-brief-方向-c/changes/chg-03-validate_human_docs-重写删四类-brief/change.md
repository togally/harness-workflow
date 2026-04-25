# Change

## 1. Title

validate_human_docs 重写删四类 brief（BRIEF_DEPRECATED_FROM_REQ_ID + 扫描精简）

## 2. Goal

- 在 `src/harness_workflow/validate_human_docs.py` 新增常量 `BRIEF_DEPRECATED_FROM_REQ_ID = 41`；重写 `HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` / `BUGFIX_LEVEL_DOCS` 常量结构删除四类 brief 项；req-id ≥ 41 走新精简扫描（只校验 raw `requirement.md` artifacts 副本 + `交付总结.md`），req-id ∈ [39, 40] 维持现行扫描，req-id ≤ 38 维持 legacy 废扫描。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- `src/harness_workflow/validate_human_docs.py`：
  - 新增常量 `BRIEF_DEPRECATED_FROM_REQ_ID = 41`（紧贴 `LEGACY_REQ_ID_CEILING` / `FLAT_LAYOUT_FROM_REQ_ID` 同文件常量区，若缺则从 `workflow_helpers` import）；
  - 重写 `HUMAN_DOC_CONTRACT` / `REQ_LEVEL_DOCS` / `CHANGE_LEVEL_DOCS` / `BUGFIX_LEVEL_DOCS`：删除 `需求摘要.md` / `chg-NN-变更简报.md` / `chg-NN-实施说明.md` / `reg-NN-回归简报.md` 四项；保留 raw `requirement.md`（artifacts 副本）/ `交付总结.md`；
  - `_collect_req_items` / 核心扫描函数按 req-id 加三分支：≥ 41 走精简扫描（只查 raw + 交付总结）/ 39-40 走现行扫描 / ≤ 38 走 legacy；
  - 同步删除 `耗时与用量报告.md` 扫描项（配合 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）的 usage-reporter 废止）；
- pytest 新增：
  - `test_validate_human_docs_brief_deprecated_req_41`：mock req-41（机器型工件回 flow）目录只放 `requirement.md` + `交付总结.md`，断言 validate 返回 exit 0、items 数 = 2、status 全 ok；
  - `test_validate_human_docs_req_39_unchanged`：mock req-39（对人文档家族契约化）目录保留现行扫描行为不变；
  - `test_validate_human_docs_req_38_legacy`：mock req-38（api-document-upload 工具闭环）目录维持 legacy 废扫描；
- 涉及文件：
  - `src/harness_workflow/validate_human_docs.py`
  - `tests/test_validate_human_docs.py`（既有文件扩展）

### Excluded

- **不动** `.workflow/flow/repository-layout.md`（白名单重写归属 chg-01（repository-layout 契约底座））；
- **不动** 角色文件的 brief 模板（归属 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止））；
- **不动** `harness-manager.md` Step 4（归属 chg-06（harness-manager Step 4 派发硬门禁））；
- **不动** `done.md` 交付总结模板（归属 chg-05（done 交付总结扩效率与成本段））；
- **不删除、不迁移**历史存量 brief 文件（`artifacts/main/requirements/req-02 ~ req-40` 下现存 brief 原地保留）；
- **不改**测试结论 / 验收摘要相关逻辑（req-31（角色功能优化整合与交互精简）/ chg-04（S-D 对人文档缩减）已废止，本 chg 与之并列生效）。

## 5. Acceptance

- Covers requirement.md **AC-08**（validate 重写）：
  - `grep -q "BRIEF_DEPRECATED_FROM_REQ_ID = 41" src/harness_workflow/validate_human_docs.py`；
  - `grep -cE "需求摘要|变更简报|实施说明|回归简报" src/harness_workflow/validate_human_docs.py` 命中数 = 0（常量 / whitelist 中已删；若出现仅为注释说明 historical deprecation 可豁免，但硬门禁看实际扫描项常量值）；
  - `harness validate --human-docs req-41`（或 pytest mock）退出码 = 0 时只校验 raw + 交付总结，不报四类 brief missing；
  - `harness validate --human-docs req-39` 仍按 req-39 规则扫描（pytest 回归护栏）。
- Covers requirement.md **AC-09**（pytest brief deprecated）：
  - `pytest tests/ -k "test_validate_human_docs_brief_deprecated_req_41" -v` PASS；mock 目录含 `requirement.md` + `交付总结.md`，断言 items 数 = 2、status 全 ok、exit 0。
- Covers requirement.md **AC-06**（回归不破坏）：
  - `pytest tests/` 全量绿；
  - `test_validate_human_docs_req_39_unchanged` / `test_validate_human_docs_req_38_legacy` 维持现行行为。

## 6. Risks

- **风险 1：常量结构改写影响 req-39/40 既有用例行为**。缓解：扫描入口按 req-id 分三分支，39-40 走完全独立的 legacy 路径常量表；executing 开局先跑既有 req-39 pytest 用例作 baseline，改写后再跑确认不变。
- **风险 2：artifacts/ 下四类 brief 空壳（CLI 自动生成）被 req-41（机器型工件回 flow）validate 误报缺失**。缓解：新精简扫描的"期望"集合只含 raw + 交付总结，空壳 brief 既不在期望集也不在错误集（静默忽略）；chg-07（dogfood 活证 + scaffold_v2 mirror 收口）dogfood 阶段由 executing 清理残留空壳。
- **风险 3：`耗时与用量报告.md` 与 chg-04 usage-reporter 废止时序耦合**。缓解：本 chg 删扫描项不依赖 chg-04 文件删除；chg-04 先后顺序灵活（都依赖 chg-01），都落地后 usage-reporter 相关残留彻底清除。
- **风险 4：import `BRIEF_DEPRECATED_FROM_REQ_ID` / `FLOW_LAYOUT_FROM_REQ_ID` 循环依赖**。缓解：若两常量都在 `workflow_helpers.py` 定义，`validate_human_docs.py` 单向 import；避免反向。executing 开局先定 import 方向。
