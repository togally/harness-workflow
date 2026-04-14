# Regression Diagnosis

## 触发信息
- **触发时间**: 2026-04-13
- **触发阶段**: testing
- **触发来源**: 用户口头提出设计变更

## 问题描述

将 `.workflow/` 目录重命名为 `.workflow/`（dotfile 约定，隐藏目录），并同步更新所有脚本引用。

## 问题性质判断

| 判断项 | 结论 |
|--------|------|
| 是否 Bug | 否 |
| 是否功能缺失 | 否 |
| 是否设计变更 | **是** |
| 是否 Breaking Change | **是**（已有仓库使用 .workflow/，需迁移） |
| 根因 | 设计偏好：workflow 目录应遵循 dotfile 约定，对用户目录更干净 |

## 影响范围（已扫描）

| 层次 | 影响项 | 数量 |
|------|--------|------|
| Python 源码 | `core.py` Path("workflow") 常量 | ~22 处 |
| Python 源码 | `backup.py` 路径引用 | 若干 |
| 测试文件 | `test_harness_cli.py` 路径断言 | 若干 |
| Scaffold | `scaffold_v2/.workflow/` 目录结构 | 需重命名 |
| 模板文件 | `assets/templates/` 含 .workflow/ 引用 | 17 个文件 |
| Markdown 文档 | WORKFLOW.md / AGENTS.md / CLAUDE.md | 3 个文件，多处引用 |
| Slash commands | 三端所有命令文件（Hard Gate 路径） | ~56 个文件 |
| SKILL.md | 三端 harness skill | 3 个文件 |
| 当前仓库物理目录 | `.workflow/` → `.workflow/` | 整个目录树 |

## 额外影响

- **Breaking Change**：已通过 `harness install` 部署的目标仓库使用 `.workflow/`，升级需提供迁移指引或兼容处理
- **git ignore**：`.workflow/` 是否需要从 .gitignore 中排除（dotfile 默认不显示但不一定被 git 忽略）

## 诊断结论

**确认**：真实的设计变更，非误判。

**路由**：`requirement_review`

**理由**：
- 属于设计层面的目录命名规范变更
- 影响范围覆盖 Python 源码 + 模板 + Markdown + 物理目录，需完整的需求定义和变更拆分
- 需明确 Breaking Change 的兼容/迁移策略再进入实现

## 需在 requirement_review 确认的问题

1. 是否需要向后兼容（`harness update` 自动迁移 .workflow/ → .workflow/）？
2. `.workflow/` 是否应加入 `.gitignore` 排除规则（或相反，确保被提交）？
3. `WORKFLOW.md` 中的路径引用更新后，对 Hard Gate 读取文件的路径是否同步更新？
