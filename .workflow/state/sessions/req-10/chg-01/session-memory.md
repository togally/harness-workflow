# Session Memory: chg-01

## Change
suggest 数据模型与存储设计

## Status
✅ 已完成

## Steps
- [x] 确定存储路径：`.workflow/flow/suggestions/`
- [x] 确定文件命名：`sug-{两位数字}-{slug}.md`
- [x] 确定内容格式：frontmatter（id, created_at, status）+ Markdown body
- [x] ID 生成规则：扫描现有文件取最大序号 +1

## Notes
设计已体现在代码实现中，文件格式 human-readable。
