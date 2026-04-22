# Change

## 1. Title

chg-04（归档迁移 + 数据管道）：legacy archive 迁移命令 + 归档目录 `_meta.yaml` 落盘 + `.harness/feedback.jsonl` 迁移 git 变更提示 + regression `reg-NN` 独立 title 源

> 父需求：req-31（批量建议合集（20条））

## 2. Background

源自 req-31（批量建议合集（20条））§5 Split Rules 的 **chg-04 分组**（E 组归档迁移 2 条 + F 组数据管道 2 条，共 4 条 sug），以及 §4 的 **AC-10 / AC-11**：

- **现状**：
  - `.workflow/flow/archive/main/` 下仍有 36+ 个**扁平格式**的历史归档（req-01..req-26 早期 + bugfix 历史），应已迁到 `artifacts/main/archive/`；req-29（批量建议合集（2条））chg-02 完成了主要迁移，但 sug-08 明确指出**仍有残留**。
  - req-30（slug 沟通可读性增强：全链路透出 title）chg-04 是归档目录 `_meta.yaml` 落盘的工作（已在 req-30 executing 阶段**延期**，现由 req-31（批量建议合集（20条））sug-22 接管）。
  - `update_repo` / `harness install` 在迁移 `.harness/feedback.jsonl → .workflow/state/feedback/feedback.jsonl`（`workflow_helpers.py:3164-3175`）时无显式 git 变更提示，用户可能不知道该迁移需要 commit。
  - `create_regression`（`workflow_helpers.py:3851`）当前 title 默认复用 parent req 的 title，不是 reg 独立源——`harness regression "<issue>"` 的 `<issue>` 参数应成为 reg 独立 title（sug-24）。

## 3. Goal

- 新增 `harness migrate archive`（或等价命令）：扫 `.workflow/flow/archive/main/` 下扁平格式历史归档，按 `{id}-{slug}` 结构迁到 `artifacts/main/archive/requirements/` / `artifacts/main/archive/bugfixes/`；幂等 + dry-run 支持。
- `archive_requirement` / `migrate_requirements` / `migrate_archive` 在归档完成后写 `_meta.yaml`，字段至少含 `id` / `title` / `archived_at` / `origin_stage`。
- `update_repo` / `harness install` 完成 `.harness/feedback.jsonl` 迁移后打印 stderr 提示 `git status -s .workflow/state/feedback/` + 建议用户 commit 迁移变更。
- `create_regression`：title 作为独立必填参数（`--title` 或 positional `<issue>`），不再复用 parent req title。

## 4. Requirement

- req-31（批量建议合集（20条））

## 5. Scope

### 5.1 In scope

- **`src/harness_workflow/workflow_helpers.py`**：
  - 扩展 `migrate_archive`（4840）：扫 `.workflow/flow/archive/main/` 下所有扁平目录（`req-NN-*` / `bugfix-N-*`），按 id 前缀分流到 `artifacts/main/archive/requirements/` 或 `artifacts/main/archive/bugfixes/`；迁移时调用 `_write_archive_meta` 写 `_meta.yaml`；dry-run 不实际移动文件，只打印计划。
  - 新增 `_write_archive_meta(archive_dir: Path, work_item_id: str, title: str, origin_stage: str = "done") -> None` helper：
    - 写入 `archive_dir / "_meta.yaml"`，字段：`id` / `title`（从 state yaml 或目录名 slug 反查）/ `archived_at`（ISO UTC）/ `origin_stage`（done / archive / legacy-migrated）。
    - 已存在 `_meta.yaml` 时保留 `archived_at`（幂等保护），仅更新 `title`（若 state 有更新 title 的场景）。
  - `archive_requirement`（4965）改造：move 完成后调 `_write_archive_meta`。
  - `migrate_requirements`（4752）改造：legacy → primary 迁移的每个目录补写 `_meta.yaml`。
  - `update_repo` `.harness/feedback.jsonl` 迁移分支（3164-3175）：迁移成功后 stderr 打印：
    ```
    [update_repo] NOTE: migrated .harness/feedback.jsonl -> .workflow/state/feedback/feedback.jsonl
    [update_repo] NOTE: run `git status -s .workflow/state/feedback/` and commit the migration.
    ```
  - `create_regression`（3851）：
    - 现有签名 `(root, name, regression_id, title)`；把 `title` 从 "optional 默认复用 parent req" 改为 "必填，来源 CLI positional `<issue>` 参数"；无传入 raise SystemExit。
    - 相关 CLI 入口（`harness regression "<issue>"`）确认 `<issue>` 被原样传给 `title` 参数（目前已是这种签名，本 change 强化"不再 fallback 到 parent req title"）。
- **`src/harness_workflow/cli.py`**：
  - 新增 `migrate archive` 子命令（或扩展现有 `harness update --migrate-archive` flag）：`migrate_parser = subparsers.add_parser("migrate", ...)` + `migrate_parser.add_argument("target", choices=["archive", "requirements"])` + `--dry-run`。
  - `regression_parser` 确认 `title` / `<issue>` 参数必填（若当前 `nargs="?"` 改为 required）。
- **单元测试**：
  - `tests/test_migrate_archive_flat.py`（新增，sug-08）：
    - `test_migrate_archive_moves_flat_to_artifacts`：fixture 建 `.workflow/flow/archive/main/req-50-old/` 扁平目录 → `migrate_archive(root)` → 目录在 `artifacts/main/archive/requirements/req-50-old/` 下。
    - `test_migrate_archive_idempotent`：重复跑不报错，不重复移动。
    - `test_migrate_archive_dry_run`：dry-run 模式不实际移动文件。
  - `tests/test_archive_meta.py`（新增，sug-22）：
    - `test_archive_requirement_writes_meta_yaml`：fixture 归档 req-99 → 目录含 `_meta.yaml` + 字段齐全。
    - `test_archive_meta_idempotent`：重复归档不覆盖已有 `archived_at`。
    - `test_migrate_requirements_backfills_meta`：legacy 归档无 `_meta.yaml` → 迁移后补齐。
    - `test_migrate_archive_writes_meta`：扁平归档迁移后含 `_meta.yaml`。
  - `tests/test_feedback_migration_prompt.py`（新增，sug-20）：
    - `test_update_repo_prints_git_hint_after_feedback_migration`：fixture 建 `.harness/feedback.jsonl` → `update_repo(root)` → stderr 含 "run `git status`" 提示。
    - `test_update_repo_no_hint_without_migration`：无 legacy feedback → 不打印提示。
  - `tests/test_regression_independent_title.py`（新增，sug-24）：
    - `test_create_regression_requires_explicit_title`：`create_regression(root, name=None, title=None)` → raise SystemExit。
    - `test_create_regression_uses_explicit_title_not_parent_req`：parent req title="foo" + reg title="bar" → reg 目录 slug 取 "bar"，state yaml `title == "bar"`。

### 5.2 Out of scope

- 不改归档目录路径结构（仍 `artifacts/{branch}/archive/requirements/{req-id}-{slug}/`）。
- 不回填所有历史 sug body 的 `_meta.yaml`（只处理归档目录级别）。
- 不改 `.harness/feedback.jsonl` 历史数据（只提示，不改数据）。
- 不改 regression 的其他字段（diagnosis / 路由方向由 regression 角色负责）。
- 不处理 contract lint / ff 机制 / CLI 修复（由 chg-01/02/03 负责）。

## 6. 覆盖的 sug 清单（契约 7，id + title）

| sug id | title | 合入方式 |
|--------|-------|---------|
| sug-08（清理 `.workflow/flow/archive/main/` 下扁平格式的 36+ 个历史归档） | `migrate_archive` 扫扁平 + 分流 + dry-run |
| sug-20（主仓 `.harness/feedback.jsonl` 迁移 git 变更提示） | `update_repo` 迁移后 stderr 打印 git 提示 |
| sug-22（chg-04 归档 `_meta.yaml` 落盘，req-30 AC-07 延期内容） | `_write_archive_meta` helper + 4 个归档入口调用 |
| sug-24（regression reg-NN 独立 title 源） | `create_regression` title 必填 + CLI positional 强制 |

## 7. 覆盖的 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-10 | `harness migrate archive` legacy → primary + 归档 `_meta.yaml` 落盘 | Step 1 + Step 2 + 两组单测 |
| AC-11 | feedback.jsonl 迁移提示 + regression reg-NN 独立 title 源 | Step 3 + Step 4 + 两组单测 |

## 8. DoD

1. **DoD-1**：`harness migrate archive` 能把 fixture 仓库 `.workflow/flow/archive/main/req-50-old/` 迁到 `artifacts/main/archive/requirements/req-50-old/`；`tests/test_migrate_archive_flat.py` 三条用例全绿。
2. **DoD-2**：归档目录下存在 `_meta.yaml`，字段 `id` / `title` / `archived_at` / `origin_stage` 完整非空；`tests/test_archive_meta.py` 四条用例全绿。
3. **DoD-3**：`update_repo` 迁移 `.harness/feedback.jsonl` 后 stderr 打印 git 提示；`tests/test_feedback_migration_prompt.py` 两条用例全绿。
4. **DoD-4**：`create_regression` title 必填，无传入抛 SystemExit；reg 目录 slug / state yaml `title` 取显式传入值；`tests/test_regression_independent_title.py` 两条用例全绿。
5. **DoD-综合**：全量 `pytest` 零回归；本 change 产出文档过 `harness status --lint` 得绿。

## 9. 依赖 / 顺序

- **前置**：chg-01（契约自动化）+ chg-02（工作流推进 + ff 机制）+ chg-03（CLI / helper 修复）——本 change 产出文档自检依赖 chg-01；ff_mode 自动关依赖 chg-02；`_next_req_id` 扫归档依赖 chg-03 Step 4（避免迁移期间 id 冲突）。
- **后置**：chg-05 独立，可与本 change 并行或后续。
- **内部 Step 顺序**：Step 1（`_write_archive_meta` helper，sug-22 基础）→ Step 2（`migrate_archive` 扩展，sug-08，依赖 Step 1 写 `_meta.yaml`）→ Step 3（feedback.jsonl 提示，sug-20，独立）→ Step 4（`create_regression` title 强制，sug-24，独立）→ Step 5（回归 + 自证）。Step 3 / 4 可与 Step 1 / 2 并行。

## 10. 风险与缓解

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `migrate_archive` 扁平目录迁移过程中路径冲突（目标目录已存在且内容不同） | 冲突时打印 WARNING + 跳过 + 建议用户手工处理；`--force` flag 覆盖（慎用，提示用户确认） |
| R2 | `_meta.yaml` 的 `title` 在归档后与 state yaml 漂移（如 rename_requirement 后归档但 `_meta.yaml` 仍是旧 title） | `_meta.yaml` 在 rename 路径同步更新；`archive_requirement` 始终从 state yaml 最新 title 读取 |
| R3 | `.harness/feedback.jsonl` 迁移提示被 CI / 非交互环境忽略 | 提示仅作信息性输出（stderr）+ 不阻塞；CI 用户可忽略，人类用户能看到 |
| R4 | `create_regression` title 必填可能破坏现有 regression 入口测试（若之前用隐式 title） | grep `tests/test_regression_helpers.py` 确认所有 fixture 都显式传 title；若有隐式测试，同步更新 |
| R5 | body 丢失推断：sug-08 body 丢失可能有更详细的迁移策略（如某些扁平目录不迁），sug-22 的 `_meta.yaml` 字段清单可能更全 | 本 change 按最小实现；字段清单（id/title/archived_at/origin_stage）是 req-31 §4 AC-10 明确要求；sug-08 范围如果有遗漏允许回补 sug |
| R6 | `.workflow/flow/archive/main/` 下可能有非 req/bugfix 的目录（如 tmp）被误迁 | 迁移前用正则 `^(req|bugfix)-\d+-` 过滤目录名；无匹配的目录保留原位 |
