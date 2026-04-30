---
id: chg-02
title: "baseRole 追加代码加载规则 + CLAUDE.md 项目路书索引节"
req: req-55
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 `chg-01` 的 `playbook-layout.md` §1-§3 规范、`base-role.md` 现有硬门禁结构、`CLAUDE.md` 现有结构。
2. **base-role.md 追加硬门禁清单条目**：在文件头"硬门禁清单"列表追加 `- 硬门禁十：代码加载规则（req-55（项目路书Playbook体系） / chg-02（baseRole代码加载规则与CLAUDE索引））`（OQ-2=A）。
3. **base-role.md 追加章节**：在硬门禁九之后新增 `## 硬门禁十：代码加载规则（强制）` 章节，含 4 节（优先走路书 / 兜底规则 / 项目背景加载 / 不该做的事），4 节内容如下：
   - §1 优先走路书：先读 `@./artifacts/project/playbooks/code-map.md` → 关键词匹配 → `domains/<领域>/README.md` → `code.md` → 直接读文件，禁止 grep / glob。
   - §2 兜底规则：路书未命中时允许全局查找；兜底后必须显式声明，并以 `<!-- TODO: 待补入 code-map -->` 提示用户更新路书；不擅自改路书。
   - §3 项目背景加载：业务概念任务必须先读 `@./artifacts/project/playbooks/overview.md` 理解术语。
   - §4 不该做的事：未读 code-map 直接 grep / 跳过路书 / 修改 `artifacts/project/playbooks/` 下任何文件（路书是只读资源，OQ-5=A 软约束 + chg-05 漂移检测兜底）。
   溯源注释指向 req-55（项目路书Playbook体系——项目地图+代码导航）/ chg-02（baseRole 代码加载规则与 CLAUDE 索引）。
4. **CLAUDE.md 追加索引节**：文件末尾追加 `## 项目路书` 段，含 4 份顶层文件（路径全部 `artifacts/project/playbooks/{overview,architecture,runbook,code-map}.md`） + `artifacts/project/playbooks/domains/<领域>/`。
5. **新增 pytest 用例**：`tests/test_baserole_playbook_section.py` 3 条 TC（结构断言 + CLAUDE.md 索引节断言 + `artifacts/project/playbooks` 路径命中数断言）。
6. **跑 pytest**：`pytest tests/test_baserole_playbook_section.py -v`。
7. **跑 harness validate**：`harness validate --human-docs`。
8. **session-memory 留痕**：grep 命中数 / pytest 数字。

## 2. 产物

- `.workflow/context/roles/base-role.md`（追加）
- `CLAUDE.md`（追加索引节）
- `tests/test_baserole_playbook_section.py`（新增）
- `.workflow/flow/requirements/req-55-.../changes/chg-02-baseRole代码加载规则与CLAUDE索引/session-memory.md`

## 3. 依赖

- 上游：chg-01（playbook-layout.md 契约文档）。
- 下游：chg-03 install 阶段产出 `artifacts/project/playbooks/` 目录后，本 chg 落地的 baseRole 规则与 CLAUDE 索引节立即对所有 agent 生效。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - .workflow/context/roles/base-role.md（追加章节）
> - CLAUDE.md（追加索引节）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 baseRole 含硬门禁十 4 节 | 读 base-role.md | grep `## 硬门禁十：代码加载规则` 命中 1 + 内部 4 节标题命中 + grep `^## 硬门禁` 命中 ≥ 8（OQ-2=A） | AC-02.1 | P0 |
| TC-02 硬门禁清单含十 | 读 base-role.md 头部硬门禁清单 | 含 "硬门禁十" | AC-02.2 | P0 |
| TC-03 CLAUDE.md 含项目路书索引 | 读 CLAUDE.md | `^## 项目路书` 命中 1 + 4 份顶层文件名命中 + grep `artifacts/project/playbooks` 命中 ≥ 4（OQ-1=B） | AC-02.3 | P0 |
| TC-04 baseRole 路径与 OQ-1 决策一致 | 读 base-role.md 硬门禁十段 | grep `artifacts/project/playbooks` 命中 ≥ 3（路书优先 / 项目背景 / 不该做的事 三处） | AC-02.1 | P0 |
