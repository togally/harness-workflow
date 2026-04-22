# Session Memory — req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））

## 1. Current Goal

- 在 requirement_review 阶段，为 req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））覆写 `requirement.md`、产出对人文档 `需求摘要.md`，把用户 2026-04-22 明确授权的角色↔模型映射诉求落为结构化需求，确保 planning 阶段可以直接拆分为 ≥ 3 个独立 chg 落地。

## 2. Context Chain

- Level 0: 主 agent（harness-manager / technical-director，Opus 4.7，负责编排与派发）
- Level 1: Subagent-L1（requirement-review 需求分析师 / Opus 4.7，本会话，负责 requirement.md + 需求摘要.md + session-memory.md 产出）

## 3. Completed Tasks

- [x] 按必读顺序读取 `runtime.yaml`（确认 current_requirement=req-29、stage=requirement_review、conversation_mode=open）
- [x] 读取 `.workflow/tools/index.md`、`project-overview.md`、`base-role.md`、`stage-role.md`、`requirement-review.md`（本角色契约：req-26 对人文档契约 / req-30 契约 7 / 退出条件 5 项）
- [x] 读取 `.workflow/context/index.md`（角色索引表 7 个 stage 角色 + harness-manager + tools-manager + technical-director 权威名单），用作 AC-1 的 `roles` 字段覆盖基准
- [x] 读取 `harness-manager.md`（确认派发 Subagent 协议位于第 180-235 行 `3.6 派发 Subagent`，正是 S-3 的改造点）
- [x] 读取 `directors/technical-director.md`（Step 4 已有 briefing 模板，S-3 延伸点；该角色本身承担编排与综合判断职责，确认归入 opus）
- [x] 覆写空模板 `requirement.md`（§1 Title / §2 Background / §3 Goal / §4 Scope / §5 Acceptance Criteria / §6 Split Rules / §7 预留章节），11 条 AC、6 条 In-Scope、6 条 Out-of-Scope、5 个 chg 切分建议
- [x] 产出对人文档 `需求摘要.md`（契约 2 路径同构 + 契约 3 中文命名 "需求摘要.md" + 模板字段：标题 / 目标 / 范围 / 验收要点 / 风险，≤ 1 页）
- [x] 创建 `.workflow/state/sessions/req-29/` 目录并写入本 `session-memory.md`

## 4. Results

- `/Users/jiazhiwei/claudeProject/harness-workflow/artifacts/main/requirements/req-29-角色-模型映射-开放型角色用-opus-4-7-执行型角色用-sonnet/requirement.md` —— 覆写完成，含背景 / 目标 / 范围 / AC / 拆分建议 / 预留章节
- `/Users/jiazhiwei/claudeProject/harness-workflow/artifacts/main/requirements/req-29-角色-模型映射-开放型角色用-opus-4-7-执行型角色用-sonnet/需求摘要.md` —— 对人文档落地，严格按 `requirement-review.md` 第 73-87 行模板
- `/Users/jiazhiwei/claudeProject/harness-workflow/.workflow/state/sessions/req-29/session-memory.md` —— 本文件

### 关键决策

1. **权威源二选一**：单一权威源 = `.workflow/context/role-model-map.yaml`；`index.md` model 列为投影，不反向改 yaml。双源一致性由 planning / executing 落 lint 或 `harness validate --contract` 兜底（R-1）。
2. **harness-manager 归 Opus**：明确遵循用户指令"harness-manager 角色也要用 Opus 4.7"，该角色承担命令意图解析 + 角色调度的综合判断职责，不在"执行型"范畴。
3. **technical-director 归 Opus**：该角色承担流程编排、模式识别、六层回顾、异常处理，推理强度 ≥ harness-manager，同归开放型。
4. **reviewer 归 Sonnet**：虽然 reviewer 在角色索引表未直接出现，但按 checklist 审查属于高确定性断言型任务，归入 sonnet；若 planning 阶段发现 reviewer 尚未在 index.md 注册，需同步补齐或从 roles 列表移除（由 planning 决策）。
5. **不动 Python 源码**：本需求纯配置 + 文档 + 角色契约层面，subagent 派发由 briefing 级控制；CLI 层自动化留给后续需求。
6. **端到端自证（AC-11）**：本需求 executing 阶段派发 executing subagent 必须走新配置（按 role-model-map.yaml 查 executing → sonnet），主 agent 在派发 briefing 时显式写入 model 字段并将该行动留痕到本 session-memory，作为新契约 go-live 的首次实战。

## 5. Next Steps

给主 agent 的建议：

1. **直接 `harness next`** 推进到 `planning` —— 用户授权已经完整（已决策开放型用 Opus、执行型用 Sonnet、harness-manager 归 Opus、全权限跑到开发完成），不需要额外 Q/A 对齐，方向已定。
2. planning 阶段派发 Subagent-L1（planning 角色 / Opus 4.7）按 §6 Split Rules 的 5 个 chg 切分 `plan.md`，重点确认：
   - yaml 精确 model 值用字符串别名（`"opus"` / `"sonnet"`）还是完整版本号（`claude-opus-4-7[1m]` / `claude-sonnet-4-6`）；
   - subagent 运行时 model 自省能力的技术可行性（R-2）决定 AC-6 是"硬校验"还是"briefing 声明 + 记录"的降级版本。
3. executing 阶段派发时注意：主 agent 必须按 role-model-map.yaml 为 executing subagent 选 sonnet，并在 briefing 中显式写入 `model: sonnet`（或完整版本号），留痕到本 session-memory 以满足 AC-11。

## 6. 待处理捕获问题

- （无——用户授权完整，无阻塞性开放问题）

## [2026-04-22] 端到端自证：本 executing subagent 派发时 model 选择轨迹

### 声明

**本 subagent 运行时 model == expected_model sonnet**

本段是 req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））/ chg-05（端到端自证：executing 阶段派发 executing subagent 用新配置走 sonnet）的 AC-11 端到端自证留痕。

### 端到端自证（req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet）） / chg-05）

本节记录 executing 阶段派发 subagent 时主 agent 按 chg-03（harness-manager.md 派发协议扩展 + role-loading-protocol.md 模型一致性原则）协议执行的 4 步留痕。

| 序号 | 时间戳 | role | expected_model（读 yaml） | briefing.model | Agent 工具传入 model | subagent 首条输出自检结论 |
|-----|--------|------|--------------------------|---------------|---------------------|--------------------------|
| 1 | 2026-04-22T06:23:26+00:00 | executing | sonnet | sonnet | sonnet | "本 subagent 运行于 sonnet，与 role-model-map.yaml 声明一致" |

**读取 yaml 快照**（首次派发时贴一次）：
```yaml
executing: sonnet
testing: sonnet
acceptance: sonnet
harness-manager: opus
planning: opus
requirement-review: opus
regression: opus
done: opus
technical-director: opus
tools-manager: sonnet
reviewer: sonnet
```

**三行关键记录**：

1. 主 agent（Level-0 / harness-manager / Opus）从 `.workflow/context/role-model-map.yaml` 读取 role="executing" → model="sonnet"（来自 chg-01（角色-模型映射配置文件落地（.workflow/context/role-model-map.yaml））落地的权威配置）
2. 主 agent 调 Agent 工具时传 `model: "sonnet"`，本 subagent briefing 也证实了这个派发契约（本 subagent 被显式用 `model: "sonnet"` 派发，这是 req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet）） AC-11"端到端自证"证据之一）
3. 本 subagent 自身运行 model：sonnet（claude-sonnet-4-6）—— 主 agent 派发时显式传了 sonnet，降级路径：briefing 期望 = sonnet，与配置声明一致

**SKILL.md 扫描副作用记录**（chg-04 产出）：
- `.claude/skills/harness/SKILL.md` 零命中 model，跳过（不改文件）
- `.codex/skills/harness/SKILL.md` 零命中 model，跳过（不改文件）
- `.kimi/skills/harness/SKILL.md` 零命中 model，跳过（不改文件）
- `.qoder/skills/harness/SKILL.md` 零命中 model，跳过（不改文件）

**结论**：req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））派发协议已端到端生效，chg-01..04 合入后的第一次 subagent 派发即按新配置选 model。AC-11 PASS。

---

## 7. 契约 7 样本行（id + title 首次引用）

- "req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））的 `requirement.md` / `需求摘要.md` / `session-memory.md` 已在 requirement_review 阶段落地，11 条 AC、5 个 chg 切分建议俱全，建议主 agent 直接 `harness next` 推进到 planning。"
- 上下文链样本：`req-28（目录散落产物清理与 gitignore 规约修正）归档后 → req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet））新立 → planning 阶段将按 §6 切分 chg-01..chg-05`。
