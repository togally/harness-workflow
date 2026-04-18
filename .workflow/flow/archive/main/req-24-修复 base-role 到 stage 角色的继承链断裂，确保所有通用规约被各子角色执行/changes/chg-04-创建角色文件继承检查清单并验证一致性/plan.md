# Plan: 创建角色文件继承检查清单并验证一致性

## 步骤

1. 基于 `base-role.md` 和更新后的 `stage-role.md`，提取必须被继承的通用规约要点
2. 创建 `.workflow/context/checklists/role-inheritance-checklist.md`
3. 对每个检查项定义：检查内容、检查方法、通过标准
4. 使用检查清单逐一验证 req-24 中修改的 8 个角色文件
5. 记录验证结果，如有未通过项回修对应角色文件
6. 将检查清单引用添加到 `review-checklist.md` 或相关入口文档中（如适用）
