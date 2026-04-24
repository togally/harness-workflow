# Session Memory — req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）

## 1. Current Goal

把 req-34（新增 api-document-upload 工具）落地的单次 degrade 引导，升级为**触发门禁 + MCP pre-check 协议 + 存量项目同步**三合一闭环。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus） → requirement_review 阶段
- Level 1: requirement-review subagent（opus） → 今日仅 seed，不展开完整澄清

## 3. 模型自检留痕（降级）

- 期望 model = `opus`（按 `.workflow/context/role-model-map.yaml` roles.requirement-review）
- 本 subagent 未能自省自身 model 一致性，按 role-loading-protocol 降级规则留痕；自我介绍中已显式声明。

## 4. 今日做了什么（为什么 seed 而非完整澄清）

- 用户今晚下线，明日继续 requirement-review；今日目标：**把已达成的共识忠实落入 requirement.md + session-memory，不丢上下文**。
- 已完成：
  - [x] 填充 `artifacts/main/requirements/req-38-.../requirement.md` §2 Goal / §3 Scope / §4 Acceptance Criteria；§1 Title 保持原样；§5 Split Rules 保留模板文字（拆分由 planning 决定）。
  - [x] 新建 `.workflow/state/sessions/req-38/` 目录与本 session-memory.md。
- **未做**（按 briefing 禁止项）：
  - [ ] 未展开 AC 细化问答（留给明日）；
  - [ ] 未派发下层 subagent；
  - [ ] 未推进 stage，未跑任何 `harness *` 命令；
  - [ ] 未修改 requirement.md 与 session-memory.md 以外的项目文件。

## 5. 今日达成的共识摘要（对齐 requirement.md §2-4）

### 5.1 动机 / 问题现场

- 现版 `api-document-upload.md`（req-34（新增 api-document-upload 工具）/ chg-01（protocols 目录 + catalog 单行引用））在 `mcp__apifox_*` 未注册时仅做"打印引导 + 返回 degraded"的**单次 degrade**，缺闭环。
- req-02（湖南 UAV MQTT 接入）executing 阶段暴露："用户说'帮我上传接口文档'时主 agent 绕过 tools-manager 直接给 A/B/C 通用选项"——关键词登记 ≠ 触发闭环。

### 5.2 三合一 scope（缺一即不完整）

- **Scope-1 触发识别硬门禁**：在 `harness-manager.md` §3.5.1 附近新增一节（参照 project-reporter 召唤模板），强制命中触发词时召唤 tools-manager；触发词单一权威源 = `keywords.yaml`。
- **Scope-2 MCP pre-check 协议**：4 阶段状态机（探测 / 注册引导 / 恢复 / 归属校验），**落地方案 B** —— 新建 `.workflow/tools/protocols/mcp-precheck.md`；方案 A（放 catalog/ 加后缀）**已否决**（保持 catalog 一文件一工具纯度）。`api-document-upload.md` 每个 Provider section 前置检查改单行引用 + 参数槽。
- **Scope-3 存量项目同步**：通过 `harness install` scaffold_v2 mirror 契约（req-36（harness install 同步契约完整性修复））propagate 到存量项目；硬门禁五保护面扩展涵盖 `protocols/`。

### 5.3 default-pick 决策清单（本 stage 内）

- **DP-1**：pre-check 协议落位方式 = 方案 B（新建 `protocols/` 子目录）。理由：保持 catalog "一文件一工具" 纯度，protocols 语义独立。**来源：今日用户已确认，不再重开。**
- **DP-2**：触发词单一权威源 = `keywords.yaml`，`harness-manager.md` 镜像列表靠 lint 防漂移。理由：避免两处漂移，single source of truth。**来源：今日用户已确认。**

## 6. 明日接续提示（优先级从高到低）

明日 requirement-review 接续时，**先做以下 TODO**：

1. **TODO-1（优先）**：敲定 `project-profile.md` 字段形态 —— 单 provider（`apifox_project_id`）vs 多 provider map（`mcp_project_ids: { apifox: ..., swagger: ... }`）。决定影响 AC-7 归属校验条款的具体写法。
2. **TODO-2**：敲定 `runtime.yaml` 是否新增 `stage_pending_user_action` 状态表达"暂停到重启"；如新增，要确定对 `harness next` / `harness status` 的行为（next 是否报错 / status 如何展示）。
3. **TODO-3**：敲定硬门禁五适用范围清单扩展 + scaffold_v2 mirror 对应结构；查 req-36 的 scaffold_v2 契约现状，明确 `protocols/` 如何声明。
4. **TODO-4**：敲定触发词 lint 实现方式 —— harness CLI 子命令（如 `harness validate --contract triggers`）？reviewer script？或 grep 脚本。
5. **TODO-5**：敲定可插拔 provider 的 pre-check 参数槽位是否写入 `catalog/_template.md`，强约束后续 provider catalog 条目。

TODO 推进完毕后：

- 细化 §4 AC（当前 AC-1 ~ AC-10 是"最小判定"版，需按 TODO 答案落实可量化条款 / 成功指标）；
- 把 §5 Split Rules 保留模板文字原样（拆分交给 planning）；
- 与用户最终 review 后，再跑 `harness next` 进 planning。

## 7. 待处理捕获问题（职责外）

- 无。

## 8. default-pick 决策清单（按 stage-role 同阶段不打断原则）

- DP-1（方案 B vs A）/ DP-2（keywords.yaml 单一权威源）—— 已在第 5.3 节记录，**本 stage 无新增待决策项**（其它问题全部作为 TODO 留给明日用户面对面澄清，不在 subagent 内部 default-pick）。

## 9. 产出清单

- `artifacts/main/requirements/req-38-.../requirement.md` §2-4 已填充（§1 原样，§5 模板保留）
- `.workflow/state/sessions/req-38/session-memory.md` 本文件
- 未新建对人文档 `需求摘要.md`（今日仅 seed，对人文档留给明日完整澄清后一次性产出）

---

## 第 2 轮：TODO 澄清 + AC 量化（2026-04-23/24）

### 10.1 本轮 Context Chain

- Level 0: 主 agent（technical-director / opus）→ requirement_review 阶段（stage 未切换）
- Level 1: requirement-review subagent（opus，本轮）→ 按 req-31（角色功能优化整合与交互精简）/ chg-05（S-E 决策批量化协议）批量化 TODO 1-5 + 量化 AC-1~10

### 10.2 模型自检留痕（降级）

- 期望 model = `opus`（`.workflow/context/role-model-map.yaml` roles.requirement-review = "opus"）
- 本 subagent 未能自省自身 model 一致性，按 role-loading-protocol 降级规则留痕；自我介绍中已显式声明"未能自检 model 一致性，briefing 期望 = opus"。

### 10.3 TODO 1-5 default-pick 结果（全部采纳 briefing 推荐）

#### DP-3 TODO-1 `project-profile.md` 字段形态 = 多 provider map

- **决策**：`mcp_project_ids: { apifox: <id>, postman: <id>, swagger: <id> }`（dict 形态，key 为 provider 名）。
- **理由**：api-document-upload 设计本身是 pluggable provider，未来新增 postman / swagger / confluence 等 provider 时单字段 `apifox_project_id` 会迫使每次加字段；map 形态对新增零成本。
- **可逆性**：高。`project_scanner.py::ProjectProfile` dataclass 字段可增可删，`render_project_profile` / `load_project_profile` 双向一致即可；若未来决定回退单字段，只需 dataclass 删字段 + 反向解析兼容；不影响 catalog / protocol 引用（protocol 用 `profile_key=mcp_project_ids.apifox` 路径式定位，改字段路径即可）。

#### DP-4 TODO-2 `runtime.yaml` 新增 `stage_pending_user_action` 状态字段

- **决策**：新增 `stage_pending_user_action: { type: "mcp_register", details: {...} } | null`。
- **理由**：pre-check 协议的核心机制是"探测失败 → stage 原地暂停等重启 → 重启后恢复"。没有状态字段，`harness next` 无法区分"stage 正常进行中"与"stage 在等重启"两种情形；`harness status` 也无法向用户展示 pending 状态。单纯依赖 `session-memory.md` 文本记录无法保证幂等（agent 可能重复打印引导）。
- **副作用**：
  - `workflow_helpers.py` 的 runtime 字段白名单需追加 `"stage_pending_user_action"`（现有白名单 line ~591 `"stage_entered_at"` 旁）；
  - `harness next` 推进逻辑新增 pending gate：字段非空时拒绝推进，stderr 提示类型 + details；
  - `harness status` 输出新增一行 `Pending User Action: {type}({key_details}) | None`；
  - 旧 runtime.yaml 无该字段时缺省视为 null，向前兼容。
- **可逆性**：中。字段增加不破坏现有结构，删除需同时回退 harness next / status 的读逻辑；未来若发现该机制被滥用（如 non-MCP 场景也塞 pending），可收缩为 `stage_pending_mcp_register` 专用字段。

#### DP-5 TODO-3 硬门禁五保护面扩展 + scaffold_v2 mirror 结构 = 直接扩展

- **决策**：`.workflow/context/roles/harness-manager.md §硬门禁五` 适用范围的第 2 条（`.workflow/tools/`）显式追加 `protocols` 子目录；`src/harness_workflow/assets/scaffold_v2/.workflow/tools/protocols/mcp-precheck.md` 同步 mirror。
- **理由**：沿用现有硬门禁五机制即可，protocols 子目录语义属于"跨工具共享规约"，与 catalog / index / stage-tools 同层；零新增设计成本。
- **可逆性**：高。文档行改动 + mirror 文件落盘，rollback 通过 `git revert` 单 commit 完成。
- **与 workflow_helpers.py `_SCAFFOLD_V2_MIRROR_WHITELIST` 的关系**：新增路径**不**进入白名单（受硬门禁五保护），与 ratings.yaml / runtime 状态类白名单区分；AC-8 / AC-9 明确要求保持该不对称。

#### DP-6 TODO-4 触发词 lint 实现 = `harness validate --contract triggers`

- **决策**：reviewer 阶段 checklist 调用 `harness validate --contract triggers`，diff `keywords.yaml[api-document-upload].keywords` vs `harness-manager.md §3.5.2` 镜像列表；非空 diff 非零退出码。
- **理由**：`--contract` 已有 `all` / `7` / `regression` 先例（`src/harness_workflow/cli.py` line 252-256 的 choices）；统一 CLI 入口便于维护，存量项目跑 `harness install` 刷新 pipx 后即得能力；避免另建一次性脚本散落。
- **可逆性**：高。新增 choices 值 + `run_contract_cli` 新分支，回滚只需删 choices 值 + 分支代码；不破坏其他 contract 行为。
- **实现路径**：`src/harness_workflow/cli.py` 的 `--contract` choices 追加 `"triggers"`；`src/harness_workflow/validate_contract.py::run_contract_cli(root, contract="triggers")` 新分支；`harness validate --contract all` 聚合时串联调用。

#### DP-7 TODO-5 `catalog/_template.md` = 不强制，模板加可选段

- **决策**：`_template.md` 增加一段可选注释性占位（位于 `## 注意事项` 之后或独立 `## 前置检查` 段），说明"若本工具依赖 MCP 或外部服务，必须按 `protocols/mcp-precheck.md` 引用 + 参数槽填写；纯本地工具可删去本段"。
- **理由**：并非所有工具依赖 MCP（bash / grep / read / edit / write-bootstrap / harness-log-action 等纯本地工具无需）；强制引用会出现大量 N/A 段，降低模板可读性。可选 + 注释性占位兼顾约束力（新增 MCP 类 provider 时必须显式删注释即补参数槽）与灵活性（纯本地工具可删段）。
- **可逆性**：高。模板改动不影响历史 catalog 条目；未来若决定强制，可把注释去掉变成 mandatory 段。
- **历史 catalog 处理**：不回填；已有 bash.md / grep.md 等不受影响。

### 10.4 AC 量化要点（从 seed → planning-ready 的 diff 摘要）

| AC | seed 形态 | 量化后形态 |
|----|----------|-----------|
| AC-1 | "必须召唤 tools-manager ... 不得直接给 A/B/C 通用选项" | 落位明确到 `harness-manager.md §3.5.2`；给出 session-memory.md 预期记录行；reviewer 明确 grep 黑名单词（"复制文件" / "转 PDF" / "git commit 接口定义"） |
| AC-2 | "lint 工具发现 diff 时阻塞（具体 lint 实现见 TODO-4）" | 落位到 `harness validate --contract triggers`；给出 CLI 改动点（`cli.py` choices + `validate_contract.py` 分支）；给出 pytest 用例名 |
| AC-3 | "protocols/mcp-precheck.md 存在且承载 4 阶段状态机" | 给出 ≥ 4 `^## ` 章节数 + ≥ 3 参数槽行 grep 量化判据；mirror diff 为空 |
| AC-4 | "改为单行引用 + 参数槽" | 给出"前置检查块 ≤ 3 行 / Provider" + "mcp__ grep ≤ 1 条 / Provider" 量化判据 |
| AC-5 | "打印片段 + 注册命令，状态写 session-memory，stage 原地暂停" | 追加 `runtime.yaml.stage_pending_user_action` 字段约束 + `harness next` pending gate + `harness status` 输出新行 + pytest ≥ 2 条 |
| AC-6 | "重启后 agent 重新探测命中则继续" | 追加"pending 字段被清空为 null" + session-memory 记录 `mcp_registration_resolved: apifox` + pytest 用例名 |
| AC-7 | "调 list / current project 工具拿 id 与 profile 比对" | 落位到 `ProjectProfile.mcp_project_ids` dict 字段 + render / load 格式样本 + pytest roundtrip 用例 |
| AC-8 | "存量项目 harness install 后 propagate 到位，复现 AC-1~7" | 追加 `diff -rq` 对 protocols / catalog 路径零差异 + `_SCAFFOLD_V2_MIRROR_WHITELIST` 不得加 protocols/ 的反证 |
| AC-9 | "protocols/ 子目录纳入硬门禁五保护清单" | 落位到 harness-manager.md §硬门禁五"适用范围"第 2 条追加 `protocols` + reviewer checklist + done 六层回顾 diff -rq 零差异 |
| AC-10（契约 7） | "新增 / 修改的对人文档首次引用带 title / 简短描述" | 拆成 AC-10 _template 可选段 + AC-11 契约 7 合规；AC-10 给出 grep 计数 + 行数 ≤ 10 量化；AC-11 给出 `harness validate --contract all` 退出码 0 |

（新增 AC-11 独立一条专门管契约 7 + 硬门禁六合规，避免与 AC-10 语义混叠；原 seed AC-10 拆成 AC-10 / AC-11。）

### 10.5 本 stage default-pick 决策清单（汇总）

- DP-1（方案 B vs A）：已在第 5.3 节记录，用户已确认，本轮不重开。
- DP-2（keywords.yaml 单一权威源）：已在第 5.3 节记录，用户已确认，本轮不重开。
- DP-3（TODO-1 多 provider map）：见第 10.3 DP-3。
- DP-4（TODO-2 新增 pending 字段）：见第 10.3 DP-4。
- DP-5（TODO-3 直接扩展硬门禁五）：见第 10.3 DP-5。
- DP-6（TODO-4 `harness validate --contract triggers`）：见第 10.3 DP-6。
- DP-7（TODO-5 可选段 + 注释占位）：见第 10.3 DP-7。

本轮新增 DP-3 ~ DP-7 五项，全部按 briefing 推荐 default-pick 推进，stage 内未打断用户；例外条款（数据丢失 / 不可回滚 / 法律合规）均未触发。

### 10.6 本 stage 退出前待确认清单

- [x] `requirement.md` §1 Title / §2 Goal / §3 Scope / §4 AC / §5 Split Rules 全部填充 + TODO 决策入 §3 表格
- [x] AC-1~11 全部量化（AC-11 新增）
- [x] session-memory 第 2 轮决策留痕（本段）
- [ ] 对人文档 `需求摘要.md` 产出（**留给用户下轮明确同意 / 触发 `harness next` 前由需求分析师产出**，本轮 briefing 未要求产出）
- [ ] `harness validate --contract all` 自检（planning 切换前由主 agent 跑，本 subagent 不跑）

### 10.7 产出清单（第 2 轮）

- 覆写 `artifacts/main/requirements/req-38-.../requirement.md`（§3 追加 TODO 决策表；§4 AC-1~10 全部量化 + 新增 AC-11；§5 追加 planning-ready 拆分建议）
- 追加本 session-memory.md 第 10 节（本段），未覆写前 9 节。
- 未修改 requirement.md / session-memory.md 之外的任何项目文件（禁止项）。
- 未派发下层 subagent（禁止项）。
- 未推进 stage / 未跑 `harness *` 命令（禁止项）。

---

## 第 3 轮：planning 拆分决策 + chg-01~05 落地 + DAG（2026-04-23）

### 11.1 本轮 Context Chain

- Level 0: 主 agent（technical-director / opus）→ planning 阶段
- Level 1: planning subagent（opus，本轮）→ 把 requirement.md §5 planning-ready 拆分建议正式落地为 chg-01~05 的 change.md + plan.md

### 11.2 模型自检留痕（降级）

- 期望 model = `opus`（`.workflow/context/role-model-map.yaml` roles.planning = "opus"）
- 本 subagent 未能自省自身 model 一致性，按 role-loading-protocol 降级规则留痕；briefing 已显式声明"本 subagent 未能自检 model 一致性，briefing 期望 = opus"。

### 11.3 拆分粒度最终决策

**采纳 §5 候选 5 切分，但对 chg-01 / chg-05 做最小边界调整**：

- **调整点**：把原 §5 候选中归属 chg-05 的 AC-9（硬门禁五保护面扩展）挪到 chg-01。
- **理由**：AC-9 要求 `protocols/` 子目录纳入硬门禁五保护面；而 protocols/ 子目录落盘本身由 chg-01 完成。两者紧耦合——protocols/ 文件 live 落盘但 harness-manager.md §硬门禁五 未扩展、scaffold_v2 mirror 未同步时，若有任何人跑 reviewer checklist 扫 diff 即会 FAIL。将 AC-9 合并到 chg-01 保证"protocols/ 第一次落盘 = 保护面同步扩展 + mirror 就位"原子完成。
- **chg-05 调整后收敛**：AC-8（存量项目同步验证）+ AC-10（_template 可选段）+ AC-11（契约 7 / 硬门禁六合规自检），定位为"端到端复现 + 模板可选段 + 全 req 契约自检"的收官 chg。
- **其他 chg 粒度不变**：chg-02（触发门禁 + lint）、chg-03（runtime pending + gate）、chg-04（ProjectProfile dataclass）各自独立边界清晰。
- **DP-8 记录**：该调整按 default-pick 协议推进，不打断用户，本轮 batched-report。可逆性高（若后续想回滚到原粒度，把 AC-9 相关 Step 从 chg-01 挪回 chg-05 即可）。

### 11.4 最终 chg 清单（覆盖 AC-1~11 全部）

| chg | title | 覆盖 AC | 依赖 |
|-----|-------|---------|------|
| chg-01 | protocols 目录 + catalog 单行引用 + 硬门禁五保护扩展 | AC-3 / AC-4 / AC-9 | 无（起点） |
| chg-02 | 触发门禁 §3.5.2 + harness validate triggers lint | AC-1 / AC-2 | chg-01 |
| chg-03 | runtime pending 字段 + next/status gate | AC-5 / AC-6 | chg-01（推荐 chg-02 先落地以便人工复现 AC-5） |
| chg-04 | ProjectProfile.mcp_project_ids 多 provider map | AC-7 | chg-01（代码层可与 chg-03 并行） |
| chg-05 | 存量项目同步验证 + _template 可选段 + 契约合规 | AC-8 / AC-10 / AC-11 | chg-01 + chg-02 + chg-03 + chg-04 |

AC 覆盖自证：AC-1（chg-02）/ AC-2（chg-02）/ AC-3（chg-01）/ AC-4（chg-01）/ AC-5（chg-03）/ AC-6（chg-03）/ AC-7（chg-04）/ AC-8（chg-05）/ AC-9（chg-01）/ AC-10（chg-05）/ AC-11（chg-05）= 11/11 全覆盖，无遗漏，无重复。

### 11.5 跨 chg 依赖 DAG + 推荐 executing 顺序

```
                              req-38 planning DAG
                              ====================

              chg-01 (protocols 目录 + catalog 单行引用 + 硬门禁五保护扩展)
                  │  [AC-3 / AC-4 / AC-9]
                  │
        ┌─────────┼──────────┬───────────┐
        ↓         ↓          ↓           ↓
    chg-02     chg-03      chg-04       │
(触发门禁+lint)(pending gate)(ProjectProfile)
  [AC-1/AC-2] [AC-5/AC-6]    [AC-7]     │
        │         │          │           │
        └─────────┴──────────┴───────────┘
                  ↓
              chg-05 (存量同步验证 + _template + 契约合规)
                  [AC-8 / AC-10 / AC-11]
```

- **推荐 executing 线性顺序**：chg-01 → chg-02 → chg-03 → chg-04 → chg-05。
- **可并行点**：chg-02 / chg-03 / chg-04 三者之间**代码层互不依赖**（分别触碰 harness-manager.md + cli.py validate 分支 / workflow_helpers 白名单 + cli.py next/status / project_scanner.py），可在 chg-01 完成后并行进入 executing。
- **推荐线性不并行的理由**：
  - 减少 reviewer 并发审查认知负担；
  - chg-03 / chg-04 均要细化 `protocols/mcp-precheck.md` 某阶段的占位文本到实际细节，并行会出现 mirror 文件双写冲突；
  - chg-05 的 AC-8 端到端复现必须在 chg-01~04 全部落地后才能跑通。

### 11.6 本 stage default-pick 决策清单（汇总）

- **DP-8（本轮新增）**：AC-9 归属从 chg-05 挪到 chg-01（与 AC-3 / AC-4 耦合落地 protocols 保护面）。理由：protocols 落盘 + 硬门禁五保护扩展 + scaffold_v2 mirror 三者原子一致性保证。可逆性高。
- **DP-1 ~ DP-7**：第 1-2 轮已记录，本轮不重开。
- **例外条款**（数据丢失 / 不可回滚 / 法律合规）本轮未触发。

### 11.7 本 stage 退出前待确认清单

- [x] 5 个 chg 工作区已通过 `harness change "<title>"` 创建，path 落到 `artifacts/main/requirements/req-38-.../changes/chg-01~05-*/`
- [x] 每个 chg 的 change.md 填充完毕（Goal / Scope / AC / Risks）
- [x] 每个 chg 的 plan.md 填充完毕（Development Steps / Verification Steps / Dependencies & Execution Order）
- [x] AC-1~11 全部覆盖，无遗漏，无重复
- [x] 跨 chg 依赖 DAG 已画出 + 推荐执行顺序已标注
- [x] session-memory 第 3 轮决策留痕（本段）
- [ ] 对人文档 `变更简报.md`（每个 chg 一份）产出——**按 briefing 此轮不硬性要求**（briefing 未在步骤列表中显式要求产出 5 份变更简报；是否补齐由主 agent / 用户决定是否在 stage 流转前补）
- [ ] `harness validate --contract all` 自检（planning → executing 切换前由主 agent 跑，本 subagent 不跑）

### 11.8 产出清单（第 3 轮）

- 跑 `harness change` 创建 5 个 chg 工作区（chg-01~05），自动生成 change.md / plan.md / required-inputs.md / session-memory.md 模板。
- 覆写 5 份 `change.md`（每个 chg 一份，含 Title / Goal / Requirement / Scope / AC / Risks）。
- 覆写 5 份 `plan.md`（每个 chg 一份，含 Development Steps / Verification Steps（2.1 unit + 2.2 manual + 2.3 AC Mapping）/ Dependencies & Execution Order）。
- 追加本 session-memory.md 第 11 节（本段），未覆写前 10 节。
- 未派发下层 subagent（禁止项）。
- 未推进 stage（禁止项，不跑 `harness next`）。
- 未修改 requirement.md（禁止项）。
- 未写 executing 阶段该写的 impl 代码（禁止项）。

### 11.9 产出文件清单（绝对路径）

- `artifacts/main/requirements/req-38-api-document-upload-工具闭环-触发门禁-mcp-pre-check-协议-存量项目同步/changes/chg-01-protocols-目录-catalog-单行引用-硬门禁五保护扩展/{change.md, plan.md}`
- `artifacts/main/requirements/req-38-api-document-upload-工具闭环-触发门禁-mcp-pre-check-协议-存量项目同步/changes/chg-02-触发门禁-3-5-2-harness-validate-triggers-lint/{change.md, plan.md}`
- `artifacts/main/requirements/req-38-api-document-upload-工具闭环-触发门禁-mcp-pre-check-协议-存量项目同步/changes/chg-03-runtime-pending-字段-next-status-gate/{change.md, plan.md}`
- `artifacts/main/requirements/req-38-api-document-upload-工具闭环-触发门禁-mcp-pre-check-协议-存量项目同步/changes/chg-04-projectprofile-mcp_project_ids-多-provider-map/{change.md, plan.md}`
- `artifacts/main/requirements/req-38-api-document-upload-工具闭环-触发门禁-mcp-pre-check-协议-存量项目同步/changes/chg-05-存量项目同步验证-_template-可选段-契约合规/{change.md, plan.md}`

---

## 12. reg-01（对人汇报批量列举 id 缺 title 不可读）诊断留痕

### 12.1 触发背景

- req-38 testing 阶段结尾，主 agent 对用户的 batched-report 末尾写「DAG 完成度：chg-01 / 02 / 03 / 04 / 05 全落地……」，5 个 chg id 被压缩为裸数字扫射形态。
- 用户反馈：「我希望所有的对话中不要出现光有 id 没有 title 的情况……根本不知道你在说什么」。
- 主 agent 走 `harness regression "对人汇报批量列举 id 缺 title 不可读"` 创建 reg-01，派发 regression subagent（opus）独立诊断。

### 12.2 诊断结论

- **真实问题**：体验层确凿违反契约 7（req-30（slug 沟通可读性增强：全链路透出 title）） / 硬门禁六（req-35（base-role 加硬门禁：对人汇报 ID 必带简短描述））的根目的。
- **根因三层**：字面层（例外条款歧义）+ 批量场景层（规约未显式定义）+ agent 行为偏差层（优先 token 紧凑而非对人可读）。
- **推荐路由**：`harness regression --change "硬门禁六 + 契约 7 批量列举子条款补丁"` → 转为 req-38 scope 内新 chg。

### 12.3 模型自检留痕（降级）

- 期望 model = `opus`（按 `.workflow/context/role-model-map.yaml` roles.regression）；briefing 声明 Opus 4.7。
- 本 regression subagent 未能完全自省子版本号，按 role-loading-protocol 降级规则留痕；自我介绍中已显式声明 `regression / opus`。

### 12.4 产出文件清单

- `artifacts/main/requirements/req-38-.../regressions/reg-01-对人汇报批量列举-id-缺-title-不可读/regression.md`（覆写）
- `artifacts/main/requirements/req-38-.../regressions/reg-01-对人汇报批量列举-id-缺-title-不可读/analysis.md`（覆写）
- `artifacts/main/requirements/req-38-.../regressions/reg-01-对人汇报批量列举-id-缺-title-不可读/decision.md`（覆写）
- `.workflow/state/sessions/req-38/reg-01/session-memory.md`（新建）
- 本 session-memory.md 第 12 节（本段，追加）

### 12.5 不做清单（按 briefing 禁止项）

- 未派发下层 subagent。
- 未修改 base-role.md / stage-role.md / 契约文件（执行交给后续 chg executing）。
- 未翻转 meta.yaml status（由主 agent 走 `harness regression --change` CLI 完成）。
- 未推进 stage。
- `.workflow/state/sessions/req-38/session-memory.md`（本轮第 11 节追加）
