# Requirement

## 1. Title

harness next over-chain bug 修复（紧急）

## 1.5 Background

`harness next` 当前实现：从 verdict-driven stage（testing / acceptance）出发后，链式跳过下一 stage 直达 done。**未检查这些 stage 的 subagent 工作是否实际完成**（test-evidence.md / acceptance/checklist.md 是否产出）。

**dogfood 实证**：req-43（交付总结完善）+ req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 周期均触发——一次 `harness next`（含 `--execute`）从 executing 跳到 done，跳过独立 testing 和 acceptance 验证。主 agent 用手动 Edit runtime.yaml 滚回每个 stage 各派 subagent 才得以走完。

**关联 sug**：
- sug-38（harness next 在 verdict stage 链跳前应检查 subagent 工作是否完成，high）
- sug-40（sug-38 修复优先级评估，meta-followup）
- sug-46（sug-38 升 P0 / high，本 req 容器源 sug）

**优先级**：P0 紧急。不修则后续每个 req / bugfix 都得手动 Edit runtime 兜底。

## 2. Goal

- 给 verdict stage 加 "subagent 工作完成" gate 检查；未完成时不连跳，停在该 stage。
- 保留 same-role auto-jump（bugfix-5 落地的能力）和 explicit gate（executing → testing 用 --execute）逻辑。
- 不破坏 bugfix-5（同角色跨 stage 自动续跑硬门禁） / bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 的 stage_policies 契约。

## 3. Scope

### 3.1 IN

- `src/harness_workflow/workflow_helpers.py` `workflow_next` 主体：在 while 连跳条件上叠加"subagent 工作完成"检查（auto/verdict 才检查；same-role / terminal / explicit 不变）。
- 新增 helper `_is_stage_work_done(stage, root, requirement_id)`：按 stage 检查关键产物：
  - testing：`{req-flow-dir}/test-report.md` 存在 + 含 `§结论` PASS/FAIL/PARTIAL
  - acceptance：`{req-flow-dir}/acceptance/checklist.md` 存在 + 含 §结论
  - planning：`{req-flow-dir}/changes/chg-*/plan.md` 存在 ≥ 1 + 各含 §测试用例设计（bugfix-6 落地的契约）
  - executing：每个 chg/session-memory.md 末尾含 ✅ 标记 + 至少 1 个新 pytest 文件
  - bugfix 模式：testing/acceptance 同上，executing 检查 bugfix.md §修复方案 全 ✅
- `harness validate --contract stage-work-completion`：手动检查当前 stage 是否符合 work-done gate，方便 debug。
- 补 e2e 用例：mock 各 stage 缺产物时 `harness next` 不连跳；产物齐时正常连跳。

### 3.2 OUT

- 不改 stage_policies / role-stage-map / role-model-map（属 bugfix-5/6 范畴）。
- 不改 done 阶段六层回顾本身。
- 不改 record_subagent_usage / token 渲染（属 sug-39 / sug-41 / sug-42）。
- 不实现 "stage 工作部分完成" 的细粒度检查（done gate 只 boolean）。

## 4. Acceptance Criteria

- **AC-01**：`harness next` 从 executing 出发，若 chg session-memory 未含 ✅ 或缺 pytest，**不**自动跳过 testing；手工 Edit runtime workaround 不再必要。
- **AC-02**：`harness next` 从 testing 出发，若 test-report.md 不存在或 §结论 段缺，**不**自动跳过 acceptance。
- **AC-03**：`harness next` 从 acceptance 出发，若 acceptance/checklist.md §结论 缺，**不**自动跳过 done。
- **AC-04**：work-done gate 通过时，verdict-driven 自动跳行为保留（bugfix-5 / bugfix-6 不退化）。
- **AC-05**：补 ≥ 6 个 pytest 用例覆盖各 stage gate 正负 case；scaffold mirror 同步（如有）。

## 5. Split Rules

- 拆 1-2 chg：单 chg 含 helper + workflow_next 修改 + lint 子命令；分 2 chg 则 helper / lint 单独。analyst 自决。
- 紧急修复，scope 集中。完成后填 completion.md + 验证项目启动。
