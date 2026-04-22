# 测试报告：req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）

## 1. 测试范围

覆盖 req-32 的 7 条 AC：

- AC-01：`harness update` 生成 `.workflow/context/project-profile.md`（结构化字段 + LLM 占位 + 时间戳 + hash）
- AC-02：update 二次执行 hash 稳定；描述文件变更触发 stderr 漂移提示
- AC-03：`next --execute` / `ff --auto` / `regression` 派发 briefing 含 `task_context_index`（≤ 8 条，`{path, reason}`）
- AC-04：subagent 按索引路径加载失败时不报错，回退至 `.workflow/context/index.md`
- AC-05：用户自定义 CLAUDE.md / AGENTS.md update 跳过覆盖，stderr 提示
- AC-06：TDD 红绿 + `harness validate --contract all` 绿
- AC-07：快照落盘 `.workflow/state/sessions/{req-id}/task-context/{stage}-{seq}.md`，frontmatter 4 字段 + 正文完整

## 2. 执行记录

### AC-01: PASS

- 证据：本仓 `.workflow/context/project-profile.md` 存在
  - frontmatter：`generated_at: 2026-04-22T00:44:37.438501+00:00` / `content_hash: 17682b34...` / `schema: project-profile/v1`
  - 结构化字段：`package_name: harness-workflow` / `language: python` / `stack_tags: [python+pyproject]` / `deps_top: [questionary>=2.0.0, pyyaml>=6.0]` / `entrypoints: [harness=harness_workflow.cli:main]`
  - LLM 占位：`## 项目用途（LLM 填充）` + `## 项目规范（LLM 填充）` 两段齐全
- tmp 仓 `/tmp/harness-test-req32/tmp-repo` 首次 `harness update` 输出 `[update_repo] project-profile 已生成（初始 hash: 50be7e0）`

### AC-02: PASS

- 本仓第二次 `harness update` → stderr/stdout 无 "hash 漂移"，hash 保持 `17682b34...`
- tmp 仓改 `pyproject.toml`（name + 依赖）后 update → stderr 输出 `[update_repo] project-profile 已刷新（hash 漂移：50be7e0→dea9f05）`
- pytest：`tests/test_update_repo_profile.py::test_update_profile_hash_stable_on_second_run` + `test_update_profile_drift_on_pyproject_change` 均绿

### AC-03: PASS

- 本仓 testing briefing（本任务派发）已证明 `task_context_index` 8 条（9→8 截断触发）+ `task_context_index_file: .workflow/state/sessions/req-32/task-context/testing-001.md`
- tmp 仓 `harness next --execute`：briefing JSON 含 8 条 `{path, reason}` + `task_context_index_file: .workflow/state/sessions/req-01（smoke-test-ac03）/task-context/changes_review-001.md`
- tmp 仓 `harness ff --auto`：派发 testing stage briefing 含 8 条 index + `testing-001.md` 快照
- tmp 仓 `harness regression "smoke test ..."`：briefing 含 `regression_id: reg-01（smoke test regression briefing）` + `regression_title` + 8 条 index + `regression-001.md` 快照
- pytest：`test_task_context_index.py`（7 用例）+ `test_task_context_snapshot.py`（3 用例）+ `test_briefing_ff_regression.py`（6 用例）全绿

### AC-04: PASS（代码 + 文档 + 单测三角覆盖）

- 代码：`src/harness_workflow/workflow_helpers.py::_resolve_task_context_paths`（行 6017-6038）返回 `(existing, missing)` 分流；docstring 明确 "对 missing 中的路径应静默降级到 `.workflow/context/index.md` 全量加载"
- 文档：`src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md` 行 200-205 新增 "task_context_index 回退语义（req-32 / chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘））" 小节，明确 "静默 fallback"
- 单测：`tests/test_task_context_index.py::test_resolve_task_context_paths_missing_not_raise` 绿
- CLI 不对 subagent 强约束（本 AC 为 LLM 消费语义，符合 chg-03 spec）

### AC-05: PASS（有措辞偏差，非阻塞）

- tmp 仓 install → 修改 CLAUDE.md 尾部 → `harness update`：
  - 实际输出（stdout）：`- skipped modified CLAUDE.md`
  - CLAUDE.md 用户内容完整保留（`USER EDIT TO CLAUDE.md` 未被擦除）
- pytest：`test_update_repo_profile.py::UpdateRepoUserAuthoredGuardTest::test_update_skips_user_authored_claude_md` 绿
- **偏差**：chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）spec 要求 stderr `skip user-authored: CLAUDE.md`，实际走 `_sync_requirement_workflow_managed_files` 既有分支输出 stdout `skipped modified`（已登记 managed 且用户改过 → 不触发 stderr 路径）。首次 adopt 场景会走 stderr `[update_repo] skipping user-authored file ...`（`workflow_helpers.py` 行 2971-2975）。保护语义完整，仅消息路径与 spec 文字措辞不完全一致

### AC-06: PASS（契约 7 有 3 条 req-32 自身新增违规）

- `pytest -q`：**287 passed / 50 skipped** in 31.87s（baseline）；复跑 **287 passed / 50 skipped** in 32.70s（无回归）
- 本 req 相关测试模块全绿：
  - `test_project_scanner.py`：14 用例
  - `test_update_repo_profile.py`：4 用例
  - `test_task_context_index.py`：7 用例
  - `test_task_context_snapshot.py`：3 用例
  - `test_briefing_ff_regression.py`：6 用例
  - 合计 34 新增用例
- `harness validate --contract all`：exit 1，322 violations（历史基线），其中 req-32 artifacts 下 3 条新增违规（见 "发现的问题" P1-01）

### AC-07: PASS

- 本仓 `.workflow/state/sessions/req-32/task-context/testing-001.md` 已落盘（本派发生成）
  - frontmatter 4 字段：`req_id: req-32` / `stage: testing` / `ts: 2026-04-22T02:01:02.099223+00:00` / `index_count: 8`
  - 正文 8 行，每行 `{path}: {reason}`，等价 briefing 内 `task_context_index`
- tmp 仓连续派发产出 `changes_review-001.md` / `plan_review-001.md` / `testing-001.md` / `regression-001.md`，{seq} 按 stage 独立
- 归档路径：既有 `harness archive` 会把 `.workflow/state/sessions/{req-id}/` 迁入 `artifacts/{branch}/requirements/{req-id}-{slug}/sessions/`；本 chg 复用既有归档代码，未新增迁移逻辑（chg-03 spec 允许）

## 3. pytest 结果

- 基线：`287 passed, 50 skipped in 31.87s`
- 复跑：`287 passed, 50 skipped in 32.70s`
- 与基线对比：**零回归**，新增 34 用例全绿
- 分模块直接运行（带 PYTHONPATH=src）：
  - `test_project_scanner.py + test_update_repo_profile.py`：18 passed
  - `test_task_context_index.py + test_task_context_snapshot.py`：10 passed
  - `test_briefing_ff_regression.py`：6 passed

## 4. 契约校验结果

- `harness validate --contract all` exit code：**1**（历史基线）
- 总违规数：**322**（与历史基线一致）
- req-32 artifacts 下违规：**3 条**，均为 contract-7 bare id，定位于 chg-01（项目描述扫描器 + project-profile 落地）的 session-memory.md：
  - `session-memory.md:1` → 首行 `# Session Memory — req-32 / chg-01（项目描述扫描器 + project-profile 落地）`，首次引用 req-32 无 title 修饰
  - `session-memory.md:38` → chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）/ chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）两个裸 id
- contract all 其余违规全部位于 `artifacts/requirements/req-0x-*.md` / `artifacts/main/archive/` 等历史 legacy 文件（契约 7 fallback 条款豁免"本次提交之后"新增）

## 5. 发现的问题

### P1-01：chg-01 session-memory.md 有 3 条 contract-7 bare id 新增违规
- 复现：`harness validate --contract 7 2>&1 | grep req-32-动态` → 3 行
- 文件：`artifacts/main/requirements/req-32-动态上下文生成-update-扫描项目描述-cto-任务级上下文注入/changes/chg-01-.../session-memory.md`
- 行 1：`# Session Memory — req-32 / chg-01（...）`——首次引用 `req-32` 裸 id，按契约 7 应为 `req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）`
- 行 38：`chg-02 / chg-03 另派 subagent 处理` —— 两个裸 id，应为 `chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）` / `chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）`
- 影响 AC-06（契约 all 须绿）。阻塞等级：**P1**（done 阶段六层回顾必须拦截）

### P2-01：AC-05 的 stderr 消息文本与 chg-02 spec 不完全一致
- spec 文字：`skip user-authored: CLAUDE.md`（stderr）
- 实际行为：已登记 managed + 用户改过 → stdout `skipped modified CLAUDE.md`；首次未登记 + 用户内容 → stderr `[update_repo] skipping user-authored file CLAUDE.md; pass --force-managed ...`
- 用户自定义保护语义完整（文件未覆盖），只是消息路径 / 文字与 spec 描述有偏差
- 建议：若 acceptance 认可现行消息语义，将 chg-02 spec 的 "stderr `skip user-authored`" 修订为实际实现

### P2-02：tests 直接运行缺 sys.path 引导
- 现象：独立运行 `pytest tests/test_task_context_index.py` 报 `ModuleNotFoundError: No module named 'harness_workflow'`；完整 `pytest -q` 由早期测试（如 `test_active_agent_and_feedback_relocation.py` 行 35 `sys.path.insert(0, str(REPO_ROOT / "src"))`）兜底才通过
- 建议：补 `tests/conftest.py` 顶层注入 `sys.path`，或约定所有新测试 `from __future__` 后 `sys.path.insert`
- 非本 req 引入，历史遗留，但本 req 新增 3 个测试文件同样受影响

### P2-03-bis：`harness update` 一次调用产生多文件副作用
- 现象：本次测试流程中在本仓单次 `harness update`（AC-02 验证）导致 `.claude/skills/harness/assets/templates/*.tmpl` 4 文件 + `.workflow/context/experience/index.md` 被更新（内容从老模板同步为 scaffold_v2 最新模板）
- 影响：test run 留下了非本 req 范围的 diff；虽然是 update 正常行为，但缺一个"只做 profile 刷新"的 dry-run/focused flag，每次验证 profile 漂移都会附带刷其他 managed 文件
- 建议：后续 sug 评估是否新增 `harness update --scan-profile-only` 便于 CI/测试

### P2-03：`.workflow/context/project-profile.md` 尚未纳入 git
- 现象：`git log -- .workflow/context/project-profile.md` 空
- 影响：`harness update` 生成后该文件作为本地修改存在，需用户决定是否提交
- 建议：done 阶段补 commit 或文档说明本文件定位为"每次 update 本地重生成"

## 6. 建议

1. **sug-28（优先 high）**：chg-01 session-memory.md 契约 7 修正 —— 行 1 / 行 38 首次引用点补 title（`req-32（...）` / `chg-02（...）` / `chg-03（...）`），作为 done 阶段硬门禁拦截项
2. **sug-29（优先 medium）**：AC-05 spec 文字与实现的偏差二选一 —— 要么修订 chg-02 spec 接受现实现，要么补一条 stderr 统一用户自定义保护文案
3. **sug-30（优先 medium）**：tests/ 顶层加 `conftest.py` 注入 `sys.path`，解除"必须整套跑才绿"的隐性耦合
4. **sug-31（优先 low）**：`harness update` 后把 project-profile.md 路径写入 `.gitignore` 或明确 commit 策略（本地 per-developer 还是 repo-shared）
5. **Polish item**：LLM 占位 section 目前只有注释 `<!-- ... -->`，后续可在 done 阶段由主 agent 按 project-profile 填充本仓的"项目用途"与"项目规范"两段文字，作为 req-32 动态上下文生成的首个闭环自证

## 7. 结论

**PASS（有条件通过）**。

- 7 条 AC 全部功能性通过，代码 / 单测 / 集成三路证据齐备
- 287 passed / 50 skipped 零回归，34 新增 TDD 用例全绿
- **唯一阻塞项**：P1-01（chg-01 session-memory 3 条 contract-7 bare id）须在 done 阶段六层回顾前由开发者补 title，否则违反契约 4 "契约 all 须绿" 硬门禁
- 其余 P2 为 polish / 非阻塞，可承接到下一 req 或 sug 池处理
