# Requirement: bugfix 快速修复与验证

## 背景

当前 Harness Workflow 的标准六阶段流（requirement_review → planning → executing → testing → acceptance → done）适用于功能需求开发，但对已知缺陷修复来说过重：

1. bugfix 的触发点本身就是问题描述，不需要完整的需求评审
2. bugfix 的范围通常很聚焦（一个函数、一个配置、一条边界 case），不需要拆分成多个 change + plan
3. bugfix 的核心诉求是快：快速定位根因 → 快速修复 → 快速验证 → 快速回归

如果强制走标准流程，用户倾向于把 bugfix 塞到某个现有需求的 `changes/` 下，导致 traceability 混乱；或者干脆绕过 Harness，直接动手改。

## 目标

设计并实现一条比标准流程更短的 **Bugfix 快速流程**，保留 regression 诊断、testing 验证、acceptance 判定等质量关卡，但跳过 requirement_review 和 planning，让已知缺陷的修复能在 4 个阶段内完成。

## 范围

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

## 关键设计决策

### 1. 流程模式由 technical-director 识别

- 标准需求：`req-*` 前缀 → 模式 A（六阶段流）
- bugfix 需求：`bugfix-*` 前缀 → 模式 B（四阶段流）

### 2. stage 角色完全复用

- `regression` → `regression.md`
- `executing` → `executing.md`
- `testing` → `testing.md`
- `acceptance` → `acceptance.md`

不新增专门的"bugfix 执行角色"，bugfix 是编排层的流程模式，不是 stage 执行层的角色。

### 3. 产物结构

```
.workflow/flow/bugfixes/
└── bugfix-{数字}-{title}/
    ├── bugfix.md          ← 三合一：问题 + 根因 + 方案 + 验证标准
    ├── session-memory.md
    ├── test-evidence.md
    └── regression/
        ├── diagnosis.md
        └── required-inputs.md
```

### 4. 与 req-22 的衔接

req-22 已预埋 technical-director 的双模式分支。req-23 的实现重点在于：
1. CLI 命令扩展
2. bugfix.md 模板
3. 目录创建逻辑
4. 端到端验证
