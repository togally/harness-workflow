# Experience Index

## 阶段加载（进入阶段时自动加载）
| 阶段 | 加载文件 |
|------|---------|
| 需求阶段 | stage/requirement.md + business/*.md |
| 开发阶段 | stage/development.md + architecture/*.md |
| 测试阶段 | stage/testing.md + debug/*.md |
| 验收阶段 | stage/acceptance.md + business/*.md |
| 回归阶段 | stage/regression.md + debug/*.md + risk/known-risks.md |

## 工具加载（任务涉及时按需加载，跨阶段通用）
| 工具 | 加载文件 |
|------|---------|
| Playwright | tool/playwright.md |
| MySQL MCP | tool/mysql-mcp.md |
| Nacos MCP | tool/nacos-mcp.md |
| harness | tool/harness.md |

## 风险门禁（每次阶段推进前必读）
→ risk/known-risks.md

## 目录说明
- stage/     阶段方法论与最佳实践
- tool/      工具使用经验（跨阶段）
- business/  业务领域知识（项目级）
- architecture/ 设计决策与模式
- debug/     诊断模式与修复套路
- risk/      已知风险与缓解方案
