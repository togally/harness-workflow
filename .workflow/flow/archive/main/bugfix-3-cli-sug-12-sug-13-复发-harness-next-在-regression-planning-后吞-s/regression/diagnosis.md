# Regression Diagnosis — bugfix-3

## Issue
CLI sug-12 / sug-13 复发：`harness next` 在 regression/planning 后吞 stage（执行至 testing 跳过应有的 planning/executing），且 `runtime.yaml` ↔ `state/{requirements,bugfixes}/*.yaml` 的 stage 字段不同步（多次手工修复）。新增证据：今天 `harness archive` 错把 bugfix-3 当 archive 目标（不是 current_requirement bugfix-2）。

## 真实性判定

- [x] **真实问题**：3 个独立缺陷叠加，全部已在源码中定位到具体函数 + 行号。

## 根因分析（按缺陷分）

### 缺陷 1（sug-12）：harness next 不读 regression decision，直接走默认 sequence

- 出处：`src/harness_workflow/workflow_helpers.py::workflow_next`（line 6162-6259）
- 根因：函数实现完全不读 `runtime.current_regression`，也不读 `regressions/{reg-id}/decision.md`，无条件按 `WORKFLOW_SEQUENCE / BUGFIX_SEQUENCE / SUGGESTION_SEQUENCE` 推进 `idx + 1`。
- 触发场景：req-36 跑到 done（或 acceptance）后，发现 reg-01 / reg-02 → 跑 `harness regression`（写入 `current_regression = reg-01`）→ 诊断师在 `decision.md` 写"路由：planning（拆新 chg）"→ 主 agent 跑 `harness next` → 期望切到 `planning`，实际从 `done` 卡住或从 `acceptance` 推到 `done`，**完全忽略 regression 路由意图**。
- 二级根因：`regression-decision.md.tmpl`（`assets/skill/assets/templates/regression-decision.md.tmpl`）没有结构化"路由 stage"字段，只有自由文本"3. 后续流转"，机器无法可靠解析。

### 缺陷 2（sug-13）：runtime ↔ state yaml 不同步（含 enter 后 operation_type 残留）

- 出处 A：`src/harness_workflow/workflow_helpers.py::enter_workflow`（line 6298-6340）
- 根因 A：`enter_workflow` 只写 `current_requirement` + `current_requirement_title`，**不更新 `operation_type` + `operation_target`**。当用户从 req-X 切到 bugfix-Y 时，`operation_type` 残留 "requirement"。
- 出处 B：`src/harness_workflow/workflow_helpers.py::load_requirement_runtime`（line 383-404）
- 根因 B：懒回填 `operation_type` / `operation_target` 仅在字段为空时触发（line 395 `if current_req and not operation_type`），**不覆盖**残留值。
- 联级后果：`workflow_next` 调用 `_sync_stage_to_state_yaml(root, operation_type, ...)` 时 `operation_type = "requirement"` → 写到 `state/requirements/` 子目录而非 `state/bugfixes/`，对应的 bugfix yaml 永远不更新；`runtime.stage` 一路推进而 bugfix yaml 的 stage 永远停在初始值。
- 用户活证：今天 `harness enter bugfix-2` → 4 次 `harness next` → runtime.stage 走 regression→executing→testing→acceptance→done，但 `state/bugfixes/bugfix-2-*.yaml` 的 stage 一直停在 "regression"。

### 缺陷 3（额外发现）：harness archive 选错目标

- 出处：`src/harness_workflow/cli.py::main` 的 `archive` 分支（line 555-592）
- 根因 A：调用 `prompt_requirement_selection(done_reqs, preselect=args.requirement)`，**没传 `current_requirement`**作为 preselect。
- 出处：`src/harness_workflow/cli.py::prompt_requirement_selection`（line 120-153）
- 根因 B：当 preselect 为 None 时，`default_value = requirements[0]["req_id"]`（列表第一个），non-tty 直接返回 default。
- 联级后果：用户跑 `harness archive`（无参）期望 archive current_requirement (bugfix-2)，CLI 按字典序 / 文件 mtime 取列表第一个 (bugfix-3) 当 default，用户按 enter 接受，bugfix-3 被错移走。

## 路由决策

- **路由方向 = executing 直接修**（不需要 requirement_review / planning 重审）。
- **理由**：3 个根因都在 CLI 层 / helper 层，定位精确到函数 + 行号，修复范围有限（≤ 4 个函数 + 1 个模板 + 1 个新测试文件），不涉及角色文件 / 工作流模型变更。

## 修复方案（交付给 executing）

### 修复 1（缺陷 1）
1. `workflow_next` 入口加分支：若 `runtime.current_regression` 非空，调用新 helper `_resolve_regression_route(root, regression_id) -> str | None`，命中则把 `next_stage` 设为路由值（覆盖默认 sequence + 1），并清空 `current_regression`（消费完）。
2. `_resolve_regression_route`：
   - 复用 `_locate_regression_dir(root, reg_id, language)` 找目录；
   - 读 `decision.md`，优先解析 yaml frontmatter `route_to: <stage>`；
   - fallback：正则扫文本 `路由\s*[:：=]\s*(\w+)` / `harness next\s*[→\->\s]+(\w+)`；
   - 返回值校验在合法 stage 列表内（WORKFLOW_SEQUENCE ∪ BUGFIX_SEQUENCE），否则返回 None。
3. `regression-decision.md.tmpl` 头部加 yaml frontmatter 占位：
   ```yaml
   ---
   route_to: ""  # planning / executing / testing / acceptance / done / requirement_review / 留空走默认
   ---
   ```

### 修复 2（缺陷 2）
1. `enter_workflow(req_id)` 在 `runtime["current_requirement"] = req_id` 之后**显式重设** `operation_type` + `operation_target`：按 `req_id` 前缀（`bugfix-` → bugfix；`sug-` → suggestion；其他 → requirement）。
2. `load_requirement_runtime` 的懒回填把"残留值与 current_requirement 前缀**不一致**"也作为触发条件：若 `operation_type == "requirement"` 但 `current_requirement.startswith("bugfix-")`，强制改写为 "bugfix"。这样手工编辑 runtime.yaml 后也自愈。

### 修复 3（缺陷 3）
1. `cli.py` archive 分支：从 runtime 读 `current_requirement` 当作 `preselect`，传给 `prompt_requirement_selection`。
2. （可选加固）若 `current_requirement` 不在 done 列表中，stderr 提示用户："current_requirement {id} 当前 stage != done，archive 默认改为列表首个"。

### 测试清单
- 新建 `tests/test_state_sync_invariants.py`，覆盖：
  1. `test_next_consumes_regression_route_planning`：mock req + reg + decision.md 含 frontmatter `route_to: planning` → `workflow_next` → runtime.stage = planning + state yaml.stage = planning + current_regression 清空。
  2. `test_next_consumes_regression_route_text_marker`：decision.md 无 frontmatter，含文本 "路由：planning" → 同上断言。
  3. `test_runtime_stage_synced_to_bugfix_yaml_after_enter`：先 seed runtime（operation_type=requirement，current=req-x），再 `enter_workflow(root, "bugfix-7")`，再 `workflow_next` → bugfix yaml 必须从 regression 推进到 executing（不再写到 requirements 子目录）。
  4. `test_archive_selects_current_requirement_by_default`：mock 多个 done 候选（含 current=bugfix-2 + 干扰 bugfix-3），CLI archive non-tty → archive 的是 bugfix-2 不是 bugfix-3。

## Required Inputs
- 无需人工额外输入。所有证据已闭环（源码行号 + 用户活证）。

## Routing Direction
- [x] **Real issue → proceed to fix（路由 = executing 直接修）**
- [ ] False positive → revert to previous stage
