# Change Plan

## 1. Development Steps

### Step 1: 扩 CLI 参数

- 在 `src/harness_workflow/tools/harness_ff.py`：
  - 新增 `--auto` flag（store_true）。
  - 新增 `--auto-accept` 选项，`choices=["low","all"]`，未传为 None。
  - `--auto-accept` 依赖 `--auto`：若仅传 `--auto-accept` → argparse 报错 + 非零退出。
- 帮助文本：中文简述两个 flag 的语义，并指向 `requirement.md` 5.1 / 5.3。

### Step 2: 抽 auto_runner

- 新建 `src/harness_workflow/auto_runner.py`（或 workflow_helpers 内新函数，由 executing 低风险决策）：
  - 入口 `run_auto(root, req_id, auto_accept: str | None, stage_iter: Callable, decision_reader: Callable, summary_writer: Callable) -> int`。
  - 依赖注入 stage 推进、决策读、汇总写三个函数，便于单测。
  - 主循环：for each stage in `[requirement_review, planning, plan_review, ready_for_execution, executing, testing]`：
    1. 调 `stage_iter(stage)` 推进并返回本阶段新产生的 `DecisionPoint[]` + stage 执行摘要。
    2. 每个新 point：先 `detect_blocking(point, stage)`；命中 → abort（不 append、不继续）；否则 `append_decision`。
    3. stage 推进结束后更新 runtime.yaml 的 stage。
  - 循环结束后（到达 testing 完成）：
    - `points = load_decisions(root, req_id)`
    - `content = render_decision_summary(points, ...)`
    - 写 `artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md`
    - 按 `auto_accept` 交互：
      - `None` → 逐条交互；
      - `low` → `risk=="low"` 自动 ack，其它交互；
      - `all` → 全自动 ack；
    - 全部 ack 完成后才允许进 acceptance；否则打印"acceptance blocked"并退出非零。

### Step 3: 实现阻塞检测

- 新建 `src/harness_workflow/auto_blocking.py`：
  - `@dataclass(frozen=True) class BlockingRule`: `id / category / keywords: tuple[str,...] / description / suggested_risk="high"`。
  - `BLOCKING_CATEGORIES`：按 req-29 5.1 清单硬编码 8 条（破坏性 IO / 不可逆 git / 跨 req / archive 物理删除 / 凭证 / 敏感配置 / 依赖变更 / schema 变更）。
  - `detect_blocking(point: DecisionPoint | str, stage: str) -> BlockingHit | None`：
    - 对 point 的 `reason + choice + options + extra` 串联后做大小写不敏感关键词匹配；命中返回 `BlockingHit(rule, matched_keyword)`。
    - stage 白名单：例如 `archive 物理删除` 在 `planning` 阶段允许讨论但 executing 不允许执行；规则里带 `applicable_stages`。

### Step 4: 调 chg-03 helper 落盘汇总

- `run_auto` 结尾调 `render_decision_summary`（来自 `auto_decisions.py`），把返回字符串写到 `artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md`。
- 路径解析用现有 `resolve_requirement_root` + runtime 里的 `current_requirement` slug 推断；不 hardcode。

### Step 5: 新增 `tests/test_ff_auto.py`

- 模拟 fake req + fake stage_iter（回放预设 DecisionPoint 序列）：
  - `test_auto_accept_none_interactive`：每个决策都用 mock input 交互；选 n 时非零退出。
  - `test_auto_accept_low_auto_ack_low`：low 自动、medium/high 交互。
  - `test_auto_accept_all_auto_ack_all`：全自动通过。
  - `test_blocking_category_rm_rf_abort`：fake 决策含 "rm -rf" → 命中破坏性 IO 规则 → 退出非零 + 不 append。
  - `test_summary_file_written_before_interaction`：assert `决策汇总.md` 已在交互之前存在。
  - `test_summary_contents_grouped_by_risk`：读回汇总文件，断言三段标题顺序与条目数。
  - `test_auto_accept_requires_auto`：仅传 `--auto-accept low` 而无 `--auto` → argparse SystemExit 非零。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_ff_auto.py -v` → 7 条用例全绿。
- `pytest tests/test_auto_decisions.py tests/test_archive_path.py` → 无回归。
- `grep -rn "from harness_workflow.auto_decisions import" src` 确认 CLI 正确 import chg-03 helper。

### 2.2 Manual smoke / integration verification

- **不** 在本仓真跑（会污染 runtime）；执行 `harness ff --help` 应能看到 `--auto` / `--auto-accept` 新帮助文本。
- 真实 smoke 由 chg-05 在 fake req 下完成。

### 2.3 AC Mapping

- AC-01 → Step 1 + Step 2 + Step 4 + Step 5 的交互用例。
- 5.1 阻塞清单 → Step 3 + Step 5 的 rm -rf 用例。
- 5.2 双轨 → Step 2 + Step 4（运行时写 flow、汇总写 artifacts）。
- 5.3 三档 → Step 2 + Step 5 的三档用例。

## 3. Dependencies & Execution Order

- **强依赖 chg-03**：需要 `DecisionPoint` / `append_decision` / `load_decisions` / `render_decision_summary`。
- 与 chg-01 / chg-02 无文件冲突。
- 是 chg-05 的前置。
