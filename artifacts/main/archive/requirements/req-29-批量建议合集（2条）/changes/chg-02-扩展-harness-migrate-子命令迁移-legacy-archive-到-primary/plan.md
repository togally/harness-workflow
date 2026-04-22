# Change Plan

## 1. Development Steps

### Step 1: 设计 migrate_archive helper 算法

- 在 `src/harness_workflow/workflow_helpers.py` 增加：
  - `migrate_archive(root: Path, dry_run: bool = False) -> int`
  - 扫描 `.workflow/flow/archive/` 下所有直接子条目，按两种形态处理：
    - `main/` / `<branch>/` 前缀：整体迁到 `artifacts/<branch>/archive/...`（保留子树结构）。
    - 无分支前缀的裸条目（如历史 `req-20-...`）：迁到 `artifacts/main/archive/<条目名>`。
  - 输出：已迁移、跳过（幂等）、冲突三类清单。

### Step 2: 实现 copy-then-verify-then-unlink

- 对每个待迁移条目：
  1. 计算源目录 `rel` 相对路径与目标路径。
  2. 若目标已存在：递归比对文件列表 + 每文件 hash（使用 `hashlib.sha256`）；一致 → 跳过记 `already migrated`；不一致 → 加入冲突列表，不动。
  3. 目标不存在：`shutil.copytree(src, dst)` → 迁移后再次 walk 对比源/目标文件数与 hash 一致 → 成功后 `shutil.rmtree(src)`；任意验证失败 → 立即 `shutil.rmtree(dst)` 回滚、报错。
- 所有条目处理完后，若 `.workflow/flow/archive/<branch>/` 为空，可选保留 `.gitkeep`；不递归删除父目录。

### Step 3: 扩展 CLI `harness_migrate.py`

- `resource` choices 增加 `"archive"`。
- dispatch：`args.resource == "archive"` → `migrate_archive(root, dry_run=args.dry_run)`。
- 帮助文本更新：说明 `archive` 与 `requirements` 的语义差异与 dry-run 建议。

### Step 4: 新增 `tests/test_migrate_archive.py`

- `test_migrate_archive_happy_path`：构造 legacy 下 `req-xx/` + `main/req-yy/` → 调用迁移 → 断言目标路径存在、源清空、返回 0。
- `test_migrate_archive_idempotent`：连跑两次 → 第二次无变化、退出码 0、打印 `already migrated`。
- `test_migrate_archive_conflict`：目标已存在且内容不同 → 冲突列表非空、退出码非零、源不动、目标不动。
- `test_migrate_archive_dry_run`：传 `--dry-run` → 打印计划、源与目标均不变。
- `test_migrate_archive_multi_branch`：legacy 同时有 `main/...` 与 `feature-x/...` → 分别迁到各自 primary。

### Step 5: 手工回归

- 在本仓库（含真实 legacy 归档）执行 `harness migrate archive --dry-run`，核对打印的计划包含 req-26 / req-27 / req-28 / bugfix-3 / bugfix-4 / bugfix-5 / bugfix-6 等预期条目。
- 再执行真实迁移；迁移后 `harness status` / `harness archive` 无 `using legacy archive path` 警告。
- 立即再跑一次迁移命令 → 退出码 0、打印 `already migrated`（幂等）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_migrate_archive.py -v`：5 个用例全绿。
- `pytest tests/test_archive_path.py -v`：chg-01 的用例不回归。
- `grep -rn "using legacy archive path" src` 与 `tests`：仅在 warning 构造点出现。

### 2.2 Manual smoke / integration verification

- 本仓（真实 legacy 数据）执行迁移流程见 Step 5。
- 人工核对：迁移后 `artifacts/main/archive/` 下应包含 `req-26-uav-split/`、`bugfix-3/` 等；`.workflow/flow/archive/` 仅剩空目录或 `.gitkeep`。

### 2.3 AC Mapping

- AC-04 → Step 2 + Step 3 + Step 5 + 2.1。

## 3. Dependencies & Execution Order

- **强依赖 chg-01**：本 change 必须在 chg-01 合入后才跑（否则 `harness status` 迁移后仍可能报 legacy 警告，验收会失败）。
- 与 chg-03 / chg-04 / chg-05 无文件冲突，可与其并行但整体顺序建议 chg-01 → chg-02 → chg-03 → chg-04 → chg-05。
