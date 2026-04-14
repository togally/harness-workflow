# Context 加载规则

本文件定义会话启动时的完整加载顺序，以及如何根据运行时状态路由到对应角色、经验和约束文件。

---

## 加载顺序

### Session Start（每次会话开启时，在 Step 1 之前）

读取以下背景文件，建立项目和团队上下文：
- `.workflow/tools/index.md`：了解工具系统结构和可用工具层
- `.workflow/context/project/project-overview.md`：项目定位、六层架构、演进背景

---

### Step 1：读取运行时状态（必须第一步）

读取 `.workflow/state/runtime.yaml`，提取以下字段：

| 字段 | 用途 |
|------|------|
| `current_requirement` | 确定当前活跃需求 |
| `stage` | 路由到对应角色文件和经验分类 |
| `conversation_mode` | 判断是否锁定当前节点 |
| `locked_requirement` / `locked_stage` | 若非空，优先使用锁定值 |

**如果 `current_requirement` 为空或 `stage` 字段缺失**：立即停止加载，告知用户会话未路由，引导用户创建需求（`harness requirement "<title>"`）。

---

### Step 2：加载角色文件（依据 stage 路由）

读取 `.workflow/context/roles/index.md` 获取路由表，再按 stage 加载对应角色文件：

| Stage | 角色文件 |
|-------|---------|
| `requirement_review` | `.workflow/context/roles/requirement-review.md` |
| `planning` | `.workflow/context/roles/planning.md` |
| `executing` | `.workflow/context/roles/executing.md` |
| `testing` | `.workflow/context/roles/testing.md` |
| `acceptance` | `.workflow/context/roles/acceptance.md` |
| `regression` | `.workflow/context/roles/regression.md` |

角色文件包含该阶段的完整行为约束，是 subagent 的完整 briefing，**必须完整加载**。

在 `testing`、`acceptance`、`regression` 阶段，还需在 `.workflow/evaluation/` 下加载对应的评估文件（如存在）：
- `evaluation/testing.md`（testing 阶段）
- `evaluation/acceptance.md`（acceptance 阶段）
- `evaluation/regression.md`（regression 阶段）

---

### Step 3：加载经验文件（按 stage 分类）

读取 `.workflow/state/experience/index.md` 获取加载规则，再按 stage 加载 `.workflow/context/experience/` 下的对应经验文件：

| Stage | 加载分类 |
|-------|---------|
| `requirement_review` / `planning` | `.workflow/context/experience/stage/requirement.md` |
| `executing` | `.workflow/context/experience/stage/development.md` + `.workflow/context/experience/tool/harness.md` |
| `testing` / `acceptance` | `.workflow/context/experience/stage/testing.md` + `.workflow/context/experience/stage/acceptance.md` |
| `regression` | `.workflow/context/experience/stage/regression.md` + `.workflow/context/experience/risk/known-risks.md` |

**不得批量加载整棵经验目录树**，只加载与当前 stage 匹配的分类。

---

### Step 4：加载团队与项目上下文（before-task）

在开始实质性任务（生成代码、修改文件、制定计划）前加载：
- `.workflow/context/team/development-standards.md`：团队开发规范、代码风格约束

---

### Step 5：加载风险文件

读取 `.workflow/constraints/risk.md`，扫描高风险关键词。

约束文件层级参考 `.workflow/constraints/index.md`：
- `constraints/boundaries.md`：行为边界细则（before-task 时按需加载）
- `constraints/risk.md`：风险扫描规则（before-task 必须执行）
- `constraints/recovery.md`：失败恢复路径（遇到失败时加载）

---

### Step 6：检查流转规则（按需）

如需判断 stage 推进条件或归档规则，读取 `.workflow/flow/stages.md`。

---

## 状态缺失或不一致的处理

| 情况 | 处理方式 |
|------|---------|
| `runtime.yaml` 不存在 | 立即停止，告知用户文件缺失，不执行任何工作 |
| `current_requirement` 为空 | 停止，引导用户用 `harness requirement` 创建需求 |
| `stage` 字段缺失或不在已知列表 | 停止，告知 stage 未识别，请检查 runtime.yaml |
| `conversation_mode: harness` | 锁定当前节点，不得漂移到其他需求或阶段 |
| `locked_requirement` / `locked_stage` 非空 | 使用锁定值覆盖 `current_requirement` / `stage` |

---

## 加载顺序速查

```
[session-start]
tools/index.md + context/project/project-overview.md ← 工具和项目背景
    ↓
runtime.yaml
    ↓ 提取 current_requirement + stage
roles/{stage}.md          ← 角色约束（必须）
evaluation/{stage}.md     ← testing/acceptance/regression 阶段额外加载
    ↓
context/experience/{分类}/  ← 按 stage 过滤（规则见 state/experience/index.md）
    ↓
[before-task]
team/development-standards.md ← 团队规范
    ↓
constraints/risk.md       ← 风险扫描（必须）
    ↓
flow/stages.md            ← 按需（流转判断时）
```
