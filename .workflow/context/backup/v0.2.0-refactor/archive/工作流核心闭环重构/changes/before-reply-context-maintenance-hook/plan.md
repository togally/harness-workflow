# Change Plan

## 1. Development Steps

### 步骤 1：创建主动检查 hook

**文件**：`workflow/context/hooks/before-reply/10-context-maintenance-check.md`

**内容**：
- 读取当前 session-memory.md 中的状态追踪信息
- 检查是否满足任一触发条件（轮次、文件数、阶段切换）
- 如果满足条件，提供维护建议
- 更新 session-memory.md 中的状态追踪信息

**验收标准**：
- Hook 文件存在且格式正确
- Hook 逻辑正确实现三种触发条件

### 步骤 2：更新 session-memory.md 模板

**文件**：`workflow/templates/session-memory.md`

**内容**：
- 新增 `Session State Tracking` 区域
- 添加 `conversation_turns` 计数器
- 添加 `files_read` 计数器
- 添加阈值配置信息

**验收标准**：
- 模板包含完整的状态追踪结构
- 新创建的 session-memory.md 包含状态追踪区域

### 步骤 3：更新 hook README 文档

**文件**：`workflow/context/hooks/README.md`

**内容**：
- 在 `before-reply/` 部分添加新 hook 的说明
- 更新 hook 加载顺序
- 说明主动触发机制的工作原理

**验收标准**：
- 文档准确描述新 hook 的作用和位置
- hook 加载顺序正确

### 步骤 4：更新当前变更的 session-memory.md

**文件**：`workflow/versions/active/v0.2.0-refactor/changes/before-reply-context-maintenance-hook/session-memory.md`

**内容**：
- 初始化 `Session State Tracking` 区域
- 设置初始计数器为 0

**验收标准**：
- session-memory.md 包含状态追踪区域
- 初始值设置正确

### 步骤 5：更新 workflow-runtime.yaml（可选）

**文件**：`workflow/context/rules/workflow-runtime.yaml`

**内容**：
- 添加 `context_maintenance` 配置节
- 配置默认阈值：
  - `turn_threshold: 10`
  - `file_threshold: 15`

**验收标准**：
- 配置节存在且格式正确
- 默认阈值合理

### 步骤 6：验证文件完整性

**操作**：
- 检查所有创建/修改的文件是否存在
- 验证文件格式（特别是 YAML 和 Markdown）
- 确认没有破坏现有结构

**验收标准**：
- 所有文件存在且格式正确
- 现有功能未受影响

## 2. Verification Steps

### 验证 1：Hook 文件正确性

```bash
# 检查 hook 文件存在
ls -la workflow/context/hooks/before-reply/10-context-maintenance-check.md

# 验证文件格式
head -20 workflow/context/hooks/before-reply/10-context-maintenance-check.md
```

**预期结果**：
- 文件存在
- 文件以 Markdown 格式开头，包含清晰的标题和说明

### 验证 2：模板更新正确性

```bash
# 检查模板文件包含状态追踪
grep -A 10 "Session State Tracking" workflow/templates/session-memory.md
```

**预期结果**：
- 模板包含 `Session State Tracking` 区域
- 包含 `conversation_turns` 和 `files_read` 计数器

### 验证 3：文档更新正确性

```bash
# 检查 README 包含新 hook 说明
grep -A 5 "context-maintenance-check" workflow/context/hooks/README.md
```

**预期结果**：
- README 中提到新 hook
- hook 位置在加载顺序中正确

### 验证 4：YAML 格式验证

```bash
# 验证 workflow-runtime.yaml 格式
python3 -c "import yaml; yaml.safe_load(open('workflow/context/rules/workflow-runtime.yaml'))"
```

**预期结果**：
- 无语法错误
- YAML 可以正确解析

### 验证 5：功能测试

**测试场景 1**：轮次触发
1. 在当前变更的 session-memory.md 中设置 `conversation_turns: 10`
2. 模拟 before-reply 检查
3. 验证是否触发维护建议

**测试场景 2**：文件数触发
1. 在当前变更的 session-memory.md 中设置 `files_read: 16`
2. 模拟 before-reply 检查
3. 验证是否触发维护建议

**测试场景 3**：阶段切换触发
1. 模拟执行 `harness next` 命令
2. 验证是否强制触发检查

**预期结果**：
- 每种场景都能正确触发相应的维护建议
- 建议内容清晰且可操作

## 3. Rollback Plan

如果实施后发现问题，可以按以下步骤回滚：

1. 删除新增的 hook 文件：
   ```bash
   rm workflow/context/hooks/before-reply/10-context-maintenance-check.md
   ```

2. 恢复原始的 session-memory.md 模板（如果有备份）

3. 恢复原始的 workflow/context/hooks/README.md（如果有备份）

4. 从 workflow-runtime.yaml 中移除 `context_maintenance` 配置节

## 4. Dependencies

- 无外部依赖
- 依赖现有的 hook 机制
- 依赖 session-memory.md 的结构
