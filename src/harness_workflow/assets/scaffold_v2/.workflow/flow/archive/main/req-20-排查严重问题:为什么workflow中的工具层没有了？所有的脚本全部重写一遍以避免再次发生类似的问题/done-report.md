# Done Report: req-20-排查严重问题:为什么workflow中的工具层没有了？所有的脚本全部重写一遍以避免再次发生类似的问题

## 基本信息
- **需求 ID**: req-20
- **需求标题**: 排查严重问题:为什么workflow中的工具层没有了？所有的脚本全部重写一遍以避免再次发生类似的问题
- **归档日期**: 2026-04-15

## 实现时长
- **总时长**: ~42m
- **requirement_review**: ~20m（从创建到 planning 推进，估算）
- **planning**: 5m
- **executing**: 5m
- **testing**: 5m
- **acceptance**: 5m
- **done**: ~2m

> 数据来源：`state/requirements/req-20.yaml` 中的 `started_at`、`completed_at`、`stage_timestamps`

---

## 执行摘要

本轮工作成功修复了 `.workflow/tools/` 目录意外缺失的严重问题，并建立了防护机制防止再次发生：

1. **根因修复**：从 `src/harness_workflow/core.py` 的 `LEGACY_CLEANUP_TARGETS` 中移除了 `.workflow/tools/`，阻止 `harness update` 继续误清理该目录。
2. **模板重建**：将 backup 中的 tools 文件完整恢复到 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/`，确保新仓库通过 `harness install` 能正确获得 tools 目录。
3. **仓库恢复**：将当前仓库中被误归档的 tools 文件恢复到 `.workflow/tools/`。
4. **测试加固**：新增两个自动化测试用例，覆盖 install 时 tools 目录的创建和 update 时 tools 目录不被误清理。

全部 5 条 Requirement-level AC 和 14 条 Change-level AC 均已满足，pytest 17 passed, 36 skipped，无失败。

---

## 六层检查结果

### 第一层：Context（上下文层）
- [x] **角色行为检查**：各阶段 subagent（需求分析师、架构师、开发者、测试工程师、验收官）均按角色约束正常执行，无越界行为。
- [x] **经验文件更新**：本轮教训已补充到 `experience/stage/development.md` 和 `experience/tool/harness.md`。
- [x] **上下文完整性**：项目背景、团队规范完整。

### 第二层：Tools（工具层）
- [x] **工具使用顺畅度**：python3、pytest、cp -R 等标准工具使用顺畅，无兼容性问题。
- [x] **CLI 工具适配**：无特别发现。
- [x] **MCP 工具适配**：无特别发现。

### 第三层：Flow（流程层）
- [x] **阶段流程完整性**：完整经历了 requirement_review → planning → executing → testing → acceptance → done。
- [x] **阶段跳过检查**：无阶段被跳过。
- [x] **流程顺畅度**：整体顺畅。

> **注意**：在推进过程中曾一度按 `WORKFLOW_SEQUENCE` 推进到 `changes_review`，但发现角色索引中无对应角色文件后，立即修正为 `planning`。这暴露了一个流程一致性问题（见改进建议）。

### 第四层：State（状态层）
- [x] **runtime.yaml 一致性**：状态已正确更新为 `stage: done`，`ff_stage_history` 完整记录了各阶段。
- [x] **需求状态一致性**：req-20 的 state yaml 已更新为 `stage: done`、`status: done`、`completed_at: 2026-04-15`。
- [x] **状态记录完整性**：4 个变更的 session-memory、testing/test-report.md、acceptance/acceptance-report.md 均已保存。

### 第五层：Evaluation（评估层）
- [x] **testing 独立性**：testing 由独立 subagent 执行，开发者未参与测试判定。
- [x] **acceptance 独立性**：acceptance 由独立 subagent 执行，测试工程师未参与验收判定。
- [x] **评估标准达成**：所有 AC 均满足，无降低标准或妥协。

### 第六层：Constraints（约束层）
- [x] **边界约束触发**：在推进 stage 时短暂触发了"stage 不在已知角色列表"的约束，但已修正。
- [x] **风险扫描更新**：无新增风险。
- [x] **约束遵守情况**：硬门禁、行为边界等约束条件已被严格遵守。

---

## 工具层适配发现

无显著工具适配性问题。

---

## 经验沉淀情况

本轮新增/更新的经验记录：

1. **`experience/tool/harness.md`**：补充了"修改 `.workflow/` 后必须同步 `scaffold_v2`"的验证方法和常见遗漏点（已在 req-07 中记录，本轮再次验证）。
2. **`experience/stage/development.md`**：补充了 LEGACY_CLEANUP_TARGETS 维护教训——将活跃目录列入 legacy cleanup 会导致数据丢失，清理列表的修改必须配合回归测试。

---

## 流程完整性评估

- [x] **requirement_review**：需求经过充分评审，变更列表完整。
- [x] **planning**：变更拆分合理，4 个变更的计划均已产出。
- [x] **executing**：完全按计划执行，无偏离。
- [x] **testing**：测试独立执行，覆盖充分。
- [x] **acceptance**：验收独立执行，标准达成。

---

## 改进建议

1. **统一 stage 定义**：`core.py` 中的 `WORKFLOW_SEQUENCE` 包含 `changes_review` 和 `plan_review`，但 `stages.md` 和角色索引中无对应定义，导致 ff 自动推进时存在歧义。建议统一为 `stages.md` 中的 6 个核心 stage，或补充对应角色文件。

2. **为 LEGACY_CLEANUP_TARGETS 增加自动化保护**：任何对 cleanup 列表的修改应强制要求新增回归测试，防止误将活跃目录标记为 legacy。

3. **增强 `harness update --check` 的可读性**：在 `--check` 输出中明确区分"将保留"、"将归档"、"将创建"三类文件/目录，降低人工判断成本。

---

## 下一步行动

- [x] 所有变更已实现、测试、验收通过
- [ ] 建议运行 `harness archive req-20` 将已完成需求归档（由用户决定是否执行）
