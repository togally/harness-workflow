# Change

## 1. Title

over-chain bug 真修 + deploy 契约 + 子进程 dogfood

## 2. Background

reg-02（over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done）— sug-46/-50/-53 同根因复发）confirmed → 路由 planning。三维失配根因摘要 + 本会话内三次复发证据 + req-45（harness next over-chain bug 修复（紧急）） chg-01（verdict stage work-done gate + workflow_next 集成） dogfood 设计盲点：

- **三维失配（契约 / 源码 / 部署）**：
  - **契约层 ✓**：`stage_policies` + `_is_stage_work_done` 双 gate 设计正确，role-model-map.yaml 出口决策语义清晰。
  - **源码层 ✓**：`src/harness_workflow/workflow_helpers.py:7338-7429` `_is_stage_work_done` helper 已落地（commit b64bcd7），第 7548 first-hop gate + 第 7580 while 内 gate 都在；在线复验 `_is_stage_work_done('executing'/'testing'/'acceptance', root, 'req-46', 'requirement')` 全部正确返回 False。
  - **部署层 ✗**：pipx site-packages 下 `workflow_helpers.py` mtime = 2026-04-26 23:35:05（chg-01 commit b64bcd7 = 2026-04-27 14:54:13 之前一天），grep `_is_stage_work_done` 在 pipx 路径下**完全无命中**——helper 整段 + 双 gate 都不在运行时二进制里。
- **本会话内三次复发证据（feedback.jsonl）**：
  - 02:00:28.576 ~ 02:00:28.585：5 条 stage_advance 9 ms 内全发，RFE → executing → testing → acceptance → done；
  - 06:49:32.548 ~ 07:03:22.728：两次短链跳跨（testing → acceptance → done，4-5 ms）；
  - **09:25:35.779 ~ 09:25:35.787**：本 reg-02 触发的 4 跳完整链（RFE → executing → testing → acceptance → done，8 ms 内）。
- **req-45 chg-01 dogfood 盲点**：testing 用 `pytest tests/test_workflow_next_workdone_gate.py` 跑直接 `from harness_workflow.workflow_helpers import _is_stage_work_done`——pytest 走 src/ 版本，`harness next` CLI 走 pipx site-packages 版本，**不是同一个二进制**。tmpdir mock dogfood 也是直接调 helper 函数，不走 CLI 子进程，所以测试链条没有覆盖"CLI 实际部署版本"维度。
- **临时验证活证**：今日 23:00 已临时跑 `pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow` 验证 bug 在部署刷新后即时止（gate 正常拦 `Stage executing 工作未完成，请先完成当前阶段工作再推进。`）。本 chg-02 把这个临时修固化成代码契约 + AC，避免下次再依赖人工记得 `pipx install --force`。

## 3. Requirement

- req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）

## 4. Scope

### Included

- **改动 1（保守降级严格化）**：`src/harness_workflow/workflow_helpers.py::_is_stage_work_done` 第 7407-7409 在 `executing` stage 且 `changes_dir` 缺时返回 False（现行返回 True 太宽）；其他 stage 维持 True 保守降级；planning / RFE 出口走 `_FALLBACK_STAGES` 豁免，不动。
- **改动 2（子进程 dogfood）**：新增 `tests/test_workflow_next_subprocess.py`，用 `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next', ...])` 真跑 CLI（不只 import helper），覆盖 4 路径：first-hop / while-internal / 缺产物 / 有产物；用 tmpdir 干净 fixture（呼应 sug-51（testing 红线 — subprocess dogfood 必须真跑 CLI 不只 mock helper））。
- **改动 3（部署同步契约）**：`.workflow/evaluation/acceptance.md` checklist 新增"部署同步：`pipx install --force <repo-path>` 或 `harness install --force-skill` 已执行（验证 venv `_is_stage_work_done` 存在 + mtime ≥ HEAD commit ts）"硬条目，缺此步则 acceptance FAIL；`done.md` 六层 State 层 grep 校验扩展（部署版本 vs source mtime / hash 对比）。
- **改动 4（sug 状态翻转）**：sug-46（req-44 二次实证 over-chain）/ sug-50（chg-01 gate gap 实为部署 gap）/ sug-53（usage-log 缺失 over-chain 副作用）frontmatter 加 `linked_regression: reg-02` + `promoted_to_chg: chg-02`；chg-02 acceptance PASS 后 sug-46（二次实证 over-chain）+ sug-50（gate gap 部署 gap） status 翻 `archived`；sug-53（usage-log 缺失） over-chain 副作用部分 archived，主因（sug-39（record_subagent_usage 钩子未接通））保留 pending。
- **改动 5（scaffold_v2 mirror 同步）**：本 chg 涉及 `.workflow/evaluation/acceptance.md` + `.workflow/evaluation/testing.md` + `.workflow/context/experience/roles/regression.md` 改动，按硬门禁五同步至 `src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/` + `.../experience/roles/`，同 commit 落地。
- **改动 6（经验沉淀 + testing 红线）**：`.workflow/evaluation/testing.md` 加"子进程 dogfood 必须真跑 CLI"经验（呼应 sug-52（testing 经验沉淀模板缺 dogfood 维度））；`.workflow/context/experience/roles/regression.md` 新增经验九"三维失配（契约 / 源码 / 部署）诊断模板"——经验八（契约 vs 实现二维）扩展到三维。

### Excluded

- **UI / 前端**：本 chg 不涉及任何 UI 改动。
- **其他 chg**：与 chg-01（机器型工件路径修复 + 防再犯 lint）独立可并行，本 chg 不包揽 chg-01 工作；roadmap chg-2（sug-39 钩子接通）/ chg-3（首批 P0 第二+三批）后置等待本 chg PASS，不在本 chg 范围。
- **跨 repo**：不动 Yh-platform 等其他 repo 的部署同步行为；仅在本仓库 harness-workflow 落地。
- **sug-53（usage-log 缺失） 主因（sug-39（派发钩子未接通））**：本 chg 仅收 sug-53 的 over-chain 副作用部分，sug-39 主因留独立 chg；避免 scope 蔓延。

## 5. Acceptance

- **AC-1（保守降级严格化）**：`_is_stage_work_done('executing', root, req_id, 'requirement')` 在 `changes_dir` 缺时返回 `False`；unit test 覆盖该边界（呼应 requirement.md AC-02 chg 落地有依据）。
- **AC-2（子进程 dogfood 4 路径全绿）**：`tests/test_workflow_next_subprocess.py` 4 路径（first-hop / while-internal / 缺产物 / 有产物）全绿，子进程实跑 `harness next` / `harness next --execute`，断言 stdout / runtime.yaml stage 落点 + feedback.jsonl 事件数。
- **AC-3（自身周期 dogfood 自证）**：本 chg-02 走完 executing → testing → acceptance → done 全程，feedback.jsonl 中本 chg 周期内 `stage_advance` 事件相邻间隔 ≥ 4 ms（无 < 4 ms 连跳），4 跳由 4 次 `harness next` 驱动而非 1 次连跳。
- **AC-4（sug 状态翻转）**：sug-46（二次实证 over-chain）+ sug-50（gate gap 部署 gap）+ sug-53（usage-log 缺失） frontmatter 字段全填——`linked_regression: reg-02` + `promoted_to_chg: chg-02`；acceptance PASS 后 sug-46（二次实证 over-chain）+ sug-50（gate gap 部署 gap） status 翻 `archived`；sug-53（usage-log 缺失） over-chain 副作用部分 archived，主因部分留 pending（呼应 requirement.md AC-05 出池清理）。
- **AC-5（部署同步契约文档化）**：`.workflow/evaluation/acceptance.md` checklist 含"pipx 重装已执行 + venv mtime ≥ commit ts"硬条目；模拟反例（mtime 早于 commit）触发 acceptance FAIL；模拟正例（mtime ≥ commit）通过。
- **AC-6（mirror diff 一致 + 经验沉淀）**：`diff -rq .workflow/evaluation/ src/harness_workflow/assets/scaffold_v2/.workflow/evaluation/` 与 `diff -rq .workflow/context/experience/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/` 均无差异；`testing.md` 含"子进程 dogfood 必须真跑 CLI"经验；`regression.md` 含经验九"三维失配（契约 / 源码 / 部署）诊断模板"。

## 6. Risks

- **R1（保守降级改严风险）**：把 `if not changes_dir.exists(): return True` 改 `return False`（仅 `executing`）可能误伤合法场景（如新 req 还没创建任何 chg 时跑 next）。**缓解**：仅 `executing` stage 严格化，其他 stage（planning / RFE / 等）保留 True 兜底；unit test TC-01 / TC-02 覆盖边界。
- **R2（部署契约 user-friction 风险）**：开发态 pipx 频繁重装可能影响别的工作（每次改 src/ 都要重装）。**缓解**：通过 `dev mode flag`（`HARNESS_DEV_MODE=1` 环境变量）豁免开发态；`harness install --force-skill` 已具备复用机制，仅在 src/ 修改后触发；提供 `harness install --check` 子命令做版本对比预警（不强制重装）。
- **R3（子进程 dogfood 时间长）**：subprocess 跑 CLI 比直调 helper 慢（启动 venv ~500ms × 4 路径 = 2 s）。**缓解**：标 P1 子集（仅 acceptance 跑全量），P0 子集（unit）跑 helper 直调即可；CI 全量在 acceptance gate 跑。
- **R4（subprocess test 跨平台风险）**：tests/test_workflow_next_subprocess.py 在 Windows / Linux / Mac 行为可能差异（路径分隔符 / 子进程启动方式）。**缓解**：fixture 用 `tmp_path` + `pathlib.Path`，subprocess 用 `sys.executable` 而非硬编码 python；`subprocess.run` 用 `text=True` 强制 UTF-8。

## 7. Dependencies

- **前置依赖**：无。本 chg 与 chg-01（机器型工件路径修复 + 防再犯 lint）完全独立，可并行启动 executing。
- **后置阻塞**：roadmap chg-2（sug-39 钩子接通）+ chg-3（roadmap 首批 P0 第二+三批）等待本 chg acceptance PASS——避免后续 chg 也踩 over-chain bug 导致 stage 跳过 + subagent 漏派。
- **跨 chg 信号**：本 chg 落地的 dogfood 红线（subprocess 真跑 CLI）+ 三维失配诊断模板，作为后续所有 P0 修复 chg 的 testing / acceptance 共用基础设施；后续 chg 在 plan.md §测试用例设计段引用本 chg 的 `tests/test_workflow_next_subprocess.py` 模式。
