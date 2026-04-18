# Requirement

## 1. Title

harness 完全由 harness-manager 角色托管

## 2. Background

当前 harness 的功能实现在 `core.py` 等 Python 脚本中，role 文件是描述性的（定义职责和工作流程），但实际执行仍依赖 Python 代码驱动。这与六层架构"以 role 为核心"的设计理念不符。

改造后，role 文件成为唯一执行依据，agent 被 role 引导自主执行，而非读取 Python 脚本。

## 3. Goal

1. 所有 `harness` 命令触发后，主 agent 立即加载 `harness-manager` 角色
2. `harness-manager` 理解整个项目结构和工作流
3. `harness-manager` 按需调度 subagent，subagent 可嵌套启动其他 subagent
4. 检测循环嵌套并终止
5. Role 文件成为执行手册；辅助功能按最小化原则实现为工具，注册在工具层由 `toolsManager` 管理

## 4. Scope

**包含**：
- 设计并实现 `harness-manager` 角色的完整执行逻辑
- 实现加载引导机制（使用 harness 命令时自动加载）
- 实现 subagent 嵌套调用机制
- 实现循环检测与终止机制
- 工具层工具注册与管理
- 删除 `core.py` 等非工具层脚本（项目中只允许工具层存在脚本）

**不包含**：
- 其他已完成的 role 文件的内部逻辑改造（除非被 harness-manager 调用）
`
`## 5. Acceptance Criteria

- [ ] `harness install claude` 能正常完成安装
- [ ] 其他命令（requirement/change/bugfix/ff/next 等）均能正常执行
- [ ] Subagent 嵌套调用正常工作
- [ ] 循环调用能被检测和终止
- [ ] 安装后 agent 能正确加载 `harness-manager`
- [ ] 工具层工具能正常工作

## 5. Split Rules

- Split the requirement into independently deliverable changes
- Each change should cover one clear unit of delivery
- When the requirement is complete, fill `completion.md` and record successful project startup validation
