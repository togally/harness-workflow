---
version: 1
owner: "stage-role.md 契约 2/3"
created_by: "chg-01（artifacts-layout 契约底座 + stage-role 路径同构改写）"
req: "req-39（对人文档家族契约化 + artifacts 扁平化）"
---

# artifacts-layout 契约底座

本文件是 `artifacts/` 仓库语义的**权威定义**：`artifacts/` 只装对人文档，按需求扁平组织，不出现机器型文档、不出现多层子目录。

本文件由 req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-01（artifacts-layout 契约底座 + stage-role 路径同构改写）新建，是后续 chg-02（validate_human_docs 重写）/ chg-03（requirement-review + planning 自检硬门禁代码化）/ chg-04（acceptance gate 强执行）/ chg-05（CLI 路径对齐扁平化 + scaffold mirror 同步）的公共语义基。

---

## 1. 扁平结构定义

**核心语义**：`artifacts/{branch}/requirements/{req-id}-{slug}/` 是**对人文档仓库**，目录下只有平铺文件（`.md` / `.sql` / `.pdf` 等白名单后缀），**不出现 `changes/` / `regressions/` 子目录**。

### 目录结构示例（req-39 及以后新规）

```
artifacts/
└── main/
    └── requirements/
        └── req-39-对人文档家族契约化-artifacts-扁平化/
            ├── 需求摘要.md                     # req 级，需求分析师产出
            ├── 交付总结.md                     # req 级，done 阶段产出
            ├── 决策汇总.md                     # req 级，ff --auto 产出
            ├── chg-01-变更简报.md              # chg 级，架构师产出
            ├── chg-01-实施说明.md              # chg 级，开发者产出
            ├── chg-02-变更简报.md
            ├── chg-02-实施说明.md
            ├── reg-01-回归简报.md              # regression 级，诊断师产出
            ├── deploy-prod.sql                 # 部署类 SQL 脚本
            ├── 部署文档.md                     # 部署操作手册
            └── 接入配置说明.md                 # 外部系统接入配置
```

**关键约束**：
- `artifacts/main/requirements/req-XX-slug/` 下**无 `changes/` 子目录**，对人文档全部平铺。
- `artifacts/main/requirements/req-XX-slug/` 下**无 `regressions/` 子目录**，回归简报同样平铺。
- 只有对人文档（见 §2 白名单）允许存入；机器型文档必须落 `.workflow/state/`（见 §3 迁移位）。

---

## 2. 对人文档白名单

**对人文档**定义：人可直接阅读、执行或签字的产物；区别于机器型文档（由 CLI / agent 读写、人无需直接操作）。

| 类型 | 文件名模式 | 粒度 | 产出角色 | 典型场景 |
|------|-----------|------|---------|---------|
| 需求摘要 | `需求摘要.md` | req 级 | 需求分析师（requirement-review） | 供业务方 / 用户快速了解需求目标与验收范围 |
| 变更简报 | `chg-NN-变更简报.md` | chg 级 | 架构师（planning） | 供 PM / 技术负责人了解某个变更的目标与方案 |
| 实施说明 | `chg-NN-实施说明.md` | chg 级 | 开发者（executing） | 供 reviewer / 测试了解实际做了什么 |
| 回归简报 | `reg-NN-回归简报.md` | regression 级 | 诊断师（regression） | 供用户了解回归问题诊断过程和修复结论 |
| 交付总结 | `交付总结.md` | req 级 | 主 agent（done） | 供管理层 / 用户一次性了解整个需求交付结果 |
| 决策汇总 | `决策汇总.md` | req 级 | 主 agent（ff --auto） | 供 reviewer 审核 ff 模式自动推进期间的所有决策 |
| SQL 脚本 | `*.sql` / `deploy-*.sql` | 按需 | 开发者 / 架构师 | 需人工执行的数据库变更脚本（DDL / DML / 初始化数据） |
| 部署文档 | `部署文档.md` / `deploy-*.md` | 按需 | 开发者 / SRE | 需人工操作的生产部署步骤、回滚手册 |
| 接入配置说明 | `接入配置说明.md` / `config-*.md` | 按需 | 架构师 / 开发者 | 外部系统 / 第三方平台接入时需人工配置的参数说明 |
| runbook | `runbook-*.md` | 按需 | SRE / 运维 | 生产事故处置 SOP、定期维护操作手册 |
| 手册 / 用户文档 | `manual-*.md` / `guide-*.md` | 按需 | 产品 / 开发者 | 需人阅读的功能使用说明、操作指南 |
| 合同附件 | `contract-*.md` / `*.pdf` | 按需 | 项目负责人 | 需人签字或存档的合同条款、SLA 文件 |
| 用量报告 | `耗时与用量报告.md` | req 级 | usage-reporter（req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-08（stage 耗时 + token 消耗统计 + usage-reporter 对人报告）） | 观察工作流效率与成本分布 |
| 其他对人产物 | 任意 `.md` / `.pdf` / `.docx` 等 | 按需 | 任意 | 兜底：其他需人执行或阅读的产物，由 planning 阶段声明并加入白名单 |

**注意**：
- `测试结论.md` / `验收摘要.md` 已由 req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-04（S-D 对人文档缩减）废止，**不在白名单内**；对应数据写入 `test-report.md` / `acceptance-report.md`（机器型）。
- 白名单是"允许存入 artifacts/" 的清单，不是"必须产出"的全量清单；具体每个 req 必须产出哪些，由各阶段角色退出条件和 `harness validate --human-docs` 约束。
- planning 阶段可扩展白名单（在 chg 计划中声明新类型），但不得把机器型文档纳入白名单。

---

## 3. 机器型文档迁移位

**机器型文档**定义：由 CLI / agent 写入、主要供工作流引擎 / agent 读取的结构化文档；人一般不直接操作。

### req 级迁移

| 机器型文档 | 旧路径（legacy，req-02 ~ req-38） | 新路径（新规，req-39+） |
|-----------|----------------------------------|----------------------|
| `requirement.md` | `artifacts/{branch}/requirements/{req-id}-{slug}/requirement.md` | `.workflow/state/requirements/{req-id}/requirement.md` |
| `testing-report.md` | `artifacts/.../requirements/{req-id}-{slug}/testing-report.md` | `.workflow/state/requirements/{req-id}/testing-report.md` |
| `acceptance-report.md` | `artifacts/.../requirements/{req-id}-{slug}/acceptance-report.md` | `.workflow/state/requirements/{req-id}/acceptance-report.md` |

### chg 级迁移

| 机器型文档 | 旧路径（legacy） | 新路径（新规，req-39+） |
|-----------|-----------------|----------------------|
| `change.md` | `artifacts/.../changes/{chg-id}-{slug}/change.md` | `.workflow/state/sessions/{req-id}/{chg-id}/change.md` |
| `plan.md` | `artifacts/.../changes/{chg-id}-{slug}/plan.md` | `.workflow/state/sessions/{req-id}/{chg-id}/plan.md` |
| `session-memory.md` | `artifacts/.../changes/{chg-id}-{slug}/session-memory.md` | `.workflow/state/sessions/{req-id}/{chg-id}/session-memory.md` |

### regression / session 级迁移

| 机器型文档 | 旧路径（legacy） | 新路径（新规，req-39+） |
|-----------|-----------------|----------------------|
| `regression.md` | `artifacts/.../changes/{chg-id}-{slug}/regression/{reg-id}/regression.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/regression.md` |
| `analysis.md` | `artifacts/.../changes/{chg-id}-{slug}/regression/analysis.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/analysis.md` |
| `decision.md` | `artifacts/.../changes/{chg-id}-{slug}/regression/decision.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/decision.md` |
| `meta.yaml` | `artifacts/.../changes/{chg-id}-{slug}/regression/meta.yaml` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/meta.yaml` |
| `required-inputs.md` | `artifacts/.../changes/{chg-id}-{slug}/regression/required-inputs.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/required-inputs.md` |
| `usage-log.yaml` | （无 legacy 路径；req-39+ 新增）| `.workflow/state/sessions/{req-id}/usage-log.yaml`（主 agent 调 `record_subagent_usage` 产生，chg-08（stage 耗时 + token 消耗统计 + usage-reporter 对人报告）新增）|

**注意**：机器型文档迁移由 chg-05（CLI 路径对齐扁平化 + scaffold mirror 同步）落地 CLI 行为；本 chg-01（artifacts-layout 契约底座 + stage-role 路径同构改写）只定义迁移目标位，实际搬家不在本 chg 范围内。

---

## 4. 命名前缀约定

**目的**：`artifacts/` 扁平目录下，同一 req 的多个 chg / reg 产出同类文档（如多份"变更简报"），必须用 `chg-NN-` / `reg-NN-` 前缀区分，避免同名冲突。

### 前缀规则

| 文档类型 | 命名模式 | 示例 |
|---------|---------|------|
| chg 级变更简报 | `chg-NN-变更简报.md` | `chg-01-变更简报.md`, `chg-02-变更简报.md` |
| chg 级实施说明 | `chg-NN-实施说明.md` | `chg-01-实施说明.md`, `chg-02-实施说明.md` |
| reg 级回归简报 | `reg-NN-回归简报.md` | `reg-01-回归简报.md`, `reg-02-回归简报.md` |
| req 级（唯一） | 直接用中文命名 | `需求摘要.md`, `交付总结.md`, `决策汇总.md` |
| 部署类 SQL | `deploy-YYYYMMDD.sql` | `deploy-20260424.sql` |
| 其他按需 | `{类型}-{描述}.md` 或按白名单模式 | `runbook-prod-restart.md` |

### 冲突规避示例

**错误示例（同名冲突）**：
```
artifacts/main/requirements/req-39-.../
├── 变更简报.md   # ← 哪个 chg 的？冲突！
└── 变更简报.md   # ← 只能保留一个
```

**正确示例（前缀区分）**：
```
artifacts/main/requirements/req-39-.../
├── chg-01-变更简报.md   # ← chg-01 的变更简报
├── chg-02-变更简报.md   # ← chg-02 的变更简报
└── chg-03-变更简报.md   # ← chg-03 的变更简报
```

---

## 5. 历史存量豁免

### 豁免范围

- **req-02（湖南 UAV MQTT 接入）~ req-37（阶段结束汇报简化：周转时不给选项，只停下 + 报本阶段结束 + 报状态）**：原有 `artifacts/` 结构（含 `changes/` 子目录）**全部保留**，不迁移、不删除、不改写；git log 自带历史分水岭。
- **req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）**：作为**混合过渡期样本**——已有的旧结构 `changes/chg-NN/` 原地保留；新规对人文档（`需求摘要.md` + `chg-NN-变更简报.md`）按新规追补平铺在 `artifacts/main/requirements/req-38-.../` 根目录（由 chg-06（req-38 对人文档按新扁平结构追补试点）完成）。

### 新规生效范围

- **req-39（对人文档家族契约化 + artifacts 扁平化）及以后**：严格执行本文件所有约束：
  - 新建 req 时 `artifacts/` 目录直接扁平，不建 `changes/` 子目录；
  - 机器型文档直接落 `.workflow/state/`，不进 `artifacts/`；
  - 对人文档命名严格按 §4 前缀约定。

### 禁止行为

- 禁止对 req-02 ~ req-37 的 `artifacts/` 历史结构执行 `mv` / `rm` / 重命名。
- 禁止因新规生效而回填历史对人文档（历史已有的按旧规留档，缺失的由各自 req 自行决定是否补）。
- 禁止把机器型文档写入 `artifacts/` 下任何路径（新规 req 严格执行）。
