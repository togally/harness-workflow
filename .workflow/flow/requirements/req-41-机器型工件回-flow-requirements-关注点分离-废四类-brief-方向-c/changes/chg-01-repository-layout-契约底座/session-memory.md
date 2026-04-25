# Session Memory — chg-01（repository-layout 契约底座（git mv + 三大子树 §2 重写））

## 1. 产出

- `.workflow/flow/repository-layout.md`（live，git mv 自 artifacts-layout.md + 全文重写）
- `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`（mirror，cp 同步，diff 零差异）

## 2. 状态

完成。全部 AC 验证通过。

## 3. AC 自证

| AC | 检查项 | 结果 |
|----|--------|------|
| AC-01 | `test -f .workflow/flow/repository-layout.md` | PASS |
| AC-01 | `test ! -f .workflow/flow/artifacts-layout.md` | PASS |
| AC-01 | `grep -c "^## "` = 6（≥ 5） | PASS |
| AC-07 | `grep -cE "需求摘要\|变更简报\|实施说明\|回归简报\|耗时与用量报告"` = 0 | PASS |
| AC-14 | 所有 req-*/chg-*/sug-*/reg-* 首引用均带 title 或 ≤ 15 字描述；无裸 id | PASS（人工核对） |
| AC-15 | `test -f src/.../scaffold_v2/.workflow/flow/repository-layout.md` | PASS |
| AC-15 | `test ! -f src/.../scaffold_v2/.workflow/flow/artifacts-layout.md` | PASS |
| AC-15 | `diff -q live mirror` 无输出 | PASS |

## 4. Default-pick

- §2 "注意"中四类 brief 说明：改为"四类 brief（req 级摘要 / chg 级对人简报 / chg 级对人说明 / regression 级对人简报）"描述性表达，不直接拼写废止文件名（AC-07 严格 grep = 0 要求）。
- §5 反例代码块同理，删去具体文件名，改为白名单范围说明段。

## 5. 下游依赖影响

- chg-02（CLI 路径迁移（FLOW_LAYOUT_FROM_REQ_ID + create_/archive_ 改写））、chg-03（validate_human_docs 重写 + 白名单清理）、chg-04（角色文件去路径化 + 删四类 brief 模板）等可独立启动（DAG 根已就绪）。
- `stage-role.md` 中 `.workflow/flow/artifacts-layout.md` 引用尚待 chg-04（角色文件去路径化 + 删四类 brief 模板）处理（scope 排除，本 chg 不动角色文件）。
- `validate_human_docs.py` 注释引用 `artifacts-layout.md` 尚待 chg-03（validate_human_docs 重写 + 白名单清理）处理。

## 6. 回归

- pytest 全量：394 passed / 39 skipped（pre-existing `test_readme_has_refresh_template_hint` 失败与本 chg 无关，git stash 验证确认为存量失败）。

本阶段已结束。
