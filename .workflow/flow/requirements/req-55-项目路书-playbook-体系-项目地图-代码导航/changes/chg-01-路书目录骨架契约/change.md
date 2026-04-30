---
id: chg-01
title: "路书目录骨架契约（playbook-layout.md）"
req: req-55
created_at: 2026-04-30
---

## 目标

为 req-55（项目路书(Playbook)体系——项目地图+代码导航）建立**只描述结构、不实现 CLI** 的契约底座。把 spec §一、§二、§三的"路书结构 / 各文件内容规范 / 跨领域归属规则"以**机器可读 + 人可读**双形态写入 `.workflow/flow/playbook-layout.md`，作为后续 chg-02 / chg-03 / chg-04 / chg-05 的引用基。

## 范围（Scope）

### Included

- 新建 `.workflow/flow/playbook-layout.md`（契约文档），含 5 节：
  - **§1 顶层文件契约**：`overview.md` / `architecture.md` / `runbook.md` / `code-map.md` 4 份顶层文件的字段规范、写作原则、TODO 留白规则。
  - **§2 domains 子树契约**：`domains/<领域>/{README.md, code.md, data-model.md, notes.md}` 4 件套字段规范 + agent 加载顺序。
  - **§3 跨领域归属规则**：跨多领域流程归调用方 `notes.md`、不复制内容、全局内容归 `architecture.md` 三条。
  - **§4 HTML 注释定界规约**：列出 `<!-- AUTO:STACK -->` / `<!-- AUTO:SCRIPTS -->` / `<!-- AUTO:DIRTREE -->` / `<!-- AUTO:CODE_FILES -->` / `<!-- AUTO:CODEMAP_LOCATIONS -->` 5 类自动区段的语义、所在文件、刷新触发条件、"破损 abort"语义。
  - **§5 校验锚点**：列出 chg-04 / chg-05 实现 CLI 时必须满足的校验点（区段格式 / 文件存在性 / 关键词非空 / 依赖链接存在性）。
- 新增 pytest 契约用例 2 条（`tests/test_playbook_layout_contract.py`）：
  - `test_playbook_layout_md_exists_and_sections_complete`：断言 5 节标题命中。
  - `test_auto_section_marker_definitions_listed`：断言 §4 列出 ≥ 5 类 AUTO 区段定义。

### Excluded

- 不动 `base-role.md`（chg-02 负责）。
- 不动 `harness_install.py` / 不新增 CLI 子命令（chg-03/04/05 负责）。
- 不生成 `artifacts/project/playbooks/` 实际目录（chg-03 负责）。

## 依赖

- 上游：无。
- 下游：chg-02 引用 §1-§3 写 baseRole 规则；chg-03 按 §1-§4 生成骨架；chg-04 按 §4 实现 AUTO 区段替换；chg-05 按 §5 实现漂移检测点。

## 验收（Acceptance）

- AC-01.1：`.workflow/flow/playbook-layout.md` 存在，含 §1-§5 共 5 节标题。
  验证：`grep -c '^## ' .workflow/flow/playbook-layout.md` ≥ 5。
- AC-01.2：§4 列出 ≥ 5 类 AUTO 区段定义（`<!-- AUTO:STACK -->` 等）。
  验证：`grep -c '<!-- AUTO:' .workflow/flow/playbook-layout.md` ≥ 5。
- AC-01.3：pytest 2 条契约用例 PASS（`tests/test_playbook_layout_contract.py`）。
- AC-01.4：`harness validate --human-docs` exit 0；`harness validate --contract artifact-placement` exit 0（契约文档落 `.workflow/flow/`，机器型，合规）。

## 风险与缓解

- 风险：契约写得过细 → 后续 chg 实现被框死失去灵活性。
  缓解：契约只规定"必须有什么字段 / 区段语义"，不规定具体模板字符串；模板 string 由 chg-03 在 generator 内部决定。
