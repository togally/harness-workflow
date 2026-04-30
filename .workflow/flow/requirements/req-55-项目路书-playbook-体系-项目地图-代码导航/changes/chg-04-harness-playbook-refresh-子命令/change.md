---
id: chg-04
title: "harness playbook-refresh 子命令"
req: req-55
created_at: 2026-04-30
---

## 目标

新增 `harness playbook-refresh` 子命令，仅刷新 `artifacts/project/playbooks/` 内 HTML 注释定界的 `<!-- AUTO:* -->` 自动区段（技术栈 / scripts / 顶层目录树 / 各 `domains/<领域>/code.md` 文件清单 / `code-map.md` 中各领域位置字段），人工写入区一律 byte-identical 不动（OQ-1=B 路径定位）。

## 范围（Scope）

### Included

- **新增 `src/harness_workflow/tools/harness_playbook_refresh.py`**：
  - 入口 `main(args) -> int`：解析 `--root` / `--dry-run`；
  - 调用 chg-03 子包的 `domain_inference` 拿当前领域列表；
  - 复用 chg-03 `templates.py` 的 AUTO 区段 marker；
  - 实现 `replace_auto_section(file_path, marker, new_content) -> bool` helper：用正则匹配 `<!-- AUTO:NAME -->...<!-- /AUTO:NAME -->` 区段，替换内容；区段格式破损时 abort + stderr 提示用户先修复定界。
  - 仅刷新 5 类 AUTO 区段（chg-01 §4 列出），其他文件 / 段落零修改。
- **修改 `cli.py`**：注册 `playbook-refresh` 子命令，dispatch 到 `harness_playbook_refresh.main`。
- **新增 pytest 用例 ≥ 3 条**（`tests/test_playbook_refresh.py`）：
  - `test_refresh_only_replaces_auto_sections`：构造 fixture（人工区 + AUTO 区），跑 refresh 后 diff 仅 AUTO 段内容变化。
  - `test_refresh_aborts_on_broken_marker`：构造缺 `<!-- /AUTO:STACK -->` 闭合的 fixture，refresh 应 stderr + exit ≠ 0。
  - `test_refresh_dry_run`：`--dry-run` 不落盘，stdout 打印 diff。
- **新增 dogfood TC**（`tests/test_playbook_refresh_dogfood.py`）：subprocess + tmpdir + `runtime.yaml` 断言。

### Excluded

- 不实现漂移检测（chg-05 负责）。
- 不动 install 行为 / 不改 chg-03 子包公共 API。
- 不刷新人工写入区 / 不改路书内容（如关键词 / 领域职责描述等），人工内容只增不减。

## 依赖

- 上游：chg-03（init_playbook 子包；本 chg 复用 `domain_inference` + `templates.py` 的 AUTO marker 定义）。
- 下游：chg-05 复用本 chg 落地的 `replace_auto_section` helper 与"AUTO 区段格式破损 abort" 语义（漂移检测项之一）。

## 验收（Acceptance）

- AC-04.1：fixture 跑 refresh 后，AUTO 区段外行 byte-identical（diff 为空）。
- AC-04.2：fixture 跑 refresh 后，AUTO 区段内容按当前项目状态刷新（如 `<!-- AUTO:STACK -->` 区段内含最新 dependency 列表）。
- AC-04.3：AUTO 区段格式破损时 refresh exit ≠ 0 + stderr 含 "AUTO marker broken"。
- AC-04.4：`--dry-run` 不落盘 + stdout 打印 diff。
- AC-04.5：dogfood TC PASS。
- AC-04.6：harness-workflow 自身仓 `harness playbook-refresh --dry-run` 在本 chg 落地后 exit 0（baseline 状态）。

## 风险与缓解

- 风险 R-1：用户在 AUTO 区段内手动加了内容，refresh 会丢失。
  缓解：refresh 启动前对每个 AUTO 区段做"格式合法性校验"，若 marker 闭合 OK 但内容明显偏离生成器预期（如含中文人话注释），abort + stderr 提示用户先把内容迁出 AUTO 区段。具体启发式由 executing 阶段定，best-effort，不是硬约束。
- 风险 R-2：路径漂移（`code-map.md` 中"位置"字段引用了不存在的 `domains/<领域>/`）。
  缓解：refresh 仅按当前文件树内容刷新位置字段，遇引用空领域时不删除条目（路书只读语义），仅更新位置；删除由人工或后续 req 决定。
