# Regression Diagnosis — bugfix-5（同角色跨 stage 自动续跑硬门禁）

## 一、现象

### 1.1 用户原话（一字不差引用）

> 1.sendMessage是什么工具？使用的话为什么不去查询
> 2.我记得需求和plan合并了吧为什么中间还停顿了

> 不不应该是只针对这一个流程，而是角色所包含的所有state都需要自动跑

> 3 因为我觉得state其实可以复用不是吗

第 1 条次要（汇报证据不到位，sendMessage 工具实际不存在于本环境，应改用 ToolSearch / Agent 工具调用查询）；第 2、3 条是主诉，限定本 bugfix 的修复范围。

### 1.2 实测案例

本会话 req-43（交付总结完善） 的 `requirement_review → planning` 流转点，主 agent（harness-manager）在 analyst subagent 完成 requirement.md 产出后，对用户输出形如「全部同意 default-pick？同意 → 我跑 next 进 planning」的话术，把"是否进入 planning"作为决策点暴露给用户拍板。该流转点契约层规定为**默认静默自动推进**。

## 二、预期

契约层规约（三处原文行号锚定）：

- `.workflow/context/roles/stage-role.md:34-43`（`#### stage 流转点豁免子条款（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））`）：
  > `requirement_review → planning` 流转点**默认静默**：analyst 自主推进 chg 拆分，不邀用户对"是否进入 planning"作拍板决策（default-pick 直接按 HM-1 = A，harness-manager §3.6.1）；

- `.workflow/context/roles/directors/technical-director.md:163-169`（`#### 6.2 requirement_review → planning 自动静默推进（req-40）`）：
  > analyst 在 requirement_review 完成 requirement.md 产出并取得用户对需求内容的拍板后，technical-director **不再邀请用户对"是否进入 planning"作决策**；technical-director 直接更新 `runtime.yaml` stage → planning，由 analyst 在同一会话续跑变更拆分（default-pick HM-1 = A，详见 harness-manager §3.6.1）；

- `.workflow/context/roles/harness-manager.md:339-344`（`#### 3.6.1 req_review / planning 统一派发 analyst（req-40）`）：
  > **default-pick HM-1 = A**：requirement_review PASS 后，technical-director **默认让 analyst 在同一会话续跑 planning 任务**（不新开 subagent 会话），以保持上下文连贯；退化路径 B（两次派发 analyst）保留作 fallback，当上下文达到 70% 阈值需 /compact 时使用。

**契约本意**：同一角色覆盖的相邻 stage（当前仅 analyst 覆盖 `requirement_review + planning` 一例），中间不暴露"是否进 {下一 stage}"决策点；用户只在角色边界（如 `planning → ready_for_execution` 由 analyst 出会前 batched-report 一次）看一次拍板。

## 三、根因（分两层 + 一句根本）

### L1 表象层

主 agent（harness-manager / technical-director 主体角色）在 `requirement_review → planning` 流转点输出"是否进入 planning"形话术，违反 stage-role.md:39 / technical-director.md:165-166 / harness-manager.md:342 三处契约；**话术违反契约 = 表象**。

### L2 中层

契约只在 role md 文档里以自然语言形式存在，无任何代码 / lint / CLI 强制：

- `.workflow/flow/stages.md`：`requirement_review` 与 `planning` 仍是两个独立 stage 定义（行 53-65），中间隔一次 `harness next`；契约层"同会话续跑"无 stages.md 反向标注。
- `src/harness_workflow/workflow_helpers.py:121`：`WORKFLOW_SEQUENCE = ["requirement_review", "planning", "ready_for_execution", "executing", "testing", "acceptance", "done"]` —— 序列里两个独立条目，无"同角色覆盖关系"元数据。
- `src/harness_workflow/workflow_helpers.py:6800-6895`（`workflow_next` 函数）：每次 `harness next` 仅 `idx + 1`（行 6849: `next_stage = sequence[idx + 1]`），**没有"同角色跨 stage 自动连跳"逻辑**。
- 没有 `harness validate` 子命令的话术 lint 规则，能够拦截 agent 输出里"是否进入 {下一 stage}"句式（即使 agent 触犯也无门禁）。
- 主 agent 提到的 `sendMessage`（"同会话续跑"工具）在本环境不存在；real fallback 是 stage-role.md §3.6.1 的"退化路径 B（两次派发 analyst）"——而两次派发的天然语义就是"中间停一次"，给"是否进 planning"决策点留出口。

### 根本根因（一句话）

**角色→stage 的"覆盖关系"无单一权威源**——`.workflow/context/index.md` 表格、`.workflow/flow/stages.md`、各 role md（analyst.md / executing.md / regression.md 等）三处分散、自然语言式记录，CLI（workflow_next）无法读、reviewer / harness validate 无法 lint，契约自然变成只能靠 agent 自觉。

## 四、影响面

- **当前发作**：仅 analyst 角色覆盖的 `requirement_review → planning` 一例（req-40 角色合并后唯一同角色跨 stage 场景），每次该流转都可能复发。
- **未来扩面**：若按用户方向继续合并（如 testing+acceptance 由同一角色承载、executing+testing 合并等），任何同角色覆盖 ≥ 2 stage 的场景都会复发同一类问题；用户已明确指示"不应该是只针对这一个流程，而是角色所包含的所有state都需要自动跑"，规则**必须通用化**，不能写死 `requirement_review → planning` 单一特例。
- **回归风险**：主 agent 模型版本切换 / prompt 微调 / 上下文压缩后，仅靠角色文档自然语言的契约极易回归（无代码门禁兜底）。

## 五、判断 + 路由

### 5.1 判断

**真实问题（confirmed）**：契约层与实现层失配，不是 agent 临时失误也不是误判。三处契约文档（stage-role / technical-director / harness-manager）已明文规定，但实现层（stages.md / workflow_helpers.py / harness validate）无对应支撑，必须从底层修复。

### 5.2 路由结论

- **路由方向**：bugfix 流程，下一 stage = **executing**。
- **修复方案落位**：已写入 `bugfix.md` §修复方案（5 个修复点 + 4 用例验证清单）。
- **不需人工额外输入**：诊断证据齐全，修复方案契约层 + 实现层 + 文档同步 + scaffold mirror 同步五点闭环；`required-inputs.md` 保持空模板。

## 六、需要人工提供的信息

无（详见 required-inputs.md 模板，无需额外补充）。

---

## §根因再深化（acceptance 后 scope 扩展）

> 触发时间：2026-04-25T20:18+00:00（acceptance 阶段判 PASS-with-followup 后用户即时反馈）。本节为 regression stage **二次进入**追加，不重做前五段诊断结构，仅扩根因覆盖面 + 加修复点 6 + 滚回 executing。

### 7.1 触发（用户原话，一字不差）

> acceptance→done这一步应该也是自动的吧

**上下文**：bugfix-5（同角色跨 stage 自动续跑硬门禁）走完 regression → executing → testing → acceptance（PASS-with-followup）后，用户对原诊断的"根因覆盖面"提出质疑——指出原修复仅覆盖"同角色"特例，但 `acceptance → done`（不同角色，acceptance verdict = PASS 已定路由）这种"无用户决策点"的流转**也应当自动跳**，原诊断遗漏了这一类。

### 7.2 根因再深化

**原 L2 中层根因表述**（§三 L2 中层）：
> 契约只在 role md 文档里以自然语言形式存在，无任何代码 / lint / CLI 强制；workflow_next 仅 `idx + 1`，**没有"同角色跨 stage 自动连跳"逻辑**。

**判定**：**正确但不完整**（partial-correct）。"同角色跨 stage 自动连跳"只是**充分条件**之一，不是**必要条件**。

**真 L2（修订版）**：**任何"无用户决策点"的 stage 转换都没有代码强制**——同角色只是"无用户决策"的一种常见情形，但不是唯一情形。真正应该建模的不是"角色边界"而是"**用户决策点边界**"；角色边界是用户决策点的常见**位置**，但不是唯一位置。

**充分性 / 必要性矩阵**（穷举四象限）：

| | 同角色 | 不同角色 |
|---|---|---|
| **无用户决策**（应自动） | analyst.requirement_review → planning ✓<br>（已被原修复覆盖） | acceptance → done（verdict=PASS 已定路由）✗<br>acceptance → regression（verdict=FAIL 已定路由）✗<br>regression → testing（diagnosis 已定路由）✗<br>**（被原修复漏掉，acceptance 后才暴露）** |
| **有用户决策**（保留 gate） | （当前无此例） | planning → ready_for_execution（用户对需求 + 拆分拍板）✓<br>ready_for_execution → executing（需 `--execute` 显式确认）✓<br>**（保留显式 gate，原修复已正确处理）** |

- **左上**：原修复"同角色 while 循环"**已正确覆盖**。
- **右上**：**原修复漏掉的真根因扩展**——所有 verdict-driven 路由（acceptance / regression 的 confirm/reject/route-to-X 决策结果）都应自动，因为路由决定本身已由 verdict 字段拍板，用户无新决策点。
- **右下**：原修复**已正确保留**显式 gate（`--execute` flag、planning batched-report 等待）。
- **左上 / 右下**对角线已闭环；**右上**为本次 scope 扩展目标。

### 7.3 影响面再评估

- **当前 scope 覆盖**（原 5 修复点已落）：analyst 跨 requirement_review + planning 自动连跳。
- **本次扩展覆盖**：
  - `acceptance → done`（verdict = PASS 后自动跳到 done，触发 done 阶段六层回顾）。
  - `acceptance → regression`（verdict = FAIL 后自动跳到 regression，由诊断师接管）。
  - `regression → testing`（diagnosis.md 路由 = 实现/测试问题，自动跳 testing）。
  - `regression → requirement_review`（diagnosis.md 路由 = 需求/设计问题，自动跳 requirement_review）。
  - `testing → acceptance`（如果 testing 内部已确定 PASS verdict，无用户决策，自动跳 acceptance）—— 视 testing 是否产出 verdict 字段而定，default-pick D-6 = A 暂不自动跳，因 testing 完成态 ≠ verdict 已写入；若后续 testing 也产出明确 verdict，归为本类自动跳。
- **保留显式 gate**（不动）：
  - `ready_for_execution → executing`（需 `harness next --execute`）；
  - `planning → ready_for_execution`（analyst 出会前 batched-report 等待用户拍板需求 + 拆分）；
  - `requirement_review → planning`（同角色，已由原修复点 2 覆盖）。
- **回归风险**：若错把"用户决策点"也归为自动跳，会跳过用户拍板 → 数据丢失风险。**缓解**：本次扩展严格按"verdict 已写入 / 路由已定 / 终局"三类正向白名单，未列入的 stage 出口默认保留用户决策语义。

### 7.4 判断

**真实根因扩展（confirmed）**——不是新 bug，是原诊断范围不够：

- 原诊断 L2 表述 "**同角色**跨 stage 流转无代码强制" 只覆盖了用户决策点边界的**一个充分条件**（角色边界 = 决策点的常见位置）；
- 真正应该建模的边界是 "**用户决策点边界**"——角色边界与之大量重合但非等价；
- `acceptance → done` 不同角色但同样无用户决策点（verdict = PASS 已定路由），属于真根因覆盖但原诊断遗漏；
- 用户对此类反例的洞察是对的，原 5 修复点不能覆盖此类，必须**追加修复点 6**做 verdict-driven 自动跳。

### 7.5 路由决定

- **滚回 executing 阶段**（不另起 bugfix），由 executing 实现新增修复点 6；
- testing / acceptance 需要重过（量小，主要验新点不破坏旧点 + 新增用例 G/H/I）；
- 修复点 6 详细方案见 `bugfix.md` §修复方案末尾"修复点 6（verdict-driven 自动跳）"段。
- 不需人工额外输入；required-inputs.md 保持空模板。

### 7.6 default-pick 决策清单（scope 扩展段）

| 编号 | 决策点 | 选项 | 默认 = | 理由 |
|------|--------|------|--------|------|
| D-6 | testing → acceptance 是否纳入自动跳 | A. 暂不（testing 完成态 ≠ verdict 已写入） / B. 纳入 | **A** | 当前 testing 完成态语义模糊，verdict 字段未必落盘；保守起见暂不自动跳，待后续 req 把 testing verdict 字段化后再扩 |
| D-7 | stage_policies 容器选型 | A. 内嵌 role-model-map.yaml 顶层字段 / B. 拆出 stage-policy.yaml | **A** | 与 D-1 = A 同源——单一权威源 / 紧凑 / 一次加载 / 不增加文件；scaffold mirror 同步路径不变 |
| D-8 | exit_decision 取值集合 | A. {user, auto, explicit, verdict, terminal} / B. 二元 {auto, manual} | **A** | 区分 auto（自决）/ verdict（路由已定）/ terminal（终局）/ explicit（显式 gate）/ user（用户拍板），语义明确，便于将来扩展；二元粒度不够 |
| D-9 | acceptance verdict 字段读取来源 | A. acceptance-report.md frontmatter / B. checklist.md 结论段正则 | **A** | frontmatter 字段化、可机读，不依赖正则；与既有 acceptance 模板对齐（如已存在 verdict 字段）；fallback：未命中时退化到正则匹配"PASS / FAIL"关键词 |

无需上报用户的开放问题，全部按默认推进。executing 实施时若发现 acceptance / testing / regression 的 verdict 字段未落盘到 frontmatter，default-pick D-9 = A 的 fallback 路径（正则关键词匹配）作为兜底。

