# Change Plan

> **optional 标注**：本 change 为 req-30（slug 沟通可读性增强：全链路透出 title）的可选子变更，若 chg-01 / chg-02 / chg-03 已覆盖核心 AC，本 change 可延期或转 sug。下述步骤仅在实施时生效。

## 1. Development Steps

### Step 1: 选型确认（executing 阶段低风险决策）

- **操作意图**：在 A（新增 `_meta.yaml`）与 B（约束"需求摘要.md"首行）之间二选一，并记录到 decisions-log。
- **涉及文件**：无代码，仅决策。
- **关键代码思路**：
  - 推荐方案 A：新增 `_meta.yaml`。理由：不侵入对人文档；机器可扫描；与未来批量 lint 工具解耦。
  - 方案 B 作为兜底。
- **验证方式**：`artifacts/main/requirements/req-30-*/decisions-log.md` 含对应决策点（`dp-NN`）。

### Step 2: 新增 `_write_archive_meta` helper

- **操作意图**：提供"归档后写 meta"的单一入口。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（放在 `archive_requirement` 附近）。
- **关键代码思路**：
  - 签名：`def _write_archive_meta(archive_dir: Path, work_item_id: str, title: str, *, archived_from: Path) -> None:`
  - 字段：`id: {work_item_id}` / `title: {title}` / `archived_at: {now ISO}` / `archived_from: {rel path}`。
  - 写入 `archive_dir / "_meta.yaml"`；用 `save_simple_yaml` 保持与现有 state yaml 风格一致。
  - 幂等：若已存在 `_meta.yaml`，保留原 `archived_at`（读取原值后再写新 title）。
- **验证方式**：单测 `test_archive_requirement_writes_meta_yaml` / `test_archive_meta_idempotent`。

### Step 3: 改造 `archive_requirement`

- **操作意图**：归档入口落地"写 meta"。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py:4784+`。
- **关键代码思路**：
  - 在 move 完成、目标目录创建后，调用 `_write_archive_meta(target_dir, req_id, title, archived_from=source_dir)`。
  - title 读取顺序：runtime `current_requirement_title`（chg-01）→ state `state/requirements/{id}.yaml` 的 `title` → 若仍空，抛 SystemExit（归档时 title 必须存在）。
- **验证方式**：单测 `test_archive_meta_includes_title_from_runtime` / `test_archive_meta_matches_state_yaml`。

### Step 4: 改造 `migrate_requirements`

- **操作意图**：迁移 legacy → primary 时同步补 `_meta.yaml`。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py:4571~`。
- **关键代码思路**：
  - 对每个迁移后的目标目录，检查是否已有 `_meta.yaml`：
    - 有 → 跳过。
    - 无 → 从目录名的 slug 反查 id，从 state yaml 读 title，写 `_meta.yaml`（`archived_at` 设为目录 mtime 或一个 `unknown-legacy-migration` 占位字符串）。
  - 若无法确定 title（legacy 目录的 slug 无法精确反查到 state yaml），`_meta.yaml` 的 `title: (unknown-legacy)`，打 stderr warning。
- **验证方式**：单测 `test_migrate_requirements_backfills_meta`。

### Step 5: 兜底方案 B 的契约更新（若选方案 B）

- **操作意图**：若方案 B 被选中，在 `requirement-review.md` / `done.md` 的"对人文档首行模板"段显式写"首行必须为 `# 需求摘要：{id} {title}` / `# 交付总结：{id} {title}`，归档前校验"。
- **涉及文件**：`.workflow/context/roles/requirement-review.md` / `.workflow/context/roles/done.md`。
- **关键代码思路**：
  - Edit 方式插入一段明确约束；`archive_requirement` 在 move 前 grep 首行，不匹配则 raise 警告（或自动修正）。
- **验证方式**：`grep -n "首行必须" .workflow/context/roles/requirement-review.md` 命中。

### Step 6: 编写单元测试

- **操作意图**：4 条用例覆盖 helper + 归档 + 迁移 + 幂等。
- **涉及文件**：`tests/test_archive_meta.py`（新增）。
- **关键代码思路**：
  - `test_archive_requirement_writes_meta_yaml`：fixture 仓库归档 req-99 → 断言 `_meta.yaml` 存在且字段完整。
  - `test_archive_meta_includes_title_from_runtime`：构造 runtime `current_requirement_title = "demo title"` → 断言 `_meta.yaml` 的 `title` 等于 `demo title`。
  - `test_migrate_requirements_backfills_meta`：legacy 目录无 `_meta.yaml` → 迁移后新目录含 `_meta.yaml`。
  - `test_archive_meta_idempotent`：二次归档不覆盖 `archived_at`。
- **验证方式**：`pytest tests/test_archive_meta.py -v` 全绿。

### Step 7: 变更简报自证

- **操作意图**：AC-10 自证样本（若本 change 实施）。
- **涉及文件**：`artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/changes/chg-04-archive-meta-title落盘/变更简报.md`。
- **关键代码思路**：按 planning.md 对人文档模板产出；首次提到 req-30 时带完整 title。
- **验证方式**：文件存在且首行正确格式。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_archive_meta.py -v`：4 条新用例全绿。
- `pytest tests/test_archive_path.py tests/test_archive_bugfix.py tests/test_migrate_archive.py -v`：零回归。
- `pytest` 全量：180+ 测试零回归。

### 2.2 Manual smoke verification

- 手工 `harness archive` 一个活跃 req-99（fixture） → 检查 `artifacts/main/archive/requirements/req-99-*/_meta.yaml` 存在且字段完整。
- 手工 `harness migrate archive`（若有 legacy 目录） → 检查 `_meta.yaml` 被补齐。

### 2.3 AC Mapping

- AC-07 → Step 2 + Step 3 + Step 4 + Step 6。

## 3. 执行依赖顺序

1. **前置推荐**：chg-01 已落地（runtime `*_title` 字段可用）。
2. Step 1（选型）最前。
3. Step 2 → Step 3 → Step 4（helper → 归档入口 → 迁移）线性推进。
4. Step 5（方案 B）仅在选方案 B 时执行。
5. Step 6 与 Step 2-4 可穿插开发（TDD 风格）。
6. Step 7 最后。

## 4. 回滚策略

- **粒度**：每个 Step 一个 commit。
- **回滚触发**：
  - `_meta.yaml` 字段设计漏项（字段不够用）→ 加字段 + 版本号（`version: 1`），不回滚。
  - `migrate_requirements` 回填破坏老数据 → 明确"已存在不覆盖"；若误覆盖，从 git 历史恢复。
  - 方案 A/B 选型错误 → revert 全部并改选另一方案。
- **兜底**：`_meta.yaml` 是新文件，不删除老数据；完全回滚无数据损失风险。

## 5. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | 四源（state yaml / runtime / 目录名 / `_meta.yaml`）title 漂移 | state 权威 + helper 单向读 + 一致性单测 |
| R2 | `migrate_requirements` 改老数据引发 reviewer 误判 | "已存在不覆盖"策略 + PR 列清单 |
| R3 | `_meta.yaml` 字段与未来通用 meta 冲突 | 预留 `version` 字段；字段精简 |
| R4 | 方案选型延迟 | 推荐方案 A；决策点入 log |
| R5 | optional 被 ff 误执行 | ff --auto 决策点 log 明确标注 optional |
