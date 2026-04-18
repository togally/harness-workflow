# Change

## 1. Title

handoff 交接协议

## 2. Goal

创建 `handoff.md` 协议模板，定义新开 agent 时的上下文交接标准：
- 上下文摘要：当前任务状态、关键决策、待处理问题
- 交接内容：必须传递的文件、状态、会话记忆片段
- 接收方指引：下一步动作、注意事项、风险提示
- 格式规范：Markdown 结构、必填字段、示例

## 3. Requirement

- `req-04-上下文维护机制设计`

## 4. Scope

**包含**：
- `handoff.md` 协议模板设计：
  - 文件结构：标题、摘要、交接内容、接收方指引、元数据
  - 必填字段：任务状态、关键决策、待处理问题、下一步动作
  - 可选字段：风险提示、依赖文件、时间戳
- 交接内容规范：
  - 必须传递的文件列表（如 `session-memory.md`、相关配置）
  - 状态信息：当前 stage、requirement、进度
  - 会话记忆摘要：关键对话片段、重要决策
- 接收方指引：
  - 如何加载交接内容
  - 注意事项（如未完成的任务、已知风险）
  - 继续工作的步骤
- 示例文件：提供完整的 `handoff.md` 示例

**不包含**：
- 维护动作决策逻辑（属于 chg-02）
- 工具层集成实现（属于 chg-04）
- 风险与恢复路径的具体内容（属于 chg-05）
- 角色职责的具体更新（属于 chg-06）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`