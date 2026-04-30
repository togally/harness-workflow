---
id: playbook-layout
version: 1.0
owner: req-55
created_by: chg-01
created_at: 2026-04-30
---

# playbook-layout 路书目录骨架契约
路书根目录 = `artifacts/project/playbooks/`（沿用 req-51（项目级规则-经验-工具支持从制品引入）/ req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）项目级承载层规范，OQ-1 决策来源 = req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-01（路书目录骨架契约））

本文件是 req-55（项目路书(Playbook)体系——项目地图+代码导航）的**结构契约底座**，定义路书目录骨架、各文件字段规范、跨领域归属规则、AUTO 自动区段语义与校验锚点。不含 CLI 实现（由 chg-03/04/05 负责）。

---

## §1 顶层文件契约

> 路书根目录 = `artifacts/project/playbooks/`

路书顶层目录结构：

```
artifacts/project/playbooks/
├── overview.md          # 项目概览地图
├── architecture.md      # 架构总览 + 技术栈
├── runbook.md           # 运维 / 操作手册入口
├── code-map.md          # 代码结构地图 + 模块索引
└── domains/
    └── {领域名}/
        ├── README.md         # 领域概览（agent 加载入口）
        ├── code.md           # 领域代码清单（AUTO 刷新）
        ├── data-model.md     # 领域数据模型
        └── notes.md          # 领域补充笔记 / 跨领域归属
```

### 1.1 overview.md — 项目概览地图

**用途**：一句话说明项目是什么、给谁用、解决什么问题；agent 加载路书时**首先**读取。

**内容字段**：
- `## 项目名称`：项目全名（必填）
- `## 用途描述`：≤ 3 句话描述项目用途和目标用户
- `## 技术决策摘要`：关键架构选型（语言 / 框架 / 存储），≤ 5 条
- `## 活跃领域列表`：当前正在开发的 domain 名称列表（<!-- AUTO:DOMAIN_LIST --> 区段）
- `## 最近变更`：最近 3 次重要 req/bugfix 概述（human-authored，非 AUTO）

**写作原则**：
- 简洁第一：每节 ≤ 5 行，不引入完整 API 文档
- 路书只读：agent 仅读取，不直接修改；刷新由 `harness playbook-refresh` 执行
- 活跃领域列表通过 AUTO 区段自动维护，不手工编辑

**AUTO 区段**：`<!-- AUTO:DOMAIN_LIST -->` 区段由 `harness playbook-refresh` 维护（见 §4）

---

### 1.2 architecture.md — 架构总览

**用途**：描述系统技术栈、顶层组件关系、关键依赖；chg 实现前 agent 在此查全局架构背景。

**内容字段**：
- `## 技术栈`（<!-- AUTO:STACK --> 区段）：语言版本 / 框架 / 构建工具，由 refresh 扫 pyproject.toml / package.json 等写入
- `## 目录结构`（<!-- AUTO:LAYOUT --> 区段）：顶层目录树，由 refresh 扫实际 fs 写入
- `## 常用脚本`（<!-- AUTO:SCRIPTS --> 区段）：Makefile / scripts/ / package.json scripts，由 refresh 写入
- `## 组件关系`：人工描述子系统间调用关系，不含 AUTO 区段
- `## 关键依赖`：列主要三方依赖及其用途（人工维护）

**写作原则**：
- AUTO 区段只在 `harness playbook-refresh` 执行时替换；其他节 human-authored
- 不重复 domains/ 内容；architecture.md 描述"全局视图"，domain code.md 描述"领域视图"

---

### 1.3 runbook.md — 运维操作手册入口

**用途**：汇聚常见操作命令、部署步骤、CI/CD 配置等运维关注点；SRE / 开发者即时查阅。

**内容字段**：
- `## 快速启动`：本地开发环境启动命令（必填）
- `## 测试命令`：测试套件运行命令（必填）
- `## 部署步骤`：生产 / 预发环境部署流程（按需）
- `## 常见问题排查`：FAQ / troubleshooting guide（按需）

**写作原则**：
- 全部 human-authored，不含 AUTO 区段
- 命令必须可直接复制执行（可含注释，但语法正确）

---

### 1.4 code-map.md — 代码结构地图

**用途**：列出所有重要模块 / 文件路径及其职责；agent 据此定向跳转，减少全局扫描。

**内容字段**：
- `## 模块索引`（<!-- AUTO:DOMAIN_FILES --> 区段）：domains/ 各领域代码文件汇总，由 refresh 扫 domains/*/code.md 写入
- `## 入口文件`：main / CLI 入口文件路径 + 一句话描述（human-authored）
- `## 配置文件`：关键配置文件路径（human-authored）
- `## 测试目录`：测试文件位置约定（human-authored）

**写作原则**：
- `## 模块索引` 为 AUTO 区段，不手工编辑
- domains/ 子目录与 code-map.md 登记必须互引（任一缺失 = 漂移，见 §5 C-05）

---

## §2 domains/ 子树契约

每个业务领域对应一个子目录 `domains/{领域名}/`，含以下 4 件套：

### 2.1 README.md — 领域概览

**用途**：agent 加载某领域时**首先**读取；一句话说明该领域的职责边界。

**字段规范**：
- `## 领域名称`：与目录名对应（必填）
- `## 职责描述`：≤ 3 句描述该领域处理什么业务（必填）
- `## 关键文件`：该领域最重要的 2-3 个文件路径（human-authored）
- `## 依赖领域`：本领域依赖的其他领域（如有，可为空）

**字段规范约束**：
- 领域名与目录名必须一致（`harness playbook-check` 验证）
- `## 职责描述` 不得为空（check 触发 `KEYWORD_COVERAGE` 漂移类型）

---

### 2.2 code.md — 领域代码清单

**用途**：列出本领域所有代码文件路径 + 一句话职责描述；`code-map.md` 的 AUTO 区段依赖此文件。

**字段规范**：
- 文件格式：Markdown 列表，每行 `- \`{相对路径}\`：{职责描述}`
- 相对路径：相对于仓库根目录
- `## 文件列表`（<!-- AUTO:DOMAIN_FILES --> 区段）：由 `harness playbook-refresh` 扫 `src/{领域}/` 或对应目录自动生成

**字段规范约束**：
- 每条路径引用的文件必须真实存在（check 触发 `CODE_MD_REF_BROKEN` 漂移类型）
- AUTO 区段格式必须配对（见 §5 C-04）

---

### 2.3 data-model.md — 领域数据模型

**用途**：描述该领域的核心数据结构、数据库表、schema 定义；agent 修改数据层前优先查阅。

**字段规范**：
- `## 核心数据结构`：主要 class / struct / schema 名称 + 字段说明
- `## 数据库表`（如适用）：表名 + 主键 + 关键索引 + 用途
- `## 数据流向`：数据创建 → 消费的简要流程（可选）

**字段规范约束**：
- 全部 human-authored，不含 AUTO 区段
- 空领域（无数据模型）可以只保留节标题，不作空文件

---

### 2.4 notes.md — 领域补充笔记

**用途**：跨领域内容的归属落点（见 §3）；其他不适合放上述 3 个文件的补充信息。

**字段规范**：
- `## 跨领域笔记`：涉及本领域且从其他领域调用的流程说明
- `## 待决策事项`：未解决的技术选型 / 架构问题（可选）
- `## 历史背景`：重要的架构决策历史（可选）

**字段规范约束**：
- 全部 human-authored
- 跨领域流程**归调用方** `notes.md`，不复制到被调用方（见 §3）

---

## §3 跨领域内容归属规则

当一个业务流程跨越多个领域时，文档归属遵守以下规则：

### 规则 1：归调用方

跨多领域的流程文档，归**发起方（调用方）**领域的 `notes.md`，不归被调用方。

> 示例：订单服务调用支付服务，"下单 → 支付流程"文档归订单领域 `notes.md`，不入支付领域 `notes.md`。

### 规则 2：不复制内容

各领域内容不得互相复制。被调用领域只需在自身 `README.md` 描述接口契约；跨域流程详情仅在调用方 `notes.md` 存放一份。

> 目的：避免两份内容漂移导致不一致，agent 只读一处权威来源。

### 规则 3：全局内容归 architecture.md

横跨 3 个及以上领域的内容（如系统级限流策略、全局错误码约定、跨服务链路追踪配置），归 `architecture.md`，不分散到各 domain。

---

## §4 AUTO 区段规约

AUTO 区段使用 HTML 注释配对定界：

```
<!-- AUTO:区段名 -->
...自动生成内容...
<!-- /AUTO:区段名 -->
```

**规则**：
- AUTO 区段由 `harness playbook-refresh` 统一写入，人工不得手动修改
- 区段标记必须配对（`<!-- AUTO:X -->` 与 `<!-- /AUTO:X -->`），见 §5 C-04
- refresh 只替换 AUTO 区段内容，区段外字节不变，见 §5 C-01

### AUTO 区段表

| 区段标记 | 所在文件 | 内容来源 | 刷新触发 | 破损语义 |
|---------|---------|---------|---------|---------|
| <!-- AUTO:STACK --> | `architecture.md` | 扫 `pyproject.toml` / `package.json` / `requirements.txt` 提取语言版本 + 主要依赖 | `harness playbook-refresh` 或文件变更钩子 | 破损（区段不配对或内容为空）→ abort refresh，报 `STACK_SEGMENT_BROKEN` |
| <!-- AUTO:SCRIPTS --> | `architecture.md` | 扫 `Makefile` / `scripts/` / `package.json scripts` 提取常用命令 | `harness playbook-refresh` | 破损 → abort，报 `SCRIPTS_SEGMENT_BROKEN` |
| <!-- AUTO:LAYOUT --> | `architecture.md` | 扫仓库根目录一层 `ls -1`，过滤 `.git` / `__pycache__` 等噪声 | `harness playbook-refresh` | 破损 → abort，报 `LAYOUT_SEGMENT_BROKEN` |
| <!-- AUTO:DOMAIN_FILES --> | `code-map.md` 与各 `domains/*/code.md` | 扫 `src/{领域}/` 或 domains/ 配置映射目录，枚举 `.py` / `.ts` / `.go` 等代码文件 | `harness playbook-refresh` | 破损 → abort，报 `DOMAIN_FILES_SEGMENT_BROKEN`；漂移（文件路径失效）→ `playbook-check` 报 `CODE_MD_REF_BROKEN` |
| <!-- AUTO:DOMAIN_LIST --> | `overview.md` | 扫 `artifacts/project/playbooks/domains/` 下一级子目录列表 | `harness playbook-refresh` | 破损 → abort，报 `DOMAIN_LIST_SEGMENT_BROKEN`；漂移（domains/ 子目录与登记不一致）→ `playbook-check` 报 `DOMAIN_SUBDIR_MISMATCH` |

---

## §5 校验锚点清单

以下锚点为 `harness playbook-refresh`（chg-04）与 `harness playbook-check`（chg-05）必须满足的契约点。任何实现改动前应先核对此清单。

- **C-01**：`harness playbook-refresh` 只替换 `<!-- AUTO:X -->` … `<!-- /AUTO:X -->` 区段内容，区段标记行本身及区段外所有字节保持 byte-identical；不得追加 / 删除区段外任何字符。

- **C-02**：`harness playbook-check` 必须扫以下 **6 类漂移** + **1 类关键词覆盖空**：
  1. **依赖漂移**（`DEPENDENCY_DRIFT`）：`pyproject.toml` / `package.json` 依赖与 `AUTO:STACK` 区段内容不一致
  2. **scripts 漂移**（`SCRIPTS_DRIFT`）：`Makefile` / `scripts/` 与 `AUTO:SCRIPTS` 区段不一致
  3. **模块目录漂移**（`MODULE_DIR_DRIFT`）：`AUTO:LAYOUT` 区段与实际目录树不一致
  4. **code-map 互引漂移**（`CODEMAP_REF_DRIFT`）：`AUTO:DOMAIN_FILES` 内容与 `domains/*/code.md` 实际列表不一致
  5. **code.md 引用失效**（`CODE_MD_REF_BROKEN`）：`domains/*/code.md` 中列出的文件路径在仓库中不存在
  6. **README 依赖链接失效**（`README_DEP_BROKEN`）：`domains/*/README.md` 的 `## 依赖领域` 引用了不存在的 domain 子目录
  7. **关键词覆盖空**（`KEYWORD_COVERAGE`）：`domains/*/README.md` 的 `## 职责描述` 节为空或内容 ≤ 10 字节（疑似未填写）

- **C-03**：path schema 锁定为 `artifacts/project/playbooks/`；实现中任何路径变量若指向其他位置，报路径合规失败 `PATH_SCHEMA_VIOLATION`，exit code ≠ 0。

- **C-04**：每类 AUTO 区段标记必须配对——`<!-- AUTO:X -->` 与 `<!-- /AUTO:X -->` 必须同时存在；任一缺失 = 区段破损，refresh / check 均报 `SEGMENT_UNPAIRED` + abort（不继续写入）。

- **C-05**：`domains/` 子目录集合与 `code-map.md` 的 `AUTO:DOMAIN_FILES` 区段登记**必须互引**：
  - 每个 `domains/{name}/` 子目录都必须在 `code-map.md` 中有对应记录
  - `code-map.md` 中每条 domain 记录都必须在 `domains/` 下有对应子目录
  - 任一方向缺失 = `DOMAIN_SUBDIR_MISMATCH` 漂移，`playbook-check` exit 1
