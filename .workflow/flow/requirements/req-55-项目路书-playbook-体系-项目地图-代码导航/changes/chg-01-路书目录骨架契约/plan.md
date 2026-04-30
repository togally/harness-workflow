---
id: chg-01
title: "路书目录骨架契约（playbook-layout.md）"
req: req-55
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 `.workflow/flow/repository-layout.md` §1-§3、`spec` §一/§二/§三/§六，确认契约层文档落位 = `.workflow/flow/playbook-layout.md`（机器型 → flow/），路书根目录 = `artifacts/project/playbooks/`（OQ-1=B 决策，沿用 req-51/req-52 项目级承载层规范）。
2. **写契约文档骨架**：新建 `.workflow/flow/playbook-layout.md`，frontmatter（version / owner / created_by），写 §1-§5 共 5 节；**§1 顶部第一行**显式声明"路书根目录 = `artifacts/project/playbooks/`（沿用 req-51/52 项目级承载层规范，OQ-1 决策）"。
3. **§4 列 AUTO 区段表**：枚举 5 类区段，每行字段 = `区段标记 / 所在文件 / 内容来源 / 刷新触发 / 破损语义`。
4. **§5 校验锚点**：列出 chg-04 / chg-05 实现 CLI 时必须满足的校验点清单，作为后续 chg 的 trace 锚。
5. **扩 `repository-layout.md` §2.1 项目级豁免**：把项目级豁免段从"3 类（constraints/experience/tools）"扩到"4 类（+ playbooks）"，加注 OQ-1=B 决策来源（req-55）。
6. **新增 pytest 用例**：`tests/test_playbook_layout_contract.py`，2 条断言（含 §1 顶部含 `artifacts/project/playbooks/` 声明）。
7. **跑 pytest**：`pytest tests/test_playbook_layout_contract.py -v` 看真实 PASS/FAIL。
8. **跑 harness validate**：`harness validate --human-docs && harness validate --contract artifact-placement`，exit 0 才推进。
9. **session-memory 留痕**：本 chg 落地路径 + pytest 数字 + harness validate exit code。

## 2. 产物

- `.workflow/flow/playbook-layout.md`（新增，§1 顶部声明路书根 = `artifacts/project/playbooks/`）
- `.workflow/flow/repository-layout.md`（修改，§2.1 项目级豁免 3 类 → 4 类 + playbooks，OQ-1 决策来源）
- `tests/test_playbook_layout_contract.py`（新增，2 条 TC）
- `.workflow/flow/requirements/req-55-.../changes/chg-01-路书目录骨架契约/session-memory.md`（执行日志）

## 3. 依赖

- 上游：无。
- 下游：chg-02（引用 §1-§3）/ chg-03（按 §1-§4 生成骨架）/ chg-04（按 §4 实现 AUTO 替换）/ chg-05（按 §5 实现漂移检测）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单（手工分析，本 chg 无 src/ 改动，仅新增契约文档 + 修改 repository-layout.md + 测试）：
> - .workflow/flow/playbook-layout.md（新增）
> - .workflow/flow/repository-layout.md（修改，§2.1 项目级豁免 3 类 → 4 类）
> - tests/test_playbook_layout_contract.py（新增）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 契约文档 5 节标题命中 | 读 `.workflow/flow/playbook-layout.md` | grep `^## ` 命中数 ≥ 5 | AC-01.1 | P0 |
| TC-02 AUTO 区段定义 ≥ 5 类 | 读 `.workflow/flow/playbook-layout.md` | grep `<!-- AUTO:` 命中数 ≥ 5 | AC-01.2 | P0 |
| TC-03 §1 顶部声明路书根路径 | 读 `.workflow/flow/playbook-layout.md` §1 前 5 行 | 含字面量 `artifacts/project/playbooks/`（OQ-1=B） | AC-01.1 | P0 |
| TC-04 repository-layout §2.1 豁免扩 4 类 | 读 `.workflow/flow/repository-layout.md` §2.1 段 | 含 "playbooks" 关键字 + 命中"4 类"或同义说明 | AC-09 | P0 |
