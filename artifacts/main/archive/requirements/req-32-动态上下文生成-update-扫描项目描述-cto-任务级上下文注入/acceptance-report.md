# 验收报告：req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）

## 1. 验收结论

- **PASS**
- 7 条 AC 全部逐条可证；3 份 chg 的 Impact Surface 与代码产出一致；Scope 不包含项无越界；Risks R1/R2/R3 防御全部落实；test-report 中 P1-01（contract-7 bare id）已在本次验收前由开发者修复，`harness validate --contract 7` 对 req-32 范围 grep 为空。

## 2. AC 逐条核查

### AC-01（update 生成 project-profile.md + 结构化字段 + LLM 占位 + 时间戳）
- 需求原文摘录："本仓 `harness update` 执行后生成 `.workflow/context/project-profile.md`，文件含 ① 项目语言 / 包名 / 主要依赖结构化字段 ② 预留 LLM 用途 / 风格段 ③ 生成时间戳"
- chg 覆盖：chg-01（项目描述扫描器 + project-profile 落地）→ `build_project_profile` + `render_project_profile`；chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）→ `update_repo` 末尾触发写盘
- 代码证据：`src/harness_workflow/project_scanner.py`（模块存在）；`.workflow/context/project-profile.md` 本仓真实产出，frontmatter 含 `generated_at: 2026-04-22T00:44:37.438501+00:00` / `content_hash: 17682b34...` / `schema: project-profile/v1`；三段 `## 结构化字段` / `## 项目用途（LLM 填充）` / `## 项目规范（LLM 填充）` 齐全且已由主 agent 填充
- 测试证据：test-report §2 AC-01；`tests/test_project_scanner.py` 14 用例 + `tests/test_update_repo_profile.py` 4 用例 全绿
- 判定：**PASS**

### AC-02（二次 update hash 稳定；变更触发 stderr 漂移提示）
- chg 覆盖：chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）
- 代码证据：`workflow_helpers.py::_write_project_profile_if_changed`（对比 old/new content_hash，不一致走 stderr 分支）
- 测试证据：`test_update_repo_profile.py::test_update_profile_hash_stable_on_second_run` + `::test_update_profile_drift_on_pyproject_change` 绿；tmp 仓端到端 `50be7e0→dea9f05` 漂移提示可复现
- 判定：**PASS**

### AC-03（briefing 注入 task_context_index，≤ 8 条，{path, reason}，覆盖 next/ff/regression）
- chg 覆盖：chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）
- 代码证据：`workflow_helpers.py` 含 22 处 `task_context_index` 引用；`_build_task_context_index` / `_build_subagent_briefing` 扩展签名
- 实证证据：本次 acceptance 派发 briefing 与 `.workflow/state/sessions/req-32/task-context/acceptance-001.md` 内容均为 8 条 `{path}: {reason}`；test-report §2 AC-03 已端到端验证 next/ff/regression 三路径各自产出快照
- 测试证据：`test_task_context_index.py` 7 用例 + `test_briefing_ff_regression.py` 6 用例 全绿
- 判定：**PASS**

### AC-04（索引路径失效静默回退 .workflow/context/index.md）
- chg 覆盖：chg-03
- 代码证据：`_resolve_task_context_paths` 返回 `(existing, missing)` 分流
- 文档证据：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md` 新增 "task_context_index 回退语义" 小节
- 测试证据：`test_resolve_task_context_paths_missing_not_raise` 绿
- 判定：**PASS**

### AC-05（用户自定义 CLAUDE/AGENTS 不被覆盖 + stderr 提示）
- chg 覆盖：chg-02
- 代码证据：`workflow_helpers.py:2968-2975`（user-authored stderr）+ `2982-2993`（user-modified stderr，test-report P2-01 已在本轮前修复）
- 测试证据：`UpdateRepoUserAuthoredGuardTest::test_update_skips_user_authored_claude_md` 绿
- 判定：**PASS**（test-report 中 P2-01 措辞偏差已由开发者在 2985-2993 行补齐 stderr 分支，保护语义与消息路径均完整）

### AC-06（TDD 红绿 + validate contract all 绿）
- 测试证据：pytest 基线与复跑均 287 passed / 50 skipped / 0 failed，34 新增用例全绿
- contract-7 证据：本次验收前对 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）artifacts 范围的 contract-7 扫描输出为空（test-report §5 P1-01 已修复：chg-01（项目描述扫描器 + project-profile 落地）的 `session-memory.md` 行 1 与行 38 均已补 title）
- 判定：**PASS**

### AC-07（task-context 快照落盘 + frontmatter 四字段 + 正文条目等价）
- chg 覆盖：chg-03
- 代码证据：`_write_task_context_snapshot` / `_next_task_context_seq`
- 实证：`.workflow/state/sessions/req-32/task-context/` 下 `testing-001.md` + `acceptance-001.md` 均含 frontmatter 四字段（req_id/stage/ts/index_count）+ 8 行正文；归档路径沿用既有 `harness archive`，无新迁移代码
- 测试证据：`test_task_context_snapshot.py` 3 用例全绿
- 判定：**PASS**

## 3. Scope 不包含项核查

- 不自动改写 `experience/**` 或 `platforms.yaml` → 未见新增写盘代码
- 不改 tools-manager / done 六层回顾派发 → 本 req 修改点未触达
- 不在 CLI 内调 LLM → `project-profile.md` 占位保持 "（LLM 填充）"，填充由主 agent 完成
- 不破坏用户自定义 CLAUDE/AGENTS/SKILL → 复用 `_is_user_authored`，未扩展判据
- 不新增 `harness status --context-stats` → `grep context-stats src/` 空
- task-context 快照不直接写 `artifacts/` → 快照落 `.workflow/state/sessions/`，归档走既有路径
- 不做热点文件统计 / TopK / 命中率报告 → 未见相关代码
- **结论：无越界交付**

## 4. Risks 防御核查

- **R1 索引 backfire** → 硬上限 8 + 截断 warn：本次 acceptance 派发 9→8 截断已实证（stderr warn 机制生效）；单测 `test_task_context_index_truncate_warn` 覆盖 → **已落实**
- **R2 profile 漂移** → hash 对比 + stderr 提示：tmp 仓端到端 `50be7e0→dea9f05` 漂移提示可复现；`test_update_profile_drift_on_pyproject_change` 绿 → **已落实**
- **R3 用户自定义保护** → 复用 `_is_user_authored`，未扩展判据；user-authored + user-modified 两条分支均走 stderr → **已落实**

## 5. 对人文档链条

- `需求摘要.md` 存在，31 行，字段齐全
- `changes/chg-01../变更简报.md` 29 行；`chg-02../变更简报.md` 28 行；`chg-03../变更简报.md` 30 行 —— 字段均含"变更名/解决什么问题/怎么做/影响范围/预期验证"契约 6 五件套
- `测试结论.md` 25 行，含通过/失败统计 + 关键失败根因 + 未覆盖场景 + 风险评估
- 本阶段产出 `验收摘要.md`（本次产出，≤ 1 页）
- `harness validate --human-docs --requirement req-32` 本阶段 acceptance 前为 8/10（acceptance/done 待补），写出 `验收摘要.md` 后应升至 9/10（done 留给下一阶段）

## 6. 衍生建议 / 未合并 sug（建议编号由 harness-manager 统一分配，下列以 title 呈现）

- （low）AC-05 spec 措辞回流 chg-02：test-report P2-01 偏差已被"补 user-modified stderr"解决，可回写 chg-02 的 spec 文案作闭环
- （low）tests/ 顶层 `conftest.py` 注入 `sys.path`（test-report P2-02）
- （low）`harness update --scan-profile-only` focused flag（test-report P2-03-bis）
- （low）`.workflow/context/project-profile.md` commit 策略澄清（per-dev 本地 vs repo-shared）
- （low）多语言混合项目的 `stack_tags` 权重判定单测补齐（testing 未覆盖场景 §1）

## 7. 最终判定

- **可进入 done 阶段**
- 归档前还需补的事项：
  1. done 阶段产出 `交付总结.md` 把 `harness validate --human-docs` 补到 10/10
  2. done 阶段将上述 5 条衍生建议评估入 sug 池或转下一 req（由 harness-manager 分配 sug 编号与 title）
  3. 无代码 / 测试 / 契约阻塞
