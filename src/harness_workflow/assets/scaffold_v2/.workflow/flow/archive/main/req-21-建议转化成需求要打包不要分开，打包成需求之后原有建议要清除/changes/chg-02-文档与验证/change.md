# Change: chg-02

## Title
文档与验证

## Goal
更新 CLI 帮助和 README 文档，验证打包转换和文件清理功能，并重新安装包。

## Scope

**包含**：
- 更新 `README.md` 中 `--apply-all` 的说明（新增打包行为和 `--title`）
- 同步 `scaffold_v2/README.md`
- 在临时项目验证打包转换和 suggest 文件删除
- `pipx inject` 重新安装

**不包含**：
- 修改核心逻辑

## Acceptance Criteria

- [ ] README 已更新 `--apply-all` 和 `--title` 的说明
- [ ] 临时项目验证：多条 suggest 打包成一个 req，且原文件被删除
- [ ] 包已重新安装
