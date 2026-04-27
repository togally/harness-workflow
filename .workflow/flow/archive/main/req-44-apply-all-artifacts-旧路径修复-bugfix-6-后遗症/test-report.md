# Test Report — req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））

- 测试日期：2026-04-25
- 测试工程师：testing subagent（Sonnet 4.6）
- 所属 stage：testing

---

## §测试矩阵

### A. plan.md §4 复测（11 用例）

#### chg-01（apply / apply-all CLI 路径与内容修复）— 6 用例

| 用例 | 描述 | 优先级 | 对应 AC | 结果 |
|------|------|--------|---------|------|
| TC-01 | apply-all 后 bugfix-6 路径成功（req-id ≥ 41 走 flow/ 目录） | P0 | AC-01 | ✅ PASS |
| TC-02 | apply-all legacy req-id 路径仍兼容（req-id ≤ 40 走 artifacts/） | P1 | AC-01 | ✅ PASS |
| TC-03 | apply-all req_md 不存在时不 unlink（exit ≠ 0 + sug 保留 + stderr ERROR） | P0 | AC-01 | ✅ PASS |
| TC-04 | apply 单 sug 取 sug.frontmatter title 当 req title（不取 content 首行） | P0 | AC-02 | ✅ PASS |
| TC-05 | apply 单 sug 真写入 requirement.md（含 ## 合并建议清单 + BODY-MARKER） | P0 | AC-02 | ✅ PASS |
| TC-06 | apply 单 sug 后 bugfix-6 路径落位（req-id ≥ 41 req_md 在 flow/） | P0 | AC-02 | ✅ PASS |

#### chg-02（rename CLI 同步范围扩展）— 5 用例

| 用例 | 描述 | 优先级 | 对应 AC | 结果 |
|------|------|--------|---------|------|
| TC-01 | rename 同步 .workflow/flow/ 目录（三处目录都改名） | P0 | AC-03 | ✅ PASS |
| TC-02 | rename 同步 runtime current_requirement_title | P0 | AC-03 | ✅ PASS |
| TC-03 | rename 同步 runtime locked_requirement_title | P1 | AC-03 | ✅ PASS |
| TC-04 | rename 不命中 current 时不动 runtime title | P1 | AC-03 | ✅ PASS |
| TC-05 | rename legacy req-id（无 flow/ 目录）兼容，静默跳过 | P1 | AC-03 | ✅ PASS |

**复测小计：11/11 PASS**

---

### B. 独立反例补充（testing 自补，4 条）

| 用例 | 描述 | 边界类型 | 结果 |
|------|------|---------|------|
| EC-01 | apply-all 空 pending 池 → exit 0 幂等 no-op | apply-all 边界 | ✅ PASS |
| EC-02 | _append_sug_body_to_req_md 幂等聚合（## 合并建议清单 marker 不重复） | apply 内部边界 | ✅ PASS |
| EC-03 | rename 相同 title 不崩溃（noop rename 容错） | rename 边界 | ✅ PASS |
| EC-04 | apply 单 sug body 写入 OSError 时 sug 仍被 archive（不阻断） | apply 写入失败 | ✅ PASS |

**独立反例小计：4/4 PASS**

---

### C. Dogfood 实跑

| 场景 | 操作 | 验证点 | 结果 |
|------|------|--------|------|
| mock sug apply 全链 | seed sug-99（frontmatter title + DOGFOOD-BODY-MARKER）→ apply_suggestion | title 来自 frontmatter；req_md 含 DOGFOOD-BODY-MARKER；sug 已 archive | ✅ PASS |
| mock req rename | rename_requirement(cur_req, "Renamed Dogfood Req") | runtime.current_requirement_title = "Renamed Dogfood Req" | ✅ PASS |

**Dogfood 小计：2/2 PASS**

---

### D. 合规扫描 5 项

| 扫描项 | 检查内容 | 结果 | 备注 |
|--------|---------|------|------|
| 1. R1 越界核查 | git diff --name-only 命中文件：workflow_helpers.py（src/）+ feedback.jsonl / runtime.yaml（.workflow/state/）+ tests/ ；均在 requirement.md §3.1 IN 范围内 | ✅ PASS | workflow_helpers.py 是本 req 核心改动文件，tests/ 为配套测试，均合规 |
| 2. revert 抽样 | git stash + git revert --no-commit HEAD dry-run（HEAD = req-43 archive commit）→ conflict = 0；git stash pop 恢复正常 | ✅ PASS | 无 merge conflict |
| 3. 契约 7 合规扫描 | grep 命中 req-44 目录下所有 .md 文件首次 id 引用，均带括号简短描述（sug-43（apply-all artifacts/ 旧路径检查导致 abort）等）；唯一例外：change.md §3 Requirement 字段 `- \`req-44\`` 为模板结构字段非叙述性引用 | ✅ PASS（minor） | change.md §3 模板字段轻微违规（非叙述性结构引用），不阻断 |
| 4. req-29（角色→模型映射）映射回归 | git diff -- .workflow/context/role-model-map.yaml 为空（本 req 未改动 yaml）；session-memory 含 analyst/opus + executing/sonnet 自检记录 | ✅ PASS | |
| 5. req-30（用户面 model 透出）回归 | session-memory grep `expected_model: sonnet（Sonnet 4.6）` ✓；`technical-director / opus` ✓；executing 自检 `role = executing，与 role-model-map.yaml 一致` ✓ | ✅ PASS | |

**合规扫描小计：5/5 PASS**

---

### E. 全量回归

```
pytest tests/ -q → 591 passed, 2 failed, 38 skipped
```

| 测试项 | 结果 |
|--------|------|
| test_req44_chg01.py（6 用例） | ✅ PASS |
| test_req44_chg02.py（5 用例） | ✅ PASS |
| test_req44_testing_extra.py（4 独立反例） | ✅ PASS |
| FAILED tests/test_smoke_req28.py::test_readme_has_refresh_template_hint | ⚠️ pre-existing（与本 req 无关） |
| FAILED tests/test_smoke_req29.py::test_human_docs_checklist_for_req29 | ⚠️ pre-existing（与本 req 无关） |

**全量回归：591 passed，2 pre-existing failure，0 new failure**

---

## §证据

| 证据 | 来源 |
|------|------|
| 11 用例 PASS | `python3 -m pytest tests/test_req44_chg01.py tests/test_req44_chg02.py -v` → 11 passed in 0.59s |
| 4 独立反例 PASS | `python3 -m pytest tests/test_req44_testing_extra.py -v` → 4 passed in 0.29s |
| Dogfood 全链 | python3 inline script → `[dogfood] all assertions passed ✅` |
| revert dry-run | `git stash + git revert --no-commit HEAD + git revert --abort + git stash pop` → no conflict |
| 全量回归 | `python3 -m pytest tests/ -q` → 591 passed, 2 failed (pre-existing), 38 skipped in 84s |
| 合规扫描 | grep 逐项扫描 + git diff role-model-map.yaml 为空 |

---

## §缺陷

本轮测试无发现新缺陷。

**pre-existing 缺陷（与本 req 无关）：**

| 缺陷 ID | 描述 | 状态 |
|---------|------|------|
| pre-existing-1 | test_smoke_req28.py::test_readme_has_refresh_template_hint — README 模板刷新提示检查失败 | pre-existing，不属本 req 范围 |
| pre-existing-2 | test_smoke_req29.py::test_human_docs_checklist_for_req29 — req-29 对人文档 changes/ 目录结构检查失败 | pre-existing，不属本 req 范围 |

---

## §结论

**判定：PASS**

- chg-01（apply / apply-all CLI 路径与内容修复）：6/6 用例 PASS，AC-01 + AC-02 全覆盖。
- chg-02（rename CLI 同步范围扩展）：5/5 用例 PASS，AC-03 全覆盖。
- 独立反例 4 条 PASS（边界：空 pending 池 / 幂等聚合 / noop rename / 写入失败不阻断）。
- Dogfood 全链跑通（apply + rename 实证）。
- 合规扫描 5 项全 PASS（R1 越界 / revert dry-run / 契约 7 / req-29（角色→模型映射）映射 / req-30（用户面 model 透出）透出）。
- 全量回归 591 passed，0 new failure，2 pre-existing failure 与本 req 无关。
- AC-05（e2e 用例数 ≥ 2 per 类）：apply 6 条 + apply-all 含于 chg-01 + rename 5 条，均超额。

**推荐流转：testing → acceptance**
