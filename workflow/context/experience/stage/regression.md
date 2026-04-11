# 回归阶段经验

> 进入回归阶段（regression）时自动加载。同时加载 `risk/known-risks.md` 和 `debug/*.md`。
> 置信度：low — 新沉淀经验，验证后逐步提升。

## 核心约束

- 用户反馈问题时，先执行 `harness regression "<issue>"` 确认是否为真实问题
- 回归开始时先填写 `regression/required-inputs.md`
- 不要在未确认问题真实性前立即开始修复

## 最佳实践

- 检查 `risk/known-risks.md` 确认是否为已知风险
- 从症状出发系统性分析根因，而非猜测
- 修复后需重新执行完整验收

## 常见错误

- 未确认问题真实性直接修复
- 修复症状而非根因
- 回归修复后未更新已知风险文档
