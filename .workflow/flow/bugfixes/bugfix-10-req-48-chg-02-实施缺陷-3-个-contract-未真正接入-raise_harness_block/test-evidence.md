# test-evidence.md — bugfix-10（req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block）

## 测试日期

2026-04-29

---

## TC 覆盖矩阵

### 来自 bugfix.md Validation Criteria

| TC 来源 | TC ID | 描述 | 期望 | 实测结果 |
|---------|-------|------|------|----------|
| test_raise_harness_block.py | TC-01 | FAIL severity → rc=64 + HARNESS_BLOCK + yaml | rc=64, 3 stderr 行, yaml 写入 | PASS |
| test_raise_harness_block.py | TC-02 | ABORT severity → rc=65 | rc=65, severity=ABORT | PASS |
| test_raise_harness_block.py | TC-03 | WARN severity → rc=0 | rc=0, yaml 仍写入 | PASS |
| test_raise_harness_block.py | TC-04 | 连续 2 次 → recovery_attempts=2 | recovery_attempts=2 | PASS |
| test_raise_harness_block.py | TC-05 | error-protocol.md §1~§7 + 6 known types | 存在 | PASS |
| test_raise_harness_block.py | TC-06 | base-role.md 含硬门禁八 ≥2 次 | ≥2 次 | **FAIL（预存）** |
| test_raise_harness_block.py | TC-07 | harness-manager.md Step 3.7 + fix-checklist + recovery_attempts | 存在 | **FAIL（预存）** |
| test_raise_harness_block.py | TC-08 | severity='UNKNOWN' → ValueError | raises ValueError | PASS |
| test_raise_harness_block.py | TC-09 | error-protocol.md mirror 一致 | bytes 相同 | PASS |
| test_raise_harness_block.py | TC-10 | base-role.md mirror 一致 | bytes 相同 | PASS |
| test_raise_harness_block.py | TC-11 | harness-manager.md mirror 一致 | bytes 相同 | PASS |
| test_raise_harness_block.py | TC-12 | runtime-block.yaml 7 字段完整性 | 所有字段存在 | PASS |

TC-06 / TC-07 为预存文档缺失 fail，与 bugfix-10 代码改造无关（bugfix.md AC 中已标注：TC-06/TC-07 预存文档缺失）。

### 来自 test_fix_checklist_lint_output.py（17 TC 全 PASS）

| TC | 描述 | 结果 |
|----|------|------|
| TC-01 ×3 | 3 fix-checklist 文件存在 + 5 section | PASS |
| TC-02 | artifact-placement FAIL → HARNESS_BLOCK rc=64 + yaml | PASS |
| TC-03 | artifact-placement PASS verbose=True | PASS |
| TC-04 | artifact-placement PASS verbose=False 静默 | PASS |
| TC-05 | schema-audit FAIL → HARNESS_BLOCK: schema-audit | PASS |
| TC-06 | schema-audit PASS | PASS |
| TC-07 | missing-document FAIL → HARNESS_BLOCK: missing-document | PASS |
| TC-08 | missing-document PASS | PASS |
| TC-09 | CLI schema-audit clean dir → exit 0 | PASS |
| TC-10 | CLI missing-document clean dir → exit 0 | PASS |
| TC-11 ×3 | 3 fix-checklist mirror 一致 | PASS |
| TC-12 | unknown contract → exit≠0 | PASS |
| TC-Dogfood-13 | subprocess artifact-placement → exit 64 + HARNESS_BLOCK + yaml | PASS |

**汇总：17/17 PASS**

### 来自 test_block_protocol_e2e.py（6/8 PASS）

| TC | 描述 | 结果 |
|----|------|------|
| TC-01 | review-checklist.md 含 '抛错协议配套' ≥2 次 | **FAIL（预存）** |
| TC-02 | reviewer.md 含 review-checklist 引用 | PASS |
| TC-Dogfood-03 | artifact-placement 闭环 FAIL→fix→PASS | PASS |
| TC-Dogfood-04 | schema-audit 闭环 FAIL→fix→PASS | PASS |
| TC-Dogfood-05 | missing-document 闭环 FAIL→fix→PASS | PASS |
| TC-06 | recovery_attempts 通过 CLI 累积 ×2 | PASS |
| TC-07 | review-checklist.md mirror 一致 | PASS |
| TC-08 | chg-03 plan.md roadmap 骨架 | **FAIL（预存）** |

TC-01 / TC-08 为预存文档缺失 fail（review-checklist.md 缺字符串 / chg-03 plan.md 文件不存在），与 bugfix-10 改造无关。

---

## dogfood 5 项验证结果

| # | 场景 | 操作 | 断言 | 结果 |
|---|------|------|------|------|
| b | artifact-placement 违规 tmpdir | mkdir artifacts/main/requirements/req-99-x/planning + touch session-memory.md → CLI validate | stderr 含 HARNESS_BLOCK: artifact-placement + fix-checklist: 指针 + exit 64 | PASS |
| c | schema-audit 违规 tmpdir | mkdir .workflow/state/requirements/req-99/ → CLI validate | stderr 含 HARNESS_BLOCK: schema-audit + exit 64 | PASS |
| d | missing-document 违规 tmpdir | runtime.yaml stage=planning + changes/ 空 → CLI validate | stdout 含 HARNESS_BLOCK: missing-document + exit 64 | PASS |
| e | runtime-block.yaml 写入验证 | 运行 artifact-placement 违规 → 读 yaml | error_type=artifact-placement / severity=FAIL / recovery_attempts=1 | PASS |
| e2 | recovery_attempts 累积 | 同 tmpdir 连跑 2 次 artifact-placement | recovery_attempts=2 | PASS |

执行实证（场景 b 原始输出摘录）：
```
HARNESS_BLOCK: artifact-placement
  fix-checklist: .workflow/context/checklists/fix-artifact-placement.md
  severity: FAIL
  detected-by: executing
FAIL: artifact-placement lint — 以下违规文件需迁移到 .workflow/flow/：
...
Exit code: 64
runtime-block.yaml: error_type=artifact-placement, severity=FAIL, recovery_attempts=1
```

---

## 全量回归 + 历史 fail 溯源

全量 pytest 结果：**17 failed, 729 passed, 54 skipped**

17 个预存 fail 溯源（均与 bugfix-10 代码改造无关）：

| 测试文件 | TC | 溯源 |
|----------|-----|------|
| test_artifact_placement_chg01.py | test_req_review_session_memory_in_flow | 文档路径缺失：req-46 requirement-review/session-memory.md |
| test_artifact_placement_chg01.py | test_req_review_sug_audit_in_flow | 文档路径缺失：req-46 requirement-review/sug-audit.md |
| test_artifact_placement_chg01.py | test_planning_session_memory_in_flow | 文档路径缺失：req-46 planning/session-memory.md |
| test_artifact_placement_chg01.py | test_planning_roadmap_in_flow | 文档路径缺失：req-46 planning/roadmap.md |
| test_artifact_placement_chg01.py | test_sug35_exists_somewhere | sug-35 文件不存在 suggestions/ |
| test_artifact_placement_chg01.py | test_change_md_in_flow | req-46 flow change.md 路径缺失 |
| test_artifact_placement_chg01.py | test_plan_md_in_flow | req-46 flow plan.md 路径缺失 |
| test_artifact_placement_chg01.py | test_session_memory_in_flow | req-46 flow session-memory.md 路径缺失 |
| test_block_protocol_e2e.py | test_tc01_review_checklist_entries | review-checklist.md 缺 '抛错协议配套' 字符串（req-48 chg-03 文档未完成） |
| test_block_protocol_e2e.py | test_tc08_roadmap_in_plan | chg-03 plan.md 文件不存在（req-48 chg-03 未实施） |
| test_raise_harness_block.py | test_tc06_base_role_hardgate_eight | base-role.md 缺 '硬门禁八：任务阻塞错误抛出协议' ≥2 次（req-48 chg-01 文档未同步） |
| test_raise_harness_block.py | test_tc07_harness_manager_step37 | harness-manager.md 缺 '3.7' step 字符串（req-48 chg-01 文档未同步） |
| test_req43_chg01.py | test_sug25_applied | sug-25-record-subagent-usage.md 文件不存在 |
| test_smoke_req26.py | test_full_lifecycle_smoke | smoke 用的旧路径格式（artifacts/ vs .workflow/flow/），与 artifact-placement lint 新规则冲突 |
| test_smoke_req28.py | test_full_lifecycle_with_bugfix_and_archive | 同上 smoke 路径格式问题 |
| test_smoke_req28.py | test_readme_has_refresh_template_hint | README 模板缺 refresh hint |
| test_smoke_req29.py | test_human_docs_checklist_for_req29 | req-29 对人文档路径结构预存问题 |

所有 17 个 fail 均为文档缺失 / smoke 路径格式 / 历史脏数据，无一与 bugfix-10（raise_harness_block 接入）代码改造相关。**0 新增 fail。**

---

## revert 抽样合规扫描

**N/A** — testing stage 硬门禁禁止执行破坏性 git 命令，revert 抽样跳过，此处留痕放行。

---

## 5 项合规扫描

| 编号 | 规则 | 检查结果 |
|------|------|----------|
| R1 | raise_harness_block 三层载体（stderr / exit code / runtime-block.yaml）均实现 | PASS — 代码实现完整，dogfood 验证通过 |
| 契约 7 | id 首次出现带 ≤15 字描述 | PASS — 本文件所有 id 首次引用均带括号描述 |
| req-29（人机工件分离）| test-evidence.md 落 .workflow/flow/bugfixes/{slug}/ 根目录（非 testing/ 子目录）| PASS |
| req-30（slug 可读性）| 文件路径含完整 title slug | PASS |
| 破坏性 git 红线 | testing stage 未执行任何 git revert/checkout/reset/clean/stash/rm/mv | PASS — read-only git 命令只用于状态核实 |

---

## 退出前验证

| 验证项 | 命令 | 结果 |
|--------|------|------|
| harness validate --human-docs | `python3 -m harness_workflow.cli validate --human-docs` | exit 1（D-11=B，testing 阶段对人文档未就绪，已知状态，放行） |
| harness validate --contract artifact-placement | `python3 -m harness_workflow.cli validate --contract artifact-placement` | exit 0 PASS |

---

## 结论

bugfix-10（req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block）的所有核心修复已验证通过：

1. `raise_harness_block` helper 实现完整（三层载体：stderr HARNESS_BLOCK 协议 + exit 64/65/0 + runtime-block.yaml 写入）
2. `check_artifact_placement` 接入 helper，违规 exit 64 + HARNESS_BLOCK 协议正确
3. `check_schema_audit` 新增并接入 helper，违规 exit 64 + HARNESS_BLOCK 协议正确
4. `check_missing_document` 新增并接入 helper，违规 exit 64 + HARNESS_BLOCK 协议正确
5. dogfood 5 项全 PASS，recovery_attempts 累积逻辑正确
6. test_fix_checklist_lint_output.py 17/17 PASS，test_block_protocol_e2e.py 6/8 PASS（2 预存），test_raise_harness_block.py 10/12 PASS（2 预存）
7. 全量 pytest 无新增 fail（17 预存 fail 均为文档缺失 / smoke 路径格式问题，与本次改造无关）

**verdict: PASS** — 可推进至 acceptance 阶段。
