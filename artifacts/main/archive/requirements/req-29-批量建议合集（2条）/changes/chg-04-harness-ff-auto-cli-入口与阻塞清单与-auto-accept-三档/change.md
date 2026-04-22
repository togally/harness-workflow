# Change

## 1. Title

harness ff --auto CLI 入口与阻塞清单与 auto-accept 三档

## 2. Goal

- 扩展 `harness ff` CLI：新增 `--auto` 和 `--auto-accept {low,all}` 两个 flag；实现 5.1 阻塞清单的白/黑名单检测 helper；`--auto-accept` 三档交互逻辑；进入 acceptance 前调用 chg-03 的 `render_decision_summary` 打印并落盘 `决策汇总.md`；确保 acceptance 阶段之前停下等人。

## 3. Requirement

- `req-29`

## 4. Scope

### Included

- 修改 `src/harness_workflow/tools/harness_ff.py`：
  - CLI 新增 `--auto`（bool）和 `--auto-accept` 枚举（`low` / `all`；未传=交互）。
  - `--auto` 激活时才允许 `--auto-accept`，否则报错退出。
- 修改 `src/harness_workflow/workflow_helpers.py` 中 `harness_ff` 推进逻辑（或抽到 `auto_runner.py`，由 executing 敲定）：
  - 在 `requirement_review → planning → plan_review → ready_for_execution → executing → testing` 各 stage 执行前自检：
    - 调 `detect_blocking(action_context) -> BlockingHit | None` 判断是否触及 5.1 阻塞类别；命中则停下并打印阻塞原因，**不写入决策日志**。
  - 进入 acceptance 前：调 `load_decisions` + `render_decision_summary` → 打印到 stdout + 写到 `artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md` → 按 `--auto-accept` 档位交互。
- 新建 `src/harness_workflow/auto_blocking.py`（或并入 `auto_decisions.py`，由 executing 敲定）：
  - `BLOCKING_CATEGORIES: list[BlockingRule]`，覆盖 req-29 5.1 八大类。
  - `detect_blocking(summary: str, stage: str) -> BlockingHit | None`：基于关键词匹配 + stage 白名单给出命中项；返回 reason + 建议等级。
- 更新 `.workflow/context/roles/harness-manager.md`（若 ff 入口在此描述）：同步 `--auto` 参数说明。
- 新增 `tests/test_ff_auto.py`：
  - auto-accept low / all / 未传 三档下进入 acceptance 前的交互契约。
  - 阻塞命中时停下 + 不写日志 + 退出码非零。
  - 决策汇总落盘路径正确、格式正确。
  - 决策风险等级合法性校验。

### Excluded

- 不实现决策点的数据层（由 chg-03 负责）。
- 不扩 `--auto` 到 acceptance 阶段之后（明确禁止）。
- 不实现 "详细阻塞清单扩展"（req-29 明确 5.1 仅是最小集，详清单由后续 sug）。
- 不改 `harness next` / 其它命令的语义。
- 不跑真实 `ff --auto`（会污染本仓 runtime，由 chg-05 在 fake req 下做 smoke）。

## 5. Acceptance

- Covers requirement.md **AC-01**：`harness ff --auto` 能从 `requirement_review / planning / plan_review / ready_for_execution / executing / testing` 任一 stage 推到 acceptance 之**前**停下；汇总决策点；支持 `--auto-accept` 跳过交互。
- Covers requirement.md **5.1 阻塞清单**：命中八类中任一类 → 立即停下、打印原因、不写日志、退出码非零。
- Covers **5.3 三档语义**：未传 → 全交互；`--auto-accept low` → 仅 low 自动 ack；`--auto-accept all` → 全自动 ack。
- Covers **5.2 双轨约定**：运行时日志写 `.workflow/flow/requirements/{req-id}/decisions-log.md`；汇总写 `artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md`。

## 6. Risks

- **R1 交互模拟**：CLI 的交互（`input()` / questionary）在单测里难以覆盖 → 用 `unittest.mock.patch('builtins.input', ...)` 或把交互抽成可注入的 callable，便于在单测替换为假 reader。
- **R2 阻塞检测误报/漏报**：5.1 列的是类别，靠关键词匹配天然不完美 → 把 `BLOCKING_CATEGORIES` 做成"规则表格 + 注释"，漏报由后续 sug 补齐、误报靠用户显式 override（但 override 必须是 high 决策点）。
- **R3 ff 入口状态机嵌入**：现有 `harness_ff.py` 推进逻辑可能是一段长状态机，插入 auto 分支有风险 → 优先把 auto 路径抽出独立 runner（`auto_runner.py`），与原交互入口解耦。
- **R4 acceptance 前打印顺序**：必须保证 `决策汇总.md` 落盘 **先于** 交互提示，避免用户看到提示但 `artifacts/...` 下还没文件 → 单测断言落盘 → 打印 → 交互 的顺序。
