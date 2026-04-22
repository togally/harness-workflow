# Change

## 1. Title

端到端 smoke 测试与对人文档示范

## 2. Goal

- 交付 req-29 的端到端 smoke：在 fake req 环境下模拟 `ff --auto` 全链路（requirement_review → testing），断言决策日志、决策汇总、阻塞拦截三件产物全部正常；同时为本 req-29 自身产出 `实施说明.md` 作为对人文档示范（不真跑 `ff --auto`）。

## 3. Requirement

- `req-29`

## 4. Scope

### Included

- 新增 `tests/test_smoke_req29.py`：
  - 使用 pytest tmp_path 构造一个 fake 仓库骨架（`.workflow/state/runtime.yaml`、`.workflow/flow/requirements/req-99/`、`artifacts/main/requirements/req-99-demo/`）。
  - 注入假 stage_iter（产生预设 DecisionPoint 序列，包含 low/medium/high 与一个触发阻塞的条目）。
  - 跑 `auto_runner.run_auto(..., auto_accept="all")` 验证：
    1. `.workflow/flow/requirements/req-99/decisions-log.md` 出现非阻塞决策，总数 = 预设数 - 阻塞数。
    2. `artifacts/main/requirements/req-99-demo/决策汇总.md` 存在，内容按 high/medium/low 分组。
    3. 阻塞场景（含 `rm -rf` 决策）单独跑时 runner 退出非零，日志不落。
  - 再跑一次 chg-02 的 `migrate_archive` 幂等用例（集成层面），验证 chg-01 + chg-02 与 ff --auto 不互踩。
- 本 change 产出面向用户的对人文档（执行阶段作品）：`artifacts/main/requirements/req-29-批量建议合集（2条）/changes/chg-05-端到端-smoke-测试与对人文档示范/实施说明.md`（由 executing 阶段填充，planning 阶段只占位说明）。
- README / 文档不改（req-29 不含文档改版）。

### Excluded

- **不**在本仓真跑 `harness ff --auto`（会污染本仓 runtime.yaml）。
- 不扩阻塞类别 / 不改数据契约 / 不改 migrate / 不改 archive 判据（这些由 chg-01~04 负责）。
- 不写跨分支 / 跨仓库的集成测试。

## 5. Acceptance

- Covers requirement.md **AC-01 ~ AC-04 的端到端整合断言**（不是单独 AC，而是 4 条 AC 在一起能跑通）。
- Covers **对人文档硬门禁**：executing 结束后 `实施说明.md` 已产出且字段齐全，满足 stage-role.md 契约 3 / 4。
- `tests/test_smoke_req29.py` 在本仓 CI / 本地 pytest 下稳定通过（不依赖外部网络、不写 runtime）。

## 6. Risks

- **R1 测试污染**：若 smoke 测试不小心写到项目真实 `.workflow/state/runtime.yaml` → 用 `monkeypatch.chdir(tmp_path)` 或把 root 参数显式传入，所有路径都以 tmp_path 为根。
- **R2 依赖前序未合**：chg-01~04 若没合入，本 change 的 smoke 会直接失败 → change.md 明确列"合入顺序"硬依赖。
- **R3 决策汇总路径解析**：`resolve_requirement_root` + branch 在 tmp_path 下可能解析异常 → 测试里显式 mock `_get_git_branch` 返回 `main`，避免真调 `git`。
