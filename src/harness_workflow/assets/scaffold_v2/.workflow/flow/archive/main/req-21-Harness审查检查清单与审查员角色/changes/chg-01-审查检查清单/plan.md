# chg-01-审查检查清单 执行计划

## 执行步骤

1. **分析现有检查缺口**
   - 读取 `.workflow/context/roles/done.md`，提取现有六层检查结构作为参考
   - 读取 `.workflow/context/roles/requirement-review.md`（如存在），了解 requirement_review 阶段的审查要点
   - 确认 req-20 遗漏 `artifacts/requirements/` 的根本原因，在清单中补强

2. **设计清单结构**
   - 定义清单头部：用途、适用阶段、更新规则
   - 定义六层检查框架：Context / Tools / Flow / State / Evaluation / Constraints
   - 定义制品完整性检查专节
   - 定义阶段速查表：各阶段必须重点检查的子集

3. **编写审查检查清单文件**
   - 新建 `.workflow/context/checklists/review-checklist.md`
   - 按上述结构填充内容
   - 自检格式（Markdown 层级、勾选框、链接可点击性）

4. **内部验证**
   - 对照 change.md 验收条件逐条核对
   - 确认文件路径正确、无拼写错误

## 产物清单
- `.workflow/context/checklists/review-checklist.md`

## 依赖关系
- 无前置依赖
- 被 chg-03 依赖（chg-03 需在角色文件中引用本清单路径）

## 执行顺序
第 1 顺位（可与 chg-02 并行执行）
