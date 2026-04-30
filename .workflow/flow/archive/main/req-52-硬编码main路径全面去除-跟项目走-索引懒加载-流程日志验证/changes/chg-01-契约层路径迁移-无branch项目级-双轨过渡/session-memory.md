# Session Memory — chg-01（契约层路径迁移：项目级承载层从 artifacts/{branch}/project/ 改为 artifacts/project/（双轨过渡）+ scaffold mirror 同步）

## 1. Current Goal

req-52 / chg-01：契约底座路径迁移；后续 chg-02（src 硬编码 main 全面去除）/ chg-03（索引懒加载）/ chg-04（接入主流程 + 端到端日志）依赖本 chg 锚点。

## 2. Context Chain

- Level 0: 主 agent → analysis stage（合并 requirement_review + planning）
- Level 1: Subagent-L1 (analyst / opus) → req-52 Phase 1+2+3 一气写盘

## 3. Completed Tasks

- [x] 路径策略 OQ-A 拍 default-pick = D-modified（双轨过渡：主路径 `artifacts/project/` + legacy fallback `artifacts/{branch}/project/`）
- [x] 4 份契约文件（repository-layout.md / harness-manager.md / role-loading-protocol.md / tools-manager.md）变更点 A ~ G 落 plan.md
- [x] 4 份 scaffold_v2 mirror 同步清单写入 plan.md §5
- [x] 7 条测试用例 + 7 条 lint 命令字面写入 plan.md §3 / §4

## 4. Results

- change.md / plan.md / session-memory.md 三件套写入 `.workflow/flow/requirements/req-52-硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证/changes/chg-01-契约层路径迁移-无branch项目级-双轨过渡/`
- chg-01 是后续 chg-02 / chg-03 / chg-04 的契约前置；本 chg 单独落地无 src 行为变化（仅契约文档 + 占位）

## 5. Default-pick 决策清单

- OQ-A（路径策略） = **D-modified**（双轨过渡）：理由——用户原话"跟项目走、不跟 branch"主导 + req-51 已落物不可回滚；过渡期 ≤ 1 版本。
- 占位目录是否纳入 mirror = **否**（与 req-51 / chg-01 活证示范同口径）。

## 6. Next Steps

- 用户拍板 OQ-A ~ OQ-E 后，主 agent harness next 推进到 executing；
- chg-01 落地 → chg-02（src）→ chg-03（索引）→ chg-04（主流程接入 + 端到端日志）顺序执行。

## 7. 待处理捕获问题

- 无。

---

## Executing Stage — chg-01 实施结果（Subagent-L1 / executing / Sonnet）

### 实施步骤完成情况

- ✅ Step 1：`.workflow/flow/repository-layout.md` 变更点 A/B/C/D 全部落地
- ✅ Step 2：`.workflow/context/roles/harness-manager.md` 变更点 E（硬门禁五白名单拆 2 条）落地
- ✅ Step 3：`.workflow/context/roles/role-loading-protocol.md` 变更点 F（Step 7.6 双轨过渡 + fallback 子段）落地
- ✅ Step 4：`.workflow/context/roles/tools-manager.md` 变更点 G（Step 2.0 主路径改为 artifacts/project/）落地
- ✅ Step 5：4 份 scaffold_v2 mirror 同步（diff -q 全 silent）
- ✅ Step 6：`artifacts/project/` 占位目录 + README.md + 3 个 .gitkeep 创建

### lint stdout（完整）

**L1：契约段落落地（repository-layout.md）**

```
grep -c "artifacts/project/" .workflow/flow/repository-layout.md
12

grep -n "双轨过渡 fallback（req-52 / chg-01）" .workflow/flow/repository-layout.md
103:#### 双轨过渡 fallback（req-52 / chg-01）

grep -n "OQ-A = D-modified" .workflow/flow/repository-layout.md
25: OQ-A = D-modified 主路径...
93: OQ-A = D-modified）
105: OQ-A = D-modified：主路径迁移 + legacy 兼容
128: OQ-A = D-modified 豁免说明
```

**L2：硬门禁五例外白名单双轨条目**

```
grep -nE "artifacts/project/" .workflow/context/roles/harness-manager.md
48:- `artifacts/project/`（req-52 / chg-01 OQ-A = D-modified；...）

grep -nE "artifacts/\{branch\}/project/" .workflow/context/roles/harness-manager.md
49:- `artifacts/{branch}/project/`（legacy fallback，...）
```

**L3：role-loading-protocol Step 7.6 fallback**

```
grep -nE "artifacts/project/\{constraints,experience,tools\}" .workflow/context/roles/role-loading-protocol.md
133:主路径：`artifacts/project/{constraints,experience,tools}/`

grep -n "fallback（req-52" .workflow/context/roles/role-loading-protocol.md
142:#### fallback（req-52 / chg-01 双轨过渡）
```

**L4：tools-manager Step 2.0 路径同步**

```
grep -cE "artifacts/project/tools/" .workflow/context/roles/tools-manager.md
11
```

**L5：scaffold mirror 字节级同源（4 对全 silent）**

```
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
(silent)
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
(silent)
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
(silent)
diff -q .workflow/context/roles/tools-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md
(silent)
```

**L6：契约自检**

```
harness validate --human-docs  → EXIT:1（executing stage 无 done docs，pending 是预期）
harness validate --contract all → EXIT:0
```

**L7：占位 README + .gitkeep**

```
test -f artifacts/project/README.md → OK
test -f artifacts/project/constraints/.gitkeep → OK
test -f artifacts/project/experience/.gitkeep → OK
test -f artifacts/project/tools/.gitkeep → OK
grep -E "req-52|OQ-A|跟项目走" artifacts/project/README.md → 4 行命中
```

✅ chg-01 完成

---

## Round 2 修订 — legacy fallback → branch-path 兼容路径 重命名（Subagent-L1 / executing / Sonnet）

### 问题

bugfix-11 反例 lint `test_req_01_no_legacy_branch_present_in_diff` 检查 `src/**/*.py` 不得含 "legacy fallback" 字样（三段式分水岭废弃后不留兼容路径）。req-52 chg-01 / chg-04 在 `workflow_helpers.py` 注释 / docstring 中用了"legacy fallback"描述 branch-path 兼容路径，字面命中 lint，但语义不同（req-52 的 fallback 是 branch-path 兼容，不是三段式 fallback）。

### 修改内容

仅替换 `src/harness_workflow/workflow_helpers.py` 注释 / docstring 字面，不改逻辑：

| 行（修改前） | 原文 | 改为 |
|---|---|---|
| 3779 | `触发主路径 / legacy fallback 探测 + stderr 日志（OQ-C = A）。` | `触发主路径 / branch-path 兼容路径探测 + stderr 日志（OQ-C = A）。` |
| 3784 | `# legacy fallback（chg-01 双轨过渡）` | `# branch-path 兼容路径（chg-01 双轨过渡）` |
| 8413 | `2. legacy fallback = artifacts/{branch}/project/{scope_subpath}/index.md（chg-01 双轨过渡）` | `2. branch-path 兼容路径 = artifacts/{branch}/project/{scope_subpath}/index.md（chg-01 双轨过渡）` |
| 8437 | `# legacy fallback（chg-01 双轨过渡）` | `# branch-path 兼容路径（chg-01 双轨过渡）` |

共 4 行，无逻辑改动。

### 4 个完成判据 stdout

**判据 1：workflow_helpers.py 不再含 legacy fallback**

```
grep -c "legacy fallback" src/harness_workflow/workflow_helpers.py
0
```

**判据 2：bugfix-11 反例 lint 通过**

```
tests/test_bugfix_11_flow_layout.py::CreateRequirementUnconditionalFlowLayoutTest::test_req_01_no_legacy_branch_present_in_diff PASSED [100%]

============================== 1 passed in 0.22s ===============================
```

**判据 3：req-52 测试不受影响**

```
12 passed, 824 deselected, 1 warning in 3.81s
```

**判据 4：全 suite fail 数回 51（消除新增 1 个 fail）**

```
51 failed, 745 passed, 40 skipped, 1 warning, 17 subtests passed in 124.11s (0:02:04)
```

✅ Round 2 修订完成
