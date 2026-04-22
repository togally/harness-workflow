# Session Memory · bugfix-3 · regression Subagent-L1

## 1. Current Goal

- 对 bugfix-3 的两条独立用户报告做只读独立诊断：
  1. install/update 仅应更新"当前选定 agent"
  2. `.harness/feedback.jsonl` 落位错误
- 产出 diagnosis.md / 回归简报.md / required-inputs.md
- 给出综合路由决策

## 2. Context Chain

- Level 0: 主 agent (harness-manager) — 创建 bugfix-3
- Level 1: 我 (regression Subagent-L1) — 独立诊断

## 3. Completed Tasks

- [x] 硬门禁三：自我介绍
- [x] 角色文件加载（runtime / tools/index / project-overview / base-role / stage-role / regression / evaluation/regression）
- [x] 加载 regression 经验文件 + bugfix-3 yaml + bugfix.md
- [x] 问题 1 证据收集：CLI 路由 → install_agent → update_repo → install_local_skills → _project_skill_targets → _managed_file_contents
- [x] 问题 1 状态层字段盘点：runtime.yaml / platforms.yaml / config.json 全部确认无 active_agent
- [x] 问题 2 证据收集：record_feedback_event 5 个调用点 / harness_export_feedback.py 消费链 / FEEDBACK_DIR 常量
- [x] 问题 2 与 stage_timestamps 字段对比：维度互补不重复
- [x] 衍生发现：bugfix-3 ID 复用 4 次（archive 未扫）
- [x] diagnosis.md 完整产出
- [x] 回归简报.md（对人 ≤ 1 页）产出
- [x] required-inputs.md 更新（标注无硬阻塞 + 4 个开放问题）

## 4. Results

### 路由决策

**`harness regression --confirm` → `testing`**

两条问题都是真实的实现/工程缺陷，共享 `update_repo` 代码段，应一并修复 + 补 ≥3 个 TDD 用例。

### 关键根因

- 问题 1：状态层缺 `active_agent` 字段；`update_repo` / `_managed_file_contents` 不感知用户实际使用的 agent
- 问题 2：`FEEDBACK_DIR = Path(".harness")` 常量早于六层架构成型，从未被纳入 `.workflow/` 统一归位

### 关键修复点（供 testing/executing 评估）

1. `workflow_helpers.py:136-137` 改 FEEDBACK_DIR → `.workflow/state/feedback/`
2. `workflow_helpers.py:2120-2139` 让 `_managed_file_contents` 接收 `active_agent`，按 agent 写入
3. `workflow_helpers.py:1989-2002` 让 `_project_skill_targets` 优先读 `active_agent`，回退 enabled[]
4. `workflow_helpers.py:5116+` 让 `install_agent` 末尾持久化 `active_agent`
5. `tools/harness_update.py` 增 `--agent` / `--all-platforms` 参数
6. `tools/harness_export_feedback.py:20` 同步路径
7. `update_repo` 加一次性迁移：`.harness/feedback.jsonl` → `.workflow/state/feedback/feedback.jsonl`
8. 文档同步：`assets/scaffold_v2/.workflow/context/roles/harness-manager.md:537` + `assets/scaffold_v2/.workflow/tools/catalog/harness-export-feedback.md:8`

## 5. Validated Approaches

- 通过 `git ls-files .harness/` 确认 `.harness/feedback.jsonl` 是被跟踪的真实数据，不可直接 rm
- 通过 grep `record_feedback_event` 找到 5 个写入点 + 1 个消费点，闭环完整
- 通过 grep `active_agent|selected_agent|current_agent` 在整个仓库无命中，确认状态层无现存字段
- 通过对比 `stage_timestamps`（per-requirement 单点）vs `feedback.jsonl`（cross-requirement 流水），确认两者维度互补，feedback 不能并入 stage_timestamps

## 6. Failed Paths

- 无失败路径，诊断单次跑通

## 7. Open Questions（已写入 required-inputs.md，testing 阶段决策）

- Q1 历史 feedback.jsonl 是否保留迁移
- Q2 update 是否提供 `--all-platforms` escape hatch
- Q3 `platforms.yaml.enabled[]` 是否保留
- Q4 bugfix-3 ID 复用是否一起修

## 8. Candidate Lessons（可沉淀到 context/experience/roles/regression.md）

```markdown
### [2026-04-20] 双独立报告共修复路径时优先合并路由
- Symptom: bugfix-3 两条独立用户报告（install agent 作用域 + feedback.jsonl 落层）看似可拆
- Cause: 二者修复都集中在 update_repo + workflow_helpers.py 同一函数族
- Fix: 拆分会引入合并冲突；单一 testing 路由 + 一次 TDD 补 ≥3 用例 + 一次 executing 实施
- 经验：诊断阶段判断"是否合并路由"的标准不是"用户描述是否同源"，而是"修复触达的代码段是否重叠"
```

```markdown
### [2026-04-20] 残留路径常量是六层架构落地的常见盲点
- Symptom: .harness/feedback.jsonl 在 .workflow/ 体系外独立存在
- Cause: FEEDBACK_DIR 常量早于六层架构成型，常量化导致后续重构成本高
- Fix: 用一次性迁移 + 常量改写 + 文档同步三步搬家
- 经验：诊断"路径不规范"问题时，先查"该路径是否被常量化"——常量化的路径迁移成本远低于散布的字面值
```

## 9. Next Steps

- 主 agent 接收回归简报 → 决定是否 `harness regression --confirm` → testing
- testing subagent 读 diagnosis.md + required-inputs.md → 拆 plan / 写 ≥3 个 TDD 用例
- executing subagent 按 plan 落地 8 个修复点（含一次性数据迁移）

## 10. 上下文消耗评估

- 文件读取：约 12 个（runtime / tools/index / project-overview / base/stage/regression role / evaluation/regression / regression 经验 / bugfix-3 yaml + md / platforms.yaml / runtime.yaml + PetMall / 多段 workflow_helpers.py / harness_export_feedback.py / harness_install.py / harness_update.py / cli.py 多段）
- 工具调用：约 25 次（含 grep / glob / bash ls / read）
- 大文件读取：workflow_helpers.py 共读 ~700 行（分段）
- 评估：约 50% 上下文，无需 /compact

---

# Session Memory · bugfix-3 · executing Subagent-L1（2026-04-20 ff 模式）

## 1. Current Goal
- 按 A/A/A/A 用户选择，一次性落地 bugfix-3 两条独立问题：
  1. install/update 仅刷新当前 active agent（新增 `platforms.yaml.active_agent` 字段 + 链路改造）
  2. `.harness/feedback.jsonl` 落层归位到 `.workflow/state/feedback/feedback.jsonl`（+ 一次性数据迁移）

## 2. Context Chain
- Level 0: 主 agent (harness-manager) — bugfix-3 推进（ff 模式，跳过 planning）
- Level 1: 我 (executing Subagent-L1) — TDD 红→绿 + 实施

## 3. Completed Tasks
- [x] 硬门禁一/二/三（toolsManager 评估 → 内联完成；自我介绍；action-log 追加本条）
- [x] 角色文件 + 经验文件加载（含经验八"managed-state 幂等同步两端判据"直接相关）
- [x] 填写 `bugfix.md` 五节（Problem Description / Root Cause Analysis / Fix Scope / Fix Plan / Validation Criteria）
- [x] 写 3 条红用例 `tests/test_active_agent_and_feedback_relocation.py`，红阶段确认 FAIL 在根因上
- [x] 改 `workflow_helpers.py` 常量 `FEEDBACK_DIR → .workflow/state/feedback/`
- [x] 新增 `read_active_agent` / `write_active_agent` + `_AGENT_TO_PLATFORM_KEY` / `_AGENT_TO_SKILL_DIR`
- [x] `_project_skill_targets` / `_managed_file_contents` / `install_local_skills` / `_sync_requirement_workflow_managed_files` / `update_repo` 全链路接 `active_agent`
- [x] `install_agent` 末尾 `write_active_agent(root, agent)` 持久化
- [x] `update_repo` 加一次性数据迁移 + `force_all_platforms` / `agent_override` 参数 + "refreshed X" 按实际写入路径动态输出
- [x] CLI 层：`tools/harness_update.py` + `cli.py` 新增 `--agent` / `--all-platforms`
- [x] `tools/harness_export_feedback.py` 读新路径
- [x] scaffold_v2 文档 2 处文案同步
- [x] 既有 `test_cli.py` 2 条用例改用 `--all-platforms` 保留原意图（experience 七）
- [x] 3 条红用例转绿：`tests/test_active_agent_and_feedback_relocation.py -v` → 3 passed
- [x] 全量 pytest：149 passed / 50 skipped / 1 pre-existing failure（`test_smoke_req29`，零新增回归）
- [x] 烟测 `/tmp/petmall-bugfix3-new-smoke/` → `install --agent claude` + `update` + `update --all-platforms` + `feedback` 全链路 PASS；`.harness/` 消失 / `.workflow/state/feedback/feedback.jsonl` 28 行数据连续 / `.codex/.qoder/.kimi/` mtime 未变动（默认模式）/ `refreshed .codex/.claude/.qoder` 仅在 `--all-platforms` 时出现。rm -rf 清理完成。
- [x] 对人文档 `实施说明.md` 落 bugfix 根目录（不放 changes/，符合 `BUGFIX_LEVEL_DOCS` 契约）
- [x] session-memory 追加本条目

## 4. Results

### 关键代码变更（紧挨诊断 §1.5 / §2.7 的修复方向）
- `workflow_helpers.py` +120 / -15（常量 / helpers / 链路改造 / 迁移逻辑）
- `tools/harness_update.py` +12 / -0（`--agent` / `--all-platforms`）
- `cli.py` +12 / -0（子命令参数 + 透传）
- `tools/harness_export_feedback.py` +2 / -1（路径 + docstring）
- scaffold_v2 两处文档 +2 / -2
- `tests/test_active_agent_and_feedback_relocation.py` +215（3 条新红）
- `tests/test_cli.py` +6 / -4（2 条既有断言改 escape hatch）

### 验证基线（bugfix.md 5 条 Validation Criteria 全部可追溯）
1. 新红 3 passed ✓（`test_install_agent_persists_active_agent` / `test_update_repo_only_refreshes_active_agent` / `test_feedback_jsonl_writes_under_state_feedback`）
2. 全量 149 passed / 50 skipped / 1 pre-existing ✓
3. 烟测 `active_agent: claude` + migrate + 单 agent 刷新 ✓
4. `--all-platforms` escape hatch 恢复全平台刷新 ✓
5. `harness feedback` 从新位置读 events_total=28 ✓

## 5. Validated Approaches
- 保持 `record_feedback_event` 零改动（走常量即可），单点改常量 + `LEGACY_FEEDBACK_DIR` 双常量同时保留迁移可能
- `_managed_file_contents` 用 `active_agent is None` 做兼容分支（旧行为 = None，新行为 = 特定 agent），避免 `force_all_platforms` 语义外溢到 install_local_skills 以外
- `write_active_agent` 使用 `yaml.safe_load` + `dump(sort_keys=False)` 避免已有字段顺序被打乱（符合 experience 六 "save 侧白名单" 精神）
- TDD 红阶段先断言"字段为 None"、"外目录文件还在"、"新位置文件缺失"三条，红绿切换一次到位

## 6. Failed Paths
- 初次全量 pytest 发现 `test_cli.py` 两条 `test_update_check_and_apply_refresh_*` fail（老断言依赖旧"全 agent 刷新"行为）→ 按 experience 七"主动改断言"改用 `--all-platforms` escape hatch 保留原测试意图，未扩大变更范围

## 7. Open Questions
- 无。Q1/Q2/Q3/Q4 已在 briefing 阶段由用户选 A/A/A/A 定型，落地无新决策点

## 8. Candidate Lessons（可沉淀到 context/experience/roles/executing.md）

```markdown
### 经验九：scaffold 模板按 "active_agent" 收敛时，三层管道必须同时接参数
- Symptom: 只改 update_repo 不改 _managed_file_contents / install_local_skills → 下游仍按 enabled[] 写 4 个 agent，CLI 层收敛无效
- Cause: scaffold 模板管道分三段——"决定作用域"（update_repo）"生成文件字典"（_managed_file_contents）"写落盘"（install_local_skills + _sync_...）；任一段不感知 active_agent 都会泄漏旧行为
- Fix: 三段同步加 active_agent 参数；兼容模式用 `active_agent is None` 做分支（旧行为默认），避免 escape hatch 与 CLI 强制二选一
- 经验：按 agent/环境/租户收敛的改造必须识别"生成 / 决策 / 落盘"三段管道，缺一段就是泄漏点
```

```markdown
### 经验十：路径常量迁移要同时建"新常量 + 旧常量 + 迁移点"三件套
- Symptom: 只改 FEEDBACK_DIR 常量 → record_feedback_event 写新位置，但旧仓 .harness/feedback.jsonl 历史数据孤立，下次 export 看不到
- Cause: 常量迁移只管新数据写入，不管老数据搬家；update_repo 是唯一全仓生命周期必经路径，必须挂迁移逻辑
- Fix: 新常量 (FEEDBACK_DIR) + 旧常量 (LEGACY_FEEDBACK_DIR) 双保留 + update_repo 一次性 shutil.move + 空目录 rmdir
- 经验：诊断"常量化路径迁移"缺陷时，列清单 "谁写 / 谁读 / 历史数据 / 迁移锚点"四项，单项缺失 = 迁移不完整
```

## 9. Next Steps
- 主 agent 在 ff 模式下：检查 executing 退出条件（3 条新红 PASS / 全量零新增回归 / 烟测 PASS / 实施说明.md 齐全）→ 自动推进 testing
- testing 阶段独立复核点：再跑 3 条新红 + 全量 + 独立烟测（不读 executing 报告）；重点验证旧仓 compat mode warning 行为 + `--all-platforms` escape hatch

## 10. 上下文消耗评估（executing 阶段）
- 文件读取：约 18 个（含 red tests 前 5 个硬门禁角色文件 / diagnosis / bugfix.md / session-memory / workflow_helpers 多段 / backup.py / harness_update.py / harness_export_feedback.py / cli.py / scaffold_v2 两处文档 / test_cli.py 局部）
- 工具调用：约 40 次（含 grep / bash ls / read / edit / write）
- 大文件读取：workflow_helpers.py 共读 ~700 行（分段）
- 测试/烟测执行：pytest 4 次（baseline / 红验证 / 绿验证 / 全量）+ 烟测 install + update + update --all-platforms + feedback 共 4 次
- 评估：约 55-65% 上下文，建议主 agent 推进 testing 前考虑 /compact


---

## 11. Acceptance 段（Subagent-L1 · ff 验收）

### Context Chain
- Level 0: 主 agent → stage: acceptance (ff)
- Level 1: 我 (acceptance Subagent-L1) → 独立核查 + 对人文档

### 核查项清单
- [x] 硬门禁加载（runtime / base-role 硬门禁+经验沉淀段 / stage-role 契约3段 / acceptance.md 全 / 经验 一+二）
- [x] 6 条新测试独立复跑 → 6 passed in 1.52s
- [x] 全量 pytest → 152 passed / 50 skipped / 1 failed
- [x] 经验二认证：git stash push -u → HEAD baseline 复跑 test_smoke_req29 仍 FAIL → pre-existing → git stash pop
- [x] 代码变更范围核查：全部在 Fix Scope 白名单；`.harness/feedback.jsonl`+`runtime.yaml` 为运行副产物
- [x] `harness validate --human-docs --bugfix bugfix-3` → 本阶段产出验收摘要后 3/5
- [x] 烟测 `/tmp/petmall-bugfix3-acceptance-smoke/`：active_agent: claude / .harness rmdir / 新路径 28 行零损耗
- [x] 产出 acceptance-report.md + 验收摘要.md

### 结论
**acceptance pass** — 5/5 Validation Criteria 满足；零新增回归；烟测 3/3；对人文档本阶段补齐。

### 衍生问题（上报主 agent）
1. `回归简报.md` 缺失导致 validate 未达 4/5（briefing 期望），由主 agent 判断豁免或由 done 阶段补
2. 主仓 `.harness/feedback.jsonl`（182 行）真实迁移等待下次主仓 `harness update` 触发

### Next Step
**done**（ff 模式自主推进）

### 上下文消耗
- 文件读取：~10（硬门禁 5 + bugfix.md + 实施说明/测试结论 + session-memory 局部 + validate 输出）
- 工具调用：~16（Read / Bash / Write / Grep）
- pytest 2 次（targeted 6 + 全量）+ 烟测 1 轮（install/update）
- 评估：~35-40% 上下文，主 agent 推进 done 前不需 compact
