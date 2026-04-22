# Change Plan

## 1. Development Steps

### Step 1: 梳理现状并敲定 opt-in 机制

- `src/harness_workflow/workflow_helpers.py` 定位 `resolve_archive_root`（约 4280 行），确认当前判据链：primary 非空 → primary；否则 legacy 非空 → legacy 告警；否则 primary。
- 敲定 opt-in 机制（二选一；在 plan 执行时由 executing 角色做 low-risk 决策并记录到 decisions-log）：
  - 方案 A（推荐）：新增关键字参数 `prefer_legacy: bool = False`，调用方显式 opt-in。
  - 方案 B（兜底）：读环境变量 `HARNESS_ARCHIVE_LEGACY`，值为 "1" 时 opt-in。
- 扫描 `src` 下所有 `resolve_archive_root(` 调用点，确认是否有需要同步改签名的调用方。

### Step 2: 修改 `resolve_archive_root` 判据

- 新判据链（无 opt-in 时）：
  1. 若 legacy 非空 → 打印 stderr 告警（`using primary archive path; legacy at ... has data, run harness migrate archive to consolidate`）；继续走第 2 步。
  2. 默认返回 primary，由调用方 `mkdir`。
- opt-in 分支：`prefer_legacy=True`（或环境变量命中）时，若 legacy 非空直接返回 legacy，保留原告警行为；legacy 空时仍返回 primary。
- 保持函数签名兼容：新参数必须有默认值；不增加必选参数。

### Step 3: 扩展 `tests/test_archive_path.py`

- 新增用例 `test_archive_root_prefers_primary_when_legacy_nonempty`：构造 legacy 有内容 + primary 空，断言返回 primary、stderr 出现迁移提示。
- 新增用例 `test_archive_root_opt_in_legacy_returns_legacy`：使用 opt-in 机制，断言返回 legacy。
- 核对原有测试：若存在"legacy 非空 → 返回 legacy（不 opt-in）"断言，按新契约改写或标注为 opt-in 场景。

### Step 4: 扫描调用方

- `grep -rn resolve_archive_root src` 列出所有调用方；确认无人依赖"legacy 降级"的老行为；若有，调用方显式传 `prefer_legacy=True`（迁移期间）。
- 特别关注 `archive_requirement` 相关路径和 `harness_status` 调用链。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_archive_path.py -v`：全部通过；新增 2 个用例命中。
- `grep -rn "resolve_archive_root" src`：所有调用方语义确认与新签名兼容。
- `git diff` 审查：除本函数 + 测试外无其他改动；函数签名默认参数未改变既有调用方。

### 2.2 Manual smoke / integration verification

- 手工构造 fixture 仓库：`mkdir -p .workflow/flow/archive/main/req-xx && touch .workflow/flow/archive/main/req-xx/foo.md`；执行 `harness status` → stderr 出现一次迁移提示，但 `resolve_archive_root` 返回 `artifacts/{branch}/archive`。
- opt-in 场景：设置 `HARNESS_ARCHIVE_LEGACY=1`（或传 `prefer_legacy=True`）→ 返回 legacy 路径。

### 2.3 AC Mapping

- AC-03 → Step 2 + Step 3 + 2.1；Step 4 保障回归面。

## 3. Dependencies & Execution Order

- 本 change 是 chg-02（`harness migrate --archive`）的**前置**：chg-02 的迁移命令必须基于"判据修复后 primary 优先"的前提工作。
- 本 change 与 chg-03/chg-04（`ff --auto` 链路）无文件冲突，可并行；但整体执行顺序建议 chg-01 → chg-02 → chg-03 → chg-04 → chg-05。
