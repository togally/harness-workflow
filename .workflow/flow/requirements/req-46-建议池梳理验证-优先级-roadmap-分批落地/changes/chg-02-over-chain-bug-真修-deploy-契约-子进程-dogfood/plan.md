# Change Plan

## 1. Development Steps

> 每步可被 executing 角色（sonnet）直接执行；步骤号在 session-memory.md 复用以标 ✅/❌。

### Step 1：保守降级严格化（_is_stage_work_done 第 7407-7409）

- 编辑 `src/harness_workflow/workflow_helpers.py::_is_stage_work_done`：
  - 定位行 7405-7409（`elif stage == "executing":` 分支，`if not changes_dir.exists(): return True`）；
  - 改为：
    ```python
    if not changes_dir.exists():
        # 严格化（reg-02（over-chain 三维失配） + chg-02（保守降级严格化））：
        # executing 但无 changes 目录 = subagent 还没派发 = work 未做，应阻断 next 自动连跳
        return False
    ```
  - 其他 stage 维持 True 保守降级；planning / RFE 出口走 `_FALLBACK_STAGES` 豁免，不动。
- 同步 docstring：在保守降级原则后追加一行"**例外**：executing stage 且 changes_dir 缺时返回 False（reg-02（over-chain 三维失配） + chg-02（保守降级严格化） 严格化）"。
- 产出：`workflow_helpers.py` 第 7405-7409 区域 5 行 diff。

### Step 2：子进程 dogfood 测试（tests/test_workflow_next_subprocess.py）

- 新增 `tests/test_workflow_next_subprocess.py`，用 `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next', ...])` 真跑 CLI（不只 import helper）；
- 用 tmpdir 干净 fixture（pytest `tmp_path`）：复制 minimal `.workflow/state/runtime.yaml` + `.workflow/flow/requirements/{req-test}/{requirement.md, changes/}` 骨架；
- 4 路径覆盖（详见 §4 TC-03 ~ TC-06）：
  - **first-hop**（RFE chg 缺 + `--execute`）：期望停在 RFE 报错或停在 executing；
  - **while-internal**（executing chg dir 存在但 session-memory 缺）：期望停在 executing；
  - **缺产物**（testing 缺 test-report.md）：期望停在 testing；
  - **有产物**（acceptance 有 checklist + 结论段）：期望连跳到 done；
- 断言项：subprocess `returncode` + `stdout`（含"未完成"或"已推进"）+ tmpdir runtime.yaml 的 `stage` 字段 + feedback.jsonl `stage_advance` 事件数；
- 跨平台：subprocess 用 `sys.executable`（不硬编码 python），`text=True` 强制 UTF-8，路径用 `pathlib.Path`。

### Step 3：升级 .workflow/evaluation/acceptance.md checklist

- 编辑 `.workflow/evaluation/acceptance.md`：
  - 新增章节"## 部署同步契约（reg-02（over-chain 三维失配） + chg-02（部署契约 + 子进程 dogfood） 落地）"；
  - 硬条目："**部署同步**：执行 `pipx install --force <repo-path>` 或 `harness install --force-skill`（二选一）；验证 venv `_is_stage_work_done` helper 存在 + venv 文件 mtime ≥ HEAD commit ts；缺此步则 acceptance FAIL，不能 done。"
  - 提供验证命令样本：
    ```bash
    python3 -c "from harness_workflow.workflow_helpers import _is_stage_work_done; print(_is_stage_work_done.__module__)"
    stat -f "%m" "$(python3 -c 'import harness_workflow.workflow_helpers as m; print(m.__file__)')"
    git log -1 --format=%ct -- src/harness_workflow/workflow_helpers.py
    ```
- 同步 `.workflow/context/roles/done.md` 六层回顾 State 层：grep 校验扩展为"部署版本 vs source mtime / hash 对比"（具体落点见 Step 6 经验沉淀，State 层校验只引用经验九）。
- 产出：acceptance.md 新增 1 节（≤ 30 行）；done.md 不动文字（仅经验九引用）。

### Step 4：升级 .workflow/evaluation/testing.md（子进程 dogfood 红线）

- 编辑 `.workflow/evaluation/testing.md`：
  - 新增章节"## 子进程 dogfood 红线（reg-02（over-chain 三维失配） + chg-02（子进程 dogfood）落地，呼应 sug-51（subprocess dogfood 红线） + sug-52（testing 沉淀模板扩 dogfood））"；
  - 红线："涉及 CLI 入口 / `harness next` / `harness install` 等子命令行为的 chg，testing 阶段**必须**至少含 1 条 subprocess 真跑 CLI 用例（`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', ...])`）；不允许只用 `from harness_workflow.workflow_helpers import ...` 直调 helper 函数代替。"
  - 例外："纯 helper 内部行为（无 CLI 入口暴露）允许直调；如不确定，default-pick 走 subprocess。"
  - 配套样本指针：`tests/test_workflow_next_subprocess.py`（本 chg 落地）。
- 产出：testing.md 新增 1 节（≤ 20 行）。

### Step 5：sug-46（二次实证 over-chain）+ sug-50（gate gap 部署 gap）+ sug-53（usage-log 缺失） frontmatter 字段更新

- 编辑 `.workflow/flow/suggestions/sug-46-*.md` frontmatter：
  - 新增 `linked_regression: reg-02`；
  - 新增 `promoted_to_chg: chg-02`；
  - 状态字段保持 `pending`（acceptance PASS 后再翻 `archived`，见时机约定）。
- 同样改动到 `sug-50-*.md`（chg-01 gate gap，实为部署 gap）；
- `sug-53-*.md`：仅在 over-chain 副作用部分加 `linked_regression: reg-02` + 在 frontmatter 加 `partial_promoted_to_chg: chg-02`（标记 partial，因 sug-39 主因不在本 chg）；status 保持 `pending`。
- **执行时机**：frontmatter 字段补全在 executing 阶段做（commit 前置）；status 翻 `archived` 必须在 acceptance PASS 后做（保留追溯链 + 防止 chg 失败时 sug 状态错位），由 acceptance subagent 或 done subagent 执行。

### Step 6：经验沉淀（regression.md 经验九）

- 编辑 `.workflow/context/experience/roles/regression.md`：
  - 新增"## 经验九：三维失配（契约层 / 源代码层 / 部署二进制层）诊断模板"；
  - 内容：经验八（契约层 vs 实现层失配）穷举二维矩阵；reg-02 表明应扩到三维：
    | 维度 | 检查方式 | 失配症状 |
    |------|---------|---------|
    | 契约（自然语言文档） | 读 role.md / WORKFLOW.md / role-model-map.yaml | 行为说明 vs 实际行为对不上 |
    | 源代码层（src/） | grep + 单元测试 + 直调 helper 函数 | helper 缺失或逻辑错 |
    | 部署二进制层（pipx / npm / docker site-packages） | grep 部署路径 + mtime 对比 + 在线 CLI 子进程行为 | helper 在 src/ 存在但 deploy 缺失 |
  - 修复模式新增："dogfood 必须**子进程真跑 CLI 命令**，不能只调 helper 函数（mock helper 测不出部署 gap）。pytest 直调 helper = src/ 版本验证；subprocess CLI = 部署版本验证；二者并列必跑。"
  - 来源：reg-02（over-chain 三维失配根因诊断） + chg-02（over-chain 真修 + 部署契约 + 子进程 dogfood）。
- 产出：regression.md 新增 1 节经验九（≤ 40 行）。

### Step 7：scaffold_v2 mirror 同步

- 把以下文件改动镜像到 `src/harness_workflow/assets/scaffold_v2/.workflow/`：
  - `evaluation/acceptance.md`（Step 3）；
  - `evaluation/testing.md`（Step 4）；
  - `context/experience/roles/regression.md`（Step 6）；
- src/ 改动（Step 1 `workflow_helpers.py` 严格化 / Step 2 新增测试）**不**进 scaffold mirror（scaffold 仅复制 `.workflow/`，无需 mirror src/）；
- **同一 commit 同步**（reviewer 拦截硬门禁五）：Step 3 / 4 / 6 改动与本 Step 7 mirror 同步必须落同一次 commit，禁止分两次提交。

### Step 8：本 chg-02 自身周期 dogfood

- 在 chg-02 走 executing → testing → acceptance → done 流转过程中，每跳一格观察：
  - feedback.jsonl 的 `stage_advance` 事件相邻间隔 ≥ 4 ms（无 < 4 ms 连跳）；
  - 4 跳由 4 次 `harness next`（或人工驱动）触发，而非 1 次连跳；
  - 每次 `harness next` 跑前先确认 `python3 -c "from harness_workflow.workflow_helpers import _is_stage_work_done"` 不报 ImportError（部署版本含 helper）；
  - acceptance 阶段对照 Step 3 部署同步 checklist 跑通；
- 实测样本写入本 chg session-memory.md `## Validated Approaches` 段，作为 AC-3 自证证据。

### Step 9：测试用例编写 + pytest 跑通 + tox / CI 验证

- 按本文件 §4 测试用例设计实现 TC-01 ~ TC-09 用例：
  - 直调 helper 用例（TC-01 / TC-02）：`tests/test_workflow_next_workdone_gate.py` 现有文件追加；
  - subprocess 用例（TC-03 ~ TC-06）：`tests/test_workflow_next_subprocess.py` 新增（Step 2 已落地骨架）；
  - dogfood 用例（TC-07 / TC-09）：`tests/test_workflow_next_subprocess.py` 含端到端 + chg-02 自身 feedback 时间戳断言；
  - mtime check 用例（TC-08）：`tests/test_pipx_freshness_helper.py` 新增；
- 跑通 `pytest tests/test_workflow_next_subprocess.py tests/test_workflow_next_workdone_gate.py tests/test_pipx_freshness_helper.py -v` 全绿；
- 跑通全仓库回归 `pytest -q`（regression_scope: full）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- **helper 严格化断言**：
  - `python3 -c "from harness_workflow.workflow_helpers import _is_stage_work_done; from pathlib import Path; import tempfile; t=Path(tempfile.mkdtemp()); (t/'.workflow/flow/requirements/req-x').mkdir(parents=True); print(_is_stage_work_done('executing', t, 'req-x', 'requirement'))"` 输出 `False`（chg dir 缺）；
- **subprocess test 跑通**：
  - `pytest tests/test_workflow_next_subprocess.py -v` 全绿（4 路径 × ≥ 1 用例 = 4+ 用例）；
- **scaffold mirror diff**：
  - `diff -rq .workflow/evaluation/ src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/` 无差异；
  - `diff -rq .workflow/context/experience/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/` 无差异；
- **frontmatter yaml lint**：
  - `python3 -c "import yaml; yaml.safe_load(open('.workflow/flow/suggestions/sug-46-...md').read().split('---')[1])"` 不报错（YAML 合法）；
  - `grep "linked_regression: reg-02" .workflow/flow/suggestions/sug-46-*.md .workflow/flow/suggestions/sug-50-*.md .workflow/flow/suggestions/sug-53-*.md` 命中 ≥ 3 行；
  - `grep "promoted_to_chg: chg-02\|partial_promoted_to_chg: chg-02" .workflow/flow/suggestions/sug-46-*.md .workflow/flow/suggestions/sug-50-*.md .workflow/flow/suggestions/sug-53-*.md` 命中 ≥ 3 行；
- **经验沉淀 grep**：
  - `grep "经验九.*三维失配" .workflow/context/experience/roles/regression.md` 命中 ≥ 1 行；
  - `grep "子进程 dogfood 红线" .workflow/evaluation/testing.md` 命中 ≥ 1 行；
  - `grep "部署同步契约" .workflow/evaluation/acceptance.md` 命中 ≥ 1 行。

### 2.2 Manual smoke / integration verification

- **本 chg-02 自身周期 stage 流转 dogfood**：
  - chg-02 走 executing → testing → acceptance → done 4 跳，每跳间隔 ≥ 4 ms；
  - 跑 `cat .workflow/state/feedback/feedback.jsonl | tail -n 20 | grep stage_advance` 确认无 < 4 ms 连跳；
- **mtime check（部署版本与 commit 一致）**：
  - 跑 `python3 -c "import harness_workflow.workflow_helpers as m; import os; print(os.path.getmtime(m.__file__))"` 输出 ts；
  - 跑 `git log -1 --format=%ct -- src/harness_workflow/workflow_helpers.py` 输出 commit ts；
  - 验证前者 ≥ 后者；不一致则跑 `pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow` 重装后重跑 mtime check；
- **subprocess CLI 行为**：
  - 跑 `python3 -m harness_workflow.cli next` 在 executing stage chg dir 缺时 → 期望 stdout 含"Stage executing 工作未完成"+ 不 advance；
  - 跑 `python3 -m harness_workflow.cli next --execute` 在 RFE stage chg plan 完整时 → 期望仅 advance 到 executing，不连跳到 done；
- **跑 pytest -q** → 全绿（含本 chg 新增 9 用例 + 既有用例无回归）。

### 2.3 AC Mapping

- **AC-1（保守降级严格化）** → Step 1 + 2.1 helper 严格化断言 + §4 TC-01 / TC-02。
- **AC-2（子进程 dogfood 4 路径全绿）** → Step 2 + Step 9 + 2.1 subprocess test 跑通 + §4 TC-03 ~ TC-06。
- **AC-3（自身周期 dogfood 自证）** → Step 8 + 2.2 本 chg-02 自身周期 stage 流转 dogfood + §4 TC-07 / TC-09。
- **AC-4（sug 状态翻转）** → Step 5 + 2.1 frontmatter yaml lint + grep 断言。
- **AC-5（部署同步契约文档化）** → Step 3 + 2.2 mtime check + §4 TC-05 部署 mtime 反例。
- **AC-6（mirror diff 一致 + 经验沉淀）** → Step 4 + Step 6 + Step 7 + 2.1 scaffold mirror diff + 经验沉淀 grep。

## 3. Dependencies & Execution Order

- **硬序约束 1（Step 1 必须在 Step 2 / Step 8 之前）**：先严格化 helper（Step 1），子进程 dogfood（Step 2）才能验证新行为；本 chg 自身 dogfood（Step 8）也需 Step 1 落地后才能观察到 4 跳间隔 ≥ 4 ms。
- **硬序约束 2（Step 2 独立可并行 Step 3 / Step 4）**：subprocess test 编写与 acceptance.md / testing.md 文档升级互相不依赖，可并行；建议同 commit 落地（避免 testing 阶段引用未落地的 testing.md 红线）。
- **硬序约束 3（Step 7 mirror 与 Step 3 / Step 4 / Step 6 同 commit）**：scaffold_v2 mirror 同步必须与对应 live 文件改动落同一次 commit（硬门禁五）；不允许分两 commit 提交。
- **硬序约束 4（Step 5 sug 翻转分两阶段）**：frontmatter 字段补全（`linked_regression` / `promoted_to_chg`）在 executing 阶段做；status 翻 `archived` 必须在 acceptance PASS 后做（防止 chg 失败时 sug 状态错位）。
- **硬序约束 5（Step 9 测试用例编写时机）**：建议与 Step 1 / Step 2 同时进行（TDD 风格），先写测试再实现 helper 严格化；最迟在 Step 7 commit 前跑通。
- **跨 chg 关系**：与 chg-01（机器型工件路径修复 + 防再犯 lint）独立可并行；roadmap chg-2（sug-39 钩子接通）+ chg-3（首批 P0 第二+三批）等待本 chg acceptance PASS。

## 4. Test Case Design

> regression_scope: full
> 理由：workflow_next 核心 helper（`_is_stage_work_done`）行为改 + 部署契约新增 + acceptance / testing 评估文件改 + experience/roles/regression.md 经验沉淀；非局部改动，影响面覆盖 CLI 主入口 + 工作流 gate 逻辑 + acceptance / testing 红线，须 full 回归。
>
> Affected interfaces (auto-generated from git diff --name-only + human supplement):
> - `src/harness_workflow/workflow_helpers.py::_is_stage_work_done`（第 7405-7409 严格化）
> - `src/harness_workflow/cli.py::main` / `harness_next.py`（subprocess 入口；行为不变，dogfood 覆盖确认）
> - `tests/test_workflow_next_subprocess.py`（新增）
> - `tests/test_workflow_next_workdone_gate.py`（既有，追加 TC-01 / TC-02 边界用例）
> - `tests/test_pipx_freshness_helper.py`（新增，TC-08）
> - `.workflow/evaluation/acceptance.md`（新增"部署同步契约"段）
> - `.workflow/evaluation/testing.md`（新增"子进程 dogfood 红线"段）
> - `.workflow/context/experience/roles/regression.md`（新增经验九"三维失配诊断模板"）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/{acceptance,testing}.md`（mirror）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/regression.md`（mirror）
> - `.workflow/flow/suggestions/sug-46-*.md`（二次实证 over-chain）+ `sug-50-*.md`（gate gap 部署 gap）+ `sug-53-*.md`（usage-log 缺失） frontmatter 字段更新

| Test Case | Input | Expected | AC Reference | Priority |
|-----------|-------|----------|--------------|----------|
| TC-01 | `_is_stage_work_done('executing', tmp_root, 'req-x', 'requirement')` 在 chg dir 缺时（仅 `requirement.md` 存在） | 返回 `False`（严格化生效） | AC-1 | P0 |
| TC-02 | `_is_stage_work_done('testing', tmp_root, 'req-x', 'requirement')` 在 `test-report.md` 缺时 | 返回 `False`（既有行为，回归用例） | AC-1 | P0 |
| TC-03 | subprocess 真跑 `python3 -m harness_workflow.cli next` 在 stage=executing 且 chg dir 缺 | exit 0 + stdout 含"Stage executing 工作未完成"+ runtime.yaml stage 不 advance + feedback.jsonl 无新 stage_advance | AC-2 | P0 |
| TC-04 | subprocess 真跑 `python3 -m harness_workflow.cli next --execute` 在 stage=ready_for_execution 且 chg plan 完整 | exit 0 + 仅 advance 到 executing（不连跳到 testing/acceptance/done）+ feedback.jsonl 仅 1 条 RFE→executing stage_advance | AC-2 + AC-3 | P0 |
| TC-05 | subprocess 真跑 `python3 -m harness_workflow.cli next` 在 stage=executing 且 chg dir + session-memory.md 全在（含 ✅）+ tests/ 含 test_*.py | exit 0 + advance 到 testing 后 stop（不连跳）+ feedback.jsonl 1 条 executing→testing stage_advance | AC-2 + AC-3 | P0 |
| TC-06 | subprocess 真跑 `python3 -m harness_workflow.cli next` 在 stage=testing 且 `test-report.md` 含 §结论 | exit 0 + advance 到 acceptance 后 stop + feedback.jsonl 1 条 testing→acceptance stage_advance | AC-2 + AC-3 | P0 |
| TC-07 | dogfood 全链：tmpdir mock 工作区，从 RFE 走到 done，期望 4 次 `harness next` 调用，每次仅 1 跳 | 4 次调用产出 4 条 stage_advance；每条相邻间隔 ≥ 4 ms（subprocess 启动开销保证）；最终 stage=done | AC-3 | P1 |
| TC-08 | mtime check helper unit：`_check_pipx_freshness()` 验证 venv `_is_stage_work_done` import 不报 `ImportError` + venv `workflow_helpers.py` mtime ≥ HEAD commit ts | 部署版本一致时返回 `True`；mtime 早于 commit ts 时返回 `False` 并报告差值（秒） | AC-5 | P0 |
| TC-09 | 本 chg-02 自身 dogfood（runtime 走完后回看 feedback.jsonl）：grep `stage_advance` 事件 | chg-02 周期内（commit ts 起到 done）所有 stage_advance 间隔 ≥ 4 ms（无 < 4 ms 连跳）；4 跳事件链由 ≥ 4 次 `harness next` 触发 | AC-3 | P1 |
