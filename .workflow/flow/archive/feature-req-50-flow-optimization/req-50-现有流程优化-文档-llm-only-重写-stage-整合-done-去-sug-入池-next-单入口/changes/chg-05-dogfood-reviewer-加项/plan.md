---
id: chg-05
title: dogfood + reviewer 加项 + llm-only-docs lint 收口
requirement: req-50
operation_type: plan
---

# Change Plan

## 1. Development Steps

### Step 1：validate_contract.py 新增 llm-only-docs lint

- `src/harness_workflow/validate_contract.py` 新增函数：
  ```python
  def _lint_llm_only_docs(root: Path) -> list[Violation]:
      """
      检查 .claude/skills/harness/assets/templates/*.tmpl：
      1. 每个文件首部含 `---` frontmatter + 必填字段（id / title / created_at / operation_type）
      2. grep `^## .*(背景|历史|修订说明|用户原话|设计理念|演进)` 命中 = 0
      3. 连续非 bullet（非 `- ` / 非 `|` / 非 `#` / 非空行）行数 ≤ 3
      4. 支持 HTML 注释豁免：`<!-- LLM-ONLY-LINT: skip -->`
      """
      ...
  ```
- `run_contract_cli(root, contract)`：`elif contract == "llm-only-docs": return _emit(...)` 分支。

### Step 2：cli.py choices 扩展

- `validate_parser.add_argument("--contract", choices=[..., "llm-only-docs"], ...)` 列表追加。
- `--contract all` 分发：`run_contract_cli(root, "all")` 内追加 llm-only-docs 调用。

### Step 3：tests/test_dogfood_req_full_cycle.py 新增

- 用 `tmp_path` fixture：
  ```python
  def test_dogfood_req_full_cycle(tmp_path, monkeypatch):
      # 1. harness install
      run([sys.executable, '-m', 'harness_workflow.cli', 'install'], cwd=tmp_path)
      # 2. harness requirement "dogfood"
      run([sys.executable, '-m', 'harness_workflow.cli', 'requirement', 'dogfood'], cwd=tmp_path)
      # 断言 runtime.yaml stage == "analysis"
      assert load_runtime(tmp_path)['stage'] == 'analysis'
      # 3. 模拟 analyst 产出 requirement.md / change.md / plan.md（用模板填充 fixture）
      _populate_dogfood_artifacts(tmp_path)
      # 4. harness next（analysis → executing 用户拍板模拟）
      run([sys.executable, '-m', 'harness_workflow.cli', 'next'], cwd=tmp_path)
      assert load_runtime(tmp_path)['stage'] == 'executing'
      # 5. ... executing → testing → acceptance → done（每步类似）
      # 6. 最终断言：
      #    - stage 历史含 ["analysis", "executing", "testing", "acceptance", "done"]
      #    - 零 "ready_for_execution"
      #    - 所有产出文档含 frontmatter（id / title / created_at / operation_type）
      #    - .workflow/flow/suggestions/ 不出现新 sug（done 不主动入池）
  ```
- 标 `@pytest.mark.slow`。

### Step 4：tests/test_dogfood_bugfix_full_cycle.py 新增

- 类似 Step 3 但跑 bugfix 流程：
  ```python
  def test_dogfood_bugfix_full_cycle(tmp_path):
      run([..., 'install'], cwd=tmp_path)
      run([..., 'bugfix', 'dogfood bug'], cwd=tmp_path)
      assert load_runtime(tmp_path)['stage'] == 'regression'
      # 模拟 regression / executing / testing / acceptance / done 各阶段产出
      ...
      # 最终断言：bugfix.md / diagnosis.md / session-memory.md / test-evidence.md / bugfix-交付总结.md 含 frontmatter
  ```
- 标 `@pytest.mark.slow`。

### Step 5：reviewer.md 增补 lint 项

- `.workflow/context/roles/reviewer.md`：在「## Checklist」段（如不存在则在文件末尾）追加：
  ```markdown
  ## LLM-only 文档 lint（req-50 / chg-05）

  - [ ] 新加 / 修改的 `.claude/skills/harness/assets/templates/*.tmpl` 文件含 frontmatter（必填 `id` / `title` / `created_at` / `operation_type`）
  - [ ] 新模板不含 `## 背景` / `## 历史` / `## 修订说明` / `## 用户原话` / `## 设计理念` / `## 演进` 段（运行 `harness validate --contract llm-only-docs` exit 0）
  - [ ] 连续 prose 行 ≤ 3 行（叙事性段落不应出现）

  ## 新加 stage 自检（req-50 / chg-05）

  - [ ] 新加 stage 前自检：是否可与现有 stage 合并？（同 role 同 model 强烈建议合并；如 req-50 把 requirement_review + planning → analysis）
  - [ ] 如确需新加，必须在 PR description 写明「不可合并理由」

  ## done 主动入池防回退（req-50 / chg-02 + chg-05）

  - [ ] done.md 不得含「自动提取改进建议入池」相关 SOP / 退出条件（除非用户显式拍板回归）
  ```

### Step 6：review-checklist.md 同步

- `.workflow/context/checklists/review-checklist.md`：在合适位置（如「## 文档质量」段）追加同步 checklist 项。

### Step 7：dogfood 实跑 + 修复

- 在主仓库运行 `pytest tests/test_dogfood_req_full_cycle.py tests/test_dogfood_bugfix_full_cycle.py -v --runslow`。
- 失败时：(a) 若是 chg-01 ~ chg-04 实施缺陷 → 回 chg-NN 修；(b) 若是 dogfood 测试本身缺陷 → 修测试。
- 断言通过：写入 session-memory.md 「dogfood 跑通」记录。

### Step 8：harness validate --contract llm-only-docs 自跑

- 在主仓库执行 `harness validate --contract llm-only-docs` exit 0。
- 在主仓库执行 `harness validate --contract all` exit 0（含新增 llm-only-docs 项）。

## 2. Verification Steps

### 2.1 单元测试 / 静态核对

- `pytest tests/test_dogfood_req_full_cycle.py -v` PASS。
- `pytest tests/test_dogfood_bugfix_full_cycle.py -v` PASS。
- `pytest tests/test_validate_contract_llm_only_docs.py -v`（新增 unit test 覆盖 lint helper）PASS。
- `harness validate --contract llm-only-docs` exit 0。
- `harness validate --contract all` exit 0。
- grep `.workflow/context/roles/reviewer.md` 含「LLM-only 文档 lint」「新加 stage 自检」「done 主动入池防回退」三段。

### 2.2 手工 smoke / 集成验证

- tmpdir 手工跑：
  ```
  harness install
  harness requirement "smoke req"
  cat .workflow/state/runtime.yaml | grep "stage:"  # 期望 stage: analysis
  harness next  # 期望推进到 executing（user 拍板模拟）
  ...直到 done
  cat .workflow/flow/requirements/{slug}/changes/{chg-id}/plan.md  # 期望含 frontmatter + §4 测试用例设计
  ls .workflow/flow/suggestions/  # 期望 done 后无新 sug 文件
  ```
- 故意构造一个含「## 背景」段的 .tmpl 测试文件，跑 `harness validate --contract llm-only-docs`：期望 exit 1 + 列出违规文件。

### 2.3 AC 映射

- AC-08 → Step 3 + Step 4 + Step 7 + 2.1 dogfood 测试。
- AC-09 → Step 5 + Step 6 + 2.1 grep。
- AC-10 → Step 1 + Step 2 + Step 8 + 2.1 contract lint exit 0。

## 3. 依赖与执行顺序

- 严格依赖 chg-01 ~ chg-04 全部落地：dogfood 测试需要新模板 + 新 stage sequence + 去 sug 入池后的 done 行为。
- 内部硬序：Step 1 → Step 2 → Step 3 + Step 4（并行）→ Step 5 → Step 6 → Step 7 → Step 8。
- 本 chg 是收口 chg，落地后 req-50 进入 testing / acceptance。

## 4. 测试用例设计

> regression_scope: full  # 改 contract lint（lint 规则本身）+ 新增 dogfood 测试 + reviewer lint 项；改动 lint 工具触发 full 回归
> 波及接口清单：
> - `src/harness_workflow/validate_contract.py::_lint_llm_only_docs`（新增 helper）
> - `src/harness_workflow/validate_contract.py::run_contract_cli`（分发分支扩展）
> - `src/harness_workflow/cli.py::validate_parser`（choices 扩展）
> - `tests/test_dogfood_req_full_cycle.py`（新增）
> - `tests/test_dogfood_bugfix_full_cycle.py`（新增）
> - `tests/test_validate_contract_llm_only_docs.py`（新增）
> - `.workflow/context/roles/reviewer.md`（lint 项扩展）
> - `.workflow/context/checklists/review-checklist.md`（lint 项扩展）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|---|---|---|---|---|
| TC-01 | `harness validate --contract llm-only-docs` 在主仓库 | exit 0 | AC-10 | P0 |
| TC-02 | 在 tmpdir 中构造 .tmpl 含「## 背景」段，跑 lint | exit 1 + stderr 列违规文件 | AC-09 + AC-10 | P0 |
| TC-03 | 在 tmpdir 中构造 .tmpl 缺 `id:` frontmatter 字段，跑 lint | exit 1 + stderr 列违规文件 | AC-09 + AC-10 | P0 |
| TC-04 | 含 `<!-- LLM-ONLY-LINT: skip -->` 注释的 .tmpl 含「## 历史」段 | lint exit 0（豁免生效） | AC-09 | P1 |
| TC-05 | reviewer.md grep `LLM-only 文档 lint\|新加 stage 自检\|done 主动入池防回退` | 各命中 ≥ 1 | AC-09 | P0 |
| TC-06 | review-checklist.md 同 grep | 各命中 ≥ 1 | AC-09 | P1 |
| TC-Dogfood-01 | tmpdir 完整 req 5-stage：install → requirement → next × N → done | runtime stage 历经 `analysis → executing → testing → acceptance → done`；零 `ready_for_execution`；所有产出文档含 frontmatter；done 后 suggestions/ 无新 sug | AC-08 | P0 |
| TC-Dogfood-02 | tmpdir 完整 bugfix 5-stage：install → bugfix → next × N → done | runtime stage 历经 `regression → executing → testing → acceptance → done`；所有产出文档含 frontmatter | AC-08 | P0 |
| TC-Dogfood-03 | tmpdir ff 模式：install → requirement → ff --auto --auto-accept all | runtime stage 自动推进到 `acceptance`；user 拍板点全 ack | AC-08 + chg-01 AC-07 | P0 |
| TC-07 | `harness validate --contract all` 在主仓库 | exit 0；stdout 含 `llm-only-docs: PASS` | AC-10 | P0 |
| TC-08 | 故意将 reviewer.md 的「LLM-only 文档 lint」段删除后跑 dogfood | TC-05 失败（提醒维护 reviewer 项） | AC-09 | P1 |
| TC-09 | dogfood 测试 stdout 含 `stage advanced to analysis` / `stage advanced to executing` | 含；不含 `ready_for_execution` 字串 | AC-08 | P0 |
| TC-10 | 模拟历史 req-46 archive 目录回放（`harness status` 列出归档） | 不 raise；列出原 stage 名（保持 legacy） | AC-11 | P1 |

**dogfood 必填字段（TC-Dogfood-01）**：

- 用例名：TC-Dogfood-01
- tmpdir fixture：`tmp_path` pytest fixture
- 子进程命令：`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next'], cwd=tmp_path, capture_output=True, text=True)`
- stdout 断言：`"stage advanced to executing" in stdout`（首次 next 后）
- runtime stage 断言：经 5 次 next 后 `runtime['stage'] == 'done'`
- `feedback.jsonl` 事件数断言：≥ 4 条 `stage_advanced` 事件
- 对应 AC：AC-08
- 优先级：P0

**dogfood 必填字段（TC-Dogfood-02）**：

- 用例名：TC-Dogfood-02
- tmpdir fixture：`tmp_path`
- 子进程命令：`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next'], cwd=tmp_path, capture_output=True, text=True)`
- stdout 断言：`"stage advanced to executing" in stdout`（regression 通过后）
- runtime stage 断言：经 4 次 next（regression 后）后 `runtime['stage'] == 'done'`
- `feedback.jsonl` 事件数断言：≥ 4 条 `stage_advanced` 事件
- 对应 AC：AC-08
- 优先级：P0
