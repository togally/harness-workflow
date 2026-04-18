# Testing Report: req-10-suggest功能

## Test Date
2026-04-15

## Test Results

### AC-1: `harness suggest "xxx"` 能成功创建建议文件
- [x] 执行 `harness suggest "测试建议"` 成功创建 `.workflow/flow/suggestions/sug-01-a.md` ✅
- [x] 文件格式正确，包含 frontmatter 和 body ✅

### AC-2: `harness suggest --list` 能列出所有未应用建议
- [x] 列出结果包含 ID、status、创建时间、内容摘要 ✅

### AC-3: `harness suggest --apply <id>` 能转化为正式需求
- [x] `--apply sug-02` 成功创建 `req-01` 并进入 `requirement_review` ✅
- [x] suggest 文件状态被更新为 `applied` ✅
- [x] `runtime.yaml` 中 `current_requirement` 已指向新需求 ✅

### AC-4: `harness suggest --delete <id>` 能删除建议
- [x] `--delete sug-01` 成功删除文件 ✅
- [x] 再次 `--list` 显示 "No suggestions found" ✅

### AC-5: suggest 文件格式 human-readable
- [x] 文件为纯 Markdown，frontmatter + body，无需数据库 ✅

### AC-6: CLI 包能正确安装并执行
- [x] `pipx inject` 后所有 suggest 命令可正常执行 ✅

## Conclusion

**所有 AC 满足，测试通过。**
