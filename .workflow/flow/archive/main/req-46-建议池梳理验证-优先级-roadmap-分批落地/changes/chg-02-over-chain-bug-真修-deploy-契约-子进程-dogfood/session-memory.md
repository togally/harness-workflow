# Session Memory — chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）

## 1. Current Goal

执行 req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）下 chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）的 plan.md 9 个 Development Steps，固化临时的 over-chain bug 修复为代码契约 + AC，避免下次再依赖人工记得 `pipx install --force`。

---

## 2. Context Chain

- Level 0: 主 agent（harness next → executing）
- Level 1: harness-manager（opus，命令解析 + 角色调度）
- Level 2: executing-L1（sonnet，本 subagent，chg-02 落地）

---

## 3. Completed Steps（执行 session）

- ✅ Step 1：保守降级严格化（_is_stage_work_done）
  - `src/harness_workflow/workflow_helpers.py` executing 分支 changes_dir 缺 → False，无 session-memory.md → False
  - 同步 docstring 记录例外原则
- ✅ Step 2：子进程 dogfood 测试（tests/test_workflow_next_subprocess.py）
  - 新建 5 个测试用例（TC-03 ~ TC-07）；4 路径（first-hop / while-internal / 缺产物 / 有产物）全绿
  - 修复 feedback.jsonl event key 为 "event"（非 "event_type"），data key 为 "data"（非 "payload"）
- ✅ Step 3：升级 .workflow/evaluation/acceptance.md checklist（部署同步契约硬条目）
- ✅ Step 4：升级 .workflow/evaluation/testing.md（子进程 dogfood 红线段落）
- ✅ Step 5：sug-46（req-44 二次实证 over-chain）+ sug-50（gate gap 部署 gap）+ sug-53（usage-log 缺失） frontmatter 字段更新
  - linked_regression: reg-02 + promoted_to_chg: chg-02 / partial_promoted_to_chg: chg-02
  - status 维持 pending（acceptance PASS 后翻 archived）
- ✅ Step 6：经验沉淀（regression.md 经验十：三维失配诊断模板）
  - 注：原文件已有经验九（bugfix 模式 diagnosis.md），新增经验十避免覆盖
- ✅ Step 7：scaffold_v2 mirror 同步（evaluation/acceptance.md + evaluation/testing.md + context/experience/roles/regression.md）
  - 三文件 diff 一致验证通过
- ✅ Step 8：本 chg-02 自身周期 dogfood 自证
  - pipx install --force 完成（venv mtime 1777304379 ≥ HEAD commit ts 1777304020）
  - python3 -m harness_workflow.cli next 在 session-memory.md 无 ✅ 时正确报"Stage executing 工作未完成"
  - 自证证据：harness next gate 阻断验证通过
- ✅ Step 9：测试用例编写 + pytest 跑通
  - tests/test_workflow_helpers_executing_gate.py：9/9 通过（TC-01/TC-01b/TC-01c/TC-01d/TC-02/TC-02b/TC-02c/TC-08/TC-08b）
  - tests/test_workflow_next_subprocess.py：5/5 通过（TC-03/TC-04/TC-05/TC-06/TC-07）
  - tests/test_workflow_next_workdone_gate.py：8/8 通过（原有用例无回归）
  - 全仓库回归：653 passed，4 failed（均为 pre-existing failures，已 git stash 验证存在于 chg-02 前）
  - harness validate --contract artifact-placement：PASS

---

## 4. Validated Approaches

- **event key 坑**：feedback.jsonl 实际写入格式 `{"ts": ..., "event": "stage_advance", "data": {...}}`，不是 `{"event_type": ..., "payload": ...}`；subprocess 测试的 `_read_feedback_jsonl` 需兼容两种格式
- **保守降级严格化边界**：仅 executing stage 改严，testing/acceptance 不变，planning/RFE/_FALLBACK_STAGES 保持 True；two-pass：changes_dir 缺 → False，无 session-memory.md → False（均严格化）
- **dogfood 自证顺序**：Step 1 先落地严格化 → Step 8 pipx --force 重装 → harness next 实测 gate → session-memory.md 加 ✅ → harness next 再测 advance
- **scaffold_v2 mirror**：git stash/pop 后 scaffold_v2 改动保留（系统 stash 策略含 staged unstaged，pop 后均回来）

---

## 5. Failed Paths

- **subprocess test 首次失败**：`_read_feedback_jsonl` 用了错误的 key `"event_type"` 和 `"payload"`；实际 CLI 写 `"event"` 和 `"data"`；修复后 5/5 通过
- **经验编号**：原 plan.md 说"经验九"但文件已有经验九（bugfix mode）；决策（default-pick）改为追加经验十，避免覆盖已有内容，合规

---

## 6. AC Mapping 自检

| AC | 落地 Step | 验证证据 |
|----|-----------|---------|
| AC-1（保守降级严格化） | Step 1 + Step 9 | TC-01/TC-01b 各自 PASS |
| AC-2（subprocess dogfood 4 路径全绿） | Step 2 + Step 9 | TC-03~TC-06 PASS |
| AC-3（自身周期 dogfood 自证） | Step 8 + TC-07 | harness next gate 阻断实测 + TC-07 全链 PASS |
| AC-4（sug 状态翻转） | Step 5 | sug-46/50/53 frontmatter grep 验证 |
| AC-5（部署同步契约文档化） | Step 3 + TC-08 | acceptance.md "部署同步契约"段 + TC-08 pipx freshness PASS |
| AC-6（mirror diff 一致 + 经验沉淀） | Step 4 + 6 + 7 | scaffold_v2 diff 一致 + regression.md 经验十 + testing.md "子进程 dogfood 红线" |

---

## 7. default-pick 决策清单（executing 阶段）

- **E-1（经验编号）**：plan.md 说"经验九"，文件已有经验九，default-pick 追加为经验十；不覆盖已有内容。
- **E-2（feedback.jsonl key 兼容）**：`_read_feedback_jsonl` 兼容 `"event"`/`"event_type"` + `"data"`/`"payload"` 两种格式；不改 CLI 写入逻辑（only-read-side fix）。

---

## 8. 模型一致性自检留痕（role-loading-protocol Step 7.5 fallback）

- expected_model（briefing）：sonnet
- 当前执行为 sonnet 模型；自检通过。

---

## 9. Next Steps（给 testing subagent）

1. 读本 session-memory.md + plan.md §4 TC 设计（regression_scope: full）；
2. 跑 `pytest tests/test_workflow_next_subprocess.py tests/test_workflow_helpers_executing_gate.py tests/test_workflow_next_workdone_gate.py -v` 全绿确认；
3. 跑 `pytest -q` 全量回归，确认 4 个 pre-existing failures 不变、无新增；
4. 验证 acceptance.md 含"部署同步契约"段 + testing.md 含"子进程 dogfood 红线"段 + regression.md 含"经验十"；
5. 验证 scaffold_v2 mirror diff 一致；
6. 验证 sug-46/50/53 frontmatter 含 linked_regression: reg-02 + promoted_to_chg: chg-02。
