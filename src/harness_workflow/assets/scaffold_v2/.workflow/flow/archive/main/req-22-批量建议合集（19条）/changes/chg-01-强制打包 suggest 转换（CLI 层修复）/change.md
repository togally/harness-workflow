# chg-01-强制打包 suggest 转换（CLI 层修复）

## 目标
修复 `harness suggest --apply-all` 默认行为，强制将所有 pending suggest 打包为单一需求，杜绝逐条拆分为独立需求的制度漏洞。

## 范围
- 修改 `src/harness_workflow/core.py` 中的 `apply_all_suggestions()` 函数
- 修改 `src/harness_workflow/cli.py` 中 `suggest` 子命令的参数定义与帮助文本
- 不修改 `apply_suggestion()`（单条应用）的行为

## 变更内容
1. **默认强制打包**：`--apply-all` 时，所有 pending suggest 必须打包成一个需求；删除"逐条创建独立需求"的默认分支。
2. **标题逻辑**：
   - 若用户显式传入 `--pack-title`，使用该标题；
   - 否则使用默认标题 `批量建议合集（{n}条）`。
3. **需求内容增强**：在打包生成的 `requirement.md` 中，必须包含所有被合并 suggest 的标题/摘要列表（利用现有模板机制或后处理写入）。
4. **参数调整**：在 `cli.py` 中更新 `--apply-all` 和 `--pack-title` 的 help 文本，明确反映"强制打包"语义。

## 验收标准
- [ ] `harness suggest --apply-all` 无论 suggest 数量多少，只生成 1 个 requirement
- [ ] 生成的 `requirement.md` 中包含所有被合并 suggest 的清单
- [ ] 原有 suggest 文件在打包后被正确删除
- [ ] `cli.py` 帮助文本准确描述新的强制打包行为
- [ ] 相关单元测试（如存在）通过或已同步更新

## 依赖
无前置变更依赖。

## 阻塞
无。
