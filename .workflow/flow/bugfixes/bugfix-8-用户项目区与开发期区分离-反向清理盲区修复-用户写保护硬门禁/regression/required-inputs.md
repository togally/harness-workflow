# Regression Required Inputs — bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）

## 1. Current Problem

- Issue summary: 5 现象（usage-reporter.md 残留 / self-audit 误报 7 条业务文件 / --force-managed 仍 skip / 用户写保护无门禁 / build/ 残留污染 mirror），详见 `regression/diagnosis.md`
- Related regression: 本 bugfix（bugfix-8 自身的 regression stage）
- Linked change: chg-01（真清理 usage-reporter.md）/ chg-02（白名单补 3 条）/ chg-03（--force-managed 透传防御）/ chg-04（user-write-protected-zones 硬门禁）/ chg-05（build/ 残留 lint）

## 2. Required Human Inputs

| Item | Required | Notes |
| --- | --- | --- |
| Configuration | no | 所有诊断证据从本仓 src/ + build/ + venv site-packages + PetMall log 收集，无需用户补充配置 |
| Test data | no | dogfood TC 在 tmpdir 自构造测试数据（chg-01 ~ chg-05 各 TC 已设计） |
| Account details | no | 本 bugfix 不涉及外部账户 / 凭据 |
| External dependency details | no | 本 bugfix 不涉及外部服务依赖 |

## 3. Human Response Section

- Configuration: 不需要
- Test data: 不需要
- Account details: 不需要
- External dependency details: 不需要

## 4. Next Step

**用户已拍板 5 chg 拆分（详见 diagnosis.md §1 + §7），无新决策点。**

regression stage 完成后路由 → executing：
1. 主 agent 调用 `harness regression --confirm` 确认问题真实
2. 自动转入 executing stage 按 5 chg 顺序落地（chg-01 / chg-05 涉及手工清理 + lint，建议先做以释放 mirror 污染状态；chg-02 / chg-03 / chg-04 为代码层修复，可并行）
