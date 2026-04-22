# Session Memory

## 1. Current Goal

- Describe the current goal for this change.

## 2. Current Status

- Summarize what is already done.

## 3. Validated Approaches

- Record commands, checks, or decisions that already worked.

## 4. Failed Paths

- Attempt:
- Failure reason:
- Reminder: do not retry this blindly unless assumptions change.

## 5. Candidate Lessons

```markdown
### [date] [summary]
- Symptom:
- Cause:
- Fix:
```

## 6. Next Steps

- Add the next actions here.

## 7. Open Questions

- Add unresolved questions here.

## 执行记录

### 2026-04-19 — chg-06 端到端 smoke 实施（executing 角色）

- ✅ 读取 `WORKFLOW.md` / `.workflow/context/index.md` / `.workflow/state/runtime.yaml` / `base-role.md` / `stage-role.md` / `executing.md` + 本 change 的 change.md / plan.md / requirement.md（req-26）。
- ✅ 新增 `tests/test_smoke_req26.py`（4 用例 / 总 270+ 行，含端到端 smoke 与 AC-06 静态契约核查）。
- ✅ 单独跑：`python3 -m unittest tests.test_smoke_req26 -v` → 4/4 通过。
- ✅ 整体回归：`python3 -m unittest discover tests -v` → 81 测试（原 77 + 新 4），失败/错误计数稳定 3/3/36 skipped，与 chg-05 合入后基线一致。
- ✅ AC 核对：
  - AC-01：`test_full_lifecycle_smoke` 步骤 6，confirm 后 current_regression 保留，--testing 仍能消费。
  - AC-02：步骤 1（rename_requirement 目录保留 `req-{n}-` 前缀 + state yaml 同步）、步骤 3（create_change + rename_change 保留 `chg-{n}-` 前缀）。
  - AC-03：步骤 2/4/5/7 每次 next 之后 `.workflow/state/requirements/{id}.yaml` 的 stage 字段与 runtime 同步；推到 done 时 status 自动写为 done。
  - AC-04：步骤 6 regression 目录以 `reg-{n}-` 前缀开头，kebab-case，无空格。
  - AC-05：步骤 8 archive 归档路径 `artifacts/main/archive/{folder}/`，断言 `/main/` 段只出现一次、无 `archive/main/main/` 双层 branch。
  - AC-06：降级为 3 个静态契约核查（stage-role 章节存在、7 角色含"对人文档输出"、scaffold_v2 镜像文本一致）。
  - AC-07：以上 6 点在一个 tempdir 会话串起验证 → 集成通过。
- ✅ 产出对人文档 `实施说明.md` 于本 change 根目录。
- ✅ 本次执行未触碰 `.workflow/flow/`、未改动 chg-01~05 的代码或测试、未污染仓库 `.workflow/state/` 与 `artifacts/`。

### 关键决策

- 按 briefing 硬约束，smoke 走 helper 函数级（`create_requirement` / `workflow_next` / `create_regression` / `regression_action` / `archive_requirement` 等），不调用真 CLI。
- `create_requirement` 本身不做 slug 化，业务场景下通过一次 `rename_requirement` 完成目录名清洗；smoke 中显式走该路径以覆盖 AC-02 的"合并 B"要求。
- AC-06 的对人文档由 agent 实际执行时产出，非 helper 函数契约；按 briefing 降级为 3 项静态断言（契约章节 + 7 角色条目 + scaffold_v2 镜像一致）。
- mock `_get_git_branch` 固定为 `main` + mock `input` 为 `n` 以隔离 git 与交互式 commit 提示。

### 交接建议

- testing / acceptance 阶段：可直接读取 `tests/test_smoke_req26.py` 与本 `实施说明.md` 作为 AC-07 证据；单独复核 AC-06 时建议 diff `.workflow/context/roles/` 与 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`。
- done 阶段：req-26 可以进入 archive；archive 后注意历史 `artifacts/bugfixes/bugfix-2/` 与 `artifacts/main/bugfixes/bugfix-{3,4,5}/` 脏数据在 req-26 的 Excluded 里，不在本次清洗范围。
