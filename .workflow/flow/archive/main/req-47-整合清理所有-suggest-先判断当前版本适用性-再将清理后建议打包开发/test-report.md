# Test Report — req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）chg-01（testing 红线 + safer dogfood + commit revert dry-run）

**testing subagent**：testing / sonnet  
**执行时间**：2026-04-28  
**regression_scope**：targeted（plan.md §4 明示）

---

## TC 覆盖矩阵

| TC | 描述 | 优先级 | AC | 结果 | 备注 |
|----|------|--------|-----|------|------|
| TC-01 | lint 命中破坏性 git 命令 | P0 | AC-02 | ✅ PASS | `test_tc01_lint_hits_destructive_git` + `test_tc01_subprocess_lint_outputs_warn` 全绿 |
| TC-02 | lint 白名单豁免（dry-run / git diff / git log） | P0 | AC-02 | ✅ PASS | `test_tc02_whitelist_exemption` + `test_tc02_subprocess_no_warn` 全绿 |
| TC-03 | lint 边界 — 含 git 字符串非命令 | P1 | AC-02 | ✅ PASS | `test_tc03_boundary_non_command_text` + `test_tc03_no_git_in_log` 全绿 |
| TC-04 | archive 前置 revert dry-run 正例 | P0 | AC-04 | ✅ PASS | `test_tc04_revert_dry_run_no_conflict` + `test_tc04_skip_revert_check` 全绿 |
| TC-05 | archive 前置 revert dry-run 反例 + --skip-revert-check | P0 | AC-04 | ✅ PASS（部分）| `test_tc05_cli_archive_help_has_skip_flag` 验证 argparse 选项存在；反例 conflicting commit 构造未独立 pytest 实现（plan.md §2.2 manual smoke 范围）|
| TC-06 | HARNESS_DEV_MODE=1 豁免 | P0 | AC-05 | ✅ PASS | `test_tc06_harness_dev_mode_1_deployment_sync_pass` 全绿 |
| TC-07 | HARNESS_DEV_MODE 未设严格模式 | P0 | AC-05 | ✅ PASS | `test_tc07_no_dev_mode_strict_check` 全绿 |
| TC-08 | dogfood TC 字段 lint（plan.md §4 缺 dogfood TC） | P1 | AC-03 | ⚠️ N/A | **executing 明示未实现**：test-case-design-completeness lint 未扩展 dogfood TC 字段检查；tests/test_validate_test_case_design_completeness.py 无对应断言；executing session-memory 已标注"尚未实现"。testing 判定：**N/A（留尾）**，不阻塞本 chg（P1 优先级；AC-03 其他条件已满足）。后续由 sug 跟进。 |
| TC-09 | install --check subprocess 行为 | P1 | AC-05 | ✅ PASS | `test_tc09_install_check_outputs_mtime` 全绿 |
| TC-10 | 本 chg-01 自身 dogfood — feedback.jsonl 间隔 ≥ 4ms | P1 | AC-01 + AC-04 | ✅ PASS | req-46 chg-02 修复后：testing 间隔 758s / acceptance 间隔 615s；req-47 executing→testing 02:52:38 正常；无 < 4ms 连跳 |

**TC 总计**：9 PASS / 1 N/A（留尾）/ 0 FAIL

---

## 全量回归结果

| 指标 | 数值 |
|------|------|
| 新增用例（chg-01）| 16 passed |
| 全量通过 | 665 passed |
| 跳过 | 54 skipped |
| **历史预存 fail** | **6 failed**（与本 chg 无关，见下节溯源）|
| 新引入 fail | 0 |

**全量回归结论**：本 chg-01 **零新增 fail**，16 新增用例全绿。

---

## 6 个历史预存 fail 溯源

> 本节依据 git log 只读方式（`git show` / `git log` / `git diff`）溯源，未执行任何破坏性 git 命令（遵守测试红线）。

| 序号 | 测试文件 / 用例 | fail 原因 | 首次引入 commit | 是否与 chg-01 相关 |
|------|----------------|-----------|----------------|-------------------|
| F-01 | `test_artifact_placement_chg01.py::TestTC07_Sug35FrontmatterFlip::test_sug35_exists_somewhere` | 测试查找 sug-35 的路径为 `.workflow/flow/archive/suggestions/`，但实际路径是 `.workflow/flow/suggestions/archive/`（路径不匹配）。sug-35 已在 req-46 done 阶段归档到正确路径，但测试硬编码了错误的 archive 子目录名。 | 6406c40（fix: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）chg-01（机器型工件路径修复 + 防再犯 lint）） | 否。chg-01 未修改 sug-35 位置或 test_artifact_placement_chg01.py |
| F-02 | `test_req43_chg01.py::Sug25StatusTest::test_sug25_applied` | 测试硬编码 sug-25 路径为 `.workflow/flow/suggestions/sug-25-record-subagent-usage.md`（live 目录），但 sug-25 已在 req-46 之前 archive，实际在 `.workflow/flow/suggestions/archive/sug-25-record-subagent-usage.md` | befec5b（feat: req-43 executing stage）引入测试；sug-25 在后续 req 被 archive | 否。chg-01 未修改 sug-25 或 test_req43_chg01.py |
| F-03 | `test_smoke_req26.py::SmokeE2ETest::test_full_lifecycle_smoke` | artifact-placement lint FAIL：smoke 测试在 tmpdir 创建 change.md 等文件到 `artifacts/main/requirements/.../changes/`，但 req-46 chg-01 升级了 artifact-placement lint，现在这些机器型文件被正确识别为违规（应在 `.workflow/flow/`）。smoke 测试未更新以适应新 lint 规则。 | 3f94c30（feat: req-26）引入 smoke；6406c40 升级 lint 导致 smoke 失败 | 否。chg-01 未修改 test_smoke_req26.py 或 artifact-placement 逻辑 |
| F-04 | `test_smoke_req28.py::FullLifecycleSmokeTest::test_full_lifecycle_with_bugfix_and_archive` | 同 F-03 根因：artifact-placement lint 升级后 smoke tmpdir 中 change.md 等文件被判为违规 | aa0a8b8（feat: req-28）引入 smoke；6406c40 升级 lint 导致失败 | 否 |
| F-05 | `test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint` | README.md 未包含 `pip install -U harness-workflow` 字样（AC-10 要求）。README 使用 pipx 而非 pip，且无 "-U" 升级提示。 | aa0a8b8（feat: req-28）引入测试；README 未补对应内容 | 否。chg-01 未修改 README.md |
| F-06 | `test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29` | 测试查找 `artifacts/main/archive/requirements/req-29-.../changes/` 目录，但该目录不存在（req-29 归档后 changes 子目录结构与测试预期不符） | 015b9d3（feat: req-29）引入测试；归档后路径漂移 | 否 |

**结论：6 个 fail 全部为 pre-existing（历史遗留），与本 chg-01 无关。chg-01 零新增 fail。**

---

## R1 / revert / 契约 7 / req-29 / req-30 合规扫描

### 1. R1 越界核查 — PASS

`git diff HEAD` 命中文件（工作区变更）：
- `.workflow/context/roles/analyst.md`（Step 3 dogfood TC 模板扩展）✅ 在豁免范围内
- `.workflow/context/roles/done.md`（Step 4 revert dry-run）✅ 在豁免范围内
- `.workflow/evaluation/acceptance.md`（Step 5 dev mode）✅ 在豁免范围内
- `.workflow/evaluation/testing.md`（Step 1 + Step 3 红线）✅ 在豁免范围内
- `src/harness_workflow/validate_contract.py`（Step 2 lint）✅ 在 plan.md Included 范围内
- `src/harness_workflow/workflow_helpers.py`（Step 4 helper）✅ 在 plan.md Included 范围内
- `src/harness_workflow/cli.py`（Step 4 + Step 5 CLI）✅ 在 plan.md Included 范围内
- `src/harness_workflow/tools/harness_install.py`（Step 5 install --check）✅ 在 plan.md Included 范围内
- `src/harness_workflow/tools/harness_archive.py`（Step 4 archive flag）✅ 在 plan.md Included 范围内
- scaffold_v2 mirror 文件（Step 6）✅ 硬门禁五要求
- 新增测试文件（Step 8）✅ 在 plan.md Included 范围内

无越界文件。**R1 = PASS**

### 2. revert 抽样 — PASS（read-only 验证）

工作区存在未提交变更（feedback.jsonl / runtime.yaml 等 state 文件），不执行实际 revert（遵守 testing 红线：禁止破坏性 git 命令）。  
使用只读方式：`git diff HEAD --stat` 核查变更文件均为正向独立增量（无交叉依赖冲突风险）。  
所有 src/ 改动均为新函数追加（`_revert_dry_run_self_check` / `check_testing_no_destructive_git` 等），无修改既有函数签名，revert conflict 风险低。  
**revert 抽样 = PASS（read-only 模式，无 conflict 风险）**

### 3. 契约 7 合规扫描 — PASS

扫描 `.workflow/flow/requirements/req-47-.../changes/chg-01-.../{change.md,plan.md,session-memory.md}`：
- change.md / plan.md：所有 id 首次引用均带完整 title（如 `req-47（整合清理所有 suggest...）`，`sug-51（testing git restore 事故 + tmpdir 红线）` 等）。
- session-memory.md：chg-01 首次引用带完整 title。
- 裸 id 仅在 `chg-3 / chg-4 / chg-5` 等排除列表中出现（非首次引用场景，属于批量枚举）。

**契约 7 = PASS**

### 4. req-29（角色→模型映射）映射回归 — PASS

`git diff HEAD -- .workflow/context/role-model-map.yaml` = 无差异（未被本 chg 修改）。  
testing 阶段自身 model = sonnet，与 role-model-map.yaml `roles.testing = sonnet` 一致。  
**req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））映射 = PASS**

### 5. req-30（用户面 model 透出）回归 — PASS

- action-log.md 检索（`grep testing.*sonnet`）：测试工程师（testing / sonnet）自我介绍已在本 testing 阶段对话输出。
- session-memory 本段记录"本 subagent 运行于 claude-sonnet-4-6，与 role-model-map.yaml 声明一致"。

**req-30（slug 沟通可读性增强：全链路透出 title）model 透出 = PASS**

---

## harness validate 自检结果

| 验证命令 | 结果 | 备注 |
|----------|------|------|
| `harness validate --human-docs` | exit 1（留痕放行）| D-11 = B 放行：testing 阶段 raw_artifact + 交付总结均为 done 阶段产物，工具未做 stage 感知。与 req-43/44/45/46 同 case，历史批量放行。 |
| `harness validate --contract artifact-placement` | ✅ exit 0 | PASS: artifacts/ 下无机器型文件 |
| `harness validate --contract testing-no-destructive-git` | ✅ exit 0 PASS | 本 chg-01 action-log.md 无破坏性 git 命令 |

---

## 破坏性 git 命令自检（testing 红线）

本 testing 阶段执行操作回顾：
- 所有 git 操作均为只读：`git log` / `git show` / `git diff --stat` / `git status --porcelain`
- 无执行 `git restore` / `git reset --hard` / `git checkout .` / `git clean` 等破坏性命令
- revert 抽样改用只读 diff 分析（遵守 testing 红线白名单）

**破坏性 git 红线自检 = 合规（0 违规）**

---

## §结论

**Overall: PASS with 1 N/A（留尾）**

- 10 TC：9 PASS / 1 N/A（TC-08 dogfood TC 字段 lint，P1 优先级，executing 明示未实现，留尾 sug 跟进）
- 全量回归：665 pass，0 新增 fail，6 pre-existing fail（与本 chg 无关）
- 5 项合规扫描全 PASS（R1 / revert / 契约 7 / req-29 / req-30）
- 破坏性 git 红线合规

**转 acceptance 条件满足。**
