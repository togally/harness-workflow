# req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致）） — Audit 报告

## § 1 元信息

| 字段 | 值 |
|------|----|
| 审计时间戳 | 2026-04-23（本 chg-01 执行时工作树状态；精确 sha 见 commit log） |
| 审计执行者 | chg-01（audit 报告（Yh-platform + 本仓库 live vs scaffold_v2 全量 drift 清单））executing 角色（Sonnet 4.6） |
| 审计基准命令 | 见 § 7 附录 1（`diff -rq .workflow/ src/harness_workflow/assets/scaffold_v2/.workflow/` + 白名单 grep -vE 排除） |
| 实测命中数（排除白名单后） | 39 行（含 archive/backup/stage/flow/state 等"仅 live"路径——这些在白名单内但 grep 模式不完全拦截；真实 A 类+B 类 drift = 27+2 = 29，其余均为白名单内运行时路径） |
| 说明 | 实测命中 39 是因为 grep -vE 的模式是子串匹配；`Only in .workflow: archive`、`Only in .workflow/context: backup`、`Only in .workflow/context/experience: stage`、`Only in .workflow/flow: archive/requirements/suggestions`、`Only in .workflow/state: bugfixes/feedback/requirements/sessions` 这 10 行属于 C 类白名单内路径，仍被输出（`grep -vE` 未覆盖这些"仅路径名"格式行）；真实需修复 drift = 29 项（A 类 27 + B 类 2）。 |

## § 2 总览

| 分类 | 数量 | 说明 |
|------|------|------|
| A 类（live 比 mirror 新，live → mirror 方向修复） | 27 项 | mirror 缺文件或内容旧于 live |
| B 类（mirror 比 live 新，mirror → live 方向修复） | 2 项 | live 缺文件（mirror 有），需反向拉回 |
| C 类白名单（仅 live 存在，预期不动） | 12 条 | 运行时数据 / 历史归档，跨项目无意义 |
| Yh-platform 缺失（only-in-scaffold，install 未推送） | 2 项 | install_repo() 未全量推送 scaffold_v2 |
| Yh-platform 内容旧版（Apr-19 时间戳停滞） | ~16 项 | install 对存量项目从未全量同步 |

## § 3 A 类清单（live → mirror，27 项）

> reconcile 方向：live 内容覆写到 `src/harness_workflow/assets/scaffold_v2/.workflow/` 同名路径。
> 全部由 chg-03（历史漂移 reconcile（live → scaffold_v2 mirror 27+ 文件 + B 类 mirror → live 2 文件））执行，除 A17 由 chg-02（install_repo sync 契约扩展（覆盖 context/tools/evaluation/flow，加 self-audit + 单测）+ harness-manager 硬门禁五保护面扩展）同 commit 闭合。

| # | 路径 | 漂移形态 | 推断成因 | reconcile 方向 | 关联 chg |
|---|------|---------|---------|--------------|---------|
| A1 | `.workflow/context/checklists/review-checklist.md` | 内容差异（live 多"契约 7 校验"段） | 历史改 live 未同步 mirror | live → mirror | chg-03 |
| A2 | `.workflow/context/experience/index.md` | 内容差异（live 多 `## regression` 段 + 4 条 reg 索引） | 经验沉淀只写了 live | live → mirror | chg-03 |
| A3 | `.workflow/context/experience/regression/reg-01.md` | mirror 缺文件 | 经验沉淀漏同步 | live → mirror（cp 创建） | chg-03 |
| A4 | `.workflow/context/experience/regression/reg-02.md` | mirror 缺文件 | 经验沉淀漏同步 | live → mirror（cp 创建） | chg-03 |
| A5 | `.workflow/context/experience/regression/reg-03.md` | mirror 缺文件 | 经验沉淀漏同步 | live → mirror（cp 创建） | chg-03 |
| A6 | `.workflow/context/experience/regression/reg-04.md` | mirror 缺文件 | 经验沉淀漏同步 | live → mirror（cp 创建） | chg-03 |
| A7 | `.workflow/context/experience/roles/acceptance.md` | live 多 2 条经验（harness validate 口径 / git stash 复跑） | 经验沉淀只写了 live | live → mirror | chg-03 |
| A8 | `.workflow/context/experience/roles/executing.md` | live 多 5 条经验（runtime 字段双保 / 路径 slug / managed-state 判据 / agent 作用域 / 路径常量迁移） | 经验沉淀只写了 live | live → mirror | chg-03 |
| A9 | `.workflow/context/experience/roles/planning.md` | 内容差异 | 经验沉淀只写了 live | live → mirror | chg-03 |
| A10 | `.workflow/context/experience/roles/regression.md` | 内容差异 | 经验沉淀只写了 live | live → mirror | chg-03 |
| A11 | `.workflow/context/experience/roles/requirement-review.md` | 内容差异 | 经验沉淀只写了 live | live → mirror | chg-03 |
| A12 | `.workflow/context/experience/roles/testing.md` | 内容差异 | 经验沉淀只写了 live | live → mirror | chg-03 |
| A13 | `.workflow/context/experience/tool/harness.md` | 内容差异 | 经验沉淀只写了 live | live → mirror | chg-03 |
| A14 | `.workflow/context/index.md` | 内容差异 | 改 live 未同步 mirror | live → mirror | chg-03 |
| A15 | `.workflow/context/roles/ROLE-TEMPLATE.md` | 内容差异 | 改 live 未同步 mirror | live → mirror | chg-03 |
| A16 | `.workflow/context/roles/directors/technical-director.md` | 内容差异 | 改 live 未同步 mirror | live → mirror | chg-03 |
| A17 | `.workflow/context/roles/harness-manager.md` | 内容差异（mirror 缺 req-33（install / update 命令合并） / chg-01 关于 install 吸收 update 的更新 + project-overview 产物段） | 改 live 未同步 mirror | live → mirror（同步更新硬门禁五覆盖范围） | chg-02（同 commit 闭合） |
| A18 | `.workflow/context/roles/role-loading-protocol.md` | 内容差异 | 改 live 未同步 mirror | live → mirror | chg-03 |
| A19 | `.workflow/context/roles/tools-manager.md` | 内容差异 | 改 live 未同步 mirror | live → mirror | chg-03 |
| A20 | `.workflow/evaluation/acceptance.md` | 内容差异（live 反映 req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界）） / chg-03 testing/acceptance 职责精简） | 改 live 未同步 mirror | live → mirror | chg-03 |
| A21 | `.workflow/evaluation/testing.md` | 内容差异（live 多 R1 / revert / 契约 7 / req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet）） / req-30（slug 沟通可读性增强：全链路透出 title）五项扫描章节） | 改 live 未同步 mirror | live → mirror | chg-03 |
| A22 | `.workflow/flow/stages.md` | 内容差异（live 多 req-31（角色功能优化整合与交互精简） / chg-01 legacy 注释段） | 改 live 未同步 mirror | live → mirror | chg-03 |
| A23 | `.workflow/state/experience/index.md` | 内容差异 | 经验沉淀只写了 live | live → mirror | chg-03 |
| A24 | `.workflow/tools/catalog/api-document-upload.md` | mirror 缺文件 | req-34（新增工具 api-document-upload（首实现 apifox MCP，可拔插）+ 修复 scaffold_v2 mirror 漂移（project-reporter 系列漏同步））新增工具漏同步 | live → mirror（cp 创建） | chg-03 |
| A25 | `.workflow/tools/catalog/harness-export-feedback.md` | 内容差异（live 已迁到 `.workflow/state/feedback/` 路径表述，mirror 仍写 `.harness/feedback.jsonl`） | 改 live 未同步 mirror | live → mirror | chg-03 |
| A26 | `.workflow/tools/index/keywords.yaml` | 内容差异（live 多 `api-document-upload` 5 条 keyword） | req-34（新增工具 api-document-upload + 修复 scaffold_v2 mirror 漂移）新增工具索引漏同步 | live → mirror | chg-03 |
| A27 | `.workflow/tools/index/missing-log.yaml` | 内容差异（live 累积 2 条 query 历史，mirror 是空 `[]`） | 运行时累积，应清空回模板态 | live → mirror，但 mirror 内容重置为 `queries: []`（运行时累积清空回模板态），live 保持不变 | chg-03 |

## § 4 B 类清单（mirror → live，2 项）

> reconcile 方向：mirror 内容覆写到 live `.workflow/` 同名路径（live 缺文件，从 mirror 拉回）。
> 全部由 chg-03（历史漂移 reconcile（live → scaffold_v2 mirror 27+ 文件 + B 类 mirror → live 2 文件））执行。

| # | 路径 | 漂移形态 | 推断成因 | reconcile 方向 | 关联 chg |
|---|------|---------|---------|--------------|---------|
| B1 | `.workflow/context/checklists/role-inheritance-checklist.md` | live 缺文件 | 历史 mirror 改了未拉回 live，或 live 误删 | mirror → live（cp 创建） | chg-03 |
| B2 | `.workflow/context/team/development-standards.default.md` | live 缺文件（关键 fallback，stage-role.md 显式声明加载） | live 误删 / 漏拉回 | mirror → live（cp 创建） | chg-03 |

## § 5 C 类白名单（仅 live 存在，预期不动，12 条）

以下路径在 live `.workflow/` 存在但 scaffold_v2 mirror 中没有，属于运行时数据 / 历史归档，**不算漂移，不纳入修复范围**，承 req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致）） requirement.md §2.3 C 段 + §7 E-1 default-pick A。

- `.workflow/archive/`
  *归档需求容器（各 req 归档后移入此处），仅本项目积累的历史归档，跨项目语义不通用，铺到新项目无意义。*

- `.workflow/context/backup/legacy-cleanup/`
  *迁移备份区，仅本项目的历史迁移产物，跨项目无意义且可能覆盖新项目的同名目录。*

- `.workflow/flow/archive/`
  *flow 归档目录（已关闭的 flow 快照），仅本项目历史积累，跨项目语义不通用。*

- `.workflow/flow/requirements/`
  *requirement.md 文档汇集（每个需求在 flow 的视图），内容与项目强绑定，铺到新项目会把本项目的需求内容带到新项目。*

- `.workflow/flow/suggestions/`
  *建议文档汇集（sug-* 条目），同上，内容与项目强绑定。*

- `.workflow/state/bugfixes/`
  *bugfix 运行时状态（bugfix-* state 文件），每次会话累积，仅本项目历史，新项目应从零开始。*

- `.workflow/state/feedback/`
  *feedback.jsonl 运行时累积数据，每次 `harness feedback` 追加，跨项目无意义（feedback 是针对本项目工作流的反馈）。*

- `.workflow/state/requirements/`
  *requirement 运行时状态（各 req-* 的 state 文件），内容与项目强绑定，不能复制到新项目。*

- `.workflow/state/sessions/`
  *session memory 运行时累积（各阶段 session-memory.md），每次会话写入，仅本项目历史，新项目从零开始。*

- `.workflow/state/runtime.yaml`
  *当前 stage 指针 + 活跃需求 + ff_mode 等运行时状态，新项目必须从初始状态开始，不能继承本项目的 runtime 状态。*

- `.workflow/state/action-log.md`
  *action 累积日志（每次 harness 命令追加一条），仅本项目历史，新项目应从空日志开始。*

- `.workflow/context/experience/stage/`
  *stage 经验沉淀（stage-scoped，仅本项目在 stage 维度积累的经验），与具体项目上下文强绑定，不适合铺到新项目（新项目应从无经验开始，自行积累）。*

## § 6 Yh-platform 真实存量项目证据

> 数据源：req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致）） requirement.md §9 + §9.1 + §9.2。
> 用户 2026-04-23 提供 `/Users/jiazhiwei/IdeaProjects/Yh-platform` 作为真实存量项目 fixture。本 chg 不真跑，记录审计发现。

### § 6.1 缺失（only-in-scaffold，Yh-platform 没装上）

| # | 路径 | 关联需求 |
|---|------|---------|
| YH-M1 | `context/role-model-map.yaml` | req-29（角色→模型映射（开放型角色用 Opus 4.7，执行型角色用 Sonnet）） chg-01 引入 |
| YH-M2 | `context/roles/project-reporter.md` | req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入） chg-01 引入 |

> 这 2 个文件在 scaffold_v2 mirror 中存在，但 Yh-platform 没有（`diff -rq Yh-platform/.workflow/context scaffold_v2/.workflow/context` 命中）。
> **这证明 install_repo() 的 sync 逻辑根本没把 scaffold_v2 全量推下去**——否则 Yh-platform 应当在最近一次 install 后拿到这 2 个文件（chg-02（install_repo sync 契约扩展）真正要修的核心）。

### § 6.2 内容不同（Yh-platform 旧版 vs scaffold_v2 新版，时间戳停在 Apr 19）

| # | 路径 | 说明 |
|---|------|------|
| YH-D1 | `context/index.md` | req-29（角色→模型映射）chg-02 加 model 列 |
| YH-D2 | `context/roles/acceptance.md` | req-29..35 系列更新，timestamp Apr 19 vs Apr 22-23 |
| YH-D3 | `context/roles/base-role.md` | 同上 |
| YH-D4 | `context/roles/directors/technical-director.md` | 同上 |
| YH-D5 | `context/roles/done.md` | 同上 |
| YH-D6 | `context/roles/executing.md` | 同上 |
| YH-D7 | `context/roles/harness-manager.md` | 同上 |
| YH-D8 | `context/roles/planning.md` | 同上 |
| YH-D9 | `context/roles/regression.md` | 同上 |
| YH-D10 | `context/roles/requirement-review.md` | 同上 |
| YH-D11 | `context/roles/stage-role.md` | 同上 |
| YH-D12 | `context/roles/testing.md` | 同上（共 11 个角色文件旧版） |
| YH-D13 | `context/experience/roles/acceptance.md` | 经验沉淀，Apr 19 旧版 |
| YH-D14 | `context/experience/roles/executing.md` | 同上 |
| YH-D15 | `context/experience/roles/regression.md` | 同上 |
| YH-D16 | `context/experience/roles/testing.md` | 同上（4 个经验文件旧版） |
| YH-D17 | `tools/catalog/harness-export-feedback.md` | 路径表述旧（`.harness/feedback.jsonl`），live 已迁移 |

共 ~17 项旧版差异（含上方 YH-D1..D17）。

### § 6.3 Yh-platform 独有（不该删）

- `context/experience/stage/`（用户项目本地积累的 stage 经验，承 § 5 白名单第 12 条，不应铺回 scaffold_v2 mirror，也不应在 install 时覆盖）。

### § 6.4 这证明了什么

1. **`harness install` 对 Yh-platform 从未真正全量同步过** —— 否则 Apr 19 timestamps 不该停在那里（req-29..35 系列在 Apr 22-23 落地，Yh-platform 未更新）。
2. **即使加了硬门禁五（req-34（新增工具 api-document-upload + 修复 scaffold_v2 mirror 漂移（project-reporter 系列漏同步）） / chg-04），存量项目不主动跑 install 也不会 reconcile** —— 硬门禁五管"未来新改动 live → mirror"，不修存量项目与 mirror 的历史漂移。
3. **缺失文件（role-model-map.yaml / project-reporter.md）证明 install_repo() 的 sync 逻辑根本没把 scaffold_v2 全量推下去**——这才是 chg-02（install_repo sync 契约扩展（覆盖 context/tools/evaluation/flow，加 self-audit + 单测）+ harness-manager 硬门禁五保护面扩展）真正要修的核心。

---

## § 7 附录 1：审计实跑命令与白名单 grep

```bash
# A. 全量 drift（含白名单）
diff -rq .workflow/ src/harness_workflow/assets/scaffold_v2/.workflow/

# B. 已剔除白名单的真实 drift（本 req 待修目标）
diff -rq .workflow/ src/harness_workflow/assets/scaffold_v2/.workflow/ \
  | grep -vE "(state/sessions|state/requirements|state/bugfixes|state/feedback|state/runtime\.yaml|state/action-log\.md|flow/archive|flow/requirements|flow/suggestions|context/backup|context/experience/stage|workflow/archive)"

# C. 端到端自证（chg-04（端到端自证双层（mktemp 干净空目录 + Yh-platform 真实存量项目 backup-then-install-then-diff）） acceptance）
TMP=$(mktemp -d); cp -R . "$TMP/repo"; cd "$TMP/repo" && python -m harness_workflow.cli install
diff -rq "$TMP/repo/.workflow/" src/harness_workflow/assets/scaffold_v2/.workflow/ \
  | grep -vE "(state/sessions|state/requirements|state/bugfixes|state/feedback|state/runtime\.yaml|state/action-log\.md|flow/archive|flow/requirements|flow/suggestions|context/backup|context/experience/stage|workflow/archive|tools/index/missing-log\.yaml)"
# 期望：空输出
```

> **注意**：grep 模式是子串匹配；`Only in .workflow: archive` 等"仅路径名"格式行在某些 grep 实现中可能不被完整过滤，实际执行时需逐行核对是否属于白名单。

## § 8 附录 2：Yh-platform 实跑命令模板

> `<YH_PLATFORM_ROOT>` 实际值见 requirement.md §9 当时记录（`/Users/jiazhiwei/IdeaProjects/Yh-platform`）。本 chg 不真跑，真跑落在 chg-04（端到端自证双层（mktemp 干净空目录 + Yh-platform 真实存量项目 backup-then-install-then-diff））且需用户显式 confirm。

```bash
# Yh-platform audit（只读，不改文件）
diff -rq <YH_PLATFORM_ROOT>/.workflow/context src/harness_workflow/assets/scaffold_v2/.workflow/context
diff -rq <YH_PLATFORM_ROOT>/.workflow/tools src/harness_workflow/assets/scaffold_v2/.workflow/tools

# Yh-platform install（chg-04 Layer 2，需用户 confirm 后才跑）
cp -R <YH_PLATFORM_ROOT>/.workflow <YH_PLATFORM_ROOT>/.workflow.backup-req-36
cd <YH_PLATFORM_ROOT> && harness install
diff -rq <YH_PLATFORM_ROOT>/.workflow/ src/harness_workflow/assets/scaffold_v2/.workflow/ \
  | grep -vE "(state/sessions|state/requirements|state/bugfixes|state/feedback|state/runtime\.yaml|state/action-log\.md|flow/archive|flow/requirements|flow/suggestions|context/backup|context/experience/stage|workflow/archive|tools/index/missing-log\.yaml)"
# 期望：空输出（或仅 Yh-platform 用户自定义内容，标 "user-customized, expected"）
```

## § 9 附录 3：白名单 12 条逐条理由

**判据原则**：以下文件属于"运行时累积 / 历史归档 / 项目专属"数据，**不属于模板态文件**，不应铺到新项目（scaffold_v2 mirror 的职责是提供模板态文件，非运行时数据）。

| # | 白名单路径 | 判据类型 | 判据理由 |
|---|-----------|---------|---------|
| C1 | `.workflow/archive/` | 历史归档 | 每个 req 完成后 `harness archive` 移入此处；内容与具体项目强绑定（含本项目所有历史需求文档），铺到新项目会让新项目"继承"一套别人的历史需求，完全无意义且容量巨大。 |
| C2 | `.workflow/context/backup/legacy-cleanup/` | 迁移备份区 | 历史迁移产物，仅本项目做了特定迁移操作才有，新项目无需此目录（新项目从干净状态开始，无需兼容任何历史迁移）。 |
| C3 | `.workflow/flow/archive/` | 历史归档 | flow 归档快照，内容与项目历史强绑定，跨项目无意义。 |
| C4 | `.workflow/flow/requirements/` | 项目专属内容 | 各 req 的 requirement.md 在 flow 的视图；内容是本项目的需求文档，绝对不应铺到另一个项目。 |
| C5 | `.workflow/flow/suggestions/` | 项目专属内容 | 各 sug-* 的建议文档，同上，内容与项目强绑定。 |
| C6 | `.workflow/state/bugfixes/` | 运行时状态 | bugfix-* 的 state 文件，每次 `harness bugfix` 时创建，记录本项目的 bugfix 状态；新项目从零 bugfix 开始。 |
| C7 | `.workflow/state/feedback/` | 运行时累积 | `feedback.jsonl` 是 `harness feedback` 每次追加的运行时反馈数据，仅对本项目工作流有意义；新项目无历史反馈。 |
| C8 | `.workflow/state/requirements/` | 运行时状态 | 各 req-* 的运行时 state 文件（stage / status / timestamps 等），与本项目需求周期绑定；铺到新项目会让新项目"以为"自己已经完成了本项目的所有需求，造成 runtime 混乱。 |
| C9 | `.workflow/state/sessions/` | 运行时累积 | session-memory.md 每次 agent 会话写入，记录本项目每个需求每个阶段的执行记忆；新项目无任何历史 session。 |
| C10 | `.workflow/state/runtime.yaml` | 运行时指针 | 当前需求、当前 stage、ff_mode 等运行时状态；新项目必须从 `current_requirement: ""` / `stage: "open"` 初始态开始。 |
| C11 | `.workflow/state/action-log.md` | 运行时累积日志 | 每次 harness 命令追加一条记录；新项目应从空日志开始，继承别项目的日志会造成操作历史混乱。 |
| C12 | `.workflow/context/experience/stage/` | 项目专属经验 | stage-scoped 经验沉淀，内容是本项目在 stage 维度积累的具体经验（含该项目的特定架构决策、边界案例等）；与具体项目上下文强绑定，新项目无需继承，且可能造成误导（新项目上下文完全不同）。 |
