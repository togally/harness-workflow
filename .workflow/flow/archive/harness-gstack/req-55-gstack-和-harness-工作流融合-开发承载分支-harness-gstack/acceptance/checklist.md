---
id: acceptance-req-55
title: "req-55 验收 checklist（gstack 和 harness 工作流融合）"
parent_requirement: req-55
created_at: 2026-05-08
operation_type: acceptance
stage: acceptance
---

## 验收对照表（AC-01 ~ AC-08 逐条）

| AC | 描述 | 落地证据（chg） | 自检命令 / 结果 | 验收结果 |
|----|------|----------------|----------------|---------|
| AC-01 | vendor 全 skill 落盘（46 目录 + SKILL.md + VERSION-gstack + _shared 三件套） | chg-01 | `find src/harness_workflow/assets/gstack-skills/ -maxdepth 2 -name SKILL.md \| wc -l` → 46；_shared/{bin(59 文件),agents,scripts(30 文件),LICENSE-gstack(MIT 全文),VERSION-gstack(含 upstream URL+commit c7aefc1+时间)} 齐全；`scripts/vendor-gstack.sh` 存在 | PASS |
| AC-02 | harness install --agent claude 后 ~/.claude/skills/ 下 46 skill + LICENSE-gstack 推送；agent_kind≠claude 跳过+warn | chg-01 | 集成测试 15/15 通过：test_skills_pushed_to_claude_skills + test_license_pushed_to_each_skill + test_agent_codex_skips_gstack 全覆盖；test_runtime_yaml_gstack_status_written 通过 | PASS |
| AC-03 | analyst.md Step A2 前嵌入 /office-hours 段（触发协议+adapter+fallback）；role-command-map.yaml 含 1 行 analyst→office-hours | chg-02 | grep "Step A1.5" analyst.md 命中三段；`python3 -c "import yaml; yaml.safe_load(open('role-command-map.yaml'))"` → {'roles': {'analyst': {'primary_skill': 'office-hours', 'alternates': []}}}，合法 | PASS |
| AC-04 | adapter 完整 mapping 表（startup mode 7 段 + builder mode 差异表 + 多余段 → Office Hours Notes） | chg-02 | analyst.md 含 startup mode 7 源段映射表 + builder mode 差异表 + 多余段处理 + skip+warn 说明；两表完整可机械重组 | PASS |
| AC-05 | chg-05 dogfood 自适用活证（/office-hours → design doc → adapter 重组 → requirement.md 覆盖 + retro） | chg-05 | deferred 设计约束（第 8 轮修正候选 P）：本 req 周期仅 Step 1~3 落地（retro 4 子节模板预埋 + scaffold_v2 mirror + deferred 承诺合约 6 字段 + 回填合约 3 项）；真活证由 req-56+ 首次 /harness-requirement 自然兑现 | CONDITIONAL（deferred 设计合约，非缺陷；验收接受） |
| AC-06 | scaffold_v2 三文件与 live 完全一致；harness validate --contract role-stage-continuity 通过 | chg-04 | `diff analyst.md scaffold_v2/.../analyst.md` → 无差异；`diff role-command-map.yaml scaffold_v2/.../role-command-map.yaml` → 无差异；`diff README.md scaffold_v2/.../README.md` → 无差异；`diff artifacts/project/.../analyst.md scaffold_v2/.../analyst.md` → 无差异；contract FAIL 来自 bugfix-5 历史文本（commit 205c132），git stash 基线验证确认 pre-req-55 状态同结果 | CONDITIONAL（contract FAIL 为 pre-existing；diff 全清洁；验收豁免 pre-existing） |
| AC-07 | _shared/LICENSE-gstack MIT 全文 + _shared/VERSION-gstack 含 URL+commit+时间；推送时 per-skill LICENSE 注入；README "Third-party Vendored Skills" 节 46 skill 表 + attribution | chg-01 | `grep "MIT License" _shared/LICENSE-gstack` 命中；VERSION-gstack 含 upstream_url+commit c7aefc1+vendor_timestamp；README L225 "46 skills" + L276 attribution 代码块含 URL+commit；test_license_pushed_to_each_skill 通过 | PASS |
| AC-08 | runtime.yaml.gstack_status 4 子字段；schema 含入 .workflow 校验；装载失败回退 warn + gstack_run_log | chg-01 | DEFAULT_STATE_RUNTIME (workflow_helpers.py:80-86) 含 4 子字段 + gstack_run_log；scaffold_v2 runtime.yaml 模板含同字段；test_runtime_yaml_gstack_status 通过；test_skill_push_failure_does_not_block 通过 | PASS |

**小计**：6 PASS + 2 CONDITIONAL（无 FAIL）。

---

## testing WARN 处理

### W-01：AC-01"三件套"描述不精确

**testing 报告**：requirement.md AC-01 写"每目录至少 SKILL.md + LICENSE-gstack + VERSION-gstack 三件套"，但 vendor 副本 skill 目录实际只有 SKILL.md + VERSION-gstack；per-skill LICENSE-gstack 在 harness install 推送到 ~/.claude/skills/ 时从 _shared 注入。

**acceptance 处理（直接修）**：AC-01 描述已在本 acceptance 阶段修正——将"三件套（SKILL.md + LICENSE-gstack + VERSION-gstack）"改为"SKILL.md + VERSION-gstack；per-skill LICENSE-gstack 在推送时从 _shared 注入"，并在 _shared 共享资源处明确列出 LICENSE-gstack。

**裁定**：PASS（实现正确，描述已修正，无残留问题）。

---

### W-02：47 vs 46 数量描述不一致

**testing 报告**：requirement.md 多处写"47"，实际 upstream（commit c7aefc1）有 46 个含 SKILL.md 的 skill 目录；README.md 已正确写 46。

**acceptance 处理（直接修）**：已在本 acceptance 阶段修正 requirement.md 以下位置：
- L11 Goal："47 个 SKILL.md" → "46 个 SKILL.md"；"全部 47 个 gstack skill" → "全部 46 个 gstack skill"
- L19 Scope.Included chg-01："vendor 全部 47 个 gstack SKILL.md" → "vendor 全部 46 个 gstack SKILL.md"
- L45 AC-01："47 个 skill 目录" → "46 个 skill 目录"（同时修正三件套描述，见 W-01）
- L46 AC-02："全部 47 个 vendored skill" → "全部 46 个 vendored skill"
- L51 AC-07："全部 47 个 vendored skills" → "全部 46 个 vendored skills"

保留 Office Hours Notes（L77-78）中的"47"——该段是历史决策背景记录，不代表当前规范。
README.md 已写 46，无需修改。
chg-01 change.md 中的"47"不修（历史 snapshot 保留 audit trail）。

**diff 摘要**：requirement.md 共 5 处"47"（数量描述）→"46"；1 处三件套描述精确化（同时含 W-01 修正）。

**裁定**：PASS（已直接修正，数量描述与实现一致）。

---

### W-03：AC-05 dogfood deferred

**testing 报告**：chg-05 真活证由 req-56+ 兑现；本 req 周期仅 Step 1~3 落地。

**acceptance 裁定**：明确接受 deferred 合约。

理由：
1. chg-05 第 8 轮设计修正（候选 R → 候选 P）已记录在 change.md，设计意图明确——真活证必须通过 `/harness-requirement → harness-manager → analyst → /office-hours → adapter` 完整链路自然触发，而非 req-55 周期内手工抽测。
2. deferred 承诺合约完整（chg-05 session-memory.md 含 deferred 承诺声明 + 触发条件 + 兑现判定 3 项 + 回填合约 3 项 + 6 字段触发证据预留 + Step 1~3 完成标记）。
3. retro 4 子节模板预埋于 `artifacts/project/experience/roles/analyst.md`（自检命中）+ scaffold_v2 mirror 一致（diff 清洁）。

**AC-05 deferred 合约以下一个真实 req-56+ 兑现为验收门；本 req 内 Step 1~3 已落地为合规接受。**

---

### W-04：AC-06 harness validate pre-existing FAIL

**testing 报告**：`harness validate --contract role-stage-continuity` FAIL 来自 bugfix-5 session-memory 历史文本（commit 205c132），早于 req-55 任何改动；本 req 引入新违规：0 条。

**acceptance 裁定**：豁免。

理由：
1. git stash + 基线验证：pre-req-55 状态下同一命令结果完全相同，FAIL 来源与本 req 无关。
2. FAIL 来源是 bugfix-5（同角色跨 stage 自动续跑硬门禁）的 session-memory.md 历史文本引用（target_stage=planning/acceptance/done），是 pre-existing 文本格式问题，非 req-55 引入的功能缺陷。
3. chg-04 AC-06 原文要求"harness validate 通过"——该要求在 pre-existing FAIL 问题解决前无法严格满足，但本 req 范围内 scaffold_v2 镜像功能本身（diff 全清洁）已满足 chg-04 的真实交付意图。

**pre-existing FAIL 在本 req 验收基线之外；建议另开 sug 池条目处理 bugfix-5 引用清理（文本格式修正，不影响功能）。**

---

## testing INFO 记录

### I-01：5 个 test_trivial_*.py 文件预存 ImportError

- tests/test_create_trivial.py + tests/test_trivial_admission.py + tests/test_trivial_sequence_helper.py + tests/test_trivial_state_machine.py + tests/test_suggest_apply_trivial.py 均 import 不存在的函数（create_trivial / classify_diff_change_types 等）。
- git log 确认：早于 req-55，属 pre-existing，非本 req 引入。
- **处理**：记入 sug 池后续清理条目（建议按 sug 直接处理路径删除这 5 个孤立测试文件）。

### I-02：test_tc07_dogfood_full_chain 预存失败

- tests/test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops 在 pre-req-55 基线就已失败，独立比对确认。
- 非本 req 引入，不影响 req-55 功能验收。
- **处理**：记入 sug 池后续清理条目（建议独立分析根因，可能与 harness next subprocess 超时或环境有关）。

---

## 已修正动作（acceptance 阶段直接处理的文档微调）

按 base-role 硬门禁四降级语义（"文档微调可直接做"），本 acceptance 阶段直接修正以下文档：

**文件**：`.workflow/flow/requirements/req-55-gstack-和-harness-工作流融合-开发承载分支-harness-gstack/requirement.md`

**修正 1（W-02）**：5 处数量描述 47 → 46
- Goal L11："47 个 SKILL.md" → "46 个 SKILL.md"；"全部 47 个 gstack skill" → "全部 46 个 gstack skill"
- Scope.Included L19："vendor 全部 47 个 gstack SKILL.md" → "vendor 全部 46 个 gstack SKILL.md"
- AC-01 L45："47 个 skill 目录" → "46 个 skill 目录"
- AC-02 L46："全部 47 个 vendored skill" → "全部 46 个 vendored skill"
- AC-07 L51："全部 47 个 vendored skills" → "全部 46 个 vendored skills"

**修正 2（W-01）**：AC-01 三件套描述精确化
- 原文："每目录至少 SKILL.md + LICENSE-gstack + VERSION-gstack 三件套"
- 新文："每目录至少 SKILL.md + VERSION-gstack；per-skill LICENSE-gstack 在 harness install 推送到 ~/.claude/skills/ 时从 _shared 注入，vendor 副本目录本身不含独立 LICENSE-gstack"；_shared 清单明确列出 LICENSE-gstack + VERSION-gstack。

**未修改**：
- README.md（已正确写 46，无需修改）
- chg-01 change.md / plan.md（历史 snapshot 保留 audit trail，不改）
- Office Hours Notes 段（历史决策背景记录，不代表当前规范，保留"47"）

---

## harness validate --human-docs 状态说明

运行结果：`harness validate --human-docs --requirement req-55` → 0/2 present：
- [ ] requirement.md（raw_artifact 副本）→ 缺失
- [ ] 交付总结.md → 缺失（done stage 才产出）

**分析**：
1. `交付总结.md` 在 done stage 由 done 角色产出，在 acceptance 阶段尚未到达，缺失属正常预期状态（同 req-51 ~ req-53 的 acceptance 阶段状态一致）。
2. `requirement.md` raw_artifact 副本：检查 req-51 ~ req-53 artifacts 目录，均无此文件（仅 req-50 有，系人工复制），说明该文件在当前流程下非 done 前自动产出。
3. 这是系统性预存约束（validate --human-docs 在 acceptance 阶段对 req-41+ 永远无法全绿），非 req-55 特有问题。

**裁定**：此 0/2 为系统性预存约束，不构成 req-55 的 FAIL 点。建议后续 sug 条目评估是否修正 validate --human-docs 在 acceptance 阶段的检查逻辑（例如 done 级文档在 done stage 前设为 expected-deferred 状态）。

---

## 风险残留 / 后续跟踪

| 编号 | 性质 | 内容 | 建议处理 |
|------|------|------|---------|
| R-01 | deferred 合约 | AC-05 chg-05（dogfood 活证）真活证由 req-56+ 兑现 | req-56 analyst 按 chg-05 session-memory 回填合约三项 |
| R-02 | sug 池条目 | bugfix-5 session-memory 文本格式引发 harness validate contract FAIL（pre-existing） | 开 sug 条目：修正 bugfix-5 session-memory.md 中 target_stage= 格式，清洁 contract lint |
| R-03 | sug 池条目 | 5 个 test_trivial_*.py 孤立测试文件预存 ImportError | 开 sug 条目：删除这 5 个孤立文件 |
| R-04 | sug 池条目 | test_tc07_dogfood_full_chain 预存失败 | 开 sug 条目：独立分析根因 |
| R-05 | sug 池条目 | validate --human-docs 在 acceptance 阶段对 req-41+ 永远 0/2（交付总结 deferred + raw_artifact 副本非自动产出） | 开 sug 条目：评估修正检查逻辑或为 done-deferred 文档设 expected-deferred 状态 |

---

## 结论

- **验收判定：CONDITIONAL_PASS**

**理由**：

代码层测试全通过（15/15 chg-01 专项，0 新增回归），文档层测试满足（Step A1.5 三段齐全、YAML 合法、README ≤ 50 行），scaffold_v2 mirror 全清洁（4 diff 均 exit 0），vendor 副本结构完整（46 SKILL.md + _shared 全件），触发链逻辑自洽（3 场景 fallback 全覆盖 + deferred 合约 6 字段），runtime.yaml schema 4 子字段已落。

CONDITIONAL 原因及处置：
1. **AC-05 deferred（设计合约）**：chg-05 dogfood 真活证 deferred 到下一个真实 req；本 req 内 Step 1~3（retro 模板预埋 + scaffold mirror + deferred 承诺合约）已落地，acceptance 明确接受；验收门为 req-56+ analyst 兑现。
2. **AC-06 pre-existing contract FAIL 豁免**：harness validate --contract role-stage-continuity FAIL 来自 bugfix-5 历史文本（commit 205c132），本 req 引入新违规 0 条；scaffold_v2 镜像 diff 全清洁，chg-04 核心交付意图已满足；豁免并建议后续 sug 处理。

无 BLOCKER 级问题。W-01 + W-02 已直接修正（requirement.md 文档微调）。I-01 + I-02 记入 sug 池条目。

- **verdict 路由建议：done**（CONDITIONAL_PASS → done；acceptance exit_decision = verdict）
- **关键证据引用**：
  - 代码层：tests/installer/test_gstack_skills_push.py 8/8 + tests/integration/test_install_pushes_gstack.py 7/7（独立复跑确认）
  - 文档层：analyst.md Step A1.5 三段 grep 命中；role-command-map.yaml yaml.safe_load 合法；README 36 行 ≤ 50 行约束
  - mirror 层：4 条 diff 全无差异（exit 0）
  - vendor 层：`find ... -name SKILL.md | wc -l` → 46；_shared 目录 bin(59)+scripts(30)+agents(1)+LICENSE-gstack+VERSION-gstack 齐全
  - 状态一致性：runtime.yaml stage=acceptance 与 state/requirements/req-55.yaml stage=acceptance 一致
