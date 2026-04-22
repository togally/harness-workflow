# Acceptance Report — bugfix-3 pipx 重装后新项目 install/update 生成数据不正确

> 验收官（acceptance 角色，Subagent-L1）独立核查，不信任 executing 简报，所有结论由独立复跑 / 独立烟测 / 独立 stash-diff 得出。
> 日期：2026-04-20  
> 工件目录：`artifacts/main/bugfixes/bugfix-3-pipx-重装后新项目-install-update-生成数据不正确/`

---

## 1. Validation Criteria 逐条核查（对照 bugfix.md）

| # | Validation Criteria（原文） | 核查方式 | 结论 | 证据 |
|---|---------------------------|---------|------|------|
| 1 | `PYTHONPATH=src python3 -m pytest tests/test_workflow_helpers_update_idempotent.py -v` → 2 passed | 独立复跑 | **PASS** | 输出：`2 passed in 0.75s`；两条用例 `test_experience_index_md_not_cycled_into_legacy_cleanup` / `test_unregistered_stale_scaffold_file_is_adopted_by_update` 均 PASSED |
| 2 | `PYTHONPATH=src python3 -m pytest -x --no-header -q` → 零新增回归（容忍 pre-existing failure） | 独立复跑全量 + `git stash` 回到 HEAD 基线复跑唯一 failure 确认其 pre-existing | **PASS** | 应用 diff 后：`146 passed / 50 skipped / 1 failed`；唯一 failure 为 `tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`（期望 `artifacts/main/requirements/req-29-批量建议合集（2条）` 目录存在）。`git stash` 回到 HEAD baseline 独立复跑同一 test → 同样 FAIL（与本 bugfix-3 无关；根因是 req-29 归档 slug 已被清洗为英文但该测试代码仍硬编码旧中文 slug，属于 req-29/30 遗留），故本 bugfix-3 零新增回归。 |
| 3 | 烟测：`/tmp/petmall-bugfix3-smoke` 副本上跑 `update_repo`，stdout 不再出现 `skipped modified .workflow/context/roles/*.md` 或 `archived legacy .workflow/context/experience/index.md ...`；`legacy-cleanup/.workflow/context/experience/` 下不再新增 `index.md-N` | 独立烟测 `/tmp/petmall-bugfix3-acceptance-smoke/` 连续跑两次 `harness update` | **PASS** | Run1：32 条 `adopted `，0 条 `skipped modified`，0 条 `archived legacy`；Run2（幂等性）：0 条 `adopted`，0 条 `archived legacy`，3 条 `skipped modified`（`.workflow/context/experience/index.md` / `.workflow/state/runtime.yaml` / `.codex/skills/harness/SKILL.md`，均**非** `context/roles/*.md`，属 executing 已上报的衍生问题范围）。`legacy-cleanup/.workflow/context/experience/` 下仅保留 baseline `index.md` + `index.md-2`（副本复制时即存在，历史堆积），**未新增** `index.md-3`。循环归档已终止。 |
| 4 | 对人文档 `changes/实施说明.md` 已产出（开发者角色契约） | 只读核查 | **PASS（内容）** / **FAIL（契约路径）** | 文件存在 `changes/实施说明.md`（23 行，字段全）。但 `validate --human-docs --bugfix` 期望 bugfix **根目录** `实施说明.md`，当前工件放到 `changes/` 子目录——validator 判为缺失。**列入未达项上报**，但 bugfix.md 原文只要求"产出"未规定路径，开发者产物内容合规。 |
| 5 | session-memory.md 追加 executing 阶段条目（context_chain 延长 + 步骤 ✅ + 经验候选 ≥ 1 条） | 只读核查 | **PASS** | `session-memory.md` 第 142-207 行为 executing 阶段条目，context_chain 从 L0 延长到 L1 executing；Step 0~D 均 ✅；经验候选 2 条（"managed-state 三态判据" + "LEGACY_CLEANUP_TARGETS 与活跃再生成器互斥"）≥ 1，字段齐全。 |
| 6 | `.workflow/state/action-log.md` 顶部追加 executing 阶段条目 | 只读核查 | **PASS** | 已确认顶部存在 bugfix-3 executing 阶段条目（未逐行摘录，仅结构检查）。 |

**小计**：6/6 passed（条款 4 因 validator 路径约定不匹配算 conditional pass，见第 5 节）

---

## 2. 独立复跑结果

### 2.1 红用例（bugfix.md Validation Criteria #1）

```
PYTHONPATH=src python3 -m pytest tests/test_workflow_helpers_update_idempotent.py -v
```

结果：
```
tests/test_workflow_helpers_update_idempotent.py::UpdateIdempotencyTest::test_experience_index_md_not_cycled_into_legacy_cleanup PASSED [ 50%]
tests/test_workflow_helpers_update_idempotent.py::UpdateIdempotencyTest::test_unregistered_stale_scaffold_file_is_adopted_by_update PASSED [100%]
============================== 2 passed in 0.75s ===============================
```

### 2.2 全量回归 + pre-existing failure 独立认证

```
PYTHONPATH=src python3 -m pytest -q --no-header
```

结果：`1 failed, 146 passed, 50 skipped in 28.40s`  
失败：`tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`

独立 stash 验证：
```
git stash push -u src/harness_workflow/workflow_helpers.py tests/test_workflow_helpers_update_idempotent.py
PYTHONPATH=src python3 -m pytest tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29 -v
# → 1 failed (HEAD baseline 下同样 FAIL)
git stash pop
```

**结论**：failure 为 pre-existing（root cause：req-29 归档 slug 从"批量建议合集（2条）"清洗为 "req-29"，但 `test_smoke_req29.py` 测试代码仍硬编码旧中文 slug），与本 bugfix-3 修复无关。**零新增回归**。

### 2.3 烟测（bugfix.md Validation Criteria #3）

基线准备：
```
rm -rf /tmp/petmall-bugfix3-acceptance-smoke/
cp -R /Users/jiazhiwei/claudeProject/PetMallPlatform /tmp/petmall-bugfix3-acceptance-smoke/
# 基线: backup/legacy-cleanup/.workflow/context/experience/ 已有 index.md + index.md-2 (历史堆积)
```

Run1（`cd /tmp/petmall-bugfix3-acceptance-smoke && harness update`）：
- `adopted `：32 条
- `skipped modified`：0 条
- `archived legacy`：0 条
- `skipped modified .workflow/context/roles/*.md`：**0 条** ✓（根因 A 修复生效）
- `archived legacy .workflow/context/experience/index.md`：**0 条** ✓（根因 B 修复生效）

Run2（幂等性验证）：
- `adopted `：0 条（已稳态）
- `archived legacy`：0 条
- `skipped modified`：3 条（`.workflow/context/experience/index.md` / `.workflow/state/runtime.yaml` / `.codex/skills/harness/SKILL.md`）—— 均**非** `context/roles/*.md`，与 executing 衍生问题条目完全一致（多生成器共享文件语义冲突，pre-existing，不在 bugfix-3 范围）

`legacy-cleanup/.workflow/context/experience/` 副本检查：
- 初始（副本源）：`index.md`、`index.md-2`（两份历史副本）
- Run2 之后：**仍为** `index.md`、`index.md-2`（无 `index.md-3` 新增）
- 即：连续两次 update 不再产生递增副本，循环归档已终止 ✓

清理：已 `rm -rf /tmp/petmall-bugfix3-acceptance-smoke/`（见第 7 节）。

---

## 3. 边界检查

### 3.1 代码变更范围

```
git diff --stat HEAD
 .harness/feedback.jsonl                  |  3 +++
 .workflow/state/runtime.yaml             |  9 +++++----
 .workflow/tools/index/missing-log.yaml   | 12 +++++++++++-
 src/harness_workflow/workflow_helpers.py | 17 ++++++++++++++++-
```

- **代码层**：确认只修改 `src/harness_workflow/workflow_helpers.py`（LEGACY_CLEANUP_TARGETS 移除一行 + `_sync_requirement_workflow_managed_files` 新增 adopt 分支），符合 bugfix.md Fix Scope"将改"边界 ✓
- **状态层**：`runtime.yaml` / `missing-log.yaml` / `feedback.jsonl` 属工作流运行时元数据，executing 阶段正常副作用（stage 推进 / toolsManager 未命中记录 / hook 反馈），**未越界**
- **不改清单核对**：
  - `tests/test_workflow_helpers_update_idempotent.py`（git status 显示 Untracked，即 testing 阶段新增但未被 commit；`git diff HEAD` 下不出现，符合 bugfix.md"不改红用例"口径）✓
  - `src/harness_workflow/assets/scaffold_v2/`：`git diff --stat HEAD` 中不出现 ✓
  - 目标项目 `/Users/jiazhiwei/claudeProject/PetMallPlatform`：烟测用的是 `/tmp/` 副本，未触碰原始目标项目 ✓
  - `_refresh_managed_state` / `cleanup_legacy_workflow_artifacts` / `_unique_backup_destination` 语义：未修改（仅改常量 + 新增分支）✓

### 3.2 验收阶段只读边界

本 subagent 只读核查 + 只写文档（acceptance-report.md / 验收摘要.md / session-memory 追加 / action-log 追加），未修改任何代码、测试、scaffold、目标项目、runtime.yaml stage ✓

---

## 4. 状态漂移检查（acceptance → done 流转前硬门禁）

| 文件 | 字段 | 值 | 一致性 |
|------|------|-----|--------|
| `.workflow/state/runtime.yaml` | `stage` | `acceptance` | ✓ |
| `.workflow/state/runtime.yaml` | `operation_target` | `bugfix-3` | ✓ |
| `.workflow/state/runtime.yaml` | `current_requirement` | `bugfix-3` | ✓ |
| `.workflow/state/bugfixes/bugfix-3-....yaml` | `stage` | `acceptance` | ✓ |
| `.workflow/state/bugfixes/bugfix-3-....yaml` | `status` | `active` | ✓ |

**无状态漂移**，acceptance → done 推进前无需修复。

---

## 5. 对人文档硬门禁（harness validate --human-docs --bugfix bugfix-3）

实际输出：
```
[ ] regression           回归简报.md  →  artifacts/.../bugfix-3-.../回归简报.md
[ ] executing            实施说明.md  →  artifacts/.../bugfix-3-.../实施说明.md
[ ] testing              测试结论.md  →  artifacts/.../bugfix-3-.../测试结论.md
[ ] acceptance           验收摘要.md  →  artifacts/.../bugfix-3-.../验收摘要.md
[ ] done                 交付总结.md  →  artifacts/.../bugfix-3-.../交付总结.md

Summary: 0/5 present, 5 pending/invalid.
```

briefing 预期："至少 4/5（回归简报/测试简报/实施说明/验收摘要；交付总结在 done 阶段）"；实际 **0/5**。

原因分析（事实核查，以工具输出为准，对照 `src/harness_workflow/validate_human_docs.py` L64-L69 `BUGFIX_LEVEL_DOCS` 契约）：

| 期望路径（validator） | 实际工件位置 | 差异 |
|---------------------|-------------|------|
| `bugfix-3-.../回归简报.md` | `bugfix-3-.../regression/回归简报.md` | 路径偏（子目录） |
| `bugfix-3-.../实施说明.md` | `bugfix-3-.../changes/实施说明.md` | 路径偏（子目录） |
| `bugfix-3-.../测试结论.md` | `bugfix-3-.../testing/测试简报.md` | 路径 + 文件名都偏（`简报` vs `结论`） |
| `bugfix-3-.../验收摘要.md` | 本次新增（见产出 B） | 本阶段产出时会落在根目录，合规 |
| `bugfix-3-.../交付总结.md` | 尚未产出（done 阶段） | 预期 done 前不产出 |

**结论**：对人文档**内容已全部产出且字段齐全**（逐文件检查过），但**落盘路径+命名不符契约**。validator 判为 0/5 是真实的硬门禁违规。

执行官按 acceptance.md Step 1 的要求："未达项必须写入后续产出的 `验收摘要.md`，并停下来把 subagent 交回 executing 角色补齐对人文档"——此条**必须作为未达项上报主 agent**（本 subagent 不自行修复，见 briefing"不得自行修复发现的问题"）。

---

## 6. 衍生问题清单（上报主 agent，不在本阶段处理）

### 6.1 执行官衍生问题（已在 `changes/实施说明.md` 和 session-memory 中登记）

**D1：第二次 update 仍有 3 条 `skipped modified`（多生成器共享文件 hash 竞争）**
- 范围：`.workflow/context/experience/index.md` / `.workflow/state/runtime.yaml` / `.codex/skills/harness/SKILL.md`
- 根因：`_sync_...` 写完 hash 后，同一次 update 内 `_refresh_experience_index` / `save_requirement_runtime` / `install_local_skills` 再改这些文件
- 性质：pre-existing（HEAD baseline 下也存在），**不属 bugfix-3 根因 A/B**，烟测已独立验证
- 建议：**done 阶段由主 agent 起 sug 跟踪**"update 幂等性二阶段：多生成器共享文件的 hash 竞争消除"

**D2：`adopt` 判据对"用户自建同路径但从未登记的文件"会误覆盖**
- 范围：scaffold_v2 暴露的文件路径下，用户手动创建同名自定义文件
- 现状：scaffold_v2 下全是受管模板，真实使用场景概率极低
- 建议：留待未来反例出现时扩展白名单，当前不处理

### 6.2 验收官本阶段新发现的衍生问题

**D3：对人文档落盘路径与 validator 契约不一致（硬门禁失败）**
- 范围：`regression/回归简报.md` / `changes/实施说明.md` / `testing/测试简报.md` 三份文件
- 根因：executing / testing / regression 阶段按直觉落到子目录（`changes/` / `testing/` / `regression/`），且 testing 阶段将 `测试结论.md` 写成了 `测试简报.md`；`validate_human_docs.py#BUGFIX_LEVEL_DOCS` 明确要求这三份文件落在 bugfix **根目录** 且 testing 阶段的文件名是 `测试结论.md`
- 影响：`harness validate --human-docs --bugfix bugfix-3` 判 0/5，acceptance → done 流转前的硬门禁会拦截
- 建议：**条件通过（conditional pass）**，交主 agent 在推进 done 之前，交回 executing/testing 角色：
  1. 将三份文件 **移动**（mv）到 bugfix 根目录
  2. `testing/测试简报.md` → `测试结论.md` 改名
  3. 原 `regression/` `changes/` `testing/` 子目录下的 agent 过程产物（`diagnosis.md` / `required-inputs.md` / `测试简报.md` / `实施说明.md` 等 agent 过程产物/副本）按 stage-role.md 契约 1"双轨不迁移"保留原位
  4. 重跑 `harness validate --human-docs --bugfix bugfix-3`，期望至少 4/5（`交付总结.md` 留到 done）

**D4：pre-existing test failure `test_smoke_req29`**
- 非本 bugfix 范围，但影响 `pytest -q --no-header` 全量绿；建议在独立回归/req 中跟踪（可能已有 sug）

---

## 7. 验收清理

- `/tmp/petmall-bugfix3-acceptance-smoke/` 已 `rm -rf` 清理（在第 2.3 节烟测完成后执行）
- 本 subagent 未 commit / push，未执行 `harness next` / `harness ff`

---

## 8. 最终结论

**acceptance conditional pass**

理由：
- bugfix.md 明确列出的 6 项 Validation Criteria 全部通过（#1~#6 实质均 PASS，独立复跑与独立烟测证据齐全）
- 但本 bugfix 工件违反 **acceptance.md Step 1 / stage-role.md 契约 2 / validate_human_docs.py BUGFIX_LEVEL_DOCS 的"对人文档落盘路径"硬门禁**（0/5 validate），需要由 executing/testing 角色补齐路径移动 + testing 文件改名，之后重跑 validate 应达 ≥4/5 方可进入 done
- 代码修复实质有效（独立烟测证明根因 A/B 已终结），无新增回归，状态无漂移，衍生问题已全部登记不遗漏
- 本阶段不自行修复（遵守 briefing 执行规则），将 D3 作为阻塞项明确上报主 agent

**建议下一步**：
1. 主 agent 接收本报告，安排 executing/testing subagent 完成 D3 修复（mv 3 份文件到根目录 + 文件改名）
2. 重跑 `harness validate --human-docs --bugfix bugfix-3` 应达 4/5（`交付总结.md` 待 done）
3. 重跑本 acceptance 条款 6（validate 复核）后，acceptance 转为 **pass**，推进到 done
4. done 阶段时起 sug 跟踪 D1（多生成器共享文件幂等性二阶段）

---

## 9. 经验候选（上报主 agent，由 done 阶段决定是否沉淀到 `context/experience/roles/executing.md`）

**候选一：bugfix 对人文档必须直落 bugfix 根目录，子目录是 agent 过程产物专用**
- 场景：executing/testing/regression 阶段直觉把"对人文档"和 "agent 过程产物（diagnosis.md / required-inputs.md / test-evidence.md）" 放在一起（`regression/` / `changes/` / `testing/` 子目录）
- 经验：`stage-role.md` 契约 2 + `validate_human_docs.py#BUGFIX_LEVEL_DOCS` 明确要求 bugfix 级对人文档（`回归简报.md` / `实施说明.md` / `测试结论.md` / `验收摘要.md` / `交付总结.md`）直落 bugfix 根目录，子目录只放 agent 过程产物；命名使用契约表固定名（testing = `测试结论.md` 而非 `测试简报.md`）
- 预防机制：每个 stage 角色产出对人文档后，应当场跑一次 `harness validate --human-docs --bugfix <id>` 自检，不要留到 acceptance 阶段才发现
- 来源：bugfix-3 acceptance 阶段

**候选二：acceptance 独立复跑必须覆盖 pre-existing failure 的 HEAD baseline 验证**
- 场景：executing 简报声称某 test failure 是 pre-existing，acceptance 不得直接信
- 经验：`git stash` 应用 diff，在 HEAD baseline 下独立复跑同一 failing test，确认同样 FAIL 才算 pre-existing。这也是对 `.workflow/context/experience/roles/acceptance.md` 经验一"以工具输出为准"的延展：凡涉及"是否属本 bugfix 新增回归"的判定，必须有 stash-diff 证据
- 来源：bugfix-3 acceptance 阶段（stash 验证 `test_smoke_req29`）

---

## 10. 上下文消耗评估

- 本 subagent 累计 Read 约 18 个文件（多数 ≤ 200 行）、Bash 约 15 次（pytest x4 + smoke x2 + git stash x2 + ls/grep/diff 若干）、Edit/Write 2 次（本报告 + 验收摘要）
- 预估上下文占比 ~50-55%（未到 70% 阈值），无需 `/compact`
- 交接给主 agent 后，主 agent 处理 D3 修复应新开 executing subagent，不在本层继续堆积
