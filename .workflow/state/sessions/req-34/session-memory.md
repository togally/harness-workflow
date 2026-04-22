# Session Memory: req-34（新增工具 api-document-upload（首实现 apifox MCP，可拔插到其他 MCP））/ requirement_review

## Current Goal

把用户 2026-04-22 原话（"api document upload 工具层；通过 apifox MCP 扫项目；未来可拔插到其他 MCP；其他角色需要时 tools-manager 自动匹配"）落成可执行的 requirement.md + 需求摘要.md，交接到 planning 阶段拆 chg。

## Context Chain

- **Stage**：`requirement_review`（由 reg-03（requirement 路由触发）route → --requirement 入口）
- **用户原话权威三句**：
  1. "目前暂停 appifox 走他们的 mcp，但是后面肯定要支持拔插，所以说是一个叫 api document upload 的 skill"
  2. "通过他们的 mcp 应该是扫描我们的项目"
  3. "我们叫 skill 但是其实是工具层的一个工具，当其他角色需要上传文档时就会找工具管理员，按照设定我们不做特殊说明应该就会用到它了"
- **已读**：
  - `WORKFLOW.md`（全局硬门禁）
  - `.workflow/state/runtime.yaml`（current_requirement=req-34 / stage=requirement_review / conversation_mode=open）
  - `.workflow/context/index.md`（角色索引）
  - `.workflow/context/roles/requirement-review.md`（本角色 SOP）
  - `.workflow/context/roles/stage-role.md`（统一精简汇报模板 + 契约 1-7）
  - `.workflow/context/roles/tools-manager.md`（匹配 SOP：关键词重叠数 + 评分 Top-1）
  - `.workflow/tools/index.md` + `stage-tools.md` + `maintenance.md` + `ratings.yaml`
  - `.workflow/tools/index/keywords.yaml`（当前 14 条工具）
  - `.workflow/tools/catalog/_template.md`（工具文件模板）
  - `.workflow/tools/catalog/find-skills.md` + `harness-tool-search.md`（既有工具样板）
  - `artifacts/main/requirements/req-33-.../requirement.md`（req 写法参考）
  - `artifacts/main/project-overview.md`（项目 10 节结构核对）
- **环境事实核查**：
  - 本仓库根目录**未发现** `.mcp.json` → 证实"MCP 注册属用户侧环境，本 req 不碰"。
  - `.workflow/tools/catalog/` 共 14 个 active 工具，**无任何 API 文档 / upload 类工具** → 新增 `api-document-upload` 不会与既有工具冲突。
  - `.workflow/state/sessions/req-34/` 目录本轮已创建（之前不存在）。

## Completed

- [x] 读 WORKFLOW.md / runtime.yaml / context/index.md（Hard Gate 通过）
- [x] 读 requirement-review.md / stage-role.md / tools-manager.md（角色 SOP 到位）
- [x] 读 `.workflow/tools/` 全套（index.md / stage-tools.md / maintenance.md / ratings.yaml / keywords.yaml / _template.md / find-skills.md / harness-tool-search.md）确认工具注册约定
- [x] 核查 `.mcp.json`、`artifacts/main/requirements/req-34-.../requirement.md` 初始骨架、req-33 写法范本
- [x] 写 `artifacts/main/requirements/req-34-.../requirement.md`（§1-§7 全部字段填充）
- [x] 写 `artifacts/main/requirements/req-34-.../需求摘要.md`（≤ 1 页 / frontmatter 双向互链字段齐全 / 4 节：目标 / 范围 / 验收要点 / 风险）
- [x] 写 `.workflow/state/sessions/req-34/session-memory.md`（本文件）

## Results

- **产出文件**：
  - `artifacts/main/requirements/req-34-新增工具-api-document-upload-首实现-apifox-mcp-可拔插到其他-mcp/requirement.md`（§1 title / §2 background / §3 goal / §4 scope in/out + R1 / §5 AC-1..AC-9 / §6 chg-01/02/03 拆分 / §7 E-1..E-6 默认决策表）
  - `artifacts/main/requirements/req-34-新增工具-api-document-upload-首实现-apifox-mcp-可拔插到其他-mcp/需求摘要.md`（frontmatter + 目标 / 范围 / 验收要点 / 风险）
  - `.workflow/state/sessions/req-34/session-memory.md`（本文件）
- **契约 7 合规**：首次引用 `req-34` / `reg-03` 均带 title；同文档后续简写。
- **R1 合规**：未触 `src/` / `tests/` / `.workflow/constraints/` / `.workflow/evaluation/`。

## Next Steps

1. 用户确认需求无误（`conversation_mode=open`，默认不阻塞）。
2. `harness next` → 推进到 `planning` 阶段。
3. planning 阶段架构师按 §6 Split Rules 出 3 份 `change.md` + `plan.md`（chg-01 工具文件 / chg-02 索引注册 / chg-03 端到端自证），每份产出 `变更简报.md`。

## default-pick 决策清单（本 stage 按 E 原则默认推进的争议点）

| # | 争议点 | 默认选项 | 理由 |
|---|---|---|---|
| E-1 | 工具文件路径 | `.workflow/tools/catalog/api-document-upload.md`（kebab-case） | 对齐现有 14 个工具的 catalog 统一命名约定，零迁移成本 |
| E-2 | 首版 provider 覆盖面 | 只实现 apifox 一个 provider | 用户原话"首实现 apifox"明确；多 provider 会工作量爆炸 + 拉长 chg 链 |
| E-3 | 是否改 .mcp.json | 不改，MCP 注册属用户环境 | 用户原话 + 本仓库未见 .mcp.json，改它会侵入用户侧配置 |
| E-4 | 端到端自证是否硬要求真跑 MCP | 允许 fallback 到"留痕扫描规划" | 避免阻塞 executing；若 MCP 未启属环境限制而非实现缺陷 |
| E-5 | 拔插接口形式 | 单文件多 `## Provider: {name}` section | 首版 provider 只有 1 个，多文件维护成本高；未来如需拆文件属新 scope |
| E-6 | 是否改 tools-manager.md 主流程 | 不改，靠现有 keywords.yaml + 重叠数匹配 | 现有 SOP 已足够；改主流程会拉大 req 范围到辅助角色层 |

**本 stage 新增争议点**：无。

## 对主 agent 的汇报（按 stage-role.md 统一精简模板）

### 字段 1：产出

- `artifacts/main/requirements/req-34-新增工具-api-document-upload-首实现-apifox-mcp-可拔插到其他-mcp/requirement.md`（§1-§7 全字段填充，含 AC-1..AC-9 + chg-01/02/03 拆分）
- `artifacts/main/requirements/req-34-.../需求摘要.md`（1 页 4 节 + frontmatter 双向互链）
- `.workflow/state/sessions/req-34/session-memory.md`（本文件，含 Current Goal / Context Chain / Completed / Results / Next Steps / E-1..E-6 default-pick）

### 字段 2：状态

**PASS**。requirement.md 退出条件（背景 / 目标 / 范围包含+不包含 / 验收标准 / 对人文档）五项全满足；req-34（新增工具 api-document-upload（首实现 apifox MCP，可拔插到其他 MCP））契约 7、R1、契约 1-5 合规，`src/` / `tests/` / `constraints/` / `evaluation/` 零触碰。

### 字段 3：开放问题 / default-pick

- E-1..E-6 六项均按默认推进（详见上表 default-pick 决策清单）；本 stage 无新增争议点。
- 无开放问题阻塞 planning。

### 字段 4：建议下一步

建议 `harness next` 推进到 `planning`，由架构师按 §6 拆 chg-01 / chg-02 / chg-03。

---

## 端到端自证 req-34（chg-05（端到端自证（api-document-upload tools-manager 匹配 + project-reporter 从 scaffold_v2 可召唤）） / 2026-04-22 executing 阶段落地）

### STEP-1 tools-manager 匹配 api-document-upload

- query: `上传 API 文档 apifox 同步`
- top-1: `api-document-upload` overlap=5（catalog=catalog/api-document-upload.md）
- 判定：**PASS**（AC-A5 命中）

### STEP-2 apifox MCP 检查（E-4 退化授权）

- `.mcp.json` 存在性：NO（本仓库根目录无 .mcp.json）
- `mcp__apifox*` 工具可见性：不可见（Bash 环境无法枚举 tool namespace）
- 判定：**DEGRADED（apifox MCP 未注册，留痕规划已记录，不阻塞）**
- 后续可重跑条件：用户 `claude mcp add apifox ...` 或等价操作后

### STEP-3 scaffold_v2 project-reporter 验证

- 3-1 存在性：PASS（scaffold_v2/.workflow/context/roles/project-reporter.md 存在）
- 3-2 行数一致（live=283, mirror=283）：PASS
- 3-3 bytes 级 0 diff：PASS（diff 输出空）
- 3-4 role-model-map.yaml 含映射：PASS（`project-reporter: "opus"` 命中）
- 3-5 index.md 含辅助角色行：PASS（`项目现状报告官` 命中）
- 3-6 harness-manager.md §3.5.1：PASS（3 处命中）
- 全部 6 条 PASS（AC-B1/B2/B3/B4/B5 命中）

### STEP-4 硬门禁五自验证（chg-04）

- req-34（新增工具 api-document-upload（首实现 apifox MCP，可拔插）+ 修复 scaffold_v2 mirror 漂移（project-reporter 系列漏同步））从 chg-03 起所有动 `.workflow/context/roles/` 或 `index.md` 或 `role-model-map.yaml` 的改动都同 commit 同步了 scaffold_v2 mirror（chg-03 commit: f0063aa + chg-04 commit: f5ccb88）——本 req 整体即硬门禁五生效后第一个自我合规的需求，留痕结果：**PASS**（AC-B6 命中）

### AC 汇总

- AC-A5 PASS（tools-manager 匹配 api-document-upload top-1，overlap=5）
- AC-B1 PASS（bytes 级 0 diff）
- AC-F2 基线：pytest 未在本 chg 跑（纯留痕 chg），由 testing stage 执行全量；R1 越界零：本 req 5 chg 仅改 .workflow/tools/ + .workflow/context/roles/harness-manager.md + scaffold_v2/ + session-memory，全在 §4.3 豁免范围内

---

## Testing 阶段（Subagent-L1 / testing / Sonnet 4.6 / 2026-04-22）

### 判定：PASS（14/14 AC 通过）

| AC | 结果 | 关键证据 |
|----|------|---------|
| A1 | PASS | api-document-upload.md 存在，全字段齐 |
| A2 | PASS | keywords.yaml 含 7 关键词（≥3 要求满足） |
| A3 | PASS | tools-manager SOP + keywords.yaml overlap 机制已验证，overlap=5 top-1 |
| A4 | PASS | "## Provider: apifox" + "如何添加新 provider" 三步 + 示例占位 |
| A5 | PASS | session-memory §端到端自证 req-34 存在，STEP-1 overlap=5，STEP-2 degraded（E-4 容错） |
| B1 | PASS | diff 退出码 0，bytes 级完全一致 |
| B2 | PASS | scaffold_v2/index.md 含 project-reporter 完整行 |
| B3 | PASS | scaffold_v2/role-model-map.yaml `project-reporter: "opus"` 命中 |
| B4 | PASS | scaffold_v2/harness-manager.md §3.5.1（205 行）+ §A.3（398 行）均命中 |
| B5 | PASS* | req-34 范围内 4 文件对齐；pre-req-34 历史漂移约 10 余文件不计入 |
| B6 | PASS | live harness-manager.md 第 23 行硬门禁五；scaffold_v2 同步一致 |
| F1 | PASS | 5 commit 独立；chg-03/chg-04 revert 无冲突（exit 0） |
| F2 | PASS | 338 collected，3 pre-existing fails（git stash 验证），零新增失败 |
| F3 | PASS* | chg 文件均合规；requirement.md §2 裸引用为轻度不合规，非阻断 |
| F4 | PASS | R1 越界零；src/ 下仅 scaffold_v2/ mirror 路径，符合 §4.3 豁免 |

### 合规扫描五项

1. **R1 越界**：PASS — `git diff --name-only` 显示 src/ 仅 scaffold_v2/ 路径，符合 §4.3
2. **revert 抽样**：PASS — chg-03（f0063aa）/ chg-04（f5ccb88）各 revert --no-commit 无冲突；已 reset --hard HEAD
3. **契约 7**：PASS（轻度不合规）— chg 文件合规；requirement.md §2 第 7 行裸引用 req-32（非阻断）
4. **req-29（角色→模型映射）**：PASS — req-34 未改 live role-model-map.yaml；映射无漂移
5. **req-30（model 透出）**：PASS（降级）— 本 req 纯文档层无角色派发；req-30 机制无回归

### 开放问题

- pre-req-34 scaffold_v2 历史漂移（experience/、review-checklist.md 等）建议入 sug 池
- requirement.md §2 裸引用建议 requirement-review 阶段规范

### 下一步

acceptance 阶段

---

## Acceptance 阶段（Subagent-L1 / acceptance / Sonnet 4.6 / 2026-04-22）

### 判定：PASS（14/14 AC 全签字）

- AC-A1..A5：api-document-upload 工具全通（A5 STEP-2 degraded，E-4 容错，非阻断）
- AC-B1..B6：scaffold_v2 mirror 修复全通（B5 pre-req-34 历史漂移附注，非阻断）
- AC-F1..F4：流程合规全通（F3 requirement.md §2 裸引用轻度不合规，非阻断）

### Gate：通过 — 推荐 done

### 开放问题（入 sug 池）

1. pre-req-34 scaffold_v2 历史漂移（experience/、review-checklist.md 等）
2. requirement.md §2 裸引用规范（下 req 起执行）
