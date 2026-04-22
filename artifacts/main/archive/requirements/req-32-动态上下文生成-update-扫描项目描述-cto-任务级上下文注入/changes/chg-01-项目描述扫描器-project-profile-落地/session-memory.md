# Session Memory — req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入） / chg-01（项目描述扫描器 + project-profile 落地）

## 1. Current Goal

- 新建 `ProjectScanner` helper 模块，静态扫描项目根描述文件并产出 `.workflow/context/project-profile.md`（含结构化字段 + LLM 占位 section + generated_at + content_hash）。

## 2. Current Status

- Step 1 ✅ pyproject.toml + package.json 解析（commit 793adee）
- Step 2 ✅ pom.xml / go.mod / Cargo.toml / README / CLAUDE / AGENTS 解析（commit 580961d）
- Step 3 ✅ render_project_profile + 时间戳 + content_hash（commit e0eec95）
- Step 4 ✅ load_project_profile + write_project_profile + 空仓兜底（commit f84971c）
- 对人文档 `实施说明.md` ✅
- 基线 253 passed → 267 passed / 50 skipped（+14 新用例）

## 3. Validated Approaches

- tomllib（标准库，Python 3.11+）解析 pyproject / Cargo.toml
- xml.etree.ElementTree 解析 pom.xml 时需处理 Maven 命名空间（`{http://maven.apache.org/POM/4.0.0}`）
- go.mod 解析：正则 `^module\s+(\S+)` + `require\s*\(([^)]*)\)` 块
- content_hash 计算基于"正文去 frontmatter"，保证 frontmatter 的 generated_at 变动不影响 hash

## 4. Failed Paths

- 无。

## 5. Candidate Lessons

```markdown
### 2026-04-21 Python 3.14 可直接使用 tomllib 解析 Cargo.toml 与 pyproject
- Symptom: 需要统一 toml 解析，无 toml 第三方依赖
- Cause: Python 3.11+ 已内置 tomllib（只读）
- Fix: 直接 `import tomllib; tomllib.loads(text)` 无需新增依赖
```

## 6. Next Steps

- 交 testing 独立复核；chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护） / chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘） 另派 subagent 处理。

## 7. Open Questions

- 无阻塞。chg-02 接入 update 时需评估与 `_managed_file_contents` 的交互路径（profile 非 scaffold 文件，应走独立分支而非 adopt）。
