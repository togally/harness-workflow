# Done Report: req-26-uav-split

## 基本信息
- **需求 ID**: req-26
- **需求标题**: uav-split（六条 sug 合并修复 + 双轨对人文档机制）
- **归档日期**: 2026-04-19（本报告产出日期；archive 动作由用户决策）

## 实现时长
- **总时长**: 同日完成（started_at = completed_at = 2026-04-19）
- **requirement_review**: N/A（未记录独立时间戳）
- **planning**: N/A（同日合并记录）
- **executing**: N/A（同日合并记录）
- **testing**: 2026-04-19 07:59:19 UTC
- **acceptance**: 2026-04-19 08:04:56 UTC
- **done**: 2026-04-19 08:07:11 UTC

> 数据来源：`.workflow/state/requirements/req-26-uav-split.yaml` 的 `started_at` / `completed_at` / `stage_timestamps`。

---

## 执行摘要

req-26 系统化处理了 req-25 及之前遗留的 6 条合并建议（sug-01~sug-06），拆为 6 个 change 并行推进：

1. **sug-01+sug-04 → chg-01**：修复 `harness regression` 命令簇（--confirm 不消费 regression 标记 + 产出目录 kebab-case 带 id 前缀）
2. **sug-02 → chg-02**：修复 `harness rename` 保留 `{id}-` 前缀并同步 state yaml / runtime.yaml（并入 `harness change` 目录 kebab-case 清洗）
3. **sug-03 → chg-03**：`harness next` 自动写回 stage yaml 的 stage / status 字段
4. **sug-05 → chg-04**：修复 `harness archive` 归档路径双层 branch（`archive/main/main/` → `archive/main/`）
5. **sug-06 → chg-05**：建立各 stage 角色双轨输出对人文档 SOP + 7 份中文模板（并入 scaffold_v2 同步 + `harness change` 模板中文完整化）
6. **AC-07 → chg-06**：端到端 smoke 验证六条 sug 集成效果

**测试结果**：req-26 新增 23 条 helper/smoke 用例 + 独立补测 5 条，共 28 条**全部通过**；全量 86 条中 3 failures + 3 errors 经 `git checkout 3f94c30^` 回滚核验为**预存基线**，与 req-26 无关。

**验收结果**：有条件通过（AC-01~AC-05 / AC-07 全部通过；AC-06 机制侧静态契约齐全，运行时对人文档部分符合 chg-05 SOP"对后续阶段生效"的豁免）。

---

## 六层检查结果

### 第一层：Context（上下文层）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 角色行为检查 | **通过** | planning / executing / testing / acceptance 各阶段 subagent 按 SOP 执行，session-memory 结构完整；planning 阶段主动捕获 2 条潜在问题并请用户拍板（B/C 并入 chg-02 / chg-05）。 |
| 经验文件更新 | **部分** | `experience/roles/testing.md` 已有"预存测试失败需随模板演进修复""静态检查不能替代工具运行"两条已有经验，本轮相关但未新增；其他 5 份角色经验文件为 placeholder。本报告已在 testing.md 补充本轮教训（详见"经验沉淀"）。 |
| 上下文完整性 | **通过** | `requirement.md` Goal/Scope/Excluded/AC 覆盖完整，7 条 AC 清晰可核查；planning session-memory 第 8 节"修订记录"完整记录了 B/C 问题并入过程。 |

**L1 结论**：需求 Goal/Scope/AC 完整覆盖；6 条 sug 全部落入 AC-01~AC-07 中，零遗漏。

### 第二层：Tools（工具层）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 工具使用顺畅度 | **通过** | `harness change` × 6 次 / `harness next` × 多次 / `harness regression --confirm` / `harness archive` 全部无报错执行。 |
| CLI 工具适配 | **本轮修正** | planning 阶段报告：`harness change` 目录命名未 kebab-case（空格 + 中文标点），且生成模板是英文极简 placeholder。两项已并入 chg-02 / chg-05 在本需求内修复。 |
| MCP 工具适配 | **无** | 本轮为 CLI / 文档 / 测试变更，无 MCP 工具需求。 |

**L2 结论**：6 个 change 拆分合理——AC-01+AC-04 合并入 chg-01（regression 命令簇共享入口代码，合并避免同命令簇改两次）；AC-02/03/05 独立命令独立成 change；AC-06 作为纯文档变更单独成 chg-05；AC-07 端到端 smoke 依赖前 5 个 change 合入压轴成 chg-06。无遗漏、无重复。

### 第三层：Flow（流程层）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 阶段流程完整性 | **通过** | runtime.yaml `ff_stage_history: [regression, planning, testing, acceptance]` + stage_timestamps 记录了 testing / acceptance / done 时间戳。 |
| 阶段跳过检查 | **通过** | 无阶段跳过行为。 |
| 流程顺畅度 | **通过** | changes_review 与 plan_review 阶段由主 agent 确认后合并推进；executing 分 6 个 change 并行执行。 |

**L3 结论**：代码改动质量可控——chg-02 / chg-01 共享 `slugify` / 新增 `sanitize_artifact_dirname()`，util 层复用降低重复实现风险；chg-05 采用纯文档策略不改 CLI 代码，风险隔离；chg-06 smoke 在 tempdir 走完整生命周期链路，端到端覆盖充足。

### 第四层：State（状态层）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| runtime.yaml 一致性 | **通过** | `current_requirement: req-26` / `stage: done` / `active_requirements: [bugfix-3, bugfix-4, bugfix-5, req-26]` 与实际一致。 |
| 需求状态一致性 | **通过** | `.workflow/state/requirements/req-26-uav-split.yaml` 的 `stage: done` / `status: done` / `completed_at` 自动写回（chg-03 生效证明）。 |
| 状态记录完整性 | **通过** | stage_timestamps 记录 testing / acceptance / done 三阶段（requirement_review / planning / executing 未单独记录，属 sug-07 已归档范畴，不阻塞本轮）。 |

**L4 结论**：测试覆盖度满足 AC-01~AC-05/07 helper 层 + 端到端；AC-06 降级为静态契约，运行时行为仅在 executing/testing/acceptance 的对人文档实际落盘中体现（`测试结论.md` / 6 份 `实施说明.md` / `验收摘要.md` 均落盘 ✓）。基线漂移问题（3 fail + 3 error）已确认为预存，补测 5 条独立复核 AC-06 字段顺序。

### 第五层：Evaluation（评估层）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| testing 独立性 | **通过** | testing 子 agent 独立跑全量 + 增量用例，独立补测 5 条从第三方视角核查 AC-06 字段顺序，未被 executing 影响。 |
| acceptance 独立性 | **通过** | acceptance 独立核对 7 条 AC，独立做 Excluded 反例核对（`git show --stat 3f94c30`），独立统计对人文档落盘数量，未被 testing 影响。 |
| 评估标准达成 | **有条件** | AC-06 机制侧静态契约齐全但未在本 req-26 内验证"agent 真实落盘行为"——已转为 sug-09。 |

**L5 结论**：AC 验证充分度——AC-01/02/03/04/05/07 硬验；AC-06 静态契约 + 部分运行时落盘（executing/testing/acceptance 产出真实对人文档）间接证明。未达项按"下一需求首次完整示范"+"新开 bugfix-6"两路承接，不驳回本需求。

### 第六层：Constraints（约束层）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 边界约束触发 | **通过** | `.workflow/flow/` 反例核对 **OK**（仅 chg-01 合规删除 `sug-01-regression-confirm-bug.md`）；`artifacts/bugfixes/bugfix-2/` + `artifacts/main/bugfixes/bugfix-{3,4,5}/` 未触碰（git stat 核对）。 |
| 风险扫描更新 | **无** | 本轮未引入新风险。 |
| 约束遵守情况 | **通过** | 硬门禁一（委派 toolsManager）/ 二（action-log）/ 三（自我介绍）由各阶段 subagent 按 SOP 执行；对人文档硬门禁在 executing/testing/acceptance 阶段被遵守。 |

**L6 结论**：本周期暴露的流程/工具/角色 SOP 问题：
1. **`harness change` 模板历史积弊**——英文极简 + 未做目录 kebab-case 清洗，已在本需求内顺带修复；
2. **对人文档 SOP 执行起点问题**——req-26 自身 requirement_review / planning 阶段在 chg-05 合入前已完成，按规约豁免回溯；下一需求需作为首次完整示范（sug-11）；
3. **预存基线长期未修**——3 fail + 3 error 基线多轮未清，降低测试可信度（sug-08）。

---

## 工具层适配发现

- **CLI 工具**：`harness change` 目录命名 + 模板质量已在 chg-02 / chg-05 修复；其他 CLI 命令本轮无新发现。
- **MCP 工具**：无。

---

## 经验沉淀情况

本轮已验证并补充 `.workflow/context/experience/roles/testing.md`（新增"经验五：AC 可降级为静态契约但需后续闭环"）。其他 placeholder 经验文件（planning/acceptance）暂不强制初始化，留待 sug-11 下一需求完整示范后一次性沉淀更有价值的样例。

`experience/roles/testing.md` 经验一（预存基线需及时修）和经验三（静态检查不能替代工具运行）与本轮现象高度相关，已通过 sug-08 / sug-09 转为实际行动项。

---

## 流程完整性评估

- requirement_review：完成，产出 `requirement.md`（7 条 AC）。
- changes_review / planning / plan_review：合并推进，产出 6 份 change.md + plan.md，session-memory 完整记录 B/C 并入决策。
- executing：6 个 change 并行执行，各产出 `实施说明.md`。
- testing：全量 + 增量 + 独立补测，产出 `测试结论.md`。
- acceptance：独立核对 7 条 AC + Excluded 反例核对，产出 `验收摘要.md`。
- done：六层回顾本报告 + `交付总结.md`。

**流程完整、无跳阶段、无短路**。

---

## 改进建议（转 suggest 池）

本轮产出 4 条 suggest：

- **sug-08**：新开 bugfix-6 修复 3 fail + 3 error 预存基线（`.workflow/flow/suggestions/sug-08-bugfix-6-preexisting-baseline.md`）
- **sug-09**：补充 AC-06 对人文档"agent 运行时真实落盘"验证（`.workflow/flow/suggestions/sug-09-ac06-agent-runtime-verification.md`）
- **sug-10**：下游已安装仓库的 `harness change` 模板刷新策略（`.workflow/flow/suggestions/sug-10-downstream-repo-change-template-refresh.md`）
- **sug-11**：下一需求作为对人文档产出链首次完整示范（`.workflow/flow/suggestions/sug-11-next-req-first-full-human-doc-demo.md`）

编号续 archived 中最大 sug-07 之后，起于 sug-08。

---

## 下一步行动

- **行动 1**：由用户决策是否现在执行 `harness archive "req-26"` 归档。
- **行动 2**：开 bugfix-6 承接 sug-08（预存基线），不阻塞本需求归档。
- **行动 3**：下一新需求（预计承接 sug-09 / sug-11）启动时，首阶段即严格执行对人文档产出链。

## 报告末尾校验

- [x] 六层检查已全部完成
- [x] runtime.yaml `stage: done` 与 `state/requirements/req-26-uav-split.yaml` `stage: done` 一致
- [x] 改进建议已提取并写入 suggest 池（sug-08~11 四条）
- [x] 经验沉淀已检查（testing.md 补充一条；planning/acceptance placeholder 留待下一需求示范）
- [x] 对人文档 `交付总结.md` 已在 `artifacts/main/requirements/req-26-uav-split/` 下产出
