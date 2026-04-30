---
id: chg-05
title: "harness playbook-check 子命令"
req: req-55
created_at: 2026-04-30
---

## 目标

新增 `harness playbook-check` 子命令，对 `artifacts/project/playbooks/` 做漂移检测 + 健康报告（OQ-1=B 路径定位），漂移返回非零 exit code 供 CI 接入。检测项覆盖：依赖 / scripts / 模块目录 / `code-map.md` 互引 / `code.md` 引用失效 / `README.md` 依赖链接失效 / 关键词为空领域 + 未填 TODO 分组报告 + `@./` 引用路径有效性 + AUTO 区段 marker 格式 + AUTO 区段被改但未跑 refresh 的兜底检测（OQ-5=A 路书只读软约束的事后审计闭环）。

## 范围（Scope）

### Included

- **新增 `src/harness_workflow/tools/harness_playbook_check.py`**：
  - 入口 `main(args) -> int`：解析 `--root` / `--dry-run` / `--strict`（漂移即 fail）；
  - 复用 chg-03 `domain_inference` + chg-04 AUTO marker 校验 helper；
  - 实现 8 类检测：
    1. `check_dependency_drift`：扫 `pyproject.toml` 依赖列表 vs `architecture.md` 提及，未提则告警。
    2. `check_scripts_drift`：扫 `pyproject.toml [tool.scripts]` / `package.json scripts` vs `runbook.md`。
    3. `check_module_dir_drift`：扫 `src/modules/* / src/domains/* / app/* / src/{pkg}/*次级` vs `domains/<领域>/`。
    4. `check_codemap_consistency`：`domains/` 子目录 ↔ `code-map.md` 条目互引完整性（双向）。
    5. `check_codefile_path_validity`：`code.md` 行内引用的文件路径是否都存在。
    6. `check_readme_dep_link`：各 `domains/<领域>/README.md` 中 "依赖领域: payment, user" 链接是否指向已存在的 `domains/<dep>/README.md`。
    7. `check_keyword_coverage`：`code-map.md` 关键词为空的领域（`关键词:` 后空白或仅 `<!-- TODO -->`）。
    8. `check_todo_inventory`：扫所有 `<!-- TODO: ... -->` 按文件分组报告。
    9. `check_local_link_validity`：`@./...` 引用路径有效性。
    10. `check_auto_marker_format`：每个 AUTO 区段闭合 marker 完整性（复用 chg-04 helper）。
- **修改 `cli.py`**：注册 `playbook-check` 子命令。
- **新增 pytest 用例 ≥ 7 条**（`tests/test_playbook_check.py`）：每类漂移 1 条 fixture + 健康仓库 exit 0 用例。
- **新增 dogfood TC**：subprocess + tmpdir + 健康 fixture exit 0 + 漂移 fixture exit 1。
- **新增 `harness validate --contract playbook-layout`**（OQ-6）：在 `validate_contract.py` 注册新契约名，调本 chg helper 做漂移检测；exit 同 `playbook-check` 但 stdout 走 validate 风格。

### Excluded

- 不实现"修复"行为（check 只报告，refresh 才改）。
- 不引入 LLM；纯静态分析。
- 不动 install / refresh 行为。

## 依赖

- 上游：chg-03（init_playbook 子包，复用 `domain_inference`）+ chg-04（AUTO marker helper）。
- 下游：CI 可在 PR 流水线中接入 `harness playbook-check --strict`，作为路书漂移闸门。

## 验收（Acceptance）

- AC-05.1：每类漂移（≥ 7 类）各 1 条 fixture，跑 check 命中并 exit ≠ 0。
- AC-05.2：健康 fixture（无漂移）跑 check exit 0 + stdout 含 "no drift detected"。
- AC-05.3：dogfood TC PASS。
- AC-05.4：`harness validate --contract playbook-layout` 注册并能调用，exit 与 `playbook-check` 等价。
- AC-05.5：harness-workflow 自身仓在 chg-03/04 落地后跑 `harness playbook-check` exit 0（baseline 状态）。
- AC-05.6：`--strict` flag：默认非 strict 时 TODO inventory 不算 fail；strict 模式下未填 TODO ≥ 1 即 exit 1。

## 风险与缓解

- 风险 R-1：检测误报（如开发环境引入临时 dep 但未提交即跑 check）。
  缓解：`--strict` 默认 off，普通模式只 stdout warning，CI 接入显式 `--strict`。
- 风险 R-2：检测项太多导致 stdout 噪声大。
  缓解：分组打印（按检测类）+ 每组限制最多 10 条，超出折叠为 "+N more"。
- 风险 R-3：本 chg 可能与 `harness validate --contract` 现有契约系统命名 / 注册方式冲突。
  缓解：实施前读 `src/harness_workflow/validate_contract.py` 现有契约注册风格，沿用同模式（OQ-6 由 executing 阶段确认）。
