---
req_id: req-50
chg_id: chg-05
title: dogfood + reviewer 加项 + llm-only-docs lint 收口
ts: 2026-04-29T00:00:00+00:00
operation_type: session-memory
---

## §改动文件清单

| 文件 | 操作 |
|------|------|
| `.workflow/context/roles/reviewer.md` | 追加 3 段 lint 项（LLM-only / stage 自检 / done 防回退） |
| `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/reviewer.md` | mirror 同步（cp，diff=0） |
| `.workflow/context/checklists/review-checklist.md` | 追加 4 段 lint 项（LLM-only / stage 自检 / contract+fix-checklist / done 防回退） |
| `src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/review-checklist.md` | mirror 同步（cp，diff=0） |
| `src/harness_workflow/validate_contract.py` | 新增 `_lint_llm_only_docs()` 函数 + `llm-only-docs` contract 分支 |
| `src/harness_workflow/cli.py` | `--contract choices` 追加 `llm-only-docs` |
| `tests/test_req50_dogfood.py` | 新增 dogfood 测试套件（TC-01 ~ TC-06，27 个测试用例） |

## §核心变更

**reviewer.md 新增段：**
- `## LLM-only 文档 lint`：前 3 条 + frontmatter + prose 限制检查项
- `## 新加 stage 自检`：不可合并理由自证
- `## done 主动入池防回退`：done.md SOP 防回退检查

**review-checklist.md 新增段：**
- 上述 3 段 lint 项同步
- `## 新加 contract 配套 fix-checklist`：继承 req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）经验

**validate_contract.py 新增：**
- `_lint_llm_only_docs(root)` 函数：仅扫机器型模板（含 operation_type 字段），session-memory 类型 title 豁免
- `run_contract_cli` llm-only-docs 分支：PASS/FAIL 输出

**cli.py：**
- `--contract choices` 追加 `llm-only-docs`

**tests/test_req50_dogfood.py：**
- TC-01：5-stage 完整流转验证（27 test cases，全部 PASS）
- TC-02：D5=B legacy 兼容
- TC-03：harness next 单入口 + pending gate
- TC-04：done 不产 sug 入池
- TC-05：12 个模板（5 核心 + 7 验证交付）渲染正常 + llm-only-docs lint 自调用
- TC-06：reviewer.md / review-checklist.md 新加项 grep 验证 + scaffold mirror 同步

## §验证结果

- `pytest tests/test_req50_dogfood.py -v` → 27 passed ✅
- `harness validate --contract llm-only-docs` → PASS exit 0 ✅
- `harness validate --contract artifact-placement` → PASS exit 0 ✅
- 全量回归：33 failed（全部为 req-50 前历史失败，chg-05 零新增 fail）✅

## §决策记录

- `_lint_llm_only_docs` 仅检查含 `operation_type` 字段的机器型模板，脚手架模板（AGENTS.md / CLAUDE.md 等）跳过
- `session-memory` 类型 `title` 字段豁免（用 `stage` 替代，语义等价）
- review-checklist.md 新增第 4 段 `## 新加 contract 配套 fix-checklist`（plan.md 未明确，按 req-48 经验补）

✅
