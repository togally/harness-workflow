# Harness 工具使用经验

> 任务涉及 harness 命令操作时按需加载，跨阶段通用。
> 置信度：low — 新沉淀经验，验证后逐步提升。

## 核心命令

- `harness version "<name>"` — 创建新版本容器
- `harness active "<name>"` — 设置活跃版本
- `harness enter` — 进入 harness 会话模式
- `harness exit` — 退出 harness 会话模式
- `harness next` — 推进到下一阶段
- `harness ff` — 快进到完成状态
- `harness requirement "<title>"` — 创建需求
- `harness change "<title>"` — 创建 change
- `harness plan "<change>"` — 为 change 创建计划
- `harness regression "<issue>"` — 启动回归分析
- `harness status` — 查看当前状态

## 状态管理

- `workflow-runtime.yaml` 记录当前版本、阶段、会话模式
- `conversation_mode: harness` 时，必须锁定在当前版本和阶段，直到 `harness exit`
- 版本 `meta.yaml` 缺失或配置不一致时，立即停止并要求修复

## 常见错误

- 在 `harness` 会话模式中切换到其他版本操作
- 忘记读取 `workflow-runtime.yaml` 确认当前状态
- `harness update` 后忘记检查托管文件是否有冲突
