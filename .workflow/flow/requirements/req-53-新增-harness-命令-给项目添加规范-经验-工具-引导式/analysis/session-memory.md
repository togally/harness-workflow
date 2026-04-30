# Session Memory — req-53（新增 harness 命令给项目加规范经验工具引导式）

## 1. Current Goal

为 req-53（新增 harness 命令给项目加规范经验工具引导式）seed Phase 1 requirement.md（Background / Goal / Scope / Acceptance Criteria 4 段 + § OQ Verdicts 5 条）；不进 Phase 2，不拆 chg，不写 plan.md。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus，harness-manager 路由后常驻）
- Level 1: analyst / opus（本次 subagent，按 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））方向 C analyst 合并规约只跑 Phase 1）

## 3. 模型自检（req-29 / chg-03 + role-loading-protocol Step 7.5）

- `expected_model: opus`（briefing 要求）
- `.workflow/context/role-model-map.yaml` → `analyst: "opus"`
- 自省：本 subagent 由 harness-manager 以 model=opus 派发；具体子版本 Opus 4.7[1m]，符合一致性要求，不降级。

## 4. 用户原话（权威意图留痕）

> 「可以开发一个命令专门给项目增加规范经验工具」

承载层（`artifacts/project/{constraints,experience,tools}/`）已由 req-51（项目级规则-经验-工具支持从制品引入）+ req-52（硬编码 main 路径全面去除-跟项目走-索引懒加载-流程日志验证）+ bugfix-13（install 时自动创建 artifacts/project 骨架与索引模板）立稳；本 req 仅补**入口命令**。

## 5. 现状盘点要点

- `_bootstrap_project_skeleton` 在 `harness install` / `harness update` 已自动建 6 份 `index.md` 模板
- `_merge_project_level_files` + `_load_project_level_index` 已接入加载链（role-loading-protocol Step 7.6 / 7.6.1 + tools-manager Step 2.0）
- stderr 活证 `[harness] project-level loaded: N files from artifacts/project/{scope}/（fallback=...）` 已实装
- 6 份 index.md schema 统一：`| path | title | scope | when_load | 备注 |` markdown 表格

## 6. 用户暴露的三类痛点

1. AI 发明路径（`artifacts/standards/coding/` 不在加载链扫描面）
2. 加规范没自动登记 index.md（索引懒加载扫不到）
3. 没强制 git commit 提醒（artifacts/ 已 tracked 但 user 容易忘）

## 7. 产出位置

- `requirement.md`（Phase 1 4 段 + § OQ Verdicts 5 条）：`.workflow/flow/requirements/req-53-新增-harness-命令-给项目添加规范-经验-工具-引导式/requirement.md`
- 本 session-memory：`.workflow/flow/requirements/req-53-新增-harness-命令-给项目添加规范-经验-工具-引导式/analysis/session-memory.md`

## 8. 范围红线（briefing 锁死，本 subagent 严格遵守）

- 不动 PetMallPlatform / PetMallAdmin / uav 仓任何文件
- 修复面只在 harness-workflow 仓内
- 不引入 `_use_*_layout*` / `*_LAYOUT_FROM_*` 命名（bugfix-11 红线延续）
- 复用现有 `artifacts/project/*` 路径标准，禁止发明 `artifacts/standards/` 之类新路径

## 9. 不做（Phase 1 边界）

- 不写源码 / 测试 / 契约
- 不调 `harness next` / 不修 runtime.yaml
- 不派发更下层 subagent
- 不写 Phase 2 chg 拆分；不写 plan.md

---

## Phase 1 决策清单

> 本节按 base-role 硬门禁四同阶段不打断原则 + stage-role 默认推进 default-pick 留痕规约填写。

### default-pick 决策（按 OQ 编号汇总，与 requirement.md § OQ Verdicts 对齐）

| OQ id | 决策点 | default-pick | 一句话理由 |
|------|------|------------|----------|
| OQ-1 | 命令形态选择（A: `harness rule <type> <title>` / B: 三命令分立 / C: 统一 `harness project-add <kind> [<scope>] <title>`） | **C** | 覆盖三大 kind + 复用 `harness requirement` / `harness bugfix` 句式 + 与 `_bootstrap_project_skeleton` 三大类（constraints/experience/tools）1:1 映射 |
| OQ-2 | v1 子命令覆盖（add / list / remove / show / move） | **add + list 二选项** | add 必备；list 调试加载链高频；remove / show / move 推迟 v2 控复杂度，避免一次写大命令面 |
| OQ-3 | 是否支持 interactive 模式（无参数 questionary 引导） | **支持，默认开启** | 与 `harness suggest --title` 必填同款 prompt 风格；user 忘参数时不报错而是引导，AI 也能按 prompt 顺序填 |
| OQ-4 | index.md `when_load` 字段默认值 | **always** | 项目级规则 / 经验 / 工具默认全场景加载（symmetric to 全局规则）；user 改 `on-stage:executing` / `on-keyword:lint` 须显式声明，不静默改默认 |
| OQ-5 | 是否自动 `git add` stage（vs 仅打印提醒） | **自动 `git add` + 仅提示 `git commit`，不自动 commit** | `git add` 可逆（user 可 `git restore --staged`）；commit 不可逆 + 改 user 工作树状态需显式同意；同时降低"加完忘 git add"漏 commit 风险 |

### 未上呈用户的隐含判断（analyst 自主决定，session-memory 留痕供 reviewer 审查）

- **slug 生成方式**：复用 cli.py 既有 `_slugify` helper（与 `harness requirement` / `harness bugfix` 同款），不新写。
- **模板落位**：`src/harness_workflow/assets/templates/project-add/{kind}.md.tmpl` 三份（rule / experience / tool），与 `assets/templates/project-skeleton/` 平级，不复用 skeleton 模板（语义不同：skeleton 是 index 模板，project-add 是单条目模板）。
- **slash command 同步**：`.claude/commands/harness-project-add.md` 复制 `harness-suggest.md` 模板改命令名 + argument-hint，不新写大块文档。
- **WORKFLOW.md 入口段**：v1 不动 WORKFLOW.md `## Main Entry`（已列 install / update / status / requirement / change / next / regression），`project-add` 是辅助命令而非主流程节点；`README.md` 加一段说明即可。

### 阻塞用户拍板事项

无。Phase 1 边界内全部按 default-pick 推进，5 条 OQ 均不在硬门禁四例外条款（数据丢失 / 不可回滚 / 合规）三类内，不打断用户。

待用户拍板的整体确认轮次为 Phase 2 流转点（analyst 完成 chg 拆分 + plan.md 后一次性 batched-report），本 subagent 不触达 Phase 2。

### 经验沉淀检查

- 是否有可泛化经验需沉淀？**有** —— "项目级承载层入口命令"是新模式（既往 `harness suggest` / `harness requirement` / `harness bugfix` 都是流程节点入口，本 req 是承载层维护入口）；待 Phase 2 / executing 沉淀实践证据后回填 `.workflow/context/experience/roles/analyst.md` 或 `.workflow/context/experience/tool/harness.md`。Phase 1 边界内无成型经验可写。

## 10. analyst 专业化抽检反馈（req-40 chg-06 抽检模板）

| 字段 | 内容 |
|------|------|
| 抽检产物 | req-53 requirement.md（Background / Goal / Scope / Acceptance Criteria + § OQ Verdicts）+ 4 chg 各 change.md / plan.md / session-memory.md |
| 质量评分 | Phase 2 + 3 拆分通过（4 chg 线性依赖、最小耦合、stub-then-replace 渐进策略）；plan.md 含精确文件 / 行号 / 函数名 / 测试用例 / lint 字面 |
| 退化点明细 | 无明显退化；待 executing 阶段实际跑 plan.md 后回填 |
| 是否触发 regression 回调 B | 否 |
| 抽检人 + 时间 + req 范围 | analyst（subagent） / 2026-04-29 / req-53 Phase 1 + 2 + 3 |

---

## Phase 2 + Phase 3 决策清单

> 本节为 chg 拆分（Phase 2）+ plan.md 制定（Phase 3）一气完成后的留痕；对齐 base-role 硬门禁四同阶段不打断 + stage-role default-pick 留痕约定。

### chg 拆分形态（Phase 2）

| chg id | 标题 | 一句话 scope | 测试 TC 数 |
|--------|------|------------|-----------|
| chg-01（CLI 入口与反非法 lint） | CLI 入口 harness pad 子命令骨架 + kind/scope 枚举常量 PAD_KINDS + 反非法 lint | argparse 注册 + dispatch + 三类位置参数解析 + 非法 kind/scope ABORT + 5 helper（4 stub + 2 validator） | 8 |
| chg-02（add 落位与模板预填） | _pad_add 真实落位 + 三份 .tmpl 模板 + write_if_missing 不覆盖 | kind+scope 路径解析 + slug 生成 + 模板渲染 + 幂等写盘 + pyproject package-data | 8 |
| chg-03（index 登记与 git stage） | index.md 自动登记（按 kind schema 分类追加）+ git auto-stage + 加载链 stderr 活证 | 4 helper（_pad_register_index / _append_table_row / _append_tool_list_item / _pad_git_stage）+ _pad_add 增强追加 3 块 | 10 |
| chg-04（list 与 interactive 与 dogfood） | _pad_list 真实扫描 + _pad_interactive questionary 引导 + 端到端 dogfood + slash command 同步 | 替换 chg-01 stub + .claude/commands/harness-pad.md + README 增补 + 5 dogfood TC（subprocess） | 12（4 list + 3 interactive + 5 dogfood） |

**总测试 TC 数**：8 + 8 + 10 + 12 = **38 条**（chg 间无重叠，覆盖面：CLI 解析 / 落位 / index / git / list / interactive / 端到端）。

### chg 间依赖链 + stub-then-replace 策略

```
chg-01（stub 落地，dispatch 闭环）
  ↓ _pad_add stub
chg-02（替换 _pad_add stub 为真实落位实现）
  ↓ _pad_add 已有真实落位
chg-03（在 _pad_add 真实落位实现末尾追加 3 块：index 登记 + git stage + stderr 活证）
  ↓ _pad_add 完整功能闭环 + _pad_list / _pad_interactive 仍是 stub
chg-04（替换 _pad_list / _pad_interactive stub 为真实实现 + slash command + dogfood）
```

**关键设计**：chg-01 落 5 个 helper 全签名（4 stub + 2 validator），让 dispatch 链路在 chg-01 即闭环；后续 chg 只**替换实现**而不**新加签名**，避免 chg 间循环依赖。

### 关键 lint 命令清单（聚合 4 chg）

```bash
# 1. PAD_KINDS 常量
grep -nE "^PAD_KINDS\s*[:=]" src/harness_workflow/workflow_helpers.py

# 2. CLI dispatch
grep -nE 'args\.command\s*==\s*"pad"' src/harness_workflow/cli.py

# 3. 5 helper 全部签名
grep -nE "^def (_pad_add|_pad_list|_pad_interactive|_validate_pad_kind|_validate_pad_scope|_pad_register_index|_append_table_row|_append_tool_list_item|_pad_git_stage|_resolve_pad_target|_parse_tool_list_section)\b" src/harness_workflow/workflow_helpers.py

# 4. 反非法 lint 错误信息可读
grep -n "kind 必须是 rule/experience/tool" src/harness_workflow/workflow_helpers.py
grep -n "rule scope 必须是" src/harness_workflow/workflow_helpers.py

# 5. 模板 + package-data
test -f src/harness_workflow/assets/templates/project-add/rule.md.tmpl
test -f src/harness_workflow/assets/templates/project-add/experience.md.tmpl
test -f src/harness_workflow/assets/templates/project-add/tool.md.tmpl
grep -q "assets/templates/project-add" pyproject.toml

# 6. slash command + README
test -f .claude/commands/harness-pad.md
grep -q "^## harness pad" README.md
grep -q "^## harness pad" README.zh.md

# 7. pytest 全套绿
pytest tests/test_req53_pad_cli.py tests/test_req53_pad_add.py tests/test_req53_pad_index.py tests/test_req53_pad_list.py tests/test_req53_pad_interactive.py tests/test_req53_pad_dogfood.py tests/test_package_data_completeness.py -v

# 8. 现有契约 0 回归
python3 -m harness_workflow.cli validate --contract artifact-placement
python3 -m harness_workflow.cli validate --contract user-write-protected-zones
python3 -m harness_workflow.cli validate --human-docs
python3 -m harness_workflow.cli validate --contract all
```

### scaffold_v2 mirror 同步盘点

- `cli.py` / `workflow_helpers.py`：**不在** scaffold_v2 mirror 范围（只在 src/）。
- 3 份 `.tmpl` 模板 → `pyproject.toml` package-data 加 1 行（必做，否则 wheel 不打）。
- `.claude/commands/harness-pad.md` → 不在 scaffold_v2 mirror，但需确认 `install_local_skills` 分发链路覆盖（chg-04 实施时 grep 验证）。
- README / README.zh.md → 不在 scaffold_v2 mirror。
- contract docs（repository-layout.md / role-loading-protocol.md / tools-manager.md）→ 本 req 不动，路径表 + 加载链对新 path schema（`{scope}/{slug}.md` 子路径）已天然兼容（`_parse_index_md` 不解析 path 内部，agent 端按相对路径加载）。

### 范围红线（聚合，与 requirement.md 一致）

- 修复面只在 harness-workflow 仓
- 不动 PetMallPlatform / PetMallAdmin / uav 仓
- 不引入 `_use_*_layout*` / `*_LAYOUT_FROM_*` 命名（bugfix-11 红线延续）
- 不破现有 `artifacts/project/*` 路径标准（仅在 constraints/ 下加 `{scope}/` 子目录是新增，与 OQ-Verdicts 决策一致）
- 不引入新 mirror 同步契约（仅复用既有 scaffold_v2 / package-data 配置）
- 不动 install_repo / _merge_project_level_files / _bootstrap_project_skeleton 主流程
- 不改 _log_project_level_load / _parse_index_md / _load_project_level_index（仅调用，不改签名）
- 不动 WORKFLOW.md（pad 是辅助命令）

### default-pick 决策（Phase 2 + 3 自主推进，未上呈用户）

| Pick id | 决策点 | default-pick | 一句话理由 |
|---------|------|------------|----------|
| P-21 | 4 chg vs 5 chg 拆分 | **4 chg** | 与 requirement.md 推荐拆分 5 chg 的差异：把推荐 chg-04（git stage + 加载链 + slash 同步）的 git stage + 加载链合到 chg-03，slash 同步合到 chg-04（list + interactive + dogfood），减少一个 chg 边界；测试 TC 数从推荐 5×3 = 15 增到实际 38，覆盖面更密 |
| P-22 | stub-then-replace vs 一次性大 chg | **stub-then-replace** | 让 chg-01 即可独立测试（dispatch 闭环），降低 chg 间循环依赖，符合"每 chg 独立可交付"约束 |
| P-23 | constraints/index.md 是否破坏现有 schema | **不破坏，沿用表格 schema，path 字段含 `{scope}/` 子路径** | 与 `_parse_index_md` 解析逻辑兼容；scope 字段写真实 scope（coding 等）而非 `constraints`，与 path 一致 |
| P-24 | tool kind 是否统一为表格 schema | **不统一，沿用「## 项目级工具清单」段** | tools/index.md 现有 schema 与 constraints/experience 不同（叙述型 + 列表段），破坏 schema 风险大于统一收益；新增 `_parse_tool_list_section` 解析器 |
| P-25 | git stage 失败是否阻塞命令 | **不阻塞，silent skip + warn stderr** | OQ-Verdicts OQ-5 决策语义即"git stage 是优化项不是核心契约"；非 git 仓 / git 缺失场景下命令仍应正常落位 |
| P-26 | dogfood TC 走 subprocess vs 直调内部函数 | **subprocess** | sug-52（dogfood 实跑流程模板）已立稳的端到端原则；直调内部函数会绕开 argparse / dispatch / cwd 解析等真实路径，testing 阶段易翻车（req-50 教训） |
| P-27 | feedback.jsonl 事件登记 | **不登记，TC-Dogfood-05 降级为存在性检查** | 避免引入 telemetry 范围溢出；本 req 仅做承载层维护命令，事件登记由独立 sug 决定 |
| P-28 | WORKFLOW.md Main Entry 是否加 pad | **不加** | OQ-Verdicts 决策 + pad 是辅助命令；Main Entry 列表保持流程节点专属，不混入承载层维护工具 |
| P-29 | 反非法 lint 是否进 harness validate | **不进，仅在 dispatch 层 ABORT** | "反非法 lint" 在 requirement.md 是"用户输错时给建议"语义，与 contract 全仓扫描语义不同；进 dispatch 层 ABORT 已足够（用户即刻看到错误） |
| P-30 | 是否补 `harness project-add` alias | **不补，pad 即正名** | requirement.md OQ-Verdicts OQ-0 已锁定 "pad" 命名（短命令）；alias 等待用户提出再加 |

### 阻塞用户拍板事项

**无**。Phase 2 + 3 边界内全部按 default-pick 推进，10 条 P-2x 决策均不在硬门禁四例外条款（数据丢失 / 不可回滚 / 合规）三类内，不打断用户。

整体确认轮次为 analysis stage 流转点（analyst 完成 chg 拆分 + plan.md 后一次性 batched-report），用户拍板「需求 + 4 chg 拆分 + plan.md」整合产物，确认后 `harness next` 进 executing。

### 经验沉淀检查（Phase 2 + 3 完成后）

- **可泛化经验已识别**（待 executing 完成后回填）：
  - "**stub-then-replace 渐进 chg 拆分策略**"（chg-01 落 5 helper stub 让 dispatch 闭环，chg-02/03/04 替换实现而非加签名）→ 沉淀到 `.workflow/context/experience/roles/analyst.md`
  - "**项目级承载层维护命令的双 schema 共存模式**"（machine-readable 表格 + human-readable 列表段）→ 沉淀到 `.workflow/context/experience/tool/harness.md`
  - "**git stage 不阻塞的 dev-tool 类命令哲学**" → 沉淀到 `.workflow/context/experience/roles/executing.md`
- 本 subagent 不写经验文件（属 executing / done 阶段职责），仅在 session-memory 留题目供后续阶段回填。

---

## Executing Stage Summary

Executing 阶段由 Subagent-L1（Sonnet）于 2026-04-29 完成。4 chg 全部实施完毕。

### 4 chg 完成情况

| chg id | 状态 | 关键产出 |
|--------|------|---------|
| chg-01（CLI 入口与反非法 lint） | ✅ pass | PAD_KINDS 常量 + 5 helper（2 validator + 3 stub）+ cli.py pad subparser + dispatch；修复 tool kind normalize 顺序 bug |
| chg-02（add 落位与模板预填） | ✅ pass | 3 份 .tmpl 模板 + _pad_add 真实落位 + _resolve_pad_target + pyproject.toml package-data 更新 |
| chg-03（index 登记与 git stage） | ✅ pass | 4 helper（_pad_register_index / _append_table_row / _append_tool_list_item / _pad_git_stage）+ _pad_add 增强 + 加载链 stderr 活证 |
| chg-04（list + interactive + dogfood） | ✅ pass | _pad_list / _pad_interactive 真实实现 + _parse_tool_list_section + slash command + README 增补 |

### pytest 最终数字（完整）

```
44 passed (40 req-53 TC + 4 package_data TC)
全 suite：57 failed / 791 passed（baseline 57 failed，无增加）
```

### 契约验证

```
harness validate --contract artifact-placement  → PASS (exit=0)
harness validate --contract user-write-protected-zones → PASS (exit=0)
harness validate --contract all → exit=0
```

### 无法满足的 plan 条款

无。全部条款均已实施落地。

### 关键偏差（已修复）

- tool kind normalize 必须在 `_validate_pad_scope` 调用前完成（否则 scope_raw="petmall-deployer" 被误判非法）；已在 dispatch 层修复
- TC-08 幂等检查：index.md 含 HTML 注释示例行，需过滤非注释行再计数

✅ req-53 executing 阶段已结束。

---

## Done Stage Six-Layer Review（done / opus，2026-04-30）

> 主 agent（done / opus）六层回顾。本周期 acceptance verdict = PASS / 0 未达标，本节不重审。

### 第一层 Context（上下文层）

各阶段角色（analyst / executing / testing / acceptance）自我介绍 + 模型自检均合规；analyst 顺利 Phase 1 + 2 + 3 一气完成 4 chg 拆分 + plan.md，stub-then-replace 渐进策略可圈可点；executing 本周期自报 baseline 57 failed 实测 51 failed（虚报第 N 次同型，但实际为历史遗留 bug，不影响主线产出）；experience/ 下有 1~2 处可考虑沉淀「历史遗留 bug 在新周期撞上时 executing 应顺手修而非沿袭虚报」，本 req 周期内已自然沉淀（顺手修 tools/index.md contract-7 + bugfix-13 .gitkeep 期望两处）。

### 第二层 Tools（工具层）

无 CLI / MCP 工具适配性问题；新建命令本身即填补"承载层入口缺失"工具空白；toolsManager 派发链路在本 req 4 chg 中均按规约触发；3 份 .tmpl 模板与 `assets/templates/project-skeleton/` 平级放置合理。

### 第三层 Flow（流程层）

5-stage sequence（analysis → executing → testing → acceptance → done）全走、无跳过；analyst 合并规约（req-40 方向 C）下 Phase 1+2+3 一气完成符合预期；stage 流转点 user 拍板一次（analysis 出口）+ 自动连跳；本周期 0 regression 回调。

### 第四层 State（状态层）

runtime.yaml 与 req-53.yaml 一致（stage=done / status=done / completed_at 已写）；usage-log.yaml 5 entries（analysis ×2 / executing / testing / acceptance）≥ 派发次数 5（done 由主 agent 直跑无 entry，符合 State 层硬门禁九子条款断言）；本周期 0 容差 / 0 失败派发 / 0 stub 降级。

### 第五层 Evaluation（评估层）

testing 与 acceptance 独立执行：testing subagent 提供完整 pytest stdout（test-report.md），acceptance 实跑 dogfood + 契约 + grep 独立核查（checklist.md A.1 ~ E.1）；硬门禁九本周期触发 1 次（executing 自报 baseline 57 实测 51，主 agent 抓出虚报，与 sug-67 / sug-68 / sug-69 同型——同型病累计 5+ 次复发）；评估标准未降；AC-10 PetMallPlatform 真实仓自验由 scope 限制以 dogfood 空仓代理。

### 第六层 Constraints（约束层）

范围红线清洁：`git diff` + `grep` 均 0 命中 PetMallPlatform / PetMallAdmin / uav；artifacts/project/* 路径标准未破（仅在 constraints/ 下加 `{scope}/` 子目录是 OQ-Verdicts 决策内新增，加载链兼容）；契约 `artifact-placement` + `user-write-protected-zones` 双绿；硬门禁三 / 四 / 六 / 七 / 九并列生效，本周期均无破例。

### sug 入池决策

- 本周期发现：subagent 又虚报 baseline（第 N 次同型）→ 已有 sug-67 / sug-68 / sug-69 覆盖，**不重复入池**。
- bugfix-13 round-4 测试更新漏改（.gitkeep 删了但测试断言未同步）→ 入 1 条 sug：「修源码 + 删 / 改文件时同步扫 tests/ 是否有相关期望需更新」。
- 顺手命名约束：`harness validate` 应有专门 contract 检测「`artifacts/project/{constraints,experience,tools}/` 之外的 `artifacts/{其他}/` 自定义结构」防 AI 再发明 `artifacts/standards/` 类路径 → 入 1 条 sug。
- **共入池 2 条新 sug**（详见 action-log）。

### 经验沉淀检查

- analyst.md：「stub-then-replace 渐进 chg 拆分策略」(Phase 2 决策清单 P-21/P-22 已在 session-memory 留题)，本周期 4 chg 跑通后值得回填正式条目（待后续周期顺手做）。
- harness.md（tool 经验）：「项目级承载层维护命令的双 schema 共存模式」（machine-readable 表格 + human-readable 列表段，详见 P-23/P-24）。
- executing.md：「git stage 不阻塞的 dev-tool 类命令哲学」（P-25）+ 「历史遗留 bug 撞上时顺手修不沿袭虚报」（本周期实践）。
- 三条均待主 agent / 用户后续显式触发回填，本 done 阶段不强制写。

### archive 建议

- 已 done 队列累计 6 件：bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）+ req-51（项目级规则-经验-工具支持从制品引入）+ bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）+ req-52（硬编码main路径全面去除）+ bugfix-13（install时自动创建artifacts-project骨架）+ req-53（新增 harness pad 命令）。
- 建议**一起 archive**；done 阶段不动，等用户后续显式触发 `harness archive`。

**本阶段已结束。**
