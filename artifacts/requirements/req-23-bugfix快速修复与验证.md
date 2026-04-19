# bugfix快速修复与验证

> req-id: req-23 | 完成时间: 2026-04-17 | 分支: main

## 需求目标

设计并实现一条比标准流程更短的 **Bugfix 快速流程**，保留 regression 诊断、testing 验证、acceptance 判定等质量关卡，但跳过 requirement_review 和 planning，让已知缺陷的修复能在 4 个阶段内完成。

## 交付范围

### 包含

1. 新增 `harness bugfix "<issue>"` CLI 命令
2. 定义 bugfix 专属产物结构（`.workflow/flow/bugfixes/{id}/`）
3. 扩展 `technical-director.md` 的编排逻辑，支持"双模式流程图"
4. 扩展 `stages.md` 的流转规则，新增 bugfix 分支
5. 新建 `bugfix.md` 模板和三合一产物规范
6. 更新 `base-role.md`，增加角色自我介绍规则：每次角色执行实质性任务前，须向用户说明自身身份和当前任务意图
7. 端到端验证：用一条真实或模拟的 bug 走完整流程

### 不包含

1. 修改现有标准需求的六阶段流
2. 修改现有的 stage 角色文件（`executing.md`、`testing.md` 等）的核心职责
3. 引入新的 subagent 角色类型（不破坏 `base-role → stage-role → 具体角色` 三层继承）

## 验收标准

- [ ] `harness bugfix "xxx"` 命令能正确创建 `bugfix-{id}` 目录并进入 regression 阶段
- [ ] `technical-director.md` 能识别 bugfix 模式，强制执行 `regression → executing → testing → acceptance → done` 四阶段流
- [ ] bugfix 模式下不加载 `planning` 角色，不存在 planning stage
- [ ] `bugfix.md` 三合一天然产物包含：问题描述、根因分析、修复范围、修复方案、验证标准
- [ ] `stages.md` 包含完整的 bugfix 流转图和目录规范
- [ ] lint 脚本能正确检查 bugfix 目录结构（可选严格模式）
- [ ] 端到端测试通过：至少用一条模拟 bug 走完整 bugfix 流程
- [ ] 测试经验已沉淀到 `experience/roles/regression.md` 或新建 `experience/roles/bugfix.md`

## 变更列表

- **chg-01** chg-01-规范层更新：为 bugfix 快速流程奠定规范基础，更新 `base-role.md` 的角色自我介绍规则，并在 `stages.md` 中完善 bugfix 分支的流转定义。
- **chg-02** chg-02-bugfix模板与目录规范：定义 bugfix 需求的专属产物结构和 `bugfix.md` 模板，确保 bugfix 流程有统一的三合一天然产物。
- **chg-03** chg-03-实现harness-bugfix命令：在 Harness CLI 中新增 `harness bugfix "<issue>"` 子命令，支持创建 bugfix 需求目录、初始化状态文件，并进入 regression 阶段。
- **chg-04** chg-04-端到端验证与经验沉淀：用一条模拟 bug 走完整 bugfix 流程，验证各阶段流转正常，并将测试经验沉淀到经验文件。
