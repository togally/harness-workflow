# Change

## 1. Title

实现 subagent 嵌套调用机制

## 2. Goal

定义 subagent 启动协议，实现上层可以无限调用下层的 subagent 嵌套启动能力，并建立上下文在 subagent 间传递的机制。

## 3. Requirement

- `req-25`

## 4. Scope

### Included

- 定义 subagent 启动协议（如何传递上下文、如何指定角色）
- 实现 subagent 嵌套启动能力（上层可以无限调用下层）
- 实现上下文在 subagent 间传递机制
- 更新 harness-manager.md 添加派发 subagent 协议
- 更新 base-role.md 添加嵌套调用规则

### Excluded

- 具体 subagent 派发的代码实现（由 Agent 工具调用）
- stage 流转逻辑（已在其他变更中实现）

## 5. Next

- [x] Add `design.md`
- [x] Add `plan.md`
- [x] Update `harness-manager.md` with Step 3.6
- [x] Update `base-role.md` with nested dispatch rules
- Regression input requests live in `regression/required-inputs.md`
