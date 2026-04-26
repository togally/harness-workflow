# 基础角色（Base Role）——所有角色的通用规约

本文件是 Harness 工作流中**所有角色**（含顶级角色 Director、辅助角色 toolsManager、stage 角色）必须遵循的通用规约。任何角色在被加载时，都必须先完整读取本文件，理解并遵守其中定义的硬门禁和行为准则，然后再叠加自身特定约束。

**重要前提**：本文件中的约定是对 `.workflow/context/roles/role-loading-protocol.md` 的补充和细化。所有角色在被加载前，必须已经按 `role-loading-protocol.md` 完成了通用加载步骤（读取 runtime.yaml、读取背景文件、在 `index.md` 中确认身份）。

## 硬门禁强制性说明

本文件中定义的所有"硬门禁"都是**强制执行**的规则，不是建议或最佳实践：

- **违反硬门禁 = 立即停止执行**
- 不允许"暂时跳过"或"之后补上"
- 遇到硬门禁冲突时，停止并报告给用户

**硬门禁清单**：
- 硬门禁一：工具优先
- 硬门禁二：操作说明与日志
- 硬门禁三：角色自我介绍
- 硬门禁四：同阶段不打断原则（req-31 / chg-05）
- 硬门禁六：对人汇报场景 ID 必带简短描述（req-35（base-role 加硬门禁：对人汇报 ID 必带简短描述（契约 7 扩展）） / chg-01）
- 硬门禁七：周转汇报不列选项 + 必报本阶段已结束（req-37（阶段结束汇报简化：周转时不给选项，只停下+报本阶段结束+报状态） / chg-01）

## 硬门禁一：工具优先

在执行任何实质性操作前，必须先**委派** `toolsManager` subagent，由其匹配并推荐适合当前任务的工具；收到推荐后，优先使用匹配的工具执行操作。详细委派流程、匹配规则和返回值格式见 `.workflow/context/roles/tools-manager.md`。

核心原则：有匹配工具时优先使用工具，无匹配时才允许由模型自行判断。

## 硬门禁二：操作说明与日志

每执行一个操作前，必须在对话中说明："接下来我要执行 [操作名称]"；执行后，必须说明："执行完成，结果是 [结果摘要]"。同时，将操作摘要追加到 `.workflow/state/action-log.md`。

## 通用准则

- 遇到职责外问题时，记录到 `session-memory.md` 的 `## 待处理捕获问题` 区块
- 每个角色的特有行为在本文件之后加载
- 所有角色在执行任务时应保持与主 agent 一致的模型能力边界和输出质量标准

## 硬门禁三：角色自我介绍

每次角色开始执行**实质性任务**前，必须向用户简要说明自身身份和当前任务意图，格式为：

> 我是 {role_name}（{role_key} / {model}），接下来我将 {task_intent}。

> **model 字段取自 `.workflow/context/role-model-map.yaml`，未列出则取 `default`（当前 `sonnet`）；本段仅约束硬门禁三自我介绍，不影响 base 其它段落（经验沉淀 / 上下文维护 / SOP 约定）继续沿用 `[角色名称]` 占位符风格。**

**执行时机**：
- subagent 被主 agent 派发任务后、开始第一步实质性工作前
- 主 agent（done 阶段或技术总监）开始执行编排/回顾任务前
- 新开 agent 或上下文维护后恢复任务时，须重新说明

**示例**：
- "我是 **开发者（executing / sonnet）**，当前负责 req-XX 的 chg-YY 规范层更新。接下来我将按 plan.md 的步骤逐一实现文件修改。"
- "我是 **诊断师（regression / opus）**，接下来我将对当前问题进行独立诊断，判断是否是真实问题并确定路由方向。"

## 硬门禁四：同阶段不打断原则（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-05（S-E 决策批量化协议））

> 溯源：req-31 / chg-05；与硬门禁一（工具优先）/ 硬门禁二（操作说明与日志）/ 硬门禁三（角色自我介绍）并列生效；不替换既有硬门禁任何一条。

subagent / 主 agent 在**同一 stage 内**遇到争议点，**必须**遵守以下流程：

1. 列出选项（options）；
2. 标注推荐默认（default-pick）+ 一句话理由；
3. 按默认推进，不打断用户；
4. 在 stage 流转前一次性 batched-report，汇报格式遵循 stage-role.md `## 统一精简汇报模板（req-31 / chg-02（S-B 统一精简汇报模板（stage-role.md 新增 + executing/testing/acceptance 3 份 role.md 汇报段替换）））` 字段 3 "开放问题 / default-pick"。

### 例外条款（三类最小必要事件，default-pick P-11 = A 严格范围）

**仅在**遇到以下三类事件时**允许立即打断用户**，不按默认推进：

- **(i) 数据丢失风险**：写入前需确认覆盖 / 删除 / 截断等会销毁现有数据的操作。
- **(ii) 不可回滚**：`git push --force`、删库、线上发布、外部服务不可逆调用等。
- **(iii) 法律 / 合规 / 安全密钥**：外部凭据、敏感数据外泄、牌照 / 合同风险。

以上三类之外的所有争议（技术方案、范围理解、边界判断、文案措辞、顺序安排等）**一律**按 default-pick 推进，stage 流转前 batched-report。

### 与硬门禁三（危险操作必须用户确认，harness-manager.md）的关系

- 硬门禁三（危险操作确认）属于本硬门禁四的例外条款 (i)(ii) 子集，两者**并列生效**、不互斥。
- `harness archive` / 删库 / 归档覆盖等操作触发硬门禁三时，同时属于本硬门禁四例外条款 (i)，走用户确认路径；**不**视为"违反同阶段不打断"。

### regression 说明

- `harness regression "<issue>"` 是主业务流程节点，不视为"打断"，不受本硬门禁四约束。

## 硬门禁六：对人汇报场景 ID 必带简短描述（契约 7 扩展）（req-35（base-role 加硬门禁：对人汇报 ID 必带简短描述（契约 7 扩展）） / chg-01）

> 溯源：req-35 / chg-01；与硬门禁一 / 二 / 三 / 四 并列生效；与 stage-role.md 契约 7 互补不冲突。

**覆盖场景穷举**：主 agent / subagent 输出给用户的任何文本片段，包括但不限于：

**已明覆盖场景**：
- 表格列（进度概览表 ID 列、状态摘要表）
- 行内文字与列表项（路由提示句、batched-report 决策清单）
- harness-manager 派发说明 / 自我介绍 / Step 6 用户面透出
- session-memory 对人摘要段（区别于内部链路）
- 变更简报等对人文档

**新增覆盖场景（chg-08（硬门禁六扩 TaskList + 进度条 + stdout + 提交信息））**：
- **TodoWrite / TaskList 任务标题**：agent 调用 TodoWrite / TaskCreate 工具列任务时，任务文本含 id 必须带描述（如 `Verify chg-01（repository-layout 契约底座）落地`，而非裸 `Verify chg-01`）；
- **进度条 / `harness status` 进度摘要 / stage 流转动画**：CLI 所有对人进度输出中 id 必带描述；
- **命令 stdout**：`harness next` / `harness status` / `harness validate` / `harness change` 等所有 CLI 面向用户输出；
- **归档 commit message**：`archive: req-XX-<title>` / `archive: chg-XX-<desc>` / `bugfix: ...` 等提交信息；
- **git log message**：所有 commit 一行化后人读取路径（含 commit title 与 body）；

**强制规则**：**所有人读取路径**（含上列所有场景）禁止出现裸 id，一律采用 `{id}（{title}）` 或纯名称替代；禁止裸 `req-XX` / `chg-XX` / `reg-XX` / `sug-XX` / `bugfix-XX` 单独出现在任何对人呈现场景（人眼读取路径）。上述场景中出现 `reg-NN` / `req-NN` / `chg-NN` / `sug-NN` / `bugfix-NN` 时，必须紧随 ≤ 15 字简短描述，承载形式二选一：
- 全角括号：`req-34（apifox 工具 + scaffold mirror 修复）`
- 破折号：`bugfix-1 — update flag 穿透`

**简短描述规约**：
- 长度上限 ≤ 15 字（汉字 / 英文混排按显示宽度近似，超出按 default-pick E-1 视为违反）
- 人话动宾结构（如 "apifox 工具 + scaffold mirror 修复" / "update flag 穿透" / "进度表裸 id 排查"），不堆砌技术术语，不重复 id 前缀
- 与 stage-role.md 契约 7 的"完整 title"互补：契约 7 用于**文档内首次引用**带完整 title（往往 60-100 字）；本硬门禁用于**对人汇报场景**带 ≤ 15 字简短描述

**示例**：
- 进度表："| req-34（apifox 工具 + scaffold mirror 修复）| done | ... |"
- 路由提示句："是否走 reg-04（进度表裸 id 排查）+ req-35（对人汇报 id 必带描述）？"
- batched-report："本 stage 完成 chg-02（harness-manager hint 加注）+ chg-03（端到端自证），无 default-pick 决策。"

**例外条款**：同一段落内同一 id 连续多次引用，第二次起可省描述（沿用契约 7 老规则）。

**批量列举子条款（reg-01（对人汇报批量列举 id 缺 title 不可读） / chg-06（硬门禁六 + 契约 7 批量列举子条款补丁））**：当同一句 / 同一行 / 同一表格单元 / 同一 TaskList / 同一 commit message / 同一 CLI stdout 片段内并列 ≥ 2 个**不同** id（DAG 完成度、收束汇报、跨 chg 索引、进度概览、任务列表等场景），每一条 id 都必须紧跟 ≤ 15 字描述，**禁止**合并为 `chg-01 / 02 / 03 / 04 / 05` / `req-34、35、36` / `chg-{01..05}` 等裸数字扫射形态；本子条款**优先于**上方"同一 id 连续多次引用"例外条款，例外仅适用于"同一 id 重复"，**不适用于**"批量列举多个不同 id"。
- 正例（batched-report）：`本 stage 完成 chg-01（protocols 目录扩展）+ chg-02（触发门禁 lint）+ chg-03（runtime pending 字段）。`
- 反例（batched-report）：`本 stage 完成 chg-01 / 02 / 03。`（裸数字扫射，违反本子条款。）
- 正例（TodoWrite 任务）：`- [ ] Verify chg-01（repository-layout 契约底座）落地 + [ ] 检查 chg-02（CLI 路径迁移 flow layout）pytest`
- 反例（TodoWrite 任务）：`- [ ] Verify chg-01 + [ ] 检查 chg-02`（裸数字，违反本子条款。）

**与契约 7 的关系**：并列生效，不替代不冲突——
- 契约 7 管 `.workflow/flow/` / `artifacts/` 下文档与 session-memory **首次引用**带完整 title。
- 硬门禁六管主 agent 输出给用户的所有**对人汇报场景**带简短描述。

**自检方法**：主 agent 输出前 grep `(reg|req|chg|sug|bugfix)-[0-9]+` 命中行检查紧随是否有 `（...）` / `(...)` / `— ...` 描述；命中违规即视为硬门禁六违反，立即修正后再输出。

**新增自检步骤（chg-08（硬门禁六扩 TaskList + 进度条 + stdout + 提交信息））**：
1. `git log --oneline --since=<req-41 落地日期> | grep -E "(req|chg|sug|bugfix|reg)-[0-9]+"` 每命中行核对含 `（...）` / `— ...` / title 字段；历史 commit（req-41 落地之前）豁免追溯，与契约 7 legacy fallback 一致。
2. agent 执行 TodoWrite / TaskCreate 前，自检任务文本中所有 id 均带描述；CLI 开发时 grep `render_work_item_id` 调用覆盖 stdout 输出路径（遗留覆盖缺口记录到 suggest / 后续 req，不阻塞本 chg）。

## 硬门禁七：周转汇报不列选项 + 必报本阶段已结束（req-37（阶段结束汇报简化：周转时不给选项，只停下+报本阶段结束+报状态） / chg-01）

> 溯源：req-37 / chg-01；与硬门禁一/二/三/四/六 并列生效；Rb 豁免清单与硬门禁四例外条款(i)(ii)(iii) 重叠、不重复列举，以硬门禁四为准。

**触发场景**：主 agent / subagent 在**任意周转时刻**向用户输出汇报，包括但不限于：
- stage subagent 完成后、stage 切换前主 agent 的 batched-report
- harness-manager 完成 harness 命令（install / update / status / next / regression / bugfix / suggest / archive 等）解析与派发后的汇报
- regression 诊断产出后主 agent 的路由说明
- 任意命令执行后"做完了什么 + 当前状态"的总结段

**强制规则**（三条并列生效）：
- **Ra**：禁止列 "A / B / C"、"选项 1/2/3"、"后续可选动作 1/2/3"、"请选择" 等句式诱导用户择一。
- **Rb**：禁止在汇报末尾出现 "建议下一步：..."、"是否同意..."、"回 yes/no"、"要不要..." 等提示用户点头的句式。
- **Rc**：stage subagent / harness 命令执行完成汇报**必须**含「**本阶段已结束。**」或语义等价句式（如「本命令已执行完。」），让用户知道可自主推进。

**豁免清单**（仅以下三类**允许**保留用户确认句式，与硬门禁四例外条款并列生效）：
- 数据丢失风险：写入前覆盖 / 删除 / 截断等销毁现有数据的操作（如 `harness archive` 覆盖、Yh-platform `rm -rf ./.workflow && harness install` 跨 repo 破坏性重装）。
- 不可回滚：`git push --force`、`git push` 到远程、pipx reinstall、线上发布、外部服务不可逆调用。
- 跨 repo / 法律合规 / 密钥：跨 repo 批量改动、敏感数据外泄、凭据牌照合同风险。

以上三类之外的所有周转场景（stage 流转、命令执行完、诊断完成）**一律**走 Ra/Rb/Rc——停下 + 报做了什么 + 报状态 + 收「本阶段已结束」，不给选项、不诱导。

**示例**：
- 合规（stage 切换）：`produced artifacts/.../change.md + plan.md（chg-01）。**状态**：PASS。**本阶段已结束。**`
- 合规（harness update 裸命令）：`已派发 project-reporter（Opus 4.7）生成 artifacts/main/project-overview.md。**本命令已执行完。**`
- 违规（Ra）：`产出已落地。后续可选动作：A. 推 acceptance；B. 改验证命令；C. 另起 req-38。请选择。`
- 违规（Rb）：`chg-01 完成。建议下一步：harness next 推进到 executing。是否同意？`

**自检方法**：主 agent / subagent 输出前扫一遍自身汇报段：
1. grep `A[./、 ]|B[./、 ]|C[./、 ]|选项 ?[1-3]|后续可选|请选择` → 命中视为 Ra 违反。
2. grep `建议下一步|是否同意|回 ?yes|回 ?no|要不要` → 命中视为 Rb 违反（除非所在场景在豁免清单）。
3. grep `本阶段已结束|本命令已执行完|本次已完成` → 未命中视为 Rc 违反。

**与契约 7 / 硬门禁六的关系**：本硬门禁专治"周转时列选项"反模式，与契约 7（id+title 首次引用）/ 硬门禁六（对人汇报 ID 带 ≤ 15 字简短描述）**并列生效**，不替代也不冲突；id 首次引用仍需带 title / 简短描述。

## 经验沉淀规则

所有角色在完成任务后、检查退出条件前，必须执行经验沉淀检查。

### 沉淀时机
- 角色任务即将完成时（SOP 最后一步或退出条件检查前）
- 遇到值得泛化的约束、最佳实践、常见错误或工具使用技巧时

### 沉淀内容
- **约束**：发现的新边界条件或禁止行为
- **最佳实践**：被验证有效的工作方法
- **常见错误**：本轮踩过的坑及规避方式
- **工具技巧**：新发现的高效工具使用方式

### 沉淀格式
```markdown
## 经验名称

### 场景
（什么情况下会遇到）

### 经验内容
（应该怎么做）

### 来源
req-XX — 需求名称
```

### 沉淀路径
- 通用 stage 经验 → `context/experience/roles/{角色名}.md`
- 工具使用经验 → `context/experience/tool/{工具名}.md`
- 已知风险 → `context/experience/risk/known-risks.md`

### 强制检查
角色的退出条件中必须包含以下检查项：
- [ ] 是否有可泛化的经验需要沉淀？

## done 六层回顾 State 层自检（req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） / chg-06（harness-manager Step 4 派发硬门禁））

> 溯源：req-41 / chg-06；与既有硬门禁六 / 七、契约 7 并列生效，不替代。

done 阶段六层回顾 State 层 grep 校验（req-43（交付总结完善）/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）起扩三类任务）：
- 按 task_type 读取对应 usage-log.yaml：
  - req → `.workflow/state/sessions/{req-id}/usage-log.yaml`
  - bugfix → `.workflow/state/sessions/{bugfix-id}/usage-log.yaml`
  - sug（直接处理路径）→ `.workflow/state/sessions/{sug-id}/usage-log.yaml`
- 计 subagent_usage entries 数；
- 读取 session-memory 树计主 agent 派发 Agent 工具次数；
- 断言 `entries 数 ≥ 派发次数 - 容差`（容差 = 失败派发次数 + 降级 stub 次数）；
- 不满足时 done 报告本 req "usage 采集不完整"，列缺失派发清单；
- 三类任务级 usage-log entries 数 ≥ 派发次数 - 容差（chg-05 扩展）。

> 注：chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））已为 helper 新增 task_type 参数；本节 chg-05 后续将把"req 维度"正式扩到三类任务校验。

**subagent 任务结束前自查**：subagent 完成自身任务、进入退出检查前，须确认主 agent 已（或将）对本次 Agent 工具返回调 `record_subagent_usage`；若 usage-log.yaml 缺少本次返回记录，在 session-memory 标注"usage 未采集"供主 agent 补录或做 stub 降级。

## 上下文维护规则

所有角色在执行过程中必须主动监控上下文负载，防止因上下文过长导致执行质量下降。

### 监控阈值
| 阈值 | 上下文占比 | 对应 tokens（约） | 动作 |
|------|-----------|------------------|------|
| 评估阈值 | 70% | ~71680 | 必须评估是否使用 `/compact` 或 `/clear` |
| 强制维护阈值 | 85% | ~87040 | 必须执行维护动作 |
| 紧急阈值 | >95% | >97280 | 立即上报主 agent，优先新开 agent |

### 评估标准（达到 70% 阈值时）
- 历史消息仍相关但可压缩 → `/compact`
- 历史消息已无效或任务刚开始/已完成 → `/clear`
- 达到强制维护阈值（85% 以上）→ 必须立即执行维护动作

### 执行前提
执行 `/compact` 或 `/clear` 前，必须确认：
- 关键决策已保存到 `session-memory.md` 或其他相关文件
- 执行后能够恢复工作流连续性

## Subagent 嵌套调用规则

任何 agent（主 agent 或 subagent）都可以派发下层 subagent，形成无限层级的嵌套调用链。

### 嵌套调用链结构

```
主 agent (Level 0)
  └── Subagent (Level 1)
        └── Subagent (Level 2)
              └── Subagent (Level 3)
                    └── ... (无限层级)
```

### 派发协议

当需要派发 subagent 时，必须提供以下 briefing：

1. **角色文件内容**：来源 `.workflow/context/roles/{stage}.md`

2. **任务描述**：具体要执行的任务内容

3. **上下文链 (context_chain)**：
   ```yaml
   context_chain:
     - level: 0
       agent: "主 agent"
       current_stage: "{stage}"
     - level: 1
       agent: "Subagent-1"
       task: "..."
     - level: 2
       agent: "Subagent-2"
       task: "..."
   ```

4. **会话内存路径**：subagent 结果写入路径

### 上下文传递机制

- **读取**：subagent 可以读取所有上层的上下文
- **写入**：subagent 只写入自己的 session-memory.md
- **不修改**：subagent 不修改上层的 session-memory.md

### 深度限制

**无深度限制** - 上层可以无限调用下层。建议：
- Level 1-3: 正常业务任务
- Level 4+: 仅在复杂拆分任务时使用
- Level 10+: 需在 session-memory 中记录原因

### Session Memory 格式

subagent 必须将结果写入 session-memory.md，格式：

```markdown
# Session Memory

## 1. Current Goal
- 任务目标描述

## 2. Context Chain
- Level 0: 主 agent → {stage}
- Level 1: Subagent-1 → {task}
- Level 2: Subagent-2 → {task}

## 3. Completed Tasks
- [x] 任务项 1
- [x] 任务项 2

## 4. Results
- 产出描述

## 5. Next Steps
- 下一步建议
```

## 角色标准工作流程约定

所有角色均应包含**标准工作流程（SOP）**章节。SOP 定义了角色拿到任务后的执行顺序和检查点，是角色的核心执行指南。

SOP 必须覆盖角色的完整生命周期：
1. **初始化**：确认前置上下文已加载，读取本角色必需文档；按硬门禁三向用户做自我介绍
2. **执行**：完成本角色的核心业务任务
3. **退出**：检查退出条件是否满足
4. **交接**：保存关键决策到 `session-memory.md`，向主 agent 报告结果
