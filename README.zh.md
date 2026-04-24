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
- **多平台支持** — 支持 Claude Code、Codex、Qoder、kimicli

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

**普通用户** — 从 GitHub 安装：

```bash
pipx install git+https://github.com/togally/harness-workflow.git
```

**开发者 / 本机要改源码** — 使用 editable 模式安装，源码改动即时生效，无需 reinstall：

```bash
pipx install -e /path/to/harness-workflow
# 本模式下改源码即生效，无需 reinstall。
```

然后在目标仓库初始化：

```bash
cd your-project
harness install          # 安装 Claude Code / Codex / Qoder / kimicli 的 skill 文件
```

`harness install` 幂等运行，可重复执行。它负责初始化 `.workflow/` 脚手架、同步 skill 文件、迁移 legacy state、写盘 experience index 和 project-profile（req-33（install 吸收 update CLI 职责）/ chg-01）。

如需强制覆写已有 skill 文件（例如有 breaking update 后）：

```bash
harness install --force  # 强制重装所有平台 skill
```

---

## 更新 / 升级

共三种场景，请按需选择。

### 场景 A — 升级已发布的 harness-workflow CLI（多数用户）

拉取 PyPI / git 上的新版 CLI 代码（例如获取 chg-03（runtime pending + next/status gate）新增的 pending gate）：

```bash
pipx reinstall harness-workflow
# 或
pipx upgrade harness-workflow
```

> **注意：** pipx 安装的 binary 是快照，**不会**随上游仓库自动更新。每次想用最新发布版时，需手动执行上述命令。

### 场景 B — 本机 editable 安装，同步最新代码

若你使用 `pipx install -e` 安装，`git pull` 即可；editable 模式直接从源码加载，无需 reinstall：

```bash
git pull    # 在 harness-workflow 仓库目录下执行；改动立即生效
```

无需 reinstall。

### 场景 C — 在某个 harness 用户仓库里刷新 workflow 模板 / skill / managed 文件

```bash
harness install          # 幂等；已吸收原 update 全部刷新职责（req-33（install 吸收 update CLI 职责）/ chg-01）
harness update --check   # 可选：预览仓库文件与模板的 drift
```

---

## `harness update` — 它实际做什么

`harness update` **不是** CLI 升级命令，请勿用它来升级 harness 工具本体（请走场景 A）。

| 调用方式 | 行为 |
|----------|------|
| `harness update`（无 flag） | 打印 3 行引导后退出。若需生成项目现状报告，请在 agent 会话中说 **"生成项目现状报告"**（或"项目状态" / "项目快照" / "生成 project-overview.md"）——这将触发 project-reporter 角色（req-32（新设 project-reporter 角色）/ chg-02）产出 `artifacts/main/project-overview.md`。 |
| `harness update --check` | Drift 预览——显示仓库文件与 harness 模板的差异。 |
| `harness update --scan` | 项目适配扫描——检测技术栈和目录结构。 |

**升级 CLI 本体**请用 `pipx reinstall harness-workflow`（场景 A）。

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
| `harness archive <req-id> [--folder <名称>]` | 归档已完成的需求（仅限 `done` 状态） |
| `harness rename requirement <旧> <新>` | 重命名需求 |
| `harness rename change <旧> <新>` | 重命名变更 |
| `harness ff` | 快进到 ready_for_execution |
| `harness update`（无 flag） | 打印引导；在 agent 会话说"生成项目现状报告"召唤 project-reporter（req-32（新设 project-reporter 角色）/ chg-02） |
| `harness update --check` | Drift 预览：显示受管文件与模板的差异 |
| `harness update --scan` | 项目适配扫描：检测技术栈和目录结构 |
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

## 本地开发

**推荐做法：** 从一开始就用 editable 模式安装（见安装章节）。源码改动即时生效，无需任何 reinstall 操作。

如果你安装的是非 editable 版本，需要在本地测试改动时，重新注入到 pipx 环境：

```bash
pipx inject harness-workflow . --force
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
| kimicli | `.kimi/skills/{命令}/SKILL.md`（YAML frontmatter + Markdown 格式） |

---

## 制品仓库

根目录 `artifacts/` 作为已完成需求的知识库：

- **`artifacts/requirements/`** — 由 `harness archive` 自动生成。每个归档需求会生成一份 `{req-id}-{标题}.md` 摘要文档，包含业务背景、需求目标、交付范围、验收标准、变更列表和关键设计决策，便于新成员快速接手。
  > **注意：** `harness archive` 仅处理 `done` 状态的需求。未完成完整工作流的需求无法被归档。
- 其他子目录（`sql/`、`api/` 等）由团队手动维护。

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
