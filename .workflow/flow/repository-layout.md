---
version: 2
owner: "stage-role.md 契约 2/3"
created_by: "req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ chg-01（repository-layout 契约底座（git mv + 三大子树 §2 重写））"
req: "req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））"
migrated_from: ".workflow/flow/artifacts-layout.md（req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-01（artifacts-layout 契约底座 + stage-role 路径同构改写）新建；req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ chg-01（repository-layout 契约底座（git mv + 三大子树 §2 重写））升格为全仓库三大子树权威契约）"
---

# repository-layout 全仓库布局契约

本文件是全仓库路径语义的**权威定义**，覆盖三大子树：`.workflow/state/`（runtime 真·实时数据）/ `.workflow/flow/`（权威工作流工件）/ `artifacts/`（对人可读签字执行产物）。

本文件由 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ chg-01（repository-layout 契约底座（git mv + 三大子树 §2 重写））从 `.workflow/flow/artifacts-layout.md` 升格重写，是后续 chg-02（CLI 路径迁移（FLOW_LAYOUT_FROM_REQ_ID + create_/archive_ 改写））/ chg-03（validate_human_docs 重写 + 白名单清理）/ chg-04（角色文件去路径化 + 删四类 brief 模板）/ chg-05（done.md 交付总结模板扩 §效率与成本）/ chg-06（harness-manager.md §3.6 Step 4 升级硬门禁）/ chg-07（dogfood 活证 + scaffold_v2 mirror + 收口）/ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）的公共语义基。

---

## 1. 三大子树语义总览

全仓库按"用途"划分三大子树，每类文档**只能**落在对应子树，不得越界：

| 子树 | 语义 | 典型内容 | 产出者 | 消费者 |
|------|------|---------|--------|--------|
| `.workflow/state/` | Runtime 真·实时数据。只装工作流引擎的瞬态运行时状态；**不**承载 req/chg/regression 周期工件（req-41+ 起）。 | `runtime.yaml` / `feedback/feedback.jsonl` / `action-log.md` / `experience/index.md` | harness CLI / 主 agent | 主 agent / harness CLI |
| `.workflow/flow/` | 权威工作流工件。包含本文件（布局契约）/ 流程定义文件（`stages.md` 等）/ **req 周期机器型文档**（req-41+ 落位，见 §3）/ 归档（`archive/{branch}/`）。 | `repository-layout.md` / `stages.md` / `requirements/{req-id}-{slug}/` 子树 / `archive/` | harness CLI / subagent | harness CLI / subagent / 主 agent |
| `artifacts/{branch}/` | 对人可读签字执行产物。只装人可直接阅读、执行或签字的产物；**不**出现机器型文档。 | raw `requirement.md` 副本 / `交付总结.md` / `决策汇总.md` / SQL / 部署文档 / 接入配置说明 / runbook / 手册 / 合同附件 | subagent（done / analyst） | 业务方 / PM / 运维 / 外部审阅者 |

### `.workflow/flow/requirements/` 子树结构（req-41+ 新位）

```
.workflow/flow/
└── requirements/
    └── {req-id}-{slug}/                    # 例：req-41-机器型工件回-flow-requirements/
        ├── requirement.md                  # req 权威机器型定义（主 agent / analyst 读写）
        ├── usage-log.yaml                  # subagent 调用 record_subagent_usage 产生
        ├── {req-id}.yaml                   # req yaml（含 stage_timestamps）
        ├── task-context/                   # req 级 task-context（可选）
        ├── changes/
        │   └── {chg-id}-{slug}/            # 例：chg-01-repository-layout-契约底座/
        │       ├── change.md               # chg 权威机器型定义
        │       ├── plan.md                 # 执行计划
        │       └── session-memory.md       # 执行记忆（executing 产出）
        └── regressions/
            └── {reg-id}-{slug}/            # 例：reg-01-xxx/
                ├── regression.md           # regression 定义
                ├── analysis.md
                ├── decision.md
                ├── meta.yaml
                └── session-memory.md
```

### `artifacts/{branch}/` 子树结构（对人产物）

```
artifacts/
└── main/
    └── requirements/
        └── {req-id}-{slug}/                # 扁平目录，无 changes/ 子目录
            ├── requirement.md              # raw authoritative 副本（外部审阅用，非引擎读写）
            ├── 交付总结.md                 # req 级，done 阶段产出
            ├── 决策汇总.md                 # req 级，ff --auto 产出
            ├── deploy-prod.sql             # 部署类 SQL 脚本（按需）
            ├── 部署文档.md                 # 部署操作手册（按需）
            ├── 接入配置说明.md              # 外部系统接入配置（按需）
            └── runbook-*.md               # SRE runbook（按需）
```

**关键约束**：
- `artifacts/main/requirements/{req-id}-{slug}/` 下**无 `changes/` 子目录**，对人文档全部平铺。
- `artifacts/main/requirements/{req-id}-{slug}/` 下**无 `regressions/` 子目录**，无四类 brief。
- 只有对人文档（见 §2 白名单）允许存入；机器型文档必须落 `.workflow/flow/requirements/` 子树（req-41+ 见 §3 权威落位）。

---

## 2. 对人文档白名单（artifacts/ 子树）

**对人文档**定义：人可直接阅读、执行或签字的产物；区别于机器型文档（由 CLI / agent 读写、人无需直接操作）。

| 类型 | 文件名模式 | 粒度 | 产出角色 | 典型场景 |
|------|-----------|------|---------|---------|
| raw requirement 副本 | `requirement.md` | req 级 | harness CLI（done 阶段 copy） | 供外部审阅者直接阅读需求全文；权威来源是 `.workflow/flow/requirements/{req-id}-{slug}/requirement.md`，不参与流程引擎读写 |
| 交付总结 | `交付总结.md` | req 级 | 主 agent（done） | 供管理层 / 用户一次性了解整个需求交付结果；含 §效率与成本段（chg-05（done.md 交付总结模板扩 §效率与成本）落地） |
| 决策汇总 | `决策汇总.md` | req 级 | 主 agent（ff --auto） | 供 reviewer 审核 ff 模式自动推进期间的所有决策 |
| SQL 脚本 | `*.sql` / `deploy-*.sql` | 按需 | 开发者 / 架构师 | 需人工执行的数据库变更脚本（DDL / DML / 初始化数据） |
| 部署文档 | `部署文档.md` / `deploy-*.md` | 按需 | 开发者 / SRE | 需人工操作的生产部署步骤、回滚手册 |
| 接入配置说明 | `接入配置说明.md` / `config-*.md` | 按需 | 架构师 / 开发者 | 外部系统 / 第三方平台接入时需人工配置的参数说明 |
| runbook | `runbook-*.md` | 按需 | SRE / 运维 | 生产事故处置 SOP、定期维护操作手册 |
| 手册 / 用户文档 | `manual-*.md` / `guide-*.md` | 按需 | 产品 / 开发者 | 需人阅读的功能使用说明、操作指南 |
| 合同附件 | `contract-*.md` / `*.pdf` | 按需 | 项目负责人 | 需人签字或存档的合同条款、SLA 文件 |
| 其他对人产物 | 任意 `.md` / `.pdf` / `.docx` 等 | 按需 | 任意 | 兜底：其他需人执行或阅读的产物，由 planning 阶段声明并加入白名单 |

**注意**：
- 四类 brief（req 级摘要 / chg 级对人简报 / chg 级对人说明 / regression 级对人简报）已由 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））废止（req-id ≥ 41 不再产出），**不在白名单内**。独立用量报告文件同步废止，效率数据并入 `交付总结.md §效率与成本段`（chg-05（done.md 交付总结模板扩 §效率与成本）落地）。
- `测试结论.md` / `验收摘要.md` 已由 req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-04（S-D 对人文档缩减）废止，**不在白名单内**；对应数据写入 `test-report.md` / `acceptance-report.md`（机器型）。
- 白名单是"允许存入 artifacts/" 的清单，不是"必须产出"的全量清单；具体每个 req 必须产出哪些，由各阶段角色退出条件和 `harness validate --human-docs` 约束。
- planning 阶段可扩展白名单（在 chg 计划中声明新类型），但不得把机器型文档纳入白名单。

---

## 3. 机器型文档权威落位（`.workflow/flow/requirements/{req-id}-{slug}/`）

**机器型文档**定义：由 CLI / agent 写入、主要供工作流引擎 / agent 读取的结构化文档；人一般不直接操作。

req-41+ 所有机器型工件统一落 `.workflow/flow/requirements/{req-id}-{slug}/` 子树。

### req 级落位

| 机器型文档 | 权威路径（req-41+ flow 新位） | 旧路径（req-39/40 state/ flat layout） | 旧路径（req-02 ~ req-38 legacy） |
|-----------|------------------------------|---------------------------------------|-------------------------------|
| `requirement.md` | `.workflow/flow/requirements/{req-id}-{slug}/requirement.md` | `.workflow/state/requirements/{req-id}/requirement.md` | `artifacts/{branch}/requirements/{req-id}-{slug}/requirement.md` |
| `testing-report.md` | `.workflow/flow/requirements/{req-id}-{slug}/testing-report.md` | `.workflow/state/requirements/{req-id}/testing-report.md` | `artifacts/.../requirements/{req-id}-{slug}/testing-report.md` |
| `acceptance-report.md` | `.workflow/flow/requirements/{req-id}-{slug}/acceptance-report.md` | `.workflow/state/requirements/{req-id}/acceptance-report.md` | `artifacts/.../requirements/{req-id}-{slug}/acceptance-report.md` |
| `usage-log.yaml` | `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml` | `.workflow/state/sessions/{req-id}/usage-log.yaml` | （无 legacy 路径）|
| `{req-id}.yaml`（含 stage_timestamps） | `.workflow/flow/requirements/{req-id}-{slug}/{req-id}.yaml` | `.workflow/state/requirements/{req-id}/{req-id}.yaml` | （无 legacy 路径）|

### chg 级落位

| 机器型文档 | 权威路径（req-41+ flow 新位） | 旧路径（req-39/40 state/ flat layout） |
|-----------|------------------------------|---------------------------------------|
| `change.md` | `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/change.md` | `.workflow/state/sessions/{req-id}/{chg-id}/change.md` |
| `plan.md` | `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/plan.md` | `.workflow/state/sessions/{req-id}/{chg-id}/plan.md` |
| `session-memory.md` | `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/session-memory.md` | `.workflow/state/sessions/{req-id}/{chg-id}/session-memory.md` |

### regression 级落位

| 机器型文档 | 权威路径（req-41+ flow 新位） | 旧路径（req-39/40 state/ flat layout） |
|-----------|------------------------------|---------------------------------------|
| `regression.md` | `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/regression.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/regression.md` |
| `analysis.md` | `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/analysis.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/analysis.md` |
| `decision.md` | `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/decision.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/decision.md` |
| `meta.yaml` | `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/meta.yaml` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/meta.yaml` |
| `session-memory.md` | `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/session-memory.md` | `.workflow/state/sessions/{req-id}/regressions/{reg-id}/session-memory.md` |

**注意**：机器型文档路径迁移由 chg-02（CLI 路径迁移（FLOW_LAYOUT_FROM_REQ_ID + create_/archive_ 改写））落地 CLI 行为（req-id ≥ 41 走 flow/ 新位，req-id ∈ [39, 40] 维持 state/ legacy fallback）；本 chg-01（repository-layout 契约底座（git mv + 三大子树 §2 重写））只定义权威落位，不执行 CLI 迁移。

---

## 4. 历史存量豁免与三段式分水岭

### 分水岭总览

| 区间 | 布局规则 | 机器型工件位 | 对人产物位 |
|------|---------|-------------|----------|
| req-02（湖南 UAV MQTT 接入）~ req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）（legacy） | 旧多层 brief 结构 | `artifacts/.../changes/{chg-id}/` 等旧位 | `artifacts/.../requirements/{req-id}-{slug}/` 含 `changes/` 子目录 |
| req-39（对人文档家族契约化 + artifacts 扁平化）~ req-40（flat layout 过渡） | 扁平对人文档 + state/ 机器型 | `.workflow/state/requirements/{req-id}/` / `.workflow/state/sessions/{req-id}/` | `artifacts/main/requirements/{req-id}-{slug}/` 扁平（无 `changes/` 子目录） |
| req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））+（flow/ 新位） | 本文件全约束 | `.workflow/flow/requirements/{req-id}-{slug}/`（本文件 §3 权威） | `artifacts/main/requirements/{req-id}-{slug}/` 扁平（仅 §2 白名单内） |

### 豁免细则

- **req-02（湖南 UAV MQTT 接入）~ req-37（阶段结束汇报简化：周转时不给选项，只停下 + 报本阶段结束 + 报状态）**：原有 `artifacts/` 结构（含 `changes/` 子目录 + 四类 brief）**全部保留**，不迁移、不删除、不改写；git log 自带历史分水岭。
- **req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）**：作为混合过渡期样本——已有的旧结构 `changes/chg-NN/` 原地保留；新规对人文档按扁平结构追补（req-38 / chg-06（req-38 对人文档按新扁平结构追补试点）完成）。
- **req-39（对人文档家族契约化 + artifacts 扁平化）/ req-40（活跃需求）**：机器型文档仍在 `.workflow/state/sessions/` + `.workflow/state/requirements/`（flat layout legacy fallback）；对人文档已按扁平规则落 `artifacts/`；两 req 的现有目录位**不迁移**，只有 req-41+ 走本文件 §3 flow/ 新位。

### 禁止行为

- 禁止对 req-02 ~ req-40 的 `artifacts/` / `state/` 历史结构执行 `mv` / `rm` / 重命名。
- 禁止因新规生效而回填历史对人文档（历史已有的按旧规留档，缺失的由各自 req 自行决定是否补）。
- 禁止把机器型文档写入 `artifacts/` 下任何路径（req-41+ 严格执行）。

---

## 5. 命名前缀约定（req-41+ 白名单范围）

**目的**：`artifacts/` 扁平目录下，req-41+ 只允许 §2 白名单内文件名；禁止用废止的四类 brief 命名。

### 前缀规则

| 文档类型 | 命名模式 | 示例 |
|---------|---------|------|
| raw requirement 副本 | `requirement.md` | `requirement.md` |
| req 级交付总结 | `交付总结.md` | `交付总结.md` |
| req 级决策汇总 | `决策汇总.md` | `决策汇总.md` |
| 部署类 SQL | `deploy-YYYYMMDD.sql` | `deploy-20260424.sql` |
| 其他按需 | `{类型}-{描述}.md` 或按白名单模式 | `runbook-prod-restart.md` |

### req-41+ 白名单范围说明

req-41+ 的 `artifacts/` 目录**只允许** §2 白名单内的文件名（`requirement.md` / `交付总结.md` / `决策汇总.md` / SQL / 部署 / 接入 / runbook / 手册 / 合同附件 / 其他按需声明类型）。

四类 brief（req 级摘要 / chg 级对人简报 / chg 级对人说明 / regression 级对人简报）及独立用量报告已由 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））废止，req-41+ **禁止**在 `artifacts/` 目录写入此类文件名。

req-02 ~ req-40 存量目录中已有旧式文件名的，按旧规原地保留（历史豁免，见 §4）。

---

## 6. 参考

- req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））§3.1 Scope-共骨架：顶层契约扩管 + 角色文件去路径化。
- req-41 §5.2 推荐 chg DAG：chg-01（契约底座）→ chg-02（CLI 路径迁移）/ chg-03（validate 重写）/ chg-04（角色去路径化）→ chg-05（done 扩段）/ chg-06（harness-manager 硬门禁）→ chg-07（dogfood 收口）。
- reg-01（artifacts 布局语义复核：需求文档归属 + flow/requirements 应否复用）：用户原话——"绝对不应该 requirements 和 change 都跑到制品仓库去"，驱动本 req-41 立项。
