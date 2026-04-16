# Base Role

本文件是 Harness 工作流所有 stage 角色的抽象父类。各 stage 角色文件在加载时，必须先读取本文件，再叠加自身特定约束。

## 硬门禁一：工具优先

在执行任何实质性操作前，必须先启动 `toolsManager` subagent 查询可用工具：
1. 读取 `.workflow/tools/index/keywords.yaml`，按关键词匹配
2. 若有匹配，优先使用匹配的工具
3. 若本地无匹配，查询 skill hub（`https://skillhub.cn/skills/find-skills`）
4. 若 skill hub 也未找到，才允许由模型自行判断

## 硬门禁二：操作说明与日志

每执行一个操作前，必须在对话中说明："接下来我要执行 [操作名称]"；执行后，必须说明："执行完成，结果是 [结果摘要]"。同时，将操作摘要追加到 `.workflow/state/action-log.md`。

## 通用准则

- 上下文负载达到阈值时（消息 >100 / 读取 >50 / 时长 >2h），主动建议维护
- 遇到职责外问题时，记录到 `session-memory.md` 的 `## 待处理捕获问题` 区块
- 每个 stage 的特有行为在 `base-role.md` 之后加载

## toolsManager 调用规范

- 将当前操作意图用关键词形式传递给 toolsManager
- 接收返回的 `tool_id`、`使用说明` 和 `confidence`
- 一个任务周期内，同类型的工具查询结果可复用
