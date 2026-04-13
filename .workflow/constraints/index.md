# 约束与失败恢复层

## 约束层级

```
CLAUDE.md                          全局硬门禁（始终在 context，始终生效）
    ↓
context/roles/{stage}.md           Stage 级约束（进入阶段时加载，内嵌在角色文件中）
    ↓
constraints/boundaries.md          行为边界细则（before-task 时按需加载）
    ↓
constraints/risk.md                风险扫描规则（before-task 必须执行）
```

## 文件索引

| 文件 | 内容 | 加载时机 |
|------|------|---------|
| `boundaries.md` | 行为边界细则（跨层/跨阶段的通用边界） | before-task |
| `risk.md` | 风险关键词 + 处理规则 | before-task（必须） |
| `recovery.md` | 失败恢复三条路径 + 上下文爆满处理 | 遇到失败时 |

## 核心原则

1. 重要约束不只放在本层——必须注入到始终在 context 的文件（CLAUDE.md、角色文件）
2. 本层是约束的详细规则库，不是执行入口
3. 执行入口是：CLAUDE.md（全局）、角色文件（stage 级）、before-task hook（触发点）
