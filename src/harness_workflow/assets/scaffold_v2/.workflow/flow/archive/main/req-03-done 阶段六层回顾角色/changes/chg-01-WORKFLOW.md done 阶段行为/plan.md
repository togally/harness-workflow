# Change Plan

## 1. Development Steps

1. **定位插入点**：读取 `WORKFLOW.md`，在 `## 职责外问题处理` 区块之后、文件结束之前选择合适位置
2. **编写内容**：
   - 区块标题：`## done 阶段行为`
   - 说明：当 stage=done 时，主 agent 执行以下动作
   - 动作清单：
     a. 读取 `context/roles/done.md`（作为检查清单）
     b. 逐层执行六层回顾检查（context/tools/flow/state/evaluation/constraints）
     c. 工具层专项：询问本轮有无 CLI/MCP 工具适配性问题
     d. 经验沉淀验证：确认 experience/ 文件已更新本轮教训
     e. 流程完整性检查：各阶段是否实际执行（非跳过）
     f. 输出回顾报告到 `session-memory.md` 或单独文件
3. **保存文件**：使用 Edit 工具将新内容写入 `WORKFLOW.md`

## 2. Verification Steps

1. **文件存在检查**：确认 `WORKFLOW.md` 包含 `## done 阶段行为` 区块
2. **内容完整性检查**：
   - 区块是否引用 `context/roles/done.md`？
   - 是否列出六层回顾动作（context/tools/flow/state/evaluation/constraints）？
   - 是否包含工具层适配性问题询问（CLI/MCP）？
   - 是否包含经验沉淀验证步骤？
   - 是否包含流程完整性检查？
   - 是否指定输出位置（session-memory.md）？
3. **格式检查**：区块格式是否符合 Markdown 规范，有无语法错误
