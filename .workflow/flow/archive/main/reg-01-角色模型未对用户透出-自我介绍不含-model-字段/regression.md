# Regression Intake — reg-01（角色模型未对用户透出：自我介绍不含 model 字段）

> 契约 7 首次引用：reg-01（角色模型未对用户透出：自我介绍不含 model 字段）/ req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））/ chg-01（角色-模型映射配置文件落地（.workflow/context/role-model-map.yaml））/ chg-02（context/index.md 角色索引表同步 model 列）/ chg-03（harness-manager.md 派发协议扩展 + role-loading-protocol.md 模型一致性原则）/ chg-04（experience/tool/harness.md 补模型选择依据 + SKILL.md 扫描同步）/ chg-05（端到端自证：executing 阶段派发 executing subagent 用新配置走 Sonnet）。

## 1. Issue Title

角色模型未对用户透出：自我介绍不含 model 字段。

## 2. Reported Concern

用户原话：

> 关于角色使用不同的模型，我怎么知道它在用什么模型呢，介绍的时候可以说明下吗

req-29 刚归档，实现了**后台**的角色↔模型映射闭环（yaml 权威 + index.md 镜像 + 派发协议 4 步 + Step 7.5 一致性自检 + experience 说明）。用户发现一个**用户侧透明度**缺口：每个角色做自我介绍或主 agent 派发 subagent 时，都不透出"正在用的 model"，用户无法直接观察到映射是否生效、某个角色到底跑在 Opus 还是 Sonnet。

## 3. Current Behavior（证据）

自扫描采集，不依赖记忆。

### 3.1 `grep -n "我是" .workflow/context/roles/harness-manager.md`

```
28:- 向用户自我介绍："我是 **harness-manager（命令引导中心）**，接下来我将解析你的命令并协调执行。"
```

仅 1 行，不含 model 字段。

### 3.2 `grep -nE "自我介绍|我是.*角色|Session Start" .workflow/context/roles/*.md .workflow/context/roles/directors/*.md`

命中要点：

- `base-role.md:36-49` — 硬门禁三格式模板 `> 我是 [角色名称]，接下来我将 [任务意图]。`，示例中 **没有** model 字段。
- `stage-role.md:26` — 清单第 3 项引用 base-role 硬门禁三，格式同上，**没有** model 字段。
- `harness-manager.md:28` — 顶层自我介绍模板，**没有** model 字段。
- `directors/technical-director.md:87` — 主 agent 自我介绍模板，**没有** model 字段。
- `planning.md:78` — 是"变更简报.md"对人文档模板里的"变更名 - 一句话自我介绍"字段，与角色自我介绍无关，略。
- `ROLE-TEMPLATE.md:23` — 模板引用硬门禁三，未额外约定 model。
- `requirement-review.md` / `executing.md` / `testing.md` / `acceptance.md` / `done.md` / `tools-manager.md` / `reviewer.md` / `regression.md` — **无** 本角色专属的自我介绍段，均依赖 base-role 硬门禁三的通用模板（也就是说一改 base-role 模板即可覆盖所有 stage 角色）。

### 3.3 `grep -nE "我是.*Subagent.*L[0-9]" .workflow/state/sessions/`

无历史留痕。本会话中 subagent 汇报格式只是 briefing 里的 `你是 Subagent-L{N}（{role}角色）` 模板，并未强制 subagent 在给用户的输出里透出 model。

### 3.4 req-29 的 5 个 change.md / plan.md 是否约定"对用户透出 model"

`grep -rn "自我介绍|我是|用户透|对用户" artifacts/main/archive/requirements/req-29-.../changes/*/change.md 和 plan.md` 结果：

- chg-01（角色-模型映射配置文件落地（.workflow/context/role-model-map.yaml））：只建 yaml，不涉及用户侧输出。
- chg-02（context/index.md 角色索引表同步 model 列）：只同步索引表，不涉及自我介绍。
- chg-03（harness-manager.md 派发协议扩展 + role-loading-protocol.md 模型一致性原则）：只改 briefing 内部字段和 Step 7.5 自检；**唯一**碰到"自我介绍"的地方是 `此节与 base-role.md 硬门禁三的"角色自我介绍"同时执行，先做自检再做自我介绍`，也就是说 req-29 明知存在自我介绍门禁，但**只约束了先做自检**，**没有**要求自我介绍内容里显式透出 model。
- chg-04（experience/tool/harness.md 补模型选择依据 + SKILL.md 扫描同步）：经验沉淀和 skill 扫描，不涉及用户面。
- chg-05（端到端自证：executing 阶段派发 executing subagent 用新配置走 Sonnet）：只要求 subagent 在"自我介绍前先输出"model 自检字符串（Step 7.5 的一致性回显），用于开发者自证；**不**要求每个角色在自我介绍里显式写 model 给用户。

### 3.5 `stage-role.md` / `base-role.md` 的统一自我介绍约定

- `base-role.md` 硬门禁三定义了**全局唯一**的自我介绍格式：`我是 [角色名称]，接下来我将 [任务意图]。`
- `stage-role.md` 公共父类清单第 3 项引用 base-role 硬门禁三，**不重复声明**。
- 所以只要在 base-role 硬门禁三加一个 model 字段，全家桶一网打尽；其次是 harness-manager.md Step 0 + technical-director.md Step 0 + harness-manager.md 3.6 派发段的派发说明文案。

## 4. Expected Outcome

用户期望在角色自我介绍时能看到"我用的是什么 model"，以便直观确认 req-29 的映射生效、并在跨角色观察时知道哪个角色跑在 Opus、哪个跑在 Sonnet。

## 5. Assertion — 是 req-29 的 Scope 盲区，不是 req-29 回归

- req-29 的 AC 围绕"配置权威 / 索引镜像 / 派发协议 / 一致性自检 / 端到端自证"展开，**没有**一条 AC 要求"对用户自我介绍层面透出 model"。
- req-29 归档时状态全绿（288 tests passed，零回归）。
- 用户提出的是一个**新需求**：把后台配置对用户**可观测化**。
- 结论：**真实问题**，但**不是 req-29 的 bug，而是 req-29 的 Scope 边界外的新增用户侧诉求**。适合走新需求 / 新 change 流程，不适合走 `--reject`。

## 6. Next Step

- 已完成独立诊断（见 `analysis.md`）。
- 路由建议见 `decision.md`。
- 由主 agent 与用户确认方案 A/B/C 与路由（--requirement / --change / --reject）。
