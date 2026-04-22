# Session Memory — chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）

## 1. Current Goal

- req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03：扩展 `_build_subagent_briefing` 注入 `task_context_index` + `task_context_index_file`，并在 `workflow_next(execute=True)` 派发点前构建索引 + 落盘快照。

## 2. Current Status

- ✅ Step 1 红：`tests/test_task_context_index.py`（7 条）+ `tests/test_task_context_snapshot.py`（3 条）已落盘，10 条 TDD 红（1 条向后兼容 test 意外绿通过，9 条真红）。
- ✅ Step 2 绿：`_build_subagent_briefing` 扩展 kw-only 参数 `task_context_index` / `task_context_index_file`，JSON fence 追加两字段；向后兼容。
- ✅ Step 3 绿：`_build_task_context_index` 按优先级构建候选（role / stage-role / base-role / experience / profile / constraints / checklist），硬上限 8 + stderr warn。
- ✅ Step 4 绿：`_write_task_context_snapshot` + `_next_task_context_seq` 落盘 frontmatter 四字段 + 正文；seq 按 stage 独立递增（001/002...）。
- ✅ Step 5 绿：`workflow_next` 派发点串接，`execute=True` 时构建索引 → 写快照 → briefing 两字段。
- ✅ Step 6 绿：`.workflow/context/roles/stage-role.md` + `scaffold_v2/.../stage-role.md` 新增 C2 回退语义小节 + `_resolve_task_context_paths` helper。
- ✅ 10 条新测全绿；`pytest -q` 281 passed / 50 skipped（基线 271，+10 新增），零回归。
- ✅ 对人文档 `实施说明.md` 已产出。
- ✅ 契约 7 自检：新文件 0 新增违规（历史 322 条基线不动）。

## 3. Validated Approaches

- `json.dumps(index_list, ensure_ascii=False, indent=4)` + 手工 shift 2 空格缩进，保证 briefing 内嵌 JSON 既合法又对齐美观。
- `_next_task_context_seq` 用正则扫 `{stage}-\d+\.md` 取 max + 1，兼容 seq 空洞场景。
- 集成测试用 `ready_for_execution → executing`（`plan_review → ready_for_execution` 命中 `_NO_BRIEFING_STAGES` 不派发 briefing，无法验证字段）。
- `load_project_profile(path)` 接收**文件绝对路径**（非 root），故判断 profile 存在改用 `(root / profile_rel).exists()`。

## 4. Failed Paths

- 首次集成测试选 `stage="plan_review"`：`workflow_next` 把 stage 推到 `ready_for_execution`（属 `_NO_BRIEFING_STAGES`），stdout 无 fence 导致测试失败。修正为 `stage="ready_for_execution"` → `executing`。
- 单独 `pytest tests/test_task_context_snapshot.py`（不带其他 tests）报 `ModuleNotFoundError`：pytest 路径发现依赖其他测试先拉起 `harness_workflow` 包；组合跑（搭 test_project_scanner.py）即正常。

## 5. Candidate Lessons

```markdown
### 2026-04-21 briefing JSON 序列化
- Symptom: 手工拼字符串易错（中文 reason + 转义 + 缩进）。
- Cause: Python 字符串拼接缺乏 JSON schema 校验。
- Fix: 让 `_build_subagent_briefing` 内部用 `json.dumps(..., ensure_ascii=False, indent=4)` 序列化索引数组 + `json.dumps(str)` 序列化字符串字段，再整体 shift 缩进对齐 2 空格。后续扩字段优先走此模式。
```

## 6. Next Steps

- 等主 agent 进入 testing 阶段做独立验证。
- ✅ **扩展范围补齐（2026-04-21）**：ff --auto / regression 派发路径 briefing 接入完成（AC-03 全量覆盖）
  - `_build_subagent_briefing` 新增 3 个可选 kwarg（`root` / `regression_id` / `regression_title`），全部向后兼容
  - `workflow_ff_auto` 最终落点非终局 stage 派发 briefing（复用 `_NO_BRIEFING_STAGES`）
  - `create_regression` 派 `stage=regression` briefing，注入 `regression_id` / `regression_title` 两字段
  - 新增 `tests/test_briefing_ff_regression.py` 6 条 TDD（红绿分开 commit）
  - pytest 287 passed / 50 skipped（基线 281，+6 新增，零回归）

## 7. Open Questions

- 无阻塞。`task_context_index` 目前未做 stack_tag 深度加权，后续若有 domain-specific 经验文件可扩 helper。
