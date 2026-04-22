# Requirement

## 1. Title

批量建议合集（20条）

## 2. Goal

**一句话**：打包处理 bugfix-3（apply-all path-slug bug 批次）+ req-29（批量建议合集（2条））+ req-30（slug 沟通可读性增强：全链路透出 title）三轮沉淀的 20 条建议，按 A-G 主题分组逐批消化，维持 harness workflow 自身的健康与自我改进节奏。

**分层目标**（按 §6 的 A-G 分组阐述每组的核心目标状态）：

- **A. 契约自动化 / 对人文档自检（5 条：sug-10 / sug-12 / sug-15 / sug-25 / sug-26）**：让对人文档契约（契约 1-7）在 stage 产出时即被自检，减少 done 阶段人工 `grep`；辅助角色（harness-manager / tools-manager / reviewer）同步纳入契约 7 id+title 硬门禁；`create_suggestion` 写入时 frontmatter 字段完整。
- **B. 工作流推进 / ff 机制整治（4 条：sug-09 / sug-18 / sug-21 / sug-27）**：补齐 `harness next` 的**执行触发**能力（不止更新 stage）+ ff 路径下 `stage_timestamps` 字段完整 + ff 模式下 subagent 长任务有 timeout 兜底 + `ff_mode` 在 done / archive 成功后自动关闭。
- **C. state yaml 字段完整性（2 条：sug-16 / sug-21，与 B 部分重叠）**：`_sync_stage_to_state_yaml` 覆盖 `regression --testing` 与 bugfix ff 所有路径，所有 stage 均写入时间戳。
- **D. CLI / helper 行为修复（5 条：sug-11 / sug-13 / sug-14 / sug-17 / sug-19）**：`apply_all_suggestions` 与 `_path_slug` helper 统一去重；`update_repo` 多生成器共享文件 hash 竞争保护；`adopt-as-managed` 对用户自建同路径文件的误覆盖保护；CLI 对 cwd 敏感 → auto-locate repo root；`harness bugfix` / `harness requirement` ID 分配器扫归档树去重。
- **E. 归档 / 迁移（2 条：sug-08 / sug-22）**：`.workflow/flow/archive/main/` 下 36+ 个 legacy 扁平归档迁到 `artifacts/{branch}/archive/`（接续 req-29（批量建议合集（2条））chg-02 的工作）；归档目录 `_meta.yaml` 落盘（req-30 AC-07 延期内容）。
- **F. 数据管道（2 条：sug-20 / sug-24）**：`.harness/feedback.jsonl` 迁移时给用户 git 变更提示；regression reg-NN 有独立 title 源，不再复用 req title。
- **G. 杂项（1 条：sug-23）**：`render_work_item_id` 读 title 时 strip 掉 legacy yaml 中的 `'` `"` 非标准空串字符，兜底历史脏数据。

## 3. Scope

### 3.1 Included

- §6 合并建议清单列出的 20 条 sug（sug-08..sug-27）**全部纳入本 req 的 scope**。
- 按主题分组拆为 4-5 个 change（见 §5 Split Rules），每个 change 独立可交付、独立可验收。
- 本 req 自身的 `requirement.md` / `需求摘要.md` / 各 `change.md` / `plan.md` / `实施说明.md` / `变更简报.md` 等产物遵循 req-30（slug 沟通可读性增强：全链路透出 title）/ chg-03 建立的**契约 7（id + title 硬门禁）**—— 作为契约 7 的自证样本。
- 登记一条针对 `harness suggest --apply-all` path-slug bug（`workflow_helpers.py:3605` 拼接 req_dir 未清洗 title 导致路径 miss，清单追加被静默跳过但 `unlink` 照常执行）的修复——与 sug-11（`apply_all_suggestions` 同源隐患下沉到 `_path_slug` helper）合并，归入 D 组。
- 登记一条关于 **body 丢失不可恢复**的约定：sug-08..sug-27 的 body 文件已被上述 bug 物理删除且在 `.gitignore` 范围内无 git 历史，planning 阶段按 title 级颗粒度推进，必要时从 action-log / session-memory / git log 推断具体细节。

### 3.2 Excluded

- 不重新恢复已被删除的 sug 文件 body（不现实；planning 阶段按 title 级颗粒度或从 git / action-log 补）。
- 不再引入新的 sug 或变更本 req 范围（新建议一律走下一轮 suggest 池）。
- 不修 req-30 已交付的 chg-01 / chg-02 / chg-03 部分（已闭环，不在本 req 回归范围内）。
- 不触碰 `.harness/feedback.jsonl` 的历史数据（只改迁移提示逻辑，不改已有数据）。
- 不改 slug / id 编号规则（延续 req-30 不包含项）。
- 不扩 `ff --auto` 到 acceptance 之后（延续 req-29（批量建议合集（2条））约束，acceptance 必须停下等人）。
- 不做 Python 包发布 / pip install -U 流程。

## 4. Acceptance Criteria

- **AC-01（A 组 — 契约自检 CLI，对应 sug-25）**：`harness status --lint`（或等价子命令）已实现，能扫描 `artifacts/{branch}/**/*.md` + `.workflow/state/sessions/**/session-memory.md` + `.workflow/state/action-log.md`，对每个首次引用工作项 id（`req-*` / `chg-*` / `sug-*` / `bugfix-*` / `reg-*`）且未带 title 的行按"文件:行号"报告违规；至少 1 单测覆盖违规检测 + 合规样本。
- **AC-02（A 组 — 产出后自检，对应 sug-15）**：stage 角色产出对人文档后（`变更简报.md` / `实施说明.md` / `session-memory.md` 等），自动触发 `harness validate` 或等价契约自检（契约 1-7 全量），发现违规时阻塞 stage 推进；至少 1 集成测试覆盖。
- **AC-03（A 组 — 契约扩展辅助角色，对应 sug-26）**：辅助角色 `harness-manager.md` / `tools-manager.md` / review-checklist 已补契约 7 id+title 硬门禁条款；所有辅助角色首次引用 id 时强制带 title。
- **AC-04（A 组 — regression 契约 + frontmatter，对应 sug-10 + sug-12）**：regression 阶段《回归简报.md》契约执行补强（契约 3-4 落地校验）；`create_suggestion` 写入 sug 文件时 frontmatter 必含 `id` / `title` / `status` / `created_at` / `priority` 五字段（契约 6 全量），缺字段直接 fail。
- **AC-05（B 组 — next 执行触发，对应 sug-09）**：`harness next` 引入 `--execute` 或等价行为，触发下一 stage 的实际工作（派发 subagent / 执行 agent 任务），而不只是翻 `runtime.yaml` 的 stage 字段；至少 1 单测覆盖 "next 更新 stage" 与 "next --execute 触发任务" 两条主路径。
- **AC-06（B/C 组 — stage_timestamps 完整性，对应 sug-16 + sug-21）**：`_sync_stage_to_state_yaml` 覆盖 `regression --testing` + bugfix ff 路径，所有 stage（requirement_review / planning / executing / testing / acceptance / regression / done / archive）均写入时间戳；至少 1 单测覆盖 "regression --testing" 与 "bugfix ff 全程" 两条路径下 stage_timestamps 无缺字段。
- **AC-07（B 组 — ff 自动关 + subagent 粒度，对应 sug-27 + sug-18）**：`ff_mode` 在 done + archive 成功后由 CLI 自动重置为 `false`（本 req 产出后 `runtime.yaml` 的 `ff_mode` 字段自证为 false）；ff 模式下 subagent 长任务有 timeout 兜底（超时自动上报主 agent 而非悬挂）。
- **AC-08（D 组 — helper 去重 + 竞争 + 覆盖保护，对应 sug-11 + sug-13 + sug-14 + `apply-all` path-slug bug）**：`apply_all_suggestions` 与其他路径拼接逻辑统一到 `_path_slug` helper（单一数据源）；`update_repo` 多生成器共享文件（`experience/index.md` / `runtime.yaml` / SKILL.md）引入 hash 竞争保护；`adopt-as-managed` 判据对用户自建同路径文件的误覆盖风险已加保护；`apply-all` path-slug 拼接 bug 修复 + 回归单测（"legacy title 含特殊字符 `'` `"` 空格 `（）` 时 apply-all 不再静默删除 body"）。
- **AC-09（D 组 — CLI 易用性，对应 sug-17 + sug-19）**：CLI 通过 auto-locate repo root 解决 cwd 敏感问题（任意子目录下 `harness status` 能找到项目根）；`harness bugfix` / `harness requirement` ID 分配器扫描归档树去重，避免新建 id 与归档 id 冲突。
- **AC-10（E 组 — 归档 meta + legacy 清理，对应 sug-08 + sug-22）**：`harness migrate archive`（或等价命令）把 `.workflow/flow/archive/main/` 下 36+ 个扁平格式历史归档（req-01..req-26 早期 + bugfix 历史）迁到 `artifacts/main/archive/`（接续 req-29（批量建议合集（2条））chg-02 未完部分）；归档目录 `_meta.yaml` 落盘（req-30 AC-07 延期内容），字段至少含 `id` / `title` / `archived_at` / `origin_stage`。
- **AC-11（F 组 — 数据管道，对应 sug-20 + sug-24）**：`.harness/feedback.jsonl` 在 `harness update` / `harness install` 触发路径切换时有明确 git 变更提示（"建议 commit 本次迁移"）；regression 阶段 `reg-NN` 有独立 title 源（新建 regression 时必须显式传 title 或从 issue 摘取），不再复用 parent req title。
- **AC-12（G 组 — legacy yaml strip 兜底，对应 sug-23）**：`render_work_item_id` 读取 title 字段时 strip 掉 legacy yaml 中的 `'` `"` 字符以及前后空格，即使 state yaml 历史脏数据（如 `title: "'批量建议合集'"`）也能渲染出干净 title；至少 1 单测覆盖。
- **AC-综合（测试 + 零回归）**：每个 change 至少交付 2 条单测 + 1 条集成/smoke；全量 `pytest` 零回归（维持当前 183+ passed 基线，不允许下降）。
- **AC-自证（契约 7）**：req-31（批量建议合集（20条））自身所有产出文档（本 `requirement.md` / `需求摘要.md` / 后续 `change.md` / `plan.md` / `变更简报.md` / `实施说明.md` / `测试结论.md` / `验收摘要.md` / `交付总结.md`）首次引用工作项 id 时必须形如 `{id}（{title}）`，裸 id 视为契约 7 硬门禁违反。

## 5. Split Rules

按 A-G 分组拆 change，推荐拆为 **5 个 change**（chg-05 可选合并入 chg-03）：

### chg-01：契约自动化 + apply-all bug（A 组 + D 组 apply-all）

- 覆盖 sug：sug-10 / sug-12 / sug-15 / sug-25 / sug-26 + sug-11（含 apply-all path-slug bug 修复，属于同源）= 6 条
- 交付：`harness status --lint` CLI；stage 产出后自动 `harness validate`；辅助角色契约 7 扩展；`create_suggestion` frontmatter 补齐；回归简报契约补强；`apply-all` path-slug bug 修复 + 防护单测
- DoD：AC-01 / AC-02 / AC-03 / AC-04 + AC-08（apply-all 部分）全通过

### chg-02：工作流推进 + ff 机制（B + C 组合并）

- 覆盖 sug：sug-09 / sug-16 / sug-18 / sug-21 / sug-27 = 5 条
- 交付：`harness next --execute`；`_sync_stage_to_state_yaml` 补齐 regression/bugfix ff 路径；ff 模式 subagent timeout；ff_mode 自动关
- DoD：AC-05 / AC-06 / AC-07 全通过；本 req 完成后 `runtime.yaml.ff_mode == false`

### chg-03：CLI / helper 剩余修复（D 组剩余）

- 覆盖 sug：sug-13 / sug-14 / sug-17 / sug-19 = 4 条
- 交付：`update_repo` hash 竞争保护；`adopt-as-managed` 覆盖保护；CLI auto-locate repo root；ID 分配器扫归档树
- DoD：AC-08（剩余部分）+ AC-09 全通过

### chg-04：归档 / 迁移 + 数据管道（E + F 组）

- 覆盖 sug：sug-08 / sug-22 / sug-20 / sug-24 = 4 条
- 交付：legacy archive 迁移命令；归档 `_meta.yaml` 落盘；feedback.jsonl 迁移提示；regression title 源
- DoD：AC-10 / AC-11 全通过

### chg-05：legacy yaml strip 兜底（G 组，optional）

- 覆盖 sug：sug-23 = 1 条
- 交付：`render_work_item_id` strip `'` `"` 空格
- DoD：AC-12 全通过
- **注**：可与 chg-03 合并（修改位置相近），由 planning 阶段最终决定

### 依赖顺序

- **chg-01 → chg-02 → chg-03 → chg-04 → chg-05**（chg-01 契约自检优先，后续 change 自证；chg-05 独立可延期）
- chg-02 的 `ff_mode` 自动关需在本 req 完成前落地，否则 AC-自证不通过。

### 每个 change 的 DoD 共性

- 对应 AC 全通过；
- `change.md` 明确列出覆盖的 sug id 清单（带 title，契约 7）；
- `plan.md` 有 TDD 单测清单 + 回滚策略 + body 丢失时的推断来源（git log / action-log / session-memory）；
- 交付时 `实施说明.md` + `变更简报.md` 双轨对人文档产出。

### req 完成时

- `completion.md` 记录 20 条 sug 的最终处置（**已落 / 延期 / 放弃**三态），以及启动验证（`pytest` 零回归 + `harness status --lint` 全绿）成功。

## 6. 合并建议清单（恢复自 apply-all stdout — sug body 文件已被删除）

> **告警**：`harness suggest --apply-all` 存在 bug（`workflow_helpers.py:3605` 拼接 req_dir 时用未清洗 title 导致路径 miss，清单追加被静默跳过；但 `path.unlink()` 照常执行），sug-08..27 共 20 个 sug 文件已被物理删除，且均在 `.gitignore` 范围内、无 git 历史。以下仅能从 `harness suggest --list` stdout 恢复 **id + title**；body 已不可恢复（planning 阶段需结合 session 记忆 / git log 重建，或选择性放弃）。

| id | title | 来源批次 |
|----|-------|---------|
| sug-08 | 清理 `.workflow/flow/archive/main/` 下扁平格式的 36+ 个历史归档（req-01~26 早期） | bugfix-3（2026-04-20） |
| sug-09 | `harness next` 支持触发下一 stage 的实际工作（当前仅更新 stage） | bugfix-3（2026-04-20） |
| sug-10 | regression 阶段《回归简报.md》契约执行补强 | bugfix-3（2026-04-20） |
| sug-11 | `apply_all_suggestions` 同源隐患下沉到 `_path_slug` helper | bugfix-3（2026-04-20） |
| sug-12 | `create_suggestion` 写 sug 文件时补齐 title 与 priority frontmatter 字段 | bugfix-3（2026-04-20） |
| sug-13 | `update_repo` 多生成器共享文件 hash 竞争（experience/index.md / runtime.yaml / SKILL.md） | bugfix-3（2026-04-20） |
| sug-14 | `adopt-as-managed` 判据对用户自建同路径文件的误覆盖风险 | bugfix-3（2026-04-20） |
| sug-15 | stage 角色产出对人文档后当场 `harness validate` 自检 | bugfix-3（2026-04-20） |
| sug-16 | `_sync_stage_to_state_yaml` 在 `regression --testing` 路径盲区导致 stage_timestamps 字段缺 | bugfix-3（2026-04-20） |
| sug-17 | `harness` CLI 对 cwd 敏感，建议 auto-locate repo root | bugfix-3（2026-04-20） |
| sug-18 | ff 模式下 subagent 任务拆分粒度与 API idle timeout 保护 | bugfix-3（2026-04-20） |
| sug-19 | `harness bugfix`/`harness requirement` ID 分配器必须扫描归档树 | bugfix-3（2026-04-20） |
| sug-20 | 主仓 `.harness/feedback.jsonl` 迁移 git 变更提示 | bugfix-3（2026-04-20） |
| sug-21 | bugfix ff 路径下 stage_timestamps 仍缺 regression/executing/testing 字段 | bugfix-3（2026-04-20） |
| sug-22 | chg-04 归档 `_meta.yaml` 落盘（req-30 AC-07 延期内容） | req-30（2026-04-21） |
| sug-23 | AC-04 legacy yaml 非标准空串 title 的 strip 兜底 | req-30（2026-04-21） |
| sug-24 | regression reg-NN 独立 title 源 | req-30（2026-04-21） |
| sug-25 | `harness status --lint` 自动化契约 7 校验 | req-30（2026-04-21） |
| sug-26 | 辅助角色（harness-manager / tools-manager / reviewer）契约 7 扩展 | req-30（2026-04-21） |
| sug-27 | `ff_mode` 在 done / archive 后应自动关闭 | req-30（2026-04-21） |

### 按主题初步分组（给 planning 阶段参考，非最终拆分）

- **A. 契约自动化 / 对人文档自检**（5 条）：sug-10 / sug-12 / sug-15 / sug-25 / sug-26
- **B. 工作流推进 / ff 机制整治**（4 条）：sug-09 / sug-18 / sug-21 / sug-27
- **C. state yaml 字段完整性 / stage_timestamps**（2 条）：sug-16 / sug-21（与 B 部分重叠）
- **D. CLI / helper 行为修复**（5 条）：sug-11 / sug-13 / sug-14 / sug-17 / sug-19
- **E. 归档 / 迁移**（2 条）：sug-08 / sug-22
- **F. 数据管道**（2 条）：sug-20 / sug-24
- **G. 杂项**（1 条）：sug-23

