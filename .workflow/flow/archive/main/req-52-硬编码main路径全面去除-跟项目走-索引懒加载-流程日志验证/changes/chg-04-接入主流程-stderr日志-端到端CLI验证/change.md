---
id: chg-04
title: "接入主流程 + stderr 日志 + 端到端 CLI 验证：_merge_project_level_files 接入 install_repo / update_repo + 日志输出 + subprocess 真实 CLI 触发 stderr 断言"
requirement: req-52
operation_type: change
---

# Change Definition

## Why（动机）

req-52 P3（用户原话："`_merge_project_level_files` docstring 自承不接入 install_repo / update_repo 主流程；要：接入主流程、加 stderr 日志、用真实 CLI 端到端验证"）。

现状（req-51 已落地的设计缺陷）：

- `_merge_project_level_files` docstring 第 8293 行原话："本 helper 不接入 install_repo / update_repo 主流程；仅供 role-loading-protocol Step 7.6 与 tools-manager Step 2.0 的加载链按文档 SOP 解析使用，以及 tests/test_req51_project_level_loading.py 断言。"
- 实际效果：项目级合并行为完全靠 agent 按文档 SOP 自觉走，没有任何 stderr 可证 / e2e CLI 验证；
- 下游真实仓的"项目级是否生效"完全黑盒；test_req51_project_level_loading.py 是 fixture-only 单测，不能证明真实 CLI 触发后行为正确。

本 chg 是 req-52 收口 chg：把 `_merge_project_level_files` 接入 `install_repo` / `update_repo` 主流程（在入口段调用以预热 + 日志记录），加 stderr 结构化日志（`[harness] project-level loaded: {N} files from {path}`），并新增端到端 pytest（`subprocess.run([sys.executable, "-m", "harness_workflow.cli", ...])` 真实 CLI 触发，断言 stderr 含日志字面值）。

依赖：chg-01（契约层路径迁移）+ chg-02（src 硬编码 main 全面去除）+ chg-03（索引懒加载）已落地。

## Scope（范围）

### In Scope

1. **`_merge_project_level_files` docstring 改造**：
   - 删除"本 helper 不接入 install_repo / update_repo 主流程"字样；
   - 新增 docstring 段说明本 helper 已被 `install_repo` / `update_repo` 入口段调用（chg-04 落地）；

2. **新增 `_log_project_level_load(root, scope, hits, fallback_used)` helper**：
   - 入参：root / scope / hits（int 文件数）/ fallback_used（bool 是否走了 legacy 路径）；
   - 输出：stderr 单行 `[harness] project-level loaded: {N} files from {path}（fallback={legacy_path or "n/a"}）`；
   - 行为：仅写 stderr，不写盘；e2e pytest 断言依赖此格式；

3. **`install_repo` 入口段集成**：
   - 在 line ~3786 区域（feedback.jsonl 迁移后、平台选择前）加 1 段：
     - 对三个 scope 大类（`constraints` / `experience` / `tools`）逐个调 `_merge_project_level_files` 拿合并 dict（仅触发探测，结果暂不消费）；
     - 调 `_log_project_level_load` 输出 stderr 日志；
   - 不修改 mirror 同步 / managed-files 行为（只增加日志，不改变写盘逻辑）；
   - `check=True`（dry-run）模式下也输出日志（让 e2e 用 `--check` 可观测）；

4. **`update_repo` 入口段集成**：
   - `update_repo` 是 `install_repo` 空壳委托（`force_skill=True`），无需独立改动；自动继承 install_repo 的日志；

5. **新增 `tests/test_req52_e2e_log.py`** 端到端 CLI 触发测试：
   - 使用 `subprocess.run([sys.executable, "-m", "harness_workflow.cli", "install", "--check"], cwd=tmpdir, capture_output=True)`；
   - 断言 stderr 含 `project-level loaded` 字面值；
   - 三场景覆盖：(a) 项目级 0 文件（无 artifacts/project/，无 legacy）；(b) 项目级 ≥ 1 文件（artifacts/project/constraints/rule.md）；(c) legacy fallback 命中（仅 artifacts/{branch}/project/ 有文件）；
   - 子进程退出码断言 = 0；

6. **scaffold_v2 mirror 行为同步**：本 chg 仅改 src/，不改契约文档 / scaffold_v2 mirror。

### Out of Scope

- 索引懒加载实际改造 `_merge_project_level_files` 内部行为（rglob → 走 index.md）→ 归 chg-03（本 chg 仅在主流程接入 + 日志，不改 helper 内部算法）；
- 端到端测试覆盖 `harness next` / `harness status` / `harness regression` 等其他 CLI 子命令 → 不在范围（OQ-D 拍板限于 install + update）；
- 日志格式国际化（i18n）→ 不在范围；
- agent SOP 层按 when_load 实际过滤的行为校验 → 由 agent 自觉走，本 chg 不在 src 层强制。

## 接口面（对外约束）

- **`workflow_helpers.py:_merge_project_level_files`**：函数签名不变；docstring 改写；
- **`workflow_helpers.py:_log_project_level_load`**：新增 helper，签名 `(root: Path, scope: str, hits: int, fallback_used: bool) -> None`；仅写 stderr；
- **`workflow_helpers.py:install_repo`**：入口段新增项目级日志调用块（约 8 ~ 12 行新增）；不影响现有 `actions` 列表 / 返回值；
- **`tests/test_req52_e2e_log.py`**：新增文件，subprocess 真实 CLI 触发；
- **stderr 日志格式**：`[harness] project-level loaded: {N} files from {path}（fallback={legacy_path or "n/a"}）`；与现有 `[install_repo]` / `[update_repo]` stderr 风格一致（OQ-C = A）。

## 影响面

- **直接影响**：`workflow_helpers.py` `_merge_project_level_files` docstring 改 + 新增 `_log_project_level_load` helper（~15 行）+ `install_repo` 入口段增 1 块代码（~12 行）+ 新增 1 份 e2e test 文件；
- **间接影响**：
  - 所有现有 `harness install` / `harness update` 调用方（含 CI / 下游用户）的 stderr 输出新增 3 行日志（每个 scope 一行）；可能影响 stdout/stderr 抓取脚本（向后兼容性：新增行不破坏现有日志，只增不减）；
  - 现有 5 份 req-51 tests 不受影响（它们直接调 helper，不走 install_repo 入口）；
  - `tests/test_install_repo_sync_contract.py` 等现有 install_repo 单测：可能需检查是否有 stderr 行数硬断言；如有需同步更新（实施层确认）；
- **e2e test 性能**：subprocess 真实 CLI 触发耗时 ~2 ~ 5 秒/用例，3 用例总耗时 ~10 ~ 15 秒，可接受。

## 验收边界（chg 级 PASS 条件）

- AC-06（接入主流程 + stderr 日志）：
  - `_merge_project_level_files` docstring "不接入 install_repo / update_repo 主流程" 字样消除；
  - `_log_project_level_load` helper 注册且在 `install_repo` 入口段被调用；
  - 真实 `harness install --check` 执行 stderr 含 `[harness] project-level loaded:` 字面值；
- AC-07（端到端真实 CLI 触发 + stderr 断言）：
  - `pytest tests/test_req52_e2e_log.py -v` 全 PASS（≥ 3 用例，subprocess 真实 CLI 触发）；
  - 包含 0 文件 / ≥ 1 文件 / legacy fallback 三场景；
- 现有 5 份 req-51 tests 无回归；
- `harness validate --contract all` exit 0。
