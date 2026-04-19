# Change: chg-03

## Title

harness archive 自动清理残留目录

## Goal

在 `harness archive` 成功归档需求后，自动删除 `flow/requirements/` 中对应的残留目录，避免活跃需求与归档副本并存。

## Scope

**包含**：
- 修改 `core.py` 中的归档逻辑
- 在需求移动到 archive 后，检查并删除 `flow/requirements/{req-id}/`
- 记录清理动作

**不包含**：
- 修改归档目录结构
- 自动清理其他位置的残留

## Acceptance Criteria

- [ ] `harness archive` 执行后，`flow/requirements/` 中对应目录已被删除
- [ ] 如果目录不存在，不报错正常继续
- [ ] 清理动作被记录到输出日志
