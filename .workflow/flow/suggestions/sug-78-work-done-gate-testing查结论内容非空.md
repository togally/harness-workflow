---
id: sug-78
title: work-done gate testing 阶段查 `## 结论` 内容非空（防 test-evidence 模板裸过）
status: pending
created_at: 2026-05-10
priority: medium
---

# sug-78：work-done gate testing 阶段查 `## 结论` 内容非空

## 现状

`src/harness_workflow/workflow_helpers.py` `_is_stage_work_done` 对 testing stage 的检查：

```python
def _has_conclusion_heading(text: str) -> bool:
    import re as _re
    return bool(_re.search(r"(?:^|\n)##\s*§?结论", text))

if stage == "testing":
    if operation_type == "bugfix":
        report = req_flow / "test-evidence.md"
    else:
        report = req_flow / "test-report.md"
    if not report.exists():
        return False
    content = report.read_text(encoding="utf-8")
    return _has_conclusion_heading(content)
```

**漏洞**：仅检查文件存在 + 含 `## 结论` heading；不查 heading 之后的**内容**。

## 触发场景

bugfix-12（harness archive 输入未识别时误归档首个 done req）executing → testing 流转：

- `harness bugfix` 创建 bugfix workspace 时自动生成 `test-evidence.md` 模板
- 模板自带：
  ```markdown
  ## 结论

  - [ ] 通过 — 可进入验收
  - [ ] 未通过 — 需继续修复
  ```
- 这份**内容空白的模板**已能让 `_has_conclusion_heading` 返回 True，work-done gate 直接放行
- 结果：testing stage 被自动连跳到 acceptance，testing 子 agent 没派、`5 项合规扫描 + 独立 PASS/FAIL 决策`不强制；只有靠主 agent 在 acceptance 之前补救填实 test-evidence.md

实证：bugfix-12 `harness next` 一次性 `Workflow advanced to testing` + `Workflow advanced to acceptance` 连跳。

## 评估方案

加强 `_has_conclusion_heading` 或加新校验函数 `_has_conclusion_content`：

1. **方案 A（最小改动）**：检查 `## 结论` heading 后**至少一行非模板内容**（不是 `- [ ]` 空 checkbox 行）：
   ```python
   def _has_conclusion_content(text: str) -> bool:
       import re as _re
       m = _re.search(r"(?:^|\n)(##\s*§?结论\b.*?)(?=\n##\s|\Z)", text, _re.DOTALL)
       if not m:
           return False
       body = m.group(1)
       # 移除空 checkbox 行 + 空白行；剩余至少 1 行非空
       non_empty_lines = [
           l for l in body.splitlines()[1:]
           if l.strip() and not _re.match(r"^\s*-\s*\[\s*\]\s", l)
       ]
       return len(non_empty_lines) > 0
   ```

2. **方案 B**：检查 testing 阶段必须有 `[x]` 已勾选行（PASS/FAIL 必选其一）：
   ```python
   _re.search(r"-\s*\[x\]\s+(通过|未通过|PASS|FAIL)", text, _re.IGNORECASE)
   ```

3. **方案 C**：bugfix.md / test-evidence.md 模板移除 `## 结论` heading（让 testing 子 agent 显式追加）；缺点：破坏既有 bugfix 模板兼容

推荐 **方案 B**：`[x]` 勾选是 testing 子 agent 的明确签字行为，模板的 `[ ]` 空白勾选不算；既符合 testing.md 退出条件"通过 PASS/FAIL"语义，又不破坏现有模板。

## 影响面

- `src/harness_workflow/workflow_helpers.py` `_is_stage_work_done` 扩展为方案 B 检查
- 同步 acceptance stage（`acceptance/checklist.md` 也有同型 `## 结论` heading 模板，可能有同型漏洞，需要同步修）
- 既有 bugfix / req archive 工件不受影响（已 archive 的不再走 gate）

## 工程量评估

- 1 chg，约 30 行代码 + 5 个单测；半天工时

## 承载需求

- 触发：bugfix-12 / executing → testing 阶段流转实证
- 承载：单独 bugfix 或与 sug-75/76/77 合并到下一个"流程加固"小 req
