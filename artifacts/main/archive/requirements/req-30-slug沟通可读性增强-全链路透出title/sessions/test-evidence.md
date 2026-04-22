# Test Evidence — req-30（slug 沟通可读性增强：全链路透出 title）

> 本文档首次提到 req-30（slug 沟通可读性增强：全链路透出 title）和 chg-01（state schema — title 冗余字段）/ chg-02（CLI 渲染 — render_work_item_id helper）/ chg-03（角色契约 — id + title 硬门禁）/ chg-04（归档 meta — title 落盘）；后续沿用简写 id（契约 7 — AC-10 自证）。

## 1. 测试基线

- 执行时间：2026-04-21
- 执行人：Subagent-L1（testing 角色 / 测试工程师）
- Python：3.14.3，pytest 9.0.3
- 基线（executing 报告）：188 collected → 220 collected / 183 passed / 36 skipped / 1 failed（pre-existing：`test_smoke_req29::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`）
- 本次测试重跑：**220 collected / 183 passed / 36 skipped / 1 failed**，与 executing 报告完全一致（零回归）
- 唯一失败为 pre-existing（req-29 归档后目录缺失，与 req-30 无关）

## 2. AC 验证矩阵

| AC | 状态 | 证据 | 备注 |
|----|------|------|------|
| AC-01（汇报模板强制 title） | ✅ | `session-memory.md` 第 1 / 25 / 44 行均以 `req-30（slug 沟通可读性增强：全链路透出 title）` 形式首次引用；`action-log.md` 2026-04-21 首段标题带 title | 首次引用 100% 合规 |
| AC-02（旧模板已更新） | ✅ | `grep "契约 7" .workflow/context/roles/` 命中 9 个文件（stage-role + 7 stage + technical-director） | 全部角色契约覆盖 |
| AC-03（CLI 默认带 title） | ✅ | 临时仓库 smoke：`harness status` stdout = `current_requirement: req-01（测试标题）` + `active_requirements: req-01（测试标题）`；`harness suggest --list` 每行 `sug-XX（title）` | 端到端验证 |
| AC-04（title 缺失降级） | ✅ | 直接调用 `render_work_item_id("req-404", runtime=None, root=root)` → `"req-404 (no title)"`；空 id → `"(none)"`；不抛错 | 降级路径验证 |
| AC-05（runtime yaml 含 *_title） | ✅ | `DEFAULT_STATE_RUNTIME` 含 `current_requirement_title` / `locked_requirement_title` / `current_regression_title` 三字段；smoke 测试 v2 仓库生成的 runtime.yaml 三字段齐全；req-30 自身 state yaml `title: "slug沟通可读性增强：全链路透出title"` 非空 | schema + 活跃需求双验证 |
| AC-06（写入路径统一） | ✅ | `grep "_title"` 命中 26 处；4 个 `runtime["current_requirement"] = ...` 写入点（3686 / 3775 / 5108 / 5389）均紧随 `runtime["current_requirement_title"] = _resolve_title_for_id(...)` 同步写入 | executing 报告声称 11 处写入点已全覆盖 |
| AC-07（归档目录 meta） | 📌 延期覆盖 | chg-04（归档 meta — title 落盘）已明确延期（session-memory 第 161-171 行有决策说明）；现状归档目录名 + `需求摘要.md` 首行模板已部分满足；AC-07 不阻塞 req-30 主线 | 需 done 阶段决定是否登 sug |
| AC-08（experience index 带 title） | ✅ | `.workflow/state/experience/index.md` 第 64-74 行含"来源字段校验规则" + 正例 + 反例；`experience/roles/planning.md` 第 44 行来源段 `req-29（批量建议合集 2 条）— sug-01（ff --auto）+ sug-08（archive 判据）合集` 符合新格式 | 校验规则 + 示范回填双备 |
| AC-09（测试覆盖 2+1） | ✅ | chg-01（12）+ chg-02（12）+ chg-03（8）= **32 条新增单测**；均含 smoke 级 subprocess 验证（`test_workflow_status_prints_current_requirement_with_title`）；全量零回归（151→183） | 超额完成 2+1 要求 |
| AC-10（自证样本） | ✅ | `需求摘要.md` / 3 份 `实施说明.md` / 3 份 `变更简报.md` / `session-memory.md` 首次引用 req-30 / chg-XX 均带 title；`test_chg03_title_contract.py::TestReq30SelfCertification` 2 条自证断言全绿 | 契约 7 自证通过 |

**综合：9 条 ✅ + 1 条延期覆盖（AC-07，已计划内登记）。**

## 3. 新增测试统计

| 来源 | 文件 | 用例数 | 结果 |
|------|------|--------|------|
| chg-01（state schema — title 冗余字段） | `tests/test_runtime_title_fields.py` | 12 | 12/12 passed |
| chg-02（CLI 渲染 — render_work_item_id helper） | `tests/test_render_work_item_id.py` | 12 | 12/12 passed |
| chg-03（角色契约 — id + title 硬门禁） | `tests/test_chg03_title_contract.py` | 8 | 8/8 passed |
| **合计** | **3 文件** | **32** | **32/32 passed** |

## 4. Smoke / 端到端验证

- **Smoke 1（净仓安装 + 新建需求 + status）**：`/tmp/harness-req30-test-v2`：
  - `harness install` → 成功生成 `.workflow/` 框架
  - `harness requirement "测试标题"` → 生成 `req-01-测试标题.yaml`（`title: "测试标题"` 非空）
  - `harness status` stdout：
    ```
    current_requirement: req-01（测试标题）
    active_requirements: req-01（测试标题）
    ```
  - 证据：AC-03 端到端通过；新建路径 AC-06 同步写 title 生效。
- **Smoke 2（runtime.yaml 字段齐全）**：Smoke 1 仓库生成的 runtime.yaml 含 `current_requirement_title: "测试标题"` / `locked_requirement_title: ""` / `current_regression_title: ""`。证据：AC-05 schema 活性验证。
- **Smoke 3（render_work_item_id 降级）**：直接调用 helper 的 4 分支（runtime cache / state fallback / missing / empty）均符合预期；证据：AC-04。
- **Smoke 4（`harness suggest --list` 真实仓库）**：主仓执行输出每行 `sug-XX（title）`，legacy sug 的 title 通过 body 首行截断 fallback 显示，无 `(no title)` 大面积劣化；证据：AC-03 suggest 分支。

## 5. 文本 lint 校验

- `grep "契约 7" .workflow/context/roles/`：9 个文件命中（AC-02）
- `grep "req-30（slug" .workflow/state/sessions/req-30/session-memory.md`：命中（AC-01）
- `grep "^title:" .workflow/state/requirements/req-*.yaml`：活跃 req-30 非空（AC-05）
- `grep "req-29（批量建议合集" .workflow/context/experience/roles/planning.md`：命中（AC-08）

## 6. 已知失败

### pre-existing（不计入）

- `tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`：req-29（批量建议合集 2 条）已归档，期望的 `artifacts/main/requirements/req-29-*/` 路径不存在导致断言失败。根因与 req-30 无关，executing 报告已登记，本次测试不重新引入。

### 本次引入的失败

- **无**。

## 7. 问题与建议

### 小观察（不阻塞）

- **AC-04 降级边界**：手动用 `yaml.safe_dump` 写回 `title: ''` 后再加载，yaml 读回得到字符串 `"''"`（带引号），触发 `render_work_item_id` 显示 `req-01（''）` 而非降级。此场景不属于 CLI 正常路径（CLI 自身写回使用 `"..."` 双引号格式，读回为空串正确降级），不视为缺陷。若未来出现 legacy yaml 混入非标准空串，可加 `.strip("'\"")` 兜底。登记为后续可选增强（不阻塞 acceptance）。

### 评估结论

- **可推进 acceptance**：核心 AC-01~AC-06 / AC-08~AC-10 全部 ✅ 通过；AC-07 属 chg-04（归档 meta — title 落盘）延期覆盖，已按需求 §8 / planning 决策 / executing 决策三处一致登记为"不阻塞主线"；32 条新增单测全绿，零回归。
- **无需 regression**：未发现本次引入的失败；pre-existing 失败与 req-30 无关。
- **AC-07 处理建议**：done 阶段六层回顾时评估是否登 sug（"归档 meta _meta.yaml 落盘"）或独立 bugfix；建议登 sug，维持 req-30 干净完成。

## 8. 上下文消耗评估

- 文件读取：约 20 次（runtime.yaml / WORKFLOW.md / index.md / role-loading-protocol.md / base-role.md / stage-role.md / testing.md / testing experience / evaluation/testing.md / requirement.md / session-memory.md / 4 × change.md / 部分 plan.md / 部分代码片段）
- 工具调用：Read × 20+ / Grep × 10+ / Bash × 10+（含 pytest 4 次 + smoke shell 3 次）
- 预估：消耗约 45-50%，**无需立即维护**（未到 70% 阈值）

## 9. 汇报摘要（给主 agent）

- AC 结果：9 ✅ + 1 延期（AC-07 / chg-04 optional）
- pytest：220 collected / 183 passed / 36 skipped / 1 pre-existing failed（零回归）
- 新增测试：32 条全绿（chg-01 × 12 + chg-02 × 12 + chg-03 × 8）
- 本次引入失败：无
- 可直接推进 acceptance，无需 regression
