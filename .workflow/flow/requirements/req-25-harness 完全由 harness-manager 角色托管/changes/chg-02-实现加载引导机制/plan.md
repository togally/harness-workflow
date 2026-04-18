# Change Plan

## 1. Development Steps

1. 分析现有安装流程（install_agent 函数）
2. 设计加载引导机制：
   - 安装时写入引导指令到 agent 入口文件（CLAUDE.md/AGENTS.md）
   - 或在 SKILL.md 中定义加载规则
3. 实现引导指令的写入逻辑
4. 验证引导机制在各个 agent（Claude Code、Codex、Qoder、Kimi）上正常工作

## 2. Verification Steps

- [ ] Claude Code 安装后读取 CLAUDE.md 能加载 harness-manager
- [ ] Codex 安装后读取 AGENTS.md 能加载 harness-manager
- [ ] Qoder 安装后读取 AGENTS.md 能加载 harness-manager
- [ ] Kimi 安装后读取 AGENTS.md 能加载 harness-manager
