# Requirement

## 1. Title

suggest 功能

## 2. Goal

当前 Harness workflow 中，任何想法都必须立即通过 `harness requirement "<title>"` 进入完整的 requirement_review → planning → executing → ... 流程。这导致：
- 一些零散的想法、优化点、待办事项没有地方临时存放
- 用户在和 AI 对话时产生的灵感，如果不立即转成需求，很容易丢失
- 有些想法还需要进一步酝酿，不适合立刻启动完整工作流

本需求的目标是：**开发一个轻量级的 `sarness suggest` 功能**，允许用户随手记录想法，形成一个建议池；当某个建议成熟时，可以一键将其转化为正式需求并进入标准 Harness workflow。

## 3. Scope

**包含**：
- 设计 `suggest` 的数据模型和存储位置
- 实现 `harness suggest "<content>"` 命令：随手记录一条建议
- 实现 `harness suggest --list` 命令：查看所有未应用的建议
- 实现 `harness suggest --apply <id>` 命令：将某条建议转化为正式需求，并自动进入 `requirement_review`
- 实现 `harness suggest --delete <id>` 命令：删除某条建议
- 定义 suggest 文件的格式和存放目录
- 更新 CLI 命令注册和 skill 命令文档

**不包含**：
- 修改现有 stage 流转规则
- 修改 requirement 的验收标准结构
- 开发 Web UI 或数据库后端
- 建议的优先级排序/标签系统（V1 只保留最基础的增删查用）

## 4. Acceptance Criteria

- [ ] `harness suggest "xxx"` 能成功创建一条建议文件
- [ ] `harness suggest --list` 能列出所有未应用建议的 ID、创建时间和内容摘要
- [ ] `harness suggest --apply <id>` 能将指定建议转化为正式需求，并自动进入 `requirement_review`
- [ ] `harness suggest --delete <id>` 能删除指定建议
- [ ] suggest 的文件格式 human-readable，不依赖复杂数据库
- [ ] 更新后的 CLI 包能正确安装并执行上述命令

## 5. Split Rules

### chg-01 suggest 数据模型与存储设计

定义 suggest 的文件格式和目录结构：
- 存储路径：`.workflow/flow/suggestions/` 或 `.workflow/state/suggestions/`
- 文件命名：`sug-{两位数字}-{slug}.md`
- 内容格式：包含 `id`、`created_at`、`content`、`status`（pending / applied）
- 讨论并确定路径（flow 层还是 state 层更合适）

### chg-02 CLI 命令实现

在 `core.py` 和 `cli.py` 中实现 suggest 相关命令：
- `harness suggest "<content>" [--title <title>]`
- `harness suggest --list`
- `harness suggest --apply <id>`
- `harness suggest --delete <id>`

`--apply` 的逻辑：
1. 读取 suggest 文件
2. 调用现有的 `create_requirement` 逻辑，以 suggest 的内容为基础创建 requirement
3. 将 suggest 的 `status` 标记为 `applied`
4. 可选：在 requirement.md 中引用原始 suggest 的 ID

### chg-03 skill 命令文档更新

更新 `.claude/commands/`、`.codex/skills/`、`.qoder/commands/` 下的命令定义文件：
- 新增 `harness-suggest.md`
- 更新命令索引（如有）

### chg-04 验证与文档

- 在临时项目中测试 suggest 的增删查用全流程
- 更新 `stages.md` 或 README 中关于 suggest 的说明
- 产出 done-report 并归档 req-10
