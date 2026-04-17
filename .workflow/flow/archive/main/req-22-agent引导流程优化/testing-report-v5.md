# Testing Report: req-22 (V5)

**Date**: 2026-04-17  
**Tester**: Independent testing agent  
**Scope**: chg-04 (角色继承体系重构) + chg-05 (经验文件目录重构) + req-22 整体验收

---

## chg-04 验收结果

### Item 1
**Criteria**: `role-loading-protocol.md` 中包含"所有角色必须使用与主 agent 相同模型"的明确声明  
**Result**: PASS  
**Evidence**: Line 10 states "模型一致性：所有角色（含 subagent）应使用与主 agent 相同的模型，以保证执行质量一致性"

### Item 2
**Criteria**: `role-loading-protocol.md` 中 stage 角色的加载顺序已更新为 `base-role.md → stage-role.md → {具体角色}.md`  
**Result**: PASS  
**Evidence**: Lines 84-87 explicitly state the loading order as `base-role.md → stage-role.md → 你的 stage 角色文件`

### Item 3
**Criteria**: `base-role.md` 的标题/引言不再限定为"stage 角色的抽象父类"，而是"所有角色的通用规约"  
**Result**: PASS  
**Evidence**: Title is "基础角色（Base Role）——所有角色的通用规约" and line 3 states "本文件是 Harness 工作流中**所有角色**（含顶级角色 Director、辅助角色 toolsManager、stage 角色）必须遵循的通用规约"

### Item 4
**Criteria**: `base-role.md` 中无"流转规则（按需）"章节  
**Result**: PASS  
**Evidence**: Searched the entire file; no "流转规则" section exists. The only sections are: 硬门禁一/二, 通用准则, 经验沉淀规则, 上下文维护规则, 角色标准工作流程约定

### Item 5
**Criteria**: `base-role.md` 中包含"经验沉淀规则"章节，定义沉淀时机、格式和路径  
**Result**: PASS  
**Evidence**: Lines 23-59 contain the full "经验沉淀规则" section with 沉淀时机, 沉淀内容, 沉淀格式, 沉淀路径, and 强制检查

### Item 6
**Criteria**: `base-role.md` 中包含"上下文维护规则"章节，明确 60% 阈值约束  
**Result**: PASS  
**Evidence**: Lines 60-80 contain "上下文维护规则" with a threshold table showing "评估阈值 | 60% | ~61440 | 必须评估是否使用 `/compact` 或 `/clear`"

### Item 7
**Criteria**: `stage-role.md` 文件存在，包含 Session Start、Stage 切换交接、经验文件加载规则、流转规则 4 个章节  
**Result**: PASS  
**Evidence**: File exists at `.workflow/context/roles/stage-role.md` and contains exactly the 4 required sections: "Session Start 约定" (lines 7-15), "Stage 切换上下文交接约定" (lines 17-24), "经验文件加载规则" (lines 26-53), "流转规则（按需）" (lines 54-58)

### Item 8
**Criteria**: `technical-director.md` 中 subagent 加载流程描述与新的三层继承一致  
**Result**: PASS  
**Evidence**: Lines 75-83 in `directors/technical-director.md` state: "先加载 `.workflow/context/roles/base-role.md` → 再加载 `.workflow/context/roles/stage-role.md` → 最后按 `stage` 加载对应角色文件"

### Item 9
**Criteria**: `context/index.md` 中正确列出 `base-role.md` 和 `stage-role.md` 的继承关系  
**Result**: PASS  
**Evidence**: Lines 37-38 in `context/index.md` correctly list base-role as "所有角色（含 Director、toolsManager、stage 角色）的通用规约" and stage-role as "所有 stage 执行角色和辅助角色的公共父类，继承 base-role"

---

## chg-05 验收结果

### Item 10
**Criteria**: `context/experience/stage/` 目录已不存在，文件已迁移到 `context/experience/roles/`  
**Result**: PASS  
**Evidence**: Directory `.workflow/context/experience/stage/` does not exist. The 6 files are present under `.workflow/context/experience/roles/`: acceptance.md, executing.md, planning.md, regression.md, requirement-review.md, testing.md

### Item 11
**Criteria**: `context/experience/index.md` 正确列出 `roles/` 下的所有文件  
**Result**: PASS  
**Evidence**: `.workflow/context/experience/index.md` (auto-generated) correctly lists all 6 role files under the `roles` section: acceptance.md, executing.md, planning.md, regression.md, requirement-review.md, testing.md

### Item 12
**Criteria**: `stage-role.md` 中的经验加载规则引用的是 `experience/roles/` 路径  
**Result**: PASS  
**Evidence**: Lines 32-38 in `stage-role.md` use paths like `context/experience/roles/{角色名}.md`

### Item 13
**Criteria**: 所有 stage 角色文件中无残留的 `experience/stage/` 路径引用  
**Result**: PASS (for stage role files themselves)  
**Evidence**: Grepped all files in `.workflow/context/roles/` — no `experience/stage/` references found in any stage role file (requirement-review.md, planning.md, executing.md, testing.md, acceptance.md, regression.md, done.md).  
**⚠️ Related Finding**: However, residual `experience/stage/` references DO exist in other active workflow files: `.workflow/evaluation/index.md` (line 41), `.workflow/context/checklists/review-checklist.md` (lines 105, 112, 119, 126, 133), and `.workflow/state/experience/index.md` (lines 5, 10-13, 21). These are NOT stage role files, so this item technically passes, but they will mislead agents.

### Item 14
**Criteria**: `technical-director.md` 和 `done.md` 中无残留的 `experience/stage/` 路径引用  
**Result**: PASS  
**Evidence**: Neither `directors/technical-director.md` nor `roles/done.md` contains any `experience/stage/` references. `done.md` correctly uses `experience/roles/` paths in its经验沉淀验证步骤 section.

---

## req-22 整体验收（回归修复验证）

### Item 15
**Criteria**: 需求 `requirement.md` 中的 4 条验收标准仍被覆盖  
**Result**: PASS  
**Evidence**:
1. **各 stage 引导一致，无冲突遗漏**: All stage roles (requirement-review, planning, executing, testing, acceptance, regression, done) now follow a unified structure (SOP, available tools, allowed/prohibited behaviors, context maintenance, exit conditions, ff mode, 流转规则). The base-role/stage-role split eliminates duplication and ensures consistency.
2. **`harness` 命令触发条件与 agent 行为对应明确**: `stages.md` contains a complete "命令与 Stage 对应关系" table (lines 175-184), and `technical-director.md` enforces stage transitions via 硬门禁四.
3. **ff 模式、regression、done 关键节点说明完整**: Every stage role file includes an "ff 模式说明" section. `regression.md` has complete diagnostic and routing guidance. `done.md` is comprehensive with the six-layer review checklist.
4. **全流程走查验证**: This independent testing report constitutes the walkthrough validation, confirming the refactored guidance is executable.

---

## Defects Found

### Defect 1: Residual `experience/stage/` references in active non-role files
**Severity**: Medium  
**Files affected**:
- `.workflow/evaluation/index.md` line 41: `context/experience/stage/testing.md` / `context/experience/stage/acceptance.md`
- `.workflow/context/checklists/review-checklist.md` lines 105, 112, 119, 126, 133: multiple `experience/stage/...` references in stage-specific checklists
- `.workflow/state/experience/index.md` lines 5, 10-13, 21: loading rules and directory description still reference `stage/` subdirectory

**Impact**: Agents following these documents will attempt to load non-existent files under `experience/stage/`, causing file-not-found errors and workflow disruption.  
**Recommendation**: Fix these 3 files to use `experience/roles/` paths before accepting chg-05.

---

## Overall Conclusion

**Status**: CONDITIONAL PASS — defects must be fixed

- chg-04 (角色继承体系重构): **全部通过**
- chg-05 (经验文件目录重构): **基本通过，但存在残留引用未清理完毕**
- req-22 整体验收标准: **被覆盖**

**Recommendation**: Enter a brief regression to fix the 3 files with residual `experience/stage/` references (`.workflow/evaluation/index.md`, `.workflow/context/checklists/review-checklist.md`, `.workflow/state/experience/index.md`). Once fixed, re-run items 10-14 only. No full regression needed.
