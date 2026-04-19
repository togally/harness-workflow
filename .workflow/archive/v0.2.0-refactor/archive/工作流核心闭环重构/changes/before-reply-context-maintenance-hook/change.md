# Change

## 1. Title

before-reply 新增主动 context-maintenance 触发 hook

## 2. Goal

在 before-reply 阶段添加主动的上下文维护触发机制，防止 session 上下文累积过高，确保长期对话的性能和可靠性。

## 3. Requirement

- `None`（源于回归问题 context-maintenance）

## 4. Scope

**包含内容**：
- 在 `workflow/context/hooks/before-reply/` 目录下新增主动触发 hook
- 实现三种触发条件：轮次触发、文件数触发、阶段切换强制
- 添加 session 状态追踪机制（轮次计数、已读文件数）
- 更新 `workflow/context/hooks/README.md` 文档说明

**排除内容**：
- 修改 context-maintenance 的具体实现逻辑（保持现有清理机制不变）
- 修改其他阶段的 hook 触发机制
- 修改 workflow-runtime.yaml 的结构

## 5. Trigger Conditions

1. **轮次触发**：每 8-10 轮对话后自动触发检查
2. **文件数触发**：当前 session 已读文件数 > 15 时触发
3. **阶段切换强制**：执行 `harness next` 之前强制触发检查

## 6. Next

- 添加 `design.md`：详细设计触发机制和实现方案
- 添加 `plan.md`：制定分步实施计划
- 添加 `acceptance.md`：定义验收标准和测试用例
- Regression input requests live in `regression/required-inputs.md`
