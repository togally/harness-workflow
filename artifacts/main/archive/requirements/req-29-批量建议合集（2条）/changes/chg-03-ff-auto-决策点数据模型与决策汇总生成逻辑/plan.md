# Change Plan

## 1. Development Steps

### Step 1: 新建 `src/harness_workflow/auto_decisions.py`

- 定义 `DecisionPoint` dataclass（frozen=True），字段 `id` / `ts` / `stage` / `risk` / `options: tuple[str,...]` / `choice` / `reason` / `extra: Mapping[str, str] | None = None`。
- `risk` 用 `Literal["low","medium","high"]`；非法值在序列化前 assert。
- 决策点 id 由 `_next_decision_point_id(log_path) -> str` 按现有日志里最大 `dp-NN` +1 分配。

### Step 2: 实现日志追加/读取

- `append_decision(root: Path, req_id: str, point: DecisionPoint) -> Path`：
  - 目标路径 `.workflow/flow/requirements/{req_id}/decisions-log.md`，不存在则创建目录与文件（含 header `# Decisions Log`）。
  - 每条决策追加为 fenced YAML block（`\`\`\`yaml decision\n...\n\`\`\``），字段按固定顺序。
  - 返回写入路径。
- `load_decisions(root: Path, req_id: str) -> list[DecisionPoint]`：
  - 解析所有 fenced yaml block，按 id 排序返回；文件不存在时返回 `[]`。
  - 对字段缺失/越界容错：未知字段放到 `extra`，不抛异常；非法 `risk` 保留原值但 log warning。

### Step 3: 实现汇总渲染

- `render_decision_summary(points: Sequence[DecisionPoint], *, req_id: str, req_title: str) -> str`：
  - Markdown 输出，按风险分组：`## 高风险（human-must-ack）` / `## 中风险` / `## 低风险`。
  - 每条决策渲染为 `- [dp-NN] [stage] {choice}（risk={risk}，ts={ts}）\n  - 选项：{options}\n  - 理由：{reason}`。
  - 顶部加一句汇总：`共 N 条决策，其中 high=X, medium=Y, low=Z`。
  - **不**写盘（纯函数），调用方决定落到哪里。

### Step 4: 更新 `stage-role.md` 对人文档契约

- 在"契约 3：中文命名 + 阶段粒度"表格中新增一行：
  - `acceptance（前置）` / `决策汇总.md` / `req` / `主 agent（ff --auto 生成）`
- 在"契约 4：硬门禁"下追加一条：
  - `当 ff_mode=true 且 --auto 被激活时，acceptance 入口前必须产出 决策汇总.md；未产出视为硬门禁违反。`
- 保持现有 7 行字段名和顺序不变。

### Step 5: 新增 `tests/test_auto_decisions.py`

- `test_decision_point_roundtrip`：构造 point → append → load → 等值断言。
- `test_append_is_idempotent_on_same_id`：同 id 重复 append 抛异常或覆盖（executing 阶段选其一，建议抛异常更安全）。
- `test_load_empty_log_returns_empty_list`
- `test_render_summary_groups_by_risk`：混合 low/medium/high 构造 → 渲染后每组含预期条目、顶部 count 正确。
- `test_render_summary_handles_empty_points`：返回 "无决策点" 兜底文案。
- `test_next_decision_point_id_monotonic`：日志里已有 `dp-03`，新增 id=`dp-04`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_auto_decisions.py -v` → 6 个用例全绿。
- `grep -rn "DecisionPoint\|append_decision\|render_decision_summary" src` 仅命中本模块 + 未来 chg-04 的调用点。
- `git diff stage-role.md` 仅命中"契约 3 表格新增行" + "契约 4 新增硬门禁段"，不破坏已有字段。

### 2.2 Manual smoke / integration verification

- 手工构造一个 fake req（`.workflow/flow/requirements/req-99/`），用 Python REPL 调用 `append_decision` 写 3 条（low/medium/high），再调 `render_decision_summary` 打印检查分组与文案。

### 2.3 AC Mapping

- AC-02 → Step 1 + Step 2 + Step 5（数据契约与日志读写）。
- 间接支撑 AC-01 → Step 3（渲染逻辑供 chg-04 调用）。

## 3. Dependencies & Execution Order

- 不依赖 chg-01 / chg-02，可并行。
- 是 chg-04 的**强前置**：chg-04 需要 import `DecisionPoint` / `append_decision` / `render_decision_summary`。
- 与 chg-05 端到端 smoke 构成链式依赖：chg-03 → chg-04 → chg-05。
