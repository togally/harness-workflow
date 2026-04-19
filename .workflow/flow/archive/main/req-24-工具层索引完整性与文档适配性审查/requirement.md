# Requirement

## 1. Title

工具层索引完整性与文档适配性审查

## 2. Background

用户提出疑问：当前工具层的逻辑和文档是否适合现有角色使用。经过初步审查发现：

- `toolsManager` 角色的核心职责是搜索、匹配并推荐最合适的工具
- 其 SOP 要求读取 `.workflow/tools/index/keywords.yaml` 和 `.workflow/tools/ratings.yaml` 进行工具匹配
- 但 `keywords.yaml` 中仅注册了 3 个工具（agent、find-skills、git-commit），而 `catalog/` 中实际存在 7 个工具定义 + 1 个模板
- `ratings.yaml` 几乎为空，没有评分数据供 toolsManager 做优先级排序
- 这意味着当 stage 角色需要查询 Read、Edit、Bash、Grep 等常用工具时，toolsManager 无法在本地索引中命中

## 3. Goal

1. 补全 `keywords.yaml`，将所有 `catalog/` 中已定义的工具注册到本地索引
2. 评估 `ratings.yaml` 的评分机制是否必要，如有必要则填充初始评分
3. 审查各工具 `catalog/*.md` 文档是否与实际使用场景（Claude Code / Codex / Qoder）对齐
4. 修正与当前环境不匹配的工具调用方式描述（如 `find-skills.md` 中的 `skillhub` CLI 调用）
5. 验证 toolsManager 角色按 SOP 执行时，能够正确为各 stage 角色推荐匹配的工具

## 4. Scope

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

## 5. Acceptance Criteria

- [x] `keywords.yaml` 包含 catalog 中所有已定义工具（至少覆盖 read、edit、bash、grep、agent、find-skills、git-commit、claude-code-context）
- [x] `ratings.yaml` 要么被填充有效评分，要么在文档中说明其当前为空的原因及填充规则
- [x] `find-skills.md` 中的调用方式与当前 agent 平台（Claude Code 的 `Skill` 工具）对齐
- [x] 所有 `catalog/*.md` 文档的"适用场景"和"不适用场景"描述准确、无过时信息
- [x] toolsManager 按 SOP 执行时，能够为 executing/testing/regression 等阶段的常见操作意图返回匹配结果

## 6. Split Rules

- chg-01: 补全 `keywords.yaml` 索引并填充 `ratings.yaml`
- chg-02: 审查并修正 `catalog/*.md` 文档（按平台适配性）
- chg-03: 端到端验证 toolsManager 的工具查询流程
