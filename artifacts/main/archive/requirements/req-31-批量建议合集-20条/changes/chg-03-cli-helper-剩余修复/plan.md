# Change Plan

> 父 change：chg-03（CLI / helper 剩余修复）/ req-31（批量建议合集（20条））

## 1. Development Steps

### Step 1：`_write_with_hash_guard` + `update_repo` 统一调用（sug-13）

- **操作意图**：多生成器共享文件写入引入 hash 竞争保护，防并发覆盖。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::update_repo`（3142）及其内部写入点。
- **关键代码思路**：
  ```python
  import hashlib
  def _write_with_hash_guard(path: Path, content: str) -> bool:
      old_content = path.read_text(encoding="utf-8") if path.exists() else ""
      old_hash = hashlib.sha256(old_content.encode()).hexdigest()
      path.write_text(content, encoding="utf-8")
      # 二次读取验证没有被别的进程并发覆盖
      written = path.read_text(encoding="utf-8")
      written_hash = hashlib.sha256(written.encode()).hexdigest()
      expected_hash = hashlib.sha256(content.encode()).hexdigest()
      if written_hash != expected_hash:
          print(f"[update_repo] WARNING: hash mismatch at {path}; rolling back", file=sys.stderr)
          path.write_text(old_content, encoding="utf-8")
          return False
      return True
  # update_repo 里所有 "path.write_text(...)" 共享文件调用改为 _write_with_hash_guard
  # 共享文件清单（grep update_repo 确定）：
  #   - experience/index.md
  #   - runtime.yaml (仅 update_repo 入口写的部分; save_requirement_runtime 保留独立路径)
  #   - SKILL.md / AGENTS.md / CLAUDE.md
  ```
- **body 丢失补位**：sug-13 title "多生成器共享文件 hash 竞争" 推断来源 = req-31 §4 AC-08 + `update_repo`（3142）目前对共享文件的直接写入 + commit `90a75f6`（update_repo 幂等性）的 idempotent 改造经验。
- **验证方式**：`tests/test_update_repo_hash_guard.py` 两条用例。

### Step 2：`adopt-as-managed` 判据 + `_HARNESS_TEMPLATE_HASHES` 白名单（sug-14）

- **操作意图**：防止 `update_repo` 误覆盖用户自建的同路径文件（典型场景：用户自定义 CLAUDE.md）。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（2862 附近 adopt-as-managed 分支）；可能新增 `src/harness_workflow/template_hashes.py`（模板 hash 清单常量）。
- **关键代码思路**：
  ```python
  # template_hashes.py
  # 保留最近 3 个版本的 CLAUDE.md / AGENTS.md / SKILL.md 模板 hash（update_repo 生成模板内容后 sha256）
  _HARNESS_TEMPLATE_HASHES: dict[str, set[str]] = {
      "CLAUDE.md": {"<hash_v1>", "<hash_v2>", "<hash_v3>"},
      "AGENTS.md": {...},
      "SKILL.md": {...},
  }

  # workflow_helpers.py adopt-as-managed 分支
  def _is_user_authored(path: Path, template_key: str) -> bool:
      if not path.exists(): return False
      content_hash = hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
      return content_hash not in _HARNESS_TEMPLATE_HASHES.get(template_key, set())

  # update_repo 改造：
  if _is_user_authored(target_path, template_key) and not force_managed:
      print(f"[update_repo] skipping user-authored file {target_path}; pass --adopt-as-managed to force.", file=sys.stderr)
      continue  # 跳过覆盖
  _write_with_hash_guard(target_path, new_content)
  ```
- **body 丢失补位**：sug-14 title "用户自建同路径文件的误覆盖风险" 推断来源 = req-31 §4 AC-08 + `workflow_helpers.py:2862` 已有 "bugfix-3 根因 A：adopt-as-managed 分支" 注释 + commit `da91ab3`（bugfix-3 install/update 单 agent 作用域）附近的 adopt-as-managed 实现。
- **验证方式**：`tests/test_adopt_as_managed_protection.py` 三条用例。

### Step 3：CLI `_auto_locate_repo_root` + `main()` 集成（sug-17）

- **操作意图**：CLI 从任何子目录启动都能找到仓库根，提升用户体验。
- **涉及文件**：`src/harness_workflow/cli.py::main`（320）。
- **关键代码思路**：
  ```python
  # cli.py
  _MAX_LOCATE_DEPTH = 20
  def _auto_locate_repo_root(start: Path) -> Path:
      current = start.resolve()
      for _ in range(_MAX_LOCATE_DEPTH):
          if (current / ".workflow").is_dir():
              return current
          if current.parent == current:  # reached filesystem root
              break
          current = current.parent
      raise SystemExit(
          f"[harness] Not a harness repository (no .workflow/ found from {start} upward). "
          f"Run `harness install` first or cd to the repo root."
      )

  # main() 内 args 解析后：
  if args.root == ".":
      root = _auto_locate_repo_root(Path.cwd())
  else:
      root = Path(args.root).resolve()  # 用户显式指定则不 auto-locate
  ```
- **body 丢失补位**：sug-17 title "CLI 对 cwd 敏感, 建议 auto-locate repo root" 推断来源 = req-31 §4 AC-09 + CLI 现有 `--root default="."` 实现 + 用户场景（session-memory / action-log 曾记录 "用户在子目录跑 harness status 失败" 的反馈）。
- **验证方式**：`tests/test_cli_auto_locate.py` 两条用例。

### Step 4：`_next_req_id` / `_next_bugfix_id` 扫归档树（sug-19）

- **操作意图**：避免新建 id 与归档 id 冲突。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::_next_req_id`（3251）/ `_next_bugfix_id`（3283）/ `_next_suggestion_id`（3300）/ `_next_regression_id`（3321）。
- **关键代码思路**：
  ```python
  def _scan_ids_in_dir(dir_path: Path, prefix: str) -> list[int]:
      if not dir_path.exists(): return []
      ids = []
      for p in dir_path.iterdir():
          m = re.match(rf"{prefix}-(\d+)", p.name)
          if m: ids.append(int(m.group(1)))
      return ids

  def _next_req_id(root: Path) -> str:
      branch = _get_git_branch(root) or "main"
      sources = [
          root / ".workflow/state/requirements",
          root / "artifacts" / branch / "requirements",
          root / "artifacts" / branch / "archive" / "requirements",
          root / ".workflow/flow/archive/main",  # legacy 扁平归档（chg-04 迁移前）
      ]
      all_ids = []
      for src in sources:
          all_ids.extend(_scan_ids_in_dir(src, "req"))
      next_n = (max(all_ids) + 1) if all_ids else 1
      return f"req-{next_n:02d}"
  # _next_bugfix_id / _next_regression_id / _next_suggestion_id 同理
  ```
- **body 丢失补位**：sug-19 title "ID 分配器必须扫描归档树" 推断来源 = req-31 §4 AC-09 + req-29 / req-30 批量归档历史（`.workflow/flow/archive/main/` 下 36+ 历史目录）+ commit `1d73f90`（归档 req-29）+ `2dd9db5`（slug 清洗与截断 sug 归档）。
- **验证方式**：`tests/test_id_allocator_scans_archive.py` 三条用例。

### Step 5：回归 + 自证

- **操作意图**：确认 chg-03 不引入既有测试回归；自证契约 7。
- **验证方式**：
  - `pytest` 全量绿。
  - 本 change 产出文档过 `harness status --lint` 得绿（依赖 chg-01）。
  - smoke：`cd src/` → `harness status` 输出正常（依赖 Step 3）。

## 2. Verification Steps

### 2.1 单测 / 集成测清单

| 测试文件 / 用例 | 意图 | 关键断言 |
|----------------|------|---------|
| `tests/test_update_repo_hash_guard.py::test_update_repo_writes_file_with_hash_guard` | 正常路径 | 写入成功 + sha256 匹配 |
| `tests/test_update_repo_hash_guard.py::test_update_repo_reverts_on_hash_mismatch` | mock 并发场景 | 回退到 old content + stderr WARNING |
| `tests/test_adopt_as_managed_protection.py::test_user_authored_file_not_overwritten_without_flag` | 用户自建保护 | 文件内容不变 + stderr 含 "skipping user-authored" |
| `tests/test_adopt_as_managed_protection.py::test_adopt_as_managed_flag_forces_overwrite` | --force 覆盖 | 文件被模板内容覆盖 |
| `tests/test_adopt_as_managed_protection.py::test_template_match_adopts_automatically` | hash 命中白名单 | 无 WARNING，正常覆盖 |
| `tests/test_cli_auto_locate.py::test_cli_runs_from_subdir_locates_repo_root` | 子目录 auto-locate | `harness status` 退出码 0 |
| `tests/test_cli_auto_locate.py::test_cli_raises_clearly_when_no_repo_root` | 非仓库环境 | SystemExit + 明确错误消息 |
| `tests/test_id_allocator_scans_archive.py::test_next_req_id_considers_archived_requirements` | 归档 id 参与计数 | `_next_req_id` 返回最大 id + 1 |
| `tests/test_id_allocator_scans_archive.py::test_next_bugfix_id_considers_archived` | bugfix 归档 id | 同理 |
| `tests/test_id_allocator_scans_archive.py::test_next_req_id_ignores_non_matching_dirs` | 非 id 目录 | 不影响计数 |

### 2.2 Manual smoke verification

- fixture 仓库：
  1. 用户自定义 `CLAUDE.md`（随便写几行）→ `harness update` → 文件**内容不变**，stderr 含 "skipping user-authored"。
  2. `harness update --adopt-as-managed` → 文件被模板覆盖（显式 opt-in）。
  3. `cd src/harness_workflow/` → `harness status` → 成功输出（auto-locate）。
  4. 已归档 req-50 存在 → `harness requirement "smoke"` → 新建 req-51（不重复）。

### 2.3 AC Mapping

- AC-08（剩余部分）→ Step 1 + Step 2 + 两组单测。
- AC-09 → Step 3 + Step 4 + 两组单测。

## 3. body 丢失补位专段

| sug id | title | 推断来源 |
|--------|-------|---------|
| sug-13（`update_repo` 多生成器共享文件 hash 竞争） | req-31 §4 AC-08 + `update_repo`（3142）共享文件写入 + commit `90a75f6` |
| sug-14（`adopt-as-managed` 判据对用户自建同路径文件的误覆盖风险） | 源码 `workflow_helpers.py:2862` 已有 bugfix-3 根因注释 + commit `da91ab3` |
| sug-17（CLI 对 cwd 敏感） | req-31 §4 AC-09 + CLI 现有 `--root default="."` 实现 |
| sug-19（ID 分配器扫归档树） | req-31 §4 AC-09 + `.workflow/flow/archive/main/` 36+ 历史目录 + commit `1d73f90`/`2dd9db5` |

## 4. 回滚策略

- **粒度**：按 Step 1-5 拆分 git 提交；每个 Step 独立 revert。
- **回滚触发**：
  - Step 1 若 `_write_with_hash_guard` 回退逻辑引入"写入失败被静默吞掉"（影响 update_repo 正常路径）→ 降级为"仅检测不回退"，WARNING 后继续。
  - Step 2 若 `_HARNESS_TEMPLATE_HASHES` 白名单导致历史用户的 CLAUDE.md 全被判定为 user-authored（更新不再生效）→ 加 `--adopt-as-managed` 自动触发条件或文档化首次启用。
  - Step 3 若 `_auto_locate_repo_root` 向上查找误命中父目录（如 monorepo 的根级 `.workflow/`）→ 改为同时检查 `WORKFLOW.md` 文件存在。
  - Step 4 若归档树扫描性能回归（归档目录过大）→ 加缓存（扫一次结果缓存在 runtime.yaml `_next_id_cache`）。
- **兜底**：所有修改集中在 `workflow_helpers.py` + `cli.py` + 新增 `template_hashes.py` + 新增 tests；`git revert` 单次可撤销。

## 5. 执行依赖顺序

1. Step 1 / Step 2 / Step 3 / Step 4 **独立**，可并行实施。
2. 建议顺序 commit：Step 1 → Step 2（Step 2 依赖 Step 1 的 `_write_with_hash_guard`）→ Step 3 → Step 4。
3. Step 5（回归）最后。

**前置依赖**：chg-01（契约自动化）+ chg-02（工作流推进 + ff 机制）——本 change 对人文档自检依赖 chg-01 的 `harness status --lint`；ff_mode 自动关依赖 chg-02。

## 6. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `_write_with_hash_guard` read-then-write 无锁 | 不追求真正并发安全，仅防误写；update_repo 单线程运行 |
| R2 | `_HARNESS_TEMPLATE_HASHES` 白名单迭代成本 | 保留最近 3 版本 + `update_repo --check` 打印 hash 对比 |
| R3 | `_auto_locate_repo_root` 向上查找跨 mount / 无限递归 | 深度 20 + mount 检测 |
| R4 | `_next_req_id` 扫描归档包含其他 branch / fork 的目录 | scope 限定为 `_get_git_branch(root)` 对应的 branch |
| R5 | body 丢失导致 sug 细节不全（尤其 sug-17 的 "auto-locate 语义"可能原 body 有更精确设想） | 本方案按最小实现；若 executing 阶段发现遗漏允许回补 sug |
