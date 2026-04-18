# Session Memory: chg-02

## Change
修复 harness install/update 模板同步机制

## Status
✅ 已完成

## Steps
- [x] 定位 `harness_workflow` 包位置（pipx venv）
- [x] 读取 `core.py` 中 install/update 逻辑
- [x] 确认根因：`assets/scaffold_v2/` 中的模板是旧版本
- [x] 将 harness-workflow 最新 `.workflow/`、`WORKFLOW.md`、`CLAUDE.md` 同步到 `src/harness_workflow/assets/scaffold_v2/`
- [x] 使用 `pipx inject harness-workflow . --force` 重新安装包
- [x] 在临时目录验证 `harness install` 可正确部署最新模板

## Internal Test
- [x] scaffold_v2 已包含 `harness-ff.md` ✅
- [x] scaffold_v2 的 `stages.md` 已包含 ff 模式章节 ✅
- [x] 临时目录 `harness install` 验证通过 ✅
- [x] 新安装项目包含 `claude-code-context.md` 和 `harness-ff.md` ✅

## Notes
修复方案非常简单：将仓库根目录的最新 workflow 文件完整复制到 `src/harness_workflow/assets/scaffold_v2/`。但根本的**流程问题**是：开发者在修改 `.workflow/` 时容易忘记同步 scaffold 模板。chg-05 中需要在经验文件中强调这一点，并建议在 CI 或 lint 中增加 scaffold 同步检查。
