# Session Memory

## 1. Current Goal

- req-29 收尾 change：端到端 smoke 覆盖 AC-01~04 整合、`实施说明.md` 示范对人文档硬门禁。

## 2. Current Status

- planning 阶段已产出：change.md / plan.md / 变更简报.md。
- 强依赖 chg-01 / chg-02 / chg-03 / chg-04 全部合入，本 change 最后跑。

## 3. Validated Approaches

- 所有 smoke 在 pytest tmp_path 下，`monkeypatch` 屏蔽 `_get_git_branch` 真调 git。
- smoke 用"注入预设 DecisionPoint 序列"的假 stage_iter，不走真正的 LLM / subagent 决策逻辑。
- `实施说明.md` 是 executing 阶段责任，planning 只约定路径和模板。

## 4. Failed Paths

- Attempt: 无
- Failure reason: n/a
- Reminder: 绝不能在本仓真跑 `harness ff --auto`，所有断言都依赖 fake 仓。

## 5. Candidate Lessons

```markdown
### 2026-04-19 收尾 change 必须同时验集成 + 对人文档
- Symptom: 单 change 都绿但整体跑不起来、或忘出对人文档导致 acceptance 卡壳。
- Cause: 只做功能断言不做双轨断言。
- Fix: 最后一个 change 专门放端到端 smoke + 对人文档示范，缺一不可。
```

## 6. Next Steps

- executing 接手：先写 fake_repo fixture，再写 happy path 用例，再写阻塞 / 集成用例。
- executing 末尾产出 `实施说明.md`，按 stage-role 契约 3 最小模板。

## 7. Open Questions

- `test_smoke_req29.py` 要不要跑在 CI 里？若 CI 无 git 环境，`monkeypatch _get_git_branch` 就够用；否则需要 skip 标记。由 executing 阶段按 low-risk 敲定。

## 8. Executing 执行记录（2026-04-19）

- ✅ 读取 change.md / plan.md / 变更简报.md + 对照 requirement.md AC-01 ~ AC-04 与 §5.1
- ✅ 新增 `tests/test_smoke_req29.py`（5 条用例，参照现有 `test_ff_auto.py` / `test_migrate_archive.py` / `test_archive_path.py` 的 fixture 风格）
  - `test_archive_lands_in_primary_by_default`（AC-03）
  - `test_migrate_archive_moves_legacy_to_primary`（AC-04，含幂等）
  - `test_ff_auto_produces_decision_summary`（AC-01 + AC-02，决策汇总三档）
  - `test_blocking_category_always_interactive`（§5.1，rm -rf + risk=low 仍阻塞）
  - `test_human_docs_checklist_for_req29`（AC-11，只读检查 req-29 artifacts）
- ✅ 中途故意不先写 `实施说明.md` → 预跑 5 用例：4 绿 1 红（AC-11 正确捕捉到缺失），证明 checklist 断言有效
- ✅ 落盘 `实施说明.md`（本 change 目录），再跑：`python3 -m unittest tests.test_smoke_req29 -v` → 5/5 OK
- ✅ 全量 `python3 -m unittest discover tests` → 171 tests（166 基线 + 5 新增），zero 回归，skipped=36 与基线一致
- Open Question 7 回答：low-risk，默认 `_get_git_branch` mock 就够，不加 skip 标记；若未来 CI 明确失败再追加条件 skip
- 所有 smoke 路径均在 `tempfile.TemporaryDirectory` 内，绝未触碰仓真实 `.workflow/state/runtime.yaml`；未跑真 `harness ff --auto` / `harness migrate archive`（briefing 硬约束）

## 9. 退出条件 checklist

- [x] plan.md 5 个步骤全部标记 ✅
- [x] 内部测试：单测 5/5 + 全量 171/171 通过
- [x] 对人文档 `实施说明.md` 已产出且字段完整
- [x] 变更范围仅限 `tests/test_smoke_req29.py` + 本 `实施说明.md` + session-memory 增补，未碰 chg-01 ~ chg-04 生产代码
- [x] 经验沉淀：本 change 的"先红再绿的 checklist 活证"可作为通用做法，但属于阶段性常识，不单列经验文件
