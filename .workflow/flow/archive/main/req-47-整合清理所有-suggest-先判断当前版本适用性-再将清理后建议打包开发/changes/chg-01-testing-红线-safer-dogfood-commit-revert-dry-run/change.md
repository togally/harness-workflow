# Change

## 1. Title

testing 红线 + safer dogfood + commit revert dry-run

## 2. Background

req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）planning Part B 推荐首批落地（K=1）；对应 req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）roadmap §2 chg-7 簇 + §5 首批推荐。本 chg 同根因合并 5 条 sug（sug-58 主因 + sug-51 / sug-52 / sug-31 / sug-55 同根因）—— 围绕 testing 阶段安全 + dogfood 协议 + done 阶段 commit revert 自动化展开。

**核心驱动**：

- **sug-51（P0 数据安全）**：req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））现场实证 testing subagent 跑 `git restore src/` 擦除当前仓库未提交改动事故；testing.md 当前虽含子进程 dogfood 红线（chg-02 落地）但**没有**"任何破坏性 git 命令一律禁止 + dogfood 必须 tmpdir mock"红线，也无 testing-no-destructive-git lint。
- **sug-58（首批必含承接 marker）**：req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）交付总结明确"下个 req 优先承接 chg-7（testing 红线 + safer dogfood）"；本 req 即"下个 req"，承接 marker。
- **sug-52（dogfood 实跑流程模板）**：testing.md 已有 chg-02 落地的 4 路径 fixture / `_run_harness_next()` wrapper，但 plan.md §测试用例设计 dogfood TC 必填字段 + testing.md 完整经验沉淀模板未做。
- **sug-31（done 后 commit + revert dry-run 自动化）**：testing.md §R1 越界 / revert 抽样有 chg-level revert dry-run 抽样，但 done 阶段全 chg 自动 dry-run + harness archive 前自检未做。
- **sug-55（dev mode flag）**：chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）R2 风险条款已声明开发态 pipx 重装 friction；HARNESS_DEV_MODE=1 环境变量未实现，acceptance.md 部署同步硬条目无 dev mode 豁免；本 chg 同步落地避免 dev mode friction 阻塞落地节奏。

**关联 sug**（5 条）：sug-31 / sug-51 / sug-52 / sug-55 / sug-58；详见 §4 Included。

## 3. Requirement

- req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）

## 4. Scope

### Included

- **testing.md 红线扩展（sug-51 主线）**：
  1. 新增"任何破坏性 git 命令一律禁止"红线 — 禁止 testing subagent 在当前仓库执行 `git restore` / `git reset --hard` / `git checkout .` / `git clean -f` / `git branch -D` / `git rebase -i`（不含 dry-run）；
  2. 新增"dogfood 必须 tmpdir mock"红线 — testing 必须使用 `pytest tmp_path` / `tempfile.mkdtemp()` 创建独立工作区，禁止改写当前仓库 git 状态；
  3. 与 chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）已落"子进程 dogfood 红线"互补不重写；本 chg 加 sug-51 数据安全维度。

- **testing-no-destructive-git lint（sug-23 配套，本 chg 落 lint 实现）**：
  1. `validate_contract.py` 加 `check_testing_no_destructive_git(root, req_id)` 函数；
  2. 扫 `.workflow/state/sessions/{req_id}/action-log.md` 是否含破坏性 git 命令模式；
  3. 白名单豁免：`git revert --dry-run` / `git diff --name-only` / `git log` 等读操作豁免；
  4. CLI 入口 `harness validate --contract testing-no-destructive-git`；
  5. 默认 WARN 一轮（不阻塞），观察期后切 FAIL（写文档化条款）。

- **dogfood 经验沉淀模板（sug-52 主线）**：
  1. `testing.md` 加完整 dogfood 标准流程模板段（≤ 30 行）—— 含 tmpdir 工作区 fixture / `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', ...])` 调用 / stage 落点断言 / runtime.yaml stage 字段断言 / feedback.jsonl 事件数断言；
  2. `analyst.md` 或 `stage-role.md` Step B2.5 模板加 dogfood TC 必填字段（plan.md §4 测试用例设计）—— 当 chg 涉及 CLI 入口 / harness next / harness install 等子命令时，必须含至少 1 条 dogfood TC（用例名 / tmpdir fixture / 子进程命令 / 断言 / 对应 AC / 优先级 P0）；
  3. 配套样本指针：参考 `tests/test_workflow_next_subprocess.py`（chg-02 落地）。

- **done 阶段 commit + revert dry-run 自动化（sug-31 主线）**：
  1. `done.md` 六层回顾后加自动 git revert --dry-run 抽样段：对本 req 所有 chg commit 跑 `git revert --no-commit --no-edit -n <sha>` dry-run，发现 conflict 不阻塞 done 但落 acceptance-report.md 警告；
  2. `harness archive` 前置自检：`harness archive` 命令开始时跑一次 dry-run 抽样（最近 N 个 commit，N=本 req chg 数 + 1）；conflict 时阻塞归档并提示用户；
  3. 与 testing.md §R1 越界 / revert 抽样（已存在）互补不重写；本 chg 加 done 阶段 + harness archive 自动化维度。

- **dev mode flag（sug-55 配套）**：
  1. `HARNESS_DEV_MODE=1` 环境变量定义；
  2. `acceptance.md` §部署同步契约硬条目加 dev mode 豁免子条款 — `HARNESS_DEV_MODE=1` 时不强制要求 `pipx install --force` + venv mtime 检查；
  3. `harness install --check` 子命令实现：检查 venv vs HEAD commit ts 差值，仅报告不强制重装；
  4. 文档化 dev / prod / ci 三种语义到 `harness install --help` + `acceptance.md`。

- **池清理（chg-01 acceptance PASS 后执行）**：
  - sug-31 / sug-51 / sug-52 / sug-55 / sug-58 翻 frontmatter `status: archived` + `applied_by_chg: chg-01` + `applied_at: <today>` → `git mv` 到 `archive/` 目录。

- **scaffold_v2 mirror 同步（硬门禁五）**：
  - 本 chg 涉及 `.workflow/evaluation/testing.md` + `.workflow/evaluation/acceptance.md` + `.workflow/context/roles/done.md` + `.workflow/context/roles/analyst.md`（或 stage-role.md）改动，按硬门禁五同 commit 同步至 `src/harness_workflow/assets/scaffold_v2/.workflow/`。

### Excluded

- **不在本 chg 范围**：
  - chg-2（usage-log runtime 接通）—— 数据底座大工作量，与本 chg 正交，留下个 req 承接（roadmap-r2 §5.2）；
  - chg-3 / chg-4 / chg-5 / chg-6 / chg-8 / chg-9 / chg-10 等留尾 chg —— 见 roadmap-r2 §3 / §5；
  - sug-39 钩子接通主因 —— 与 sug-59 路径漂移在 chg-2 一并修，不在本 chg；
  - 历史 testing 阶段 git 事故追溯 —— 仅修当前红线 + lint，不回溯审计已发生事故。

- **跨 repo**：
  - 不动 Yh-platform 等其他 repo 的 testing 行为；仅在本仓库 harness-workflow 落地。

- **legacy req**：
  - 不修改 req-02 ~ req-40 的历史 action-log.md；testing-no-destructive-git lint 仅扫 req-id ≥ 41 活跃目录。

## 5. Acceptance

- **AC-01（testing 红线扩展）**：`.workflow/evaluation/testing.md` 含"破坏性 git 命令禁止"红线段 + "dogfood 必须 tmpdir mock"红线段；grep 命中各 ≥ 1 行；红线段不与 chg-02 已有"子进程 dogfood 红线"重复，互补共存。

- **AC-02（testing-no-destructive-git lint 端到端）**：
  - `python3 -m harness_workflow.cli validate --contract testing-no-destructive-git` 命令可跑 exit 0 / 1；
  - 反例：构造一条 action-log.md 含 `git restore src/`（命中破坏性命令），lint 报 FAIL；
  - 正例：构造一条 action-log.md 仅含 `git diff` / `git revert --dry-run`（白名单），lint 报 PASS；
  - lint 默认 WARN 模式（exit 0 + stderr 警告），切 FAIL 由后续 chg / 用户决定。

- **AC-03（dogfood 经验沉淀模板）**：
  - `.workflow/evaluation/testing.md` 含 dogfood 标准流程模板段（≤ 30 行）；grep "dogfood 标准流程" 命中 ≥ 1 行；
  - `analyst.md` Step B2.5（或 stage-role.md 测试用例模板）含 dogfood TC 必填字段说明；grep "dogfood TC" 命中 ≥ 1 行；
  - 模板提供 `tests/test_workflow_next_subprocess.py` 作参考样本指针（grep 命中）。

- **AC-04（done 阶段 commit revert dry-run 自动化）**：
  - `.workflow/context/roles/done.md` 六层回顾段含"git revert --dry-run 抽样"硬条目；grep 命中 ≥ 1 行；
  - 端到端用例：本 chg-01 自身 done 阶段跑 dry-run 抽样并落 acceptance-report.md 或 done-report 段；
  - `harness archive` 命令前置自检：dry-run conflict 时 stderr 提示并阻塞归档；新增 unit / subprocess test ≥ 1 条。

- **AC-05（HARNESS_DEV_MODE=1 dev mode flag）**：
  - `acceptance.md` §部署同步契约含 dev mode 豁免子条款；grep "HARNESS_DEV_MODE" 命中 ≥ 1 行；
  - 环境变量实测：`HARNESS_DEV_MODE=1 python3 -m harness_workflow.cli validate ...` 跑通豁免；
  - `harness install --check` 子命令存在 + 输出版本对比报告（不强制重装）。

- **AC-06（池清理 5 条 sug 出池）**：
  - sug-31 / sug-51 / sug-52 / sug-55 / sug-58 frontmatter 全部 `status: archived` + `applied_by_chg: chg-01`；
  - 物理位置：5 条文件全部在 `.workflow/flow/suggestions/archive/`（live 目录无残留）；
  - 验证：`ls .workflow/flow/suggestions/sug-{31,51,52,55,58}-*` exit 1（不存在）。

- **AC-07（scaffold_v2 mirror 一致 + 全量回归）**：
  - `diff -rq .workflow/evaluation/ src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/` 无差异；
  - `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 无差异；
  - `pytest -q` 全绿（含本 chg 新增测试用例 + 既有用例无回归）；
  - `harness validate --contract artifact-placement` exit 0；`harness validate --human-docs` exit 0（按 D-11 = B 留痕放行 raw_artifact 同 case）。

## 6. Risks

- **R1（testing-no-destructive-git lint 误报）**：lint 扫 action-log.md 可能命中合规场景（如 `git revert --dry-run` 含 git revert 字符串）。**缓解**：白名单豁免 `--dry-run` / `--no-commit -n` / 读操作（git diff / log / show）；先 WARN 一轮观察 ≥ 1 个 req 周期再切 FAIL；本 chg AC-02 仅验证 WARN 模式行为，不强制 FAIL。

- **R2（dogfood 模板与 chg-02 已有红线重叠）**：testing.md 已含 chg-02 落地的"子进程 dogfood 红线"段；本 chg 加 sug-51 数据安全维度可能重复。**缓解**：plan.md §1 step 1 显式核对 testing.md 已有内容，仅补充 sug-51 数据安全维度（破坏性 git 禁止 + tmpdir mock），不重写 chg-02 已写章节，章节标题清晰区分（"破坏性 git 红线" vs "子进程 dogfood 红线"）。

- **R3（dev mode flag 设计盲点）**：HARNESS_DEV_MODE=1 在 CI / 自动化场景误触发可能跳过部署同步检查。**缓解**：默认未设 = 严格模式（prod / ci 走严格）；env var 仅开发态主动设置；明确文档化三种语义；CI 配置文件不要 export 此 var。

- **R4（commit revert dry-run 影响 done / archive 阶段时长）**：done 阶段跑 dry-run 增加几秒；archive 前置自检增加阻塞时机。**缓解**：done 阶段 dry-run 仅抽样（≤ 3 条 commit）；archive 自检有 conflict 时输出修复指引而非硬阻塞，用户可 `harness archive --skip-revert-check` 强制跳过（保留 escape hatch）。

- **R5（池清理时机错位）**：5 条 sug 必须等 chg-01 acceptance PASS 后才能 archive；过早 archive 导致回滚困难。**缓解**：plan.md §3 硬序约束 — 池清理必须在 acceptance subagent verdict PASS 后由 done subagent 或主 agent 执行；executing 阶段不允许动 sug 文件。

- **R6（dogfood 模板与 plan.md §4 模板冲突）**：analyst.md Step B2.5 已有 §4 测试用例设计模板（bugfix-6 B1 落地）；本 chg 加 dogfood TC 必填字段可能冲突。**缓解**：以"扩展"形式落 — 在既有 §4 模板末尾加 dogfood TC 子段，不重写既有结构；plan.md §1 step 2 显式 diff 对比。

## 7. Dependencies

- **前置依赖**：
  - chg-01（机器型工件路径修复 + 防再犯 lint）（req-46，已 done）：本 chg 工件落点遵循 chg-01 路径修复后契约（机器型必落 `.workflow/flow/`）。
  - chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）（req-46，已 done）：本 chg 扩展 testing.md 子进程 dogfood 红线段，依赖 chg-02 已落地的"子进程 dogfood 红线"作底座。

- **后置阻塞**：
  - 本 req（req-47）后续无其他 chg；本 chg acceptance PASS 后即转 done。
  - 留尾 chg（chg-2 / chg-3 / ... 见 roadmap-r2 §5）由下个 req 承接，不阻塞本 chg。

- **跨 chg 信号**：
  - 本 chg 落地的 testing 红线 + dogfood 模板 + commit revert 自动化 + dev mode flag，作为后续所有 chg 的 testing / acceptance / done 阶段共用基础设施；后续 chg 在 plan.md §4 测试用例设计段引用本 chg 的 dogfood TC 必填字段约定。
