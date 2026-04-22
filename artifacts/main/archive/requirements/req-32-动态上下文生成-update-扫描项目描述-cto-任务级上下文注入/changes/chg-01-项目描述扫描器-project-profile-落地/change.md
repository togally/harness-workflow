# Change: chg-01（项目描述扫描器 + project-profile 落地）

## 1. Goal

- 新建 `ProjectScanner` helper 模块，静态扫描项目根描述文件并产出 `.workflow/context/project-profile.md`（含结构化字段 + LLM 占位 section + 生成时间戳 + sha256 hash）。

## 2. Scope

### 包含

- 新增 `src/harness_workflow/project_scanner.py` 模块，封装 `ProjectScanner` 类与 `build_project_profile(root: Path) -> ProjectProfile` 入口。
- 识别并静态解析以下项目描述文件（存在即解析，缺失即跳过）：`pyproject.toml` / `package.json` / `pom.xml` / `go.mod` / `Cargo.toml` / `README.md` / `README.rst` / `CLAUDE.md` / `AGENTS.md`。
- 提取结构化字段：包名 / 主要语言 / 主要依赖（限 TopN=20）/ 入口命令（脚本 / bin / main 等）/ 技术栈标签（由文件组合推断，如 `python+poetry`、`node+ts`、`java+maven`、`go-module`、`rust-cargo`）。
- 生成 profile 渲染函数：输出 Markdown，包含三块：`## 结构化字段`（YAML/表格）、`## 项目用途（LLM 填充）`（占位）、`## 项目规范（LLM 填充）`（占位）；首部 frontmatter 含 `generated_at`（ISO 时间戳）与 `content_hash`（正文 sha256，复用 `workflow_helpers._managed_hash` 语义的 hasher）。
- 提供 `load_project_profile(path: Path) -> ProjectProfile | None`，支持从已存在文件读回结构化字段，用于 hash 对比。
- 单元测试覆盖每种描述文件的解析 + profile 渲染快照 + 空项目兜底。

### 不包含

- 不接入 `harness update`（由 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）的 chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）负责）。
- 不调用任何 LLM（B3：仅留 `LLM 填充` 占位 section，由主 agent 后续填充）。
- 不构建 `task_context_index` / 不做 briefing 注入（由 chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）负责）。
- 不修改现有 `.workflow/context/index.md` 内容。

## 3. Acceptance Criteria

- 覆盖 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）的 **AC-01**：执行 `build_project_profile(repo_root)` 后返回的 profile 渲染产物包含 ① 语言/包名/主要依赖结构化字段 ② LLM 用途/规范占位 section ③ 生成时间戳 + content_hash。
- 单元测试：
  - 每种描述文件（pyproject / package.json / pom.xml / go.mod / Cargo.toml / README / CLAUDE / AGENTS）至少 1 条解析用例（fixture）。
  - profile 渲染快照：固定输入 → 固定输出（时间戳与 hash 可 mock）。
  - 空项目兜底：根目录无任何描述文件时仍产出结构化字段为空但 section 完整的 profile。

## 4. Dependencies

- 无前置 chg。
- 复用 `src/harness_workflow/workflow_helpers.py::_managed_hash`（或其等效 sha256 helper）以保证 hash 口径一致。
- 复用既有 YAML 加载 helper（如 `workflow_helpers._load_yaml_mapping`）用于 frontmatter 解析。

## 5. Impact Surface

- 新增文件：
  - `src/harness_workflow/project_scanner.py`
  - `tests/test_project_scanner.py`
  - 首次执行后生成 `.workflow/context/project-profile.md`（本 chg 仅提供能力，不强制生成）。
- 修改文件：无。
- 新增 helper：`ProjectScanner` / `build_project_profile` / `load_project_profile` / `render_project_profile`。

## 6. Risks

- 解析异常（畸形 toml/json）→ 捕获异常后字段置空并在 profile 注释 `parse_error`，保证主流程不崩。
- TopN 依赖截断过少 → TopN=20 作为初始常量，后续按需调整，文档化。
