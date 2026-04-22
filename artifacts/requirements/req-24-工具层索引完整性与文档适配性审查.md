# 工具层索引完整性与文档适配性审查

> req-id: req-24 | 完成时间: 2026-04-17 | 分支: main

## 需求目标

1. 补全 `keywords.yaml`，将所有 `catalog/` 中已定义的工具注册到本地索引
2. 评估 `ratings.yaml` 的评分机制是否必要，如有必要则填充初始评分
3. 审查各工具 `catalog/*.md` 文档是否与实际使用场景（Claude Code / Codex / Qoder）对齐
4. 修正与当前环境不匹配的工具调用方式描述（如 `find-skills.md` 中的 `skillhub` CLI 调用）
5. 验证 toolsManager 角色按 SOP 执行时，能够正确为各 stage 角色推荐匹配的工具

## 交付范围

**包含：**
- `.workflow/tools/index/keywords.yaml` 补全
- `.workflow/tools/ratings.yaml` 评估与填充（如必要）
- `.workflow/tools/catalog/*.md` 文档审查与修正
- `toolsManager` 角色 SOP 与工具层实际能力的对齐验证

**不包含：**
- 新增工具到 catalog（除非审查中发现明显缺失）
- 修改 stage-tools.md 中的阶段白名单
- 修改 selection-guide.md 的决策流程
- 代码实现类工作（本项目为文档/配置层审查）

## 验收标准

- [x] `keywords.yaml` 包含 catalog 中所有已定义工具（至少覆盖 read、edit、bash、grep、agent、find-skills、git-commit、claude-code-context）
- [x] `ratings.yaml` 要么被填充有效评分，要么在文档中说明其当前为空的原因及填充规则
- [x] `find-skills.md` 中的调用方式与当前 agent 平台（Claude Code 的 `Skill` 工具）对齐
- [x] 所有 `catalog/*.md` 文档的"适用场景"和"不适用场景"描述准确、无过时信息
- [x] toolsManager 按 SOP 执行时，能够为 executing/testing/regression 等阶段的常见操作意图返回匹配结果

## 变更列表

- **chg-01** 补全 keywords.yaml 索引并填充 ratings.yaml：让 toolsManager 在本地索引中能够命中 catalog/ 下已定义的所有工具，并具备基于评分的优先级排序能力。
- **chg-02** 审查并修正 catalog 文档的平台适配性：确保所有 `catalog/*.md` 中的工具描述、调用方式与当前 Claude Code / Codex / Qoder 平台的行为一致，无过时或误导性信息。
- **chg-03** 端到端验证 toolsManager 查询流程：验证在 chg-01 和 chg-02 完成后，toolsManager 角色按 SOP 执行时，能够为各 stage 的常见操作意图正确匹配并推荐工具。
- **chg-04** 重构 stage-tools.md 约束表达，提升工具扩展性：将 `stage-tools.md` 从"枚举式白名单"重构为"能力类型 + 禁止规则 + 推荐列表"的表达式，降低新增工具的维护成本，确保 toolsManager 推荐的新工具能自然融入各 stage。
