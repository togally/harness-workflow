# chg-03: 优化关键节点与命令说明

## 目标

明确 `harness` 系列命令的触发条件和 agent 行为，补充 ff 模式、regression、done 等关键节点的引导说明，完成一轮 agent 全流程走查验证。

## 范围

### 包含

- 更新 `.workflow/flow/stages.md`：
  - 命令与 stage 对应关系更清晰
  - ff 模式启动条件、推进规则、暂停与退出机制更明确
  - regression 恢复路径更直观
- 检查并补充 `context/roles/done.md` 中的六层回顾检查清单（如有缺失）
- 检查 `constraints/boundaries.md` 中 ff 决策边界和职责外问题处理规则，确保与角色文件一致
- 检查 `constraints/recovery.md` 中的失败恢复路径，确保与 regression 角色一致
- 完成一轮 agent 全流程走查验证（从 requirement_review 到 done，检查各 stage 切换时引导逻辑是否连贯）

### 不包含

- 修改 `WORKFLOW.md` 和 `context/index.md`（由 chg-01 负责）
- 修改各 stage 角色的具体 SOP（由 chg-02 负责）
- 引入新的 harness 命令

## 验收标准

- [ ] `stages.md` 中的命令-行为对应关系一目了然
- [ ] ff 模式、regression、done 节点的说明完整且无歧义
- [ ] `constraints/boundaries.md` 和 `constraints/recovery.md` 与角色文件一致
- [ ] 完成一轮 agent 全流程走查验证，输出走查报告
- [ ] 走查中发现的问题已记录并修复（或在报告中标注为后续跟进）
