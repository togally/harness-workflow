# harness-workflow

> 📖 [English](README.md)

**结构化 AI 工作流系统**，用于在 AI 辅助软件开发中实现需求管理、变更追踪、多阶段质量门控和经验沉淀。

核心理念：**管理 AI 开发，而不是放飞**。通过文档驱动、角色分离、结构约束，让 AI agent 在明确边界内可控、可追溯地完成软件工程任务。

---

## 为什么需要 harness-workflow？

大多数 AI 编码工具只给你一个大上下文窗口，然后听天由命。harness-workflow 提供：

- **阶段门控工作流** — 需求 → 变更 → 规划 → 执行 → 测试 → 验收 → 完成
- **角色分离** — 每个阶段使用专属 agent 角色（分析师、架构师、工程师、测试员、验收官）
- **持久化状态** — 需求和变更通过 YAML + Markdown 文件在上下文窗口重置后依然存在
- **经验沉淀** — 每个项目的教训被捕获并在未来会话中复用
- **多平台支持** — 支持 Claude Code、Codex、Qoder

---

## 六层架构

```
.workflow/
├── context/        ← 第一层：角色定义、经验沉淀、项目背景、团队规范
├── tools/          ← 第二层：工具目录、选择指南、各阶段工具白名单
├── flow/           ← 第三层：Stage 定义、需求文档、变更计划
├── state/          ← 第四层：运行时状态、需求进度、会话记忆
├── evaluation/     ← 第五层：测试规则、验收规则、回归诊断
└── constraints/    ← 第六层：行为边界、风险扫描、失败恢复路径
```

### Stage 流转

```
requirement_review  （需求评审）
        ↓
  changes_review    （变更评审）
        ↓
   plan_review      （计划评审）
        ↓
ready_for_execution （等待执行确认）
        ↓
    executing       （执行中）
        ↓
     testing        （测试）
        ↓
    acceptance      （验收）
        ↓
      done          （完成）
```

每个 Stage 都有专属角色文件（`.workflow/context/roles/`），约束行为、工具访问和退出条件。

---

## 安装

```bash
pipx install git+https://github.com/togally/harness-workflow.git
```

然后初始化仓库：

```bash
cd your-project
harness install          # 安装 Claude Code / Codex / Qoder 的 skill 文件
```

---

## 核心命令

| 命令 | 说明 |
|------|------|
| `harness status` | 查看当前需求、阶段和运行时状态 |
| `harness requirement "<标题>"` | 创建新需求并进入 requirement_review |
| `harness change "<标题>"` | 在当前需求下创建新变更 |
| `harness next` | 推进到下一个工作流阶段 |
| `harness next --execute` | 确认执行（进入 executing 阶段必须） |
| `harness regression "<问题>"` | 开始回归分析流程 |
| `harness archive <req-id> [--folder <名称>]` | 归档已完成的需求 |
| `harness rename requirement <旧> <新>` | 重命名需求 |
| `harness rename change <旧> <新>` | 重命名变更 |
| `harness ff` | 快进到 ready_for_execution |
| `harness update` | 刷新仓库中的受管文件 |
| `harness feedback` | 导出使用事件统计摘要 |

### 快速开始

```bash
harness install
harness requirement "在线健康服务"
# ... 与 AI 讨论并确认需求 ...
harness next
# ... 拆分变更，评审计划 ...
harness next --execute
# ... 实施 ...
harness next          # → testing
harness next          # → acceptance
harness next          # → done
```

---

## 实践原则

1. **上下文爆满时不压缩** — 新开 agent，通过 `session-memory.md` 交接
2. **每阶段 agent 分开** — 生产者和评估者必须是不同实例
3. **审查不只审代码** — 也要操作页面、检查交互、验证结果
4. **独立才有反馈闭环** — 角色分离是有效循环的前提
5. **从缺失的结构性能力总结经验** — agent 出问题时向内归因
6. **薄入口** — 通过目录索引保证入口精简，详细信息按需暴露
7. **可持续自治** — 目标是构建能自我运行的自治系统

---

## 支持平台

| 平台 | 入口文件 |
|------|---------|
| Claude Code | `CLAUDE.md`、`.claude/commands/harness-*.md`、`.claude/skills/harness/` |
| Codex | `AGENTS.md`、`.codex/skills/harness/`、`.codex/skills/harness-*/` |
| Qoder | `.qoder/skills/harness/`、`.qoder/commands/harness-*.md`、`.qoder/rules/harness-workflow.md` |

---

## 详细规则位置

- `WORKFLOW.md` — agent 工作流入口
- `.workflow/context/index.md` — 加载顺序和路由规则
- `.workflow/context/roles/<stage>.md` — 各阶段角色定义
- `.workflow/context/experience/` — 积累的项目经验
- `.workflow/constraints/` — 行为边界和风险规则
- `.workflow/flow/stages.md` — 阶段流转条件

---

## 目录结构

```
.workflow/
├── context/
│   ├── index.md              # 加载顺序和路由规则
│   ├── roles/                # 各阶段角色定义
│   ├── experience/           # 经验索引和经验文件
│   ├── project/              # 项目概述和背景
│   └── team/                 # 团队开发规范
├── tools/
│   ├── index.md              # 工具系统总览
│   ├── stage-tools.md        # 各阶段工具白名单
│   ├── selection-guide.md    # 工具选择指南
│   └── catalog/              # 单个工具文档
├── flow/
│   ├── requirements/         # 活跃需求工作区
│   ├── archive/              # 已归档需求（按需创建）
│   └── stages.md             # 阶段流转规则
├── state/
│   ├── runtime.yaml          # 全局运行时状态
│   ├── requirements/         # 每个需求的状态文件
│   └── sessions/             # 会话记忆文件
├── evaluation/               # 测试和验收规则
└── constraints/              # 行为边界和恢复路径
```
