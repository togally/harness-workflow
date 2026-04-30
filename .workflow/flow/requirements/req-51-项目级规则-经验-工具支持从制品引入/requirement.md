---
id: req-51
title: "项目级规则-经验-工具支持从制品引入"
created_at: 2026-04-29
operation_type: requirement
stage: analysis
---

## Background

> 用户原话："我希望把规则和经验工具等支持从制品引入，例如可以有项目自己规范，有自己的经验，有自己的工具类都可以放到制品包内的管理。"

### 现状 — 全局共享的工作流规约

harness-workflow 把"规则 / 经验 / 工具"放在三个全局共享子树，由 `harness install` / `harness update` 从 `src/harness_workflow/assets/scaffold_v2/` mirror 同步下发：

- `.workflow/context/constraints/`、`.workflow/context/roles/`、`.workflow/context/role-model-map.yaml`、`.workflow/context/index.md` —— 角色规范与索引
- `.workflow/context/experience/{regression,risk,roles,tool,stage}/` —— 全局经验（roles / tool / risk 由 mirror 守护，regression / risk / stage 在白名单内运行时业务态）
- `.workflow/tools/{catalog,index,protocols,stage-tools.md,selection-guide.md,...}` —— 工具清单与协议
- `.workflow/evaluation/`、`.workflow/flow/repository-layout.md` 等流程契约

这五大子树受 **harness-manager.md 硬门禁五（跨 repo scaffold mirror 同步）** 保护：任何 live 改动必须在同 commit 同步 mirror，否则 reviewer / done 拦截 FAIL。

### 现状 — 已有的项目独有子树（白名单豁免，但语义不全）

`harness-manager.md` 硬门禁五例外白名单已经允许少量项目独有数据存在：

- `.workflow/context/team/`、`.workflow/context/project/` —— 项目独有规约/概览
- `.workflow/context/checklists/` —— 项目演进的 checklist
- `.workflow/context/experience/{stage,regression,risk}` —— 项目沉淀的 stage/reg/risk 经验
- `.workflow/state/experience/stage/` —— stage-scoped 经验
- `.workflow/context/backup/`、`.workflow/state/`、`artifacts/`、`.workflow/flow/{archive,requirements,suggestions,bugfixes}/`

**但**：`.workflow/context/roles/`（角色规范）、`.workflow/context/constraints/`（边界规则）、`.workflow/context/experience/{roles,tool}/`（角色/工具经验）、`.workflow/tools/{catalog,index,protocols,...}`（工具清单/协议）这些**对项目最有价值的"自有规则/经验/工具"位置**，目前都被硬门禁五守护，下游用户在自己仓改动会被 `harness install --force-managed` 升级时覆盖（实测案例：sug-21（scaffold-v2 漂移）/ sug-15（mirror 同步漏改）反复出现）。

### 触发线索（下游用户痛点）

1. **bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）**：下游用户仓 PetMallPlatform 在使用 harness 时多次踩到"项目自身规约 vs 工具自身规约"的边界 —— 暴露下游用户希望把项目特有的规范沉淀到自己仓但缺乏标准位置。
2. **bugfix-8（用户项目区与开发期区分离 + 用户写保护硬门禁）/ chg-04**：当前 `harness validate --contract user-write-protected-zones` 把整个 `.workflow/` 列为用户**写保护区**，在用户仓手写 `.workflow/context/roles/my-custom-role.md` 等文件直接 ABORT；提示 "用户自定义内容请放 artifacts/ 下" —— 但 `artifacts/` 又被 `repository-layout.md` §1/§3 限定为"对人可读签字执行产物"，机器型规则/经验/工具明文禁止入。**下游用户面对"既不能写 .workflow/，也不能写 artifacts/"的真空地带**。
3. **sug-21 / sug-15 / req-34 / req-36 等漂移系列**：scaffold_v2 mirror 与 live 的同步问题反复爆雷，根因之一就是缺乏"全局 vs 项目级"的清晰分层，下游做了改动也无法稳定保留。

### 用户诉求（一句话）

下游项目仓（PetMallPlatform / uav 等）需要一个**有标准位置、有契约保护、不会被 harness install 覆盖**的项目级规则-经验-工具承载层；用户原话中的"制品包内管理"暗示"跟代码仓一起 commit、可跨开发者携带"。

---

## Goal

**核心目标**：建立"项目级规则 / 经验 / 工具"的标准承载层与加载契约，让下游用户仓可以维护自己独有的规范、经验、工具类，且：

1. `harness install --force-managed` / `harness update` 升级时**不被 mirror 覆盖**；
2. 与全局规则在加载与冲突时有**明确策略**（覆盖 / 合并 / 优先级）；
3. 与硬门禁五（scaffold mirror 同步）/ user-write-protected-zones 不打架，**有清晰的写保护豁免边界**；
4. 路径选择不违反 `repository-layout.md` §1 / §3（机器型不入 artifacts/）。

**可度量预期效果**：
- PetMallPlatform 在自己仓新增 1 条项目级规则 + 1 份项目级经验 + 1 个项目级工具 catalog 条目，跑 `harness install --force-managed` 升级后**全部保留**（diff = 0）；
- 项目级规则与全局规则同名时，按拍板策略加载（**default-pick = 项目级覆盖全局**，详见 OQ-2）；
- `harness validate --contract user-write-protected-zones` 对项目级目录**自动豁免**（不再 ABORT）；
- 项目级位置在 `repository-layout.md` 中有权威定义（§ 新增子段）。

---

## Scope

### In scope（本 req 范围内）

1. **项目级承载位置定义**：在 `.workflow/` 内或 `artifacts/` 内确定一个标准目录承载项目级规则 / 经验 / 工具（详见 OQ-1 路径选型）；
2. **覆盖的子类**：constraints / experience / tools 三类项目级化（角色规范 roles/ 出于风险考虑暂不开放，详见 OQ-3）；
3. **加载顺序与冲突解决**：role-loading-protocol.md 加载链增加项目级一段（详见 OQ-2 默认策略）；
4. **写保护豁免清单更新**：`check_user_write_protected_zones` 项目级目录加入豁免，不再 ABORT；
5. **mirror 同步契约更新**：硬门禁五例外白名单扩展，明确项目级目录**不**纳入 scaffold_v2 mirror 同步；
6. **harness install 升级保护**：`harness install --force-managed` / `harness update` 不覆盖项目级目录（即使在 managed-files.json 中也不登记，或登记后特殊处理）；
7. **repository-layout.md 契约更新**：§1 三大子树语义、§2 / §3 路径表新增项目级承载段；
8. **dogfood 测试**：在 tmpdir / 真实下游仓证明项目级数据在 install / update 流程不丢、加载时正确融合。

### Out of scope（明确划界，避免 scope creep）

1. **跨项目共享项目级规则**：本 req 只解决"单仓维护自己的"；跨仓共享（如多个微服务共享一份项目级 constraints）不在范围。
2. **角色规范（roles/）项目级化**：`.workflow/context/roles/{role}.md` 改写直接影响角色加载链与硬门禁，风险高，本 req **不开放**项目级 roles/ 覆盖（OQ-3 default-pick）；如需后续支持，新开 req。
3. **role-model-map.yaml 项目级覆盖**：模型映射变更影响成本与质量，下游一般不需要改；不在范围。
4. **工具实际实现（src/）层项目级化**：本 req 只管 `.workflow/tools/catalog/*.md` 类**工具清单 / 协议描述**的项目级化；具体工具脚本实现（如 `src/harness_workflow/tools/*.py`）打到 venv，下游无法注入新 Python 工具实现 —— 该方向超出范围。
5. **用户登录 / 权限管理**：与"项目级"无关。
6. **项目级数据的版本管理 / 迁移工具**：本 req 只定义承载层与契约；项目级数据的 schema 演进、跨版本迁移（如 v1 → v2）不在范围。
7. **PetMallPlatform 自身的项目级数据迁移**：本 req 只交付承载层；PetMallPlatform 把自己已有规则迁过来由用户后续操作（regression / suggest 路径）。

### §OQ — 关键 Open Questions（用户拍板请求）

> 本 req 涉及与既有契约（repository-layout / 硬门禁五 / user-write-protected-zones）的边界冲突，识别出 5 条关键决策点；analyst 已给 default-pick + 一句话理由，用户可一次性拍板或逐条调整。

#### OQ-1：项目级承载路径选型（**最大矛盾点**）

**冲突**：用户原话"制品包内管理"字面 → `artifacts/`，但 `repository-layout.md` §1 / §3 明文禁止机器型文档入 artifacts/（最近 bugfix-11 / req-41 / chg-01 刚把这条契约升格为底座）。

| 选项 | 路径 | 优点 | 缺点 |
|------|------|------|------|
| **A**（default-pick） | `.workflow/project/` 子树（如 `.workflow/project/{constraints,experience,tools}/`） | 不破坏 §1/§3 契约；与现有 `.workflow/context/project/` 同子树语义；硬门禁五例外白名单已包含 `.workflow/context/project/`，扩展简单 | 用户原话"制品包内"字面落空，需向用户解释"制品包" = 仓库（含 .workflow），非 artifacts 子树 |
| B | `artifacts/{branch}/project/` 子树 | 字面贴合用户"制品包内管理" | **正面冲突 §1/§3 契约**；artifacts 跨 branch 切换会丢；需为机器型契约开后门，破坏 bugfix-11 刚立的底座 |
| C | 同时支持 A + B（双轨） | 灵活 | 加载优先级复杂度翻倍；契约面同时改两处；不推荐 |

**default-pick = A**。理由：保持 `repository-layout.md` 三大子树契约清洁；用户的"制品包"理解为"代码仓制品（含 `.workflow/`）"而非"`artifacts/` 子树"，承载层放 `.workflow/project/{constraints,experience,tools}/` 与现有 `.workflow/context/project/` 子树同语义、自然延伸。**请用户拍板是否接受此理解**；若坚持 B，需另开 req 推翻 §1/§3 契约。

#### OQ-2：项目级与全局的冲突解决策略（同名规则/经验/工具）

| 选项 | 策略 | 优点 | 缺点 |
|------|------|------|------|
| **A**（default-pick） | 项目级**覆盖**全局（项目级优先） | 符合"项目特殊性 > 通用规约"直觉；下游可针对自己业务收紧 | 项目级可能违反全局硬门禁，需在 lint 层补"项目级不得删全局硬门禁字段"约束 |
| B | 全局**覆盖**项目级 | 全局契约不可破坏，安全 | 下游做的所有项目级规则形同虚设，与本 req 目标矛盾 |
| C | 项目级与全局**合并**（merge） | 两者并存 | constraints / experience 是 markdown，无结构化 schema 难自动 merge；实现复杂 |

**default-pick = A**。理由：用户诉求是"项目自己有规范"——若全局优先则项目级无意义；同时配套 lint 补丁（OQ-5）防止项目级删全局硬门禁。

#### OQ-3：项目级化的子类范围

| 选项 | 覆盖面 | 风险 |
|------|--------|------|
| **A**（default-pick） | constraints / experience / tools（三类，不含 roles/） | 中等：tools 项目级化需扩 `tools-manager` 加载逻辑 |
| B | A + roles/ | 高：roles/ 覆盖直接影响 stage 调度与硬门禁加载链；可能让项目级覆盖 base-role.md 等基础契约 |
| C | 仅 experience（最小集） | 低，但用户诉求"规则"未覆盖，目标缩水 |

**default-pick = A**。理由：覆盖用户原话三类（规则=constraints / 经验=experience / 工具=tools），剔除高风险的 roles/。roles/ 项目级化由后续 req 单独评估。

#### OQ-4：升级保护实现路径

| 选项 | 实现 | 优点 | 缺点 |
|------|------|------|------|
| **A**（default-pick） | 项目级目录**不**纳入 `_managed_file_contents` / `_scaffold_v2_file_contents` mirror；`_install_self_audit` whitelist 加项目级路径；`check_user_write_protected_zones` 豁免项目级路径 | 改三处 helper + 一处 contract，复用既有白名单机制 | mirror diff 自检需排除项目级目录 |
| B | 在 managed-files.json 中登记，但 `--force-managed` 时显式跳过 | 与 managed_state 体系兼容 | 与 `--force-managed` 语义打架（用户记忆里 force = 强制覆盖）；不直观 |
| C | 新增专门的 `--preserve-project` flag | 显式可控 | 用户每次 install 都得加 flag，易遗漏；UX 倒退 |

**default-pick = A**。理由：复用 `_SCAFFOLD_V2_MIRROR_WHITELIST` + `protected_zones` 豁免机制，最小改动；项目级目录在 `harness install` / `update` 全流程**自动**跳过同步。

#### OQ-5：项目级 lint 边界

是否需要"项目级不能删全局硬门禁字段"的 lint？

| 选项 | 策略 | 备注 |
|------|------|------|
| **A**（default-pick） | 不增 lint，仅文档警告 + done 阶段六层回顾抽查 | 复杂度低；信任下游开发者；与 OQ-2 = A 配套 |
| B | 增 `harness validate --contract project-overrides` lint | 防止下游误删硬门禁；但需要识别"哪些字段不可删"，工程量大 |
| C | 不增 lint 也不警告 | 风险大 |

**default-pick = A**。理由：本 req 优先解决"路径承载 + 升级保护"；lint 防御作为 followup sug 入池，不阻塞主线。

---

## Acceptance Criteria

> 每条 AC 可独立测试；`{project-path}` 占位符在 OQ-1 拍板后落定（default A → `.workflow/project/`）。

- **AC-01（路径承载与契约定义）**：`repository-layout.md` 含项目级承载段落，明确 `{project-path}/{constraints,experience,tools}/` 三子树的语义、产出者、消费者；`harness validate --human-docs` exit 0；scaffold_v2 mirror 同步该契约文件。

- **AC-02（升级保护）**：在下游用户仓 `{project-path}/constraints/my-rule.md` 写入项目独有规则，跑 `harness install --force-managed` 后**文件不变**（`diff` 空，文件 mtime 不更新到 install 时间）；同时 `harness install` self-audit 不报 drift WARNING。

- **AC-03（用户写保护豁免）**：在下游用户仓 `{project-path}/{constraints,experience,tools}/` 下手写文件后，跑 `harness validate --contract user-write-protected-zones` exit code = 0（PASS，不再 ABORT）；同时 `.workflow/context/roles/` 等其他保护区手写仍 ABORT（豁免精准，不放大保护面）。

- **AC-04（mirror 同步豁免）**：本仓 `git diff --name-only` 命中 `{project-path}/...` 任意文件时，硬门禁五**不要求**同步 `src/harness_workflow/assets/scaffold_v2/{project-path}/...`；`harness-manager.md` 硬门禁五例外白名单含项目级路径（条目可被 grep 命中）；reviewer 阶段 checklist 通过。

- **AC-05（加载顺序与冲突解决）**：`role-loading-protocol.md` 含项目级加载段；当全局 `.workflow/context/experience/roles/analyst.md` 与项目级 `{project-path}/experience/roles/analyst.md` 同名同标题时，role 加载链**优先**使用项目级版本（OQ-2 default A 落地）；提供单测 / dogfood TC 证明加载顺序与覆盖语义。

- **AC-06（工具项目级化）**：在下游用户仓 `{project-path}/tools/catalog/my-custom-tool.md` 新增工具，`harness tool-search my-custom` stdout 命中该工具；`tools-manager` 派发时按 OQ-2 default A 优先匹配项目级工具；`harness update` / `harness install --force-managed` 不删除该文件。

- **AC-07（dogfood 端到端 TC）**：tmpdir 模拟"项目级 constraints + experience + tools 各 1 文件"，跑完整链路：(i) `harness install --force-managed` → 项目级保留；(ii) `harness validate --contract user-write-protected-zones` → PASS；(iii) `harness validate --contract all` → PASS；(iv) 角色加载链优先项目级 → PASS。

- **AC-08（PetMallPlatform 真实验证）**：用户在 PetMallPlatform 仓库按 AC-01 ~ AC-07 步骤验证一遍，所有断言通过；`PetMallPlatform/{project-path}/...` 通过 `git commit` 跟随业务代码携带，团队成员 clone 后可读到项目级规则。

## Split Rules

> Phase 2（chg 拆分）由 analyst 承接，本 requirement.md 不预设 chg 边界。Phase 1 已识别的可能 chg 切面参考（仅供后续 Phase 2 拆分参考）：契约层（repository-layout + harness-manager 硬门禁五）/ helper 层（mirror + protected-zones 双豁免）/ 加载层（role-loading-protocol + tools-manager 项目级合并）/ 测试层（dogfood + 真实 PetMallPlatform 验证）。

- 各 chg 落地后跑 `harness validate --contract all` 全绿；
- 综合退出标准：AC-01 ~ AC-07 dogfood 全 PASS + AC-08 用户真实验证通过。

---

## OQ Verdicts（用户 2026-04-29 22:50 拍板，锁定）

| # | 用户决议 | 与 default-pick 对比 |
|---|---------|---------------------|
| **OQ-1** | **B-modified**：路径 = `artifacts/{branch}/project/{constraints,experience,tools}/`；同时在 `repository-layout.md` §2 白名单 + §3 落位段**显式添加豁免段**——三类项目级机器型文档允许入 artifacts/，**仅这三类**豁免，其他机器型文档严禁入 artifacts/ 不变。 | **改 default-pick A**（原推 `.workflow/project/`）：用户原话"制品包内"字面落到 artifacts/，以代码仓制品携带。 |
| OQ-2 | A：项目级覆盖全局 | 收 default |
| OQ-3 | A：constraints / experience / tools 三类（不动 roles/） | 收 default |
| OQ-4 | A：mirror 白名单 + protected-zones 双豁免 | 收 default |
| OQ-5 | A：不加专门 lint，文档警告 + done 抽查（lint 入 sug 池） | 收 default |

**`{project-path}` 占位符落定 = `artifacts/{branch}/project/`**。所有 AC 的 `{project-path}` 引用以此为准；scaffold_v2 mirror 不同步本路径下文件。

**契约改动锚点**：
- `.workflow/flow/repository-layout.md` §2 白名单**新增 1 段**：`artifacts/{branch}/project/{constraints,experience,tools}/` 三类项目级机器型文档豁免；
- `.workflow/flow/repository-layout.md` §3 / §3.2 顶部**新增豁免说明**：项目级三类豁免不破坏全局"机器型不入 artifacts/"原则；
- `.workflow/context/roles/harness-manager.md` 硬门禁五**例外白名单新增 1 条**：`artifacts/{branch}/project/`。
