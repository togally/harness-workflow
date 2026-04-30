---
id: chg-03
title: "索引懒加载：项目级子目录 index.md 模板 + role-loading-protocol Step 7.6 改按需加载 + _load_project_level_index helper"
requirement: req-52
operation_type: change
---

# Change Definition

## Why（动机）

req-52 P2（用户原话："constraints / experience 应该有自己的索引，按需加载、不要一次性 glob 全树读"）。

现状（req-51 已落地的加载链）：
- `_merge_project_level_files(global_dir, project_dir)` 内部 `rglob("*")` 一次性扫描整个项目级子树，文件数 ≥ 10 时 token 消耗显著上涨；
- agent 按 `role-loading-protocol.md` Step 7.6 SOP 加载时，等于把所有项目级 constraints / experience 文件一次性塞进上下文，无差别加载；
- tools 子目录因为有 `keywords.yaml` 天然懒加载（按 keyword 命中再读 catalog），不在本 chg 范围。

本 chg 目标：constraints / experience 各子目录加 `index.md` 清单文件（schema = OQ-B = A：YAML frontmatter + Markdown 表，含 `path` / `title` / `scope` / `when_load` 字段）；agent 加载链先读 `index.md` 拿清单，再按 `when_load` 触发条件按需加载；新增 `_load_project_level_index(root, scope)` helper 解析 index.md。

## Scope（范围）

### In Scope

1. **`index.md` 模板（schema 定义）**：在仓库根 `artifacts/project/{constraints,experience/{roles,tool,risk,regression,stage}}/index.md` 各加 1 份占位模板（共 6 个 index.md 文件）；schema = YAML frontmatter + Markdown 表，参考 `.workflow/state/experience/index.md` 现有形态扩 `when_load` 字段；
2. **`_load_project_level_index(root, scope)` helper**：新增至 `src/harness_workflow/workflow_helpers.py`，签名 `(root: Path, scope: str) -> list[dict]`；
   - 入参：`scope` ∈ `{constraints, experience-roles, experience-tool, experience-risk, experience-regression, experience-stage}`；
   - 行为：解析 `artifacts/project/{scope}/index.md` 的 YAML 表格，返回过滤后的清单；主路径不存在 fallback 到 `artifacts/{branch}/project/{scope}/index.md`（双轨 chg-01）；两者均不存在返回空 list；
   - 不读取条目内容（仅返回路径清单），由 agent 按 `when_load` 决定是否后续读取；
3. **`role-loading-protocol.md` Step 7.6 改造**：新增 "Step 7.6.1 索引懒加载" 子段，描述：
   - agent 加载链先调 `_load_project_level_index(root, scope)` 拿清单；
   - 按 `when_load` 触发条件（`always` / `on-stage:{stage}` / `on-keyword:{keyword}`）按需加载条目；
   - 全量 rglob fallback 仅在 index.md 缺失时启用（向后兼容）；
4. **scaffold_v2 mirror 同步**：`role-loading-protocol.md` mirror 同 commit；6 份 `index.md` 模板**不**纳入 mirror（属 artifacts/，与 chg-01 同口径）；
5. **`tests/test_req52_lazy_index_loading.py` 单测（≥ 3 用例）**：覆盖 index.md 解析 / when_load 过滤 / fallback 行为 / 全量 rglob fallback。

### Out of Scope

- `tools/` 子目录索引懒加载 → 已天然懒加载（keywords.yaml），不在范围；
- agent 实际按 `when_load` 读取条目内容的行为 → 由 agent SOP 自觉走，不在 src 层强制；本 chg 仅交付 helper + 索引模板 + 加载协议描述；
- 现有 `.workflow/state/experience/index.md` schema 改造 → 不在范围（不动全局索引，仅在项目级子目录加新索引）；
- 端到端 CLI 触发验证 → 归 chg-04（接入主流程-stderr日志-端到端CLI验证）。

## 接口面（对外约束）

- **`workflow_helpers.py:_load_project_level_index`**：新增 helper，签名稳定；返回 `list[dict]` 每项含 `{path, title, scope, when_load}`；
- **`role-loading-protocol.md` Step 7.6**：新增 7.6.1 子段不破坏现有 7.6 既定语义；
- **`artifacts/project/{constraints,experience/*}/index.md`** 6 份：占位模板，下游可按需扩展。

## 影响面

- **直接影响**：`workflow_helpers.py` 新增 `_load_project_level_index` helper（~30 行）；`role-loading-protocol.md` 新增 7.6.1 子段；6 份 index.md 模板；新增 1 份 test 文件；
- **间接影响**：
  - 现有 5 份 req-51 tests 不受影响（测试目标是合并行为而非懒加载）；
  - 下游用户感知：本 chg 落地后下游可在 `artifacts/project/{scope}/index.md` 维护清单，agent 按需加载，token 消耗下降；
- **现有 `_merge_project_level_files` helper**：本 chg 不动（保留作为 7.6.1 fallback 路径）；chg-04 才接入主流程。

## 验收边界（chg 级 PASS 条件）

- AC-05（索引懒加载）：6 份 `index.md` 模板存在；`_load_project_level_index` 单测全 PASS；`role-loading-protocol.md` 含 Step 7.6.1 段；scaffold_v2 mirror 同 commit；
- `tests/test_req52_lazy_index_loading.py` 全 PASS（≥ 3 用例）；
- `harness validate --contract all` exit 0；
- 现有 5 份 req-51 tests 无回归。
