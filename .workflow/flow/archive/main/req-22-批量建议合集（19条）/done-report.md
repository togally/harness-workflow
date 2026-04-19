# Done Report: req-22-批量建议合集（19条）

## 基本信息
- **需求 ID**: req-22
- **需求标题**: 批量建议合集（19条）
- **归档日期**: 2026-04-15

## 实现时长
- **总时长**: ~35m
- **planning**: ~8m
- **executing**: ~20m
- **testing**: ~5m
- **acceptance**: ~2m
- **done**: ~3m

## 执行摘要
本轮工作修复了"harness suggest --apply-all 没有遵守硬门禁导致错误拆分为19个独立需求"的制度漏洞。核心成果包括：
1. **CLI 层修复**：`core.py` 的 `apply_all_suggestions()` 已强制要求只创建 1 个需求；`cli.py` 的 help 文本已更新
2. **约束文档**：新建 `.workflow/constraints/suggest-conversion.md`，明确规定 suggest 批量转换必须打包、禁止拆分
3. **角色/清单集成**：在 `planning.md` 和 `review-checklist.md` 中植入了 suggest 转换约束检查项
4. **Skill 层提示**：在 `.claude`、`.qoder`、`.codex` 三平台的 `skills/harness/SKILL.md` 中增加了强制打包要求

## 六层检查结果

### Context 层
- [x] 角色行为符合预期：开发者、测试员、验收员各司其职
- [x] 新增约束文档已纳入 Harness 工作流体系

### Tools 层
- [x] 工具使用顺畅：临时目录测试验证了 `harness suggest --apply-all` 的打包行为
- [x] pytest 通过（17 passed, 36 skipped）

### Flow 层
- [x] 流程完整：planning → executing → testing → acceptance → done
- [x] 无阶段被跳过

### State 层
- [x] `runtime.yaml` 状态与实际执行一致
- [x] `req-22` 状态已更新为 done
- [x] 关键产物已保存

### Evaluation 层
- [x] testing 独立执行，确认强制打包逻辑、约束文档、Skill 提示均正确
- [x] acceptance 独立执行，确认 4 条验收标准全部满足
- [x] 评估标准达成

### Constraints 层
- [x] 硬门禁和角色约束均被遵守
- [x] 新增 `suggest-conversion.md` 本身就是约束层的重要补强

## 经验沉淀情况
- `suggest-conversion.md` 已成为 Harness 约束体系的一部分
- 硬门禁提示植入经验：在 CLI 代码层、约束文档层、Skill 提示层同时设防，才能覆盖 agent 的所有执行入口
- 临时目录测试验证了 `harness suggest --apply-all` 的行为符合预期

## 流程完整性评估
- 各阶段均实际执行，无跳过
- 本次修复从代码、文档、Skill 三个层面同时堵住了制度漏洞

## 改进建议
1. 观察未来 2-3 个月 `harness suggest --apply-all` 的使用情况，确认不再有拆分行为
2. 如发现其他 CLI 命令存在类似"不经过角色阶段"的入口，建议同样补充约束文档和 Skill 提示

## 下一步行动
- 执行 `harness archive "req-22"` 归档本需求
