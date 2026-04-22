# Session Memory

## 1. Current Goal

重构经验目录结构：从平铺改为按分类组织（stage/tool/business/architecture/debug/risk），并将现有经验内容迁移到对应分类。

## 2. Current Status

**已完成**：

1. 创建新目录结构：
   - `workflow/context/experience/stage/`（5个文件）
   - `workflow/context/experience/tool/`（4个文件）
   - `workflow/context/experience/business/`（.gitkeep 占位）
   - `workflow/context/experience/architecture/`（.gitkeep 占位）
   - `workflow/context/experience/debug/`（.gitkeep 占位）
   - `workflow/context/experience/risk/`（known-risks.md）

2. 新建经验文件：
   - `stage/requirement.md` — 需求阶段约束与最佳实践
   - `stage/development.md` — 开发阶段约束与编译验证要求
   - `stage/testing.md` — 测试阶段经验
   - `stage/acceptance.md` — 验收阶段逐条核对要求
   - `stage/regression.md` — 回归阶段流程
   - `tool/harness.md` — harness 命令参考与状态管理
   - `tool/playwright.md` — Playwright 工具经验
   - `tool/mysql-mcp.md` — MySQL MCP 工具经验
   - `tool/nacos-mcp.md` — Nacos MCP 工具经验
   - `risk/known-risks.md` — 4条已知风险（阶段跳过、版本不一致、编译遗漏、经验遗漏）

3. 重写 `workflow/context/experience/index.md` 为路由索引格式（阶段加载表 + 工具加载表 + 风险门禁）

4. 更新模板文件：
   - `src/.../templates/experience-index.md.tmpl`（中文）
   - `src/.../templates/experience-index.md.en.tmpl`（英文）

5. 更新 `src/harness_workflow/core.py`：
   - `_required_dirs()` 新增 6 个子目录
   - 新增 `_experience_stub()` helper 函数
   - `_managed_file_contents()` 注册 10 个新经验文件路径（write_if_missing 模式）

**保留**：旧有 `index.md` 内容已被路由索引格式覆盖（原内容仅为示例映射表，无实质迁移内容丢失）

## 3. Validated Approaches

- `python3 -c "import ast; ast.parse(...)"` 验证 core.py 语法正确（Syntax OK）
- 所有新目录通过 `mkdir -p` 创建成功
- 所有新文件通过 Write 工具创建成功

## 4. Failed Paths

- Edit 工具首次编辑 core.py 失败，原因：文件在 Read 后被 linter 修改（file state stale）。解决：重新 Read 后再 Edit。

## 5. Candidate Lessons

```markdown
### 2026-04-11 经验目录分类路由模式
- 症状：平铺经验文件导致 AI 难以判断何时加载哪些文件
- 原因：缺乏按阶段/工具分类的加载策略
- 修复：引入路由索引（index.md 改为加载表格式），经验文件按 stage/tool/risk/etc. 分类
- 建议置信度：medium（首次实施，待后续迭代验证）
```

## 6. Next Steps

- 在实际项目使用中验证路由索引效果，按需补充 business/ 和 architecture/ 目录内容
- 后续可将 `harness update` 集成到 CI 以自动同步模板变更

## 7. Open Questions

- `business/` 和 `architecture/` 占位目录：具体项目应在需求阶段或开发阶段补充内容，占位文件仅为 `.gitkeep`
- 是否需要为 `debug/` 目录提供初始诊断模板，待下一个 change 评估
