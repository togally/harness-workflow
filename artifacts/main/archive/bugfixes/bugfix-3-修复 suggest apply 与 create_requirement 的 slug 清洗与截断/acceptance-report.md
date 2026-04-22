# Acceptance Report: bugfix-3 修复 suggest apply 与 create_requirement 的 slug 清洗与截断

- 角色：验收官（Subagent-L1, acceptance 角色）
- 验收时间：2026-04-20
- runtime.yaml：`current_requirement=bugfix-3`, `stage=acceptance`, `stage_entered_at=2026-04-20T06:08:19Z`
- 流程模式：模式 B（Bugfix 快速流程 `regression → executing → testing → acceptance → done`）

---

## 0. 硬门禁：对人文档校验（AC-09）

执行命令：

```
harness validate --human-docs --bugfix bugfix-3
```

工具实际输出（Summary 以工具为准）：

```
[ ] regression           回归简报.md  →  .../回归简报.md
[✓] executing            实施说明.md  →  .../实施说明.md
[✓] testing              测试结论.md  →  .../测试结论.md
[ ] acceptance           验收摘要.md  →  .../验收摘要.md
[ ] done                 交付总结.md  →  .../交付总结.md

Summary: 2/5 present, 3 pending/invalid.
```

解读：

- `执行阶段（实施说明.md）` + `测试阶段（测试结论.md）`：✓ 已落盘。
- `验收摘要.md`：当前阶段本 subagent 职责，将与本报告同批产出，提交后该项应翻绿。
- `交付总结.md`：done 阶段产出，当前 stage=acceptance 下未落盘为正常。
- `回归简报.md`：**未产出**。bugfix-3 `regression/` 子目录仅有 `diagnosis.md` + `required-inputs.md`，无对人文档《回归简报.md》。属于 regression 阶段对人文档契约（stage-role.md 契约 3）未执行，是一项**流转前建议补齐的历史遗留**。

硬门禁语义：stage-role.md 经验文件指出硬门禁应以工具 Summary 的"All human docs landed."为最终判据。当前 Summary 为 "2/5 present"（非 All landed），但：

1. 唯一当前 stage 在本 subagent 职责内的缺失（验收摘要.md）将在本批次产出 → acceptance 阶段自洽。
2. done 阶段的 `交付总结.md` 不属于 acceptance 阶段硬门禁内容。
3. `回归简报.md` 缺失是 regression 阶段遗留，非本阶段制造，也不阻断本阶段验收判定，但需在验收摘要中显式列出作为"流转前补齐项"。

结论：**不自动回滚到 executing**；本 subagent 完成验收摘要后，主 agent 决策是否把 regression 阶段的《回归简报.md》作为流转到 done 前的补丁任务回派（建议派 regression 角色补出即可，无需回退 stage）。

---

## 1. Validation Criteria 逐条核查（bugfix.md 5 条 + 测试工程师扩展 1 条 = 6 条）

bugfix.md `# Validation Criteria` 原文 5 条；testing 阶段 test-evidence.md 额外列出了"新增 3+ 条单测全绿"作为第 6 条，与 bugfix.md 第 5 条之后的"3+ 单测"项对应。本报告按 test-evidence 的 6 条口径核查。

| # | AC 原文 | 判定 | 证据定位 |
|---|---------|------|---------|
| 1 | `harness requirement "含/的 标题"` 只产出单级 `req-NN-<slug>/`，state yaml 同理 | [x] 满足 | 代码：`workflow_helpers.py` L3301-3302 `slug_part = _path_slug(requirement_title); dir_name = f"{req_num_id}-{slug_part}" if slug_part else req_num_id` + L3317 state yaml 路径复用 `dir_name`。单测：`tests/test_slug_paths.py::CreateRequirementSlugTest::test_slash_in_title_does_not_create_nested_dir`（断言 `children==1`、`/` not in dir_name、state yaml 无嵌套子目录）。E2E：`/tmp/harness-bugfix3-e2e-20260420-115447/` 场景 2 `req-02-含-斜杠-的-标题/`。 |
| 2 | `harness suggest --apply sug-08` 单级 req + sug-08 搬到 `flow/suggestions/archive/` + frontmatter `status: applied` | [x] 满足 | 代码：`workflow_helpers.py` L3119-3120 首行 `[:60]` 截断；L3125-3131 `archive_dir.mkdir + target.replace + status: pending → applied`。单测：`test_slug_paths.py::ApplySuggestionArchiveTest::test_apply_sug08_style_long_line_produces_flat_dir_and_archives_source`（显式断言 req 单级、源文件被 move、archive 存在、`status: applied`）。E2E：场景 1 `req-01-清理-workflow-flow-archive-...-早/` + sug 搬入 archive + frontmatter 翻转。 |
| 3 | 长 title（>100 字）slug ≤ 60，state yaml `title` 保留原句 | [x] 满足 | 代码：`_path_slug` L2193 `slug[:max_len].strip("-")` + L3324 `save_simple_yaml(..., "title": requirement_title, ...)` 使用 raw title。单测：`test_slug_paths.py::test_long_title_slug_is_truncated_but_state_keeps_original`（240 字输入，断言 slug 段 ≤60 且 state yaml 含完整 240 字原文）。E2E：场景 2.5（72 字输入，slug 恰 60 字）。 |
| 4 | `harness bugfix "含/的 标题"` 单级 | [x] 满足 | 代码：`workflow_helpers.py` L3365-3366 `create_bugfix` 同源修复。单测：`test_slug_paths.py::CreateBugfixSlugTest::test_slash_in_bugfix_title_does_not_create_nested_dir` + 补测 `test_slug_paths_extra.py::test_backslash_and_windows_illegal_chars_in_title`。E2E：场景 3 `bugfix-1-含-路径-的-缺陷/`。行为变更适配：`tests/test_cli.py` L1052/L1060 将旧 raw title 路径更新为 `bugfix-1-login-form-validation-fails` kebab-case。 |
| 5 | `python3 -m unittest discover tests` 与基线一致，无回归（基线 171 → 新增后 180） | [x] 满足 | 本轮复跑 `python3 -m unittest discover tests` → `Ran 180 tests` / `FAILED (failures=1, skipped=36)`；唯一 failure=`test_human_docs_checklist_for_req29`（pre-existing，与 bugfix-3 无关）。零新增回归。基线轨迹 171（旧）+ 5（开发者 test_slug_paths.py）+ 4（testing 补测 test_slug_paths_extra.py）= 180。 |
| 6 | 新增的 3+ 条针对 slug 清洗的单元测试全绿 | [x] 满足 | 本轮复跑 `python3 -m unittest tests.test_slug_paths tests.test_slug_paths_extra` → 9 passed / 0 failed。覆盖：req slash、req 长 title、req 空回退、bugfix slash、apply sug-08 风格、反斜杠+Windows 非法字符、换行折叠、幂等 id 自增、无 frontmatter sug 归档。9 > 3+ 下限。 |

**Validation Criteria 判定汇总**：6/6 全部满足。

---

## 2. Regression 根因修复逐点核查（diagnosis.md 列 3 处 + 1 附加缺口）

`regression/diagnosis.md` 列的根因清单（`apply_suggestion` / `create_requirement` / `create_bugfix` + 附加 sug 归档缺口）与实际修复一一对照：

| # | diagnosis.md 根因定位 | 修复位置（workflow_helpers.py） | 判定 |
|---|---|---|---|
| R1 | `apply_suggestion` L3100-3103：`splitlines()[0]` 无长度上限 | L3116-3120：`body.splitlines()[0].strip()[:60]` 显式截断；空回退 `suggest_id`。 | [x] 已修 |
| R2 | `create_requirement` L3275/L3290：`f"{req_num_id}-{requirement_title}"` 拼 raw title 到 Path，无 slugify，无长度上限 | L3299-3302：新增 `_path_slug` 清洗 + 长度上限 60 + 空回退 id-only；state yaml L3317 路径复用 `dir_name`。 | [x] 已修 |
| R3 | `create_bugfix` 同款缺陷（L3337/L3375） | L3363-3366：与 `create_requirement` 同源修复（`_path_slug` + id-only 回退）。 | [x] 已修 |
| R4 | 附加：`apply_suggestion` 成功后 sug 未搬 archive（与 sug-06 归档惯例不一致） | L3123-3131：`archive_dir.mkdir(parents=True, exist_ok=True)` + `target.replace(archive_path)` + frontmatter `pending → applied`（顺序：先搬文件再翻转，避免 race）。 | [x] 已修 |

**根因修复汇总**：4/4 全部到位。无漏修、无 over-fix。

**衍生风险（testing 已识别，不阻断本次验收）**：
- `apply_all_suggestions`（L3261 附近）仍用旧 `f"{req_id}-{title}"` 拼接路径，属同源缺陷的潜在复发点。已在 `测试结论.md#未覆盖场景` 记录为"建议后续 sug 跟踪"，不在 bugfix-3 范围内。建议 done 阶段转入 suggest 池跟踪（新开 sug）。

---

## 3. 非回归核查

- 本轮主仓全量 `python3 -m unittest discover tests` 实跑：
  - 结果：`Ran 180 tests` / `FAILED (failures=1, skipped=36)` / 0 errors。
  - 唯一 failure：`test_smoke_req29.HumanDocsChecklistTest.test_human_docs_checklist_for_req29`（pre-existing，req-29 人文档 checklist 相关，与 bugfix-3 完全解耦）。
  - 与 testing 阶段 test-evidence.md 声明的 180 / 1 failure / 36 skipped 完全一致，可复现。
- 行为变更适配性核查（3 个被修改的测试）：
  - `tests/test_cli.py` L1053 `bugfix-1-login-form-validation-fails` + L1060 同步 state yaml 路径：正确反映新行为（英文 title kebab-case 化，与 `_path_slug` 对英文 title 的 `slugify_preserve_unicode` 结果一致），未隐藏 bug。
  - `tests/test_suggest_cli.py` L138-155：`mock.patch(create_requirement)` 屏蔽真实创建，聚焦 apply 路径的"文件被 move 到 archive"断言；正确、不过度削弱断言。
  - `tests/test_smoke_req28.py` L305-310：apply 后断言源路径不存在 + archive 存在 + frontmatter `status: applied`；正确反映 bugfix-3 新行为。
- 结论：三处断言更新全部属于"行为变更的必要适配"，未放水、未覆盖缺陷。

---

## 4. 状态漂移检查（acceptance → done 前置，sug-05）

| 检查项 | runtime.yaml | state/bugfixes/bugfix-3-*.yaml | 判定 |
|---|---|---|---|
| `stage` | `acceptance` | `stage: "acceptance"` | [x] 一致 |
| `status` 类 | `current_requirement: bugfix-3` + `active_requirements: [bugfix-3]` | `status: "active"` | [x] 一致（bugfix 的"active" 与 runtime 的 current/active 语义同步） |
| `stage_timestamps` | n/a | `executing / testing / acceptance` 三个时间戳均已落 | [x] 与 ff_stage_history 吻合 |

未发现状态漂移，流转到 done 前无需先修状态。

---

## 5. AI 侧综合建议

基于：
- Validation Criteria 6/6 全部满足，全部有代码 + 单测 + E2E 三层证据；
- regression 根因 4/4 修复到位，无漏修；
- 主仓全量 180 tests / 唯一 pre-existing failure 可复现，零新增回归；
- 状态一致性检查通过；
- 行为变更断言更新合理、不削弱验证强度；

**AI 侧建议：通过（建议 acceptance pass）**。

附加建议（不阻断通过判定）：

1. **regression 阶段《回归简报.md》补齐**（对人文档契约 3）：流转到 done 前，建议主 agent 回派 regression subagent 产出 `artifacts/main/bugfixes/bugfix-3-.../回归简报.md`（或主 agent 在 done 六层回顾阶段统一补），使 `harness validate --human-docs` 能达到 Summary 全绿。当前 2/5 的两项缺失中，`交付总结.md` 属 done 产出，`验收摘要.md` 随本次提交即补，真正的历史遗留仅 `回归简报.md` 一项。
2. **apply_all_suggestions 同源隐患跟踪**（testing 已记）：建议在进入 done 阶段前 / done 阶段内新开 sug，把 `workflow_helpers.py` L3261 附近的 `f"{req_id}-{title}"` 同类隐患挂到 suggest 池跟踪，避免未来批量 apply 重演 bugfix-3 场景。

---

## 6. 需要人工最终判定的事项

本 AI 报告不代替人工最终判定。请人工确认以下一项即可敲定验收：

- 是否把"《回归简报.md》regression 阶段对人文档补齐"作为**通过的后置条件**（即允许先过 acceptance 再补）还是**硬前置**（回退到 executing 补齐）。
- 根据 `stage-role.md` 契约 3 + `acceptance.md` 经验文件的"以 Summary 为准"解读，推荐"后置补齐"（不回退），符合 bugfix 快速流程不硬扣押的精神。

---

## 7. 产出文件清单

- `artifacts/main/bugfixes/bugfix-3-修复 suggest apply 与 create_requirement 的 slug 清洗与截断/acceptance-report.md`（本文件，agent 侧详细报告）
- `artifacts/main/bugfixes/bugfix-3-修复 suggest apply 与 create_requirement 的 slug 清洗与截断/验收摘要.md`（对人文档，≤ 1 页）
- `artifacts/main/bugfixes/bugfix-3-修复 suggest apply 与 create_requirement 的 slug 清洗与截断/session-memory.md`（追加 acceptance 条目）
- `.workflow/state/action-log.md`（追加 acceptance 条目）
