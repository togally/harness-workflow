# Base Role

本文件是 Harness 工作流所有 stage 角色的抽象父类。各 stage 角色文件在加载时，必须先读取本文件，再叠加自身特定约束。

## 硬门禁一：工具优先

在执行任何实质性操作前，必须先启动 `toolsManager` subagent 查询可用工具。具体行为约束见 `.workflow/context/roles/tools-manager.md`。

流程概要：
1. 读取 `.workflow/context/roles/tools-manager.md` 获取完整 briefing
2. 将当前操作意图用关键词形式传递给 toolsManager
3. 若有匹配，优先使用匹配的工具
4. 若本地无匹配，由 toolsManager 查询 skill hub
5. 仍未找到时，才允许由模型自行判断

## 硬门禁二：操作说明与日志

每执行一个操作前，必须在对话中说明："接下来我要执行 [操作名称]"；执行后，必须说明："执行完成，结果是 [结果摘要]"。同时，将操作摘要追加到 `.workflow/state/action-log.md`。

## 通用准则

- 上下文负载达到阈值时（消息 >100 / 读取 >50 / 时长 >2h），主动建议维护
- 遇到职责外问题时，记录到 `session-memory.md` 的 `## 待处理捕获问题` 区块
- 每个 stage 的特有行为在 `base-role.md` 之后加载

## 角色标准工作流程约定

所有 stage 角色（含 toolsManager）均应包含**标准工作流程（SOP）**章节。SOP 定义了 subagent 拿到任务后的执行顺序和检查点，是角色的核心执行指南。
