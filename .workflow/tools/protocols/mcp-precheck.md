# 协议：mcp-precheck

> 本文件为**跨工具共享协议**，非工具条目，不进入 tools-manager 关键词匹配，不在 `catalog/` 下登记。
> catalog 条目如需 MCP 前置检查，按 `引用：protocols/mcp-precheck.md（参数槽=...）` 形态单行引用。
> 溯源：req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）/ chg-01（protocols 目录 + catalog 单行引用 + 硬门禁五保护扩展）

## 参数槽声明

调用方（catalog 条目）在单行引用时，必须填写以下参数槽：

- prefix: <provider 前缀，如 apifox>
- list_tool: <MCP 工具名，如 mcp__apifox_list_projects>
- profile_key: <project-profile.md 中期望 id 的路径，如 mcp_project_ids.apifox>

## 阶段 1 探测

**目标**：判断当前 agent 环境是否暴露指定 provider 的 MCP 工具。

**动作**：

1. 在 agent 可见工具列表中 grep `mcp__{prefix}*`（前缀来自调用方参数槽 `prefix`）。
2. **命中** → 直接进入**阶段 4 归属校验**。
3. **未命中** → 进入**阶段 2 注册引导**。

**provider-agnostic**：本阶段不硬编码任何具体 provider 名称；`{prefix}` 由调用方在单行引用中传入。

## 阶段 2 注册引导

**目标**：引导用户在本地 `.mcp.json` 中注册 provider MCP server，然后重启会话。

**动作**：

1. 打印 `.mcp.json` 片段模板（保留 `{prefix}` 占位，调用方替换）：

   ```json
   {
     "mcpServers": {
       "{prefix}": {
         "command": "<填写 provider MCP 可执行路径>",
         "args": ["<参数>"]
       }
     }
   }
   ```

2. 打印注册命令模板（如适用）：

   ```
   claude mcp add {prefix} <server-url-or-command>
   ```

3. 把当前状态写入 `session-memory.md` 当前 stage 块，追加一行（ISO 8601 格式时间戳，精确到秒，含时区，例 `2026-04-23T15:00:35+00:00`）：

   ```
   mcp_registration_pending: {prefix} (2026-04-23T15:00:35+00:00)
   ```

4. 把状态写入 `.workflow/state/runtime.yaml` 的 `stage_pending_user_action` 字段（chg-03（runtime pending 字段 + next/status gate）已落地，此字段可直接写入）：

   ```yaml
   stage_pending_user_action:
     type: "mcp_register"
     details:
       provider: "{prefix}"
   ```

   写入后，`harness next` 将拒绝推进 stage（返回退出码 3），`harness status` 将显示 `Pending User Action: mcp_register(provider={prefix})`。

5. **Stage 原地暂停**：提示用户"完成注册并重启会话后，再次说触发词继续流程"；不推进 stage，不调用任何后续工具。

## 阶段 3 恢复

**目标**：用户重启会话、注册完成后，重新探测并清除暂停标记，衔接进入阶段 4。

**动作**：

1. 重新执行**阶段 1 探测**逻辑（grep `mcp__{prefix}*`）。
2. **命中**：
   - 清空 `runtime.yaml.stage_pending_user_action` 为 `null`，写入方式：

     ```yaml
     stage_pending_user_action: null
     ```

   - 在 `session-memory.md` 当前 stage 块追加一行（ISO 8601 格式时间戳，正则参考 `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\+\-]\d{2}:\d{2}`）：

     ```
     mcp_registration_resolved: {prefix} (2026-04-23T15:05:00+00:00)
     ```

   - 继续进入**阶段 4 归属校验**。
3. **仍未命中**：重复打印阶段 2 引导，不静默继续。

## 阶段 4 归属校验

**目标**：确认 MCP 侧项目 id 与仓库声明的期望 id 一致，防止文档错传到错误项目空间。

**前置条件**：阶段 4 仅在阶段 1 探测命中（或阶段 3 恢复完成）后进入；若前置未满足，回阶段 2。

**动作**：

1. 调 `{list_tool}`（来自调用方参数槽，如 `mcp__apifox_list_projects` / `mcp__apifox_current_project`）拿 MCP 侧当前项目 id（或 project list）；记为 `<actual_id>`。
2. 读 `project-profile.md`，按 `{profile_key}`（来自调用方参数槽，如 `mcp_project_ids.apifox`）路径取期望 id；记为 `<expected_id>`。
3. **匹配**（`<actual_id>` == `<expected_id>`）：继续执行 catalog SOP（上传步骤），本 pre-check 协议结束。
4. **不匹配**（`<actual_id>` ≠ `<expected_id>`）：
   - 打印两侧 id 差异对照：
     ```
     MCP 侧: <actual_id>
     profile 声明 ({profile_key}): <expected_id>
     ```
   - 引导用户**二选一**（**禁止静默继续**、**禁止默认选一**、**禁止跳过校验**）：
     - **选项 A**：切换 provider 工作空间到 `<expected_id>`（由用户在 MCP 客户端侧操作，agent 不代为切换）。
     - **选项 B**：更新 `project-profile.md` 把 `mcp_project_ids.{prefix}` 改为 `<actual_id>`（agent 可协助编辑该文件）。
   - 等待用户明确选择后，方可继续；否则原地暂停。
