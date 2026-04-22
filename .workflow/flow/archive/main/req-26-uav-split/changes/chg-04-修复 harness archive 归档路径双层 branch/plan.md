# Change Plan

## 1. Development Steps

### Step 1：全局定位 archive 路径拼接点

- Grep `archive/` 路径字面量与拼接函数，例如：
  - `src/harness_workflow/cli/archive.py`
  - `src/harness_workflow/state/paths.py` 或等价模块中的 `archive_root(branch)` / `archive_requirement_path(branch, req_id)` 工具函数；
- 确认 bug 根因：是在 `archive_root` 已经包含 `{branch}`，调用方又重复传 `{branch}`，还是两处分别拼了一次。

### Step 2：统一路径拼接 API

- 选定单一 API（建议 `archive_requirement_path(branch, req_id, slug) -> Path`），内部只拼一次 branch；
- 替换所有重复拼接调用点，参数签名保持清晰：调用方传 `branch` + `req_id` + `slug`，不再自己拼 `archive/{branch}/...`。
- 涉及文件（预期）：
  - `src/harness_workflow/cli/archive.py`
  - `src/harness_workflow/state/paths.py`
  - 如 migrate 命令共用了路径函数，同步验证。

### Step 3：兼容历史错位路径（只读）

- 归档搜索（如 `find existing archive for req-id`）仍需能找到老的双层 branch 路径；
- 在查找逻辑中，先按新规则拼一次，找不到再回落到老规则（仅用于读取，不再写入）。

### Step 4：单元测试

- `tests/test_archive_paths.py`（新增或扩写）：
  - `test_archive_path_single_branch_segment`：构造 `branch=main`、`req_id=req-99`、`slug=demo`，断言结果为 `archive/main/req-99-demo/`；
  - `test_archive_handles_legacy_double_branch_readonly`：预置老路径 `archive/main/main/req-88-foo/`，断言查找函数能找到它但不再写入这种路径；
  - `test_archive_new_write_never_double_branch`：执行一次真实 archive，断言磁盘无 `main/main`。

### Step 5：文档与经验沉淀

- 在 `.workflow/context/experience/roles/done.md` 或 `tool/harness-cli.md` 下补"archive 路径单层 branch"约定，附反例。

## 2. Verification Steps

### 2.1 单元测试

- 运行 pytest，新增 3 条用例全部通过，老用例零回归。

### 2.2 手工 smoke（沙盒仓库）

1. 跑一轮完整 requirement → done → `harness archive`；
2. `find .workflow/flow/archive -maxdepth 3 -type d` → 无 `main/main` 路径；
3. 进入归档目录，确认 change / session-memory / done-report 等文件完整。

### 2.3 AC 映射

- AC-05：Step 2 + 2.2 步骤 2。

## 3. 依赖与执行顺序

- 独立 change，与其他 P0 修复 change 可并行；
- 与 chg-03 有潜在耦合：chg-03 让 archive 不再依赖人工改 yaml，若同时验证 smoke 建议 chg-03 / chg-04 一起合入再验。
