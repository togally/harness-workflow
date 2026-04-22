# Requirement

## 1. Title

工作流核心闭环重构

## 2. Goal

当前 harness 工作流缺少测试阶段和独立验收阶段，经验沉淀也没有与各阶段强绑定。本次重构目标是让包结构和文档产出完整体现以下五阶段闭环：

```
需求 → 开发 → 测试 → 验收 → 回归
              ↑___________________↓（派发回需求或测试）
```

每个阶段均配套：子步骤流转、文档模板、强制经验沉淀节点。

## 2.1 执行模型

```
主 Agent（Orchestrator）
  ├── 控制阶段流转（需求 → 开发 → 测试 → 验收 → 回归）
  ├── 读取 workflow-runtime.yaml，决定当前阶段和任务
  ├── 开启 Subagent 执行各阶段内的具体任务
  │     ├── 开发阶段：Subagent 实现单个 change
  │     ├── 测试阶段：Subagent 执行测试用例
  │     ├── 验收阶段：Subagent 逐项核对验收清单
  │     └── 回归阶段：Subagent 诊断并分析问题
  └── 收到 Subagent 结果后决定：推进/修正/派发回归
```

**关键约束：**
- 阶段推进只能由主 Agent 执行（`harness next`）
- Subagent 只执行当前阶段内的任务，不能跨阶段操作
- Subagent 通过 `session-memory.md` 向主 Agent 汇报结果
- 主 Agent 根据汇报结果决定是否满足阶段完成条件

## 3. Scope

**包含：**
- **两层测试模型**：
  - 第一层（change 级别，开发阶段内）：每个 change 开发完成后执行自测，不合格立即修正，合格才能标记该 change 完成
  - 第二层（requirement 级别）：所有 change 完成后，整体进入 `testing` stage 做集成/全量测试
- **验收粒度 = requirement 级别**：testing 通过后统一验收一次，不按 change 单独验收（按 change 验收会对不完整系统下结论，与整体测试前提冲突）
- **结构化经验体系**：见下方经验分类设计
- 新增 `testing` stage（测试用例设计 → 测试计划产出 → 经验沉淀）
- 新增 `acceptance` stage（依据文档验收 → 人工验收 → 经验沉淀），从 `done` 中剥离
- 每个阶段末尾新增强制经验沉淀节点（不再是可选 hook）
- 新增测试相关文档模板：`test-plan.md`、`test-cases.md`、`acceptance-checklist.md`
- `harness regression` 派发路径扩展，支持以下回归模型：
  ```
  发现问题 → 讨论确认是 bug
      ↓
  bug 写入 testing/bugs/（记录编号、描述、影响范围）
      ↓
  版本 stage 回退到 testing
      ↓
  Subagent 修复 bug
      ↓
  主 Agent 评估 bug 影响范围：
    - 影响范围小（局部）→ 针对性验证通过即可
    - 影响范围大（波及已验证模块）→ 触发全量回归，重走受影响测试用例
      ↓
  全部通过 → 重新进入 acceptance
  ```
- **版本目录结构按四阶段划分**（见下方目录设计）
- `core.py` 中 `apply_stage_transition` 增加新 stage 的状态机节点
- `harness next` 流转路径更新：`executing → testing → acceptance → done`

### 目录结构设计

每个版本下按四个阶段分文件夹，与工作流阶段一一对应：

```
versions/active/<version>/
  requirements/           ← 需求阶段
    <req-id>/
      requirement.md      ← 需求提出与讨论
      changes.md          ← 功能拆分列表
      completion.md       ← 需求完成记录
      meta.yaml
  changes/                ← 开发阶段
    <change-id>/
      change.md           ← 功能描述
      plan.md             ← 开发计划
      self-test.md        ← 自测记录（change 级别）
      session-memory.md
      meta.yaml
  testing/                ← 测试阶段（requirement 级别）
    test-plan.md          ← 测试计划
    test-cases.md         ← 测试用例
    bugs/                 ← 回归发现的 bug 列表
      <bug-id>.md         ← 单条 bug：描述、影响范围、修复记录
    session-memory.md
  acceptance/             ← 验收阶段（requirement 级别）
    acceptance-checklist.md  ← 依据文档的验收清单
    sign-off.md           ← 人工验收结论
    session-memory.md
  regressions/            ← 回归入口记录（指向 testing/bugs/）
  version-memory.md
  README.md
```

各阶段有独立文档模板，经验沉淀在每个阶段关闭时强制触发。

### 经验分类体系

经验分为两种加载模式：**阶段触发**（进入某阶段自动加载）和**工具触发**（任务涉及某工具时按需加载，跨阶段通用）。

```
workflow/context/experience/
  index.md                   ← 路由索引，定义各场景加载规则
  stage/                     ← 阶段触发（进入阶段时加载）
    requirement.md           ← 需求讨论、范围控制、拆分方法
    development.md           ← 开发规范、自测模式、常见陷阱
    testing.md               ← 测试设计、用例编写、覆盖策略
    acceptance.md            ← 验收方法、文档比对、结论记录
    regression.md            ← bug 判定、影响评估、回归范围决策
  tool/                      ← 工具触发（跨阶段，涉及工具时加载）
    playwright.md            ← 自动化测试（测试阶段常用）
    mysql-mcp.md             ← MCP 操作 MySQL（开发/测试阶段常用）
    nacos-mcp.md             ← MCP 接入 Nacos（开发阶段常用）
    harness.md               ← harness 命令与工作流操作
    <tool>.md                ← 其他工具按需扩展
  business/                  ← 业务触发（项目级，需求/验收阶段加载）
    <domain>.md
  architecture/              ← 设计触发（plan_review/功能拆分时加载）
    <pattern>.md
  debug/                     ← 诊断触发（testing/regression 阶段加载）
    <pattern>.md
  risk/                      ← 门禁（每次阶段推进前必读）
    known-risks.md
```

**index.md 路由规则：**

```markdown
## 阶段加载（进入阶段时）
需求阶段    → stage/requirement.md + business/*.md
开发阶段    → stage/development.md + architecture/*.md
测试阶段    → stage/testing.md + debug/*.md
验收阶段    → stage/acceptance.md + business/*.md
回归阶段    → stage/regression.md + debug/*.md + risk/known-risks.md

## 工具加载（任务涉及时，跨阶段按需）
Playwright  → tool/playwright.md
MySQL MCP   → tool/mysql-mcp.md
Nacos MCP   → tool/nacos-mcp.md
harness     → tool/harness.md
（主 Agent 根据任务上下文决定加载哪些工具经验）

## 风险门禁（每次阶段推进前）
→ risk/known-risks.md
```

### Hook 体系扩展设计

**结构原则**：保持现有**时机优先、阶段其次**的组织方式不变，仅在各时机目录下扩展新阶段子目录。

```
workflow/context/hooks/
  session-start/
    15-detect-subagent-mode.md    ← 新增：识别主/Subagent 身份
                                     Subagent 跳过 workflow 路由，直接读任务上下文
  node-entry/
    testing/                      ← 新增
      10-spawn-testing-subagent.md
    acceptance/                   ← 新增
      10-spawn-acceptance-subagent.md
  before-reply/
    testing/                      ← 新增
      10-no-advance-before-cases-pass.md
    acceptance/                   ← 新增
      10-require-document-basis.md
  during-task/
    testing/                      ← 新增
      10-subagent-reports-to-session-memory.md
    acceptance/                   ← 新增
      10-checklist-driven-only.md
  before-complete/
    testing/                      ← 新增
      10-require-all-cases-recorded.md
      20-require-bug-list-closed-or-tracked.md
    acceptance/                   ← 新增
      10-require-sign-off.md
      20-require-experience-capture.md
  context-maintenance/
    testing/                      ← 新增
    acceptance/                   ← 新增
```

**主 / Subagent 分工规则**（`15-detect-subagent-mode.md`）：
- 主 Agent：读 `workflow-runtime.yaml`，控制阶段推进，通过 Agent 工具派发 Subagent
- Subagent：不读 workflow 状态，只读分配给自己的任务上下文，结果写入 `session-memory.md`，完成即退出

### harness update 迁移兼容设计

本次重构需通过 `harness update` 向已有业务项目分发，迁移策略：

| 变更类型 | 迁移方式 |
|---------|---------|
| 新增模板文件（test-plan.md 等） | `write_if_missing` — 仅写入不存在的文件，不覆盖用户内容 |
| 新增 hook 文件 | `write_if_missing` — 同上 |
| 现有 hook 修改（如 before-complete） | 作为 managed 文件，按 hash 比对更新（用户未改则自动更新） |
| `_required_dirs` 新增目录 | `mkdir -p` 幂等创建，不影响现有数据 |
| 现有版本数据（requirements/changes/） | **不触碰**，仅新增 testing/ acceptance/ 空目录占位 |
| `AGENTS.md` / `CLAUDE.md` | 作为 managed 文件更新（新增 testing/acceptance 阶段说明） |

**迁移后现有项目状态**：已有 `executing` 阶段的版本在下次 `harness next` 时会进入新增的 `testing` stage，而非直接跳 `done`。需要在 `apply_stage_transition` 中处理此边界（见 change 1）。

### 进度监控设计

**架构**：进度文件作数据层，`harness status` 作展示层，主 Agent 用进度数据做阶段门禁决策。

**数据层**：版本目录下维护 `progress.yaml`，由工具和 Subagent 协同写入：

```yaml
stage: testing
stages:
  requirement:
    status: done
  development:
    status: done
    changes_total: 5
    changes_done: 5
  testing:
    status: in_progress
    cases_total: 10
    cases_passed: 7
    cases_failed: 3
    bugs_total: 2
    bugs_fixed: 1
    bugs_open: 1
  acceptance:
    status: pending
  done:
    status: pending
```

**展示层**：`harness status` 读取 `progress.yaml`，追加可视化进度树：

```
[v0.2.0-refactor] 工作流核心闭环重构
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 需求    完成
✅ 开发    完成  (5/5 changes)
🔄 测试    进行中 (7/10 用例通过 | 2 bugs: 1 open)
⏳ 验收    待开始
⏳ 完成    待开始
```

**决策层**：主 Agent 在执行 `harness next` 前读取进度，满足门禁条件才允许推进：
- `testing → acceptance`：`cases_failed == 0 && bugs_open == 0`
- `development → testing`：`changes_done == changes_total`

**不包含：**
- 自动化测试执行（仍由 AI/人工运行，不做 CI 集成）
- 现有已完成版本（v0.1.0-self-optimization）的数据回填

## 4. Acceptance Criteria

- `harness next` 可从 `executing` 推进到 `testing`，再到 `acceptance`，再到 `done`
- `harness regression --testing` 可将回归结果派发回 `testing` 节点，bug 写入 `testing/bugs/`
- 每个阶段完成时工具强制要求经验沉淀确认，不可跳过
- 新增文档模板和 hook 可通过 `harness update` 分发到业务项目
- `harness status` 可正确显示 `testing` / `acceptance` 阶段信息
- Subagent 模式下 `session-start` hook 正确识别身份，跳过 workflow 路由
- 已有 `executing` 阶段的版本升级后，`harness next` 进入 `testing` 而非 `done`
- 经验目录按分类结构初始化（`stage/` `tool/` `business/` `architecture/` `debug/` `risk/`）
- `harness update` 在已有项目中执行后：新增文件写入、现有用户文件不被覆盖、新目录幂等创建
- `harness status` 展示阶段进度树（✅/🔄/⏳ + 数量统计）
- `harness next` 在 `testing → acceptance` 时校验 `cases_failed == 0 && bugs_open == 0`
- `harness next` 在 `development → testing` 时校验 `changes_done == changes_total`

## 5. Split Rules

按依赖顺序独立交付：

1. **stage 状态机扩展**（`core.py`）
   - `apply_stage_transition`：`executing → testing → acceptance → done`
   - `harness regression --testing` 派发路径
   - `_required_dirs` 新增 `testing/` `acceptance/` 目录
   - `_sync_artifact_statuses` 扩展新阶段

2. **文档模板新增**
   - `test-plan.md`、`test-cases.md`、`bug.md`（单条 bug 模板）
   - `acceptance-checklist.md`、`sign-off.md`
   - `self-test.md`（change 级自测记录）

3. **Hook 扩展**
   - `session-start/15-detect-subagent-mode.md`
   - `node-entry/testing/`、`node-entry/acceptance/`
   - `before-reply/testing/`、`before-reply/acceptance/`
   - `during-task/testing/`、`during-task/acceptance/`
   - `before-complete/testing/`、`before-complete/acceptance/`
   - `context-maintenance/testing/`、`context-maintenance/acceptance/`

4. **经验体系重构**
   - `experience/` 目录按分类重组（`stage/` `tool/` `business/` `architecture/` `debug/` `risk/`）
   - `index.md` 改为路由索引格式
   - 现有经验文件迁移至对应分类

5. **harness update 迁移兼容**
   - `_managed_file_contents` 注册所有新模板和 hook
   - `_required_dirs` 新增目录幂等创建
   - `AGENTS.md`/`CLAUDE.md` 模板更新（加入新阶段说明）
   - 现有版本边界处理（`executing` → `testing` 路径验证）

6. **进度监控**
   - `progress.yaml` 数据结构设计与写入逻辑（工具侧在阶段推进时自动更新）
   - `harness status` 读取 `progress.yaml` 输出可视化进度树
   - 阶段推进门禁：`harness next` 校验进度条件（cases_failed、bugs_open、changes_done 等）
   - Subagent 侧：测试用例执行结果、bug 修复状态写回 `progress.yaml`
