# Requirement

## 1. Title

建议池梳理验证 + 优先级 roadmap + 分批落地

## 2. Goal

针对 .workflow/flow/suggestions/ 累积的 45 条 pending sug（sug-08~sug-53，编号有跳号），逐条验证现状（是否仍存在 / 是否已被后续 req/chg/bugfix 顺手覆盖 / 是否 stale），按主题簇归并去重，排出优先级，拆分为多个 chg 分批落地。本 req 阶段产出 sug-audit + roadmap + 首批推荐，不直接创建 chg 工件，由用户拍板首批范围后再由主 agent 用 `harness change` 创建。

核心问题：
- 池累积过大（45 条），跨主题、跨优先级、部分已被覆盖，主 agent 难以判定下一步入场顺序；
- 多条同根因 sug 重复登记（如 over-chain 簇 7 条 / usage-log 簇 5 条），消耗 done 阶段六层回顾注意力；
- 已 applied / stale sug（如 sug-25 / sug-44 / sug-45 / sug-46 / sug-50）仍占池容量，违反 sug 池"pending = 待办"的语义。

## 3. Scope

### 3.1 In Scope

- sug-08 ~ sug-53 全量（含 sug-25 已 applied 在池、sug-46 archive 在池的状态核实）
- 主题簇归类（已识别 10 簇：over-chain / usage-log runtime / apply-rename CLI / scaffold mirror / 契约 lint / archive 路径 / testing-dogfood / install-update 体验 / runtime 同步 / 杂项）
- 每条 sug 的 live / stale / applied-out / dup-of 判定
- chg 拆分粒度 5~10 个簇 chg + 优先级 + 依赖图 + 工作量估算 + 首批推荐
- 出池清理建议（applied delete / stale delete / dup 合并）

### 3.2 Out Scope

- 本 req 周期之后**新增的 sug**（如 sug-54+）不纳入本 req 范围（避免无限滚动）
- chg 实施本身（chg 工件创建 + 代码变更落地由后续独立 req/chg 周期承接）
- sug.md frontmatter 优先级回填（避免 sug 文件 churn，新优先级仅落 roadmap.md）
- 跨 repo 影响（如 Yh-platform / scaffold_v2 mirror）：仅在本仓库 .workflow/context/ + scaffold_v2 同步范围内处理，不动其他 repo
- bugfix 周期触发的 hot fix（如新发现 P0 bug 走 harness bugfix 路径，不挪进本 req 的 roadmap）

## 4. Acceptance Criteria

- AC-01：`sug-audit.md` 产出，45 条 sug 全部有明确判定（live / stale / applied-out / dup-of），无遗漏，无"待评估"占位
- AC-02：`roadmap.md` 产出，含 5~10 个 chg 拆分 + 每 chg 优先级（P0/P1/P2/P3）+ 依赖图 + 工作量估算（小 / 中 / 大）+ 首批 chg 推荐（≥ 2 条）
- AC-03：每条 sug 的处理建议（进 chg-N / 出池 delete / 出池 archive / dup 合并）有依据 — 引用工件 id / 代码行号 / commit sha
- AC-04：用户拍板首批 chg 范围（最少 1 个 chg，可选最多 3 个）后，主 agent 用 `harness change` 创建对应 chg 工件 — 本 AC 由用户介入完成，本 req 周期不强制等用户回复
- AC-05：池清理路径明确：applied / stale sug 列表给出，主 agent 可在 chg 落地后批量执行 `harness suggest --delete` / `harness suggest --archive` 出池

## 5. Split Rules

按主题簇切 chg，每 chg 解决一个主题簇的核心 sug + 相关 followup。粒度规则：

- **同根因** sug 必须合并到一个 chg（如 over-chain 簇 7 条都进 chg-1）
- **同代码触点** sug 优先合并（如 apply / rename / suggest CLI 在同 helper 文件，进 chg-3）
- **数据底座 / 行为底座** chg 优先级最高，作为后续 chg 前置（chg-1 over-chain dogfood + chg-2 usage-log runtime）
- **契约硬化 lint** 集中到一个 chg（chg-5），避免 lint 工具骨架重复实现
- **体验 / 杂项** chg 末位，可并行
- 单 chg 工作量上限：**大**（粒度过大应再拆）；下限：**小**（粒度过小可与同簇合并）
- chg 间依赖必须显式声明（roadmap.md 中以 DAG 表达）

完整 chg 拆分见 `artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/roadmap.md`。
