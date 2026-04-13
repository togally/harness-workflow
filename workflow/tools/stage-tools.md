# Stage 工具白名单

## requirement_review / planning
**可用：** Read、Write、Edit、Agent（讨论/分析类 subagent）
**禁用：** Bash（不得执行命令）、Write/Edit（项目代码文件）

## executing
**可用：** Read、Write、Edit、Bash、Grep、Glob、Agent（执行类 subagent）
**推荐：** 按 plan.md 步骤顺序调用，每步完成后更新 session-memory

## testing
**可用：** Bash（运行测试）、Read、Grep、Agent（测试类 subagent）
**禁用：** Write、Edit（不得修改被测内容）

## acceptance
**可用：** Read、Agent（验收类 subagent）
**禁用：** Write、Edit、Bash（只读核查）

## regression
**可用：** Read、Grep、Glob、Bash（只读命令，查日志）、Agent（诊断类 subagent）
**禁用：** Write、Edit（确认问题前不得修复）
