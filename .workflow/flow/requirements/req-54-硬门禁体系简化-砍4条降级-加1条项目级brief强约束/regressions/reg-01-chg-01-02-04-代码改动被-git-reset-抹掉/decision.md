---
id: reg-01
title: "chg-01/02/04（代码改动被 git reset 抹掉）"
parent_requirement: req-55（gstack 和 harness 工作流融合（开发承载分支 harness-gstack））
created_at: 2026-05-08
operation_type: regression
stage: regression
route_to: "confirm"
---

> **路径错位说明**：本 reg-01 被 harness CLI 挂在 req-54（硬门禁体系简化-砍 4 条降级-加 1 条项目级 brief 强约束） 下，是因为 runtime.yaml 已被 git reset 回 req-54 done 状态，CLI 视角看不到 req-55 active。**实际诊断对象是 req-55（gstack 和 harness 工作流融合（开发承载分支 harness-gstack））**；后续修复路由也以 req-55 为承载需求。

## 现场摘要

### 1. 文件系统现状（独立核查命令 + 数字一致）

| 项 | 状态 | 命令 / 数字 |
|---|---|---|
| `src/harness_workflow/workflow_helpers.py` GSTACK_SKILLS_ROOT / `_install_gstack_skills` | 丢失 | `grep -c GSTACK_SKILLS_ROOT` = 0 |
| `.workflow/context/roles/analyst.md` Step A1.5 三段（触发协议 / adapter / fallback） | 丢失 | `grep -c "Step A1.5"` = 0 |
| `.workflow/state/runtime.yaml` `gstack_status` schema | 丢失 | `grep -c gstack_status` = 0；`stage_entered_at = 2026-04-30T11:16:37`（req-54 done 时点） |
| `README.md` "Third-party Vendored Skills" 节 | 丢失 | `grep -c 'Third-party.*[Vv]endored'` = 0 |
| `git ls-files --others --exclude-standard \| wc -l` 未跟踪文件 | 261 | 与 reset --hard 抹除 tracked 改动 + 保留 untracked 新文件 行为一致 |
| `find src/harness_workflow/assets/gstack-skills/ -maxdepth 2 -name SKILL.md \| wc -l` | 46 | vendor 副本完整保留（untracked，不受 reset 影响） |
| `.workflow/flow/requirements/req-55-.../`（含 requirement.md + 4 chg + test-report + acceptance/checklist + session-memory） | 保留 | untracked，全套完整 |
| `.workflow/state/requirements/req-55-...yaml` | 保留 | untracked |
| `artifacts/project/experience/roles/analyst.md`（chg-05 retro 模板预埋） | 保留 | untracked |
| `src/harness_workflow/assets/scaffold_v2/.workflow/context/integrations/gstack/` | 保留 | untracked |

### 2. runtime.yaml 现状

```yaml
operation_type: "requirement"
operation_target: "req-54"
current_requirement: "req-54"            # 应该是 req-55
stage: "done"                             # req-54 done 的旧状态被恢复
stage_entered_at: "2026-04-30T11:16:37"   # req-54 done 时点（不是 req-55 done 的 2026-05-08）
current_regression: "reg-01"              # CLI 刚写入
active_requirements:
  - req-54                                # req-55 已从列表消失
```

`git diff HEAD .workflow/state/runtime.yaml` 仅显示 `current_regression` / `current_regression_title` 两行新增——其余字段（含 stage_entered_at）已与 HEAD（f8d15fd = req-54 done snapshot）一致，进一步证明 reset 把 runtime.yaml 也回滚到了 req-54 状态。

### 3. reflog 决定性证据（独立核查 `git reflog` 输出）

```
f8d15fd HEAD@{0}: reset: moving to f8d15fde9cd20ce80e7e6f0d296438827e768d1f   ← 1778206595 = 2026-05-08 10:16:35 CST
f8d15fd HEAD@{1}: reset: moving to f8d15fde9cd20ce80e7e6f0d296438827e768d1f   ← 1778206594 = 2026-05-08 10:16:34 CST（同秒 4 次）
f8d15fd HEAD@{2}: reset: moving to f8d15fde9cd20ce80e7e6f0d296438827e768d1f
f8d15fd HEAD@{3}: reset: moving to f8d15fde9cd20ce80e7e6f0d296438827e768d1f
f8d15fd HEAD@{4}: reset: moving to HEAD                                       ← 1778166131 = 2026-05-07 23:02:11 CST
f8d15fd HEAD@{5}: reset: moving to HEAD                                       ← 1778163239 = 2026-05-07 22:13:59 CST
f8d15fd HEAD@{6}: checkout: moving from main to harness-gstack                ← 1778142569 = 2026-05-07 16:29:29 CST
```

**决定性副产物**：`.git/ORIG_HEAD` 时间戳 = `May 7 22:13`（与 `HEAD@{5}` reset 时刻完全一致）。`git reset` 命令会自动写 `ORIG_HEAD`；`git revert --abort` / `git checkout` 不会写 `ORIG_HEAD`。**reset 是真实的 `git reset` 命令**，不是其它命令的副作用。

## 根因诊断

### 根因 1：触发源 = 外部 `git reset --hard` 命令（非 harness CLI 内部）

**否定线索**：

1. **harness CLI 代码层无 `git reset` 调用**。`grep -rn "subprocess.*reset\|reset.*--hard" src/harness_workflow/ --include="*.py"` 仅命中 `decision_log.py` / `validate_contract.py` 把 `reset --hard` 当**禁止字符串模式**做 lint，没有任何执行路径调用 `git reset`。
2. **archive 的 revert dry-run 不会产生 `reset: moving to HEAD`**。`workflow_helpers.py:6420 _revert_dry_run_self_check` 只跑 `git revert --no-commit -n <sha>` + `git checkout -- .` + `git revert --abort`——其中 `git checkout -- .` 会写 `.git/index` 但**不**会写 ORIG_HEAD；`revert --abort` 在 reflog 体现为 `revert: aborting`，不是 `reset: moving to HEAD`。
3. **`.git/hooks/` 全部是 `*.sample`**，无自定义 hook。

**肯定线索**：

1. `.git/ORIG_HEAD` 内容 = `f8d15fde9cd20ce80e7e6f0d296438827e768d1f`，时间戳 = 第 1 次 `reset: moving to HEAD` 时刻——典型 `git reset --hard HEAD` 副产物。
2. 4 次 reset 集中在 `1778206594-595`（2026-05-08 10:16:34-35 CST，1 秒内）——与 `/harness-archive` 命令前置流程"用户尝试清理工作树以满足 archive 前置条件"的人为操作时序吻合。
3. reflog 历史显示**早期 archive 周期 HEAD@{14}-HEAD@{32} 全是同样模式的 `reset: moving to <sha>`**——这是**重复出现的人/工作流模式**，不是本次孤立事件。

**结论**：**触发源是某 agent（包括用户主对话 / subagent / harness-manager 派发的 sandbox 内进程）通过 Bash 调用 `git reset --hard <sha>`**，最可能位置是：
- `/harness-archive` revert dry-run FAIL 后，用户或 agent 试图"清掉所有未提交改动重来"；
- chg-01 / chg-04 实施期间（22:13、23:02 两次）某 subagent 出错后用 `git reset --hard HEAD` 清理失败的写盘，无意中抹掉了同会话内已写到 tracked 路径的改动（兄弟改动是同一个 commit 状态机内）。

### 根因 2：影响范围

被 `git reset --hard` 抹掉的是所有 **tracked** 文件的工作区改动；**untracked** 新增文件不受影响。这恰好命中：

| 改动类型 | 路径例 | 是否丢失 |
|---|---|---|
| **修改 tracked 文件** | `src/harness_workflow/workflow_helpers.py`（新增 GSTACK_SKILLS_ROOT/_install_gstack_skills 函数）；`.workflow/context/roles/analyst.md`（注入 Step A1.5 三段）；`.workflow/state/runtime.yaml`（新增 gstack_status schema）；`README.md`（新增 vendored skills 节）；`src/harness_workflow/tools/harness_install.py`（新增 --force-gstack flag）；scaffold_v2 mirror 内已存在的 analyst.md / runtime.yaml | **全部丢失** |
| **新增 untracked 文件** | `src/harness_workflow/assets/gstack-skills/**`（46 SKILL.md + _shared）；`scripts/vendor-gstack.sh`；`tests/installer/test_gstack_skills_push.py`；`tests/integration/test_install_pushes_gstack.py`；`.workflow/context/integrations/gstack/{role-command-map.yaml,README.md}`；`.workflow/flow/requirements/req-55-...`（req 元数据全套）；`artifacts/project/experience/roles/analyst.md`；`scaffold_v2/.workflow/context/integrations/gstack/`；`scaffold_v2/artifacts/project/...` | **全部保留** |

### 根因 3：恢复可能性评估

- **dangling commit 不含丢失代码**：`git fsck --lost-found` 列出大量 dangling commit，但全部是 archive 周期内的 reset 残留——这些 commit 早于 req-55 启动；**req-55 期间没有产生过含 GSTACK_SKILLS_ROOT 的中间 commit**（chg-01/02/04 实施过程都直接改 working tree，未阶段性 commit）→ **从 git 对象库无法恢复任何丢失的代码改动**。
- **session-memory 不含完整代码片段**：`grep` chg-01/chg-02/chg-04 三份 session-memory.md 均只记录"步骤完成 ✓ DONE + 落点路径"，没有把改动 patch / 完整函数体写进去 → **session-memory 无法用来照搬重做**。
- **change.md / plan.md 含完整 SOP / 落点 / AC 描述**：可作为重做时的契约依据（功能粒度等价），但**不是**逐行代码 → 重做需要 executing 角色按 plan.md 重新实现。

**恢复结论**：**tracked 改动彻底丢失，无法从 git 历史恢复**；只能依据 plan.md / change.md / test-report.md 的契约 + 完整保留的 untracked 资产（46 SKILL.md vendor 副本、新增测试用例、scaffold mirror 新增子树等）**重做** chg-01/chg-02/chg-04 的 tracked 部分。chg-05 因为只产出 retro 模板段（落 untracked 路径 `artifacts/project/experience/roles/analyst.md`）**未受影响**。

## 影响评估

| 维度 | 影响 | 说明 |
|---|---|---|
| req-55 整体进度 | **回退到 chg 实施前 zero state** | tracked 改动全没；untracked 新增完整保留——相当于"加法部分都在，乘法部分都丢了" |
| chg-01（gstack 内置发布契约） | 部分丢失 | install 推送逻辑（`workflow_helpers.py` GSTACK_SKILLS_ROOT/_install_gstack_skills 函数 + `harness_install.py` --force-gstack flag）丢失；vendor 副本 + vendor 脚本 + 测试用例完整保留 |
| chg-02（analyst-office-hours 强映射） | 部分丢失 | `analyst.md` Step A1.5 三段丢失；`role-command-map.yaml` + `README.md`（新增文件）保留 |
| chg-04（scaffold_v2 镜像） | 部分丢失 | scaffold_v2 内的 analyst.md / runtime.yaml mirror 改动丢失；新增的 `scaffold_v2/.workflow/context/integrations/gstack/` 子树保留 |
| chg-05（dogfood 活证） | **未受影响** | 只产出新增 untracked 文件（retro 模板段），全保留 |
| test-report / acceptance/checklist | 已落地（PASS），但**已与现实脱节** | testing/acceptance 是 reset 之前跑的，报告记录的"15/15 PASS / 6 PASS+2 CONDITIONAL"基于已丢失的代码——**重做后必须重跑 testing 和 acceptance** |
| runtime.yaml 状态 | 回退到 req-54 done | `current_requirement = req-54`；`active_requirements = [req-54]`；req-55 在 CLI 视角不存在 |
| 用户已投入工作量 | 6+ 次轮深谈 + 4 chg 实施 + testing + acceptance 全套 | 元数据 / 契约 / 设计完全保留；**重做工作量 ≈ tracked 改动那部分的 executing**（粗估 1~2 人时） |

## 路由决策

- **路由**：**confirm**（真问题，必须修复——3 chg 的 tracked 改动确认丢失，且测试 / 验收报告已与现实脱节）
- **子路由**：**a + 其他组合**（**先修 runtime → 再开 chg-06 修复包 → testing/acceptance 重跑 → archive 重启**）

### 决策理由

1. **不能选 reject**：6 项独立核查命令全部命中"丢失"，影响是真实且严重的；rejection 会让用户带着假装通过的 acceptance 报告进 done / archive。
2. **不能选子路由 b（开 req-56 防御机制）单独**：防御机制（如 archive 前自动 stash、Bash hook 警告 reset --hard、subagent 禁用 git reset 类命令等）是**第二优先**——必须先修复本次丢失，再考虑长期防御；防御本身仍可作为独立 sug / 后续 req（不阻塞本路由）。
3. **不能选子路由 c（不开新 chg 直接重做）**：违反 req-41 后的 chg 拆分契约——req-55 已 acceptance 通过的 4 个 chg 是历史 snapshot，重做 tracked 部分应作为 chg-06（fix 性质）登记，便于审计 + commit message + archive 索引追溯本事故。
4. **必须先修 runtime**：当前 CLI 视角看不到 req-55，任何 `harness next` / `harness change` 调用都会路由到 req-54——重做 chg-06 必须先把 runtime.yaml 改回 req-55 active 状态，否则新工件会被错放到 req-54 下（已发生：本 reg-01 就被错挂）。
5. **必须重跑 testing/acceptance**：现有 test-report.md / acceptance/checklist.md 是基于已丢失代码的报告；chg-06 落地后必须重跑独立测试（pytest 15/15 / mirror diff / contract lint）+ 重新 acceptance，否则 archive 时会带入假证据。

### 后续动作清单（主 agent 应做什么，按顺序）

1. **修 runtime.yaml**：把 `current_requirement` 改回 `req-55-gstack-和-harness-工作流融合-开发承载分支-harness-gstack`；`stage` 改回 `acceptance`（或 `executing`，取决于决定从哪个阶段重启）；`active_requirements` 加回 `req-55`；`current_regression` 改回空（reg-01 处理完后）；`stage_entered_at` 重置为当前时刻。
2. **把 reg-01 工件搬到 req-55 下**：`mv .workflow/flow/requirements/req-54-.../regressions/ .workflow/flow/requirements/req-55-.../regressions/`（CLI 已挂错位置，需手工纠正；或在 chg-06 落地后归档时统一处理）。
3. **执行 `harness regression --confirm` 接续路由**：路由目标 = chg / req-55 内执行重做。
4. **开 chg-06（chg-01/02/04 tracked 改动重做）**：在 req-55 下登记，按既有 plan.md 重新执行：
   - chg-06 step 1：`workflow_helpers.py` 重新加 GSTACK_SKILLS_ROOT + `_install_gstack_skills` 函数（按 chg-01 plan.md SOP；vendor 副本路径已就绪，函数实现可参考 chg-01 change.md L23 Key Deliverable #4）；
   - chg-06 step 2：`harness_install.py` 重新加 `--force-gstack` flag 接线；
   - chg-06 step 3：`analyst.md` 重新注入 Step A1.5 三段（触发协议 / adapter / fallback）；
   - chg-06 step 4：`runtime.yaml` 重新加 `gstack_status` 4 子字段 schema + scaffold_v2/.workflow/state/runtime.yaml mirror；
   - chg-06 step 5：`README.md` 重新加 "Third-party Vendored Skills" 节；
   - chg-06 step 6：scaffold_v2 mirror 同步 analyst.md / runtime.yaml；
   - chg-06 step 7：重跑 `pytest tests/installer/test_gstack_skills_push.py tests/integration/test_install_pushes_gstack.py` 期望 15/15。
5. **重跑 testing**：覆盖 7 个测试维度，重新落地 test-report.md（覆盖原 test-report 或新增 round-2 段）。
6. **重跑 acceptance**：重新 8 AC 校验，更新 checklist.md。
7. **重启 archive 流程**：`harness archive req-55 --skip-revert-check`（如重新出现冲突，使用 escape hatch）；或先排查 revert 冲突来源、再走默认 archive。
8. **后续 sug**：开 sug 条目"`git reset --hard` 防御机制"——评估在 base-role 加硬门禁/在 hook 拦截/在 CLI 派发 subagent 时禁止 Bash 跑 `git reset` 类命令；不阻塞本路由。

### 不在本路由内的项

- 长期防御机制（防止再次发生 git reset 抹改动）→ 单独 sug，由后续 req-56+ 评估。
- archive 内 revert dry-run 流程改造（如改用 `git stash` 替代 `git checkout -- .`）→ 单独 sug；本事故不是 archive 内 revert 引发，但用户经验"archive 失败 → 反射性跑 git reset"是普遍模式，可作为 sug 来源。
- chg-05 deferred 合约（真活证由 req-56 兑现）→ 不变，不受本事故影响。

## 结论

- **路由**：**confirm**
- **承载需求**：**req-55**（gstack 和 harness 工作流融合（开发承载分支 harness-gstack））
- **推荐执行步骤**：先修 `runtime.yaml` 回 req-55 + 把本 reg-01 工件搬到 req-55 下 → `harness regression --confirm` → 在 req-55 下开 chg-06（chg-01/02/04 tracked 改动重做） → executing → testing 重跑 → acceptance 重跑 → archive 重启 → 单独开 sug（git reset 防御机制）。

- [x] Routed
- [ ] Closed（待 chg-06 落地 + testing/acceptance 重跑后由主 agent 关闭）
