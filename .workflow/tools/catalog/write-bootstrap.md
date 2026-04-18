# 工具：write-bootstrap

**类型：** 工具层工具（tools-layer tool）
**状态：** active

## 适用场景

- **install_agent 之后**：将 bootstrap 指令写入目标 agent 的入口文件（`CLAUDE.md` / `AGENTS.md`），确保 agent 启动时立即加载 `harness-manager`
- **install_agent 流程的一部分**：`install_agent` 调用后，由 harness-manager 调用此工具完成入口文件的引导指令注入

## 核心行为

此工具是 `install_agent` 流程的最后一步。在 skill 文件已复制到目标目录后，将以下引导指令写入目标 agent 的入口文件：

**CLAUDE.md（Claude Code）**:
```
4. **立即加载 `harness-manager` 角色**：使用 Skill 工具调用 `harness-install`，由 harness-manager 接管后续路由
```

**AGENTS.md（Codex / Qoder / Kimi）**:
```
4. **立即加载 `harness-manager` 角色**：使用 Skill 工具调用 `harness-install`，由 harness-manager 接管后续路由
```

## 推荐 prompt 模式

| 任务类型 | 调用方式 |
|---------|---------|
| 安装完成后写入 bootstrap | `write-bootstrap --agent claude` |
| 批量写入所有 agent | `write-bootstrap --all` |

## 入口文件映射

| Agent | 入口文件 |
|-------|---------|
| Claude Code | `CLAUDE.md` |
| Codex | `AGENTS.md` |
| Qoder | `AGENTS.md` |
| Kimi | `AGENTS.md` |

## 注意事项

- 此工具在 `install_agent` 流程中自动调用，也可手动单独使用
- bootstrap 指令必须写在步骤 3（读取 runtime.yaml）之后、步骤 4（原路由加载）之前
- 如果入口文件已存在 bootstrap 指令，跳过写入
- 写入前先读取文件确认内容

## 迭代记录

- 2026/04/18：首次创建，作为 chg-02（实现加载引导机制）的一部分
