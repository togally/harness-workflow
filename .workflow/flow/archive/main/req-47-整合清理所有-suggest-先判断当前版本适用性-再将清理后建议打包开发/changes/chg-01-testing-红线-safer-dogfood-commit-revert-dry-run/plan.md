# Change Plan

## 1. Development Steps

> 每步可被 executing 角色（sonnet）直接执行；步骤号在 session-memory.md 复用以标 ✅/❌。

### Step 1：testing.md 红线扩展（sug-51 主线）✅

- 编辑 `.workflow/evaluation/testing.md`，在既有 chg-02 落地的"子进程 dogfood 红线"段**之后**新增章节：
  - **新章节 1：## 破坏性 git 命令禁止（sug-51（testing git restore 事故 + tmpdir 红线）落地）**
    - 红线条款：testing subagent **禁止**在当前仓库执行任何破坏性 git 命令（`git restore` / `git reset --hard` / `git checkout .` / `git clean -f` / `git branch -D` / `git rebase -i` 等）；
    - 白名单豁免：`git diff --name-only` / `git log` / `git show` / `git revert --dry-run` / `git revert --no-commit -n <sha>` 等读 / dry-run 操作豁免；
    - 来源溯源：req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））现场 testing subagent 跑 git restore 事故；
  - **新章节 2：## tmpdir mock 红线（sug-51 + sug-52（dogfood 实跑流程模板）联合落地）**
    - 红线条款：testing dogfood **必须**用 `pytest tmp_path` / `tempfile.mkdtemp()` 创建独立工作区；不允许直接改写当前仓库 git 状态；
    - 配套样本：参考 `tests/test_workflow_next_subprocess.py` fixture 设计（chg-02 已落 4 路径模板）；
- **不重写** chg-02 已落"子进程 dogfood 红线"段（互补共存，章节标题清晰区分）；
- 产出：testing.md 新增 2 章节（合计 ≤ 30 行）。

### Step 2：testing-no-destructive-git lint 实现（sug-23 / sug-51 配套）✅

- 编辑 `src/harness_workflow/validate_contract.py`：
  1. 新增函数 `check_testing_no_destructive_git(root: Path, req_id: Optional[str] = None) -> int`：
     - 默认扫所有 req-id ≥ 41 活跃目录的 `.workflow/state/sessions/{req-id}/action-log.md`（与 testing-no-destructive-git lint 作用域一致）；
     - 指定 req_id 时仅扫该 req；
     - 命中破坏性 git 模式（regex `\bgit\s+(restore|reset\s+--hard|checkout\s+\.|clean\s+-f|branch\s+-D|rebase\s+-i)\b`，不含 dry-run / no-commit）→ 报 WARN（exit 0 + stderr）；
     - WARN 模式：默认本 chg 落 WARN（exit 0），观察 ≥ 1 req 周期后切 FAIL（由后续 chg 决定，本 chg 不强切）；
     - 白名单豁免：含 `--dry-run` / `--no-commit -n` / 读操作（git diff / log / show）regex 跳过；
  2. CLI 入口 `harness validate --contract testing-no-destructive-git` 接通（在既有 _CONTRACTS 集合 + main 函数 if 分支加 testing-no-destructive-git 选项）；
- 产出：`validate_contract.py` 新增函数 ~30 行 + CLI 入口分支 ~5 行；不动既有 lint 行为。

### Step 3：dogfood 经验沉淀模板（sug-52 主线）✅

- 编辑 `.workflow/evaluation/testing.md`，在 Step 1 的 2 个新章节**之后**新增章节：
  - **新章节 3：## dogfood 标准流程模板（sug-52（dogfood 实跑流程模板） 落地）**
    - 模板内容（≤ 30 行）：
      ```python
      # tmpdir 工作区 fixture
      def test_xxx_dogfood(tmp_path):
          # 1. 复制 minimal .workflow 骨架到 tmpdir
          # 2. subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next'], ...)
          # 3. 断言 stdout / runtime.yaml stage / feedback.jsonl 事件数
      ```
    - 4 维必须满足：CLI 子进程入口 / tmpdir 隔离 / stdout 断言 / runtime + feedback 状态断言；
    - 配套样本指针：`tests/test_workflow_next_subprocess.py`（chg-02 已落 4 路径）；
- 编辑 `.workflow/context/roles/analyst.md`（Step B2.5 测试用例设计段）：
  - 在既有"§4. 测试用例设计模板"末尾新增 dogfood TC 必填字段子段（≤ 20 行）：
    - 触发条件：chg 涉及 CLI 入口 / `harness next` / `harness install` / `harness change` / `harness archive` 等子命令时；
    - 必填字段：用例名（TC-Dogfood-NN）/ tmpdir fixture / 子进程命令 / stdout / runtime stage / feedback.jsonl 断言 / 对应 AC / P0 优先级；
    - 配套样本指针：tests/test_workflow_next_subprocess.py + plan.md TC 模板；
- 产出：testing.md 新增 1 章节（≤ 30 行）；analyst.md Step B2.5 段末扩展（≤ 20 行）。

### Step 4：done 阶段 commit + revert dry-run 自动化（sug-31 主线）✅

- 编辑 `.workflow/context/roles/done.md`：
  - 在六层回顾段（State 层后）新增章节"## commit revert dry-run 抽样（sug-31（done 后 commit + revert dry-run 自动化） 落地）"：
    - 抽样规则：对本 req 所有 chg commit 跑 `git revert --no-commit --no-edit -n <sha>`（dry-run 模式）；
    - 处理逻辑：发现 conflict 不阻塞 done，但落 acceptance-report.md（或 done-report 段）"⚠️ revert 抽样发现冲突"+ 建议 regression；
    - 与 testing.md §R1 越界 / revert 抽样（已存在 chg-level 抽样）互补：本段是 done 阶段全 chg 抽样 + harness archive 前置自检维度；
- 编辑 `src/harness_workflow/cli.py`（或 `workflow_helpers.py::archive_requirement` 入口）：
  - 在 `harness archive` 命令开始时插入 `_revert_dry_run_self_check(root, req_id)` helper 调用；
  - helper 实现：拿本 req 最近 N 个 commit（N = 本 req chg 数 + 1，由 changes/ 目录 ls 计数），跑 `git revert --no-commit -n <sha>`，捕获返回码；
  - conflict 时 stderr 输出修复指引：`提示：revert 抽样发现冲突。可用 'harness archive --skip-revert-check' 强制跳过（保留 escape hatch）`；
  - 默认行为：conflict 阻塞归档（return 1）；用户传 `--skip-revert-check` 时仅 stderr 警告不阻塞；
- 产出：done.md 新增 1 章节（≤ 25 行）；cli.py / workflow_helpers.py 新增 helper ~30 行 + archive 入口插桩 ~5 行 + `--skip-revert-check` argparse 选项 ~3 行。

### Step 5：HARNESS_DEV_MODE=1 dev mode flag（sug-55 配套）✅

- 编辑 `.workflow/evaluation/acceptance.md`：
  - 在 §部署同步契约（chg-02 落地）末尾新增"### dev mode 豁免子条款（sug-55（chg-02 部署同步契约 dev mode flag）落地）"：
    - 子条款：`HARNESS_DEV_MODE=1` 环境变量为真时，acceptance 阶段不强制要求 `pipx install --force` + venv mtime 检查；
    - 适用场景：开发态本地迭代；CI / prod 不应设置此 var；
    - 三种语义文档化：
      - dev（HARNESS_DEV_MODE=1）：豁免部署同步检查；
      - prod / ci（默认）：严格部署同步检查（chg-02 行为）；
      - 切换路径：`harness install --check` 子命令做版本对比预警（不强制重装）；
- 编辑 `src/harness_workflow/cli.py`（或对应 helper）：
  - 实现 `harness install --check` 子命令：
    - 输出当前 venv `_is_stage_work_done` import 状态 + venv `workflow_helpers.py` mtime + HEAD commit ts + 差值秒数；
    - 不强制重装；不修改任何文件；exit 0 / 1（差值过大时 stderr 警告 + exit 1）；
  - acceptance 阶段验证逻辑（如 validate_contract.py 或 evaluation runner）读 `os.environ.get("HARNESS_DEV_MODE")`：
    - 为 "1" / "true" 时跳过部署同步硬条目检查；
    - 否则严格检查（与 chg-02 行为一致）；
- 产出：acceptance.md 新增 1 子条款（≤ 20 行）；cli.py / workflow_helpers.py 新增 `--check` 子命令 ~40 行 + acceptance 验证逻辑 env 检查分支 ~5 行。

### Step 6：scaffold_v2 mirror 同步（硬门禁五）✅

- 把以下文件改动镜像到 `src/harness_workflow/assets/scaffold_v2/.workflow/`：
  - `evaluation/testing.md`（Step 1 + Step 3）；
  - `evaluation/acceptance.md`（Step 5）；
  - `context/roles/done.md`（Step 4）；
  - `context/roles/analyst.md`（Step 3）；
- src/ 改动（Step 2 lint / Step 4 cli helper / Step 5 cli --check）**不**进 scaffold mirror；
- **同一 commit 同步**：本 Step 6 mirror 同步必须与对应 live 文件改动落同一次 commit（硬门禁五，reviewer 拦截）。

### Step 7：池清理（acceptance PASS 后由 done 或主 agent 执行）— 跳过（硬序约束 5，executing 禁止）

- **执行时机**：本 chg-01 走 acceptance PASS verdict 后；不在 executing 阶段执行（避免 chg 失败时 sug 状态错位）；
- 对 5 条 sug 翻 frontmatter（直接编辑 .md 文件，文件名前缀匹配）：
  - sug-31（done 后 commit + revert dry-run 自动化） status: pending → archived；加 applied_at: 2026-04-XX + applied_by_chg: chg-01；
  - sug-51（testing git restore 事故 + tmpdir 红线） status: pending → archived；同上；
  - sug-52（dogfood 实跑流程模板） status: pending → archived；同上；
  - sug-55（chg-02 部署同步契约 dev mode flag） status: pending → archived；同上；
  - sug-58（下个 req 优先 chg-7） status: pending → archived；同上；
- 物理 `git mv .workflow/flow/suggestions/sug-{31,51,52,55,58}-*.md .workflow/flow/suggestions/archive/`；
- 验证：`ls .workflow/flow/suggestions/sug-{31,51,52,55,58}-*` exit 1。

### Step 8：测试用例编写 + pytest 跑通 ✅

- 按本文件 §4 测试用例设计实现 TC-01 ~ TC-09 用例：
  - lint 用例（TC-01 / TC-02 / TC-03）：`tests/test_validate_contract_testing_no_destructive_git.py` 新增；
  - revert dry-run helper 用例（TC-04 / TC-05）：`tests/test_archive_revert_dry_run.py` 新增；
  - dev mode flag 用例（TC-06 / TC-07）：`tests/test_dev_mode_flag.py` 新增；
  - dogfood TC 字段 lint 用例（TC-08）：`tests/test_validate_contract_test_case_design_completeness.py` 追加（依赖既有 lint）；
  - subprocess CLI 入口用例（TC-09）：`tests/test_workflow_next_subprocess.py` 追加 install --check 子命令路径；
- 跑通：
  - 本 chg 新增测试 `pytest tests/test_validate_contract_testing_no_destructive_git.py tests/test_archive_revert_dry_run.py tests/test_dev_mode_flag.py -v` 全绿；
  - 全仓库回归：`pytest -q`（regression_scope: targeted，仅跑波及接口的相关测试）。

### Step 9：本 chg-01 自身 dogfood — 待流转后观察（硬序约束 6）

- 在 chg-01 走 executing → testing → acceptance → done 流转过程中，每跳一格观察：
  - feedback.jsonl `stage_advance` 事件相邻间隔 ≥ 4 ms（无 < 4 ms 连跳）；
  - 4 跳由 4 次 `harness next`（或人工驱动）触发；
  - testing 阶段实测自身新增 `testing-no-destructive-git` lint 不命中（本 chg 自身 action-log.md 不含破坏性 git）；
  - acceptance 阶段实测 HARNESS_DEV_MODE=1 豁免 + done 阶段实测 revert dry-run 抽样不阻塞；
- 实测样本写入本 chg session-memory.md `## Validated Approaches` 段，作为 AC-04 / AC-05 自证证据。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- **testing.md 红线 grep**：
  - `grep "破坏性 git 命令禁止" .workflow/evaluation/testing.md` 命中 ≥ 1 行；
  - `grep "tmpdir mock 红线" .workflow/evaluation/testing.md` 命中 ≥ 1 行；
  - `grep "dogfood 标准流程" .workflow/evaluation/testing.md` 命中 ≥ 1 行；
- **lint 接通**：
  - `python3 -m harness_workflow.cli validate --contract testing-no-destructive-git` 不报 unknown contract；
  - 反例 fixture 命中 → exit 0 stderr WARN（默认 WARN 模式，不阻塞）；
- **done.md grep**：
  - `grep "git revert --dry-run" .workflow/context/roles/done.md` 命中 ≥ 1 行；
  - `grep "commit revert dry-run 抽样" .workflow/context/roles/done.md` 命中 ≥ 1 行；
- **acceptance.md grep**：
  - `grep "HARNESS_DEV_MODE" .workflow/evaluation/acceptance.md` 命中 ≥ 1 行；
  - `grep "dev mode 豁免" .workflow/evaluation/acceptance.md` 命中 ≥ 1 行；
- **analyst.md grep**：
  - `grep "dogfood TC" .workflow/context/roles/analyst.md` 命中 ≥ 1 行；
- **CLI subcommand**：
  - `python3 -m harness_workflow.cli install --check` 不报 unknown 子命令；
  - `python3 -m harness_workflow.cli archive --help | grep skip-revert-check` 命中（argparse 选项存在）；
- **scaffold mirror diff**：
  - `diff -rq .workflow/evaluation/ src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/` 无差异；
  - `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 无差异；
- **frontmatter yaml lint（池清理后）**：
  - `python3 -c "import yaml; yaml.safe_load(open('.workflow/flow/suggestions/archive/sug-58-*.md').read().split('---')[1])"` 不报错；
  - `grep "applied_by_chg: chg-01" .workflow/flow/suggestions/archive/sug-{31,51,52,55,58}-*.md` 命中 ≥ 5 行；

### 2.2 Manual smoke / integration verification

- **本 chg-01 自身周期 stage 流转 dogfood**：
  - chg-01 走 executing → testing → acceptance → done 4 跳，每跳间隔 ≥ 4 ms；
  - `cat .workflow/state/feedback/feedback.jsonl | tail -n 20 | grep stage_advance` 确认无 < 4 ms 连跳；
- **HARNESS_DEV_MODE=1 实测**：
  - `HARNESS_DEV_MODE=1 python3 -m harness_workflow.cli validate ...` 跳过部署同步检查（如有 acceptance 验证 hook）；
  - `python3 -m harness_workflow.cli install --check` 输出 venv vs HEAD 差值秒数 + 不强制重装；
- **archive 前置 revert dry-run**：
  - 模拟一个 conflict 场景（手工创建 conflicting commit），跑 `harness archive` → stderr 提示阻塞 + 提示 --skip-revert-check；
  - 跑 `harness archive --skip-revert-check` → 仅 stderr 警告不阻塞；
- **跑 pytest -q** → 全绿（含本 chg 新增 9 用例 + 既有用例无回归）。

### 2.3 AC Mapping

- **AC-01（testing 红线扩展）** → Step 1 + 2.1 testing.md grep。
- **AC-02（testing-no-destructive-git lint 端到端）** → Step 2 + 2.1 lint 接通 + §4 TC-01 / TC-02 / TC-03。
- **AC-03（dogfood 经验沉淀模板）** → Step 3 + 2.1 testing.md / analyst.md grep + §4 TC-08。
- **AC-04（done 阶段 commit revert dry-run 自动化）** → Step 4 + 2.1 done.md grep + 2.2 archive 前置 + §4 TC-04 / TC-05 / TC-09。
- **AC-05（HARNESS_DEV_MODE=1 dev mode flag）** → Step 5 + 2.1 acceptance.md grep / cli subcommand + 2.2 dev mode 实测 + §4 TC-06 / TC-07。
- **AC-06（池清理 5 条 sug 出池）** → Step 7 + 2.1 frontmatter yaml lint + grep。
- **AC-07（scaffold_v2 mirror 一致 + 全量回归）** → Step 6 + 2.1 scaffold mirror diff + Step 8 pytest。

## 3. Dependencies & Execution Order

- **硬序约束 1（Step 1 / Step 3 testing.md 章节顺序）**：Step 1（破坏性 git 红线 + tmpdir mock 红线）必须在 Step 3（dogfood 标准流程模板）之前；章节顺序：chg-02 已有"子进程 dogfood 红线"段 → Step 1 新增 2 章节 → Step 3 新增 1 章节；保证 testing.md 章节逻辑递进。

- **硬序约束 2（Step 2 lint 实现 + Step 8 测试用例同步）**：Step 2 lint 函数实现可与 Step 8 TC-01 ~ TC-03 测试同时进行（TDD 风格）；最迟在 Step 6 commit 前跑通。

- **硬序约束 3（Step 4 / Step 5 CLI 改动可并行）**：done.md / acceptance.md / cli.py 改动各自正交（Step 4 archive 入口 / Step 5 install --check）；建议同 commit 落地（避免 testing 阶段引用未落地的 lint 改动）。

- **硬序约束 4（Step 6 mirror 与 Step 1 / Step 3 / Step 4 / Step 5 同 commit）**：scaffold_v2 mirror 同步必须与对应 live 文件改动落同一次 commit（硬门禁五）；不允许分两 commit 提交。

- **硬序约束 5（Step 7 池清理时机）**：sug 翻 frontmatter + git mv 必须在 acceptance subagent verdict PASS 后由 done subagent 或主 agent 执行；executing 阶段不允许动 sug 文件（防止 chg 失败时 sug 状态错位）。

- **硬序约束 6（Step 9 自身 dogfood 时机）**：本 chg-01 走完 stage 流转后回看 feedback.jsonl；不能在 executing 阶段提前断言 acceptance / done 行为。

- **跨 chg 关系**：本 chg-01 与 req-46 chg-01 / chg-02（已 done）独立可并行（无前置）；与本 req 其他 chg 无（首批 K=1）；下个 req 的 chg-2（usage-log）/ chg-9（runtime sync）/ ... 可在本 chg done 后独立启动。

## 4. Test Case Design

> regression_scope: **targeted**
> 理由：本 chg 主要是文档契约 + lint 实现 + CLI 子命令新增，非核心 helper 改造；改动跨 4-6 文件但每个改动独立可隔离测试；testing.md / acceptance.md / done.md / analyst.md 文档改动通过 grep 断言；lint 实现 + dev mode flag 通过 unit test 隔离；archive 前置自检通过 subprocess test；不触动 _is_stage_work_done / runtime.yaml schema / state yaml schema 等核心结构（不满足 full 触发条件）。
>
> Affected interfaces (auto-generated from git diff --name-only + human supplement)：
>
> - `.workflow/evaluation/testing.md`（新增"破坏性 git 命令禁止"+"tmpdir mock 红线"+"dogfood 标准流程模板"3 章节）
> - `.workflow/evaluation/acceptance.md`（新增"dev mode 豁免子条款"段）
> - `.workflow/context/roles/done.md`（新增"commit revert dry-run 抽样"章节）
> - `.workflow/context/roles/analyst.md`（Step B2.5 模板末尾扩 dogfood TC 必填字段子段）
> - `src/harness_workflow/validate_contract.py::check_testing_no_destructive_git`（新增）
> - `src/harness_workflow/validate_contract.py::main`（CLI 入口分支扩展）
> - `src/harness_workflow/cli.py::archive` 子命令（新增 `--skip-revert-check` argparse 选项 + 前置 dry-run 自检）
> - `src/harness_workflow/cli.py::install --check` 子命令（新增）
> - `src/harness_workflow/workflow_helpers.py::_revert_dry_run_self_check`（新增 helper）
> - `src/harness_workflow/workflow_helpers.py::archive_requirement`（入口插桩 dry-run 自检）
> - `tests/test_validate_contract_testing_no_destructive_git.py`（新增）
> - `tests/test_archive_revert_dry_run.py`（新增）
> - `tests/test_dev_mode_flag.py`（新增）
> - `tests/test_validate_contract_test_case_design_completeness.py`（追加 dogfood TC 字段断言）
> - `tests/test_workflow_next_subprocess.py`（追加 install --check 子命令 subprocess 用例）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/{testing,acceptance}.md`（mirror）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/{done,analyst}.md`（mirror）
> - `.workflow/flow/suggestions/sug-{31,51,52,55,58}-*.md`（frontmatter 翻 status + applied_by_chg；物理 git mv 到 archive/）

| Test Case | Input | Expected | AC Reference | Priority |
|-----------|-------|----------|--------------|----------|
| **TC-01**（lint 命中破坏性 git）| 反例 fixture：tmp .workflow/state/sessions/{req}/action-log.md 含 `git restore src/file.py` 行 → 跑 `python3 -m harness_workflow.cli validate --contract testing-no-destructive-git --root <tmp>` | exit 0（WARN 模式）+ stderr 含 "WARN: testing-no-destructive-git" + 命中行号输出 | AC-02 | P0 |
| **TC-02**（lint 白名单豁免）| 正例 fixture：tmp action-log.md 含 `git revert --dry-run <sha>` + `git diff --name-only` + `git log` → lint 跑 | exit 0 + 无 WARN 输出（白名单正确豁免） | AC-02 | P0 |
| **TC-03**（lint 边界 — 含 git 字符串非命令）| fixture：tmp action-log.md 含 "解释了 git restore 的语义"（中文文档段落，非命令）→ lint 跑 | exit 0 + 不命中（regex 边界 `\b` + 命令模式精确） | AC-02 | P1 |
| **TC-04**（archive 前置 revert dry-run 正例）| 模拟 tmp git repo + 1 个干净 commit，跑 `harness archive --root <tmp> req-test` | dry-run 抽样无 conflict + archive 正常完成 + exit 0 | AC-04 | P0 |
| **TC-05**（archive 前置 revert dry-run 反例）| 模拟 tmp git repo + 2 个 conflicting commits（手工构造），跑 `harness archive --root <tmp> req-test` | exit 1 + stderr 含 "revert 抽样发现冲突" + 提示 --skip-revert-check；用 `--skip-revert-check` 重跑 → 仅 stderr 警告 + archive 完成 + exit 0 | AC-04 | P0 |
| **TC-06**（HARNESS_DEV_MODE=1 豁免）| `HARNESS_DEV_MODE=1` env + tmp acceptance fixture 缺 `pipx install --force` 痕迹 → 跑 acceptance 验证（如 validate hook 或 acceptance subagent 执行入口） | 部署同步检查跳过 + acceptance PASS（不报 FAIL） | AC-05 | P0 |
| **TC-07**（HARNESS_DEV_MODE 未设严格模式）| 不设 env + 同 TC-06 fixture → 跑 acceptance 验证 | 部署同步检查严格触发 + 报 FAIL（与 chg-02 行为一致） | AC-05 | P0 |
| **TC-08**（dogfood TC 字段 lint）| chg fixture：plan.md §4 测试用例设计段缺 dogfood TC（CLI 子命令型 chg）→ 跑 `harness validate --contract test-case-design-completeness` | exit 1 + stderr 含 "缺 dogfood TC 必填字段" | AC-03 | P1 |
| **TC-09**（install --check subprocess 行为）| subprocess 真跑 `python3 -m harness_workflow.cli install --check` 在 tmp 工作区 | exit 0 + stdout 含 venv mtime 数字 + HEAD commit ts 数字 + 差值秒数；不修改任何文件 | AC-05 | P1 |
| **TC-10**（本 chg-01 自身 dogfood）| 跑完 chg-01 后看 feedback.jsonl `grep stage_advance | tail -n 5` 间隔 | 所有 stage_advance 间隔 ≥ 4 ms（无 < 4 ms 连跳） | AC-01 + AC-04 | P1 |

