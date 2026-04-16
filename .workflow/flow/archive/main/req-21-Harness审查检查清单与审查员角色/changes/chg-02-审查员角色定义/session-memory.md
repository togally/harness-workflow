# Session Memory: chg-02-审查员角色定义

## Stage
executing

## 执行摘要
已完成审查员角色定义文件的编写。

### 关键动作
- 读取 planning.md、done.md、testing.md 作为角色文件风格参考
- 定义审查员角色的职责边界、允许/禁止行为、退出条件
- 设计 pass/reject/needs_rework 三种审查结论模板
- 编写 `.workflow/context/roles/reviewer.md`

### 产出文件
- `.workflow/context/roles/reviewer.md`

## 关键决策
- 审查员独立于执行者和测试者，不得直接修改被审查代码/文档
- 审查结论必须产出审查结论文档（review-report.md 或 review-conclusion.md）
- 明确引用 `.workflow/context/checklists/review-checklist.md` 作为强制审查依据

## 遇到的问题
- 无阻塞问题

## 下一步任务
- 等待 chg-03 完成后进入 testing 阶段
