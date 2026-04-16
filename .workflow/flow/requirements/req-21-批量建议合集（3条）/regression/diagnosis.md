# Regression Diagnosis

## 问题描述

toolsManager 应该是一个实际的角色负责管理工具，但当前实现中 toolsManager 仅在 `base-role.md` 中被描述为一种"调用规范"，没有独立的角色文件（如 `.workflow/context/roles/tools-manager.md`）。

## 现象验证

- 检查 `.workflow/context/roles/` 目录，不存在 `tools-manager.md`
- 检查 `base-role.md` 的 "toolsManager 调用规范" 章节，仅描述了调用方式，未提供 subagent 可执行的完整 briefing

## 根因分析

在设计阶段，toolsManager 被定义为"subagent 角色"，但在实现时仅完成了 CLI 层面的 `tool-search`/`tool-rate` 命令和调用规范描述，遗漏了实际的角色定义文件。这导致：

1. 主 agent 启动 toolsManager subagent 时，没有标准 briefing 文件可传递
2. subagent 的行为缺乏结构化约束（如匹配算法、skill hub 查询、返回值格式等未在角色层固化）
3. 与 Harness "每环节 agent 分开、角色分离"的核心理念存在偏差

## 路由决定

这是一个**实现/设计层面的遗漏**，属于当前 change（chg-01）的范围内缺陷。

建议路由方向：
- **回到 `executing` 阶段**，补充创建 `.workflow/context/roles/tools-manager.md`
- 同步更新 `base-role.md`，将"toolsManager 调用规范"中的行为细节迁移到角色文件中，base-role 只保留硬门禁引用

## 结论

真实问题，需要修复。
