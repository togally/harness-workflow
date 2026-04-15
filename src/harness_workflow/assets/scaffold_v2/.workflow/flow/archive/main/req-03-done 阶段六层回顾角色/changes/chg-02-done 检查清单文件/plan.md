# Change Plan

## 1. Development Steps

1. **创建文件**：使用 Write 工具创建 `.workflow/context/roles/done.md`
2. **编写六层检查清单**：
   - 第一层 context/：角色行为是否符合预期？经验文件是否更新？
   - 第二层 tools/：本轮有无工具用得不顺？有无 CLI/MCP 可替代？
   - 第三层 flow/：是否走了完整的阶段流程？有无阶段跳过或短路？
   - 第四层 state/：runtime.yaml / 各需求状态是否一致？
   - 第五层 evaluation/：testing 和 acceptance 是否真正独立执行？
   - 第六层 constraints/：边界约束是否有触发？有无需要更新 risk.md？
3. **添加工具层适配性问题模板**：
   - CLI 工具：本轮有无发现更适合的 CLI 工具可以替代当前手工步骤？
   - MCP 工具：有无 MCP 工具可以更好地服务某一层（如 context 层的经验管理）？
4. **添加经验沉淀验证步骤**：
   - 检查 `.workflow/context/experience/` 下相关文件是否已更新本轮教训
   - 如未更新，提示记录
5. **添加流程完整性检查项**：
   - 各阶段是否实际执行（requirement_review → changes_review → plan_review → executing → testing → acceptance）
   - 有无阶段被跳过（如直接从 planning 跳到 executing）？
6. **添加输出规范建议**：回顾报告写到哪里（建议：`session-memory.md` 的 `## 六层回顾报告` 区块）

## 2. Verification Steps

1. **文件存在检查**：确认 `.workflow/context/roles/done.md` 文件存在
2. **内容完整性检查**：
   - 是否包含六层检查清单（六层都列出）？
   - 是否包含工具层适配性问题模板（CLI/MCP）？
   - 是否包含经验沉淀验证步骤？
   - 是否包含流程完整性检查项？
   - 是否包含输出规范建议？
3. **定位检查**：文件是否在正确路径（context/roles/ 下，非其他位置）？
4. **格式检查**：内容是否为 Markdown 格式，结构清晰
