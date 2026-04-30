---
id: chg-04
title: "harness playbook-refresh 子命令"
req: req-55
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 chg-03 落地的 `playbook/templates.py` AUTO marker、`domain_inference.py`、`cli.py` 子命令注册风格。
2. **写 `harness_playbook_refresh.py`**：实现 `main(args)` + `replace_auto_section()` helper；按 chg-01 §4 列出的 5 类 AUTO 区段逐一刷新。
3. **改 `cli.py`**：注册 `playbook-refresh` subparser；加 `--root` / `--dry-run` flag。
4. **新增 pytest 用例 3 条 + dogfood TC 1 条**。
5. **跑 pytest**：`pytest tests/test_playbook_refresh*.py -v`。
6. **dogfood 实跑**：harness-workflow 自身仓 `python3 -m harness_workflow.cli playbook-refresh --dry-run` 看 stdout / exit 0。
7. **harness validate**：`harness validate --human-docs && harness validate --contract artifact-placement`。
8. **session-memory 留痕**：测试数字 + diff 行数。

## 2. 产物

- `src/harness_workflow/tools/harness_playbook_refresh.py`（新增）
- `src/harness_workflow/cli.py`（注册子命令）
- `tests/test_playbook_refresh.py`（新增，≥ 3 TC）
- `tests/test_playbook_refresh_dogfood.py`（新增，1 dogfood TC）

## 3. 依赖

- 上游：chg-03（playbook 子包：templates / domain_inference / AUTO marker 定义）。
- 下游：chg-05（playbook-check 复用 `replace_auto_section` 的"AUTO marker 破损"判定 + chg-03 的 `domain_inference`）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/harness_workflow/tools/harness_playbook_refresh.py（新增）
> - src/harness_workflow/cli.py（注册）
> - 复用：src/harness_workflow/playbook/templates.py + domain_inference.py（chg-03 落地）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 仅替换 AUTO 区段 | fixture 含人工 + AUTO 区 | refresh 后 AUTO 外 diff 为空 | AC-04.1 | P0 |
| TC-02 AUTO 区段内容刷新 | fixture 模拟项目变更（新增 dependency） | AUTO:STACK 区内含新 dep | AC-04.2 | P0 |
| TC-03 marker 破损 abort | fixture 缺闭合 marker | exit ≠ 0 + stderr 含 'AUTO marker broken' | AC-04.3 | P0 |
| TC-04 `--dry-run` | fixture + `playbook-refresh --dry-run` | git status 无新增 + stdout 打 diff | AC-04.4 | P0 |
| TC-Dogfood-01 dogfood subprocess 实跑 | tmp_path + subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'playbook-refresh', '--root', tmp]) | exit 0 + stdout 含 'refreshed' / runtime stage 字段存在 / feedback.jsonl 事件数 ≥ 1 | AC-04.5 | P0 |
| TC-05 自身仓 dry-run | harness-workflow 仓根 + `playbook-refresh --dry-run` | exit 0 | AC-04.6 | P1 |
