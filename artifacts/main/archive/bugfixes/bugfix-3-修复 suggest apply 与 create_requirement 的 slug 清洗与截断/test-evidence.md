# Self Test Record

## Change
bugfix-3 · slug 清洗与截断修复

## Test Date
2026-04-20

## Test Summary

由独立 subagent（testing 角色）复核 bugfix-3：
1. 批判性评估开发者 5 条单测覆盖，补 4 条边界（反斜杠/Windows 非法字符、换行、幂等、无 frontmatter sug）到 `tests/test_slug_paths_extra.py`。
2. 在 `/tmp/harness-bugfix3-e2e-20260420-115447/` 真跑 4 个 E2E 场景（sug-08 apply、含 `/` requirement、长 title、含 `/` bugfix），全部用主仓 editable CLI（`pipx venvs/harness-workflow` Editable project location=主仓）。
3. 主仓全量 `python3 -m unittest discover tests`：180 tests / 1 failure（pre-existing `test_human_docs_checklist_for_req29`）/ 0 errors / 36 skipped，零新增回归。

## Validation Criteria 逐条核对

| # | bugfix.md 验收标准 | 结果 | 证据 |
|---|---|---|---|
| 1 | `harness requirement "含/的 标题"` 单级 `req-NN-<slug>/`，state yaml 同级 | PASS | E2E 场景 2：`req-02-含-斜杠-的-标题/` 单级；`.workflow/state/requirements/req-02-含-斜杠-的-标题.yaml` 单文件 |
| 2 | `harness suggest --apply sug-08` 单级 req + sug 搬 archive + frontmatter applied | PASS | E2E 场景 1：`req-01-清理-workflow-flow-archive-...-早/` 单级；原 `sug-08-*.md` 已离开 `suggestions/`，搬到 `suggestions/archive/`；归档后 frontmatter `status: applied` |
| 3 | 长 title (>100 字) slug ≤ 60，state yaml title 保留原文 | PASS | E2E 长 title 附加：输入 72 字 title；slug 段恰 60 字；state yaml title 保留 72 字原文 |
| 4 | `harness bugfix "含/的 标题"` 单级 | PASS | E2E 场景 3：`bugfix-1-含-路径-的-缺陷/` 单级；state yaml 同级；title 保留 `含/路径/的 缺陷` |
| 5 | 全量 discover 与基线一致无回归 | PASS | 180 tests / 1 failure (pre-existing) / 36 skipped；基线 176 + 本轮新补 4 = 180 |
| 6 | 新增 3+ 针对 slug 清洗的单测全绿 | PASS | 开发者 5 条 + 本轮 testing 补 4 条 = 9 条，全绿 |

## 单测结果

### 开发者原测 `tests/test_slug_paths.py`（5 条）

```
Ran 5 tests in 0.133s
OK
```

覆盖：含 `/` req / 长 title / 全被过滤 title (`///???`) / 含 `/` bugfix / apply_suggestion sug-08 风格。

### 本 subagent 补测 `tests/test_slug_paths_extra.py`（4 条）

```
Ran 4 tests in 0.074s
OK
```

用例 | 边界覆盖 | 结果
---|---|---
`test_backslash_and_windows_illegal_chars_in_title` | 反斜杠 `\` + `:*?"<>|` | PASS（全部被过滤，目录 `req-01-a-b-c-d-e-f-g-h-i-标题` 干净）
`test_newline_in_title_does_not_create_multiple_paths` | 多行 title | PASS（`\n` 折叠为 `-`，目录 `req-01-第一行-title-第二行噪声-第三行` 单级；state yaml title 保留原文）
`test_repeated_create_requirement_produces_new_ids` | 同 title 幂等性 | PASS（第二次自增 id：req-01 + req-02）
`test_apply_suggestion_on_legacy_sug_without_frontmatter` | 无 frontmatter sug 归档 | PASS（filename fallback 命中，文件搬到 archive/）

### 主仓全量

```
Ran 180 tests in 31.673s
FAILED (failures=1, skipped=36)
FAIL: test_human_docs_checklist_for_req29 (test_smoke_req29.HumanDocsChecklistTest.test_human_docs_checklist_for_req29)
```

唯一 failure 为 pre-existing，与 bugfix-3 无关（req-29 人文档检查项问题）。

## E2E 真跑关键断言

tempdir：`/tmp/harness-bugfix3-e2e-20260420-115447/`（保留作取证）

### 场景 1：`harness suggest --apply sug-08`

```
输入：sug-08 内容首行 = "清理 .workflow/flow/archive/main/ 下扁平格式的 36+ 个历史归档（req-01~26 早期格式）。..."（长度 178 字符）
```

- 产出 req：`artifacts/main/requirements/req-01-清理-workflow-flow-archive-main-下扁平格式的-36-个历史归档-req-01-26-早/`
  - 单级目录 ✓；不含 `/` ✓；slug 段 60 字符（apply_suggestion 在 L3120 先 `first_line[:60]` 截断）
  - 子项仅 `requirement.md` + `changes/` ✓（无 flow/ archive/ 残留层）
- state yaml：`.workflow/state/requirements/req-01-清理-...-早.yaml` 单文件 ✓
- 原 `sug-08-workflow-flow-archive-...-low.md` 已不在 `.workflow/flow/suggestions/` ✓
- 归档后文件在 `.workflow/flow/suggestions/archive/sug-08-workflow-flow-archive-...-low.md` ✓
- 归档后 frontmatter：`status: applied`（原 `pending` 翻转）✓
- `.workflow/state/runtime.yaml`：`current_requirement: "req-01"`, `stage: "requirement_review"`, `active_requirements: [req-01]` ✓

### 场景 2：`harness requirement "含/斜杠/的 标题"`

- 目录：`req-02-含-斜杠-的-标题/` 单级 ✓（与 req-01 平级）
- state yaml：`req-02-含-斜杠-的-标题.yaml` 单层 ✓
- state yaml `title: "含/斜杠/的 标题"` 保留原文（仅 dir_name 走 slug 清洗）✓

### 场景 2.5：长 title（72 字符） verificaiton of AC #3

- 输入 title 72 字
- 目录：`req-03-超长需求标题测试内容超长×24个-` slug 段恰 60 字（末字符 "超" 被 max_len=60 截断） ✓
- state yaml title 保留完整 72 字原文（`超长×24个结尾`） ✓

### 场景 3：`harness bugfix "含/路径/的 缺陷"`

- 目录：`bugfix-1-含-路径-的-缺陷/` 单级 ✓
- state yaml：`bugfix-1-含-路径-的-缺陷.yaml` 单层 ✓
- state yaml title 保留 `含/路径/的 缺陷` 原文 ✓

### 场景 4：修前/修后对比（Python 层面证据）

```
修前 f"bugfix-9-{title}" → Path("/tmp/artifacts/bugfixes/bugfix-9-含/路径/的 缺陷")
     → Path.parts = (..., 'bugfix-9-含', '路径', '的 缺陷')   # 3 层嵌套
修后 f"bugfix-9-{_path_slug(title)}" → "bugfix-9-含-路径-的-缺陷"
     → Path.parts = (..., 'bugfix-9-含-路径-的-缺陷')         # 单级
```

证明 `_path_slug` 真的拦住了 Path 拆分。

## Results

| Check | Result | Notes |
|-------|--------|-------|
| Compiles / runs without error | pass | `_path_slug` 可 import，CLI 正常 |
| Core functionality works as expected | pass | 4 E2E + 9 单测全绿 |
| Edge cases considered | pass | 补 4 条覆盖反斜杠/Windows 非法字符/换行/幂等/无 frontmatter |

## Issues Found and Fixed

未发现新缺陷。开发者实施与 bugfix.md / 实施说明.md 声明一致。

## Conclusion

- [x] Pass — ready for integration testing (acceptance)
- [ ] Fail — requires further work
