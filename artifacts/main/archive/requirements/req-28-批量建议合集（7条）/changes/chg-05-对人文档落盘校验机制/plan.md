# Change Plan

## 1. Development Steps

### Step 1：定义 stage → 对人文档映射表

- 将 `.workflow/context/roles/stage-role.md` 契约 3 的表格硬编码到 `src/harness_workflow/validate_human_docs.py` 中，格式：
  ```python
  HUMAN_DOC_CONTRACT = {
      "requirement_review": ("需求摘要.md", "req"),
      "planning":           ("变更简报.md", "change"),
      "executing":          ("实施说明.md", "change"),
      "testing":            ("测试结论.md", "req"),
      "acceptance":         ("验收摘要.md", "req"),
      "done":               ("交付总结.md", "req"),
  }
  ```
- 在源码注释中标注与 stage-role.md 契约 3 的对应关系。

### Step 2：实现 validate_human_docs(target_id)

- 输入：req-id（`req-*`）或 bugfix-id（`bugfix-*`）。
- 解析 artifact 根：
  - req：`artifacts/{branch}/requirements/{req-id}-{slug}/`
  - bugfix：`artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/`
- 逐条校验：
  - req / bugfix 根目录下须有 `需求摘要.md` / `测试结论.md` / `验收摘要.md` / `交付总结.md`。
  - `changes/*/` 下每个子目录须有 `变更简报.md` 与 `实施说明.md`。
- 返回 `List[ValidationItem]`，含 `stage / expected_path / status(ok|missing|malformed)`。

### Step 3：CLI 子命令

- 在 `src/harness_workflow/cli.py`（或等价入口）新增 `harness validate --human-docs` 子选项：
  - 参数：`--requirement <id>` 或 `--bugfix <id>`；二选一必填。
  - 支持 `--branch <name>` 覆盖 artifact root。
  - 输出：人类可读表 + JSON（`--json`），缺失时非零退出码。

### Step 4：acceptance 角色 SOP 引用

- 在 `.workflow/context/roles/acceptance.md` 的 SOP "Step 1" 前插入："执行 `harness validate --human-docs --requirement <current_requirement>`，结果必须为全 ok，否则停下来回交给 executing 角色补齐。"
- 同步在 scaffold_v2 的对应文件做相同补丁。

### Step 5：新增测试 `tests/test_validate_human_docs.py`

- 用 tempdir 构造一份"6 份齐全"的 req 产物，校验 pass；
- 构造"缺少变更简报.md"的 change 子目录，校验 fail 且错误指出具体路径；
- 构造"对人文档写到 .workflow/flow/ 下"的反例，校验 fail（路径异常）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_validate_human_docs.py -v` 全绿。
- `harness validate --human-docs --requirement req-28` 若 req-28 当前只有 `需求摘要.md`，输出中其他 5 份明确列为 missing 且 exit code 非 0（符合"首次示范"语境，随 req-28 推进最终变全 ok）。
- `grep -n "harness validate --human-docs" .workflow/context/roles/acceptance.md` 非空。

### 2.2 Manual smoke / integration verification

- 在本仓库跑 `harness validate --human-docs --requirement req-28` 观察输出：planning 阶段应显示 7 份 `变更简报.md` 已产出（本 change 的交付产物之一）；其他阶段 still missing。

### 2.3 AC Mapping

- AC-09 -> Step 1/2/3/4/5 + 2.1 + 2.2
- 与 AC-11 联动（反向覆盖由 chg-07 完成）。

## 3. Dependencies & Execution Order

- 与 chg-04 / chg-06 无冲突，可并行。
- chg-07 的 smoke 会直接调用本 CLI，因此 chg-05 需先于 chg-07 完成。
