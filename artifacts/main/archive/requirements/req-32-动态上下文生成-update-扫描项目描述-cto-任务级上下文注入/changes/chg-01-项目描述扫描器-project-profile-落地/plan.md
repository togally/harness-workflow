# Plan: chg-01（项目描述扫描器 + project-profile 落地）

## 前置准备

- 读 `src/harness_workflow/workflow_helpers.py` 中 `_managed_hash`（行 ~2239）、`_load_yaml_mapping`、frontmatter 解析相关 helper，确认可复用的 hash 口径与 yaml 工具。
- 跑基线：`cd /Users/jiazhiwei/IdeaProjects/harness-workflow && pytest -q` 全绿作为 TDD 起点。
- 参考现有静态解析模式：无需新增第三方依赖（仅使用标准库 `tomllib` / `json` / `re`）。

## 步骤（严格 TDD 红绿）

### Step 1: 骨架 + 解析 pyproject.toml + package.json

- 红：新增 `tests/test_project_scanner.py::test_scan_python_poetry_project` / `::test_scan_node_project`，断言返回 `ProjectProfile(package_name, language, deps_top, entrypoints, stack_tags)` 字段；此时 `project_scanner` 模块不存在，测试失败。
- 绿：新增 `src/harness_workflow/project_scanner.py`，实现 `ProjectScanner` 类与 `build_project_profile(root)` 入口；使用 `tomllib` 解析 pyproject，`json` 解析 package.json；stack_tags 由文件存在性组合推断（`python+poetry`/`node+ts`）。
- 产物：新增 scanner 模块（~180 行）+ 测试文件首 2 用例。

### Step 2: 补齐其余描述文件（pom.xml / go.mod / Cargo.toml / README / CLAUDE / AGENTS）

- 红：追加 6 条测试 fixture（每种描述文件一条），断言解析字段与 stack_tags。
- 绿：scanner 新增对应解析分支；pom.xml 用 `xml.etree.ElementTree`（标准库）；go.mod / Cargo.toml 正则提取；README / CLAUDE / AGENTS 仅提取首个 H1 作为 `project_headline`。
- 产物：scanner 模块新增 ~120 行 + 6 条测试。

### Step 3: profile 渲染 + 时间戳 + content_hash

- 红：新增 `test_render_project_profile_snapshot`（mock 时间戳为固定值），断言渲染结果包含 `## 结构化字段` / `## 项目用途（LLM 填充）` / `## 项目规范（LLM 填充）` 三段 + frontmatter 含 `generated_at` / `content_hash`；另加 `test_hash_stable_across_renders`。
- 绿：新增 `render_project_profile(profile)` 函数：输出 frontmatter + 三段 Markdown；content_hash = `_managed_hash(正文去 frontmatter)`；时间戳通过依赖注入 `now: Callable[[], datetime]` 支持测试 mock。
- 产物：新增 render 函数（~60 行）+ 2 条测试。

### Step 4: load_project_profile 反向解析 + 空项目兜底

- 红：新增 `test_load_round_trip`（render → load → 字段相等）、`test_empty_repo_profile`（空目录返回字段为空但 section 完整的 profile）。
- 绿：新增 `load_project_profile(path) -> ProjectProfile | None`，解析 frontmatter + 结构化字段；空项目分支保证 section 完整。
- 产物：新增 load 函数（~40 行）+ 2 条测试。

## 验证

- 单元测试：`pytest tests/test_project_scanner.py -v`（≥ 12 条用例全绿）。
- 集成：在本仓根手动调用 `python -c "from harness_workflow.project_scanner import build_project_profile; from pathlib import Path; p = build_project_profile(Path('.')); print(p)"`，核对 `package_name=harness-workflow` / `language=python` / `stack_tags` 含 `python+poetry` 或 `python+pyproject`。
- 回归：`pytest -q` 零回归（≥ 既有用例数，不少 1 条）。
- 契约自检：`harness validate --contract all` 绿。

## 产物清单

- 新增：
  - `src/harness_workflow/project_scanner.py`（~300-400 行）
  - `tests/test_project_scanner.py`（~250 行，≥ 12 条用例）
- 修改：无。
- 测试：上述测试文件。
