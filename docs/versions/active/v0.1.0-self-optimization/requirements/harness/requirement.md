# Requirement

## 1. Title

Harness 工程完善与自进化规范

## 2. Goal

Harness 工程已有基本工作流（version → requirement → change → plan → execution）和三平台集成（Claude Code / Codex / Qoder），但存在以下待解决的问题：

1. **能力审计不完整**：19 条命令缺乏端到端的功能验证，部分边界场景无测试覆盖
2. **缺少自进化机制**：experience 系统仅有手动索引，没有自动积累、评级升级、规则沉淀的闭环
3. **工具项目 vs 应用项目分治不足**：harness 自身作为工具项目，与被 harness 管理的应用项目，在进化路径上没有分开设计
4. **Agent 求助路径断裂**：Agent 碰到需要外部信息时（配置、数据库、服务状态），直接问人而不先查 MCP 能否解决，缺少 MCP 能力索引和自动发现机制
5. **MCP 经验无法跨项目复用**：项目 A 发现 nacos MCP 好用，项目 B 还是从零开始摸索

核心目标：让 harness 管理的项目"越用越聪明"——
- **应用项目线**：积累业务经验 + MCP 使用经验，命中越多优先级越高
- **工具项目线**：积累流程优化经验 + MCP 通用推荐，install 新项目时自动推荐已验证的 MCP
- 两条线各自闭环且互不干扰

## 3. Scope

### 包含

- **A. 现有能力审计与测试补全**：梳理全部 19 条命令的行为规格，补全缺失的测试场景
- **B. 已知缺陷修复**：审查 core.py 和模板中的已知问题并修复
- **C. 自进化规范设计**：设计 experience 自动采集 → 置信度升级 → 规则沉淀的完整闭环，含 MCP 经验沉淀规则
- **D. 工具反馈回流**：静默采集 + `harness feedback` 命令 + MCP adoption 回流
- **E. 自进化规范实现**：将设计落地为代码、模板、文档
- **F. 工具项目自优化规范**：反馈聚合 → 优化提案 → 确认 → 发版闭环
- **G. MCP 能力索引与决策链**：项目级 mcp-registry + 工具级 mcp-catalog + install 自动推荐 + before-human-input 决策链

### 不包含

- 外部 CI/CD 集成实现（仅保留模板）
- 实际 Maven 编译 / 启动验证的 mock 实现
- 三平台 API 的集成测试
- MCP Server 的实现（只做索引、推荐、决策链，不做 server 本身）

## 4. Acceptance Criteria

1. 全部 19 条 harness 命令均有对应测试覆盖，现有测试 100% 通过
2. `harness install` 后 lint 检查 0 error
3. experience 自进化闭环文档完整：采集触发点 → 置信度升级规则 → 规则沉淀条件 → 过期清理策略
4. 工具项目自优化闭环文档完整：优化提案模板 → 评审标准 → 应用流程
5. 自进化的核心采集逻辑有代码实现和测试
6. `harness feedback` 命令可运行并输出结构化 JSON
7. MCP 决策链文档完整，before-human-input hook 中集成查询逻辑
8. 项目级 mcp-registry 模板 + 工具级 mcp-catalog 模板就绪
9. `harness install` 能扫描项目依赖并推荐匹配的 MCP
10. 新增文档和模板同时提供中英文版本

## 5. Split Rules

拆分为以下独立可交付的 change 单元：

### Change 1: 现有能力审计与测试补全
- 梳理 19 条命令的完整行为规格表
- 运行现有测试，确认基线状态
- 补全缺失的边界场景测试

### Change 2: 已知缺陷修复
- 基于审计发现的问题逐项修复
- 每修一个问题补一个回归测试

### Change 3: 自进化规范设计（Experience Evolution Spec）
- 设计 experience 自动采集的触发时机和格式
- 设计置信度升级规则（low → medium → high），命中越多越频繁优先级越高
- 设计规则沉淀条件（何时从 experience 晋升为正式 rule）
- 设计过期/淘汰策略
- 区分应用项目经验 vs 工具项目经验的不同路径
- MCP 经验沉淀规则：MCP 解决问题后自动记录到 experience，含调用方式和适用场景

### Change 4: 工具反馈回流设计与实现
- 下游项目静默采集：在现有命令中嵌入结构化事件记录（ff 次数、模板 drift、regression 模式、阶段耗时、MCP adoption）
- `harness feedback` 命令：采集汇总 → 输出结构化 JSON 到当前目录
- 输出格式面向未来兼容：同一份 JSON 可被 MCP tool 提交、curl 调 API、或手动 import
- 不含业务数据，只记录结构性事件统计
- MCP 使用数据随 feedback 一起回流到工具仓库

### Change 5: 自进化核心实现
- experience 自动采集逻辑（应用项目线：命中计数 → 置信度升级 → 规则沉淀）
- feedback 事件采集逻辑（工具项目线：嵌入现有命令的 hook）
- `harness feedback` 命令实现
- 测试覆盖

### Change 6: 工具项目自优化规范设计（Tool Self-Optimization Spec）
- 设计反馈聚合 → 优化提案 → 人工确认 → 发版生效的完整闭环
- 设计三级通道规格（本地文件 / MCP / Remote API），当前只实现第一级
- 设计模板/hook/命令的优化评审标准

### Change 7: MCP 能力索引与决策链
- 项目级 mcp-registry.yaml 模板：记录本项目已安装的 MCP 及其能力范围
- 工具级 mcp-catalog.yaml：收录通用 MCP，含 triggers（依赖关键词匹配）、adoption（使用项目数）、confidence
- `harness install` 扫描项目依赖（pom.xml / package.json / go.mod / application.yml），匹配 catalog triggers，推荐安装 MCP
- before-human-input 决策链：查经验 → 查项目 registry → 扫依赖匹配 catalog → 搜索社区 MCP → 其他方式 → 才问人
- MCP 经验回流：项目用了新 MCP 并验证有效 → feedback 回报 → 工具 catalog 收录（low）→ adoption 累积升级
