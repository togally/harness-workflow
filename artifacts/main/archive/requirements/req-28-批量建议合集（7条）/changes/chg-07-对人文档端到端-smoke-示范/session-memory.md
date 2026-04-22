# Session Memory

## 1. Current Goal

- 为 req-28 / chg-07 新增端到端 smoke（覆盖 AC-07 + AC-11，联动 AC-09/10/12/13/14/15）；产出 `实施说明.md`；对 req-28 自身对人文档做一次 AC-11 "首次完整示范"统计。

## 2. Current Status

- [x] 读取 runtime.yaml / base-role / stage-role / executing.md
- [x] 读取 change.md / plan.md / 变更简报.md（chg-07）
- [x] 读取 requirement.md（确认 AC-09~AC-15 内容）
- [x] 读取 `test_smoke_req26.py`、`test_suggest_cli.py`、`test_bugfix_runtime.py`、`test_archive_bugfix.py`、`test_validate_human_docs.py`、`test_cycle_detection.py` 作为参考风格
- [x] 新增 `tests/test_smoke_req28.py`（6 条集成用例）
- [x] 跑 `python3 -m unittest tests.test_smoke_req28 -v`：6/6 OK
- [x] 跑全仓 `python3 -m unittest discover tests`：134 tests OK（基线 128 + 新增 6），0 fail / 0 error
- [x] 直接 import `validate_human_docs` 统计 req-28 对人文档：14/18 present
- [x] 产出对人文档 `实施说明.md`

## 3. Validated Approaches

### 3.1 Smoke 脚本结构

- 按 test_smoke_req26.py 风格，tempdir 隔离 + `_make_harness_workspace` 最小铺设。
- `unittest.mock.patch` 固定 `_get_git_branch` → "main"，避免依赖测试机真实 git 状态。
- `builtins.input` mock 为 "n"，避免 archive 尾部 git auto-commit 交互挂起。

### 3.2 命令与结果

```
$ python3 -m unittest tests.test_smoke_req28 -v
Ran 6 tests in 0.270s
OK

$ python3 -m unittest discover tests
Ran 134 tests in 25.654s
OK (skipped=36)
```

### 3.3 AC 覆盖对照表

| 用例 | AC 覆盖 |
|------|---------|
| `test_full_lifecycle_with_bugfix_and_archive` | AC-07 端到端 + AC-11 闭环 + AC-12 operation_type 持久化 + AC-03 扩展（bugfix yaml stage 同步）+ AC-14 archive bugfix 分流 + AC-05 单层 branch |
| `test_suggest_cli_handles_no_frontmatter` | AC-15 filename fallback（delete/apply 两路径）|
| `test_suggest_numbering_monotonic_across_archive` | AC-15 跨 archive 编号单调 |
| `test_cycle_detector_import_and_basic_detect` | AC-13 顶层 7 符号导出 + 基础 cycle 语义 |
| `test_validate_human_docs_reports_missing_and_present` | AC-09 ok / missing 区分 |
| `test_readme_has_refresh_template_hint` | AC-10 下游刷新模板提示 |

## 4. Failed Paths

- 无。一次性 6 条 smoke 全部通过，没有需要重试的失败路径。

## 5. Candidate Lessons

### [2026-04-19] tempdir smoke 是跨 chg 联动验证的首选

- Symptom：单 chg 级 unit test 只能证明各自 bug 修完，无法证明合在一起跑不炸。
- Cause：bugfix/archive/suggest 三条链路互相依赖（AC-12 断 → AC-14 走不通），需要一次端到端走完。
- Fix：一个 TestCase 串 req→done→archive 再 bugfix→done→archive，AC 在各断言点验证；用 mock 固定 git branch 和 input，保证可复现。
- 已沉淀到本 session-memory；未来类似的 chg 组合验证可复用此模板。

## 6. Next Steps

- chg-07 退出条件全部满足，等待 subagent 上报主 agent。
- req-28 推进到 testing 阶段时，由测试工程师产出 `测试结论.md`；acceptance / done 阶段依次补齐剩余 3 份 req-level 对人文档，AC-11 即 100% 闭环。

## 7. Open Questions

- 无未决问题。AC-11 首次完整示范的缺口由后续 stage 按契约产出，不属于本 chg 范围。

---

## 8. AC-11 首次完整示范证据（validate_human_docs 快照）

直接调用 `harness_workflow.validate_human_docs.validate_human_docs(root, "req-28")` 得到 18 条校验项：

- 本 `实施说明.md` 产出前：**14 / 18 present**
- 本 `实施说明.md` 产出后（即 chg-07 完成时）：**15 / 18 present**

| 状态 | 文档 |
|------|------|
| [✓] | 需求摘要.md（req 级，planning 阶段产出） |
| [ ] | 测试结论.md（req 级，testing 阶段产出） |
| [ ] | 验收摘要.md（req 级，acceptance 阶段产出） |
| [ ] | 交付总结.md（req 级，done 阶段产出） |
| [✓] | chg-01 ~ chg-06 每个 change 的 `变更简报.md` + `实施说明.md`（12 份） |
| [✓] | chg-07 `变更简报.md` |
| [✓] | chg-07 `实施说明.md`（本次产出） |

剩余 3 份 req-level 对人文档属于后续 stage 的职责；chg-07 不越权代写，由主 agent 推进到对应 stage 时由相应角色补齐。
