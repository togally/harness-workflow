# Change Plan

## 1. Development Steps

1. 读取现有 `harness-manager.md` 和相关 role 文件
2. 设计 harness-manager 的完整执行逻辑架构：
   - 命令理解层（解析 harness 命令意图）
   - 角色调度层（按需启动 subagent）
   - 项目洞察层（理解项目结构）
3. 实现所有命令的 harness-manager 引导逻辑：
   - install/update/language：工具安装和配置
   - enter/exit/next/ff/status/validate：工作流控制
   - requirement/change/bugfix/rename/archive：需求变更管理
   - suggest/tool-search/tool-rate：建议和工具管理
   - regression/feedback：回归和反馈
4. 集成 toolsManager 工具管理
5. 测试各命令执行路径

## 2. Verification Steps

- [ ] `harness install claude` 能正常完成
- [ ] `harness update` 能正常更新
- [ ] `harness requirement` 能创建需求
- [ ] `harness change` 能创建变更
- [ ] `harness bugfix` 能创建 bugfix
- [ ] `harness archive` 能归档需求
- [ ] `harness suggest` 建议功能正常
- [ ] `harness regression` 回归功能正常
- [ ] `harness ff` / `harness next` 工作流推进正常
- [ ] Agent 能正确加载 harness-manager 角色
