# Change

## 1. Title

chg-03（CLI / helper 剩余修复）：`update_repo` hash 竞争保护 + `adopt-as-managed` 误覆盖保护 + CLI auto-locate repo root + `harness bugfix` / `harness requirement` ID 分配器扫归档树

> 父需求：req-31（批量建议合集（20条））

## 2. Background

源自 req-31（批量建议合集（20条））§5 Split Rules 的 **chg-03 分组**（D 组剩余 CLI / helper 修复，共 4 条 sug），以及 §4 的 **AC-08（剩余部分）+ AC-09**：

- **现状**：
  - `update_repo`（`workflow_helpers.py:3142`）刷新多生成器共享文件（`experience/index.md` / `runtime.yaml` / SKILL.md 等）时无 hash 竞争保护——如果并发或重复调用写入同一文件，后写覆盖前写；虽然当前无明显回归，但 req-30 chg-01 state schema 改造时已观察到 "runtime.yaml 字段顺序漂移" 的类似隐患。
  - `adopt-as-managed` 判据（`workflow_helpers.py:2862` 附近，bugfix-3 根因 A）决定是否把用户自建文件纳入 harness 管理；当前判据过宽，可能误覆盖用户自建的同路径文件（如自定义 CLAUDE.md）。
  - `harness` CLI 对 cwd 敏感——必须在仓库根才能跑；在子目录（如 `src/` / `artifacts/main/`）下跑会失败，用户体验差。
  - `harness bugfix` / `harness requirement` 的 ID 分配器（`_next_req_id` / `_next_bugfix_id`，`workflow_helpers.py:3251 / 3283`）只扫 `.workflow/state/` 目录，不扫归档树；可能分配已归档的 id 造成冲突（req-29 / req-30 批量归档后曾出现风险）。

## 3. Goal

- `update_repo` 多生成器共享文件引入 hash 竞争保护：写入前先读旧内容计算 sha256，写入后核对；并发 / 竞争触发时回退并打印 warning。
- `adopt-as-managed` 判据收紧：对用户自建同路径文件引入 "content-hash + 显式 opt-in" 双保险，避免误覆盖。
- CLI 引入 `_auto_locate_repo_root(cwd)` helper：从 cwd 向上查找 `.workflow/` 目录作为 harness repo root；找到后在任意子目录都能跑。
- `_next_req_id` / `_next_bugfix_id` 扩展：扫描归档树（`artifacts/{branch}/archive/requirements/` / `.workflow/flow/archive/`）计算 max id + 1，避免与归档 id 冲突。

## 4. Requirement

- req-31（批量建议合集（20条））

## 5. Scope

### 5.1 In scope

- **`src/harness_workflow/workflow_helpers.py`**：
  - `update_repo`（3142）：新增 `_write_with_hash_guard(path, content) -> bool` helper：
    - 写入前读 old content → 计算 old hash；
    - `path.write_text(content)` 后再读 new content → 计算 new hash 验证 = sha256(content)；
    - 如果期间 old hash 变了（多生成器并发），回退（`path.write_text(old_content)`）+ 打印 stderr warning，返回 False。
    - `update_repo` 对多生成器共享文件（`experience/index.md` / `runtime.yaml` / `SKILL.md` / CLAUDE.md）统一调用 `_write_with_hash_guard`。
  - `adopt-as-managed` 判据（`workflow_helpers.py:2862` 附近）：
    - 新增 "用户自建" 标记：若目标文件已存在且 sha256 不在 harness 默认模板 hash 白名单（`_HARNESS_TEMPLATE_HASHES`）中 → 标记为 "user-authored"，update_repo 跳过覆盖 + 打印 "skipping user-authored file {path}; pass --adopt-as-managed to force."
    - `update_repo` 新增 `--adopt-as-managed` CLI flag（或 `force_managed` 已有参数）：只有显式传才能覆盖用户自建文件。
  - `_next_req_id` / `_next_bugfix_id`（3251 / 3283）：
    - 扫描范围扩展到：
      1. `.workflow/state/requirements/` / `.workflow/state/bugfixes/`（现有）
      2. `artifacts/{branch}/requirements/` 当前活跃（目录名前缀匹配 `req-NN-` / `bugfix-NN-`）
      3. `artifacts/{branch}/archive/requirements/` / `.workflow/flow/archive/main/`（归档目录）
    - 取 3 个来源的 max id + 1。
  - `_next_regression_id` / `_next_suggestion_id` 同样逻辑扩展（顺带修复，保持一致性）。
- **`src/harness_workflow/cli.py`**：
  - 新增 `_auto_locate_repo_root(start: Path) -> Path`：从 start 向上最多 20 层查找 `.workflow/` 目录；找到返回；找不到 raise SystemExit with clear message。
  - `main()` 入口（第 320 行附近）在 argparse 后、dispatch 前调 `_auto_locate_repo_root(Path(args.root).resolve())`，把解析结果作为 root 传入各 helper。
  - `--root` 默认值 "." 保留；用户显式传 `--root /path` 时跳过 auto-locate。
- **单元测试**：
  - `tests/test_update_repo_hash_guard.py`（新增，sug-13）：
    - `test_update_repo_writes_file_with_hash_guard`：`experience/index.md` 写入 → sha256 验证。
    - `test_update_repo_reverts_on_hash_mismatch`：mock `path.read_text` 第二次返回不同内容 → 触发 rollback + stderr WARNING。
  - `tests/test_adopt_as_managed_protection.py`（新增，sug-14）：
    - `test_user_authored_file_not_overwritten_without_flag`：fixture 先写用户自定义 CLAUDE.md（hash 不在白名单）→ `update_repo()` → 文件内容不变 + stderr 含 "skipping user-authored"。
    - `test_adopt_as_managed_flag_forces_overwrite`：同上 + `force_managed=True` → 文件被 harness 模板覆盖。
    - `test_template_match_adopts_automatically`：CLAUDE.md 内容匹配某 harness 模板 hash → update_repo 直接覆盖（正常路径）。
  - `tests/test_cli_auto_locate.py`（新增，sug-17）：
    - `test_cli_runs_from_subdir_locates_repo_root`：在 `tmp/.workflow/...` 下建 harness 仓库 → `chdir tmp/src/` → `harness status` 成功（非零退出前不应报 "not a harness repo"）。
    - `test_cli_raises_clearly_when_no_repo_root`：无 `.workflow/` 目录 → raise SystemExit with actionable message。
  - `tests/test_id_allocator_scans_archive.py`（新增，sug-19）：
    - `test_next_req_id_considers_archived_requirements`：fixture 归档 req-50 + 活跃 req-10 → `_next_req_id` 返回 "req-51"。
    - `test_next_bugfix_id_considers_archived`：同逻辑。
    - `test_next_req_id_ignores_non_matching_dirs`：`artifacts/main/requirements/random-dir/` 不影响计数。

### 5.2 Out of scope

- 不改 `update_repo` 的作用域逻辑（bugfix-3 已改造，req-31 不再动）。
- 不做归档树的 `_meta.yaml` 补写（chg-04 负责，sug-22）。
- 不改 slug / id 编号规则（延续 req-30 排除项）。
- 不改 `harness` CLI 其他子命令的参数（只在 `main()` 层加 auto-locate）。
- 不合并 chg-05（legacy yaml strip 兜底）——本 change 保持独立；chg-05 独立存在便于追溯（详见 §10 合并建议）。
- 不处理契约自检（由 chg-01 负责）/ ff 机制（由 chg-02 负责）/ 归档迁移（由 chg-04 负责）。

## 6. 覆盖的 sug 清单（契约 7，id + title）

| sug id | title | 合入方式 |
|--------|-------|---------|
| sug-13（`update_repo` 多生成器共享文件 hash 竞争） | `_write_with_hash_guard` helper + `update_repo` 统一调用 |
| sug-14（`adopt-as-managed` 判据对用户自建同路径文件的误覆盖风险） | `adopt-as-managed` 判据收紧 + `_HARNESS_TEMPLATE_HASHES` 白名单 |
| sug-17（`harness` CLI 对 cwd 敏感，建议 auto-locate repo root） | `_auto_locate_repo_root` 向上查找 + `main()` 集成 |
| sug-19（`harness bugfix` / `harness requirement` ID 分配器必须扫描归档树） | `_next_*_id` 扩展扫描范围（state + 活跃 + 归档） |

## 7. 覆盖的 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-08（剩余部分）| `update_repo` hash 竞争保护 + `adopt-as-managed` 覆盖保护 | Step 1 + Step 2 + 两组单测 |
| AC-09 | CLI auto-locate repo root + ID 分配器扫归档树 | Step 3 + Step 4 + 两组单测 |

## 8. DoD

1. **DoD-1**：`update_repo` 刷新 `experience/index.md` / `runtime.yaml` / `SKILL.md` 时统一走 `_write_with_hash_guard`；`tests/test_update_repo_hash_guard.py` 两条用例全绿。
2. **DoD-2**：`adopt-as-managed` 对用户自建 CLAUDE.md 默认跳过 + stderr WARNING；`tests/test_adopt_as_managed_protection.py` 三条用例全绿。
3. **DoD-3**：`harness status` 可从 `src/` / `artifacts/main/` 等子目录启动；`tests/test_cli_auto_locate.py` 两条用例全绿。
4. **DoD-4**：`_next_req_id` / `_next_bugfix_id` 扫描归档树取 max；`tests/test_id_allocator_scans_archive.py` 三条用例全绿。
5. **DoD-综合**：全量 `pytest` 零回归；本 change 产出文档过 `harness status --lint` 得绿。

## 9. 依赖 / 顺序

- **前置**：chg-01（契约自动化）——本 change 对人文档自检依赖 `harness status --lint`；chg-02（工作流推进 + ff 机制）——本 change 实施期间 ff_mode 可能短暂开启，需要 chg-02 的自动关保护。
- **后置**：chg-04 / chg-05 可依赖本 change 的 `_auto_locate_repo_root` + ID 分配器稳定（但无代码耦合，顺序依赖即可）。
- **内部 Step 顺序**：Step 1（update_repo hash guard）→ Step 2（adopt-as-managed 判据）→ Step 3（CLI auto-locate）→ Step 4（ID 分配器）→ Step 5（回归 + 自证）。Step 1-4 可并行实施，但建议按上述顺序 commit 以便 review。

## 10. 风险与缓解

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `_write_with_hash_guard` 在 ext4 / macOS 默认文件系统下 read-then-write 之间无真正锁，并发时仍可能丢更新 | 仅作为"二次校验"机制；实际并发写入由调用方（`update_repo` 单线程）控制，helper 的作用是检测异常+回退；不做进程级锁（过度设计）|
| R2 | `_HARNESS_TEMPLATE_HASHES` 白名单随模板迭代失效（模板升级后老 hash 不在白名单 → 用户自定义误判为"模板原件已过期"）| 白名单至少保留最近 3 个版本的 hash；`update_repo --check` 模式打印 hash 对比表；sug-22 `_meta.yaml` 落盘（chg-04）可辅助追溯 |
| R3 | `_auto_locate_repo_root` 向上查找无限递归或跨 mount point 失败 | 深度上限 20 层 + 跨根 `/` 立即停止；mount point 检测用 `path.parent == path` 判定 |
| R4 | `_next_req_id` 扫归档可能误扫到其他项目 fork 的归档目录（如用户 clone 了别人的 repo 做 checkout） | 扫描 scope 限定为 `artifacts/{branch}/...` 其中 `branch = _get_git_branch(root)`；非当前 branch 归档不计入 |
| R5 | body 丢失推断：sug-13 / sug-14 / sug-17 / sug-19 的 body 已被 apply-all bug 删除，细节不全 | 参考 §plan.md body 丢失补位专段；executing 阶段若发现遗漏允许回补 sug |
| R6 | 合并 chg-05 的讨论（§10）：chg-05 是否并入 chg-03？| **建议保持独立**：chg-05 修改面极小（`render_work_item_id` 读 title 时 `.strip("'\" ")`），独立有利于回溯；合并后测试用例混淆。见 chg-05 change.md §11 |
