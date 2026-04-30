# 角色加载协议（Role Loading Protocol）

本文件定义 Harness Workflow 中**所有角色**（含顶级角色、stage 角色、辅助角色）的通用加载步骤。任何 agent 在被唤醒后，必须遵循本协议加载自己的角色 briefing，然后才能执行工作。

## 核心原则

- **所有角色平等**：顶级角色（Director）和 stage 角色都遵循同一套前置加载流程
- **角色索引是入口**：`.workflow/context/index.md` 是所有角色的唯一索引表
- **角色文件是 briefing**：找到角色后，必须完整读取对应的 `.md` 文件
- **模型一致性**：所有角色按 `.workflow/context/role-model-map.yaml` 声明的 model 执行；subagent 模型不盲从 parent，也不硬编码具体版本号（见 Step 7.5）
- **base-role 是所有角色的通用规约**：加载任何角色前，必须先加载 `base-role.md`
- **stage-role 是 stage 角色的公共父类**：stage 执行角色在加载自身前，必须先加载 `base-role.md`，再加载 `stage-role.md`

---

## 通用加载步骤

### Step 1：读取运行时状态（必须第一步）

读取 `.workflow/state/runtime.yaml`，提取以下字段：

| 字段 | 用途 |
|------|------|
| `current_requirement` | 确定当前活跃需求 |
| `stage` | 如果你是 stage 执行角色，确定当前 stage |
| `conversation_mode` | 判断是否锁定当前节点 |
| `locked_requirement` / `locked_stage` | 若非空，优先使用锁定值 |

**异常处理**：
| 情况 | 处理方式 |
|------|---------|
| `runtime.yaml` 不存在 | 立即停止，告知用户文件缺失 |
| `current_requirement` 为空 | 停止，引导用户用 `harness requirement` 创建需求 |
| `stage` 字段缺失或不在已知列表 | 停止，告知 stage 未识别 |
| `conversation_mode: harness` | 锁定当前节点，不得漂移 |

---

### Step 2：读取背景文件

读取以下文件，建立项目和团队上下文：
- `.workflow/tools/index.md`
- `.workflow/context/project/project-overview.md`

---

### Step 3：在角色索引中确认自己的身份

读取 `.workflow/context/index.md` 的"角色索引"章节，根据以下依据确认你的角色：

| 你的身份 | 确认依据 |
|---------|---------|
| **顶级角色（Director）** | 你是主 agent，负责编排整个工作流 |
| **Stage 执行角色** | `runtime.yaml` 中的 `stage` 字段 |
| **辅助角色** | 你被主 agent 或 stage 角色显式召唤（如工具优先硬门禁触发 toolsManager） |

---

### Step 4：加载自己的角色文件

根据 `index.md` 中的角色索引表，找到对应角色文件路径并完整读取：

- **顶级角色** → `.workflow/context/roles/directors/technical-director.md`
- **Stage 角色** → `.workflow/context/roles/{stage}.md`
- **辅助角色** → `.workflow/context/roles/tools-manager.md`

**硬门禁**：角色文件必须完整加载，不允许只读摘要或跳过章节。

---

### Step 5：加载通用规约

**所有角色**（含顶级角色 Director、辅助角色 toolsManager、stage 角色）在加载自己的角色文件前，**必须先加载** `.workflow/context/roles/base-role.md`。`base-role.md` 中定义的通用硬门禁、行为准则、经验沉淀规则和上下文维护规则对所有角色生效。

加载顺序（所有角色）：
```
base-role.md → 你的角色文件
```

### Step 6：stage 角色额外加载 stage-role

如果你的角色是 **stage 执行角色**（requirement-review、planning、executing、testing、acceptance、regression、done）或 **辅助角色**（toolsManager），在加载 `base-role.md` 之后、加载自己的角色文件之前，**必须先加载** `.workflow/context/roles/stage-role.md`。

加载顺序（stage 角色和辅助角色）：
```
base-role.md → stage-role.md → 你的 stage 角色文件
```

`stage-role.md` 中定义的 Session Start 约定、Stage 切换上下文交接约定、经验文件加载规则和流转规则对你生效。

---

### Step 7：按需加载附加上下文

根据你的角色和当前 stage，按需加载以下附加文件：

- **评估文件**（testing / acceptance / regression 阶段）：
  - `evaluation/testing.md`
  - `evaluation/acceptance.md`
  - `evaluation/regression.md`

- **经验文件**（按 `state/experience/index.md` 的规则，加载与当前角色匹配的分类）
- **团队规范**（before-task 时加载 `context/team/development-standards.md`）
- **风险文件**（before-task 时加载 `constraints/risk.md`）
- **流转规则**（判断 stage 推进时加载 `flow/stages.md`）

---

---

### Step 7.5：模型一致性自检（req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet）） / chg-03）

subagent 加载完自己的角色文件后、开始执行实质性任务前，必须核对自身运行 model 与 `.workflow/context/role-model-map.yaml` 中 `roles[{自己的 role}]` 声明值是否一致：

1. 读取 `.workflow/context/role-model-map.yaml`，取 `roles[{role}]` 得到期望 model（未列出则取 `default`）。
2. 若 runtime 支持自省自身 model（如环境变量 / Agent 工具返回值），与期望值比对。
3. **一致** → 在首条输出中简述"本 subagent 运行于 {model}，与 role-model-map.yaml 声明一致"。
4. **不一致** → 立即上报主 agent，在当前 session-memory.md 追加一段"## 模型一致性告警"记录（期望值 / 实际值 / 时间戳），不得静默继续。
5. **无法自省**（runtime 限制）→ 降级：读 briefing 的 `expected_model` 字段（由 harness-manager / technical-director 按 chg-03 协议注入），在首条输出中显式写："本 subagent 未能自检 model 一致性，briefing 期望 = {expected_model}"，并在 session-memory.md 记录一条"未自检"留痕即可，不阻塞。

此节与 `base-role.md` 硬门禁三的"角色自我介绍"同时执行，先做自检再做自我介绍。

---

### Step 7.6：项目级覆盖加载（req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并）+ req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-01（契约层路径迁移-无branch项目级-双轨过渡））

> 溯源：req-51 OQ-2 = A（项目级覆盖全局）/ OQ-3 = A（仅 constraints / experience / tools 三类，不含 roles/）；req-52 OQ-A = D-modified（双轨过渡）。

加载完 Step 7 全局附加上下文后、Step 7.5 模型一致性自检前，所有角色（含顶级角色 Director、辅助角色、stage 角色）**必须**额外按项目级覆盖加载链处理：

#### 项目级承载路径

主路径：`artifacts/project/{constraints,experience,tools}/`（req-52 / chg-01 OQ-A = D-modified，无 branch 维度，跟项目走；详见 `repository-layout.md` §2.1 双轨过渡段）。

#### 加载顺序

| 阶段 | 路径 | 处理方式 |
|------|------|---------|
| 1 | `.workflow/context/constraints/` / `.workflow/context/experience/` / `.workflow/tools/` | 先按 Step 7 全局加载链加载（不变） |
| 2 | `artifacts/project/constraints/` / `experience/` / `tools/` | 后加载项目级版本，**文件级覆盖**全局同名文件 |

#### fallback（req-52 / chg-01 双轨过渡）

- 主路径 `artifacts/project/` 不存在 → fallback 到 legacy `artifacts/{branch}/project/`；命中后 agent 在首条输出追加 `（fallback=artifacts/{branch}/project/）` 提示用户后续 req 将退役 legacy 路径；
- 主路径 + legacy 均不存在 → 静默跳过，不报错（与 task_context_index 回退语义一致）。

#### 覆盖语义（OQ-2 = A）

- **同名文件**（按 basename 匹配，如 `experience/roles/analyst.md`）→ 项目级覆盖全局（项目级生效，全局忽略）；
- **不同名文件** → 两者并存（全局 + 项目级合并）；
- **段落级 merge 不支持**（markdown 无结构化 schema，merge 复杂度高，OQ-2 default-pick 已明确"覆盖而非合并"）。

#### 不参与项目级覆盖的子类（OQ-3 = A）

- `.workflow/context/roles/` 角色规范（项目级化风险高，下次 req 单独评估）；
- `.workflow/context/role-model-map.yaml` 模型映射（影响成本与质量，下游一般不需要改）。

#### 自检（角色加载完成后）

- 在首条输出（与硬门禁三自我介绍并列）追加一句："项目级加载：{命中数 / 0}（路径：artifacts/project/）"，便于用户感知是否生效。

#### Step 7.6.1：索引懒加载（req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-03（索引懒加载-index-md与加载链改造））

> 溯源：req-52 OQ-B = A（YAML frontmatter + Markdown 表 schema）。

加载顺序：

1. **先调 helper**：`_load_project_level_index(root, scope)`（scope ∈ `{constraints, experience-roles, experience-tool, experience-risk, experience-regression, experience-stage}`），拿清单；
2. **按 `when_load` 过滤**：
   - `always` → 立即加载条目；
   - `on-stage:{stage}` → 当前 stage 匹配时才加载；
   - `on-keyword:{kw}` → 当前任务描述含 keyword 时才加载（agent 自判）；
3. **全量 rglob fallback**：当且仅当 `index.md` 不存在时，回退到 Step 7.6 既有 `_merge_project_level_files` 的全量 `rglob("*")` 行为（向后兼容存量项目）；
4. **路径优先级**：`_load_project_level_index` 内部已实现"主路径优先 + legacy fallback"（chg-01 双轨），agent 无需关心；命中 legacy 时 helper 在返回值中标 `source="legacy"`，agent 在首条输出追加 `（fallback=artifacts/{branch}/project/）` 提示。

**自检**（角色加载完成后）：

- 在首条输出（与硬门禁三自我介绍并列）追加一句："项目级索引懒加载：{命中文件数 / 0}（scope={scope}）"，便于用户感知是否生效。

---

### Step 7：开始执行

角色 briefing 加载完成后，严格按角色文件中的 SOP 执行。禁止在加载完成前执行任何实质性操作。

---

## 流程速查图

```
[agent 被唤醒]
    ↓
runtime.yaml ← 必须第一步
    ↓
tools/index.md + project/project-overview.md ← 背景文件
    ↓
context/index.md ← 确认自己的角色
    ↓
base-role.md ← 所有角色必须加载
    ↓
[如果是 stage 角色] → stage-role.md
    ↓
加载自己的角色文件
    ↓
按需加载附加上下文（evaluation、experience、constraints 等）
    ↓
项目级覆盖加载（Step 7.6，artifacts/{branch}/project/）
    ↓
模型一致性自检（Step 7.5）
    ↓
[开始执行]
```

---

## 禁止的行为

- 未读取 `runtime.yaml` 前执行任何操作
- 跳过角色文件中的任何章节
- stage 角色未加载 `base-role.md` 就直接执行
- 不经过 `index.md` 索引确认身份就自行判断角色
