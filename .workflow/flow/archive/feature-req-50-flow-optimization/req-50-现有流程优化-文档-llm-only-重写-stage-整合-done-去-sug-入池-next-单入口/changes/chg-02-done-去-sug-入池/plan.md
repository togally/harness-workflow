---
id: chg-02
title: done 阶段去掉 sug 入池职责
requirement: req-50
operation_type: plan
---

# Change Plan

## 1. Development Steps

### Step 1：done.md 文档改写

- 删除「### Step 6: 输出回顾报告与建议转 suggest 池」标题中的「与建议转 suggest 池」部分。
- 删除 Step 6 内「- 提取 `done-report.md` 中的改进建议，自动创建 suggest 文件」一行。
- 删除「## 建议转 suggest 池」整段（包含 4 步「提取 / 过滤去重 / 创建 / 记录」描述）。
- 「## 退出条件」section：删除「- [ ] `done-report.md` 中的改进建议已提取（如有）」。
- 「## 完成前必须检查」section：删除第 1 条「`done-report.md` 中的改进建议已提取并写入 suggest 池（如存在）」。
- 「## 禁止的行为」section：删除「- 不得遗漏 `done-report.md` 中的改进建议提取」。
- 「## 允许的行为」section：「- 创建 suggest 文件到 `.workflow/flow/suggestions/`」改写为「- （可选）通过 `harness suggest` CLI 入口创建 sug 文件——仅在用户主动请求时」。
- 在「## 流转规则」之前新增软提示段：「## 改进点处置（req-50 / chg-02）：done 阶段不再主动入池；如六层回顾发现改进点，建议在交付总结输出后由用户主动 `harness suggest "<text>"` 入池。」

### Step 2：experience/roles/done.md 清理

- 读取 `.workflow/context/experience/roles/done.md`（若存在）。
- 删除 / 标废止包含「自动入池 / 主动扫改进 / done 入 sug」类经验条目（grep `入池\|主动扫\|sug\|建议转`）。
- 在文件末尾追加新经验段：
  ```markdown
  ## 经验：done 阶段不主动入池（req-50 / chg-02）

  ### 场景
  done 阶段六层回顾发现改进点。

  ### 经验内容
  done 不再主动调 `create_suggestion` 入池。改进点处置由用户主动 `harness suggest "<text>"` 走主流程。

  ### 来源
  req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）/ chg-02（done 阶段去掉 sug 入池职责）
  ```

### Step 3：review-checklist.md 同步

- 读取 `.workflow/context/checklists/review-checklist.md`。
- 删除含「sug 入池 / 改进建议提取 / done 自动入池」相关 lint 项（如存在）。

### Step 4：CLI helper 清理

- grep `auto_extract_suggestions\|extract_suggestions_from_done_report` 等 helper 名（若存在则删除或标 deprecated）。
- `harness suggest` CLI 子命令本身不动（grep 确保 `--create` / `--list` / `--apply` / `--delete` / `--archive` 子命令完整）。

## 2. Verification Steps

### 2.1 单元测试 / 静态核对

- `grep -n "建议转\|自动入池\|主动扫\|extract.*suggestion" .workflow/context/roles/done.md` 命中 = 0。
- `grep -n "harness suggest" .workflow/context/roles/done.md` 仅命中软提示段（≤ 2 处）。
- `python -c "import subprocess; r = subprocess.run(['harness', 'suggest', '--list', '--root', '.'], capture_output=True); assert r.returncode == 0"` 主动入口可用。
- pytest test_done_role.py（若存在）/ 新增 test_done_no_auto_suggest.py 覆盖 done subagent SOP grep 检查。

### 2.2 手工 smoke / 集成验证

- 跑 dogfood req（chg-05 提供）到 `done` stage，确认 `.workflow/flow/suggestions/` 在 done 阶段执行后无新 sug 文件出现（前提：dogfood req 不含手工 `harness suggest` 调用）。
- 手工 `harness suggest "test from chg-02 verification"` 仍能正常创建 sug 文件。

### 2.3 AC 映射

- AC-05 → Step 1 + Step 2 + 2.1 grep + 2.2 dogfood + 主动入口可用。

## 3. 依赖与执行顺序

- 依赖 chg-01：本 chg 引用 stage 名（`analysis` / `done`）需先稳定。
- 内部硬序：Step 1 → Step 2 → Step 3 → Step 4。
- 不依赖 chg-03 / chg-04（文档重写）。

## 4. 测试用例设计

> regression_scope: targeted  # 仅改 done.md 文档与少量 helper（若存在），非核心 sequence / schema 改动
> 波及接口清单：
> - `.workflow/context/roles/done.md`（Step 6 / 退出条件 / 禁止行为 / 允许行为 / 完成前必须检查）
> - `.workflow/context/experience/roles/done.md`（经验段）
> - `.workflow/context/checklists/review-checklist.md`（lint 项）
> - `src/harness_workflow/workflow_helpers.py::auto_extract_suggestions_from_done_report`（若存在则废止）
> - `src/harness_workflow/cli.py::suggest_parser`（保持不动，断言子命令完整）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|---|---|---|---|---|
| TC-01 | `grep -n "建议转\|自动入池\|主动扫" done.md` | 命中 = 0（除软提示段更新版） | AC-05 | P0 |
| TC-02 | done.md 「## 退出条件」section grep `改进建议已提取` | 命中 = 0 | AC-05 | P0 |
| TC-03 | done.md 「## 禁止的行为」section grep `不得遗漏.*改进建议` | 命中 = 0 | AC-05 | P0 |
| TC-04 | `harness suggest --create "test"` 在 tmpdir 执行 | 退出码 0；`.workflow/flow/suggestions/` 出现新 sug 文件 | AC-05 | P0 |
| TC-05 | done subagent SOP 模拟跑：done-report.md 含「## 改进建议」段 3 条 | 跑完 done 阶段后 `.workflow/flow/suggestions/` 无新 sug 文件 | AC-05 | P0 |
| TC-06 | `grep "harness suggest" done.md` | 仅命中软提示段（≤ 2 处） | AC-05 | P1 |
| TC-07 | `harness suggest --list` / `--apply` / `--delete` / `--archive` 子命令 | 全部存在且 `--help` 可读 | AC-05 | P1 |
