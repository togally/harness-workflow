# Requirement

## 1. Title

版本重做

## 2. Background

harness workflow 系统自 v0.2.0-refactor 存在以下问题：
- 上下文加载链路断裂，新会话无法从 runtime.yaml 正确恢复状态
- 状态管理混乱，runtime.yaml 缺少 stage 字段，角色路由无法正常工作
- 新旧文件结构并存，`.claude/skills/harness/` 旧版文件与新版命令系统冲突
- 需求文档目录（`flow/requirements/`）缺失，经验沉淀体系不完整

需要整体重构，迁移到基于需求管理的新架构。

## 3. Goal

1. 建立基于需求管理的新系统架构（取代版本管理）
2. 清理旧版 harness skill 文件，部署新版命令系统
3. 统一状态管理路径（`workflow/state/`）
4. 建立完整的角色-阶段-约束-经验四层体系

## 4. Scope

**包含：**
- `.claude/skills/harness/` 目录下所有旧版文件的清理
- `workflow/` 目录下所有文件的结构整理和补全
- `workflow/state/runtime.yaml` 字段规范化（含 stage 字段）
- `workflow/flow/requirements/` 目录及需求文档创建
- `workflow/state/experience/` 经验沉淀体系建立

**不包含：**
- 项目业务逻辑代码变更
- 非 workflow 系统的其他目录

## 5. Acceptance Criteria

1. 旧版 harness skill 文件物理清理完成，工作目录无残留（`.claude/skills/harness/` 中无旧版文件）
2. 经验沉淀体系可用：`workflow/state/experience/` 各分类目录有内容可写，加载路径唯一无冲突
3. 正向研发流程可运行：`workflow/context/index.md` 有完整加载规则，`runtime.yaml` 含 stage 字段，req-01 需求文档存在
4. 中断恢复可用：新会话可从 `runtime.yaml` 恢复当前 stage，req-01 状态文件和需求文档完整

## 6. Split Rules

- 每个验收标准对应一个独立可交付变更
- 变更完成后填写 `completion.md` 并记录验证结果
