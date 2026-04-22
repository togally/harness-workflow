# Change

## 1. Title

chg-04（归档 meta — title 落盘）【**optional — 2026-04-21 executing 阶段延期**】：归档 helper 强制 `_meta.yaml` 或"需求摘要.md"首行 title 格式

> **optional 标注**：若 chg-01（state schema）/ chg-02（CLI 渲染）/ chg-03（角色契约）已全面覆盖 AC-01~08，本 change 可延期到后续 sug 批次处理；**本 change 与 req-30 主线解耦，不阻塞需求完成**。建议在 req-30 acceptance 通过后，由 done 阶段决定是否立即启动或转 sug 登记。

## 1.1 延期决策（2026-04-21，Subagent-L1 开发者）

- **决策点**：chg-04 延期，不在本 executing 周期执行。
- **理由**：
  1. req-30（slug 沟通可读性增强：全链路透出 title）的核心 AC-01~AC-09 已由 chg-01（state schema）+ chg-02（CLI 渲染）+ chg-03（角色契约）完全覆盖；AC-10 自证样本由已产出的 `实施说明.md` / `变更简报.md` / session-memory.md 实现。
  2. chg-04 覆盖的 AC-07（归档目录 `_meta.yaml` / 首行 title 强约束）属于"增强而非必需"——现状归档目录名中已含 slug（人可读），`需求摘要.md` 首行模板已是 `# 需求摘要：{id} {title}` 格式（planning / requirement-review 约定），批量扫描需求极少。
  3. 预算控制：chg-01~03 完成后上下文消耗接近 65% 阈值，立即启动 chg-04（helper 新增 + archive_requirement / migrate_requirements 改造 + 4 条新测试）有维护质量下行风险。
- **后续动作**：
  - 本延期登记为衍生问题，交 done 阶段决定"登 sug 池 / 独立 bugfix / 不做"。
  - session-memory.md 交接事项已明确此项。
  - 若未来需要启动：直接按本 change 的 plan.md 6 Step 执行即可，无依赖改动。

## 2. Background

源自 req-30 方案 B 的 **L4 层目标**（归档 / 索引文件命名）与 **AC-07**：

- 现状：
  - 归档 helper（`resolve_archive_root` / `migrate_requirements` / `archive_requirement`，见 `src/harness_workflow/workflow_helpers.py:4484~4800`）在写归档目录时，仅依赖 slug 目录名携带 title 信息（如 `req-29-批量建议合集（2条）/`）；目录名被 slug 清洗规则约束长度后可能截断（bugfix-3 经验），失去完整 title。
  - `artifacts/main/archive/requirements/{req}/` 下的"需求摘要.md" / "交付总结.md"等对人文档首行**已有** `# 需求摘要：{id} {title}` 格式（planning / requirement-review 角色模板约定），但没有**硬约束**要求一定存在，也没有独立 `_meta.yaml` 方便批量扫描。
- AC-07 要求：每个归档目录下的索引/摘要显式包含 title 字段（首行或 `_meta.yaml`），便于批量脚本扫描。

## 3. Goal

在归档链路上补一道"title 落盘"硬门禁，让归档目录即使目录名被 slug 清洗截断，也能通过内部文件恢复完整 title：

**方案二选一**（executing 阶段敲定 + decisions-log 登记）：

- **方案 A（推荐）**：归档 helper 在完成归档后，**额外落盘** `_meta.yaml`（字段：`id` / `title` / `archived_at` / `archived_from`），文件名固定为 `_meta.yaml`（下划线前缀避免与产物 md 混淆）。
- **方案 B（兜底）**：强约束"需求摘要.md" / "交付总结.md" 首行必须为 `# 需求摘要：{id} {title}` / `# 交付总结：{id} {title}`；归档 helper 在 move 后 validate，首行不符即 raise 警告或自动修正。

优先方案 A：`_meta.yaml` 无需侵入对人文档、可被批量扫描工具（如 `harness status --scan-archive`）直接消费。

## 4. Requirement

- `req-30`

## 5. Scope

### 5.1 In scope

- **`src/harness_workflow/workflow_helpers.py`**：
  - 新增 helper `_write_archive_meta(archive_dir: Path, work_item_id: str, title: str) -> None`：写入 `archive_dir / "_meta.yaml"`，字段 `id` / `title` / `archived_at`（ISO UTC）/ `archived_from`（原产物路径）。
  - 改造 `archive_requirement`（约 4784 行附近）：在 move 完成后调用 `_write_archive_meta`；title 从 `state/requirements/{id}.yaml` 读取（若 chg-01 已落地，直接读 runtime `current_requirement_title`）。
  - 改造 `migrate_requirements`（约 4571 行）：对 legacy → primary 迁移的每个归档目录，同步补写 `_meta.yaml`（若已存在则不覆盖，保留原有 `archived_at`）。
  - 对 bugfix 归档 / regression 归档链路同步处理（若存在归档入口）。
- **兜底（方案 B）**：
  - 在 `requirement-review.md` / `done.md` 角色文件的"对人文档首行模板"段显式写明"首行必须为 `# 需求摘要：{id} {title}` / `# 交付总结：{id} {title}`，归档前校验"。
- **单元测试**：新增 `tests/test_archive_meta.py`：
  - `test_archive_requirement_writes_meta_yaml`：fixture 归档 req-99 → 断言归档目录含 `_meta.yaml` 且字段完整。
  - `test_archive_meta_includes_title_from_runtime`：runtime 有 `current_requirement_title` → `_meta.yaml` 的 `title` 匹配。
  - `test_migrate_requirements_backfills_meta`：构造 legacy 归档目录（无 `_meta.yaml`）→ 迁移后新建目录含 `_meta.yaml`。
  - `test_archive_meta_idempotent`：重复归档（模拟）不覆盖已有 `archived_at`。

### 5.2 Out of scope

- 不改归档目录的路径结构（仍是 `artifacts/{branch}/archive/requirements/{req-id}-{slug}/`，req-30 §4.2 排除）。
- 不改现存"需求摘要.md" / "交付总结.md" 内容（除非选定方案 B 的首行约束——推荐用方案 A 避开此点）。
- 不回填历史归档目录的 `_meta.yaml`（本 change 只改 helper，未来归档即有 `_meta.yaml`；历史目录由 `migrate_requirements` 下次运行时自动补齐，或留作 sug）。
- 不开发"批量扫描 `_meta.yaml` 做 lint" 的命令（作为 sug 登记）。
- **本 change 全部视为 optional**：若 chg-01/02/03 已覆盖 AC-01~08，done 阶段可决定跳过；不影响 req-30 acceptance。

## 6. Definition of Done（≥3 条，仅在本 change 实施时生效）

1. **DoD-1**：`archive_requirement` 被调用后，归档目录下存在 `_meta.yaml`，字段 `id` / `title` / `archived_at` / `archived_from` 完整非空。
2. **DoD-2**：`tests/test_archive_meta.py` 新增 4 条用例全部通过；现有 `tests/test_archive_path.py` / `tests/test_archive_bugfix.py` / `tests/test_migrate_archive.py` 零回归。
3. **DoD-3**：`migrate_requirements` 迁移 legacy → primary 后，每个新目标目录含 `_meta.yaml`；已存在 `_meta.yaml` 不被覆盖。
4. **DoD-4**：新建归档目录的 `_meta.yaml` 的 `title` 与 `state/requirements/{id}.yaml` 的 `title` 完全一致（数据一致性校验）。

## 7. 关联 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-07 | 归档目录每个索引/摘要显式包含 title 字段，便于批量扫描 | 方案 A：新增 `_meta.yaml`；方案 B：约束首行格式 |

## 8. 依赖 / 顺序

- **前置推荐**：chg-01 已落地（`_write_archive_meta` 优先从 runtime 读 `current_requirement_title`；未落地时 fallback 到 state yaml）。
- **独立于 chg-02 / chg-03**：本 change 不影响 CLI 渲染或角色契约。
- **建议执行时机**：chg-01 / chg-02 / chg-03 完成后再启动；或在 req-30 acceptance 通过后作为"附加增强"独立交付。
- 本 change **不阻塞** req-30 主线完成。

## 9. 风险与缓解

- **R1 `_meta.yaml` 与"需求摘要.md" / 目录名 / state yaml 四源不同步**：title 可能在四处漂移。
  - **缓解**：定义"state yaml 的 `title` 为权威源"；`_write_archive_meta` 只从 state（或 runtime 缓存）读 title；一致性单测覆盖。
- **R2 `migrate_requirements` 对已归档目录回填 `_meta.yaml` 改变现有归档目录内容**：reviewer 可能认为"不应动老数据"。
  - **缓解**：明确"首次迁移时自动补写；已存在不覆盖"；PR description 列出受影响目录清单；归档目录的 `_meta.yaml` 属于元数据增量（不修改 md 内容），风险可控。
- **R3 `_meta.yaml` 文件名与未来 `sug-04` 提案的 `_meta.yaml` 可能冲突**：若未来有通用 `_meta.yaml` 约定，字段需对齐。
  - **缓解**：字段精简（`id` / `title` / `archived_at` / `archived_from`），未来扩展时通过 `version` 字段兼容。
- **R4 方案 A / B 选型延迟**：executing 阶段可能犹豫。
  - **缓解**：在 change.md 已推荐方案 A；executing 若改选方案 B，记录到 decisions-log 并更新 plan.md。
- **R5 optional 被误执行**：本 change 被 ff 自动推进时未评估 "是否真有必要"。
  - **缓解**：ff --auto 若命中本 change，decisions-log 应记录 "chg-04 optional，选择立即执行 / 延期"；acceptance 阶段明确 chg-04 状态。
