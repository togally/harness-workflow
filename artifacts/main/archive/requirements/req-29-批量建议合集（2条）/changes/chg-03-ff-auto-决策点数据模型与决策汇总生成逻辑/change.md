# Change

## 1. Title

ff auto 决策点数据模型与决策汇总生成逻辑

## 2. Goal

- 定义 `--auto` 模式的决策点数据契约（`DecisionPoint` dataclass + `decisions-log.md` 读写 helper + `决策汇总.md` 渲染逻辑），并在 `stage-role.md` 对人文档契约中增补"决策汇总.md"条目——仅交付**数据层 + 契约层**，不动 `harness ff` CLI 入口。

## 3. Requirement

- `req-29`

## 4. Scope

### Included

- 新增模块 `src/harness_workflow/auto_decisions.py`（或挂到 `workflow_helpers.py` 的已有段落，由 executing 敲定低风险位置）：
  - `DecisionPoint` dataclass，字段：`id: str` / `ts: str (ISO)` / `stage: str` / `risk: Literal["low","medium","high"]` / `options: list[str]` / `choice: str` / `reason: str`。
  - `append_decision(root, req_id, point)`：把记录追加到 `.workflow/flow/requirements/{req-id}/decisions-log.md`，按 req-29 5.2 双轨约定的"agent 运行时记录"侧。自动分配单调递增 `dp-NN` id。
  - `load_decisions(root, req_id) -> list[DecisionPoint]`：解析已有日志。
  - `render_decision_summary(points, branch, req_slug) -> str`：生成对人文档 `决策汇总.md`，按风险等级分组（low / medium / high）渲染；输出路径 `artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md`（chg-04 会调这个 helper）。
- 更新 `.workflow/context/roles/stage-role.md` 的"对人文档输出契约"表格：在现有 7 个阶段文件之外新增一条"acceptance 前：决策汇总.md（req 级，由 harness ff --auto 生成）"，或在 acceptance 行注明该文档与 `验收摘要.md` 并列产出。
- 新增 `tests/test_auto_decisions.py`：覆盖 dataclass 序列化 / 反序列化、日志追加幂等、`render_decision_summary` 分组渲染、空日志场景。

### Excluded

- 不扩展 `harness ff` CLI（由 chg-04 负责）。
- 不实现 5.1 阻塞清单的检测函数（由 chg-04 负责）。
- 不实现 `--auto-accept` 三档交互逻辑（由 chg-04 负责）。
- 不改已有的对人文档（需求摘要 / 变更简报 / 验收摘要 等）。

## 5. Acceptance

- Covers requirement.md **AC-02（数据契约）**：`DecisionPoint` 字段定义完整、可序列化、日志读写幂等；每次自主决策写入一行追加记录，格式固化且可解析。
- **间接服务 AC-01**：acceptance 前打印的决策点汇总靠 `render_decision_summary` 渲染，chg-04 调用其结果。
- `stage-role.md` 新增"决策汇总.md"契约行，字段名与现有 7 行风格一致。
- 单测覆盖 dataclass 往返、日志追加、汇总渲染三类核心逻辑。

## 6. Risks

- **R1 契约漂移**：若 `DecisionPoint` 字段后续被 chg-04 扩展（如新增 `agent_level`、`source_stage_file`），日志格式变更会破坏老日志 → 固化字段顺序 + 预留 `extra: dict | None` 扩展位；序列化用"每条 fenced YAML block + 分隔标记"而非纯 Markdown 表格，便于未来扩展。
- **R2 位置放错**：模块放在 `workflow_helpers.py` 还是独立文件？独立文件便于测试和职责隔离，但要求 `workflow_helpers` 反向 import → 建议独立文件 `src/harness_workflow/auto_decisions.py`，仅被 `harness_ff.py` 和测试 import，避免反向依赖。
- **R3 stage-role 改动**：修改契约文件属于全仓基础设施变更，需在 change.md / plan.md 明确列出修改行，避免 reviewer 误判越界。
