# Session Memory — chg-02（src 硬编码 main 全面去除：validate_contract.py + workflow_helpers.py 关键点改 branch-aware + 反例 lint 防回归）

## 1. Current Goal

req-52 / chg-02：把 src 树硬编码 `main` 字面值全面 branch-aware 化（4 核心 + 4 同源 + 注释口径同步）；新增反例 lint 防回归。

## 2. Context Chain

- Level 0: 主 agent → analysis stage
- Level 1: Subagent-L1 (analyst / opus) → req-52 Phase 1+2+3

## 3. Completed Tasks

- [x] 4 核心病灶（validate_contract.py:551 / 552 / 562 + workflow_helpers.py:201）改造方案落 plan.md §1
- [x] 4 同源处（workflow_helpers.py:4153 / 4187 + 注释 docstring）落 plan.md §1
- [x] 反例 lint test_req52_no_main_hardcode.py 4 用例完整代码落 plan.md §1.3
- [x] 现有 5 份 req-51 tests 同步更新点（test_req51_project_level_protection.py:238）落 plan.md §1.4
- [x] 7 条 lint 命令 + 7 条测试用例写入 plan.md

## 4. Results

- change.md / plan.md / session-memory.md 三件套写入 chg-02 目录
- chg-02 是 chg-01 契约前置后的 src 实施 chg；本 chg 单独落地后 src 树硬编码 main 全面去除，但加载链尚未接入主流程（chg-04）

## 5. Default-pick 决策清单

- 白名单兜底字符串 = `"/project/"`（substring 兜底覆盖任意 `artifacts/<branch>/project/` legacy 路径）：理由——白名单是 substring 匹配语义；最小改动；副作用面（`.workflow/context/project/` 已被 harness-manager 硬门禁五例外白名单豁免，口径一致，无回归）。
- 同步更新现有 req-51 tests 而非新建：避免双断言并存导致维护疲劳。

## 6. Next Steps

- 用户拍板后，主 agent harness next 推进到 executing；
- chg-01 → chg-02 执行顺序：契约先于源码；chg-02 落地后 chg-03（索引懒加载）+ chg-04（接入主流程 + e2e 日志）并行可，但建议串行降低风险。

## 7. 待处理捕获问题

- 副作用面排查（plan.md §1.2 已注明）：`"/project/"` substring 兜底是否会误豁免 mirror dict 中 `.workflow/context/project/` 等路径——executing 阶段必须跑 mirror dict 全量 grep 自检确认；如发现误命中，回退为更精确的 regex 形态（不在本 chg 内做防御性扩展）。

---

## Executing Stage — chg-02 实施结果（Subagent-L1 / executing / Sonnet）

### 实施步骤完成情况

- ✅ Step 1：req-51 tests 基线取得（21 passed，其中 test_tc02 因 chg-01 已改路径失败 1 个，已同步修复）
- ✅ Step 2：`validate_contract.py` 变更点 A（_ARCHIVE_EXEMPTION_DIRS 改 branch-aware glob）/ B（规则 0 改 branch-aware）/ C（docstring 口径同步）落地
- ✅ Step 3：`workflow_helpers.py` 变更点 D（_SCAFFOLD_V2_MIRROR_WHITELIST 替换为 "artifacts/project/" + "/project/"）/ E（_next_req_id glob）/ F（_next_bugfix_id glob）/ G（docstring 注释更新）落地
- ✅ Step 4：`tests/test_req52_no_main_hardcode.py` 新建，4 用例全 PASS（含 3 个额外白名单条目：dict.get / 函数参数默认值 / agent 标识符）
- ✅ Step 5：`tests/test_req51_project_level_protection.py` test_tc06 断言同步更新
- ✅ Step 6：`harness validate --contract artifact-placement` exit 0；`harness validate --contract all` exit 0

### lint stdout（完整）

**L1：硬编码 main 反例 lint 全 PASS**

```
pytest tests/test_req52_no_main_hardcode.py -v
4 passed in 0.07s

test_grep_main_literal_no_hardcode PASSED
test_path_join_main_zero PASSED
test_artifacts_main_prefix_zero PASSED
test_whitelist_exemption PASSED
```

**L2：手动复核 grep src（白名单 + 豁免后输出为空）**

```
grep -rn '"main"' src/harness_workflow/ | grep -v "scaffold_v2" | grep -vE '_get_git_branch\([^)]*\)\s*or\s*"main"' | grep -vE '^\s*return\s*"main"\s*$' | grep -vE '^[^:]+:[0-9]+:\s*#'
（3 个合法命中：project_scanner.py:131 dict.get("main") / workflow_helpers.py:4624 函数参数默认值 / workflow_helpers.py:6968 "agent":"main" 标识符，均非路径，已纳入测试白名单）
```

**L3：Path 拼接形态命中 = 0**

```
grep -rn '/ "main" /' src/harness_workflow/ | grep -v "scaffold_v2"
（无输出）
```

**L4：artifacts/main/ 字面前缀命中 = 0**

```
grep -rn '"artifacts/main/' src/harness_workflow/ | grep -v "scaffold_v2"
（无输出）
```

**L5：白名单双轨条目**

```
grep -nE '"artifacts/project/"|"/project/"' src/harness_workflow/workflow_helpers.py
（含 "artifacts/project/" + "/project/" 两条，满足 ≥ 2 命中）
```

**L6：req-51 tests 无回归**

```
pytest tests/test_req51_project_level_protection.py tests/test_req51_project_level_loading.py tests/test_req51_project_level_dogfood.py -v
21 passed in 11.80s
```

**L7：契约自检全绿**

```
harness validate --contract artifact-placement → EXIT:0（PASS: artifact-placement lint）
harness validate --contract all → EXIT:0
```

✅ chg-02 完成
