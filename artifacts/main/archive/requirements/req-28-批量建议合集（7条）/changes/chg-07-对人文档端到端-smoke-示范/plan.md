# Change Plan

## 1. Development Steps

### Step 1：设计 smoke 骨架

- 新增 `tests/test_human_docs_e2e.py`（或 `tests/smoke_human_docs.py`，位置以 `tests/` 下现有 e2e 风格为准）。
- 结构：
  ```python
  def test_req_full_cycle_produces_six_human_docs(tmp_path):
      repo = _init_harness_repo(tmp_path)
      _create_req(repo, "demo")
      _write_req_summary(repo, "demo")
      _advance_next(repo)              # → planning
      _create_change(repo, "c1")
      _write_change_brief(repo, "demo", "c1")
      _advance_next(repo)              # → executing
      _write_impl_note(repo, "demo", "c1")
      _advance_next(repo)              # → testing
      _write_test_conclusion(repo, "demo")
      _advance_next(repo)              # → acceptance
      _write_acceptance_summary(repo, "demo")
      _advance_next(repo)              # → done
      _write_done_summary(repo, "demo")
      assert_validate_human_docs_ok(repo, req_id)
  ```
- 每个 `_write_*` 用最小字段写对人文档，文件路径按契约 2/3。

### Step 2：bugfix 分支 smoke

- 在同一 test 或独立 test 中用 `harness bugfix "demo-fix"` 触发：
  - 确认 runtime.yaml 的 operation_type 字段（依赖 chg-02 已合入）。
  - regression 阶段产 `回归简报.md`；executing 产 `实施说明.md`；done 产 `交付总结.md`。
  - 调 `harness validate --human-docs --bugfix bugfix-01` 断言 ok。

### Step 3：接入 chg-05 的校验 CLI

- 在 smoke 里直接 import `validate_human_docs` 函数（避免启动子进程）：
  ```python
  from harness_workflow.validate_human_docs import validate_human_docs
  items = validate_human_docs(repo, "req-01")
  assert all(i.status == "ok" for i in items)
  ```
- 失败时打印 missing path，便于定位。

### Step 4：req-28 自身示范的闭环兜底

- 本 change 同级目录的 `变更简报.md` 已产出（plan 阶段 subagent 负责）。
- 在 plan.md / change.md 中明确记录：后续 executing 每个 change 须产 `实施说明.md`；testing 产 `测试结论.md`；acceptance 产 `验收摘要.md`；done 产 `交付总结.md`。
- 结尾在本仓库跑一次 `harness validate --human-docs --requirement req-28`，期望随推进逐步变全 ok；如果执行到 done 时不全绿，视为 AC-11 未通过。

### Step 5：性能与 CI 约定

- smoke 脚本加 `@pytest.mark.slow`，支持 `--fast` 跳过 bugfix 分支。
- 在 `pytest.ini` / `pyproject.toml` 的 marker 注册位置补 `slow: end-to-end slow smoke`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_human_docs_e2e.py -v -m slow` 全绿。
- `harness validate --human-docs --requirement req-28` 在 req-28 全程推进结束后必须全 ok。
- `grep -n "validate_human_docs" tests/test_human_docs_e2e.py` 非空。

### 2.2 Manual smoke / integration verification

- 手动按 req-28 实际推进链路观察 6 份对人文档是否真实产出：
  1. `artifacts/main/requirements/req-28-批量建议合集（7条）/需求摘要.md`（已产出）
  2. `changes/chg-{01..07}/变更简报.md`（本 change 完成后应齐全）
  3. `changes/chg-{01..07}/实施说明.md`（由各 executing 子角色产出）
  4. `测试结论.md` / `验收摘要.md` / `交付总结.md`（后续 stage 产出）

### 2.3 AC Mapping

- AC-11 -> Step 1/2/3/4 + 2.1 + 2.2
- AC-07（端到端）-> Step 1/2 + 2.1

## 3. Dependencies & Execution Order

- 严格依赖 chg-05 已合入（`validate_human_docs` 可用）。
- 依赖 chg-02 已合入（bugfix 分支 smoke 用到 `operation_type` 字段）。
- 为 req-28 的收尾 change，建议与 testing 阶段并行准备。
