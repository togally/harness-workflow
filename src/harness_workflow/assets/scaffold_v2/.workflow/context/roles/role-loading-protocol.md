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
