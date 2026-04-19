# 批量建议合集（19条）

## 背景
由 suggest 池中的 19 条建议打包合并而成的一个需求。原始意图来自 req-31：建议转化成需求要打包不要分开，打包成需求之后原有建议要清除。

## 目标
系统化处理 suggest 池中积压的 19 条改进建议，按需拆分为变更并逐一实现。

## 建议清单

1. **sug-01-suggestion.md**
   - 我希望可以状态记录的时候记录一份对话摘要，这样下次我们进入或者恢复对话的时候可以展示这个摘要，让我们也可以快速回忆之前的沟通记录
2. **sug-02-suggestion.md**
   - 如果有本地git仓库，归档后可以询问是否要提交git
3. **sug-03-suggestion.md**
   - 每个需求在各个阶段的流转可以做一个记录，然后我可以指定校验某个项目的流程是否符合我们的要求
4. **sug-04-suggestion.md**
   - 每个需求在各个阶段的流转可以做一个记录，然后我可以指定校验某个项目的流程是否符合我们的要求
5. **sug-05-suggestion.md**
   - 所有的regression命令必须沉淀经验，当然不一定有经验沉淀但是必须沉淀，因为regression无论是问题还是需求肯定都说明流程有问题
6. **sug-06-suggestion.md**
   - 项目编译要过写成开发测试验收的硬门禁
7. **sug-07-req-12-stage-req-12-executing-harness-next.md**
   - 建议为 req-12 补充更精确的 stage 时间戳：当前 req-12 的时间戳是在 executing 阶段后补录的，无法准确反映各阶段真实耗时。未来应确保 harness next 正确记录时间戳。
8. **sug-08-tests-test-cli-py-4.md**
   - 建议梳理并修复预存测试失败：tests/test_cli.py 中有 4 个与模板演进相关的失败用例，长期不修复会降低测试可信度。
9. **sug-09-flow-testregressionbugtest.md**
   - 经验需要索引目录避免经验过多导致问题。flow中每个阶段结束都需要沉淀下经验，我关注到现在test都没有合适的经验沉淀。regression确定的bug就可以总结到test和测试验收阶段中不是吗
10. **sug-10-suggestion.md**
   - 建议转化成需求要打包不要分开，打包成需求之后原有建议要清除
11. **sug-11-harness-suggest-apply-all-dry-run-suggest.md**
   - 建议未来为 harness suggest --apply-all 增加 --dry-run 选项：让用户在真正执行打包和删除前，先预览哪些 suggest 会被打包、生成的标题是什么，提升操作安全感。
12. **sug-12-stage-ff.md**
   - 统一 stage 定义：core.py 中的 WORKFLOW_SEQUENCE 包含 changes_review 和 plan_review，但 stages.md 和角色索引中无对应定义，导致 ff 自动推进时存在歧义。建议统一为 stages.md 中的 6 个核心 stage，或补充对应角色文件。
13. **sug-13-legacy-cleanup-targets.md**
   - 为 LEGACY_CLEANUP_TARGETS 增加自动化保护：任何对 cleanup 列表的修改应强制要求新增回归测试，防止误将活跃目录标记为 legacy。
14. **sug-14-harness-update-check.md**
   - 增强 harness update --check 的可读性：在 --check 输出中明确区分“将保留”、“将归档”、“将创建”三类文件/目录，降低人工判断成本。
15. **suggest-01-fix-timestamp-accuracy.md**
   - 修复 harness next 时间戳记录精度
16. **suggest-02-mandatory-done-report.md**
   - 将 done-report.md 设为 done 阶段硬门禁
17. **suggest-03-fill-empty-experience.md**
   - 填充 stage/testing.md 和 stage/acceptance.md 经验文件
18. **suggest-04-simple-requirement-lessons.md**
   - 建立简单需求的经验沉淀最低标准
19. **suggest-05-mandatory-artifacts-check.md**
   - 将 artifacts/requirements/ 制品仓库纳入 done 阶段必检项

## 范围
- 处理上述 19 条建议中优先级为高/中的条目
- 低优先级建议可作为后续迭代或单独变更处理
- 不修改 harness CLI 核心架构（除非某条建议明确要求）

## 验收标准
- [ ] 所有高优先级建议均已转化为变更并进入执行
- [ ] 打包需求完成后，suggest 池已清空
- [ ] 未实现或推迟的建议已记录原因并更新状态