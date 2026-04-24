# 工具：api-document-upload

**类型：** MCP 工具 + 抽象适配器
**状态：** active
**父需求：** req-34（新增工具 api-document-upload（首实现 apifox MCP，可拔插）+ 修复 scaffold_v2 mirror 漂移（project-reporter 系列漏同步））

## 用途

Provider-agnostic 的"上传 API 文档"工具：

1. 扫描当前项目的 API 定义源（路由文件 / controller / OpenAPI schema / 注释块）
2. 生成标准化的 OpenAPI 3.x 文档（内部中间表示）
3. 将文档同步到用户选定的 **provider**（首版：apifox；可拔插：postman / swagger / confluence 等）

tools-manager 按关键词匹配到本工具后，executing subagent 按下方 `## Provider: {name}` section 对应的 SOP 执行。

## 关键词索引

- 上传 API 文档
- API 同步 apifox
- 生成 openapi
- API 文档同步
- 接口文档上传
- apifox 同步
- openapi 导出

## 适用场景

- executing / acceptance / done 阶段产出包含后端路由、controller、API schema 时，需要把 API 契约同步到团队协作平台
- 前后端联调前，需要把最新 API 定义推送到 apifox / postman 供前端 mock
- PR 合并后，需要刷新 API 文档仓库

## 不适用场景

- 项目内无 API（纯 CLI / 纯库 / 纯脚本）
- 用户明确禁用 MCP 注册（走手写文档流程）
- 当前 provider MCP 未注册且用户拒绝退化规划（见下方退化策略）

## Provider: apifox

**MCP 依赖**：`mcp__apifox_*` 系列工具（由 `.mcp.json` 注册；若未注册则退化，见本节末）。

### 前置检查

引用：protocols/mcp-precheck.md（prefix=apifox, list_tool=mcp__apifox_list_projects, profile_key=mcp_project_ids.apifox）

### SOP（全部命中前置检查时）

1. **扫描项目 API 定义**
   - 调用 apifox MCP 的项目扫描工具（通常为 `mcp__apifox_scan_project` 或等价入口）
   - 或退化为本地扫描：grep 框架路由文件（例如 `@app.route` / `@router.get` / `*.openapi.yaml` / `openapi.json`）
2. **生成 OpenAPI 3.x 中间表示**
   - 若 apifox MCP 直接接受源码，跳过此步
   - 否则用 apifox MCP 的 `convert-to-openapi` 或本地工具（如 `@apidevtools/swagger-parser`）生成 `openapi.json`
3. **上传到 apifox 项目空间**
   - 调用 apifox MCP 的上传工具（通常为 `mcp__apifox_upload_openapi` 或 `mcp__apifox_sync_spec`）
   - 参数：`project_id`（来自 `.workflow/context/project-profile.md` 或用户显式传入）、`openapi_file`、`merge_strategy`（默认 `overwrite`）
4. **留痕**
   - 把上传结果（成功条目数 / 失败条目 / apifox 返回的 URL）写到 `session-memory.md` 当前 stage 块

### 退化策略（MCP 未注册）

当 `mcp__apifox*` 工具在当前 agent 环境中不可见（典型：用户未跑 `claude mcp add apifox ...`）时：

1. 打印引导：`apifox MCP 未注册，请在 .mcp.json 中添加 apifox server 条目并重启会话；或选择其他 provider（见本文件 "## 如何添加新 provider"）。`
2. 生成"留痕规划"：在 session-memory 记录"本次跳过实际上传，规划 OpenAPI 扫描 + 上传步骤待 MCP 就绪后补跑"
3. 返回状态 `degraded`（而非失败），不阻塞当前 stage 推进

## 如何添加新 provider

本工具用"单文件多 `## Provider:` section"模式实现拔插，新增 provider（例如 postman / swagger / confluence）只需三步：

### Step 1：在本文件新增 `## Provider: {name}` section

复制 `## Provider: apifox` 段为骨架，把 `apifox` 替换为新 provider 名，填写：

- MCP 依赖（新 provider 对应的 MCP server 工具前缀，例如 `mcp__postman_*`）
- 前置检查（用户环境中如何探测 provider MCP 已注册）
- SOP（扫描 → 生成 OpenAPI → 调 provider MCP 上传工具的步骤）
- 退化策略

### Step 2：在 `.workflow/tools/index/keywords.yaml` 追加触发词

在 `api-document-upload` 条目的 `keywords` 数组里追加新 provider 相关触发词，例如：

```yaml
- tool_id: "api-document-upload"
  keywords: ["上传 API 文档", "API 同步 apifox", "生成 openapi", "API 文档同步", "接口文档上传", "apifox 同步", "openapi 导出", "postman 同步", "swagger 上传"]
  catalog: "catalog/api-document-upload.md"
  description: "扫描项目 API 定义生成 OpenAPI 并上传到选定 provider（apifox/postman/swagger/...）"
```

### Step 3：在本文件 `## 迭代记录` 追加新 provider 上线日期与来源 chg

格式：`YYYY-MM-DD：新增 Provider: {name}（chg-*）`

### 示例占位（postman）

```markdown
## Provider: postman

**MCP 依赖**：`mcp__postman_*` 系列工具

### 前置检查
1. 环境中存在 `mcp__postman*` 工具
2. `.mcp.json` 含 postman server 条目

### SOP
1. 调 `mcp__postman_scan_workspace` 或本地 openapi 生成
2. 调 `mcp__postman_import_openapi` 上传到目标 collection
3. 留痕 session-memory

### 退化策略
postman MCP 未注册 → 打印引导 + 返回 `degraded`
```

### 示例占位（swagger / swagger-ui）

```markdown
## Provider: swagger

**MCP 依赖**：通常无 MCP，走本地文件产出 + 静态 hosting

### SOP
1. 扫描项目生成 `openapi.json`
2. 写入 `docs/openapi.json`
3. （可选）调本地 swagger-ui-dist 构建静态站

（本例说明 provider 不一定依赖 MCP，可退化为本地产物）
```

## 注意事项

- 本工具**只在 executing / done 阶段**由其他 agent 通过 tools-manager 召唤，不独立成 stage
- 任何 provider 的上传动作涉及外部写，必须**用户显式授权或 ff 等价授权**后才执行
- 多 provider 并存时，tools-manager 仍返回单一 tool_id `api-document-upload`，由 executing subagent 按用户意图（或项目 profile）选 section

## 迭代记录

<!-- 发现更好用法时追加，格式：YYYY-MM-DD：{内容} -->
- 2026-04-22：首版落地（req-34（新增工具 api-document-upload（首实现 apifox MCP，可拔插）+ 修复 scaffold_v2 mirror 漂移（project-reporter 系列漏同步）） / chg-01（新建 `.workflow/tools/catalog/api-document-upload.md` 工具文件（apifox 首版 + 拔插接口）））, Provider: apifox 首实现
