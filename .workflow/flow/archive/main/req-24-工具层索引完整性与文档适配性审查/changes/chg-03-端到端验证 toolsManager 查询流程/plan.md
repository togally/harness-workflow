# Change Plan

## 1. Development Steps

1. 确认 chg-01 和 chg-02 的产出已保存并生效
2. 模拟以下操作意图，按 toolsManager SOP 执行匹配：
   - "读取配置文件" → 期望 read
   - "修改代码逻辑" → 期望 edit
   - "运行单元测试" → 期望 bash
   - "搜索函数定义" → 期望 grep
   - "派发测试 subagent" → 期望 agent
   - "上下文太长了需要压缩" → 期望 claude-code-context
3. 记录每次查询的匹配结果、评分和最终推荐
4. 如发现未命中或推荐不当，分析原因并回滚到对应 change 修复

## 2. Verification Steps

1. 检查 6 个模拟查询是否全部返回预期结果
2. 检查评分排序是否合理（无评分冲突导致随机选择）
3. 将验证结果写入 `session-memory.md`
4. 如全部通过，标记本 change 完成
