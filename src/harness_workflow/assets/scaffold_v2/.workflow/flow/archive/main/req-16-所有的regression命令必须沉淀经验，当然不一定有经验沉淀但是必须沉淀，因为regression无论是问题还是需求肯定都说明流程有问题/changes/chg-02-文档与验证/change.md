# Change: chg-02

## Title
文档与验证

## Goal
更新 README 中 regression 命令的说明，本地验证回归流程，并重新安装包。

## Scope

**包含**：
- 更新 README 说明 regression 结束后会自动沉淀经验
- 同步 `scaffold_v2/README.md`
- 本地创建临时 regression 并验证经验文件生成
- `pipx inject` 重新安装

**不包含**：
- 修改核心逻辑

## Acceptance Criteria

- [ ] README 已更新 regression 经验沉淀说明
- [ ] 本地 regression 验证通过
- [ ] 包已重新安装
