# Session Memory

## 1. Current Goal

- 实现 `--auto` 模式的决策点数据层：DecisionPoint / decisions-log.md 读写 / 决策汇总.md 渲染，并把对人文档契约加到 stage-role.md。覆盖 req-29 AC-02，支撑 AC-01。

## 2. Current Status

- planning 阶段已产出：change.md / plan.md / 变更简报.md。
- 不依赖 chg-01 / chg-02；是 chg-04 的强前置。

## 3. Validated Approaches

- 决策日志用 fenced YAML block 而非 markdown 表格，便于未来字段扩展且可解析。
- 模块放在独立文件 `auto_decisions.py`，不塞 `workflow_helpers.py`，避免反向依赖与文件膨胀。
- `render_decision_summary` 做纯函数，不写盘，让调用方（chg-04）决定目标路径，符合单一职责。

## 4. Failed Paths

- Attempt: 无
- Failure reason: n/a
- Reminder: 不要在 chg-03 里扩 harness ff CLI；那是 chg-04 的活。

## 5. Candidate Lessons

```markdown
### 2026-04-19 数据契约与 CLI 入口分 change 的价值
- Symptom: 数据契约、CLI、交互三层混在一个 change 会导致 change 粒度过大，回归和 review 都吃力。
- Cause: "一个功能一个 change"太粗，需要按"层次"切：数据 / 入口 / 端到端。
- Fix: 数据 contract 先单独合入（chg-03），CLI 再调 contract（chg-04），smoke 收尾（chg-05），方便 bisect 与回滚。
```

## 6. Next Steps

- executing 接手后：先定 `DecisionPoint` 字段，写单测把契约钉死，最后再实现 helper 实体。
- `stage-role.md` 的改动只动对人文档契约两处，其他字段一个字不改。

## 7. Open Questions

- 日志 append 同 id 冲突时是"抛异常"还是"覆盖"？建议抛异常（更安全），由 executing 阶段按 low-risk 敲定。
- 是否应该把日志路径也收到 `artifacts/` 下而非 `.workflow/flow/`？req-29 5.2 明确了"运行时日志放 flow，用户汇总放 artifacts"双轨，故按需求不改。

## 8. Executing Log（2026-04-19）

- ✅ Step 1 新建 `src/harness_workflow/decision_log.py`（394 行，frozen dataclass + 7 导出符号 + `BLOCKING_CATEGORIES`）。决策：模块名用 briefing 的 `decision_log.py`（不是 plan 的 `auto_decisions.py`，plan 允许 executing 定 low-risk 位置）；日志序列化用 fenced YAML block；ID 自动分配，显式 id 不覆盖。
- ✅ Step 2 `append_decision` / `read_decision_log` 实现，覆盖首次建文件+表头、ID 单调、显式 id 保留、双引号与反斜杠转义 round-trip。
- ✅ Step 3 `render_decision_summary` 按 high → medium → low 分组，未知 risk 并入 low；`write_decision_summary` 推断 slug 目录，找不到兜底 `{req_id}`。
- ✅ Step 4 `is_blocking_decision` 对 5.1 的 8 条阻塞类别做 keyword 匹配；`BLOCKING_CATEGORIES` 硬编码 8 条。
- ✅ Step 5 `.workflow/context/roles/stage-role.md` 与 scaffold 同名文件追加"决策汇总.md"契约条目；`diff -q` = 0。
- ✅ Step 6 `tests/test_decision_log.py`（218 行，14 用例）全绿：append / roundtrip / 空文件 / 分组渲染 / 空列表兜底 / 写盘路径 / slug 兜底 / 阻塞 rm -rf / 阻塞 --force / 非阻塞低风险 / 阻塞依赖变更 / BLOCKING_CATEGORIES 长度校验。
- ✅ Step 7 全量 `python3 -m unittest discover tests` 从 145 → 159，OK(skipped=36)，无回归。
- ✅ Step 8 `artifacts/.../chg-03/实施说明.md` 产出，字段完整。

## 9. Handoff to chg-04

- chg-04 的 CLI 入口应：(a) 在每次做决策前调 `is_blocking_decision`，命中则停下打印 `BLOCKING_CATEGORIES` 对应条目；(b) 非阻塞场景构造 `DecisionPoint` 调 `append_decision`，`risk` 字段按 5.3 三档显式填写；(c) acceptance 入口前调 `write_decision_summary(root, req_id, branch)` 一次性产出 `决策汇总.md`，路径返回值可直接 print 给用户 ack。
- 不需要在 chg-04 额外做 YAML 解析；用 `read_decision_log` 拿 list 即可。
