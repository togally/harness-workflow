# Session Memory

## 1. Current Goal

- 扩 `harness ff` 的 `--auto` / `--auto-accept` CLI 入口，实现 5.1 阻塞清单检测、5.3 三档语义、acceptance 前汇总落盘。覆盖 req-29 AC-01、5.1、5.2、5.3。

## 2. Current Status

- planning 阶段已产出：change.md / plan.md / 变更简报.md。
- 强依赖 chg-03 已合入。

## 3. Validated Approaches

- auto 主循环抽出独立 runner（`auto_runner.py`）比塞回老 `harness_ff.py` 状态机更安全。
- 阻塞检测用"规则表格 + 关键词 + applicable_stages"三段式，避免写死 if/else。
- 交互通过依赖注入 reader，便于 mock。

## 4. Failed Paths

- Attempt: 无
- Failure reason: n/a
- Reminder: 千万不要在本仓真跑 `ff --auto`，它会改 runtime.yaml / 产出垃圾决策日志。

## 5. Candidate Lessons

```markdown
### 2026-04-19 CLI 交互与阻塞检测分层
- Symptom: 交互 + 阻塞 + 推进塞在一个函数里，单测几乎无法写。
- Cause: 关注点混杂，副作用叠加。
- Fix: 依赖注入 reader + 纯函数 detect_blocking + 独立 runner，三层解耦。
```

## 6. Next Steps

- executing 先实现 `auto_blocking.py`（纯函数），再实现 `auto_runner.py`（注入式），最后改 CLI。
- 单测覆盖顺序：阻塞检测 → runner 三档 → CLI 校验。

## 7. Executing Log（2026-04-19，Subagent-L1）

- [x] `cli.py` ff 子命令扩 `--auto` / `--auto-accept {low,all}`；`--auto-accept` 不跟 `--auto` 时 `parser.error` 退出。
- [x] 新建 `src/harness_workflow/ff_auto.py`：`workflow_ff_auto` + `check_blocking_before_action` + `_should_auto_ack` + `_advance_to_stage_before_acceptance`。
- [x] 阻塞类别决策点**强制交互**（`--auto-accept all` 也不旁路，守 5.1）。
- [x] acceptance 前调 `write_decision_summary` 落盘 `决策汇总.md`；`_resolve_branch` 容错回退 `main`。
- [x] 新增 `tests/test_ff_auto.py` 7 条用例全绿；整仓 `python3 -m unittest discover tests` 159 → 166 全过。
- [x] `artifacts/.../chg-04-.../实施说明.md` 已落盘。
- **交接 chg-05 smoke 要点**：
  - 在 fake req 工作区真跑 `harness ff --auto` / `--auto --auto-accept low` / `--auto --auto-accept all`；
  - 预埋若干 `DecisionPoint`（含 low / medium / high + 一条命中 `rm -rf` 的阻塞条目），验证 5.1 强制交互 + 三档 ack 顺序；
  - 断言 `artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md` 在 acceptance 之前已落盘；
  - **不**在 harness-workflow 本仓跑，避免污染 runtime。

## 7. Open Questions

- `--auto-accept medium` 要不要支持？req-29 5.3 仅列了 low / all 两档，故本 change 严格按需求只实现两档；如用户后续要 medium，开 sug 新增。
- acceptance 前打印 + 落盘 + 交互三步是否要原子化？失败回滚策略？建议 executing 阶段按 low-risk 敲定（例如：落盘失败 → 不进交互、退出非零、不污染 runtime）。
