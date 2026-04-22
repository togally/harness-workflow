# Change Plan

## 1. Development Steps

### Step 1: 构造 fake 仓库骨架 fixture

- 在 `tests/test_smoke_req29.py` 开头定义 `@pytest.fixture def fake_repo(tmp_path, monkeypatch)`：
  - 创建 `.workflow/state/runtime.yaml`，设置 `current_requirement: req-99`、`stage: requirement_review`。
  - 创建 `.workflow/flow/requirements/req-99/`。
  - 创建 `artifacts/main/requirements/req-99-demo/requirement.md`（含最小合法字段）。
  - `monkeypatch.setattr(workflow_helpers, "_get_git_branch", lambda root: "main")`，避免调真 git。

### Step 2: happy path 全链路

- 预设 `DecisionPoint` 序列：
  - `dp-01 risk=low stage=requirement_review reason="命名选项 A"`
  - `dp-02 risk=medium stage=planning reason="拆分粒度"`
  - `dp-03 risk=high stage=executing reason="跨模块 import"`
- 假 `stage_iter`：把上面三条按 stage 回放。
- 跑 `run_auto(root=fake_repo, req_id="req-99", auto_accept="all", ...)`。
- 断言：
  - decisions-log.md 存在、含 3 条 fenced yaml block、id 递增。
  - 决策汇总.md 存在于 `artifacts/main/requirements/req-99-demo/`，三个分组标题齐全，顶部 count 正确。
  - `run_auto` 返回 0。

### Step 3: 阻塞场景

- 另一个用例，预设 `dp-04 reason="rm -rf artifacts/"`。
- 跑 `run_auto(auto_accept="all")` → 断言：
  - 返回值非零。
  - decisions-log.md 不含 dp-04（阻塞决策不写日志）。
  - 决策汇总.md 不生成（因未到 acceptance 前）。

### Step 4: chg-01/02 集成联动

- 第三个用例：构造 `.workflow/flow/archive/req-20-old/` 非空 + `artifacts/main/archive/` 为空。
- 调 `resolve_archive_root` 断言返回 primary（chg-01 契约）。
- 调 `migrate_archive(root, dry_run=False)` → 断言迁移完成 + legacy 清空（chg-02 契约）。
- 再次调 `resolve_archive_root` → 不再打印 `using legacy archive path` 警告。

### Step 5: 产出 `实施说明.md`（executing 阶段任务）

- 注意：planning 阶段不写代码、也不填 `实施说明.md` 正文；只在 plan.md 里声明该文档的产出契约。
- executing 阶段产出模板：
  ```markdown
  # 实施说明：chg-05 端到端 smoke 测试与对人文档示范

  ## 实施要点
  - ...

  ## 验证结果
  - tests/test_smoke_req29.py: PASS
  - 集成联动用例: PASS

  ## 已知问题
  - ...
  ```
- 路径固定：`artifacts/main/requirements/req-29-批量建议合集（2条）/changes/chg-05-端到端-smoke-测试与对人文档示范/实施说明.md`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_smoke_req29.py -v` → 3 条用例（happy path / blocking / chg-01-02 integration）全绿。
- `pytest tests/ -q` 全仓全绿（确认本 change 不回归其他）。
- `git diff tests/` 限于新增 smoke 文件 + 必要 fixture helper。

### 2.2 Manual smoke / integration verification

- **禁止** 在本仓执行 `harness ff --auto`。
- 执行 `harness status` 在 chg-01/02 合入后不再报 legacy 警告（本 change 只验收、不触发）。

### 2.3 AC Mapping

- AC-01~04 整合 → Step 2 + Step 4。
- 对人文档硬门禁 → Step 5。

## 3. Dependencies & Execution Order

- **强依赖 chg-01 / chg-02 / chg-03 / chg-04 全部合入**。是 req-29 的收尾 change。
- 完成后进入 testing / acceptance。
