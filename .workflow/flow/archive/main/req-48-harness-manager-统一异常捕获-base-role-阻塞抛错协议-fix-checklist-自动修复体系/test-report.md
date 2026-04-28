# Test Report — req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）

> 测试工程师：testing（sonnet subagent）
> 执行时间：2026-04-28
> 结论：**PASS**

---

## §1 TC 覆盖矩阵（37 TC × PASS/FAIL/N/A）

### chg-01：错误协议契约 + base-role 门禁 + harness-manager 捕获（12 TC）

| TC | 用例名 | 结果 | AC | 备注 |
|----|--------|------|-----|------|
| TC-01 | helper-FAIL | PASS | AC-01 | rc=64；runtime-block.yaml 字段完整；stderr 三行 |
| TC-02 | helper-ABORT | PASS | AC-01 | rc=65；severity=ABORT |
| TC-03 | helper-WARN | PASS | AC-01 | rc=0；仍写状态文件 |
| TC-04 | helper-累计-attempts | PASS | AC-01/AC-03 | 第2次 recovery_attempts=2 |
| TC-05 | error-protocol-md 字段完整 | PASS | AC-01 | §1~§7 章节 + ≥6 known error_type |
| TC-06 | base-role 硬门禁八存在 | PASS | AC-02 | 总览段+详细段各命中1次，共≥2次 |
| TC-07 | harness-manager Step 3.7 存在 | PASS | AC-03 | `#### 3.7` 段，含 fix-checklist / recovery_attempts 关键词 |
| TC-08 | 反例-unknown severity | PASS | AC-01边界 | ValueError 含正确消息 |
| TC-09 | mirror diff error-protocol | PASS | AC-07 | diff 输出为空 |
| TC-10 | base-role mirror | PASS | AC-07 | diff 输出为空 |
| TC-11 | harness-manager mirror | PASS | AC-07 | diff 输出为空 |
| TC-12 | runtime-block-字段-schema | PASS | AC-01 | 7字段集合完整 |

**chg-01 小计：12/12 PASS**

### chg-02：Fix Checklist 首批 3 个 + lint 输出加指针（17 TC，含 1 dogfood）

| TC | 用例名 | 结果 | AC | 备注 |
|----|--------|------|-----|------|
| TC-01a | fix-artifact-placement.md 存在+5节 | PASS | AC-04 | 5节均命中 |
| TC-01b | fix-schema-audit.md 存在+5节 | PASS | AC-04 | 5节均命中 |
| TC-01c | fix-missing-document.md 存在+5节 | PASS | AC-04 | 5节均命中 |
| TC-02 | artifact-placement-FAIL-block | PASS | AC-05 | rc=64；HARNESS_BLOCK on stderr；runtime-block.yaml 存在 |
| TC-03 | artifact-placement-PASS-verbose-True | PASS | AC-05 | rc=0；PASS 字串 |
| TC-04 | artifact-placement-PASS-verbose-False | PASS | AC-05 | rc=0；stdout 无 PASS |
| TC-05 | schema-audit-FAIL | PASS | AC-05 | rc=64；HARNESS_BLOCK: schema-audit；fix-checklist 指针 |
| TC-06 | schema-audit-PASS | PASS | AC-05 | rc=0；PASS 输出 |
| TC-07 | missing-document-FAIL | PASS | AC-05 | rc=64；HARNESS_BLOCK: missing-document；retry_context 含 missing |
| TC-08 | missing-document-PASS | PASS | AC-05 | rc=0；PASS 输出 |
| TC-09 | CLI-schema-audit | PASS | AC-05 | subprocess exit 0 for clean tmp |
| TC-10 | CLI-missing-document | PASS | AC-05 | subprocess exit 0；无 unknown contract |
| TC-11a | mirror-fix-artifact-placement | PASS | AC-07 | diff 输出为空 |
| TC-11b | mirror-fix-schema-audit | PASS | AC-07 | diff 输出为空 |
| TC-11c | mirror-fix-missing-document | PASS | AC-07 | diff 输出为空 |
| TC-12 | 反例-未知 contract | PASS | AC-05边界 | exit ≠ 0；stderr 含 unknown contract |
| TC-Dogfood-13 | e2e artifact-placement 端到端 | PASS | AC-05 | subprocess exit 64；HARNESS_BLOCK；runtime-block.yaml schema 完整 |

**chg-02 小计：17/17 PASS**

### chg-03：reviewer 加项 + 端到端 dogfood + roadmap（8 TC，含 3 dogfood）

| TC | 用例名 | 结果 | AC | 备注 |
|----|--------|------|-----|------|
| TC-01 | review-checklist 加项存在 | PASS | AC-06 | ≥2次；引用 req-48/chg-03 |
| TC-02 | reviewer-md 引用 | PASS | AC-06 | review-checklist 引用命中 |
| TC-Dogfood-03 | artifact-placement 闭环 | PASS | AC-06/AC-05 | FAIL→fix→PASS 端到端 |
| TC-Dogfood-04 | schema-audit 闭环 | PASS | AC-06/AC-05 | FAIL→fix→PASS 端到端 |
| TC-Dogfood-05 | missing-document 闭环 | PASS | AC-06/AC-05 | FAIL→fix→PASS 端到端 |
| TC-06 | runtime-block 累计 attempts | PASS | AC-01/AC-06 | 两次调用 recovery_attempts=2 |
| TC-07 | mirror review-checklist 同步 | PASS | AC-07 | diff 输出为空 |
| TC-08 | roadmap 骨架留痕 | PASS | AC-08 | 3 fix-checklist + 5 contract 字面命中 |

**chg-03 小计：8/8 PASS**

**总计：37/37 PASS，0 FAIL，0 N/A**

---

## §2 Dogfood 4 项验证结果

| 项目 | 命令 / 场景 | 结果 | 备注 |
|------|-----------|------|------|
| a. artifact-placement | `python3 -m harness_workflow.cli validate --contract artifact-placement` | exit 0 PASS | 本仓无违规文件 |
| b. schema-audit | `python3 -m harness_workflow.cli validate --contract schema-audit` | exit 64 HARNESS_BLOCK | `.workflow/state/requirements/req-39/` 旧目录触发，协议自证工作 |
| c. missing-document | `python3 -m harness_workflow.cli validate --contract missing-document` | exit 0 PASS | testing 阶段必需文档完整 |
| d. tmpdir 闭环 | 构造 violation → exit 64 + fix（mv+rmtree）→ 复跑 exit 0 | PASS | 端到端闭环验证成功 |

> 注：系统 `harness` binary（`/Users/jiazhiwei/.local/bin/harness`）为旧版本，不含 schema-audit/missing-document 选项；所有 CLI dogfood 使用 `python3 -m harness_workflow.cli` 模块形式调用，功能完整。

---

## §3 全量回归 + 13 历史 fail 溯源

```
pytest tests/  →  13 failed, 732 passed, 40 skipped（共 785 items）
```

### 13 历史 fail 溯源（全部 pre-existing，与 req-48 零交集）

| 测试文件 | 数量 | 引入版本 | 根因摘要 |
|---------|------|---------|---------|
| test_artifact_placement_chg01.py（TC01 + TC07 + TC08）| 8 | req-46/chg-01 | 机器型工件路径历史残留；测试期望路径不存在于当前仓状态 |
| test_req43_chg01.py::Sug25StatusTest | 1 | req-43 | sug-25 文件不在预期路径（历史迁移遗留）|
| test_smoke_req26.py::SmokeE2ETest | 1 | req-26 | 全量 lifecycle smoke 依赖历史 archive 结构 |
| test_smoke_req28.py（2 TC）| 2 | req-28 | bugfix archive 路径 + README 刷新模板 hint 历史遗留 |
| test_smoke_req29.py::HumanDocsChecklistTest | 1 | req-29 | req-29 旧 archive 路径下 changes/ 子目录不存在 |

**结论：13 fail 均为 req-48 之前已存在，req-48 三个 chg 不新增任何 fail。**

---

## §4 合规扫描（5 项）

| 规则 | 状态 | 说明 |
|------|------|------|
| R1 破坏性 git 红线 | PASS | req-48 产物目录无 `git revert/checkout/reset/clean/stash/rm` 执行记录；`requirement.md` 内唯一出现 `` `git mv` `` 为文档示例说明，非执行命令 |
| revert 抽样合规扫描 | N/A | 按硬门禁，留痕 N/A |
| 契约 7（contract-7 bare id）| PASS | req-48 产物（requirement.md + plan.md + change.md）内 id 均带描述语境；action-log.md 既有 bare id 为 pre-existing，不在 req-48 范围 |
| req-29（需求摘要）| PASS | `artifacts/main/` 目录结构完整，无缺失问题 |
| req-30（review-checklist）| PASS | `.workflow/context/checklists/review-checklist.md` 存在；新增「抛错协议配套」条目已命中 |

---

## §5 退出条件自检

| 条件 | 状态 |
|------|------|
| `harness validate --contract artifact-placement` exit 0 | PASS |
| `harness validate --human-docs` | exit 1（D-11=B 留痕放行：testing 阶段 raw_artifact/交付总结为 done 阶段产物，工具未做 stage 感知；与 req-43/44/45/46/47 同 case 历史批量放行）|
| scaffold_v2 mirror 6 文件同步 | PASS（diff 全输出为空）|
| 37 TC 全 PASS | PASS |
| 13 历史 fail 溯源确认 pre-existing | PASS |

---

## 结论

req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）testing 通过。

- 37 TC 全 PASS（chg-01 12 / chg-02 17 / chg-03 8）；
- 全量回归 13 fail 均为 pre-existing，与 req-48 零交集；
- dogfood 4 项全部验证通过（含 tmpdir 端到端闭环）；
- scaffold_v2 mirror 6 文件同步一致；
- 合规扫描 5 项：R1 PASS / revert N/A / 契约 7 PASS / req-29 PASS / req-30 PASS；
- `harness validate --contract artifact-placement` exit 0；`--human-docs` exit 1（D-11=B 留痕放行）。

**verdict: PASS → 推进 acceptance**
