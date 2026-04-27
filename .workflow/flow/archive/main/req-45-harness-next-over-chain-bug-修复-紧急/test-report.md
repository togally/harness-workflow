# Test Report — req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）

> 测试角色：测试工程师（testing / sonnet）
> 测试日期：2026-04-25（二次干净验证，Subagent-L1）
> 测试阶段：testing
> 关联：req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
> 验证 commit：b64bcd7（fix: gate 插桩位置修对 + dogfood 验证）

---

## §测试矩阵

### 单元测试（9 用例）

| 用例 | 名称 | 期望 | 实际 | 状态 |
|------|------|------|------|------|
| TC-01 | executing→testing，缺 test-report.md，while gate 在 testing 处停下 | stage=testing | stage=testing | ✅ PASS |
| TC-02 | testing，缺 test-report.md，第一格 gate 阻断（BUG-01 修复） | stage=testing（不跳 acceptance） | stage=testing | ✅ PASS |
| TC-03 | acceptance，checklist.md 缺 §结论，第一格 gate 阻断（停在 acceptance） | stage=acceptance | stage=acceptance | ✅ PASS |
| TC-03b | `_is_stage_work_done('acceptance')`缺§结论→False，有§结论→True | False / True | False / True | ✅ PASS |
| TC-04 | testing 有产物+acceptance 有结论，连跳 testing→acceptance→done | stage=done | stage=done | ✅ PASS |
| TC-05 | requirement_review same_role 跳 planning，gate 不阻断（保 bugfix-5 契约） | stage=planning | stage=planning | ✅ PASS |
| TC-06 | bugfix 模式 testing 缺 test-report，第一格 gate 阻断（BUG-01 修复） | stage=testing | stage=testing | ✅ PASS |
| TC-07 | lint stage-work-completion，缺 test-report.md → rc=1 + FAIL + 列缺项 | rc=1+FAIL | rc=1+FAIL | ✅ PASS |
| TC-08 | done/regression/未知/空 stage → True（保守降级） | True | True | ✅ PASS |

**运行结果：9/9 PASS，执行时间 0.90s（python3 -m pytest tests/test_workflow_next_workdone_gate.py -v）**

---

### 独立反例补充（testing 自补，3 条）

| 反例 | 设计意图 | 实测结论 |
|------|---------|---------|
| 反例-A | test-report.md 含 "结论" 在正文（非 `## 结论` 标题）→ 应返回 False | `_is_stage_work_done=False`✅（`_has_conclusion_heading` 用 regex `##\s*§?结论` 标题级匹配，正文"结论"不命中） |
| 反例-B | acceptance/checklist.md 含 "结论" 在 HTML 注释 `<!-- 结论 -->` → 应返回 False | `_is_stage_work_done=False`✅（HTML 注释仍匹配不到 `## §?结论` 标题，正确保护） |
| 反例-C | executing stage，chg/session-memory.md 含 FAIL 不含 ✅ → 应返回 False | `_is_stage_work_done=False`✅（代码检查 `✅ not in content`，FAIL 场景正确阻断） |

---

### dogfood 实测（gate 阻塞 over-chain 验证）

**场景**：tmpdir mock 工作区，stage=testing，req flow dir 存在，**无 test-report.md**

**命令**：`workflow_next(root)`（tmpdir，不动当前仓库 git 状态）

**实际 stdout（stderr）**：
```
Stage testing 工作未完成，请先完成当前阶段工作再推进。
```

**runtime.stage 落点**：`testing`（**gate 阻塞成功，未跳 acceptance**）

**结论：DOGFOOD PASS** — 第一格 gate 阻断 over-chain，BUG-01 修复有效。

---

### 全量回归

| 范围 | 结果 |
|------|------|
| `pytest tests/` 全量（含 chg-01 9 用例） | **591 passed / 38 skipped / 0 new fail** |
| pre-existing failures | test_smoke_req28（README 缺 pip install -U）/ test_smoke_req29（req-29 归档结构），均与 chg-01 无关 |

---

### 合规扫描（5 项）

| 项 | 扫描内容 | 结果 |
|----|---------|------|
| R1 越界核查 | commit b64bcd7 diff：src/workflow_helpers.py + src/validate_contract.py + tests/ + .workflow/state/ + flow/requirements/req-45-*/ | ✅ PASS — 仅触碰 req-45 scope，未越界 |
| revert 抽样 | 本次二次测试**不跑 git restore**（红线）；已验证 git status 无非 chg-01 改动 | ✅ PASS（无 git 破坏命令） |
| 契约 7 合规 | change.md:14 存在裸 `` `req-45` ``（template 遗留，1st testing 已登记 BUG-04 P3） | ⚠️ PARTIAL（遗留 P3，已知缺陷，建议后续 executing 补回） |
| req-29（角色→模型映射）回归 | git log -- .workflow/context/role-model-map.yaml：最近修改在 req-43 前，chg-01 未碰 | ✅ PASS |
| req-30（用户面 model 透出）回归 | session-memory.md 含"testing / sonnet"自我介绍 + 本 test-report.md 角色行含"testing / sonnet" | ✅ PASS |

---

## §证据

1. `python3 -m pytest tests/test_workflow_next_workdone_gate.py -v` → 9 passed（0.90s）
2. `python3 -m pytest tests/` → 591 passed / 38 skipped / 0 new fail
3. dogfood tmpdir mock → stdout 含 "Stage testing 工作未完成"，runtime.stage=testing（不跳 acceptance）
4. 反例-A/B/C：`_is_stage_work_done` 均正确返回 False，gate 实现健壮
5. `_has_conclusion_heading` regex `##\s*§?结论` 严格匹配标题级，排除正文/注释误匹配
6. `_is_stage_work_done` 第一格 gate 位于 `_write_stage_transition` 之前（line 7536-7551），覆盖第一跳
7. same_role 路径（requirement_review→planning）绕过 gate，bugfix-5（同角色跨 stage 自动续跑硬门禁）契约不破

---

## §缺陷登记

| ID | 描述 | 严重级别 | 状态 |
|----|------|---------|------|
| BUG-01 | gate 插桩位置错（1st testing 发现）：第一格跳转无 gate 检查，AC-01/02 未满足 | P0 Critical | **已修复（2nd executing，commit b64bcd7）** |
| BUG-02 | TC-02 断言写给错误实现（1st testing 发现）：`stage=acceptance` 应改 `stage=testing` | P0 | **已修复（2nd executing，TC-02/03/06 同步修正）** |
| BUG-03 | 1st testing 阶段 `git restore .` 意外丢失 executing source 改动（workflow_helpers.py + validate_contract.py） | P0 Critical | **已修复（2nd executing 重做 + commit b64bcd7 + push）** |
| BUG-04（次要） | change.md §3 裸 `` `req-45` ``（template 遗留，契约 7 违规） | P3 | 开放（建议后续 executing 补回，不阻塞 testing 通过） |

**活跃缺陷**：0 P0/P1 / 1 P3（不阻塞）

---

## §结论

**PASS — gate 生效，BUG-01/02/03 已修复，二次干净验证通过**

1. **9 unit 全过**：TC-01～TC-08（含 TC-03b），9/9 PASS，commit b64bcd7 代码健壮。
2. **dogfood gate PASS**：第一格 gate 在 `_write_stage_transition` 前阻断，testing 缺 test-report.md 时 `harness next` 停在 testing，over-chain 完全封堵。
3. **反例 3 条通过**：`_has_conclusion_heading` 严格标题级匹配，正文/注释误匹配排除，executing session-memory ❌无 ✅ 正确 False。
4. **全量回归 591 pass**：pre-existing failures（test_smoke_req28 / test_smoke_req29）与 chg-01 无关。
5. **合规 4/5 PASS**：change.md 裸 `req-45` P3 遗留已知，不阻塞。
6. **零 git 破坏命令**：dogfood 用 tmpdir mock，未执行任何 git restore/reset/checkout。
7. **1st testing 事故说明**：第一次 testing 执行了 `git restore .`，丢失 executing 产物，已由 2nd executing 修复（commit b64bcd7）。

**本阶段已结束。**
