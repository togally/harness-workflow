---
generated_at: 2026-04-22T00:44:37.438501+00:00
content_hash: 17682b34693a324f36cd470870925cabb2f4dc336167d8cb44679185da03e258
schema: project-profile/v1
---
## 结构化字段

- package_name: harness-workflow
- language: python
- project_headline: harness-workflow
- stack_tags:
  - python+pyproject
- deps_top:
  - questionary>=2.0.0
  - pyyaml>=6.0
- entrypoints:
  - harness=harness_workflow.cli:main

## 项目用途（LLM 填充）

harness-workflow 是一个 Python CLI 工具包，为 AI agent（Claude Code / Codex / Qoder / Kimi）提供"需求 → 变更 → 计划 → 执行 → 测试 → 验收 → 归档"的结构化工作流脚手架。核心价值是把"模糊的用户需求"分阶段固化成可审计的工件树（`artifacts/` 制品仓 + `.workflow/state/` 状态仓），并通过 stage 硬门禁 + 契约自检（契约 1-7）约束 agent 行为，避免主 agent 跳步直接写代码。对外入口为 `harness` CLI；对内由 harness-manager 角色统一路由命令并派发 subagent。典型使用者是需要与 AI 协作开发但希望保留工程严谨性的开发者。

## 项目规范（LLM 填充）

- **TDD 红绿**：新增 / 修改代码前先写失败测试；每对红绿独立 commit；`pytest -q` 必须零回归
- **stage-role 继承链**：所有 stage 角色继承 `base-role.md` + `stage-role.md`；辅助角色（harness-manager / tools-manager）也受 stage-role 约束
- **契约 7 首次引用带 title**：对人文档 / 注释 / commit message 里首次提到 `req-*` / `chg-*` / `sug-*` / `bugfix-*` / `reg-*` 必须形如 `{id}（{title}）`，同上下文后续可简写
- **对人文档 ≤ 1 页**：requirement_review 产 `需求摘要.md`、planning 产 `变更简报.md`、testing 产 `测试简报.md`/`测试结论.md`、done 前产 `completion.md`，字段名与顺序不得变更
- **节点任务派 subagent**：主 agent 不直接操作项目代码 / 文件；写文件、写代码、跑测试由 stage 角色 subagent 执行
- **runtime.yaml 唯一权威**：stage 切换 / current_requirement 记录以 `.workflow/state/runtime.yaml` 为准；不一致时修 runtime 而非另开平行工作流
- **commit 风格**：`<type>(workflow): req-NN（title）/ chg-NN（title）/ Step N {红|绿}: <summary>（... tests 零回归）`；Co-Authored-By 保留
- **禁用**：`--no-verify` / `--no-gpg-sign` / 强制 push main / `git stash pop` 后接 `git checkout HEAD --`（会污染 runtime.yaml）
