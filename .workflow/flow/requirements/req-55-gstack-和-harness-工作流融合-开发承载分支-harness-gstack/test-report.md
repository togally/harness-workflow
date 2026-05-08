---
id: test-report-req-55
title: "req-55 测试报告（gstack 和 harness 工作流融合）"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: test-report
stage: testing
---

## 测试覆盖范围

本报告覆盖 req-55（gstack 和 harness 工作流融合（开发承载分支 harness-gstack））的 4 个 chg 落地产物，按 7 个测试维度独立评估：

| chg | 标题 | 测试重点维度 |
|-----|------|------------|
| chg-01 | gstack 内置发布契约（vendor 46 skill + harness install 自动装载） | 维度 1、4 |
| chg-02 | analyst → /office-hours 强映射 + adapter 后处理 | 维度 2、5 |
| chg-04 | scaffold_v2 镜像 | 维度 3 |
| chg-05 | dogfood 活证（候选 P 第 8 轮重写，Step 1~3 deferred 落地） | 维度 2、5 |

7 个测试维度：代码层测试 / 文档层测试 / mirror 一致性测试 / vendor 副本完整性测试 / 触发链可行性 paper test / AC 覆盖度评估 / 契约 lint

---

## 维度 1：代码层测试

### 1.1 chg-01 专项测试（pytest 15/15）

运行命令：
```
python3 -m pytest tests/installer/test_gstack_skills_push.py tests/integration/test_install_pushes_gstack.py -v
```

结果：**15/15 通过（5.51s）**

| 测试文件 | 用例数 | 通过 |
|---------|--------|------|
| tests/installer/test_gstack_skills_push.py | 8 | 8/8 |
| tests/integration/test_install_pushes_gstack.py | 7 | 7/7 |

用例列表（全通过）：
- test_vendor_script_single_skill
- test_vendor_script_all
- test_install_pushes_skills_when_agent_claude
- test_install_skips_when_agent_codex
- test_conflict_default_warn
- test_force_gstack_overrides
- test_skill_push_failure_does_not_block
- test_runtime_yaml_gstack_status_written
- TestInstallPushesGstack::test_skills_pushed_to_claude_skills
- TestInstallPushesGstack::test_license_pushed_to_each_skill
- TestInstallPushesGstack::test_shared_resources_pushed
- TestInstallPushesGstack::test_runtime_yaml_gstack_status
- TestInstallPushesGstack::test_vendor_version_matches_shared
- TestInstallPushesGstack::test_idempotent_second_run_no_conflict
- TestInstallPushesGstack::test_agent_codex_skips_gstack

### 1.2 全量回归对比（排除预存失败组）

运行命令（排除 5 个预存的 trivial 系列 import error 文件）：
```
python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/test_create_trivial.py --ignore=tests/test_trivial_admission.py --ignore=tests/test_trivial_sequence_helper.py --ignore=tests/test_trivial_state_machine.py --ignore=tests/test_suggest_apply_trivial.py
```

| 状态 | pre-req-55 基线 | post-req-55 | 差值 |
|------|----------------|-------------|------|
| PASSED | 803 | 809 | +6 |
| FAILED | 66 | 60 | -6（全为预存，无新增） |
| SKIPPED | 40 | 40 | 0 |

**新引入回归：0 条（PASS）**

pre-req-55 存在但 post-req-55 修复的 6 条（req-55 附带改善）：
包括 test_role_stage_continuity::test_case_a_two_stage_autojump、test_case_c_dynamic_mapping_single_stage、test_req51_project_level_dogfood、test_req52_e2e_log、test_req54_hard_gate_simplify 等 6 条——均属 pre-existing 改善，非本 req 责任引入。

剩余 60 条失败全部来自 pre-req-55 基线（无新增），预存根因为 bugfix-9/13/req-43/req-26/req-28/req-29 等 pre-existing 问题，与 req-55 无关。

### 1.3 workflow_helpers.py 边界 bug 扫描

| 检查点 | 结论 |
|-------|------|
| hash 比对（_file_md5 冲突检测） | PASS：冲突时 src_hash != dst_hash 分支正确；hash 相同走 idempotent 路径；test_conflict_default_warn + test_force_gstack_overrides 双覆盖 |
| 失败回退 | PASS：except Exception → warn + gstack_failures 记录，不阻塞主流程；test_skill_push_failure_does_not_block 验证 |
| agent_kind 分支（non-claude 跳过） | PASS：install_agent 中 agent != "claude" 时 warn + 写 agent_kind_compatible=False；test_install_skips_when_agent_codex 验证 |
| _write_gstack_status 写入 | PASS：try/except 保护，失败仅 warn 不 crash；gstack_failures → gstack_run_log 正确追加 |
| GSTACK_SKILLS_ROOT 不存在 fallback | PASS：early return + warn，不 crash install 主流程 |

---

## 维度 2：文档层测试

### 2.1 chg-02 analyst.md Step A1.5 注入验证

检查 `.workflow/context/roles/analyst.md` Step A1.5 三段是否齐全：

| 段 | 存在 | 关键内容 |
|----|------|---------|
| 触发流程段（Step A1.5） | PASS | 含 agent_kind_compatible 检测 + batched-report 格式 + 暂停等待 path 回传 + 跳转 adapter |
| adapter SOP 段（Step A1.5.adapter） | PASS | startup mode 表（7 源段 → 5 目标段）+ builder mode 差异表 + 缺失段 skip + warn 处理 + harness validate 后置 |
| fallback 段（Step A1.5.fallback） | PASS | 场景 1（agent_kind_compatible=false）+ 场景 2（gstack_status 不存在）+ 场景 3（用户拒跑）全覆盖；fallback 行为：走原生 A1→A3 + batched-report 写入 + 不阻塞 |

### 2.2 role-command-map.yaml YAML schema 验证

```
python3 -c "import yaml; data = yaml.safe_load(open('.workflow/context/integrations/gstack/role-command-map.yaml')); print(data)"
→ {'roles': {'analyst': {'primary_skill': 'office-hours', 'alternates': []}}}
```

**PASS**：合法 YAML，含 1 行 analyst → office-hours 映射 + alternates 空列表（为渐进扩展预留）。

### 2.3 README ≤ 50 行约束

```
wc -l .workflow/context/integrations/gstack/README.md → 36 行
```

**PASS**（36 行 ≤ 50 行约束）

### 2.4 chg-05 retro 模板段 4 子节

检查 `artifacts/project/experience/roles/analyst.md`：

| 子节 | 存在 |
|------|------|
| 1. 调 /office-hours 的姿势 | PASS |
| 2. adapter 章节 mapping 实操细节 | PASS |
| 3. fallback 触发场景 | PASS |
| 4. 多余段处理选择 | PASS |

全部 4 子节齐全，含占位说明和回填说明（"req-56+"为实际触发时替换目标）。PASS。

### 2.5 README 顶层 "Third-party Vendored Skills" 节

检查 `README.md` 第 223 行：含"Third-party Vendored Skills" 节、46 个 skill 完整表格、MIT 归因代码块（含 gstack URL + commit c7aefc1 + 版本时间）、核心 skill 单独点名（office-hours / investigate / qa / review / codex）。**PASS**。

---

## 维度 3：mirror 一致性测试

所有 diff 命令在 working directory 中独立执行：

| live 文件 | scaffold_v2 镜像 | diff 结果 |
|----------|-----------------|----------|
| `.workflow/context/roles/analyst.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` | **无差异（exit 0）** |
| `.workflow/context/integrations/gstack/role-command-map.yaml` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/role-command-map.yaml` | **无差异（exit 0）** |
| `.workflow/context/integrations/gstack/README.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/README.md` | **无差异（exit 0）** |
| `artifacts/project/experience/roles/analyst.md` | `src/harness_workflow/assets/scaffold_v2/artifacts/project/experience/roles/analyst.md` | **无差异（exit 0）** |

**全 4 条 diff 均无输出（ALL_DIFF_CLEAN）**。PASS。

### runtime.yaml schema 字段一致性（gstack_status / gstack_run_log）

| 检查点 | live runtime.yaml | scaffold_v2 runtime.yaml 模板 |
|-------|------------------|-------------------------------|
| gstack_status 键存在 | PASS（注：live runtime.yaml 在执行中，字段写入在 harness install 后；DEFAULT_STATE_RUNTIME 含 gstack_status 4 子字段） | PASS（模板含 gstack_status + 4 子字段 + gstack_run_log） |
| installed_skills 子字段 | PASS | PASS |
| vendor_version 子字段 | PASS | PASS |
| last_install 子字段 | PASS | PASS |
| agent_kind_compatible 子字段 | PASS | PASS |
| gstack_run_log 键存在 | PASS | PASS |

说明：live runtime.yaml 当前处于 testing stage，gstack_status 字段会在下一次 harness install 运行后写入；DEFAULT_STATE_RUNTIME（workflow_helpers.py:80）已含全 4 子字段 + gstack_run_log，scaffold_v2 模板已同步。PASS。

---

## 维度 4：vendor 副本完整性测试

### 4.1 SKILL.md 数量

```
find src/harness_workflow/assets/gstack-skills/ -maxdepth 2 -name SKILL.md | wc -l → 46
```

**PASS（46 个）**。说明：requirement.md 及 AC-01 写"47"为估算近似值；实际 upstream gstack 仓库（commit c7aefc1）有 46 个含 SKILL.md 的 skill 目录，chg-01 session-memory 已留底此默认决策。

### 4.2 _shared 资源完整性

| 子资源 | 存在 | 内容摘要 |
|--------|------|---------|
| `_shared/bin/` | PASS | 59 个文件（含 gstack-update-check / gstack-config 等 SKILL.md 硬编码二进制） |
| `_shared/agents/` | PASS | openai.yaml 等 |
| `_shared/scripts/` | PASS | 30 个文件（analytics.ts / build-app.sh 等） |
| `_shared/LICENSE-gstack` | PASS | 含 "MIT License" |
| `_shared/VERSION-gstack` | PASS | 含 upstream_url + commit c7aefc1 + vendor_timestamp 2026-05-07T13:51:19Z |

### 4.3 VERSION-gstack 内容

```
upstream_url: https://github.com/garrytan/gstack
commit: c7aefc1abd57733848f24ee84b85d691b2973155
vendor_timestamp: 2026-05-07T13:51:19Z
notes: "Vendored by scripts/vendor-gstack.sh into harness-workflow assets."
```

**PASS**：含 upstream URL + commit hash + vendor timestamp。

### 4.4 LICENSE-gstack

```
grep "MIT License" _shared/LICENSE-gstack → "MIT License"
```

**PASS**。

### 4.5 per-skill LICENSE-gstack（install 时注入）

源 skill 目录（vendor 副本）无 per-skill LICENSE-gstack（只含 SKILL.md + VERSION-gstack）。push 到 ~/.claude/skills/ 时，install 逻辑从 _shared/LICENSE-gstack 复制到每个 skill_dir/LICENSE-gstack（workflow_helpers.py:8091-8094）。集成测试 test_license_pushed_to_each_skill 验证此行为通过。PASS。

---

## 维度 5：触发链可行性 paper test

### 5.1 Step A1.5 触发协议（路径 α）逻辑自洽性

| 检查点 | 评估 |
|-------|------|
| gstack_status.agent_kind_compatible 检测入口 | PASS：Step A1.5 第 1 步读取该字段；false 或字段不存在时直接跳 fallback |
| 触发悖论处理（subagent 不能调 slash command） | PASS：路径 α 设计为"analyst 输出 batched-report 给主 agent/用户，提示其调用 /office-hours"；触发悖论明确记录在 README + 本段 |
| 暂停等待逻辑 | PASS：Step A1.5 第 3 步明确"暂停，等主 agent/用户配合完成 /office-hours，把 path 回传" |
| adapter 入口（path 接收后跳转） | PASS：接到 path 后跳到 Step A1.5.adapter，触发重组流程 |

整体触发协议逻辑自洽。PASS。

### 5.2 fallback 覆盖完整性（3 场景）

| 场景 | fallback 处理 | 覆盖 |
|------|-------------|------|
| 场景 1：gstack 未装（agent_kind_compatible=false） | 走原生 A1→A3 + warn | PASS |
| 场景 2：gstack_status 不存在（chg-01 未 ship 或装载失败） | 走原生 A1→A3 + warn | PASS |
| 场景 3：主 agent 拒派发 / 用户拒跑 /office-hours | 走原生 A1→A3 + warn | PASS |

3 场景全部覆盖，fallback 不阻塞 stage 推进。PASS。

### 5.3 chg-05 deferred 承诺合约

| 合约项 | 状态 |
|-------|------|
| deferred 承诺文档化（本 req 周期内仅 Step 1~3） | PASS |
| 触发条件明确（下一个真实 /harness-requirement） | PASS |
| 触发证据预留段（6 字段全存在） | PASS：trigger_req_id / trigger_date / design_doc_path / 触发链耗时 / 卡点摩擦 / retro 四点落地 6 字段齐全 |
| 回填合约 3 项（retro 回填 + chg-05 session-memory 追加 + 该 req session-memory cross-link） | PASS：3 项条件全文档化 |
| "不满足 3 项不视为 chg-05 已兑现"明确声明 | PASS |

chg-05 deferred 合约完整。PASS。

### 5.4 下一个真实 req 的 analyst 自动检测能力

analyst.md Step A1.5 明确"读取 runtime.yaml.gstack_status.agent_kind_compatible"为触发判断点；当 harness install --agent claude 已执行后该字段为 true，analyst 应主动提示用户跑 /office-hours。逻辑完整，可行性评估 PASS。

---

## 维度 6：AC 覆盖度评估

| AC | 描述 | chg 覆盖 | 可验证证据 | 评估 |
|----|------|---------|----------|------|
| AC-01 | vendor 全 skill 落盘（46 目录 + SKILL.md + VERSION-gstack + _shared 三件套） | chg-01 | find SKILL.md = 46；_shared/{bin,agents,scripts,LICENSE-gstack,VERSION-gstack} 齐全 | PASS |
| AC-02 | harness install --agent claude 后 ~/.claude/skills/ 下 46 个 skill + LICENSE-gstack 推送；agent_kind≠claude 跳过 | chg-01 | 集成测试 7/7 通过（包含 test_skills_pushed_to_claude_skills + test_license_pushed_to_each_skill + test_agent_codex_skips_gstack） | PASS |
| AC-03 | analyst.md Step A2 前嵌入 /office-hours 段（触发协议 + adapter + fallback）；role-command-map.yaml 含 1 行映射 | chg-02 | 直接读 analyst.md Step A1.5 三段齐全；yaml.safe_load 验证 role-command-map.yaml 合法含 analyst→office-hours | PASS |
| AC-04 | adapter 完整 mapping 表（startup + builder 两表；多余段 → Office Hours Notes） | chg-02 | analyst.md 含 startup mode 7 源段映射表 + builder mode 差异表 + 多余段处理说明 | PASS |
| AC-05 | chg-05 dogfood 自适用活证（用户跑 /office-hours → design doc → adapter 重组 → requirement.md 覆盖 + retro） | chg-05 | 候选 P 第 8 轮重写：本 req 周期内仅 Step 1~3 落地（retro 预埋 + scaffold mirror + deferred 承诺）；真活证由下一个真实 req 兑现 | CONDITIONAL（设计约束，非缺陷） |
| AC-06 | scaffold_v2 镜像 analyst.md + role-command-map.yaml + README.md 完全一致；harness validate 通过 | chg-04 | diff -q 三条均无输出（ALL_DIFF_CLEAN）；harness validate FAIL 为 pre-existing bugfix-5 引用，非本 chg 引入 | CONDITIONAL（contract FAIL 为 pre-existing） |
| AC-07 | LICENSE-gstack 归因 4 项（vendor 根 + VERSION-gstack + README 节 + 推送时 LICENSE 副本） | chg-01 | LICENSE-gstack MIT 字样确认；VERSION-gstack 含 URL+hash；README "Third-party vendored skills" 节齐全；push 时 per-skill LICENSE-gstack 注入验证通过 | PASS |
| AC-08 | runtime.yaml.gstack_status 4 子字段；schema 加入 .workflow 校验；装载失败回退 warn + gstack_run_log | chg-01 | DEFAULT_STATE_RUNTIME 含 4 子字段；scaffold_v2 模板含 gstack_status + gstack_run_log；test_runtime_yaml_gstack_status 通过；装载失败回退测试通过 | PASS |

**8 条 AC 中 6 条 PASS，2 条 CONDITIONAL（AC-05 为 deferred 设计约束，AC-06 为 pre-existing contract FAIL）**。

---

## 维度 7：契约 lint

### 7.1 harness validate --contract role-stage-continuity

```
FAIL: role-stage-continuity lint — 以下话术向用户暴露无用户决策点的 stage 转换...
  .workflow/flow/bugfixes/bugfix-5-.../session-memory.md:25: target_stage=planning
  .workflow/flow/bugfixes/bugfix-5-.../session-memory.md:509: target_stage=acceptance
  .workflow/flow/bugfixes/bugfix-5-.../session-memory.md:511: target_stage=done
```

**pre-existing 确认**：git log 显示 bugfix-5 session-memory 最后修改于 commit 205c132（"fix: bugfix-6 工作流契约统一加固"），早于 req-55 任何改动。本报告通过 git stash → 基线运行验证：pre-req-55 状态下同一命令结果完全相同，失败来自 bugfix-5 历史内容。

**本 req 引入新违规：0 条**。PASS（非本 req 责任）。

### 7.2 harness validate --contract triggers

执行结果：无输出（exit 0）。PASS。

### 7.3 契约 7 id-title 合规扫描

扫描 req-55 新建文档中 id 引用的 title 注解情况：

- 核心 change.md 文件：chg-01 change.md 第 14 行含 `[req-55:gstack-harness 融合开荒]`——带 title 标注。PASS。
- requirement.md 中 req-56~59 作为路标出现在表格单元格（非"首次出现于对人汇报"语境）。按契约 7 范围解释，机器型文件内的规划路标不属于"对人汇报 id"约束范围。INFO（不计 FAIL）。
- analyst.md 改造段中 `[req-55:gstack-harness 融合] chg-02 落地` 含 title 标注。PASS。

总体契约 7 扫描：主要 id 引用含 title，无明显漏注。PASS。

---

## 发现的问题

### BLOCKER 级
无。

### WARN 级

| # | 问题 | 描述 | 影响 |
|---|------|------|------|
| W-01 | AC-01 "三件套"描述与实际 vendor 副本不一致 | requirement.md AC-01 写"每目录至少 SKILL.md + LICENSE-gstack + VERSION-gstack 三件套"，但 vendor 副本中 skill 目录实际只有 SKILL.md + VERSION-gstack（无 per-skill LICENSE-gstack）；per-skill LICENSE-gstack 在 push 时从 _shared 注入。 | 描述不精确，实现行为正确（测试验证），用户读 AC-01 会产生误解 |
| W-02 | AC-01 / AC-07 skill 数量描述"47"与实际"46"不符 | requirement.md 多处写"47 个 skill"，实际 upstream 在 commit c7aefc1 有 46 个含 SKILL.md 的 skill 目录。chg-01 session-memory 已留底此 default-pick，但 requirement.md / AC 文本未更新。 | 不影响功能，但影响 AC 严格核查时的数字一致性 |
| W-03 | AC-05 dogfood 活证 deferred（不阻塞本 req，但非完全 PASS） | chg-05 真活证由下一个真实 req（req-56+）兑现；本 req 周期内仅完成 Step 1~3（retro 模板预埋 + scaffold mirror + deferred 承诺）。acceptance 阶段应关注 deferred 合约 3 项是否在 req-56 中得到兑现。 | 按 chg-05 第 8 轮重写设计约束，非缺陷；但构成 CONDITIONAL |
| W-04 | AC-06 harness validate --contract role-stage-continuity pre-existing FAIL | 该合约失败来自 bugfix-5 session-memory 历史文本（205c132），与本 req 无关；但 AC-06 明写"harness validate --contract role-stage-continuity 通过"，实际无法在当前状态通过 | pre-existing，建议后续 bugfix 修复 bugfix-5 引用问题以清洁该 lint |

### INFO 级

| # | 问题 | 描述 |
|---|------|------|
| I-01 | 5 个 test_trivial_*.py 文件预存 ImportError | tests/test_create_trivial.py 等 5 个文件 import `create_trivial` / `classify_diff_change_types` 等不存在的函数，git log 显示这些文件早于 req-55，属 pre-existing。 |
| I-02 | test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops 为预存失败 | 该测试于 pre-req-55 基线就已失败（独立比对确认），与 req-55 无关。 |

---

## 结论

- **总体判定：CONDITIONAL**

**理由：**

代码层测试全通过（15/15 专项用例 PASS，0 新引入回归），文档层测试满足（Step A1.5 三段齐全、YAML 合法、README ≤ 50 行），mirror 一致性全 PASS（4 条 diff 均无输出），vendor 副本结构完整（46 SKILL.md + _shared 全件），触发链逻辑自洽（3 场景 fallback 全覆盖 + deferred 合约 3 项齐全）。

CONDITIONAL 原因：
1. **AC-05 dogfood 活证 deferred**（设计约束，非缺陷）：真活证需等下一个真实 req（req-56+）触发时由其 analyst 兑现；当前仅 Step 1~3 落地（retro 预埋 + scaffold mirror + 承诺合约）。
2. **AC-06 harness validate pre-existing FAIL**：该 FAIL 来自 bugfix-5 session-memory 历史文本，非本 req 引入；但 AC-06 原文写"harness validate 通过"——在 pre-existing 问题解决前无法严格满足该 AC 字面表述。

无 BLOCKER 级问题。全部 W 级问题均为已知预存或设计约束。

**推荐：推进 acceptance 进一步评估**

acceptance 阶段注意事项：
1. 确认 AC-01 / AC-07 skill 数量描述不一致（47 vs 46）是否需要在 requirement.md 中修正说明；
2. 核查 AC-06 pre-existing lint FAIL 是否在验收基线豁免范围内（chg-04 session-memory 已确认为预存，acceptance 可延续此判断）；
3. AC-05 deferred 合约以"下一个真实 req 兑现"为验收门，acceptance 阶段可标记为"接受 + 后续 req-56 验证"。
