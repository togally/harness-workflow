# Session Memory — chg-03（index.md 自动登记 + git auto-stage + 加载链活证）

## 1. Current Goal

为 chg-03 落 plan.md，落地 4 个 helper（`_pad_register_index` / `_append_table_row` / `_append_tool_list_item` / `_pad_git_stage`）+ `_pad_add` 增强（追加 3 块）+ 10 条 pytest TC。

## 2. Context Chain

- Level 0: 主 agent
- Level 1: analyst / opus

## 3. 关键决策（chg-03 范围内）

- **constraints / experience / tool 三种 schema 各自尊重原 schema**：
  - constraints: 顶层表格，path 含 `{scope}/` 子路径（path 字段相对 index.md 同目录的兼容语义已验证）
  - experience: 子目录 index.md 表格（5 子分类各一）
  - tool: 顶层「## 项目级工具清单」段含 markdown 列表项
  - 决策依据：现有 schema 已稳定（req-52/bugfix-13 立稳），破坏 schema 风险大于统一 schema 收益。chg-03 适配现有 schema 而非反过来。
- **scope 字段在 constraints/index.md 中写真实 scope（coding / api 等），不写 `constraints`**：与 path 字段的 `{scope}/{slug}.md` 保持一致；`_parse_index_md` 原解析逻辑兼容。
- **experience scope 写 `experience-{scope}`（如 `experience-stage`）**：与 `_load_project_level_index` scope_map 一致（line 8463）。
- **`_pad_git_stage` 用 subprocess + cwd=root**：避免依赖 user 的 cwd；非 git 仓 / git 缺失 silent skip + warn stderr，不阻塞 add（OQ-5 决策的语义：git stage 是优化项不是核心契约）。
- **stderr 活证复用 `_log_project_level_load`**：避免新 stderr 格式增项；user 只看到一个统一格式 `[harness] project-level loaded: ...`，与 install 时同款，加深印象。
- **scope label for log**：`rule → constraints` / `experience → experience` / `tool → tools`（与 install 中 `_proj_scope` 三大类对齐，line 3824）。

## 4. 未做（chg-03 边界）

- 不实装 questionary 引导（chg-04 做）
- 不实装 list 子命令（chg-04 做）
- 不写 dogfood 端到端 fresh-repo 多 pad 测试（chg-04 集中做）
- 不动 `_log_project_level_load` 函数（保持向前兼容）
- 不动 `_parse_index_md`（向前兼容已有表格 schema）

## 5. 待沉淀经验（chg 完成后回填）

- "**双 schema 共存**：machine-readable index.md 表格（constraints/experience）+ human-readable 列表段（tools）" —— 取决于 user 视角偏好，machine 侧加载链兼容两类即可。
- "**git stage 不阻塞 vs 必须成功**" —— 项目级承载层维护是 dev-tool 类命令，git 失败 silent skip 优于 abort 整命令；用户体验上"加完文件没 stage 但有警告"远好于"加完文件命令报错"。
- "**复用既有 stderr 日志格式**" —— 避免每个 chg 都引入新 log 格式，user 视野复杂度不爆炸。

## Executing Stage 完成记录

- 4 helper 落地：_pad_register_index / _append_table_row / _append_tool_list_item / _pad_git_stage
- _pad_add 已在 chg-02 基础上追加 3 块（index 登记 + git stage + 加载链活证）
- TC-08 幂等检查调整：用非注释行过滤（install 生成的 index.md 含 HTML 注释例子行）
- 测试：10 TC 全 pass（test_req53_pad_index.py）

✅ chg-03 完成
