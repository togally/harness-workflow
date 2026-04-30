# Requirement

> 溯源：用户原话——"现在有一个问题，部分任务其实没有那么复杂，但是流程过长可能要开发几十分钟，但是其实也就几行代码"

## 1. Title

工作流轻量级通道：trivial 任务（几行代码）走简化流程

## 2. Goal

### 2.1 核心问题

当前 harness workflow 已有 4 类路径：

| 路径 | stages | 适用 |
|------|--------|------|
| `harness requirement` | 7 stage（requirement_review → planning → ready_for_execution → executing → testing → acceptance → done） | 复杂需求 |
| `harness bugfix` | 5 stage（regression → executing → testing → acceptance → done） | 缺陷诊断与修复 |
| `harness suggest --apply` | 3 stage（suggestion → apply → done） | 已入池建议落地 |
| `harness ff` | 跳过中间确认点 | 高确定性场景 |

但用户实测发现：**真正"几行代码"的小改动**（如改一个 string、删一行过期代码、补一个文档错字、调一个常量）走任一现有路径仍需数十分钟，与改动量严重不匹配。`harness suggest --apply` 看似最近，但**强制要求"先入池后 apply"两步**，且语义局限于"建议→需求"转化，不接纳"临时灵感型 trivial 修改"作为入口。

### 2.2 目标

为 trivial 任务（几行代码、单一明确改动、零新增依赖、零 API/契约面变更）开辟一条**显式轻量通道**，**3 stage 内完成全闭环**（define → executing → done），**端到端 ≤ 5 分钟**（不含 agent 思考时长，仅指流程节拍数）。同时设置**自动升级护栏**——一旦 trivial 假设被打破（改动超阈值 / 测试红 / 引入新依赖），强制升级到 bugfix 或 requirement 通道。

### 2.3 实证活样本（uav bugfix-6 落地数据）

> **数据来源**：`/Users/jiazhiwei/claudeProject/uav/.workflow/flow/bugfixes/bugfix-6-事件时间允许负值-人工提报放宽飞行记录校验/`（read-only 实测）；本节为 req-49（trivial 通道）立项的关键证据，量化"流程过长 vs 改动量"的真实落差。

| 维度 | 实测数据 | 备注 |
|------|---------|------|
| Bug 1 真实代码改动 | **1 行** | `Math.max(0L, Duration.between(...).getSeconds())` 单行 fix，纯 trivial |
| Bug 2 真实代码改动 | 几行 | 删除 `getOne` 校验逻辑，需走 bugfix 通道（删验证逻辑 ≠ trivial） |
| 文档工件总量 | **44 KB**（4 文件） | bugfix.md 13 KB + session-memory 18 KB + test-evidence 8.8 KB + acceptance-report 4.5 KB |
| stage 跨度 | **regression → executing → testing → acceptance**（3+ 小时） | 单 bugfix 走完整 5 stage |
| 用户自评 | **～30 分钟** | 实际 6 倍超支 |

**结论**（驱动 req-49 范围 §3 第 2-5 条新动作）：
- 单任务内可能"半 trivial 半非 trivial"（Bug 1 可走 trivial / Bug 2 必走 bugfix），需支持 **chg 级路径选择**而非整任务级；
- 文档工件 44 KB 与 1 行代码不成比例，需 **trivial 文档模板压缩**到 ≤ 1 KB；
- 测试不应要 13 TC + 5 合规扫描，trivial 通道应 **降级到 1 unit test + 全量 pytest**；
- 用户主动选择路径成本高，工具应 **主动识别 trivial 改动量并 hint** 推荐通道。

## 3. Scope

### 3.1 In-Scope（本 req 必须做）

1. **trivial 通道命令底座**：新增 `harness trivial "<title>"` 命令（default-pick D-1 = A），3 stage 序列 `TRIVIAL_SEQUENCE = [trivial_define, executing, done]`，无 testing / acceptance / planning 阶段。
2. **trivial 准入判据（machine-checkable）**（default-pick D-2 = D 组合判据）：
   - 改动量阈值：`git diff --shortstat` ≤ 10 行 + ≤ 2 文件（含新增 / 删除）；
   - 改动类型白名单：string 字面量 / typo / 注释 / 文档（含 `.md`）/ 配置常量 / 删过期代码 / lint 修复；
   - 影响面零增：无新增 import / 无新依赖 / 无 API 签名变化 / 无新增分支逻辑。
3. **trivial_define stage 角色**：复用 `executing` 角色（sonnet）单 stage 走"自定义 + 自实现"，不另设新角色（default-pick D-3 = A，控制角色蔓延）。stage 产物：`.workflow/flow/requirements/{req-id}-{slug}/trivial-define/{trivial-spec.md, session-memory.md}`，含 1 行问题陈述 + 1 行预期 diff 描述 + 改动文件清单。
4. **executing stage（trivial 模式）**：与现有 executing 共用代码路径，但跳过 §4. 测试用例设计要求；执行后强制跑 `harness validate --trivial-guard`（见下条）。
5. **trivial-guard 自动升级护栏**（default-pick D-5 = C 兜底升级）：executing 完成后 CLI 自动跑：
   - `git diff --shortstat` 验证 ≤ 10 行 + ≤ 2 文件；
   - 现有 `pytest` 套件 + `harness validate --contract all` 不破；
   - grep `^import |^from .* import` 与基线对比无新增；
   - 任一不满足 → CLI 输出 `trivial 通道护栏触发：{原因}`，runtime stage 自动切到 `executing`（按 BUGFIX_SEQUENCE 续跑），并 echo `harness regression "<issue>"` 提示。
6. **done stage（trivial 模式精简版）**（default-pick D-6 = A）：复用 `done` 角色但跳过六层回顾，只产 `交付总结.md`（≤ 200 字）+ 经验沉淀检查；artifacts 落位与 sug 直接处理路径同形。
7. **CLI / harness-manager 路由**：
   - `harness trivial "<title>"` 创建 trivial 任务（task_type = "trivial"，与 req / bugfix / sug 并列第四类）；
   - `harness suggest --apply <id>` 增加 `--trivial` flag（default-pick D-4 = C 增强而非新建），允许 sug 池建议作为 trivial 任务执行入口；
   - `harness status` / `harness next` 按 TRIVIAL_SEQUENCE 推进；
   - 自我介绍 / progress 等所有人读取场景遵守硬门禁六。
8. **dogfood 活证**：本 req 自身用 `harness trivial` 做 1 个端到端示例（如改一个 typo），落 `trivial-define/` + 跑通 trivial-guard + done 产 `交付总结.md`，证明通道可用。
9. **chg 级 trivial 路径选择**（§2.3 实证驱动新增）：单 bugfix / req 内允许部分 chg 走 trivial 通道、其他 chg 走标准通道。即同一 bugfix 内，chg-01（Bug 1 单行 fix）可标 `trivial: true`，chg-02（Bug 2 删验证逻辑）走默认 bugfix 路径。落点：`change.md` 加 `trivial: true|false` frontmatter 字段；CLI 在 `harness next` 流转时按 chg 维度 dispatch trivial executing / 标准 executing。
10. **现有命令主动识别 trivial 并 hint**（§2.3 实证驱动新增）：`harness bugfix "<title>"` / `harness requirement "<title>"` 命令入口扫 `git diff --shortstat`；当改动量 < 阈值（≤ 10 行 / ≤ 2 文件 / 改动类型在白名单）时，stdout 输出 hint：
    > 检测到改动量 = 5 行 / 1 文件 / 仅 typo 修复，建议改用 `harness trivial "<title>"` 通道（节省 ～80% 流程节拍）。继续走 bugfix 输入 `--force-full` 抑制本提示。
    Hint 仅 stdout 提示**不阻塞命令**（用户可继续走 bugfix）；用户加 `--force-full` 抑制提示。
11. **trivial 文档模板压缩**（§2.3 实证驱动新增）：参考 sug 池 3 段模板，trivial 通道工件总量上限 ≤ 1.5 KB（对比 bugfix-6 实测 44 KB）：
    - `trivial-spec.md`（替代 bugfix.md）：≤ 1 KB，3 段（**问题 ≤ 200 字 / 修复 ≤ 200 字 / 验证 ≤ 200 字**）；
    - `session-memory.md`：trivial 通道**不强制产出**（default-pick D-8 = A，跳过；保留可选写入但 ≤ 500 字）；
    - `test-evidence.md`：trivial 通道**不强制产出**（pytest stdout 直接 echo 到 done 阶段 `交付总结.md` §测试段，≤ 500 字）；
    - `acceptance-report.md`：trivial 通道**不产出**（done 阶段 `交付总结.md` 单文件兜底，与 sug 直接处理路径同构）。
12. **trivial 测试降级**（§2.3 实证驱动新增）：trivial 通道**硬规则**：
    - 新增 1 个 unit test 断言 fix 行为（必须）；
    - 全量 pytest 不挂（trivial-guard 校验）；
    - **跳过**：13 TC 设计 / 5 合规扫描 / acceptance dimension 评分 / done 六层回顾；
    - 一旦 pytest 红 → trivial-guard 强制升级到 bugfix（已在 In-Scope 第 5 条覆盖，本条仅明确测试降级边界）。

### 3.2 Out-of-Scope（本 req 不做）

- **不替换现有 4 类路径**：requirement / bugfix / suggest --apply / ff 全保留，仅**新增**第 5 类 trivial。
- **不引入"自动检测改动量自动建议跳过 testing"逻辑**（dimension D-4 选项 D 不采用，理由：`executing` 阶段才知道改动量时已经走过 planning，节省不了多少时间，且与 trivial 显式入口语义重叠）。
- **不允许跳过全量 pytest**（dimension D-5 选项 D 不采用，理由：风险过高；保留护栏跑现有套件，只跳"为本次新写测试"这一步）。
- **不重新设计 acceptance 阶段**（acceptance 在现有路径上的精简由独立 req 处理，不并入本 req）。
- **不做 IDE / 编辑器内联触发**，仅命令行入口。

## 4. Acceptance Criteria

| 编号 | 验收点 | 验证方法 |
|------|-------|---------|
| AC-01 | `harness trivial "<title>"` 命令可用，runtime.yaml `task_type` = "trivial"，stage = "trivial_define" | `harness trivial "test"` 后读 runtime.yaml |
| AC-02 | `TRIVIAL_SEQUENCE` 在 `workflow_helpers.py` 定义为 `[trivial_define, executing, done]`，与 ff_auto / `validate_stage` 全链路联通 | grep + pytest |
| AC-03 | 准入判据（≤ 10 行 / ≤ 2 文件 / 改动类型白名单 / 影响面零增）有 helper `validate_trivial_eligibility(repo_path) -> (ok, reason)`，单测覆盖 5 类正例 + 5 类反例 | pytest |
| AC-04 | trivial-guard 在 executing 完成后自动跑：阈值超标 → runtime stage 切回 executing 续走 BUGFIX_SEQUENCE，并 echo 升级提示句 | dogfood TC + pytest 子进程 |
| AC-05 | trivial 通道 done stage 产 ≤ 200 字 `交付总结.md`，落 `artifacts/main/requirements/{req-id}-{slug}/交付总结.md`，跳过六层回顾 | 文件存在 + 字数断言 |
| AC-06 | `harness suggest --apply <sug-id> --trivial` 支持把 sug 池建议作 trivial 任务执行 | dogfood TC |
| AC-07 | dogfood 活证：本 req 自带 1 个 `harness trivial` 端到端样例（如修一处 typo），所有产物落地、护栏通过、`harness validate --contract all` exit 0 | repo diff + commit log |
| AC-08 | 端到端节拍数：从 `harness trivial "<title>"` 到 `harness next`（done 完成）≤ 5 次主 agent ↔ subagent 派发；无 testing / acceptance / planning 派发 | session-memory + usage-log.yaml entries 计数 |
| AC-09 | 硬门禁六（id 带 ≤ 15 字描述）+ 硬门禁七（不列选项 + 报本阶段已结束）+ 契约 7（id+title）在 trivial 通道所有对人输出全覆盖 | grep lint |
| AC-10 | `harness validate --contract artifact-placement` 对 trivial 通道工件落位（机器型 in `.workflow/flow/...trivial-define/`，对人型 in `artifacts/{branch}/requirements/{slug}/`）exit 0 | CLI |
| AC-N1 | **chg 级 trivial 判定可选**：单 bugfix / req 内 chg-NN `change.md` 可独立标 `trivial: true|false` frontmatter；CLI `harness next` 在流转到 executing 时按 chg 维度 dispatch trivial executing / 标准 executing | dogfood TC（混合 bugfix 内 chg-01 trivial / chg-02 标准）+ pytest 子进程 |
| AC-N2 | **现有命令主动识别 trivial**：`harness bugfix` / `harness requirement` 入口扫 git diff，命中阈值时 stdout 输出 hint `建议改用 harness trivial`（含 fix-checklist 类指针）；`--force-full` flag 抑制提示；hint 不阻塞命令 | dogfood TC（构造 1 行改动 → 跑命令 → 断言 stdout 含 hint）+ pytest |
| AC-N3 | **trivial 工件模板存在且压缩**：`trivial-spec.md` ≤ 1 KB（3 段 ≤ 200 字 / 段）；`session-memory.md` 跳过或 ≤ 500 字；`test-evidence.md` 跳过或 ≤ 500 字；`acceptance-report.md` 不产出；scaffold_v2 mirror 同步落地 | wc -c 断言 + grep 文件存在性 + scaffold mirror diff |
| AC-N4 | **trivial 测试降级硬规则**：trivial 通道仅要求 1 个新增 unit test 断言 fix + 全量 pytest 不挂；不强制 13 TC 设计 / 5 合规扫描 / acceptance 评分 / done 六层回顾；pytest 红时 trivial-guard 自动升级到 bugfix | dogfood TC + pytest 子进程 + runtime stage 断言 |

## 5. Split Rules

### 5.1 推荐 chg 拆分（analyst 自主拆分；用户触发"我要自拆"时退化为推荐）

> §2.3 实证驱动重构：原 5 chg 重新组织为 5 chg 新结构，覆盖原 8 条 + 新 4 条 In-Scope；DAG 硬序：chg-01（骨架）→ chg-02（识别）→ chg-03（模板）→ chg-04（测试）→ chg-05（dogfood + reviewer 闭环）。

- **chg-01（trivial 通道命令骨架）**：CLI 入口 `harness trivial "<title>"` + `runtime.yaml` task_type 扩枚举 + `TRIVIAL_SEQUENCE = [trivial_define, executing, done]` 常量 + 3 stage 状态机 + `cli.py choices` 注册 + harness-manager 路由表 + `harness suggest --apply --trivial` flag。**依赖**：无。
- **chg-02（trivial 准入判据 + 自动识别 hint）**：`workflow_helpers.py` 落 `validate_trivial_eligibility(repo_path) -> (ok, reason)` 组合判据（行数 + 文件数 + 改动类型白名单 + 影响面零增）；`harness bugfix` / `harness requirement` 入口扫 git diff，命中阈值时 stdout 输出 hint（含 fix-checklist 类指针，提示 `harness trivial`）；`--force-full` flag 抑制提示。**依赖**：chg-01。
- **chg-03（trivial 工件模板 + chg 级路径选择）**：模板文件（`trivial-spec.md` 3 段 ≤ 1 KB / scaffold_v2 mirror 同步）；CLI 在 trivial 模式下产出工件路径与压缩规则（session-memory / test-evidence 跳过或 ≤ 500 字 / acceptance-report 不产出）；`change.md` 加 `trivial: true|false` frontmatter 字段；CLI `harness next` 在流转到 executing 时按 chg 维度 dispatch trivial executing / 标准 executing（支持单 bugfix 内 chg-01 走 trivial、chg-02 走标准）。**依赖**：chg-02。
- **chg-04（trivial 测试降级 + trivial-guard 兜底护栏）**：trivial 通道硬规则——新增 1 unit test 断言 fix + 全量 pytest 不挂；跳过 13 TC 设计 / 5 合规扫描 / acceptance 评分 / done 六层回顾；CLI 在 executing → done 流转点自动跑 trivial-guard（`git diff --shortstat` + 全量 pytest + `import` 基线对比）；超标 / pytest 红 → runtime stage 自动切回 executing 续走 BUGFIX_SEQUENCE 并 echo 升级提示句；done 阶段产 ≤ 200 字 `交付总结.md`。**依赖**：chg-03。
- **chg-05（dogfood + reviewer 加项 + 契约 lint 闭环）**：用 `harness trivial` 修一处真 typo 跑通端到端（tmpdir fixture + 子进程命令）；扩 `reviewer.md` / `review-checklist.md` 加"trivial 通道边界检查"项（trivial-guard 是否触发 / 工件 KB 限额是否符合 / chg 级 trivial flag 是否一致）；扩 `harness validate --contract all` 覆盖 trivial 通道路径；硬门禁六 / 七 / 契约 7 grep 自检。**依赖**：chg-04。

### 5.2 拆分原则

- 每个 chg 独立可交付（≤ 1 天工作量、单 PR 可合并）；
- 测试先行（chg-01 helper 层先有单测，再走 CLI / 角色）；
- dogfood 收口在最末（chg-05），与 req-41 / req-46 模式一致。

### 5.3 完成时

完成 req-49 后，按 done 阶段标准产 `交付总结.md`（落 `.workflow/flow/repository-layout.md` §2 白名单内）+ 经验沉淀（trivial 通道使用心得 → `context/experience/roles/analyst.md` 或新设 `context/experience/tool/harness-trivial.md`）。

---

## 附录 A：分析师 default-pick 决策清单（requirement_review stage）

| 编号 | 决策点 | 选项 | default-pick | 一句话理由 |
|------|--------|------|--------------|----------|
| D-1 | trivial 通道载体形态 | A. 新命令 `harness trivial`；B. 现有命令加 `--trivial` flag；C. 强化 `harness suggest --apply`；D. auto-trigger | A | 新命令显式语义最清晰，与 4 类既有路径并列；flag 形态会污染既有命令的语义边界 |
| D-2 | trivial 准入判据 | A. 行数阈值；B. 场景类型；C. 影响面；D. 组合判据 | D | 单一阈值都有 corner case；组合判据 machine-checkable + 误判面最小 |
| D-3 | trivial_define stage 是否新设角色 | A. 复用 executing；B. 新设 `trivial-author` 角色 | A | 控制角色蔓延，trivial 任务本就不需要"分析师 / 开发者"分离；executing 单 stage 自定义 + 自实现 |
| D-4 | sug 池建议如何走 trivial | A. 必须先 `--apply` 转 req 再 `harness trivial`；B. sug 直接处理路径已够；C. `harness suggest --apply --trivial` flag 增强 | C | 用户原话痛点是"步骤多"，新增 flag 直通最省心；保留 A/B 不动 |
| D-5 | testing/acceptance 跳过的兜底 | A. 跑 lint 类静默测试；B. 不写新测试但跑全量 pytest；C. 测试红强制升级 bugfix；D. 完全不测 | B + C 组合（trivial-guard 同时含两条） | A 太弱不足以兜底；D 风险过高；B+C 共同保证"trivial 假设破裂时强制升级" |
| D-6 | done 阶段如何精简 | A. 跳六层回顾，仅产 ≤ 200 字交付总结；B. 全量六层回顾；C. 完全跳过 done | A | sug 直接处理路径已有 3 段轻量交付总结先例（req-43 / chg-05），可复用模板；六层回顾对几行代码不成比例 |
| D-7 | 本 req 产出边界 | A. 仅设计文档；B. 设计 + 1 chg 实施；C. 设计 + 完整代码 + dogfood 活证 | C | 与 req-46 / req-41 收口模式一致，非 dogfood 不算真落地 |
| D-8 | trivial 通道 session-memory 是否强制产出 | A. 跳过；B. 强制产出 ≤ 500 字 | A | uav bugfix-6 实证 18 KB session-memory 与 1 行 fix 不成比例；trivial 任务的"决策上下文"已由 trivial-spec.md §修复段承载，session-memory 冗余 |
| D-9 | hint 形态（命令入口主动识别） | A. stdout 提示不阻塞；B. 弹交互问"是否切 trivial"；C. 直接抢占式切到 trivial | A | B 打断硬门禁四同阶段不打断；C 越权剥夺用户选择；A 仅提示符合"工具优先 + 用户决策"原则 |
| D-10 | chg 级 trivial 路径选择载体 | A. `change.md` frontmatter `trivial: true`；B. 文件名前缀 `trivial-chg-NN`；C. 独立 `trivials/` 子目录 | A | frontmatter 是机器可读 + 人可读；B 污染命名；C 与 changes/ 子目录形态分裂 |
| D-11 | 现有 hint 命令清单 | A. 仅 `harness bugfix` + `harness requirement`；B. 加 `harness change`；C. 全 CLI 入口 | A | bugfix / requirement 是用户选择"通道"的关键决策点；change 在 req 内不再涉及通道决策；全 CLI 范围过宽 |

---

## 附录 B：风险与缓解

| 风险 | 级别 | 缓解 |
|------|------|------|
| 用户滥用 trivial 通道做"自以为简单实则复杂"的改动 | 高 | trivial-guard 三道护栏（行数 + 测试 + import 基线）+ 强制升级路径，不依赖人主观判断 |
| trivial 通道与 ff 模式语义重叠 | 中 | trivial 是"减少 stage 数"，ff 是"跳过 stage 内确认"；维度正交，可叠加（`harness trivial --ff`，本 req 不做但不阻塞） |
| 新增第 5 类路径增加 CLI / 角色心智负担 | 中 | 在 `harness install` / `harness status` 输出中加路径选择提示；done 阶段沉淀经验文件指引 |
| trivial-define stage 与 sug 的 suggestion stage 概念重叠 | 低 | 文档明确：suggestion = 建议入池待 triage；trivial_define = 已确定要做的小改动入口 |
