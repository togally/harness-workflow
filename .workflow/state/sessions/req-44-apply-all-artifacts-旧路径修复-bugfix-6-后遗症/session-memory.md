# Session Memory — req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））

## 1. Current Goal

planning stage：把 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））拆 chg + 起草 plan.md 大纲，不动业务代码。

## 2. Context Chain

- Level 0：主 agent（technical-director / opus）
- Level 1：本 subagent — 分析师（analyst / opus），planning stage

## 3. 模型一致性自检

briefing 期望 model = opus（Opus 4.7），与 `.workflow/context/role-model-map.yaml` `roles.analyst.model = "opus"` 一致；runtime 不可自省具体子版本，按 Step 7.5 fallback 写"未自检 / 期望 = opus"留痕。

## planning stage

### 3.1 拆 chg 决策（default-pick）

**default-pick = 拆 2 chg**（理由：apply 系列与 rename 模块物理分离 + 责任边界清晰；scope 仍小不必拆 3，但合 1 会让回归点过广）：

- **chg-01（apply / apply-all CLI 路径与内容修复）** — 合并 AC-01 + AC-02
- **chg-02（rename CLI 同步范围扩展）** — 单独承载 AC-03

AC-04（scaffold mirror）按惯例两 chg 各自负责自己改动的 mirror；AC-05（e2e 用例）拆到对应 chg 的 §测试用例设计 段。

---

### 3.2 chg-01（apply / apply-all CLI 路径与内容修复）大纲

**目标**：修复 `harness suggest --apply-all` 在 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 后路径不匹配 abort（sug-43（apply-all artifacts/ 旧路径检查导致 abort）），并修复 `--apply <id>` 单 sug 取 content 头当 title + 不真填 requirement.md（sug-44（apply 取 content 头当 title + rename 不同步 runtime） / sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/））。

**影响文件**：

- `src/harness_workflow/workflow_helpers.py`：
  - `apply_all_suggestions`（line 4489）：`req_dir` 拼接当前用 `resolve_requirement_root(root)` 返回 `artifacts/{branch}/requirements`，对 req-id ≥ 41 应改走 `.workflow/flow/requirements/`（即 `_use_flow_layout(req_id)` True 分支命中 flow 路径）；
  - `apply_suggestion`（line 4300）：`title = first_line[:60]` 改为 `title = state.get("title", "").strip() or first_line[:60]`；`create_requirement` 成功后追加把 `body` 真写入新 req requirement.md（§背景 或 §goal 段，default-pick = 追加 `## 合并建议清单` 单段，与 apply-all 同源以减少分支）。
- 配套测试：`tests/test_apply_all_path_slug.py` 扩 + 新增 `tests/test_apply_suggestion_content.py`。

**实施步骤**：

1. 在 `apply_all_suggestions` 内 `req_md` 解析处加 `_use_flow_layout(req_id)` 分支：True → `.workflow/flow/requirements/{dir_name}/requirement.md`；False → 既有 `resolve_requirement_root(...)` 路径（保持 legacy 兼容）。
2. 在 `apply_suggestion` 内 `title` 计算处加 `state.get("title", "")` 优先；`create_requirement` 成功后按 chg-01 步骤 1 同源逻辑解析 `req_md` 路径并追加 sug.body 到 §合并建议清单（与 apply-all 内容写入路径**完全同源 helper**，默认抽 `_append_sug_body_to_req_md(root, req_id, title, body_lines)` 私有 helper）。
3. 同源 helper 落 `workflow_helpers.py`，apply / apply_all 共用，避免双分支漂移。
4. 跑 pytest（目标全绿，重点 `test_apply_all_path_slug.py` + 新文件）。

**§测试用例设计**（B2.5 强制段；regression_scope: targeted；波及接口：`workflow_helpers.apply_all_suggestions` / `workflow_helpers.apply_suggestion`）：

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 apply-all 后 bugfix-6 路径成功 | 1 个 pending sug，当前 req-id ≥ 41 | exit 0；sug 全 unlink；`.workflow/flow/requirements/{req-id}-{slug}/requirement.md` 含 `## 合并建议清单` | AC-01 | P0 |
| TC-02 apply-all legacy req-id 路径仍兼容 | mock req-id ≤ 40 场景 | exit 0；走 `artifacts/{branch}/requirements/...` 路径 | AC-01 | P1 |
| TC-03 apply-all 路径 miss 不 unlink | 制造 req_md 不存在 | exit ≠ 0；sug 文件不被删 | AC-01 | P0 |
| TC-04 apply 单 sug 取 sug.title 当 req title | sug frontmatter title='X'，content 头 ='Y' | 新 req title = 'X'（不是 'Y'） | AC-02 | P0 |
| TC-05 apply 单 sug 真写入 requirement.md | sug.body = 'BODY-MARKER' | 新 req requirement.md 含 'BODY-MARKER' | AC-02 | P0 |
| TC-06 apply 单 sug 后 bugfix-6 路径落位 | req-id ≥ 41 | requirement.md 落 `.workflow/flow/requirements/...` 含 body | AC-02 | P0 |

**验证方式**：`pytest tests/test_apply_all_path_slug.py tests/test_apply_suggestion_content.py -v` 全绿；端到端 `harness suggest --apply-all` 在本仓库手跑一次 sug 全 unlink 且新 req requirement.md 有 sug 内容。

**回滚**：`git revert` chg-01 commit；apply / apply_all 逻辑回到 bugfix-6 后未修复状态（仍 abort，但不引入新回归）。

**scaffold mirror**：本 chg 仅改 src/ + tests/，不动 `.workflow/` 文档树；scaffold mirror 无变化（AC-04 在本 chg 范围内 = no-op，明示在 plan.md）。

**契约 7 注意点**：plan.md / change.md 内首次引用 sug-43（apply-all artifacts/ 旧路径检查）/ sug-44（apply 取 content 头当 title + rename 不同步 runtime）/ sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/）/ bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 必带 ≤ 15 字描述；TaskList / commit message 同样要求。

---

### 3.3 chg-02（rename CLI 同步范围扩展）大纲

**目标**：修复 `harness rename requirement <old> <new>` 在 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 后漏同步 `.workflow/flow/requirements/` 新目录 + runtime.yaml `current_requirement_title` / `locked_requirement_title` 字段（sug-44（apply 取 content 头当 title + rename 不同步 runtime） / sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/））。

**影响文件**：

- `src/harness_workflow/workflow_helpers.py`：
  - `rename_requirement`（line 5338）：当前只动 `resolve_requirement_root(root)` 返回的目录 + state yaml；对 req-id ≥ 41 须额外 mv `.workflow/flow/requirements/{old_dir_name}` → `{new_dir_name}`（如存在）；
  - 同函数末尾 runtime 同步：写入 `current_requirement_title = new_title`（如 `current_requirement` 命中本 req-id）；写入 `locked_requirement_title = new_title`（如 `locked_requirement` 命中本 req-id）。
- 配套测试：`tests/test_rename_helpers.py` 扩。

**实施步骤**：

1. 在 `rename_requirement` 目录 mv 步骤后追加：探测 `.workflow/flow/requirements/{old_dir_name}` 是否存在，存在则 `shutil.move` 到 `{new_dir_name}`（与 artifacts/ 端对称）；
2. runtime 同步段：`if runtime.get("current_requirement") == old_id: runtime["current_requirement_title"] = new_title`；`locked_requirement` 同理；
3. 不改 `rename_change` / `rename_bugfix`（不在 AC-03 范围）；
4. 跑 pytest（重点 `test_rename_helpers.py`）。

**§测试用例设计**（B2.5 强制段；regression_scope: targeted；波及接口：`workflow_helpers.rename_requirement`）：

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 rename 同步 .workflow/flow/ 目录 | 已有 req-id ≥ 41 + flow/ + artifacts/ + state/ 三处目录，rename 到新 title | 三处目录都改名；旧名都不存在 | AC-03 | P0 |
| TC-02 rename 同步 runtime current_requirement_title | rename 当前 active req | runtime.yaml 的 current_requirement_title = new_title | AC-03 | P0 |
| TC-03 rename 同步 runtime locked_requirement_title | rename 时 locked_requirement 命中本 req | runtime.yaml 的 locked_requirement_title = new_title | AC-03 | P1 |
| TC-04 rename 不命中 current 时不动 runtime title | rename 非 current_requirement 的旧 req | runtime.yaml current_requirement_title 不变 | AC-03 | P1 |
| TC-05 rename legacy req-id（无 flow/ 目录）兼容 | req-id ≤ 40，无 .workflow/flow/ 目录 | 不报错；只改 artifacts/ + state/ | AC-03 | P1 |

**验证方式**：`pytest tests/test_rename_helpers.py -v` 全绿；端到端 `harness rename requirement <old> <new>` 在本仓库手跑一次三处目录全改名 + runtime current_requirement_title 字段同步。

**回滚**：`git revert` chg-02 commit；rename 逻辑回到 bugfix-6 后未修复状态（手工 mv + 手工 Edit runtime）。

**scaffold mirror**：本 chg 仅改 src/ + tests/，不动 `.workflow/` 文档树；scaffold mirror 无变化（AC-04 在本 chg 范围内 = no-op）。

**契约 7 注意点**：plan.md / change.md 内首次引用 sug-44（apply 取 content 头当 title + rename 不同步 runtime） / sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/） / bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 必带 ≤ 15 字描述。

---

### 3.4 default-pick 决策清单

- **D-1 拆分粒度**：default-pick = 拆 2 chg（apply 合 1 + rename 单 1）。理由：CLI 模块物理分离 + 测试隔离清晰；3 chg 过细（apply 与 apply_all 共用 helper，硬拆增加耦合）；1 chg 过粗（单 commit 跨 apply / rename 两块回归面）。
- **D-2 apply 单 sug body 写入位置**：default-pick = 追加 `## 合并建议清单` 单段（与 apply-all 同源 helper）。理由：减少分支；与已有 apply_all 输出风格一致；用户不必学两套展示模型。
- **D-3 chg-01 是否抽公共 helper**：default-pick = 是，抽 `_append_sug_body_to_req_md`。理由：avoid drift；apply / apply_all 路径解析 + body 写入完全同源，单点修改。
- **D-4 rename 同步 active_requirements**：default-pick = 否（id 不变，active_requirements 存 id 不需动）。理由：与 sug-44 描述一致——只 *_title 字段需同步。

### 3.5 风险（≤ 3 条）

- **R-1**：apply / apply_all 共享 helper 后若 body 写入语义被某一侧的细节调整污染另一侧，回归面扩大。缓解：TC-05 + TC-01 双向锁住"body 必含 marker"。
- **R-2**：rename `.workflow/flow/` 目录搬迁可能与 archive 流程或后续 done 阶段路径解析冲突（archive 跨 branch 时旧目录已迁走）。缓解：本 chg 仅改 active req 路径，archive 路径不在范围；TC-05 锁住 legacy 兼容。
- **R-3**：runtime 同步漏字段（如未来新增 `pending_requirement_title`）。缓解：在 plan.md §回滚 注明"如未来扩字段，需同步本处"，并在 sug 池补一条 follow-up（done 阶段处理）。

### 3.6 planning stage 抽检反馈

- requirement.md 5 段齐全（含 §1.5 Background / §3 Scope IN/OUT / §4 5 AC / §5 Split Rules），符合契约 7。
- 关联 sug 三条（sug-43 已 applied / sug-44 / sug-45 pending）均在 requirement.md §背景 + §AC 体现，无遗漏。
- B2.5 §测试用例设计 强制段已落到两份 plan.md 大纲，每条用例对应 AC 字段非空，regression_scope 默认 targeted。
- 待主 agent 确认 ≤ 1 条：拆 2 chg 粒度（chg-01 apply 系列 + chg-02 rename）是否同意？同意后由主 agent 批量调 `harness change` 创建 chg 目录 + 落 change.md + plan.md。

## planning stage（plan.md 落地）

### 4.1 模型一致性自检

briefing 期望 model = opus（Opus 4.7）；本 subagent 不可自省具体子版本，按 Step 7.5 fallback 留痕"未自检 / 期望 = opus"，与上节 §3 自检一致，无新告警。

### 4.2 plan.md 落地状态

| chg | plan.md 路径 | 六段齐？ | §测试用例设计用例数 | 状态 |
|-----|-------------|---------|-------------------|------|
| chg-01（apply / apply-all CLI 路径与内容修复） | `.workflow/flow/requirements/req-44-apply-all-artifacts-旧路径修复-bugfix-6-后遗症/changes/chg-01-apply-apply-all-cli-路径与内容修复/plan.md` | ✅ 6 段（目标 / 影响文件 / 实施步骤 / 测试用例设计 / 验证方式 / 回滚+scaffold+契约 7） | 6（TC-01..TC-06） | ✅ 完整 |
| chg-02（rename CLI 同步范围扩展） | `.workflow/flow/requirements/req-44-apply-all-artifacts-旧路径修复-bugfix-6-后遗症/changes/chg-02-rename-cli-同步范围扩展/plan.md` | ✅ 6 段（同上） | 5（TC-01..TC-05） | ✅ 完整 |

合计 §测试用例设计用例数 = **11**（chg-01 6 + chg-02 5），覆盖 AC-01 / AC-02 / AC-03；AC-04（scaffold mirror）两 chg 均 no-op；AC-05（e2e 用例数 ≥ 2）已超额（6 + 5 ≥ 2 + 2）。

### 4.3 关键边界判断

- **D-3 同源 helper 落地**：在 chg-01 §影响文件列表 明示新增 `_append_sug_body_to_req_md(root, req_id, dir_name, sug_id, sug_title, sug_body) -> Path`，apply / apply_all 同源调用，避免双分支漂移（与 §3.4 default-pick D-3 = 是一致）。
- **D-2 body 写入位置**：default-pick = 追加 `## 合并建议清单` 段（与 apply-all 同源），plan.md TC-01 / TC-05 双向锁住"requirement.md 含 marker"。
- **bugfix-6 路径分支**：两 chg 都走 `_use_flow_layout(req_id)` True/False 双分支测试，覆盖 req-id ≥ 41（flow/）+ req-id ≤ 40（legacy artifacts/），不破坏既有归档兼容。
- **runtime 同步范围**：仅 `current_requirement_title` / `locked_requirement_title` 两字段（与 sug-44 / sug-45 描述一致）；`active_requirements` 列表存 id 不动（D-4）。

### 4.4 抽检反馈

- 两份 plan.md 六段齐全，§测试用例设计 表头列齐（用例名 / 输入 / 期望 / 对应 AC / 优先级），每行 ≤ 5 行内容；
- 用例名前缀 `TC-XX <动宾短描述>` 自带语义，符合契约 7 + 硬门禁六批量列举子条款；
- 影响文件列表对齐源码实际行号（apply_suggestion 4300 / apply_all_suggestions 4489 / rename_requirement 5338 / _use_flow_layout 4126 / resolve_requirement_root 5799），无臆造；
- 回滚方式 + scaffold mirror（AC-04 = no-op）+ 契约 7 注意点 三段都齐；
- B2.5 强制段 regression_scope 默认 targeted，波及接口清单显式列出新增 helper。

### 4.5 ✅ 完成判据

- [x] 2 份 plan.md 六段齐（含 §测试用例设计 11 用例 ≥ 11 阈值）
- [x] 每个 §测试用例设计 含表头 + ≥ 1 行用例 + 对应 AC 字段非空
- [x] 影响文件路径对齐实际源码行号
- [x] 契约 7 / 硬门禁六合规（首次引用带括号简短描述 / 批量列举不裸 id）
- [ ] 待主 agent 抽检 + 拍板进 ready_for_execution

## executing stage ✅

### 自检（Step 7.5）
- expected_model: sonnet（Sonnet 4.6），runtime stage = executing，role = executing，与 role-model-map.yaml 一致。

### 工具召唤
- Read 多个 workflow_helpers.py 区段（apply_suggestion / apply_all_suggestions / rename_requirement / _use_flow_layout / resolve_requirement_root / create_requirement）
- 工具：Read / Edit / Write / Bash（pytest）

### 2 chg 实施摘要

| chg | 核心改动 | 关键文件 | 状态 |
|-----|---------|---------|------|
| chg-01（apply / apply-all CLI 路径与内容修复） | 新增 `_append_sug_body_to_req_md` helper（_use_flow_layout 路径分支 + 原子 write）；apply_suggestion 改从 frontmatter title 取值并调 helper 写 body；apply_all_suggestions 废弃旧硬路径，改逐条调 helper，req_md 不存在 → abort + stderr + 保留 sug | `src/harness_workflow/workflow_helpers.py` | ✅ |
| chg-02（rename CLI 同步范围扩展） | rename_requirement 追加 flow/ 目录探测 + 条件 mv；末尾同步 current_requirement_title / locked_requirement_title 到 runtime | `src/harness_workflow/workflow_helpers.py` | ✅ |

### 用例数
- `tests/test_req44_chg01.py`：6 用例（TC-01 ~ TC-06）全过
- `tests/test_req44_chg02.py`：5 用例（TC-01 ~ TC-05）全过
- 合计 11 用例 ≥ plan.md §4 阈值

### 全量回归
- `pytest tests/ -q` → 2 failed（仅 pre-existing：`test_readme_has_refresh_template_hint` / `test_human_docs_checklist_for_req29`），587 passed, 38 skipped

### scaffold diff
- 本 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 仅改 src/ + tests/ + .workflow/ session-memory；不动 scaffold 模板或 .workflow/ 文档树 → scaffold mirror = no-op（AC-04 满足）

### 抽检反馈
- `_append_sug_body_to_req_md`：多次调用幂等聚合（## 合并建议清单 存在时 append ### 段），符合 plan.md §3 设计。
- `apply_suggestion`：frontmatter title 取值逻辑：`state.get("title") or "").strip().strip('"')` 防引号残留，然后 fallback 到 first_line[:60]。
- `rename_requirement`：`shutil.move` 前探测 `_flow_req_dir.is_dir()`，legacy req（无 flow/ 目录）静默跳过，TC-05 验证通过。

## testing stage

### 自检（Step 7.5）
- expected_model: sonnet（Sonnet 4.6），briefing 期望与 role-model-map.yaml `roles.testing = sonnet` 一致。本 subagent 未能自省具体子版本，按 Step 7.5 fallback 留痕。

### 矩阵摘要

| 分类 | 用例数 | 结果 |
|------|--------|------|
| plan.md 复测（chg-01（apply / apply-all CLI 路径与内容修复）6 + chg-02（rename CLI 同步范围扩展）5） | 11 | 11/11 PASS |
| 独立反例（testing 自补） | 4 | 4/4 PASS |
| Dogfood 实跑（apply 全链 + rename） | 2 | 2/2 PASS |
| 合规扫描（R1 / revert / 契约 7 / req-29（角色→模型映射）/ req-30（用户面 model 透出）） | 5 | 5/5 PASS |
| 全量回归 | 591 passed | 0 new failure，2 pre-existing |

### 缺陷数

0 新缺陷。2 pre-existing failure（test_readme_has_refresh_template_hint / test_human_docs_checklist_for_req29）与 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 无关。

### 抽检反馈

- TC-02 legacy 路径兼容：apply-all 在 req-id ≤ 40 时正确走 artifacts/ 路径，body 含 LEGACY-BODY。
- EC-02 幂等聚合：## 合并建议清单 marker 二次调用后仍只出现 1 次。
- Dogfood rename：runtime.current_requirement_title 从 "Dogfood apply 全链验证" 更新为 "Renamed Dogfood Req"，验证 runtime 同步。
- 契约 7 minor：change.md §3 模板字段 `- \`req-44\`` 裸 id（模板结构字段，非叙述性引用），不阻断。

### ✅ testing stage 完成

## acceptance stage

### 自检（Step 7.5）
- expected_model: sonnet（Sonnet 4.6），briefing 期望与 role-model-map.yaml `roles.acceptance = sonnet` 一致。

### PASS/FAIL 计数

| 检查类别 | 小计 |
|---------|------|
| AC 映射 | 5/5 PASS |
| checklist 项 | 12/12 PASS（1 minor 不阻断） |
| followup 数 | 2（F-01 change.md 裸 id + F-02 runtime 字段扩展） |

### 验收结论

**PASS** — 5 AC 全覆盖；全量回归 591 passed，0 new failure；2 followup 均不阻断。推荐流转：acceptance → done。

### 抽检反馈

- 代码抽样：`_append_sug_body_to_req_md` line 4300 / `apply_all_suggestions` line 4550 / `rename_requirement` step 4+5 line 5462–5476 均与 plan.md 设计一致。
- test 文件三份（test_req44_chg01.py / chg02.py / testing_extra.py）实际存在，用例数 6+5+4=15 超 AC-05 阈值。
- 契约 7 minor：change.md §3 模板字段裸 id，testing 已评估不阻断，本次维持。

### ✅ acceptance stage 完成

## done 阶段回顾报告

> 角色：主 agent（done / opus，Opus 4.7）；执行日期：2026-04-25；
> 自检：briefing 期望 model = opus，与 `role-model-map.yaml` `roles.done.model = opus` 一致（runtime 不可自省具体子版本，按 Step 7.5 fallback 留痕）。

### Context 层（PASS）

- 各 stage 角色行为合规：analyst（planning 拆 2 chg）/ executing（2 chg + 11 用例）/ testing（11 + 4 反例 + 2 dogfood + 5 合规）/ acceptance（12/12 PASS + 5 AC + 2 followup）均按角色 SOP 执行，无越权。
- session-memory 链路完整：planning §3 决策清单 + executing §自检 + testing §矩阵 + acceptance §结论。
- 经验文件已成熟（analyst.md 111 行 / executing.md 375 行 / testing.md 197 行）；本 req 候选教训已在 §经验沉淀 评估。

### Tools 层（PASS）

- 工具链顺畅：Read / Edit / Write / Bash（pytest）+ 主 agent 手动 Edit runtime（绕 Flow 层 over-chain）。
- 无 CLI / MCP 工具新增需求，`workflow_helpers.py` 内 helper 抽取（`_append_sug_body_to_req_md`）按 plan.md §3 D-3 同源 helper 决策落地，避免 apply / apply_all 双分支漂移。

### Flow 层（FAIL — sug-38（harness next over-chain bug）再次实证）

- **sug-38（harness next over-chain bug）本周期再次触发**：本 req `harness next --execute` 触发后，stage 从 ready_for_execution 一次性自动跑完 executing → testing → acceptance → done（`req-44.yaml` `stage_timestamps` 中 executing/testing/acceptance/done 四个时间戳全在 02:00:28，差 < 7s），主 agent 不得不**手动 Edit runtime.yaml** 滚回每个 stage 各派 subagent 才得以走完 stage gate。
- 这与 sug-40（sug-38（harness next over-chain bug） meta-followup） 描述一致；本 req 是该 bug 的**第二次跨 req 实证**，**优先级建议升级 P0 紧急修复**。
- 其他流转点（planning → ready_for_execution 跨 ~16 分钟，正常）顺畅。

### State 层（FAIL — usage-log.yaml 缺失）

- **`.workflow/state/sessions/req-44-.../usage-log.yaml` 不存在**：本 req 主 agent 派发 ≥ 4 次 subagent（analyst-planning / executing / testing / acceptance），但 `record_subagent_usage` 派发钩子文字契约未真接通（sug-39（chg-01 派发钩子真实接通 record_subagent_usage） 仍 pending），entries 数 = 0，对应交付总结 §效率与成本 token 字段全部按"⚠️ 无数据"标，禁止编造。
- runtime.yaml 一致性：stage = done / status = done / completed_at 已写，与 `req-44.yaml` 同步。
- session-memory 树完整（含 planning / executing / testing / acceptance 段）；req-44 yaml `stage_timestamps` 6 段齐（虽然 4 段同秒）。

### Evaluation 层（PASS）

- testing 与 acceptance 独立性：testing subagent 自补 4 反例 + 2 dogfood，对原 plan.md 的 11 用例补充客观验证（边界 + 集成）；acceptance 12 项 checklist 含代码抽样 + 用例数核对 + AC 映射，未被 testing 影响。
- 评估标准达成：5 AC 全 PASS；591 全量 PASS（0 new failure）；2 pre-existing failure（test_smoke_req28 / test_smoke_req29）与本 req 无关。

### Constraints 层（PASS — 1 minor）

- 硬门禁一/二/三/四/六/七：subagent 自检 + 自我介绍模板齐 + default-pick 留痕（D-1..D-4）+ 周转汇报符合 Ra/Rb/Rc + id 首次引用全带括号简短描述。
- 契约 7 minor：chg-01 / chg-02 `change.md` §3 Requirement 字段 `- \`req-44\`` 裸 id（模板结构字段，非叙述性引用），testing 与 acceptance 均评估不阻断，已转 followup F-01。
- R1 越界 / revert dry-run / req-29（角色→模型映射）/ req-30（用户面 model 透出）合规扫描全 PASS。

### 工具适配性发现

- 无新 CLI / MCP 工具需求；现有 helper 抽取（`_append_sug_body_to_req_md`）能力恰当。

### 经验沉淀验证（Step 4）

- analyst.md / executing.md / testing.md 均已含相关教训通用规约；本 req 候选教训按 §经验沉淀候选 评估后追加 1 条（testing.md "CLI bug 修复的 dogfood 实跑验证模式"）。
- acceptance / regression / harness 等其他经验文件本 req 无新教训。

### 流程完整性

- 阶段未跳过：planning → ready_for_execution → executing → testing → acceptance → done 六段全走（虽然中间四段 timestamp 因 sug-38 over-chain 同秒，主 agent 已手动滚回每段派 subagent）。
- 短路 / 重复 / 遗漏：均无。

## 5. Next Steps

acceptance 完成，推进 done。done 阶段已产出回顾报告 + 交付总结 + sug 提交。

## 6. Completed Tasks

- [x] 加载 runtime.yaml / base-role.md / stage-role.md / analyst.md / role-model-map.yaml
- [x] 读 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） requirement.md
- [x] 读 sug-43（apply-all artifacts/ 旧路径检查导致 abort）/ sug-44（apply 取 content 头当 title + rename 不同步 runtime）/ sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/）
- [x] 读 harness_suggest.py / harness_rename.py / workflow_helpers 中 apply_suggestion / apply_all_suggestions / rename_requirement / resolve_requirement_root / _use_flow_layout
- [x] 写 planning stage 拆 chg 大纲 + default-pick + 风险（§3）
- [x] 落 chg-01 plan.md 六段齐（§测试用例设计 6 用例）
- [x] 落 chg-02 plan.md 六段齐（§测试用例设计 5 用例）
- [x] 追加本 §planning stage（plan.md 落地）段含抽检反馈与完成判据
