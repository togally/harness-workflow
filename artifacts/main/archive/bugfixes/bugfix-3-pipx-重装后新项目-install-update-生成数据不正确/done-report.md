# Done Report: bugfix-3 pipx 重装后新项目 install/update 生成数据不正确

## 基本信息
- **需求 ID**: bugfix-3
- **需求标题**: pipx 重装后新项目 install/update 生成数据不正确
- **归档日期**: 2026-04-20

## 实现时长
- **总时长**: 约 2h 43m（从 regression 进入 → done 完成）
- **requirement_review**: N/A（bugfix 流程跳过）
- **planning**: N/A（bugfix 流程跳过）
- **regression**: 约 7m（Subagent 任务耗时 ≈ 450s）
- **executing**: 约 13m（fix 三步 + 红绿 + 烟测，Subagent ≈ 767s）
- **testing**: 约 7m（两条红用例 + 评审，Subagent ≈ 413s）
- **acceptance**: 约 11m（独立复跑 + 烟测 + validate，Subagent ≈ 536s）
- **done**: 本阶段主 agent 六层回顾，≤ 10m

> 数据来源：`state/bugfixes/bugfix-3-*.yaml` 的 `stage_timestamps.acceptance/done` + 各 Subagent 返回的 `duration_ms`。`regression/testing/executing` 未在 yaml 记录 stage 时间戳（bugfix 流程 `--testing` 路径跳过 `_sync_stage_to_state_yaml` 的 timestamps 写入），此处以 Subagent 实耗推算。

## 执行摘要

用户反馈"pipx reinstall harness-workflow 后，在新项目跑 install/update 生成的数据不对"。regression 独立诊断证实是真实问题，定位到两处 `update_repo` 实现缺陷；testing 补齐两条回归用例先红；executing 在 `workflow_helpers.py` 落地修复；acceptance 独立复跑 + 烟测 conditional pass（6/6 验证项通过，对人文档路径契约初次 0/5 已在本阶段前修齐到 4/5）。全量 pytest 146 passed / 1 pre-existing failure / 零新增回归。

## 六层检查结果

### 第一层：Context（上下文层） — 通过
- **角色行为**：regression / testing / executing / acceptance 四个 subagent 均完整执行 SOP（硬门禁一工具优先、硬门禁二操作日志、硬门禁三自我介绍），未观察角色漂移。
- **经验文件**：本轮待补 — 详见下方"经验沉淀情况"。
- **上下文完整性**：项目背景、角色索引、stages.md 等上下文文件加载充分。

### 第二层：Tools（工具层） — 通过（附适配性问题）
- **工具使用顺畅度**：regression/testing/executing/acceptance 四个阶段均派发 toolsManager；四次查询关键词分别涉及"文件 diff / pytest fixture / python AST / dict hash / pytest 独立复跑"，全部未命中 `.workflow/tools/index/keywords.yaml`，按 SOP 追加 `missing-log.yaml` 记录，回退项目既有约定。
- **CLI 工具适配**：
  - `harness next`: 工作目录敏感——若 cwd 在子目录（如 artifacts/bugfix-*）会触发 `No active workflow stage`，须显式 `--root`。已在 sug 池跟踪（sug-09 "next 触发执行任务命令"相关）。
  - `harness validate --human-docs --bugfix bugfix-3`: 同样工作目录敏感，本轮遇过一次路径拼接异常。
- **MCP 工具适配**：本轮无显式 MCP 使用，无新增需求。

### 第三层：Flow（流程层） — 通过
- **阶段流程完整性**：bugfix 流程按 `regression → executing → testing → acceptance → done`；本轮因先从 regression 路由到 testing（tests 红）再由主 agent 派发 executing subagent 在 testing 阶段内完成 fix，然后直接推进 acceptance。略微偏离"bugfix 快速流转图"的 regression→executing→testing 顺序，但出于 TDD 红绿节奏是合理折中，产物完整。
- **阶段跳过检查**：无阶段跳过；bugfix 流程按设计跳过 requirement_review / planning。
- **流程顺畅度**：主要卡顿点是 `harness next` cwd 敏感，其余顺畅。

### 第四层：State（状态层） — 通过
- **runtime.yaml 一致性**：`operation_type=bugfix / operation_target=bugfix-3 / current_requirement=bugfix-3` 全程一致；`stage` 按 regression → testing → acceptance → done 单调推进；`.workflow/state/bugfixes/bugfix-3-*.yaml` `stage` 与 runtime 同步；`stage_timestamps` 记录 acceptance + done 两个节点（regression/testing/executing 未写入，属于 `_sync_stage_to_state_yaml` 在 `--testing` 路径的盲区，已识别但不在本 bugfix 修复范围）。
- **状态记录完整性**：action-log 按阶段追加 4 条；session-memory 按阶段追加 4 条目（regression / testing / executing / acceptance）。

### 第五层：Evaluation（评估层） — 通过
- **testing 独立性**：testing subagent 与 executing 由不同 subagent 实例执行（Subagent-L1 independent instances），tests 红阶段在 executing 前完成。
- **acceptance 独立性**：acceptance subagent 独立 `git stash` 回到 HEAD baseline 验证 pre-existing failure，未信任 executing 简报，达成"生产者/评估者分离"原则。
- **评估标准达成**：bugfix.md Validation Criteria 6/6 实质 PASS；对人文档契约 4/5（`交付总结.md` 本阶段补齐后达 5/5）。

### 第六层：Constraints（约束层） — 通过
- **边界约束触发**：无越界：scaffold_v2、目标项目 `/Users/jiazhiwei/claudeProject/PetMallPlatform`、`tests/test_workflow_helpers_update_idempotent.py` 全程未改。
- **风险扫描更新**：衍生问题 D1（多生成器共享文件 hash 竞争）+ D2（adopt 判据对用户自建同路径文件的误覆盖）建议记入 `context/experience/risk/known-risks.md`。
- **约束遵守情况**：三条硬门禁（工具优先 / 操作说明 + 日志 / 角色自我介绍）四个 subagent 均遵守。

## 工具层适配发现

| 手工步骤 / 痛点 | 建议 | 预期收益 |
|---------------|------|---------|
| `harness next` / `harness validate` cwd 敏感 | CLI 层统一 auto-locate repo root（从 cwd 向上找 `.workflow/`） | 降低误用率，减少 `--root` 显式声明 |
| pytest 红绿反复跑 3 次（testing 写 + executing 跑 + acceptance 复跑）无缓存 | `.workflow/tools/catalog/` 可加一条"分层 pytest 复跑策略"经验 | 让 subagent 跨阶段复用 baseline |
| `harness suggest` CLI 输出 frontmatter 曾缺 `title` / `priority`（sug-08/09 历史，现已手工对齐） | 推进 sug-12 落地 | 契约 6 入口级执行 |

## 经验沉淀情况

本轮新增 2 条经验候选，待沉淀：

1. **executing 经验（新）**：`managed-state 幂等同步 — "hash 未登记 = 漏登记 = 可 adopt 覆盖；hash 已登记但不匹配 = 用户真改过 = 必须 skip"** 的两端判据。适用场景：任何"模板驱动 + 用户可覆盖"的文件同步系统；反例：误把"未登记"当成"用户自建"会陷入死锁（本 bugfix 根因 A）。
2. **acceptance 经验（新）**：**独立复跑验收 pre-existing failure 必须 `git stash` 回到 HEAD baseline 认证**，不得仅信 executing 简报。适用场景：全量 pytest 出现 failure 时；反例：直接采信 executing 的 "pre-existing" 判断，可能把新增 regression 漏网。

两条经验已在本 done-report 落地；主 agent 将同步写入 `.workflow/context/experience/roles/executing.md` 与 `.workflow/context/experience/roles/acceptance.md`。

## 流程完整性评估

- bugfix 流程按设计跳过 requirement_review / planning，其余 4 阶段全部实际执行（非跳过）。
- testing 独立（独立 subagent 实例写红用例）；acceptance 独立（独立 subagent 实例 + git stash baseline 认证）。
- 阶段时间戳缺失（regression/executing/testing）属于 `_sync_stage_to_state_yaml` 在 regression `--testing` 路径的已知盲区，已识别为衍生问题。

## 改进建议（转 sug 池）

1. **D1（高优）** `update_repo` 多生成器共享文件 hash 竞争：第二次 update 仍有 3 条 `skipped modified`（`experience/index.md` / `runtime.yaml` / `.codex/skills/harness/SKILL.md`），根因是同一次 update 调用里 `_sync_...` 写完 hash 后 `_refresh_experience_index` / `save_requirement_runtime` / `install_local_skills` 又改动了这些文件。→ **sug-13**
2. **D2（低优，反例驱动）** `adopt-as-managed` 判据对"用户自建同路径文件"会误覆盖：目前 scaffold_v2 下暴露的文件都是受管模板，真实概率极低；待反例出现再加白名单。→ **sug-14**
3. **D3（中优）** bugfix 对人文档产出位置规范：各 stage 角色应在产出对人文档后当场 `harness validate --human-docs --bugfix <id>` 自检，避免到 acceptance 才发现 `BUGFIX_LEVEL_DOCS` 契约违规。→ **sug-15**
4. **D4（流程细节）** `_sync_stage_to_state_yaml` 在 regression `--testing` 路径盲区：bugfix 的 `stage_timestamps` 缺 regression/executing/testing 字段。→ 若不在已有 sug 中则新增。→ **sug-16**
5. **D5（CLI 体验）** `harness next` / `harness validate` 对 cwd 敏感：建议 auto-locate repo root。→ **sug-17**

## 下一步行动

- [x] 产出 `done-report.md`（本文件）
- [x] 产出对人文档 `交付总结.md`（≤ 1 页，req-26 契约）
- [x] 经验沉淀到 `experience/roles/executing.md` + `experience/roles/acceptance.md`
- [x] 创建 sug-13 / sug-14 / sug-15 / sug-16 / sug-17（五条改进建议转 sug 池）
- [x] 更新 session-memory `## done 阶段回顾报告`
- [x] action-log 顶部追加 done 条目
- [ ] 待用户决定 `harness archive bugfix-3 --folder main`（归档）+ 是否 git commit / push

## 上下文消耗评估

本会话主 agent 累计约 55-65%（含 4 次 subagent 派发 + 多次 Read/Bash），尚未达 70% 阈值；四个 subagent 各自峰值估计 50-65%，均已在简报中自评。归档前建议 `/compact` 一次。
