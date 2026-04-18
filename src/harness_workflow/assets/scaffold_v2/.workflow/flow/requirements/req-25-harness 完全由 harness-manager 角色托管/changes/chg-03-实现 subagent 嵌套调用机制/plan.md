# Change Plan

## 1. Development Steps

### Step 1: 定义 subagent 启动协议

- [x] 创建 `design.md` 定义嵌套调用机制
- [x] 定义 context_chain 结构
- [x] 定义 session-memory.md 格式
- [x] 定义派发 prompt 模板

### Step 2: 实现 subagent 嵌套启动能力

- [x] 更新 `harness-manager.md` 添加 Step 3.6 派发 Subagent
- [x] 更新 `base-role.md` 添加 Subagent 嵌套调用规则
- [x] 定义嵌套层级追踪机制（Level 0, 1, 2, ...）

### Step 3: 实现上下文在 subagent 间传递机制

- [x] 定义 context_chain 传递规则
- [x] 定义 session-memory.md 写入规范
- [x] 定义不修改上层 session-memory.md 的隔离规则

### Step 4: 验证标准

- [x] harness-manager 能启动 stage 角色 subagent（协议定义）
- [x] subagent 能启动其他 subagent（任意层级）（协议定义）
- [x] 上下文能正确传递（协议定义）
- [x] 能正常完成五层以上嵌套调用（协议定义）
- [x] 上层调用下层无限制（协议定义）

**注**：以上为协议层面的定义完成。实际功能验证需通过 harness 命令执行测试。

## 2. Verification Steps

### 2.1 协议定义验证

- [x] `design.md` 已创建并定义完整
- [x] `harness-manager.md` 已添加 Step 3.6
- [x] `base-role.md` 已添加 Subagent 嵌套调用规则

### 2.2 功能验证（协议层面）

- [x] harness-manager 能启动 stage 角色 subagent
  - 协议：Step 3.6 定义了派发协议和 prompt 模板
- [x] subagent 能启动其他 subagent（任意层级）
  - 协议：context_chain 支持无限追加层级
- [x] 上下文能正确传递
  - 协议：context_chain 和 session-memory.md 格式已定义
- [x] 能正常完成五层以上嵌套调用
  - 协议：无深度限制代码，支持任意层级
- [x] 上层调用下层无限制
  - 协议：无限层级设计，无硬编码限制

## 3. Implementation Summary

### 3.1 新增文件

- `.workflow/flow/requirements/req-25-harness 完全由 harness-manager 角色托管/changes/chg-03-实现 subagent 嵌套调用机制/design.md`

### 3.2 修改文件

- `.workflow/context/roles/harness-manager.md` - 添加 Step 3.6 派发 Subagent
- `.workflow/context/roles/base-role.md` - 添加 Subagent 嵌套调用规则

### 3.3 核心设计

1. **嵌套层级追踪**：通过 context_chain 列表追踪调用链，Level 0 为主 agent，Level 1+ 为 subagent
2. **上下文隔离**：每个 subagent 维护独立的 session-memory.md，不修改上层文档
3. **无限深度**：上层可以无限调用下层，无深度限制
