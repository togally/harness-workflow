# Regression Required Inputs — bugfix-13（install时自动创建artifacts-project骨架与索引模板）

## 1. Current Problem

- Issue summary：req-52（硬编码 main 路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-04 落地半截工程：项目级覆盖**读路径** + stderr 日志已接通 install_repo，但**写盘骨架自举**漏了一步——用户仓 `harness install` 时不会自动创建 `artifacts/project/{constraints,experience,tools}/` 骨架 + 6 份 index.md 模板 + README。
- Related regression：bugfix-13 自身（无 reg-XX 嵌套）
- Linked change：本 bugfix executing 阶段 chg-01 待开（fix plan 已在 diagnosis.md §4 定稿）

## 2. Required Human Inputs

**结论：无阻塞**。诊断 4 个 OQ（OQ-A 模板落位 / OQ-B 写盘点 / OQ-C 幂等策略 / OQ-D README 内容）全部有 default-pick + 一句话理由（详见 diagnosis.md §4 / §8），按 base-role.md 硬门禁四"同阶段不打断原则"自决推进，**不需要**人工补充信息即可进 executing。

| Item | Required | Notes |
| --- | --- | --- |
| Configuration | no | 不引入新配置 / env / secret |
| Test data | no | 测试用例数据 = tmpdir 自构（详见 diagnosis.md §6 测试用例设计） |
| Account details | no | 不涉及外部账号 / 权限 |
| External dependency details | no | 不引入外部依赖 |

## 3. Human Response Section

- Configuration：N/A
- Test data：N/A
- Account details：N/A
- External dependency details：N/A

## 4. Next Step

- 主 agent 直接 `harness regression --confirm` 进入 executing 阶段；
- executing subagent 按 diagnosis.md §4.5 实施步骤草图执行（4 步）；
- testing 按 diagnosis.md §6 12 条 TC 跑回归 + 完成判据 lint 命令字面（§7）。
