# Session Memory

## 1. Current Goal

- 执行 chg-05：为 7 个 stage 角色建立"对人文档"双轨输出 SOP + 最小字段模板，并同步 scaffold_v2 镜像与中文化 change/plan 模板。

## 2. Current Status

- plan.md 1.2 / 1.3 / 1.4 / 1.5 / 1.6 / 1.7 / 1.8 全部完成。
- 本 change 自身的 `实施说明.md` 已示范写入 `artifacts/main/requirements/req-26-uav-split/changes/chg-05-*/实施说明.md`。

## 3. Validated Approaches

- 先改本仓库 `.workflow/context/roles/` 下 8 个文件，再用 `cp` 一比一刷到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 下同名文件，`diff` 核对 0 差异（self-check 全绿）。
- change.md / plan.md 模板（含 `.en.tmpl`）直接 Write 整文件重写，字段结构与本 req-26 实际在用的 change.md / plan.md 对齐。
- 反例核对：`git status` 未见 `.workflow/flow/**`（属本 change 的改动）、未见 `artifacts/bugfixes/bugfix-{2,3,4,5}/**` 变更。

## 4. Failed Paths

- 无。

## 5. Candidate Lessons

```markdown
### 2026-04-19 对人文档 SOP 必须同时落硬退出条件
- Symptom: 若仅在角色文件加描述性段落，agent 可能忽略。
- Cause: SOP 若不进"退出条件清单"，base-role 的"退出条件强制检查"不会拦截缺失对人文档的 case。
- Fix: 每个 stage 角色的"## 退出条件"末尾必须追加一条 `- [ ] 对人文档 {文件名}.md ...`，与新节"对人文档输出（req-26）"配对，缺一不可。
```

## 6. Next Steps

- 等待 chg-06 端到端 smoke 验证：
  - `harness install` 到临时仓库后 `diff -r` 新仓库与本仓库 `.workflow/context/roles/`；
  - `harness change` 生成的 `change.md` / `plan.md` 断言含新字段结构；
  - 切 `language=en` 验证 `.en.tmpl` 对称。
- req-26 后续 requirement_review 阶段可选择补充 `artifacts/main/requirements/req-26-uav-split/需求摘要.md` 作为样例。

## 7. Open Questions

- planning 表述微调的边界（契约 3 备注）是否需要在 stage-role.md 里补一条白名单？留作 chg-06 smoke 后回顾。

## 执行记录

### 改动文件清单（本 change 产出）

- `.workflow/context/roles/stage-role.md`（新增"对人文档输出契约"章节）
- `.workflow/context/roles/requirement-review.md`
- `.workflow/context/roles/planning.md`
- `.workflow/context/roles/executing.md`
- `.workflow/context/roles/testing.md`
- `.workflow/context/roles/acceptance.md`
- `.workflow/context/roles/regression.md`
- `.workflow/context/roles/done.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/requirement-review.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/planning.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/executing.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/testing.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/acceptance.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/regression.md`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/done.md`
- `src/harness_workflow/assets/skill/assets/templates/change.md.tmpl`（中文完整版）
- `src/harness_workflow/assets/skill/assets/templates/change-plan.md.tmpl`（中文完整版）
- `src/harness_workflow/assets/skill/assets/templates/change.md.en.tmpl`（英文完整版对称）
- `src/harness_workflow/assets/skill/assets/templates/change-plan.md.en.tmpl`（英文完整版对称）
- `artifacts/main/requirements/req-26-uav-split/changes/chg-05-*/实施说明.md`（本 change 自身 SOP 的第一次应用）
- `artifacts/main/requirements/req-26-uav-split/changes/chg-05-*/session-memory.md`（本文件）

总计 22 个文件（8 角色 + 8 scaffold 镜像 + 4 模板 + 1 实施说明 + 1 session-memory）。

### Self-check 结果

| 检查项 | 结果 |
|-------|------|
| 8 个角色文件均包含"对人文档输出"章节 | ✅（`grep -l 对人文档输出` 命中 8 个） |
| 7 个 stage 角色文件的"退出条件"均追加对人文档条目 | ✅（`grep '^- \[ \] 对人文档'` 命中 6 个 + planning.md 用"每个 change 都在…产出对人文档 `变更简报.md`"格式，表述等价） |
| scaffold_v2 与本仓库 8 个角色文件文本一致 | ✅（`diff` 全 0 差异） |
| change.md.tmpl 含 6 个必备节 | ✅（1.Title / 2.Goal / 3.Requirement / 4.Scope / 5.Acceptance / 6.Risks） |
| change-plan.md.tmpl 含 3 个必备节 | ✅（1.Development Steps / 2.Verification Steps / 3.依赖与执行顺序） |
| `.en.tmpl` 英文对称 | ✅（字段结构对称，措辞为英文） |
| 反例：未触碰 `.workflow/flow/**` | ✅ |
| 反例：未触碰 `artifacts/bugfixes/bugfix-{2,3,4,5}/**` | ✅ |

### 遗留问题

- `harness install` / `harness change` 端到端验证归并到 chg-06 smoke 执行。
- planning 阶段"表述微调边界"未显式列举，留 chg-06 smoke 后回顾。
