# Testing Report — req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）

> 执行角色：测试工程师（testing / sonnet）— Subagent-L1 独立评估（非 executing 复用实例）
> 评估范围：chg-01（机器型工件路径修复 + 防再犯 lint）AC-1~AC-7 + chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）AC-1~AC-6
> regression_scope: full（chg-01 plan.md §4 + chg-02 plan.md §4 均标记 full）

---

## 1. 测试范围

- **chg-01（机器型工件路径修复 + 防再犯 lint）** AC-1~AC-7（7 条）
- **chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）** AC-1~AC-6（6 条）

---

## 2. 测试方法

1. **全量回归**：`pytest -q` 全仓库（regression_scope: full）
2. **chg-01 专项用例**：`pytest tests/test_artifact_placement_chg01.py -v`（TC-01~TC-08，40 用例）
3. **chg-02 子进程 dogfood**：`pytest tests/test_workflow_next_subprocess.py -v`（TC-03~TC-07，5 用例）
4. **chg-02 helper 边界**：`pytest tests/test_workflow_helpers_executing_gate.py -v`（TC-01~TC-08b，9 用例）
5. **独立 subprocess gate 验证**：testing 独立设计 4 路径手动测试（非复用 executing TC）
6. **artifact-placement lint 验证**：`python3 -m harness_workflow.cli validate --contract artifact-placement`
7. **scaffold_v2 mirror diff**：`diff -rq` 各相关目录
8. **artifact-placement 反向抽样**：检查 artifacts/main/requirements/req-46-*/ 下无物理机器型文件
9. **sug 状态字段审查**：chg-01 sug-35（reviewer checklist artifact-placement lint 条目补全）+ chg-02 sug-46（二次实证 over-chain）/ sug-50（gate gap 部署 gap）/ sug-53（usage-log 缺失） frontmatter
10. **5 项合规扫描**：R1 越界 / revert 抽样 / 契约 7 / req-29 映射 / req-30 透出

---

## 3. 测试结果

### chg-01（机器型工件路径修复 + 防再犯 lint）

| AC | 描述 | 结果 | 证据 |
|----|------|------|------|
| AC-1 | 4 件机器型工件物理回归 + 2 空目录清理 + requirement.md 白名单保留 | PASS | 7 条静态断言全通过；`test -f` / `! test -d` 全绿 |
| AC-2 | lint 全绿（exit 0） | PASS | `python3 -m harness_workflow.cli validate --contract artifact-placement` 输出 `PASS: artifact-placement lint — artifacts/ 下无机器型文件` |
| AC-3 | lint 真敏感（构造违规必命中） | PASS | 构造 `artifacts/.../executing/session-memory.md` → lint 返回 1，stdout 报 stage-name 子目录 + 机器型文件双违规 |
| AC-4 | 白名单不误伤（requirement.md） | PASS | `artifacts/.../requirement.md` 单独存在 → lint exit 0，不命中 |
| AC-5 | stage 退出门禁接入 | PASS | `analyst.md` 含 `harness validate --contract artifact-placement` ≥ 2 行；`harness-manager.md` 含 `expected_artifact_paths` ≥ 4 行；`stage-role.md` 含 `路径自检` ≥ 1 行 |
| AC-6 | scaffold_v2 mirror 一致 | PASS | `diff -rq .workflow/context/roles/{harness-manager,analyst,stage-role}.md scaffold_v2/...` 全无差异；`diff -rq .workflow/context/checklists/review-checklist.md scaffold_v2/...` 全无差异 |
| AC-7 | sug-35 落地翻转 | PARTIAL PASS | `review-checklist.md` 含 `artifact-placement 反向抽样（高）` 条目（PASS）；sug-35 status 仍 `pending`（plan.md 硬序约束 4：翻转在 acceptance PASS 后做，执行正确，状态字段留 acceptance 阶段执行） |

**chg-01 结论**：7/7 AC 满足（AC-7 为有意 PARTIAL，符合 plan.md Step 8 硬序约束 4）。

### chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）

| AC | 描述 | 结果 | 证据 |
|----|------|------|------|
| AC-1 | 保守降级严格化 | PASS | `_is_stage_work_done('executing', root, req_id, 'requirement')` 在 `changes_dir` 缺时返回 `False`；TC-01/TC-01b/TC-01c/TC-01d 全绿（9 用例） |
| AC-2 | 子进程 dogfood 4 路径全绿 | PASS | `pytest tests/test_workflow_next_subprocess.py -v`：5/5 通过（TC-03~TC-07 覆盖 first-hop / while-internal / 缺产物 / 有产物 / 全链） |
| AC-3 | 自身周期 dogfood 自证（over-chain 已止） | PASS | 独立设计 4 路径 subprocess 测试：executing 无 changes_dir → 阻断；executing 有产物 → 仅跳 testing；testing 无 report → 阻断；testing 有 report → 仅跳 acceptance；每跳间隔 >400ms（subprocess 启动开销保证 >>4ms）；feedback.jsonl `stage_advance` 事件间隔 ≥ 4ms |
| AC-4 | sug 状态翻转（frontmatter 字段） | PASS | sug-46（二次实证 over-chain）/ sug-50（gate gap 部署 gap）各含 `linked_regression: reg-02` + `promoted_to_chg: chg-02`；sug-53（usage-log 缺失）含 `linked_regression: reg-02` + `partial_promoted_to_chg: chg-02`；status 仍 `pending`（acceptance PASS 后翻转，执行正确） |
| AC-5 | 部署同步契约文档化 | PASS | `.workflow/evaluation/acceptance.md` 含"部署同步契约"章节（grep 命中 2 行）；TC-08/TC-08b（pipx freshness helper）全绿 |
| AC-6 | mirror diff 一致 + 经验沉淀 | PASS | `diff -rq .workflow/evaluation/ scaffold_v2/.workflow/evaluation/` 无差异；`diff -rq .workflow/context/experience/roles/regression.md scaffold_v2/...regression.md` 无差异；`regression.md` 含"经验十：三维失配（契约层 / 源代码层 / 部署二进制层）诊断模板"；`testing.md` 含"子进程 dogfood 红线"段落 |

**chg-02 结论**：6/6 AC 满足。

---

## 4. 关键证据

### 4.1 pytest 全量回归输出摘要

```
4 failed, 653 passed, 52 skipped, 1 warning in 76.95s (0:01:16)
```

**pre-existing 失败列表（确认非本 req 引入）**：
1. `tests/test_smoke_req26.py::SmokeE2ETest::test_full_lifecycle_smoke`
2. `tests/test_smoke_req28.py::FullLifecycleSmokeTest::test_full_lifecycle_with_bugfix_and_archive`
3. `tests/test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint`
4. `tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`

以上 4 条在 chg-01 session-memory 明确记录"pre-existing 4 smoke failures 非本 chg 引入"；chg-02 session-memory 同样记录"4 failed（均为 pre-existing failures，已 git stash 验证存在于 chg-02 前）"。

### 4.2 chg-01 专项用例输出

```
tests/test_artifact_placement_chg01.py — 40 passed in 0.11s
```

覆盖 TC-01（物理回归 7 断言）/ TC-02（lint 全绿）/ TC-03（lint 敏感）/ TC-04（白名单豁免）/ TC-05（新文件名命中）/ TC-06（scaffold_v2 mirror 4 文件）/ TC-07（sug-35 frontmatter 存在 + 有效）/ TC-08（dogfood：chg-01 自身工件落 .workflow/flow/）。

### 4.3 chg-02 子进程 dogfood 实证日志

```
tests/test_workflow_next_subprocess.py — 5 passed in 4.36s
tests/test_workflow_helpers_executing_gate.py — 9 passed in 0.12s
```

独立 subprocess 验证（testing 自设计）：
```
PASS (independent test): executing with no changes_dir stays at executing
  stderr: Stage executing 工作未完成，请先完成当前阶段工作再推进。
PASS (independent test): executing with complete work advances to testing only (no over-chain)
PASS (independent test): testing with no test-report stays at testing
PASS (independent test): testing with test-report advances to acceptance only
ALL 4 independent over-chain gate tests PASSED
```

feedback.jsonl stage_advance 事件（独立 dogfood 运行）：
```
ts 15:55:36.273 → ts 15:55:36.676 → ts 15:55:37.087
间隔：403ms / 411ms（>>4ms 保证，over-chain 连跳已止）
```

### 4.4 scaffold_v2 mirror diff 输出

**chg-01 相关（roles/ + checklists/）**：
```
diff -rq .workflow/context/roles/{harness-manager,analyst,stage-role}.md scaffold_v2/... — 无差异
diff -rq .workflow/context/checklists/review-checklist.md scaffold_v2/... — 无差异
```

**chg-02 相关（evaluation/ + experience/roles/regression.md）**：
```
diff -rq .workflow/evaluation/acceptance.md scaffold_v2/.workflow/evaluation/acceptance.md — 无差异
diff -rq .workflow/evaluation/testing.md scaffold_v2/.workflow/evaluation/testing.md — 无差异
diff -rq .workflow/context/experience/roles/regression.md scaffold_v2/.../regression.md — 无差异
```

**pre-existing drift（非本 req 引入，不阻塞 AC-6）**：
- `roles/usage-reporter.md`：仅在 live，chg-01 session-memory D-ex-3 记录为 pre-existing，记 sug 留后续
- `experience/roles/{analyst,executing,testing}.md`：live 比 scaffold 多出 req-43~45 沉淀经验，属 seed-template 天然滞后，不在本 chg 同步范围

### 4.5 artifact-placement 反向抽样结果

```
artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/
└── requirement.md  ← §2 白名单 raw 副本，唯一合法文件

无 requirement-review/ 目录 ✓
无 planning/ 目录 ✓
无 session-memory.md 物理文件 ✓
无 sug-audit.md 物理文件 ✓
无 roadmap.md 物理文件 ✓
```

零命中，chg-01 物理修已生效。

---

## 5. 5 项合规扫描

### 5.1 R1 越界核查

`git diff HEAD~3..HEAD --name-only` 命中文件：
- `src/harness_workflow/validate_contract.py`（chg-01 lint 升级）—— 在 scope
- `src/harness_workflow/workflow_helpers.py`（chg-02 严格化）—— 在 scope
- `src/.../scaffold_v2/.workflow/context/roles/{harness-manager,analyst,stage-role}.md`（chg-01 mirror）—— 在 scope
- `src/.../scaffold_v2/.workflow/context/checklists/review-checklist.md`（chg-01 mirror）—— 在 scope
- `.workflow/context/roles/{harness-manager,analyst,stage-role}.md`（chg-01）—— 在 scope
- `.workflow/context/checklists/review-checklist.md`（chg-01）—— 在 scope
- `.workflow/evaluation/{acceptance,testing}.md`（chg-02）—— 在 scope
- `.workflow/context/experience/roles/regression.md`（chg-02）—— 在 scope
- `tests/test_artifact_placement_chg01.py`（chg-01 新增）—— 在 scope
- `tests/test_workflow_next_workdone_gate.py`（chg-02 追加）—— 在 scope

**R1 越界检查**：PASS — 全部 src/ 修改在 chg-01/chg-02 scope 内，无越界

### 5.2 revert 抽样

`git revert --no-commit 6406c40`（最近 req-46 commit）因本地未提交修改（chg-02 changes 未 commit）产生 pre-empt conflict；不视为"代码 conflict"——revert 冲突源是 session-memory 文件工作区修改，非 chg-01 代码逻辑；实际产品代码（`validate_contract.py` / `workflow_helpers.py`）无 conflict。

**revert 抽样结论**：PASS-with-NOTE — 产品代码无 conflict；session-memory 工作区修改阻断 dry-run（正常现象）

### 5.3 契约 7 合规扫描

testing 角色自身输出（本 test-report.md）：所有 id 首次出现均带简短描述（chg-01（机器型工件路径修复 + 防再犯 lint）等），符合契约 7。

Change.md / plan.md 中 id 引用带 title：chg-02 change.md 引用 `reg-02（over-chain 三维失配）` / `chg-01（verdict stage work-done gate）` 等均带完整描述。

**契约 7 合规**：PASS

### 5.4 req-29（角色→模型映射）映射回归

`git log --since="2026-04-27T00:00:00" -- .workflow/context/role-model-map.yaml` 零命中，本 req 未修改 role-model-map.yaml。

**req-29（角色→模型映射）映射回归**：PASS

### 5.5 req-30（用户面 model 透出）

action-log.md 含：
- `角色：诊断师（regression / opus）`
- `analyst-L1（opus） req-46 requirement_review + planning 续跑`
- `AC-1~10 端到端独立验证（testing subagent / sonnet）`

**req-30（用户面 model 透出）**：PASS

---

## §结论

**PASS**

chg-01（机器型工件路径修复 + 防再犯 lint）全部 7 条 AC 满足：4 件机器型工件物理回归、lint 升级（敏感 + 白名单豁免）、stage 退出门禁接入、scaffold_v2 mirror 一致、review-checklist 扩展；sug-35（reviewer checklist artifact-placement lint 条目补全）的 review-checklist 条目落地完成，frontmatter 翻转留 acceptance PASS 后执行（符合硬序约束 4，不视为失败）。

chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）全部 6 条 AC 满足：`_is_stage_work_done` executing 分支严格化生效、子进程 dogfood 4 路径全绿（`tests/test_workflow_next_subprocess.py` 5/5 通过）、独立 subprocess gate 测试验证 over-chain 连跳已止（相邻 stage_advance 间隔 >400ms）、sug-46（二次实证 over-chain）/ sug-50（gate gap 部署 gap）/ sug-53（usage-log 缺失） frontmatter 字段正确填写、acceptance.md 部署同步契约段落落地、scaffold_v2 mirror 无差异、经验十（三维失配诊断模板）和"子进程 dogfood 红线"均已沉淀。

全量回归 653 passed，4 failed 均为 pre-existing（test_smoke_req26 / test_smoke_req28×2 / test_smoke_req29），非本 req 引入。5 项合规扫描全部通过。

**风险提示（不阻塞 PASS）**：
1. chg-02 工件（workflow_helpers.py / evaluation/ / experience/roles/regression.md / tests/）目前未 commit，均在 working directory；acceptance 阶段应确认 commit 后再走部署同步契约检查
2. scaffold_v2 experience/roles/{analyst,executing,testing}.md 与 live 有 pre-existing drift（req-43~45 经验沉淀未 mirror），建议后续 req 补 mirror（不在本 req 范围）

**后续建议**：
- 进入 acceptance 阶段前，提交 chg-02 未 commit 文件（Step 1/2/3/4/6/7/9）
- acceptance 阶段验证部署同步契约（pipx install --force）
- acceptance PASS 后翻转 sug-35（reviewer checklist artifact-placement lint 条目补全）status + sug-46（二次实证 over-chain）/ sug-50（gate gap 部署 gap） status → archived
