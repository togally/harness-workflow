# Change Plan

> 父 change：chg-04（归档迁移 + 数据管道）/ req-31（批量建议合集（20条））

## 1. Development Steps

### Step 1：`_write_archive_meta` helper（sug-22 基础）

- **操作意图**：归档目录落盘 `_meta.yaml`，支撑后续 batch 扫描脚本和人可读追溯。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（可放在 `archive_requirement` 4965 之前）。
- **关键代码思路**：
  ```python
  def _write_archive_meta(
      archive_dir: Path,
      work_item_id: str,
      title: str,
      origin_stage: str = "done",
  ) -> None:
      meta_path = archive_dir / "_meta.yaml"
      payload: dict[str, object] = {
          "id": work_item_id,
          "title": title or "",
          "archived_at": datetime.now(timezone.utc).isoformat(),
          "origin_stage": origin_stage,
      }
      # 幂等：已存在则保留 archived_at，仅刷新 title
      if meta_path.exists():
          existing = load_simple_yaml(meta_path)
          if isinstance(existing, dict) and existing.get("archived_at"):
              payload["archived_at"] = existing["archived_at"]
      save_simple_yaml(meta_path, payload)
  ```
- **body 丢失补位**：sug-22 title "chg-04 归档 `_meta.yaml` 落盘（req-30 AC-07 延期内容）" 推断来源 = req-30 chg-04 change.md（已读，AC-07 延期实现方案 A）+ req-31 §4 AC-10 明确字段清单 + req-30 chg-04 plan.md Step 1-6。
- **验证方式**：`tests/test_archive_meta.py::test_archive_requirement_writes_meta_yaml`。

### Step 2：`migrate_archive` 扁平归档迁移（sug-08）

- **操作意图**：把 `.workflow/flow/archive/main/` 下扁平格式的历史归档迁到 `artifacts/{branch}/archive/`，同时落 `_meta.yaml`。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::migrate_archive`（4840）；`src/harness_workflow/cli.py`（新增 `migrate` 子命令或扩展现有）。
- **关键代码思路**：
  ```python
  def migrate_archive(root: Path, dry_run: bool = False) -> int:
      legacy_archive = root / ".workflow" / "flow" / "archive" / "main"
      if not legacy_archive.exists():
          print("No legacy archive to migrate.")
          return 0
      branch = _get_git_branch(root) or "main"
      target_req = root / "artifacts" / branch / "archive" / "requirements"
      target_bug = root / "artifacts" / branch / "archive" / "bugfixes"
      moved = []
      for item in sorted(legacy_archive.iterdir()):
          if not item.is_dir(): continue
          m = re.match(r"^(?P<id>(req|bugfix)-\d+)-(?P<slug>.+)$", item.name)
          if not m: continue  # 非 id 目录跳过
          target_base = target_req if m.group(2) == "req" else target_bug
          dst = target_base / item.name
          if dst.exists():
              print(f"[migrate_archive] SKIP {item.name}: target exists", file=sys.stderr)
              continue
          if dry_run:
              print(f"[dry-run] would move {item} -> {dst}")
          else:
              target_base.mkdir(parents=True, exist_ok=True)
              shutil.move(str(item), str(dst))
              # 读 state yaml 取 title（若存在）
              title = _resolve_title_for_id(root, m.group("id")) or m.group("slug")
              _write_archive_meta(dst, m.group("id"), title, origin_stage="legacy-migrated")
          moved.append(item.name)
      print(f"Migrated {len(moved)} legacy archive(s).")
      return 0

  # cli.py
  migrate_parser = subparsers.add_parser("migrate", help="Migrate legacy data.")
  migrate_parser.add_argument("target", choices=["archive", "requirements"])
  migrate_parser.add_argument("--dry-run", action="store_true")
  migrate_parser.add_argument("--root", default=".")
  # main() dispatch:
  if args.command == "migrate" and args.target == "archive":
      return migrate_archive(root, dry_run=args.dry_run)
  ```
- **body 丢失补位**：sug-08 title "清理 `.workflow/flow/archive/main/` 下扁平格式的 36+ 个历史归档" 推断来源 = req-31 §4 AC-10 + req-29 chg-02 commit history（migrate_requirements / migrate_archive 已有基础）+ `.workflow/flow/archive/main/` 当前文件清单（glob 验证扁平格式是否仍存在）+ commit `1d73f90`（归档 req-29 到 primary 路径 + migrate 5 个历史归档）。
- **验证方式**：`tests/test_migrate_archive_flat.py` 三条用例。

### Step 3：`update_repo` feedback.jsonl 迁移 git 提示（sug-20）

- **操作意图**：用户感知 feedback.jsonl 迁移产生的 git 变更。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::update_repo`（3164-3175）。
- **关键代码思路**：
  ```python
  if old_feedback.exists() and not new_feedback.exists():
      new_feedback.parent.mkdir(parents=True, exist_ok=True)
      shutil.move(str(old_feedback), str(new_feedback))
      legacy_dir = old_feedback.parent
      if legacy_dir.exists() and not any(legacy_dir.iterdir()):
          legacy_dir.rmdir()
      actions.append("migrated .harness/feedback.jsonl -> .workflow/state/feedback/feedback.jsonl")
      # 新增：stderr git 提示
      print(
          f"[update_repo] NOTE: migrated .harness/feedback.jsonl -> .workflow/state/feedback/feedback.jsonl\n"
          f"[update_repo] NOTE: run `git status -s .workflow/state/feedback/` and commit the migration.",
          file=sys.stderr,
      )
  ```
- **body 丢失补位**：sug-20 title "主仓 `.harness/feedback.jsonl` 迁移 git 变更提示" 推断来源 = req-31 §4 AC-11 + `update_repo`（3164-3175）现有 actions.append 但无 stderr 提示 + `da91ab3`（feedback.jsonl 落层归位 TDD 6 用例）。
- **验证方式**：`tests/test_feedback_migration_prompt.py` 两条用例。

### Step 4：`create_regression` title 独立必填（sug-24）

- **操作意图**：reg-NN 有独立 title 源，不再复用 parent req。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::create_regression`（3851）；`src/harness_workflow/cli.py`（`regression_parser`）。
- **关键代码思路**：
  ```python
  # create_regression 签名现为 (root, name, regression_id=None, title=None)
  def create_regression(root, name, regression_id=None, title=None):
      # title 从 positional name 获取（CLI `harness regression "<issue>"` 的 <issue>）
      regression_title = (title or name or "").strip()
      if not regression_title:
          raise SystemExit("A regression title/issue is required (sug-24 / chg-04).")
      # slug 取 regression_title 而非 parent req title
      slug = _path_slug(regression_title)
      # state yaml title 字段取 regression_title
      ...
  ```
- **body 丢失补位**：sug-24 title "regression reg-NN 独立 title 源" 推断来源 = req-31 §4 AC-11 + 现有 `create_regression`（3851）签名 + `.workflow/context/roles/regression.md`（reg 粒度对人文档）。
- **验证方式**：`tests/test_regression_independent_title.py` 两条用例。

### Step 5：`archive_requirement` / `migrate_requirements` 集成 `_write_archive_meta`

- **操作意图**：所有归档路径（正常归档 + legacy 迁移 + 扁平迁移）都落 `_meta.yaml`。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::archive_requirement`（4965）/ `migrate_requirements`（4752）。
- **关键代码思路**：
  ```python
  # archive_requirement 末尾（move 完成后）：
  state_title = _resolve_title_for_id(root, req_id)
  _write_archive_meta(archive_dst, req_id, state_title, origin_stage="done")

  # migrate_requirements 对每个迁移目标：
  _write_archive_meta(new_dst, req_id, state_title, origin_stage="legacy-migrated")
  ```
- **验证方式**：`tests/test_archive_meta.py::test_migrate_requirements_backfills_meta` + `test_migrate_archive_writes_meta`。

### Step 6：回归 + 自证

- **操作意图**：全量测试绿 + 契约 7 自证。
- **验证方式**：
  - `pytest` 全量绿。
  - 本 change 产出文档过 `harness status --lint` 得绿（依赖 chg-01）。
  - smoke：fixture 仓库跑 `harness migrate archive --dry-run` → 列出迁移计划。

## 2. Verification Steps

### 2.1 单测 / 集成测清单

| 测试文件 / 用例 | 意图 | 关键断言 |
|----------------|------|---------|
| `tests/test_archive_meta.py::test_archive_requirement_writes_meta_yaml` | 正常归档写 `_meta.yaml` | 字段齐全 |
| `tests/test_archive_meta.py::test_archive_meta_idempotent` | 重复归档幂等 | `archived_at` 保留 |
| `tests/test_archive_meta.py::test_migrate_requirements_backfills_meta` | legacy 迁移补 `_meta.yaml` | 新目录含 `_meta.yaml` |
| `tests/test_archive_meta.py::test_migrate_archive_writes_meta` | 扁平迁移补 `_meta.yaml` | origin_stage=="legacy-migrated" |
| `tests/test_migrate_archive_flat.py::test_migrate_archive_moves_flat_to_artifacts` | 扁平 → artifacts | 目录在 artifacts/main/archive/requirements/ |
| `tests/test_migrate_archive_flat.py::test_migrate_archive_idempotent` | 重复运行 | 不重复移动 |
| `tests/test_migrate_archive_flat.py::test_migrate_archive_dry_run` | dry-run | 不实际移动 |
| `tests/test_feedback_migration_prompt.py::test_update_repo_prints_git_hint_after_feedback_migration` | 迁移后 git 提示 | stderr 含 "run `git status`" |
| `tests/test_feedback_migration_prompt.py::test_update_repo_no_hint_without_migration` | 无迁移不提示 | stderr 不含 NOTE |
| `tests/test_regression_independent_title.py::test_create_regression_requires_explicit_title` | title 必填 | raise SystemExit |
| `tests/test_regression_independent_title.py::test_create_regression_uses_explicit_title_not_parent_req` | title 独立源 | reg slug / yaml title == 显式值 |

### 2.2 Manual smoke verification

- fixture 仓库：
  1. `.workflow/flow/archive/main/req-50-old/` 建扁平目录 → `harness migrate archive --dry-run` → 打印迁移计划（不实际移动）→ `harness migrate archive` → 目录迁到 `artifacts/main/archive/requirements/req-50-old/` + 含 `_meta.yaml`。
  2. `harness update` 触发 `.harness/feedback.jsonl` 迁移 → stderr 含 "run `git status`" 提示。
  3. `harness regression "测试独立 title"` → reg 目录 slug 含"测试独立 title" 清洗结果（非 parent req title）。
  4. `archive_requirement` 对当前 req-31 归档后 → `artifacts/main/archive/requirements/req-31-*/\_meta.yaml` 存在。

### 2.3 AC Mapping

- AC-10 → Step 1 + Step 2 + Step 5 + `tests/test_archive_meta.py` + `tests/test_migrate_archive_flat.py`。
- AC-11 → Step 3 + Step 4 + `tests/test_feedback_migration_prompt.py` + `tests/test_regression_independent_title.py`。

## 3. body 丢失补位专段

| sug id | title | 推断来源 |
|--------|-------|---------|
| sug-08（清理 `.workflow/flow/archive/main/` 下扁平格式的 36+ 个历史归档） | req-31 §4 AC-10 + req-29 chg-02 migrate_requirements 已有基础 + commit `1d73f90` |
| sug-20（主仓 `.harness/feedback.jsonl` 迁移 git 变更提示） | req-31 §4 AC-11 + `update_repo`（3164-3175）现有 actions.append + commit `da91ab3` |
| sug-22（chg-04 归档 `_meta.yaml` 落盘） | **已读 req-30 chg-04 change.md + plan.md**（完整保留方案 A 的 helper 设计和字段清单）+ req-31 §4 AC-10 |
| sug-24（regression reg-NN 独立 title 源） | req-31 §4 AC-11 + `create_regression`（3851）现有签名 + `.workflow/context/roles/regression.md` |

## 4. 回滚策略

- **粒度**：按 Step 1-6 拆分 git 提交。
- **回滚触发**：
  - Step 2 若扁平迁移对现有 `.workflow/flow/archive/main/` 有数据的仓库误迁（路径冲突） → 加 `--force` 保护；默认遇冲突跳过。
  - Step 3 若 CI 环境将 stderr 当作错误信号 → stderr 改为 stdout INFO 级别；或加 `--quiet` flag。
  - Step 4 若现有 `tests/test_regression_helpers.py` 有 fixture 不显式传 title → 全部 grep 同步更新；保留"若 title 为空则 fallback 到 id"的极端兜底（打 WARNING）。
- **兜底**：修改集中在 `workflow_helpers.py` + `cli.py` + 新增 tests；`git revert` 单次撤销。

## 5. 执行依赖顺序

1. Step 1（`_write_archive_meta` helper）**最先**——Step 2 / Step 5 都依赖。
2. Step 2（migrate_archive 扁平迁移）依赖 Step 1。
3. Step 3（feedback 提示）独立，可与 Step 1/2 并行。
4. Step 4（`create_regression` title）独立，可与 Step 1/2/3 并行。
5. Step 5（归档入口集成）依赖 Step 1。
6. Step 6（回归 + 自证）最后。

**前置依赖**：chg-01 + chg-02 + chg-03 全部落地。

## 6. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `migrate_archive` 目标目录已存在冲突 | 默认跳过 + stderr WARNING；`--force` 覆盖需用户确认 |
| R2 | `_meta.yaml` title 与 state yaml 漂移 | rename_requirement 同步更新；`archive_requirement` 始终从 state 读最新 title |
| R3 | stderr 提示被 CI 吞掉 | 信息性输出，不阻塞；CI 用户可忽略 |
| R4 | `create_regression` title 必填破坏测试 | grep 已有 test 全覆盖；兜底 fallback to id + WARNING |
| R5 | body 丢失细节（sug-08 / sug-22 最多依赖 req-30 chg-04 现有产物补位） | 本方案最小实现；executing 阶段允许回补 sug |
| R6 | `.workflow/flow/archive/main/` 下可能有非 req/bugfix 目录（如 tmp / notes） | 正则 `^(req\|bugfix)-\d+-` 过滤；非匹配目录保留原位 + 打印 INFO |
