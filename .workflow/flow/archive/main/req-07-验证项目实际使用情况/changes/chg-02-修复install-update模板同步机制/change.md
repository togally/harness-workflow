# Change: chg-02

## Title

修复 harness install/update 模板同步机制

## Goal

定位并修复 `harness install` 和 `harness update` 命令未能同步最新 workflow 模板的问题。

## Scope

**包含**：
- 检查 `harness_workflow` Python 包中的 scaffold 模板是否包含最新文件
- 检查 `harness install` 的复制逻辑是否遗漏了某些目录或文件
- 检查 `harness update` 的更新逻辑是否只更新部分文件
- 修复问题并验证

**不包含**：
- 修改 Yh-platform 的业务代码
- 重新设计整个 CLI 架构

## Acceptance Criteria

- [ ] 已定位 `harness install/update` 未同步最新模板的具体代码位置
- [ ] 已修复模板同步问题
- [ ] 已验证修复后的 install/update 能够正确部署最新模板
