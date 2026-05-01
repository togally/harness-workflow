# harness-workflow

> 📖 [English](README.md)

**结构化 AI 工作流系统**，用于 AI 辅助软件开发。harness-workflow 为 AI agent 提供文档驱动、角色分离、阶段门控的运作模式，让工作可追溯、可重复、可审计——不只是靠着大上下文窗口侥幸成功。

核心理念：**管理 AI 开发，而不是放飞。**

大多数 AI 编码工具只给你一个大上下文窗口，然后听天由命。harness-workflow 提供结构：

---

## §1 它是什么，解决什么问题

- **阶段门控工作流** — 需求评审 → 规划 → 执行 → 测试 → 验收 → 完成
- **角色分离** — 每个阶段使用专属 agent 角色；生产者与评估者始终是不同实例
- **持久化状态** — 需求和变更通过 `.workflow/` 下的 YAML + Markdown 文件在上下文重置后依然存在
- **经验沉淀** — 每个项目的教训被捕获并在未来会话中复用
- **多平台支持** — Claude Code、Codex、Qoder、kimicli

---

## §2 安装

**普通用户** — 从 GitHub 安装：

```bash
pipx install git+https://github.com/togally/harness-workflow.git
```

**升级到最新发布版** — pipx 安装的 binary 是快照，**不会**随上游仓库自动更新：

```bash
pipx reinstall harness-workflow
# 或等价：
pipx upgrade harness-workflow
```

若通过 pip 安装，升级命令为：

```bash
pip install -U harness-workflow
harness update           # 升级后刷新仓库受管文件（AC-10 下游刷新模板）
```

**开发者 / 本机要改源码** — 使用 editable 模式安装，源码改动即时生效：

```bash
pipx install -e /path/to/harness-workflow
# 在仓库目录里 git pull 即可拉取最新改动
```

**初始化项目** — 在任何你想用 harness 管理的仓库里执行：

```bash
cd your-project
harness install                                                    # 交互模式：选 agent + 同步 scaffold（默认保护本地修改）
harness install --agent <claude|codex|kimi|qoder> --force-managed  # 强制覆盖 user-modified scaffold（升级到含重大文档变化的版本时使用）
```

**两种安装模式区别**（实证 req-50 升级场景）：

| 命令 | 何时用 | 行为 |
|---|---|---|
| `harness install` | 第一次装 / 用户没改过 scaffold / 升级时只想拿新文件 | 选 agent → 同步 scaffold；遇 user-modified 文件**默认 skip**（drift 警告但不动）|
| `harness install --agent <X> --force-managed` | 升级到含重大文档/契约变化的新版本 | 强制覆盖所有 user-modified scaffold；目标项目内容应该都是工具产出，用户不该手改 |

> 默认 `harness install`（无 `--force-managed`）会跳过 user-modified 文件保护。若 self-audit drift 提示某些文件 "content differs"，那是上游改了但本地未同步——加 `--force-managed` 真同步。

`harness install` 幂等运行，可重复执行。它负责初始化脚手架、同步 skill 文件、迁移 legacy state、写盘 experience index 和 project profile。

> **刷新模板：** 在已有项目中重新同步 skill 文件和受管文件，再跑一次 `harness install` 即可（不是 `harness update`——见 §3）。

---

**多项目工作区**（1.0.1+）：root 自身无项目文件 + 顶层 ≥2 子目录各有项目文件时（如 `monorepo/{frontend,backend,admin,...}/`），自动切 workspace 模式：单一聚合路书（按 sub-project 分段），每段标 `### {dir} ({stack})`。详见 CHANGELOG 1.0.1。

**`.workflow/` 本地化**（1.0.1+）：1.0.1 起 `.workflow/` 整体不入 git（state/ 是个人运行时；context/ 是 framework-level 模板由 `harness install` 重建）；团队级经验仍在 `artifacts/project/experience/` 由 git 管理。已 commit 项目升级后跑 `git rm --cached -r .workflow/` 迁移。

## §3 命令

| 命令 | 说明 |
|------|------|
| `harness install [--force]` | 初始化 / 刷新脚手架和 skill 文件（`--force` 强制覆写） |
| `harness status` | 查看当前需求、阶段和运行时状态 |
| `harness validate` | 检查当前需求的工件完整性 |
| `harness requirement "<标题>"` | 创建需求并进入评审阶段 |
| `harness change "<标题>"` | 在当前需求下创建变更 |
| `harness next` | 推进到下一个阶段 |
| `harness next --execute` | 确认执行（进入执行阶段的必要步骤） |
| `harness ff` | 快进：AI 自动完成后续所有阶段 |
| `harness suggest "<内容>"` | 随手记下想法，不立即启动需求流程 |
| `harness suggest --list` | 列出所有待处理的建议 |
| `harness suggest --apply <id>` | 将建议升级为正式需求 |
| `harness suggest --apply-all [--pack-title "..."]` | 将所有待处理建议打包为一个需求 |
| `harness suggest --delete <id>` | 删除建议 |
| `harness regression "<问题>"` | 启动回归诊断流程；关闭时自动生成经验文件 |
| `harness regression --confirm` | 确认是真实问题，进入修复流程 |
| `harness regression --reject` | 确认为误判，回到触发前的阶段 |
| `harness regression --change / --requirement "<标题>"` | 将诊断结果转为新变更或新需求 |
| `harness archive <req-id> [--folder <名称>]` | 归档已完成的需求（仅限 `done` 状态） |
| `harness rename requirement/change <旧> <新>` | 重命名需求或变更 |
| `harness feedback` | 导出使用事件统计摘要 |
| `harness playbook-refresh [--no-llm]` | 刷新项目路书（AUTO 区段静态扫描 + LLM 区段模型推断）；NoopProvider fallback 时输出 `[ASSISTANT INSTRUCTION]` 引导当前 agent 接力填 LLM 区段 |
| `harness playbook-check` | 路书漂移检测（AUTO 哈希 / LLM marker 完整性 / USER 区段永不报漂移）|

### `harness update` — 它实际做什么

`harness update` **不是** CLI 升级命令，请勿用它升级 harness 工具本体（请用 `pipx reinstall harness-workflow`）。

| 调用方式 | 行为 |
|----------|------|
| `harness update`（无 flag） | 打印简短引导后退出。如需生成项目现状报告，在 agent 会话中说 **"生成项目现状报告"** 即可触发。 |
| `harness update --check` | Drift 预览——显示受管文件与模板的差异 |
| `harness update --scan` | 项目适配扫描——检测技术栈和目录结构 |

---

## §4 使用场景

### 场景 A：端到端交付一个新需求

```bash
harness install                          # 首次项目初始化
harness requirement "在线健康 API"        # 进入需求评审
# 与 AI 讨论并确认范围
harness next                             # 推进到规划阶段
# 评审变更拆分和执行计划
harness next --execute                   # 确认并开始执行
# AI 实施各项变更
harness next                             # → 测试
harness next                             # → 验收
harness next                             # → 完成
harness archive req-01                   # 归档已完成的需求
```

流转：需求评审 → 规划 → 执行 → 测试 → 验收 → 完成。四个平台（Claude Code、Codex、Qoder、kimicli）共用同一份 `.workflow/` 状态。

### 场景 B：随手记想法，之后再决定

```bash
harness suggest "在设置页面添加暗色主题切换"
harness suggest "重构认证中间件以支持 JWT 刷新"
harness suggest --list                              # 查看待处理列表
harness suggest --apply sug-01                      # 升级为正式需求
harness suggest --apply-all --pack-title "UI 优化冲刺"  # 全部打包为一个需求
```

建议在轻量池中存放，不需要任何阶段开销，随时可以决定要不要推进。

### 场景 C：出了问题——诊断并修复

```bash
harness regression "Token 刷新后登录失败"
# AI 诊断根因，产出 diagnosis.md
harness regression --confirm              # 确认是真实问题 → 进入修复流程
# 或
harness regression --change "修复 token 刷新边界情况"   # 转为新变更
# 或
harness regression --reject               # 误判，回到触发前的阶段
```

回归诊断可在任意阶段触发。关闭回归时会自动产出经验文件，供后续会话参考。

### 场景 D：多平台共存

`harness install` 一次性写入四个平台的 skill 文件。CLI 升级后运行 `harness install --force` 保持 skill 文件最新。

## harness pad — 项目级承载层维护

往 `artifacts/project/` 加规则 / 经验 / 工具，命令封装"路径正确 + index 登记 + git stage"全套：

```bash
# 加规则（5 个 scope：coding / architecture / api / database / security）
harness pad rule coding "禁止-API-硬编码"

# 加经验（5 个 scope：roles / stage / regression / risk / tool）
harness pad experience stage "executing-虚报教训"

# 加工具（不分 scope）
harness pad tool "petmall-deployer"

# 列已有
harness pad list

# 无参数 → 交互引导
harness pad
```

落位规则（固定枚举，user 不能发明）：

| kind | 路径 |
|------|------|
| rule | `artifacts/project/constraints/{scope}/{slug}.md` |
| experience | `artifacts/project/experience/{scope}/{slug}.md` |
| tool | `artifacts/project/tools/{slug}.md` |

命令成功后会自动 `git add`；user 仅需 `git commit -m "..."`（按 stdout 提示）。
