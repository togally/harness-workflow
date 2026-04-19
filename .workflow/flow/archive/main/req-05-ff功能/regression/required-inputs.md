# Required Inputs

## 问题来源

用户同时在操作另一个使用 Harness workflow 的外部项目。在外部项目中，agent 处理大疆 OSD 模型字段缺失问题时，调用了不存在的 `Skill(websearch)`，随后出现 API Error 400，且 `/harness-next` 也报错，导致会话卡住无法恢复。

## 需要补充的信息

为了判断这是 Harness workflow 的流程缺陷还是外部项目的使用问题，请提供以下信息：

1. **外部项目的 `.workflow/tools/` 目录结构和 `stage-tools.md` 内容**：确认是否有 Harness workflow 的文档或工具清单错误地引导了 `websearch` skill 的调用。

2. **触发 `Skill(websearch)` 时的具体上下文**：
   - 当前 stage 是什么？
   - 是哪个角色文件或 plan.md 步骤要求 "去官网上云API的文档搜索下"？
   - 这个搜索指令是用户直接输入的，还是 agent 根据角色文件/plan 主动决定的？

3. **API Error 400 的完整错误信息和触发时机**：
   - 是在 `Skill(websearch)` 失败后立即出现的，还是在后续某次对话中才出现的？
   - `/harness-next` 返回的 400 错误与前面的 skill 失败是否有直接关联，还是独立的平台错误？

4. **外部项目的关键文件**（如果可以提供）：
   - 触发搜索时正在执行的那个 `plan.md` 或 `change.md`
   - 相关角色文件（如 `executing.md`）中是否有 "使用 web search" 之类的描述

## 当前判断

初步判断：
- `Unknown skill: websearch` 表明该 skill 在当前 Claude Code 环境中不存在，这更可能是 **agent 或外部项目文档错误引用了未安装的 skill**，而非 Harness workflow 核心流程的 bug。
- 但如果 Harness workflow 的官方模板、角色文件或示例中确实推荐了 `websearch` 或其他非通用 skill，则属于 **流程文档缺陷**，需要修正。
- API Error 400 可能是 Claude Code 平台在 skill 调用失败后进入的异常状态，Harness workflow 目前缺乏 **底层调用失败后的会话恢复机制**，这可能是一个 **流程韧性缺陷**。

请补充上述信息，以便确定修复方向。
