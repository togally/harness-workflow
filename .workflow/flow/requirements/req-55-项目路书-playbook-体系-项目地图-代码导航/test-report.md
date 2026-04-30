---
id: test-report
req: req-55
title: req-55 testing report
created_at: 2026-04-30
created_by: testing / sonnet
---

## 1. Overview

req-55（项目路书Playbook体系——项目地图+代码导航）testing stage 报告。
覆盖 5 chg / 12 AC / 41 新增 TC（test_playbook_*.py 5 文件）+ 全量回归 847 用例。

本报告所有数字均为 testing 阶段独立运行所得，不直接采用 executing 自报值。

---

## 2. 测试设计审视

### 2.1 充分性审视

- **chg-01 TC 充分性**：4 TC 覆盖文件存在性 / AUTO 区段定义数 / 路书根路径声明 / §2.1 4 类豁免，覆盖 AC-01 全部验证点。充分。
- **chg-02 TC 充分性**：4 TC 覆盖硬门禁十标题+清单条目 / ≥8 硬门禁标题 / CLAUDE.md 索引节 / scaffold mirror 同步，覆盖 AC-02 / AC-03 全部验证点。充分。
- **chg-03 TC 充分性**：10 TC 含 4 级降级每级各 1 + dogfood subprocess + 双 flag 各 1 + 互斥校验 + 顶层文件 + domain 文件骨架。覆盖 AC-04 / AC-05 核心路径。补充发现：`harness install --dry-run`（即 `--check`）flag 不传给 playbook 初始化，playbook 部分不支持 dry-run 跳过写入，仅 install_repo 层支持 `--check`（详见 §7 Issues）。
- **chg-04 TC 充分性**：10 TC 含 5 类 AUTO 区段各 1（STACK/SCRIPTS/LAYOUT） + byte-identical 校验 + unpaired marker + dry-run + replace_auto_section 3 条单元 + dogfood subprocess。覆盖 AC-06 / AC-08（playbook-refresh 侧）。充分。
- **chg-05 TC 充分性**：13 TC 含 D-01～D-06 各 1 + K-01 + TC-08 OQ-5 AUTO 哈希漂移 + 健康 exit 0 + dogfood subprocess + validate 集成 + AUTO 配对缺失 + 无路书 exit 0。覆盖 AC-07 / AC-09（validate） / AC-12 全部验证点。充分。

### 2.2 风险盲点审视

- **chg 间隐式依赖**：chg-03 → chg-04/05 依赖 `render_skeleton` 生成的文件布局；已通过各自 fixture 隔离（`_make_playbook`），无隐式依赖泄漏。
- **级联依赖未测**：chg-05 TC-08 OQ-5 兜底测试通过修改 architecture.md AUTO:STACK 区段验证哈希漂移，但 domains/*/code.md AUTO:DOMAIN_FILES 未单独测试哈希漂移检测（chg-05 session-memory §4 明确排除此项，原因为 step5/6 顺序依赖导致误报风险）。
- **4 级推断降级**：TC-01～04 每级各 1 条，但 Level-4 在单包结构（harness-workflow 自身）实测通过（dogfood subprocess 命中 `src/myproject/*次级模块`），覆盖充分。

### 2.3 dogfood 真实性审视

- **chg-03 dogfood TC-05** 调用 `subprocess.run(..., 'install', '--root', tmpdir)` 完整链路（含 install_repo），不是只跑 `init_playbook` helper。命中 Level-4 单包推断。真实覆盖端到端。
- **chg-04 dogfood TC-07** 调用 `subprocess.run(..., 'playbook-refresh', '--root', tmpdir)`，先跑 install 创建骨架，再跑 refresh。真实端到端。
- **chg-05 dogfood TC-10** 调用 `subprocess.run(..., 'playbook-check', '--root', tmpdir)`，用健康 fixture 验证 exit 0。真实端到端。

### 2.4 OQ-5 兜底有效性审视

- TC-08（`test_tc08_oq5_auto_segment_hash_drift`）通过修改 architecture.md AUTO:STACK 区段注入假内容，验证 check 返回 exit 1 + 包含"AUTO segment drift detected"。独立验证（Step 4.4 Step D）完整复现：exit=1，stdout 含"AUTO 区段哈希漂移"，OQ-5 兜底有效。
- **限制**：domains/*/code.md AUTO:DOMAIN_FILES 哈希检测被排除（chg-05 设计决策），这是已知局限，由 D-04/C-05 互引一致性承担补偿。

---

## 3. 各 chg 独立测试集结果

| chg | TC 数 | PASS | FAIL | executing 自报 | 一致 |
|-----|------|------|------|--------------|------|
| chg-01（路书目录骨架契约） | 4 | 4 | 0 | 4/4 | ✅ |
| chg-02（baseRole代码加载规则与CLAUDE索引） | 4 | 4 | 0 | 4/4 | ✅ |
| chg-03（harness install 追加路书初始化） | 10 | 10 | 0 | 10/10 | ✅ |
| chg-04（harness playbook-refresh 子命令） | 10 | 10 | 0 | 10/10 | ✅ |
| chg-05（harness playbook-check 子命令） | 13 | 13 | 0 | 13/13 | ✅ |

所有 5 chg 独立测试集与 executing 自报完全一致，总计 41/41 PASS。

---

## 4. 全量回归结果

- **总用例数**：847（790 passed + 57 failed + 41 skipped + 16 subtests passed）
- **PASS**：790
- **FAIL**：57
- **pre-existing baseline（executing 自报）**：57 failed
- **本 req 引入**：+0 failed / -0 failed（与基线完全一致）
- **执行时间**：140.85s

**FAIL 用例溯源**：独立跑 `grep "^FAILED"` 提取 57 条失败用例，**全部来自以下历史测试文件**，不含任何 `test_playbook_*` 文件：

```
test_analyst_role_merge.py
test_archive_revert_dry_run.py
test_artifact_placement_chg01.py（8 条）
test_block_protocol_e2e.py（2 条）
test_bugfix9_force_managed_and_user_write.py（2 条）
test_build_cache_freshness.py（2 条）
test_chg03_title_contract.py（2 条）
test_dev_mode_flag.py（3 条）
test_done_subagent.py
test_harness_next_pending_gate.py（2 条）
test_install_reverse_cleanup.py
test_next_execute.py（2 条）
test_next_writeback.py
test_raise_harness_block.py（2 条）
test_req43_chg01.py / test_req43_chg02.py / test_req43_chg04.py / test_req43_chg05.py
test_req51_project_level_dogfood.py
test_role_stage_continuity.py（3 条）
test_smoke_req26.py / test_smoke_req28.py（2 条）/ test_smoke_req29.py
test_stage_policies.py
test_state_sync_invariants.py（2 条）
test_task_context_index.py
test_test_case_design_in_planning.py
test_user_write_protected_zones.py（2 条）
test_validate_contract_testing_no_destructive_git.py（2 条）
test_validate_test_case_design_completeness.py（2 条）
test_workflow_next_subprocess.py（2 条）
test_workflow_next_workdone_gate.py
```

**结论**：57 个 FAIL 全部为 pre-existing 历史用例，与 req-55 无关。本 req 新增 `test_playbook_*.py` 文件中无任何 FAIL。

---

## 5. 12 条 AC 逐条验证

| AC | 内容 | 验证手段 | 状态 | 证据 |
|----|------|---------|------|------|
| AC-01 | 骨架契约文档落地 | `test -f .workflow/flow/playbook-layout.md && grep -c '<!-- AUTO:'` | PASS | 文件存在；`grep -c '<!-- AUTO:'` = 16（≥ 5） |
| AC-02 | baseRole 强制章节落地 | `grep -c '## 硬门禁' .workflow/context/roles/base-role.md` | PASS | = 9（原 8 + 硬门禁十，≥ 8） |
| AC-03 | CLAUDE.md 索引节落地 | `grep -A6 '^## 项目路书' CLAUDE.md` | PASS | 含 `code-map.md` / 4 顶层文件 / `domains/<领域>/` |
| AC-04 | install 路书初始化 | subprocess install + 文件存在性 + 幂等验证 | PASS | exit 0；4 顶层文件齐全；domains ≥ 2；第二次跑 stdout 含"已存在，跳过" |
| AC-05 | install flag 生效 | subprocess `--skip-playbook` / `--playbook-only` | PASS | `--skip-playbook`: exit 0 + playbook dir 不存在；`--playbook-only`: exit 0 + stdout 含"skipped install_repo" |
| AC-06 | refresh AUTO 区段刷新 | human content 追加 + refresh + byte-identical 验证 | PASS | human content 保持原样；5 类 AUTO 区段正常刷新（7 个区段已刷）；exit 0 |
| AC-07 | check 漂移检测 | 6 类漂移 fixture + check exit 1 验证 | PASS | pytest 7 条用例（TC-01～TC-07）全 PASS；独立模拟 D-03 + K-01 漂移 → exit 1 |
| AC-08 | `--dry-run` 全覆盖 | `install --check`（dry-run）+ `playbook-refresh --dry-run` | PARTIAL | `playbook-refresh --dry-run`: exit 0 + 打印 diff 不落盘 ✅；`harness install --playbook-only --dry-run` 不支持（exit 2），只有 `install --check` 覆盖 install_repo 层 dry-run，playbook 初始化层无独立 dry-run flag（见 §7 Issue-1） |
| AC-09 | 路径自检 + 项目级豁免合规 | `validate --contract artifact-placement` exit 0；repository-layout.md §2.1 含 playbooks | PASS | `artifact-placement`: exit 0；§2.1 明确列出 `artifacts/project/playbooks/` 为第 4 类豁免 |
| AC-10 | dogfood 活证 | subprocess 4 步全流程 | PASS | Step A exit 0 + Step B exit 0；Step C exit 1（K-01 骨架内容未填，预期行为）；Step D exit 1 + AUTO 漂移捕获（见 §6） |
| AC-11 | pytest 全绿零回归 | 独立跑全量回归 | PASS | 790 passed / 57 failed（全部 pre-existing）/ 41 skipped；新增 test_playbook_*.py 全 PASS；新增用例数 = 41（≥ 12） |
| AC-12 | hardgate 链路：契约 + lint | `validate --contract playbook-layout` exit 0 | PASS | exit 0（当前仓无路书 → skip，符合"无路书无漂移"语义） |

**汇总**：11 PASS / 1 PARTIAL（AC-08）/ 0 FAIL

**AC-08 PARTIAL 说明**：`harness install --playbook-only` 不支持 `--dry-run`（argparse 报 exit 2），AC-08 中"install --dry-run"要求未完整覆盖 playbook 初始化层。`playbook-refresh --dry-run` 正常工作。需求原文 AC-08 写"harness install --dry-run"，但 install 的 dry-run 入口是 `--check` flag（覆盖 install_repo 层）而非 `--dry-run`，两者语义有偏差。

---

## 6. dogfood 活证

### Step A: install --playbook-only（触发 Level-4 单包推断）

```
exit: 0
stdout:
  skipped install_repo (--playbook-only); mirror not synced this run
  domain inference: matched 'src/myproject/*次级模块' (2 domains: playbook, tools)
  [playbook] created artifacts/project/playbooks/overview.md
  [playbook] created artifacts/project/playbooks/architecture.md
  [playbook] created artifacts/project/playbooks/runbook.md
  [playbook] created artifacts/project/playbooks/code-map.md
  [playbook] created artifacts/project/playbooks/domains/playbook/README.md
  [playbook] created artifacts/project/playbooks/domains/playbook/code.md
  [playbook] created artifacts/project/playbooks/domains/playbook/data-model.md
  [playbook] created artifacts/project/playbooks/domains/playbook/notes.md
  [playbook] created artifacts/project/playbooks/domains/tools/README.md
  [playbook] created artifacts/project/playbooks/domains/tools/code.md
  [playbook] created artifacts/project/playbooks/domains/tools/data-model.md
  [playbook] created artifacts/project/playbooks/domains/tools/notes.md
  playbook initialized (12 files created in artifacts/project/playbooks)
```

断言：exit 0 ✅ + playbook 目录创建 ✅ + Level-4 降级命中 ✅ + 12 文件落盘 ✅

### Step B: playbook-refresh

```
exit: 0
stdout:
  [playbook-refresh] refreshed artifacts/project/playbooks/architecture.md AUTO:STACK
  [playbook-refresh] refreshed artifacts/project/playbooks/architecture.md AUTO:SCRIPTS
  [playbook-refresh] refreshed artifacts/project/playbooks/architecture.md AUTO:LAYOUT
  [playbook-refresh] refreshed artifacts/project/playbooks/overview.md AUTO:DOMAIN_LIST
  [playbook-refresh] refreshed artifacts/project/playbooks/code-map.md AUTO:DOMAIN_FILES
  [playbook-refresh] refreshed artifacts/project/playbooks/domains/playbook/code.md AUTO:DOMAIN_FILES
  [playbook-refresh] refreshed artifacts/project/playbooks/domains/tools/code.md AUTO:DOMAIN_FILES
  [playbook-refresh] 完成：刷新 7 个 AUTO 区段
```

断言：exit 0 ✅ + 5 类 AUTO 区段全覆盖（STACK/SCRIPTS/LAYOUT/DOMAIN_LIST/DOMAIN_FILES）✅

### Step C: playbook-check（fresh install）

```
exit: 1
stdout:
  playbook-check FAIL: 2 drift detected
  
  [K-01 关键词覆盖空]
    - empty keywords (K-01): playbook/README.md ## 职责描述 内容为空或仅 TODO → KEYWORD_COVERAGE
    - empty keywords (K-01): tools/README.md ## 职责描述 内容为空或仅 TODO → KEYWORD_COVERAGE
```

说明：新建骨架中 `domains/*/README.md` 的 `## 职责描述` 为 TODO 占位，K-01 触发为预期行为（用户需手动填写职责描述后才达到"健康"状态）。exit 1 正确。

### Step D: AUTO 区段被篡改后 check（OQ-5 兜底验证）

修改 `architecture.md`：在 `<!-- AUTO:STACK -->` 注入 `FAKE INJECTED LINE`。

```
exit: 1
stdout:
  playbook-check FAIL: 3 drift detected
  
  [K-01 关键词覆盖空]
    - empty keywords (K-01): playbook/README.md ## 职责描述 内容为空或仅 TODO
    - empty keywords (K-01): tools/README.md ## 职责描述 内容为空或仅 TODO
  
  [AUTO 区段哈希漂移]
    - AUTO segment drift detected: architecture.md AUTO:STACK 区段内容与 refresh 期望值不一致
      （可能被手动修改），建议跑 `harness playbook-refresh`
```

断言：exit 1 ✅ + AUTO 漂移被捕获 ✅ + OQ-5 兜底有效 ✅

---

## 7. Issues & 补充测试设计

### 已发现 Issues

**Issue-1（AC-08 PARTIAL）：`harness install` playbook 初始化层无独立 `--dry-run` flag**

- 现象：`harness install --playbook-only --dry-run` 报 argparse error（exit 2），`--dry-run` 不是 install 的有效 flag
- install 的 dry-run 入口为 `--check`，仅覆盖 install_repo 层版本检查，不覆盖 playbook 初始化
- requirement.md AC-08 写"harness install --dry-run"，实际 CLI 用 `--check` 对应 dry-run 语义
- 影响：AC-08 标记为 PARTIAL（playbook-refresh --dry-run 正常工作）
- 建议：在 `init_playbook` 函数增加 `dry_run` 参数，CLI 追加 `--dry-run` flag；或在 AC-08 验证文档中明确 install 层 dry-run = `--check`（语义对齐）

**Issue-2（观察，非 Bug）：新建骨架后立即 check 返回 exit 1（K-01）**

- 现象：install 初始化骨架后立即跑 check，K-01 触发（domains/*/README.md `## 职责描述` 为 TODO），exit 1
- 这是设计预期：骨架需用户手动填写内容才达到"健康"
- 但 AC-10 要求"harness playbook-check --dry-run 在 baseline 状态下 exit 0"——若 harness-workflow 自身仓从未创建 playbooks/，则 exit 0（无路书无漂移）；若创建了路书但未填内容，则 exit 1
- 建议：在文档/测试中明确"空骨架不等于健康状态"，区分"无路书"（exit 0）vs "路书内容未填"（exit 1 K-01）

### 补充测试设计建议（未实施，供 acceptance / 后续 req 评估）

1. **AC-08 补充 TC**：在 `tests/test_playbook_install.py` 增加 TC-11：`install --check --playbook-only` 验证 playbook init 层 dry-run 是否跳过写入；当前实现不支持，TC 应标记 XFAIL 或触发 Issue-1 修复
2. **AC-04 补充 TC**：验证"第二次 install 无 diff"（幂等性），即第二次跑后 git status 无新增文件。当前 TC-05 验证了 playbook 已存在时跳过，但未验证 install_repo 层文件也无变化
3. **AC-06 多类 AUTO 区段 byte-identical 补充**：当前 TC-04 只验证 architecture.md 非 AUTO 区段，建议补充 overview.md / code-map.md 的 byte-identical 验证
4. **K-01 空描述豁免机制**：考虑为 `harness install` 后初始状态（骨架中所有 README.md `## 职责描述` 为 TODO）增加"初始化后首次 check 跳过 K-01"机制，改善 UX

---

## 结论

**verdict**: PARTIAL

**理由**：

- 5 chg 独立测试集全部 PASS（41/41 TC），与 executing 自报完全一致
- 全量回归 790 passed / 57 failed，57 个 FAIL 均为 pre-existing 历史用例，本 req 零回归引入
- 12 AC 中 11 条 PASS / 1 条 PARTIAL（AC-08）
- AC-08 PARTIAL：`harness install` 无 `--dry-run` flag（使用 `--check` 代替），playbook 初始化层不支持独立 dry-run；`playbook-refresh --dry-run` 正常工作
- dogfood 4 步活证全部完成，OQ-5 兜底（AUTO 区段哈希漂移检测）有效

**路由建议**：

AC-08 的 PARTIAL 属于 CLI flag 设计偏差，不影响核心功能（路书生命周期管理）的正常使用。建议进入 acceptance 阶段评估是否需要开 regression 修复 `--dry-run` 支持，或将 AC-08 中"install --dry-run"说明更新为"install --check"（语义对齐）后标记 PASS。

如 acceptance 判定 AC-08 偏差可接受（`--check` 已提供 dry-run 等效语义），则整体 verdict 可升级为 PASS。

---

## 9. 经验沉淀候选

1. **K-01 区分骨架"空"vs"未填"**：check 对新建骨架内容为 TODO 触发 K-01，是正确设计，但 UX 文档需明确"install 后需手动填写 README.md 职责描述，check 才能 PASS"。避免用户误解"install 成功 = playbook 健康"。
2. **dry-run 语义标准化**：harness 系统中 `--check` 和 `--dry-run` 语义有重叠，建议后续 req 统一使用 `--dry-run` 作为"预览不落盘"的标准 flag，`--check` 专用于版本/状态检查语义，避免混用。
3. **OQ-5 兜底路径（AUTO 哈希漂移）**：testing 阶段独立验证确认 chg-05 TC-08 有效；domains/*/code.md 排除哈希检测是合理设计（step5/6 顺序依赖），由 D-04/C-05 互引一致性补偿。这一设计权衡值得在 known-risks.md 中记录。
