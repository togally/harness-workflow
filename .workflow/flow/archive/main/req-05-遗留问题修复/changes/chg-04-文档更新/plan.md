# Plan: 开发与归档文档更新

## 执行步骤

### Step 1: 确定开发文档位置

检查项目中是否有 CONTRIBUTING.md、DEVELOPMENT.md 或类似文件。如果没有，在 README.md 中增加「本地开发」节。

### Step 2: 添加本地开发说明

在开发文档中添加：

```markdown
## 本地开发

源码修改后，需重新注入到 pipx 环境才能生效：

\`\`\`bash
pipx inject harness-workflow . --force
\`\`\`
```

### Step 3: 补充 archive 行为说明

在 README.md 的 `harness archive` 命令说明处，补充：

> `harness archive` 仅处理 `done` 状态的需求。未完成的需求无法归档。

### Step 4: 验证

- 确认文档内容准确
- 确认 markdown 格式正确

## 产物

- README.md（修改）
- 可能额外的开发文档文件（如 CONTRIBUTING.md）

## 风险评估

低风险：仅文档变更，无代码影响
