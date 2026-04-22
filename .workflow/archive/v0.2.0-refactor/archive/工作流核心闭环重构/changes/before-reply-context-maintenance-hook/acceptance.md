# Change Acceptance

## 1. Scope

本变更必须交付以下内容：

1. **新增 Hook 文件**：
   - `workflow/context/hooks/before-reply/10-context-maintenance-check.md`
   - 实现三种主动触发条件（轮次、文件数、阶段切换）
   - 提供清晰的维护建议

2. **更新模板文件**：
   - `workflow/templates/session-memory.md`
   - 新增 `Session State Tracking` 区域
   - 包含 `conversation_turns` 和 `files_read` 计数器

3. **更新文档**：
   - `workflow/context/hooks/README.md`
   - 说明新 hook 的作用和位置
   - 更新 hook 加载顺序

4. **可选配置**：
   - `workflow/context/rules/workflow-runtime.yaml`
   - 添加 `context_maintenance` 配置节
   - 设置合理的默认阈值

## 2. Checks

### 检查 1：文件完整性

```bash
# 检查所有必需文件是否存在
ls -la workflow/context/hooks/before-reply/10-context-maintenance-check.md
ls -la workflow/templates/session-memory.md
ls -la workflow/context/hooks/README.md
```

**验收标准**：所有文件存在且可读

### 检查 2：文件格式验证

```bash
# 验证 Markdown 文件格式
head -5 workflow/context/hooks/before-reply/10-context-maintenance-check.md
head -5 workflow/templates/session-memory.md

# 验证 YAML 文件格式（如果更新了）
python3 -c "import yaml; yaml.safe_load(open('workflow/context/rules/workflow-runtime.yaml'))"
```

**验收标准**：
- Markdown 文件格式正确
- YAML 文件无语法错误

### 检查 3：内容正确性

**Hook 文件内容检查**：
```bash
# 检查 hook 包含触发逻辑
grep -i "trigger" workflow/context/hooks/before-reply/10-context-maintenance-check.md
grep -i "conversation_turns" workflow/context/hooks/before-reply/10-context-maintenance-check.md
grep -i "files_read" workflow/context/hooks/before-reply/10-context-maintenance-check.md
```

**模板文件内容检查**：
```bash
# 检查模板包含状态追踪
grep -A 10 "Session State Tracking" workflow/templates/session-memory.md
```

**文档内容检查**：
```bash
# 检查 README 包含新 hook 说明
grep -i "context-maintenance-check" workflow/context/hooks/README.md
```

**验收标准**：
- Hook 文件包含所有三种触发条件的逻辑
- 模板文件包含完整的状态追踪区域
- 文档准确描述新 hook

### 检查 4：功能验证

**验证轮次触发**：
1. 在当前变更的 session-memory.md 中设置：
   ```yaml
   ## Session State Tracking
   ### Conversation Turns
   - Current: 10
   - Last Maintenance: 0
   - Threshold: 10
   ```
2. 阅读 hook 文件，验证逻辑会触发维护建议
3. 检查建议内容是否清晰

**验证文件数触发**：
1. 在当前变更的 session-memory.md 中设置：
   ```yaml
   ### Files Read
   - Current: 16
   - Last Maintenance: 0
   - Threshold: 15
   ```
2. 阅读 hook 文件，验证逻辑会触发维护建议
3. 检查建议内容是否清晰

**验收标准**：
- 两种触发条件都能正确识别
- 提供的维护建议清晰且可操作

### 检查 5：向后兼容性

```bash
# 验证现有 hook 未受影响
ls -la workflow/context/hooks/before-reply/
```

**验收标准**：
- 现有 hook 文件仍然存在
- 现有 hook 的加载顺序合理（新 hook 在最前面）

### 检查 6：编译验证

**注意**：本项目不使用 Maven，因此跳过 `mvn compile` 检查。

替代验证：
```bash
# 验证 YAML 文件语法
python3 -c "import yaml; yaml.safe_load(open('workflow/context/rules/workflow-runtime.yaml'))"

# 验证 Markdown 文件语法
for file in workflow/context/hooks/before-reply/*.md; do
    if [ -f "$file" ]; then
        echo "Checking $file..."
        head -1 "$file"
    fi
done
```

**验收标准**：
- 所有 YAML 文件语法正确
- 所有 Markdown 文件格式正确

## 3. Result

### 验收状态

- [x] 检查 1：文件完整性 - 通过
- [x] 检查 2：文件格式验证 - 通过
- [x] 检查 3：内容正确性 - 通过
- [x] 检查 4：功能验证 - 通过（设计验证）
- [x] 检查 5：向后兼容性 - 通过
- [x] 检查 6：编译验证 - 通过（YAML/JSON 格式验证）

### 最终结论

**✅ 通过**

### 验收记录

**验收日期**：2026-04-11
**验收人**：Claude (GLM-4.7)
**备注**：所有必需文件已创建，内容完整，格式正确，向后兼容性良好。变更已成功实施。

### 问题记录

| 检查项 | 问题描述 | 解决方案 | 状态 |
|--------|----------|----------|------|
| - | - | - | - |

### 后续行动

- [x] 如果验收通过，更新变更状态为 `completed`
- [ ] 如果验收失败，创建回归问题并修复
- [ ] 考虑将经验捕获到 `workflow/context/experience/`
