# Session Memory — req-55（项目路书(Playbook)体系——项目地图+代码导航）analysis stage 汇总

## 1. Current Goal（analysis stage）

完成 req-55 analysis stage：
- 完善 `requirement.md`（Goal / Scope / 12 条 AC / Split Rules）
- 拆出 5 个 chg（chg-01～chg-05），每个含 change.md / plan.md / session-memory.md
- 列出 5 条开放问题（OQ）+ default-pick 推荐

## 2. Context Chain

- Level 0: 主 agent（harness-manager）→ analysis stage 编排
- Level 1: Subagent-L1（analyst / opus）→ req-55 analysis stage 全流程

## 3. Completed Tasks

- [x] 完善 `.workflow/flow/requirements/req-55-.../requirement.md`（Goal / Scope / 12 AC / Split Rules / 5 chg DAG）
- [x] chg-01（路书目录骨架契约）：change.md + plan.md + session-memory.md 各 1 份
- [x] chg-02（baseRole 代码加载规则与 CLAUDE 索引）：change.md + plan.md + session-memory.md 各 1 份
- [x] chg-03（harness install 追加路书初始化）：change.md + plan.md + session-memory.md 各 1 份
- [x] chg-04（harness playbook-refresh 子命令）：change.md + plan.md + session-memory.md 各 1 份
- [x] chg-05（harness playbook-check 子命令）：change.md + plan.md + session-memory.md 各 1 份

## 4. Results

### requirement.md 摘要

- **Goal**：解决 AI agent 全局扫描代码的浪费 + 业务术语错误推断；交付"项目地图 + agent 强制加载规则 + 路书生命周期 CLI"三件一体。
- **Scope Included**：5 chg 覆盖（骨架契约 / baseRole 规则 / install 追加 / refresh / check）。
- **Scope Excluded**：脚本不调 LLM / agent 不维护路书 / 路书不写流程文档 / 不复制内容到多 domain / 不在每个角色 prompt 重复写规则。
- **Acceptance Criteria**：12 条，每条配可验证手段（grep / pytest / subprocess / harness validate exit code）。

### 5 chg DAG

```
chg-01（路书目录骨架契约：playbook-layout.md）
   ↓
chg-02（baseRole 代码加载规则 + CLAUDE 索引）   ← 与 chg-03 可并行
chg-03（harness install 追加路书初始化阶段）       ← 依赖 chg-01
   ↓
chg-04（harness playbook-refresh 子命令）           ← 依赖 chg-03 fixture
chg-05（harness playbook-check 子命令）             ← 依赖 chg-03/04，可与 chg-04 并行
```

### 各 chg plan.md 关键步骤摘要

- **chg-01（路书目录骨架契约）**：写 `.workflow/flow/playbook-layout.md`（5 节）+ pytest 2 TC + harness validate。
- **chg-02（baseRole 代码加载规则与 CLAUDE 索引）**：base-role.md 加硬门禁十（4 节）+ CLAUDE.md 加项目路书索引节 + pytest 3 TC。
- **chg-03（harness install 追加路书初始化）**：建 `src/harness_workflow/playbook/` 子包（4 文件）+ 改 `harness_install.py` / `cli.py` + 4 级降级领域推断 + pytest ≥ 4 TC + dogfood TC。
- **chg-04（harness playbook-refresh 子命令）**：新建 `harness_playbook_refresh.py` + 5 类 AUTO 区段替换 helper + cli 注册 + pytest 3 TC + dogfood TC。
- **chg-05（harness playbook-check 子命令）**：新建 `harness_playbook_check.py`（10 类 check 函数）+ 注册 `--contract playbook-layout` + pytest ≥ 8 TC + dogfood TC。

## 5. 开放问题（OQ）+ default-pick 清单（一次性 batched-report）

### OQ-1：路书路径定位（`artifacts/playbooks/` vs `artifacts/project/playbooks/`）

- **问题**：spec §一明确写 `artifacts/playbooks/`，但 req-52 / chg-01 已确立 `artifacts/project/{constraints,experience,tools}/` 作为项目级承载主路径（无 branch 维度，跟项目走）。路书是否应纳入项目级承载（即 `artifacts/project/playbooks/`）？
- **选项**：
  - A：沿用 spec `artifacts/playbooks/`（与 `artifacts/project/` 平级，独立子树）。
  - B：纳入项目级 `artifacts/project/playbooks/`（与 constraints/experience/tools 同级，享用 §2.1 项目级豁免段）。
  - C：跟随 branch `artifacts/{branch}/playbooks/`（与 §1 主架构对齐，但每条分支一份独立路书 → 漂移加倍）。
- **default-pick = A**（沿用 spec `artifacts/playbooks/`）
- **理由**：(i) spec 用户原话明确 `artifacts/playbooks/`；(ii) 路书是"项目地图"，跟项目走、不跟 branch 走，与 req-52 项目级理念一致；(iii) 但路书内容（4 顶层 + domains/）不属 req-51 §2.1 豁免的 3 类（constraints/experience/tools），强行塞 `artifacts/project/` 会污染 §2.1 豁免边界；(iv) 推荐在 `repository-layout.md` §2 白名单新增"playbook 文档"类型（chg-01 内顺手扩白名单），保证 `artifact-placement` 契约不报违规。
- **若用户选 B**：把 `artifacts/playbooks/` 改为 `artifacts/project/playbooks/`，全部 5 chg 路径相应迁移；§2.1 豁免段需扩展容纳 4 类（constraints/experience/tools/playbooks）；CLAUDE.md 索引节 + baseRole 引用同步改路径。

### OQ-2：base-role 章节编号

- **问题**：base-role.md 现有硬门禁清单为"一/二/三/四/六/七/九"（缺 五/八，历史编号），spec §三的"代码加载规则"如何编号才不冲突？
- **选项**：
  - A：沿用既有"硬门禁 N"风格 → 新编号 = **硬门禁十**（与现有硬门禁九平行）。
  - B：单独章节 `## 代码加载规则（强制）`，不进硬门禁清单（弱化等级）。
  - C：补齐 五/八 缺号（重排所有编号）。
- **default-pick = A**（硬门禁十）
- **理由**：(i) spec §三明确写"硬性规则"+"无条件生效"，与既有硬门禁等价；(ii) 沿用既有风格变更最小、兼容历史引用；(iii) C 选项要重排所有引用代价高、与本 req 边界不符；(iv) 历史缺号（五/八）属早期清理痕迹，不在本 req 修复范围。

### OQ-3：与 req-51 / req-52 既有 install 行为冲突

- **问题**：`harness install` 已被 req-50/req-51/req-52 多次扩展（install_agent + install_repo + project mirror 同步等）。再追加路书初始化阶段是否引发执行链耦合 / 现有调用方 expectation 偏差？
- **选项**：
  - A：默认行为 = `install_agent → install_repo → init_playbook`（追加阶段，不修改既有内部）。
  - B：默认行为不动，路书初始化仅在显式 `--with-playbook` flag 下触发（现有调用方零感知）。
  - C：把路书初始化做成独立子命令 `harness playbook-init`，不进 install。
- **default-pick = A**（追加阶段，不修改既有内部）
- **理由**：(i) spec §四明确"`harness install` —— 已有命令，**追加**路书初始化能力"；(ii) 路书初始化幂等（已存在则跳过），不破坏既有 install_repo 产物；(iii) `--skip-playbook` flag 提供逃生口，CI 中需关闭路书的场景显式传 flag；(iv) C 选项与 spec 直接冲突。
- **风险监控**：实施时 chg-03 的 dogfood TC 必须断言"现有 install 默认行为产物（mirror / agent skill）依然落地"，避免追加阶段意外破坏。

### OQ-4：领域骨架自动推断 fallback（harness-workflow 自身仓不适用）

- **问题**：spec §四"领域骨架自动推断"按 `src/modules/* / src/domains/* / app/*` 模式，但 harness-workflow 自身是 `src/harness_workflow/*.py` 单包结构，3 种模式零命中 → install 跑出 0 个 domain，路书形态不完整。
- **选项**：
  - A：3 种模式零命中时 abort + 提示用户手动配置。
  - B-modified：4 级降级链（`src/modules/* → src/domains/* → app/* → src/{pkg}/*次级模块`），单包项目把 `src/harness_workflow/{tools, playbook, assets}` 这类次级目录作 fallback 领域。
  - C：零命中时生成单一 `domains/main/` 占位领域，所有内容 TODO。
- **default-pick = B-modified**（4 级降级链 + 次级模块兜底）
- **理由**：(i) A 太严格，对单包项目不友好；(ii) C 占位过弱，路书几乎无内容；(iii) B-modified 在保持 spec 三种模式优先级的同时给单包项目实质性的领域骨架（如 `tools / playbook / assets`），且推断器永远 ≥ 1 个领域；(iv) 用户后续可手工编辑 `domains/<领域>/README.md` 调整。
- **实施约束**：chg-03 的 `domain_inference.py` 必须暴露推断顺序为 stdout（"matched mode: src/{pkg}/*次级模块"），让用户感知 fallback 已触发。

### OQ-5：路书"只读"约束如何对 agent 生效

- **问题**：spec §三明确"路书只读"，但 base-role 是写规则，无 hook 拦截 agent 真正的写入操作。是否在本 req 阶段引入硬强制？
- **选项**：
  - A：本 req 仅写规则 + chg-05 漂移检测兜底（CI 闸门），不引入 hook。
  - B：在 settings.json 加 PreToolUse hook 拦截 `Edit / Write` 对 `artifacts/playbooks/` 的写入。
  - C：把路书目录设 read-only filesystem 权限（chmod / git ignore-check）。
- **default-pick = A**（仅写规则 + chg-05 漂移检测）
- **理由**：(i) hook 强制力强但跨平台（Codex / Claude Code / Qoder）实现不一致，本 req 边界外；(ii) C 文件权限影响 install 的写入路径，复杂度高；(iii) chg-05 `playbook-check` 在 CI 阶段能检出 agent 偷改（如 AUTO 区段被改但未跑 refresh 即提交），形成事后审计闭环；(iv) 真实 req 跑过 1 次后再决定是否升级 B（沉淀 known-risks 留观察项）。
- **若观察到 agent 频繁违反**：开 reg-NN 升级到 B（PreToolUse hook）。

## 6. 经验沉淀候选

- **候选 1（analyst → 经验文件）**：本 req 演示了"按交付物层次拆 chg + DAG 单向依赖"的小型 req 拆法（5 chg / 4 day），适合作为 req-50 后"机器型 + 单 stage analysis" 流程下的拆 chg 样本，待 req-55 真实落地后由 acceptance / done 阶段判断是否沉淀到 `.workflow/context/experience/roles/analyst.md`。
- **候选 2（known-risks → 风险文件）**：风险 R-1（领域推断在单包项目零命中）→ 单包结构项目按"4 级降级 fallback"，可作为通用 install 推断器经验沉淀；待 chg-03 落地后回写 `.workflow/context/experience/risk/known-risks.md`。
- **候选 3（known-risks 新增，OQ-5 补充）**：路书只读软约束 + CI 兜底（OQ-5=A 拍定）—— 本 req 不引入 PreToolUse hook / 不改文件系统权限，依赖 baseRole 硬门禁十规则 + chg-05 `playbook-check` AUTO 区段漂移检测的事后审计闭环；**观察项**：如果观察到 agent 频繁违反（如绕过规则手改路书），开 reg-NN 升级到 PreToolUse hook（settings.json）或文件系统权限锁。沉淀位置 = `.workflow/context/experience/risk/known-risks.md`，沉淀触发 = req-55 真实落地 1 次后；详见 chg-05 session-memory.md `## 6`。
- **本 stage 不写经验文件**（沉淀在执行 / 验收后由对应角色按真实落地数据回写）。

## 7. 路径自检（硬门禁四 + 路径自检硬门禁，chg-01）

| 工件类型 | 落点 | 是否合规 |
|---------|------|---------|
| requirement.md | `.workflow/flow/requirements/req-55-项目路书-playbook-体系-项目地图-代码导航/requirement.md` | ✅ 机器型 → flow/ |
| chg-01 ~ chg-05 change.md / plan.md / session-memory.md | `.workflow/flow/requirements/req-55-.../changes/{chg-id}-{slug}/` | ✅ 机器型 → flow/ |
| 本 req session-memory.md | `.workflow/flow/requirements/req-55-.../session-memory.md` | ✅ 机器型 → flow/ |
| inputs/initial-spec.md | `artifacts/feature-req-55-playbook/requirements/req-55-.../inputs/initial-spec.md` | ✅ 用户原始 spec 只读，不在本 stage 改写 |

无工件落 `artifacts/main/...` 或 `artifacts/{stage}/...`，符合 chg-01（机器型工件路径修复）契约 + repository-layout.md §3 落位表。

## 8. 汇报字段（按 stage-role.md 统一精简汇报模板）

### 字段 1：产出（≤ 3 行）

- `.workflow/flow/requirements/req-55-项目路书-playbook-体系-项目地图-代码导航/`：requirement.md（1 份完善版，含 12 条 AC）+ session-memory.md（本汇总）+ 5 chg 子目录（chg-01 路书目录骨架契约 / chg-02 baseRole 代码加载规则与 CLAUDE 索引 / chg-03 harness install 追加路书初始化 / chg-04 harness playbook-refresh 子命令 / chg-05 harness playbook-check 子命令），每个 chg 含 change.md + plan.md + session-memory.md 共 16 份机器型工件。
- 拆分粒度 = 4 day 总量 / 5 chg / DAG 单向依赖（chg-01 → chg-02/chg-03 → chg-04 ← chg-05）。
- 测试用例设计：每个 chg plan.md §4 含 ≥ 2 P0 TC，chg-03/04/05 各含 1 条 dogfood TC（subprocess + tmpdir + stdout/runtime/feedback 三断言）。

### 字段 2：状态（单行）

- **PASS**。analysis stage 退出条件全部满足：requirement.md 含 Goal/Scope/AC/Split Rules / 5 chg 全部含 change.md + plan.md / 每个 plan.md 含 §4 测试用例设计 / 5 OQ 已 batched-report 含 default-pick / 路径自检合规。

### 字段 3：开放问题（5 条）+ 用户拍定结果（汇报版本 v2，2026-04-30 同步完成）

- **OQ-1（路书路径定位）= 用户拍定 = B**（`artifacts/project/playbooks/`）→ 已批量同步至所有 chg。
- **OQ-2（base-role 章节编号）= 用户拍定 = A**（硬门禁十：代码加载规则（强制））→ chg-02 章节标题已对齐。
- **OQ-3（与 req-51 / req-52 install 行为冲突）= 用户拍定 = A**（默认追加阶段 + `--skip-playbook` / `--playbook-only` 互斥逃生口；dogfood TC 守护"现有 install 默认行为产物依然落地"）。
- **OQ-4（领域推断在本仓不适用）= 用户拍定 = B-modified**（4 级降级链 `src/modules/* → src/domains/* → app/* → src/{pkg}/*次级模块`，命中即停 + stdout 打印命中级别）。
- **OQ-5（路书只读对 agent 强制力）= 用户拍定 = A**（本 req 仅写规则 + chg-05 漂移检测兜底；不引入 PreToolUse hook、不改文件系统权限；known-risks 沉淀候选记录于 chg-05 session-memory.md `## 6`，done 阶段回写）。

### 字段 5：结尾硬约束

**本阶段已结束。**

---

## 9. 用户决策记录（增量更新，2026-04-30）

### OQ-1：用户拍定 = **B**（`artifacts/project/playbooks/`）

- **用户原话**：`artifacts/project/playbooks/ 与规范保持一致`
- **理由**：与 req-51（项目级规则-经验-工具支持从制品引入）/ req-52（硬编码main路径全面去除-跟项目走）确立的项目级承载规范保持一致，不在 `artifacts/` 下另开独立子树。
- **影响范围**：
  - chg-01（路书目录骨架契约）：`playbook-layout.md` 中所有路径引用 `artifacts/playbooks/` → `artifacts/project/playbooks/`
  - chg-02（baseRole 代码加载规则与 CLAUDE 索引）：base-role.md / CLAUDE.md 中 `@./artifacts/playbooks/...` 全部 → `@./artifacts/project/playbooks/...`
  - chg-03（harness install 追加路书初始化）：写入路径 + dogfood TC fixture 路径同步
  - chg-04（harness playbook-refresh 子命令）：扫描 / 写入路径同步
  - chg-05（harness playbook-check 子命令）：扫描 / 漂移检测路径同步
  - `repository-layout.md` §2.1 项目级豁免：从 3 类（constraints/experience/tools）扩 4 类（+ playbooks）
- **批量更新时机**：5 OQ 全部拍板后，由 analyst 二次回到 worktree 一次性把所有 chg 文件路径改完，不分次。

### OQ-2：用户拍定 = **A**（硬门禁十）

- **决策**：base-role.md 新增 `## 硬门禁十：代码加载规则（强制）`，与既有硬门禁一/二/三/四/六/七/九并列。
- **影响范围**：
  - chg-02（baseRole 代码加载规则与 CLAUDE 索引）：base-role.md 章节标题为"硬门禁十"，内容覆盖 4 节（路书优先 / 兜底规则 / 项目背景加载 / 不该做的事）
  - 不补齐五/八历史缺号（保持 req 边界）
  - base-role.md 顶部"硬门禁清单"列表追加"硬门禁十：代码加载规则"
  - testing 阶段 grep `'## 硬门禁'` 期望命中数 ≥ 8（原 7 + 新 1）

### OQ-3：用户拍定 = **A**（默认追加 + `--skip-playbook` 逃生口）

- **决策**：`harness install` 默认行为 = `install_agent → install_repo → init_playbook`（追加阶段，不修改既有内部）；提供 `--skip-playbook` 跳过路书阶段，`--playbook-only` 仅跑路书阶段。
- **影响范围**：
  - chg-03（harness install 追加路书初始化）：`init_playbook(root, skip=False, only=False)` helper + cli flag 注册 + dogfood TC 必须断言"现有 install 默认行为产物（mirror / agent skill）依然落地"
  - 文档（README / SKILL.md / scaffold mirror）补"`harness install` 现含路书初始化阶段"

### OQ-4：用户拍定 = **B-modified**（4 级降级链 + 单包次级模块兜底）

- **决策**：领域骨架自动推断按以下优先级匹配，命中即停：
  1. `src/modules/*`（spec 原文优先级 1）
  2. `src/domains/*`（spec 原文优先级 2）
  3. `app/*`（spec 原文优先级 3）
  4. **兜底**：`src/{pkg}/*` 次级模块（单包项目，如本仓自动得 `tools / playbook / assets / hooks` 等）
- **影响范围**：
  - chg-03 `domain_inference.py`：实现 4 级匹配 + stdout 打印命中级别（如 `matched mode: src/{pkg}/*次级模块`）
  - 推断器永远 ≥ 1 个领域（兜底兜底）
  - chg-03 plan.md §4 测试用例：覆盖 4 级各 1 条 fixture，含本仓 dogfood TC
  - 用户后续可手编 `domains/<领域>/README.md` 调整

### OQ-5：用户拍定 = **A**（仅写规则 + chg-05 漂移检测兜底，本 req 不引入 hook）

- **决策**：本 req 阶段只写 baseRole 规则约束 agent 不改路书；chg-05 `harness playbook-check` 在 CI 阶段扫描 `<!-- AUTO:* -->` 区段是否被改但未跑 refresh、`code.md` 引用文件是否失效等漂移，构成事后审计闭环。
- **影响范围**：
  - chg-02 base-role.md 硬门禁十明确"不要修改 `artifacts/project/playbooks/` 下任何文件"
  - chg-05 playbook-check 实现 AUTO 区段哈希校验 + 路径有效性 + 关键词覆盖三类检查
  - 不在 settings.json 加 PreToolUse hook（跨 4 平台复杂度，本 req 边界外）
  - 不改文件系统权限（chmod / 权限锁影响 install 写入路径）
- **沉淀候选**：写入 `.workflow/context/experience/risk/known-risks.md` 一条"路书只读软约束 + CI 兜底，观察项；如果观察到 agent 频繁违反，开 reg-NN 升级到 PreToolUse hook"。

---

## 10. 决策同步任务（待 analyst 执行）

5 OQ 全部拍定后，由 analyst 二次回到 worktree 执行**一次性批量同步**，覆盖：

1. **路径迁移（OQ-1=B）**：5 chg 全部 `artifacts/playbooks/` → `artifacts/project/playbooks/`；`repository-layout.md` §2.1 豁免 3 类 → 4 类
2. **章节编号（OQ-2=A）**：chg-02 明确"硬门禁十"
3. **install 行为（OQ-3=A）**：chg-03 默认追加 + 双 flag（`--skip-playbook` / `--playbook-only`） + dogfood TC 守护
4. **领域推断（OQ-4=B-modified）**：chg-03 4 级降级 + stdout 打印命中级别
5. **路书只读（OQ-5=A）**：chg-02 规则段 + chg-05 漂移检测兜底；known-risks 沉淀候选

同步完成后，session-memory `## 8. 汇报字段` 更新对人汇报版（确认 5 OQ 已对齐），requirement.md AC-09 路径合规说明微调。

### 同步执行记录（2026-04-30，analyst / opus）

**修改文件清单（按 chg 分组）**：

- **req 主目录**（共 3 文件）
  - `requirement.md`：AC-04 / AC-05 / AC-09 / Goal / Scope / Risk R-1 路径与领域推断描述全量同步至 `artifacts/project/playbooks/` + 4 级降级 + OQ-1/3/4/5 决策注脚。
  - `session-memory.md`：`## 8` 字段 3 升级为 v2 汇报版（5 OQ 拍定结果），`## 6` 新增候选 3（OQ-5 路书只读软约束 + CI 兜底），`## 10` 末尾追加本同步执行记录。
- **chg-01（路书目录骨架契约）**（3 文件）
  - `change.md`：`artifacts/playbooks/` → `artifacts/project/playbooks/`。
  - `plan.md`：执行步骤插入"§1 顶部声明路书根 = `artifacts/project/playbooks/`" + 新增"扩 `repository-layout.md` §2.1 项目级豁免 3 类 → 4 类"步骤；产物段 + §4 测试用例新增 TC-03/TC-04（路径声明 + §2.1 豁免扩展断言）。
  - `session-memory.md`：Current Goal 补 §1 顶部路径声明 + §2.1 扩 4 类；Completed Tasks 同步；Open Questions 标注 OQ-1=B 拍定。
- **chg-02（baseRole 代码加载规则与 CLAUDE 索引）**（3 文件）
  - `change.md`：硬门禁十章节标题确认 = `## 硬门禁十：代码加载规则（强制）`（OQ-2=A）；4 节内容路径全量替换；新增"不修改 `artifacts/project/playbooks/` 下任何文件" → OQ-5；AC-02.1/2.3/2.4 grep 命中数 ≥ 8 + `artifacts/project/playbooks` ≥ 4。
  - `plan.md`：执行步骤 2 顶部硬门禁清单条目改成 `- 硬门禁十：代码加载规则（req-55（项目路书Playbook体系） / chg-02（baseRole代码加载规则与CLAUDE索引））`；步骤 3 详写 4 节具体内容（含 OQ-5 路书只读说明）；步骤 5 pytest TC 数 2→3→4；§4 测试用例新增 TC-04 路径命中数断言。
  - `session-memory.md`：Completed Tasks 路径同步；Open Questions 标注 OQ-1/2/5 拍定。
- **chg-03（harness install 追加路书初始化）**（3 文件）
  - `change.md`：目标段补 OQ-3=A 默认追加 + 双 flag 互斥；新增内部模块段 `domain_inference.py` 详写 4 级降级链顺序 + 命中即停 + stdout 命中级别打印 + 单包 `{pkg}` 名称解析（pyproject/setup.py/`src/` 唯一子目录）；写入路径全量 `artifacts/project/playbooks/`；新增 pytest 用例升至 ≥ 6 条（含 4 级降级每级 ≥ 1 fixture + 互斥校验）；dogfood TC 加双 flag 守护断言；AC-03.1/3.7 同步；R-1 缓解描述补"命中即停 + stdout 打印"。
  - `plan.md`：执行步骤 3 详写 4 级降级 + `{pkg}` 解析；步骤 5 写入路径同步；步骤 7/8 双 flag 互斥校验；新增步骤 9（README/SKILL.md mirror 同步行）；步骤 10 pytest 数 ≥ 4 → ≥ 6；步骤 13 dogfood 加双 flag 守护；产物段 + 调用链段 + §4 测试用例 11 条全量重写（TC-01/03/04 路径替换 + TC-06 互斥校验 + TC-07~10 4 级降级 + TC-Dogfood-01 守护断言 + TC-11 自身仓第 4 级命中）。
  - `session-memory.md`：Current Goal 补 OQ-1/3/4 决策注脚；Completed Tasks 升级（4 文件子包 / 双 flag 互斥 / mirror 同步行 / pytest TC ≥ 6 / dogfood 双 flag 断言）；Open Questions 标注 OQ-1/3/4 拍定。
- **chg-04（harness playbook-refresh 子命令）**（2 文件，plan.md 无字面量改动）
  - `change.md`：扫描 / 写入路径 `artifacts/playbooks/` → `artifacts/project/playbooks/` + OQ-1=B 注脚。
  - `session-memory.md`：Current Goal 补路径同步注脚；Open Questions 标注 OQ-1=B 拍定。
- **chg-05（harness playbook-check 子命令）**（3 文件）
  - `change.md`：扫描路径 `artifacts/playbooks/` → `artifacts/project/playbooks/` + OQ-1=B 注脚；新增"AUTO 区段被改但未跑 refresh"漂移检测（OQ-5=A 兜底）。
  - `plan.md`：§4 测试用例新增 TC-12（OQ-5 兜底，stdout 含 "AUTO segment drift detected" + exit 1）；调用链段补 OQ-1=B 路径 + OQ-5 兜底说明。
  - `session-memory.md`：Current Goal 补 OQ-1/5 决策注脚；Completed Tasks 同步含 TC-12；Open Questions 标注 OQ-1/5/6；新增 `## 6 经验沉淀候选`（OQ-5 known-risks 沉淀候选，done 阶段回写 `.workflow/context/experience/risk/known-risks.md`）。

**替换次数统计**：

- 同步前 `grep -rn 'artifacts/playbooks' .workflow/flow/requirements/req-55-...` 总命中 = 34 行。
- 同步后预期 = 0 行（除 §9 OQ-1 历史决策对照行豁免）。
- 关键新关键词命中数（同步后）：`artifacts/project/playbooks` ≥ 30；`硬门禁十` ≥ 2（chg-02 内）；`4 级降级` / `matched mode` ≥ 1（chg-03 内）；`AUTO segment drift` ≥ 1（chg-05 内）；`--skip-playbook` / `--playbook-only` ≥ 4。

**Step 3 自检命中数**：见末尾 Step 3 grep 结果块（自检全过）。

**经验沉淀候选回写位置确认**：

- chg-05 session-memory.md `## 6 经验沉淀候选` 已写入"路书只读软约束 + CI 兜底（OQ-5=A）"作为待 done 阶段沉淀至 `.workflow/context/experience/risk/known-risks.md` 的候选条目。
- req 主 session-memory.md `## 6 经验沉淀候选` 已新增候选 3（OQ-5 沉淀细节）。
- 本 stage（analysis）不写入 known-risks.md 实文件；待 req-55 真实落地 1 次后由 done 阶段回写。

---

## Done Stage Six-Layer Review（2026-04-30T16:30+，主 agent done / opus）

> 主 agent（done / opus）对 req-55（项目路书Playbook体系——项目地图+代码导航）整需求周期六层回顾；与 acceptance verdict（PASS / 12 AC 全过）并列生效，不重审业务结论。

### Layer 1: Requirement 层

- **12 AC 全过**：acceptance §2 独立判定 11 PASS + AC-08 路径 A 升级 PASS；spec 与最终交付一致（5 chg DAG 完整落地）；5 OQ 用户拍板（OQ-1=B / OQ-2=A / OQ-3=A / OQ-4=B-modified / OQ-5=A）全部对应到产物（acceptance §5 5 OQ 落地复核 5/5 PASS）。
- **偏差**：AC-08 字面 `--dry-run` vs 实际 `--check`，spec 原注"遵循现有约定"已豁免，acceptance 路径 A 升级 PASS 理由充分（详见 acceptance §3）。
- **结论**：PASS。

### Layer 2: Analysis 层

- **拆分粒度合理**：5 chg / 4 day（线性）或 3 day（chg-04/05 并行），DAG 单向依赖（chg-01→chg-02/03→chg-04 ← chg-05），每个 chg 落地代码 + 测试在 1 stage 内完成。
- **派发合规**：analyst 由主 agent（harness-manager）派发 model=opus；二次派发为同 stage 决策同步任务（5 OQ 用户拍板后路径批量同步），符合 req-40 HM-1=A 协议。
- **决策记录完整**：5 OQ 用户拍定结果在 `session-memory.md §9` 留痕（含原话 / 理由 / 影响范围 / 批量同步执行记录）。
- **结论**：PASS。

### Layer 3: Execution 层

- **5 chg 实施真实性**：acceptance §5 独立 grep 命中数核查（OQ-1 主路径 0 残留 / 硬门禁十 9 处 / 双 flag 7 处 cli.py / Level-1~4 标识 / AUTO 哈希漂移检测多行）；chg-03 / chg-04 / chg-05 dogfood subprocess 端到端 PASS 已由 acceptance 复测确认。
- **scaffold_v2 mirror 同步**：chg-02 base-role.md mirror diff = 0（acceptance §7 独立验证）；chg-03/04/05 改动全在 `src/harness_workflow/*.py`（不属于 scaffold mirror 同步范围，硬门禁五不触发）；chg-01 仅改 `.workflow/flow/playbook-layout.md` 与 `.workflow/flow/repository-layout.md`，scaffold mirror 路径覆盖（CLAUDE.md mirror 差异为模板设计性差异，非 mirror 违规）。
- **pytest 真实数字一致**：testing 独立跑 41/41 PASS；acceptance 独立跑 41/41 PASS；executing 自报与 testing/acceptance 三方一致；全量回归 790 passed / 57 failed 与 chg-03/04/05 基线完全一致。
- **结论**：PASS。

### Layer 4: Testing 层

- **测试设计独立**：testing §2 充分性 / 风险盲点 / dogfood 真实性 / OQ-5 兜底有效性四维度审视，独立判定不直采 executing 自报；41/41 TC PASS。
- **dogfood 真实性**：chg-03 TC-05 / chg-04 TC-07 / chg-05 TC-10 均为 subprocess 端到端实跑（含 install_repo），非 unit；testing §6 dogfood 4 步活证完整复现，OQ-5 兜底（AUTO 区段哈希漂移）经独立注入假内容验证 exit 1 + 提示文案准确。
- **AC-08 PARTIAL 升级溯源**：testing 以字面义判 PARTIAL（`--dry-run` vs `--check`），acceptance 路径 A 引 spec 原文豁免条款升级 PASS，独立判定合规（不盲信 executing/testing 任一方）。
- **结论**：PASS。

### Layer 5: Acceptance 层

- **独立验证证据充分**：acceptance §2 12 AC 表逐条独立验证（grep 命中数 / pytest 独立跑 / dogfood 4 步独立复测 / mirror diff 独立 diff -q）；§4 dogfood 4 步独立复测与 testing §6 数字完全一致（exit code / stdout 关键行）。
- **AC-08 升级理由充分**：acceptance §3 引 spec 原文 5 项理由（豁免条款 / 语义等效 / 真正新增命令已覆盖 / 用户实际场景 / testing 字面义解读忽略豁免），路径 A 升级 PASS 推理链完整。
- **verdict 路由合理**：12/12 AC PASS + 5/5 OQ PASS + 全量回归零回归 + mirror 同步合规 + Issues 三类（AC-08 升级 / human-docs pre-existing / AC-12 状态依赖）均说明清楚 → verdict = PASS 路由 done 合理。
- **结论**：PASS。

### Layer 6: State 层（usage 自检）

- **usage-log 缺失**：`.workflow/state/sessions/req-55/usage-log.yaml` **不存在**（该目录从未创建）。
- **本 req 派发链路**：根据 session-memory 推算约 9 次（analyst × 2 含决策同步 + executing × 5 chg + testing × 1 + acceptance × 1）。
- **断言**：entries 数 = **0** vs 派发次数 ≈ 9（容差 = 0，无失败 / 无降级 stub 可知）→ **不满足 entries ≥ 派发次数 - 容差**。
- **判定**：State 层"usage 采集不完整"。本周期 9 次派发全部缺 record_subagent_usage 写入。同型病第 7 次复发（与 sug-67 / sug-68 / sug-69 / sug-70 同根因），但本周期不重复入池（建议合并升级 reg-NN，已沉淀于 known-risks 沉淀候选）。
- **结论**：观察项（不阻塞 done，但记录为 State 层数据缺口）。

### 综合结论

- **Layer 1 - 5：PASS**；**Layer 6：观察项（usage 采集不完整，非业务缺陷）**。
- **不重审 acceptance verdict**：PASS / 12/12 AC PASS / 5/5 OQ PASS / 0 FAIL。
- **本周期无新阻塞事项**；硬门禁九未触发（acceptance 已对 testing PARTIAL 路径 A 独立升级，主 agent 不再二次核查同一结论）。
- **commit revert dry-run 抽样**：本 worktree 尚未 commit，跳过 sug-31 dry-run 抽样（commit 由用户决定，archive 触发时再校验）。

**本阶段已结束。**
