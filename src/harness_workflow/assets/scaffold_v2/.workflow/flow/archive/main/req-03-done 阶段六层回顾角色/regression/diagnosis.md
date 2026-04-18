# Regression Diagnosis

## 触发现象
用户收到 API 错误：`This model's maximum context length is 102400 tokens. However, you requested 102838 tokens`。上下文爆炸，超出模型限制。

用户提问：上下文处理机制是什么？`/compact` `/clear` 新启 agent 该什么时候执行？

## 问题确认
**真实问题**：工作流系统缺乏明确的上下文维护机制，导致会话历史积累超出模型限制，且用户不知何时应使用 Claude Code 内置命令（`/compact`、`/clear`）或何时应新开 agent。

## 根因分析
1. **原则与实现脱节**：`project-overview.md` 实践原则第 1 条写明 "上下文爆满时不压缩：新开 agent，通过 handoff.md 交接"，但：
   - `handoff.md` 文件不存在，交接机制未实现
   - 未定义 "爆满" 的量化标准（如 token 数、消息条数）
   - 未规定新开 agent 的触发时机和责任人

2. **工具层缺失上下文维护策略**：
   - Claude Code 提供 `/compact`（压缩历史）和 `/clear`（清除历史）命令，但工作流未定义何时使用
   - 无自动监控上下文长度的机制
   - 无经验文件记录上下文爆炸的应对方法

3. **状态层未跟踪上下文负载**：
   - `state/` 层未记录会话长度、token 估算等指标
   - 无法在上下文接近极限时预警或自动触发维护动作

4. **职责不明确**：
   - 主 agent 是否应主动监控上下文负载？
   - 用户是否应手动执行维护命令？
   - subagent 是否应在任务完成后清理自身上下文？

## 路由决定
**需求/设计问题** → `requirement_review`

理由：
- 上下文维护是跨层（tools、state、constraints）的基础设施能力，属于系统设计范畴
- 需要定义明确的策略、触发条件、交接协议，而非单个变更能解决
- 涉及对 Claude Code 工具的理解和集成，需在需求层明确范围

## 建议处置
1. 创建新需求（如 `req-04-context-maintenance`），定义上下文维护机制：
   - 监控指标（token 估算、消息条数、文件读取量）
   - 触发阈值（如 80% 最大上下文时预警，90% 时强制维护）
   - 维护动作清单（`/compact`、`/clear`、新开 agent + handoff 交接）
   - handoff.md 交接协议格式
   - 各角色职责（主 agent 监控、subagent 清理、用户手动干预）

2. 在 tools 层增加 Claude Code 上下文管理工具 catalog 条目
3. 在 constraints 层增加上下文爆炸的风险条目和恢复路径
4. 在 context/experience/ 下沉淀本次教训

## 关联文件
- `.workflow/context/project/project-overview.md`（实践原则第 1 条）
- `.workflow/tools/index.md`（工具系统）
- `.workflow/state/`（状态层）
- `.workflow/constraints/risk.md`（风险扫描）