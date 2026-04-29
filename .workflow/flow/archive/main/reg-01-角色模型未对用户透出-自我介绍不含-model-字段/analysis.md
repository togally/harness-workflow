# Regression Analysis — reg-01（角色模型未对用户透出：自我介绍不含 model 字段）

## 1. Problem Assessment

**真实问题**，但**不是 req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））的回归**。

- req-29 已归档、全绿，它做的是"后台映射闭环"：yaml 权威 / index.md 镜像 / 派发协议 4 步 / Step 7.5 一致性自检 / experience 说明 / 端到端自证。
- 用户诉求是"对用户透出 model"，即**用户视角的可观测面**。
- req-29 的 5 个 change.md / plan.md 均未覆盖该用户面（chg-03（harness-manager.md 派发协议扩展 + role-loading-protocol.md 模型一致性原则）唯一触碰"自我介绍"的一处是要求"先自检再自我介绍"，不是"把 model 写到自我介绍里给用户看"；chg-05（端到端自证：executing 阶段派发 executing subagent 用新配置走 Sonnet）只要求 subagent 自检回显，属开发者自证非用户透出）。

→ 属于 req-29 的 **Scope 盲区**（合理未覆盖，不是 bug），需要补一个增量工作项。

## 2. Evidence（汇总，详见 `regression.md` §3）

- `base-role.md:36-49` 硬门禁三模板 `我是 [角色名称]，接下来我将 [任务意图]。` — 全局唯一自我介绍模板，不含 model 字段。
- `stage-role.md:26` 清单第 3 项引用 base-role 硬门禁三，不重复声明。
- `harness-manager.md:28` Step 0 自我介绍，不含 model。
- `harness-manager.md` 3.6 派发协议的 briefing 里有 `model`，但 briefing 是 agent ↔ agent 的内部消息，**不在**主 agent 给用户的派发说明文案中显式体现。
- `directors/technical-director.md:87` Step 0 自我介绍，不含 model。
- 其它 stage 角色（requirement-review / executing / testing / acceptance / regression / done / tools-manager / reviewer）无专属自我介绍段，统一依赖 base-role 硬门禁三。
- req-29 chg-03 明确要求"先做自检再做自我介绍"，但**未**扩展自我介绍内容；chg-05 只要求 subagent 自检回显（session-memory 留痕，非对用户稳定可见面）。

## 3. 根因

req-29 的设计把 model 信息锁在 2 个面：

1. **配置面**：`.workflow/context/role-model-map.yaml`（权威） + `index.md` 的 model 列（镜像）；
2. **dispatch 面**：briefing JSON 的 `model` 字段 + Step 7.5 subagent 自检回显。

**缺失的是第 3 个面——用户面**：

- 主 agent 派发 subagent 时，**给用户的派发说明文字**里没有显式透出 `{subagent_role, model}`。
- subagent 自我介绍（硬门禁三）的**固定格式**不强制含 model 字段。
- 用户日常观察路径（读主 agent 派发文案 + 读 subagent 自我介绍）全程见不到 model。

于是 req-29 "后台绿、用户看不见"。

## 4. 修复方案候选

### 方案 A（轻）— 仅扩展自我介绍模板

**改动面**：

- `base-role.md` 硬门禁三：格式从 `我是 [角色名称]，接下来我将 [任务意图]。` 升级为 `我是 [角色名称]（role-key / model，如 executing / sonnet），接下来我将 [任务意图]。`
- `stage-role.md` 清单第 3 项同步说明（不重复模板）。
- `harness-manager.md:28` Step 0 / `directors/technical-director.md:87` Step 0 的自我介绍实例同步加 model。
- `ROLE-TEMPLATE.md` 硬门禁三章节示例同步。
- `stage-role.md` Session Start 约定段可点一句子 agent 自我介绍模板 `我是 Subagent-L{N}（{role} / {model}）`。

**代价**：1~2 个契约文件 + 3 个 role 头 + 1 个模板。小。

**局限**：

- 主 agent 在给用户的派发说明文案（如 "接下来我派发 executing subagent 完成 chg-05…"）里**仍然看不到 model**，用户只在 subagent 真正开讲时才补上一行，反馈延迟；
- 嵌套派发（Level 2+）场景下用户仍难以预判每层 model。

### 方案 B（中）— A + 派发说明文案同步透出 model 【推荐】

在方案 A 基础上扩展派发面：

**额外改动**：

- `harness-manager.md` 3.6 派发协议步骤 3 之后追加显式规则："**在给用户的派发说明文案里**首次提到 subagent 时必须形如 `派发 {subagent_role}（{model}）执行 {task_short}`。例如：`派发 executing（sonnet）执行 chg-05 的端到端自证`。"
- `technical-director.md` Step 4 briefing 段同步声明"对用户说明文案必须透出 model"。

**收益**：

- 用户在派发**前**即可见 model，预判 Opus/Sonnet 分布；
- 补在 req-29 Scope 边界**外侧**，与 req-29 chg-03 派发协议 Step 2.5、Step 7.5 一致性自检、chg-05 自证回显**互补不冲突**。

**代价**：A + harness-manager.md 追加 1 条协议语 + technical-director.md 同步 1 行。仍属小 req 级别（2-3 契约 + 3-4 role/模板同步）。

### 方案 C（重）— B + 把"model 自我标识"升为契约硬门禁 + lint

在方案 B 基础上：

**额外改动**：

- `stage-role.md` 对人文档契约新增"契约 8：model 自我标识"，规定所有自我介绍、派发说明、subagent 完成汇报都必须含 `role-key / model` 形如 `executing / sonnet`。
- 新增 `harness validate --contract 8` 校验（grep 所有 `我是 **...**` 开头行核对是否含 `（... / ...）`）。
- done 阶段六层回顾加一条 lint 命令。

**代价**：B + 1 个契约条款 + 1 个 CLI 校验实现 + done checklist 更新 + 大量历史文案扫描。与 req-29 chg-03 的 Step 7.5 一致性自检**职责交叠**，有边界模糊风险。

## 5. 推荐：方案 B

- 方案 A 太单薄（主 agent 派发时用户看不到 model）。
- 方案 C 与 req-29 Step 7.5 一致性自检职责交叠、实现开销大（需 CLI 新校验）、带 breaking change 风险。
- 方案 B 刚好补在 req-29 Scope 边界**外**的用户面一小片空白，粒度 2-3 个契约文件 + 3-4 个 role 同步，一轮 harness 小 req 可收口，不与既有资产冲突。

## 6. 影响范围（按方案 B 估算）

**契约 / 规约层**：

- `.workflow/context/roles/base-role.md`（硬门禁三模板 + 示例）
- `.workflow/context/roles/stage-role.md`（公共父类清单第 3 项说明同步；Session Start 约定段可点一句子 agent 自我介绍模板）
- `.workflow/context/roles/ROLE-TEMPLATE.md`（硬门禁三章节示例同步）

**主 agent / 派发面**：

- `.workflow/context/roles/harness-manager.md` Step 0 自我介绍实例 + 3.6 派发协议追加"派发说明文案透出 model"规则
- `.workflow/context/roles/directors/technical-director.md` Step 0 自我介绍实例 + Step 4 briefing 模板说明

**stage / 辅助角色**：

- 以下 role 文件若含显式自我介绍段则同步更新实例；若无则不动（继承 base-role 硬门禁三新模板即可）：
  - `requirement-review.md` / `planning.md` / `executing.md` / `testing.md` / `acceptance.md` / `regression.md` / `done.md` / `tools-manager.md` / `reviewer.md`
- 经查只有 `planning.md:78` 是"变更简报"对人文档字段非角色自我介绍，不需动；其它 stage role 没有专属自我介绍段。

**实测体感**（本次对话就是 Subagent-L1 实例）：

- 我作为 Subagent-L1 regression 诊断师，按硬门禁三做自我介绍时只会写"我是诊断师"，确实没透出"我跑在 Opus 4.7"，正是用户反馈的体感。

## 7. 与 req-29 资产的兼容性

- **不覆盖**：Step 7.5 一致性自检保留（agent 内部自检回显）；派发协议 Step 2.5 保留（briefing 字段）。
- **新增面**：自我介绍模板 + 派发说明文案，是两个新增的**用户可见面**。
- **contract 7**（id + title 硬门禁）不受影响，model 字段与 id/title 独立。

## 8. Discussion Outcome / Recommended Action

由主 agent 向用户确认两个决策点：

1. 方案 A/B/C 取哪个？（诊断师推荐 B）
2. 路由走 `--requirement`（新开 req）还是 `--change`（挂到已归档 req-29 重开）？（诊断师推荐 `--requirement`，理由见 `decision.md`）
