# Change: chg-04

## Title

验证与文档更新

## Goal

验证 req-08 的前三个变更在真实场景中可用，并更新相关文档。

## Scope

**包含**：
- 运行 lint 脚本验证 scaffold 同步检查生效
- 在临时项目中测试 `harness update` 的 state 迁移功能
- 在临时项目中测试 `harness archive` 的残留清理功能
- 更新 `stages.md` 或 CLI 文档中关于 `update` 和 `archive` 的说明
- 产出 done-report 并归档 req-08

**不包含**：
- 修改 workflow 核心阶段定义

## Acceptance Criteria

- [ ] lint 检查验证通过
- [ ] update 迁移验证通过
- [ ] archive 清理验证通过
- [ ] 文档已更新
- [ ] req-08 已归档
