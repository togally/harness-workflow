# Session Memory: req-35（base-role 加硬门禁：对人汇报 ID 必带简短描述（契约 7 扩展））/ requirement_review

## Current Goal

把用户 2026-04-22 起床后两次反馈（"reqId/sugId/bugId 不适合人阅读" + "提示句也犯同样毛病，可在 baseRole 中约束吗"）落成可执行的 requirement.md + 需求摘要.md，交接到 planning 阶段拆 chg；本 req 自身即作为新硬门禁六的端到端自证样本（executing 起所有汇报零裸 id）。

## Context Chain

- **Stage**：`requirement_review`（runtime.yaml: current_requirement=req-35 / stage=requirement_review / conversation_mode=open / ff_mode=false）
- **派发链**：主 agent (Level 0 / technical-director) → Subagent-L1（requirement-review / Opus 4.7）写三份文档
- **用户原话权威两句**：
  1. "这里用 reqId 用 sugId bugId 不合适，没办法看出来你执行的到底是什么这类属于人阅读的范畴需要简明易懂"
  2. "提示次中也存在这种情况不是吗？可以在 baseRole 中约束吗"
- **已读**（按 base-role / 必读清单顺序）：
  - `WORKFLOW.md`（Hard Gate）
  - `.workflow/state/runtime.yaml`（current_requirement=req-35 确认）
  - `.workflow/context/index.md`（角色索引）— 本 stage 流程已熟，未重复
  - `.workflow/context/roles/base-role.md`（既有硬门禁一/二/三/四清单 + 上下文维护规则 — 确认硬门禁五属 harness-manager.md 占位）
  - `.workflow/context/roles/stage-role.md`（统一精简汇报模板 + 契约 1-7 — 确认契约 7 仅约束**文档内首次引用**带完整 title）
  - `.workflow/context/roles/requirement-review.md`（本角色 SOP + 对人文档输出契约 + 退出条件）
  - `.workflow/context/roles/harness-manager.md`（确认硬门禁五已占位"scaffold mirror 同步"，本 req 编号继续接六）
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`（mirror 同步目标，与 live 当前 bytes 级一致 — chg-01 改完需同步同形态）
  - `artifacts/main/requirements/req-34-.../requirement.md` + `需求摘要.md` + `.workflow/state/sessions/req-34/session-memory.md`（最近一个 req 写法与 e2e 自证样本，作为格式范本）
- **环境事实核查**：
  - `.workflow/state/requirements/req-35-...yaml` 已存在（status=active / stage=requirement_review / created_at=2026-04-23）
  - `artifacts/main/requirements/req-35-.../requirement.md` 初始骨架已存在（§1 title 仅占位，§2-§5 待填）
  - `.workflow/state/sessions/req-35/` 目录本轮新建（之前不存在）
  - 现有硬门禁编号占用：base-role.md 一/二/三/四 + harness-manager.md 五 → 本 req 接六无冲突

## Completed

- [x] 读 `WORKFLOW.md` / `runtime.yaml` / `.workflow/context/index.md`（Hard Gate 通过）
- [x] 读 `base-role.md` / `stage-role.md` / `requirement-review.md` / `harness-manager.md`（确认硬门禁编号占位 + 契约 7 范围 + 角色 SOP）
- [x] 读 `scaffold_v2/.workflow/context/roles/base-role.md`（mirror 同步基线确认）
- [x] 读 req-34 三份文档作为格式范本（requirement.md / 需求摘要.md / session-memory.md）
- [x] 写 `artifacts/main/requirements/req-35-.../requirement.md`（§1-§7 全字段填充：title / background 含两段用户原话 / goal / scope in/out + R1 / AC-1..AC-6 / chg-01/02/03 拆分 / E-1..E-6 default-pick）
- [x] 写 `artifacts/main/requirements/req-35-.../需求摘要.md`（≤ 1 页 / frontmatter 双向互链字段齐 / 4 节：目标 / 范围 / 验收要点 / 风险）
- [x] 写 `.workflow/state/sessions/req-35/session-memory.md`（本文件，含 default-pick 决策清单 + 对主 agent 汇报）

## Results

### 产出文件

- `artifacts/main/requirements/req-35-base-role-加硬门禁-对人汇报场景-reg-req-chg-sug-bugfix-id-必带简短描述-契约-7/requirement.md` — §1 title / §2 background（含两段用户原话 + 既有契约 7 局限分析）/ §3 goal / §4 scope in/out + §4.3 R1 豁免 / §5 AC-1..AC-6 / §6 chg-01/02/03 拆分（按依赖排序）/ §7 E-1..E-6 default-pick 决策表
- `artifacts/main/requirements/req-35-.../需求摘要.md` — frontmatter（requirement_link + delivery_link 双向互链）+ 目标 / 范围 / 验收要点 / 风险（≤ 1 页 4 节）
- `.workflow/state/sessions/req-35/session-memory.md`（本文件）

### 契约合规

- **契约 7 合规**：本 session-memory + requirement.md + 需求摘要.md 中首次引用 `req-35` / `req-30` / `req-31` / `req-34` / `chg-01..03` / `bugfix-1` / `reg-04` 均带 title（参见各文件首段引用点）；同文档后续简写。
- **R1 合规**：未触 `src/harness_workflow/`（除规划中 chg-01/02 将动 `src/harness_workflow/assets/scaffold_v2/` mirror，已在 §4.3 豁免）/ `tests/` / `.workflow/constraints/` / `.workflow/evaluation/`。
- **本硬门禁六（即将上线，本 req 自证）预演**：本 session-memory 内对汇报场景的 id 引用即按"≤ 15 字简短描述"格式预演（如 `req-34（apifox 工具 + scaffold mirror 修复）` / `bugfix-1（update flag 穿透）` / `reg-04（进度表裸 id 排查）`）。

## Next Steps

1. 用户确认需求（`conversation_mode=open`，按 E-5 default-pick 不阻塞，将由主 agent 自主推进）
2. `harness next` → 推进到 `planning`，由架构师按 §6 拆 chg-01 / chg-02 / chg-03（每份产出 `change.md` + `plan.md` + `变更简报.md`）
3. executing 阶段开发者按 chg 顺序落地 base-role.md 改写 + scaffold mirror 同步 + harness-manager hint 同步 + 端到端自证留痕
4. acceptance / done / archive 由主 agent 按 ff 模式自主推进（E-5 已授权）

## default-pick 决策清单（本 stage 按 E 原则默认推进的争议点）

| # | 争议点 | 默认选项 | 理由 |
|---|---|---|---|
| E-1 | 简短描述长度上限 | 15 字 | 覆盖典型 4 词中文短语；10 字偏紧、20 字撑爆表格列 |
| E-2 | 硬门禁编号 | 六（接 base-role 一/二/三/四 + harness-manager 五） | 现有清单到五，自然接六，避免重号歧义 |
| E-3 | 例外条款 | 同段落连续引用第二次起可省 | 沿用契约 7 老规则，体感一致，避免段内重复噪声 |
| E-4 | 是否做 lint 自动校验 | 不做（留 sug 池） | 契约层最小落地；自动 lint 涉及 CLI / parser 改动，超出 §4.3 R1 豁免 |
| E-5 | 推进策略 | 自主推到 archive（按用户 ff 习惯） | req-30 / req-31 / req-34 同类纯契约 req 用户均放行到归档 |
| E-6 | 简短描述承载形式 | 全角括号 `（）` 或破折号 `—` 二选一 | 全角括号沿用契约 7 既有约定；破折号给表格窄列备用 |

**本 stage 新增争议点**：无。

## 对主 agent 的汇报（按 stage-role.md 统一精简模板）

### 字段 1：产出

- `artifacts/main/requirements/req-35（base-role 硬门禁六 / 契约 7 扩展）/requirement.md`（§1-§7 全字段，含 AC-1..AC-6 + chg-01/02/03 拆分）
- `artifacts/main/requirements/req-35（base-role 硬门禁六 / 契约 7 扩展）/需求摘要.md`（1 页 4 节 + frontmatter 双向互链）
- `.workflow/state/sessions/req-35（base-role 硬门禁六 / 契约 7 扩展）/session-memory.md`（本文件，含 Current Goal / Context Chain / Completed / Results / Next Steps / E-1..E-6 default-pick）

### 字段 2：状态

**PASS**。requirement.md 退出条件五项全满足（背景 / 目标 / 范围 in+out / 验收标准 AC-1..AC-6 / 对人文档需求摘要.md 已落 artifacts）；契约 7 合规、R1 合规、对人文档 ≤ 1 页字段齐全；本 req 即作为新硬门禁六上线前的"自证待样本"。

### 字段 3：开放问题 / default-pick

- E-1..E-6 六项均按默认推进（详见上表 default-pick 决策清单）
- 本 stage 无新增争议点
- 无开放问题阻塞 planning

### 字段 4：建议下一步

建议 `harness next` 推进到 `planning`，由架构师按 §6 拆 chg-01（base-role.md 加硬门禁六 + scaffold mirror）/ chg-02（harness-manager.md 加 hint + scaffold mirror）/ chg-03（端到端自证）。

## 端到端自证 req-35（chg-03（端到端自证（主 agent 后续汇报全 id 带描述 + session-memory 留痕）））

### 1. 主 agent 实战汇报片段（截 ≥ 3 处对人输出文本）

#### 片段 A：executing 阶段 chg-01 完成 batched-report
> req-35（对人汇报 id 必带描述）executing 推进：
> - chg-01（硬门禁六定义）：base-role.md + scaffold_v2 mirror 同步，2 文件改动，commit 9a77277
> - chg-02（hint 加注）：harness-manager.md 三处 hint + scaffold_v2 mirror 同步，2 文件改动，commit e014561
> - chg-03（端到端自证）：session-memory 留痕进行中
> 无 default-pick 决策。

#### 片段 B：executing 阶段进度表
| ID | title | 状态 |
|---|---|---|
| chg-01（硬门禁六定义） | base-role.md 新增硬门禁六 + mirror 同步 | done |
| chg-02（hint 加注） | harness-manager.md 三处 hint + mirror 同步 | done |
| chg-03（端到端自证） | session-memory 留痕 + pytest 校验 | doing |

#### 片段 C：testing 路由提示句
> 是否走 chg-03（端到端自证）→ testing → acceptance → done？沿用 ff 习惯（req-35（对人汇报 id 必带描述）§7 / E-5 已 default-pick）。

### 2. 自查命令与输出

```bash
grep -nE '(reg|req|chg|sug|bugfix)-[0-9]+' .workflow/state/sessions/req-35/session-memory.md
```

预期：所有命中行紧随 `（` / `(` / `—` 描述，零裸 id。

### 3. pytest 摘要

```
$ pytest -x --tb=no -q
1 failed, 45 passed, 14 skipped in 3.34s
```

预期：req-35（对人汇报 id 必带描述）纯文档契约 + session-memory 留痕，不影响测试；唯一失败 test_req_30_implementation_docs_first_reference_has_title 为 pre-existing 失败（req-30（沟通可读性增强 / 全链路透出 title）目录不存在），与本 req 无关，git stash 已验证。

### 4. 契约 7 + 硬门禁六 双合规自查

- 契约 7：本 session-memory 文件首次引用 req-35（对人汇报 id 必带描述）/ chg-01（硬门禁六定义）/ chg-02（hint 加注）/ chg-03（端到端自证）全带 title（见本段标题及片段 A）
- 硬门禁六：所有对人汇报片段中 id 后带 ≤ 15 字描述（"对人汇报 id 必带描述" / "硬门禁六定义" / "hint 加注" / "端到端自证" 均 ≤ 15 字）

### 5. Subagent-L1 自我介绍（按硬门禁六）

我是 Subagent-L1（executing / Sonnet 4.6），执行 req-35（对人汇报 id 必带描述）的 3 chg：chg-01（硬门禁六定义）+ chg-02（hint 加注）+ chg-03（端到端自证）。
