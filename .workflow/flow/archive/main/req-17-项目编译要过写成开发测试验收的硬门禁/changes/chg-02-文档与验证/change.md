# Change: chg-02

## Title
文档与验证

## Goal
更新 README 文档，验证编译检查功能，并重新安装包。

## Scope

**包含**：
- 更新 README 说明 `harness validate` 包含编译检查
- 同步 `scaffold_v2/README.md`
- 本地验证编译检查（制造临时语法错误并恢复）
- `pipx inject` 重新安装

**不包含**：
- 修改核心逻辑

## Acceptance Criteria

- [ ] README 已更新 validate 的编译检查说明
- [ ] 本地验证通过
- [ ] 包已重新安装
