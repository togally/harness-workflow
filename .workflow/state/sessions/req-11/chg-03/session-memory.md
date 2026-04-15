# Session Memory: chg-03

## Change
验证与文档

## Status
✅ 已完成

## Steps
- [x] 临时项目端到端测试：构造 done-report → `harness next` → 自动提取 4 条 suggest
- [x] `harness suggest --list` 验证 suggest 文件正确生成
- [x] 同步 `done.md` 和 `WORKFLOW.md` 到 `scaffold_v2`
- [x] 重新安装包 `pipx inject harness-workflow . --force`

## Notes
`stages.md` 和 `README.md` 无需额外更新，因为 done 阶段的流转规则未变，新增的是内部自动化行为。
