# Change

## 1. Title

重构 stage-tools.md 约束表达，提升工具扩展性

## 2. Goal

将 `stage-tools.md` 从"枚举式白名单"重构为"能力类型 + 禁止规则 + 推荐列表"的表达式，降低新增工具的维护成本，确保 toolsManager 推荐的新工具能自然融入各 stage。

## 3. Requirement

- `req-24`

## 4. Scope

**包含：**
- 定义工具能力类型分类（读写型、执行型、搜索型、协调型、上下文管理型）
- 重构 `stage-tools.md` 各 stage 段落：明确禁止的能力类型 + 推荐工具列表
- 补充新增工具的默认规则：已注册 catalog 且未落入禁止类型的工具默认可用
- 保留并优化上下文管理规则

**不包含：**
- 修改 `selection-guide.md`
- 修改 `maintenance.md`
- 修改 stage 角色的核心 SOP

## 5. Verification

- `stage-tools.md` 各 stage 均使用"禁止 + 推荐"的表达方式，不再使用硬性的枚举白名单
- 新增一个假设工具时，不需要修改 `stage-tools.md` 即可判断其是否可用
- 各 stage 的禁止规则与 req-24 之前的约束语义等价（无放宽核心安全边界）
