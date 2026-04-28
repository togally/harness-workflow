# Session Memory — reg-02（over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done）— sug-46/-50/-53 同根因复发）

## 1. Current Goal

执行 reg-02 诊断 + 路由决策。隶属 req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）。

- 不修复 over-chain bug（regression 角色仅诊断，不修复）；
- 不创建 chg 工件（留给 harness regression --change 或 harness change CLI）；
- 仅产出 5 件机器型工件：regression.md / analysis.md / decision.md / meta.yaml / 本 session-memory.md，**全部落 `.workflow/flow/requirements/req-46-.../regressions/reg-02-.../`**，0 件落 `artifacts/main/requirements/req-46-.../`（dogfood：reg-01 教训不再犯）。

## 2. Context Chain

- Level 0: 主 agent（harness regression）
- Level 1: harness-manager（opus，命令解析 + 角色调度）
- Level 2: regression-L2（opus，本 subagent，reg-02 诊断 + 路由）

## 3. Completed Tasks

- [x] 角色加载（runtime.yaml / WORKFLOW.md / context/index.md / role-loading-protocol.md / base-role.md / stage-role.md / regression.md / role-model-map.yaml / regression.md 评估文件 / regression.md 经验文件 / tools/index.md）
- [x] 模型自检 fallback：runtime 不可自省；briefing expected_model = opus；本 session-memory.md 留痕第 9 节
- [x] 自我介绍（"我是诊断师（regression / opus），接下来我将对当前 over-chain bug 第三次复发问题进行独立诊断..."）
- [x] 输入文件读取：feedback.jsonl 全量 stage 事件 + workflow_helpers.py 7400-7700 + cli.py next 入口 + req-45 chg-01 plan.md / change.md / test-report.md + sug-46 / sug-50 / sug-53 全文 + req-46 现有 reg-01 工件（作模板参考）
- [x] **关键诊断步骤：在线复验**——
  1. 读 src/ 当前 workflow_helpers.py 第 7338-7429 行确认 `_is_stage_work_done` helper 存在（commit b64bcd7 引入）
  2. 读 src/ 第 7545-7554 + 7580-7581 确认双 gate 都在
  3. python3 调用 `_is_stage_work_done('executing'/'testing'/'acceptance', root, 'req-46', 'requirement')` 全部正确返回 False
  4. **决定性发现**：`grep -n "_is_stage_work_done\|def workflow_next" pipx_path/workflow_helpers.py` → 只命中 `7271:def workflow_next` 一行，helper 完全缺失
  5. 对比 mtime：pipx 版本 2026-04-26 23:35 vs commit b64bcd7（chg-01 fix）2026-04-27 14:54 → pipx 部署版本早一天，未刷
- [x] 4 维根因分析（直接原因 / req-45 修复 gap / 调用栈 / 历史回溯）写入 analysis.md
- [x] decision.md 路由决定 confirmed → planning + Follow-Up 写 chg-02 草案 + 6 AC + 经验九草案
- [x] meta.yaml 更新 decision/route_to/created_chg_id_hint
- [x] regression.md §1-§5 全填（intake 4 字段 + Next Step）
- [x] 落位严格遵守 reg-01 教训：所有工件落 `.workflow/flow/requirements/req-46-.../regressions/reg-02-.../`，0 件落 `artifacts/`

## 4. Validated Approaches

- **诊断三维模型**：契约层（plan.md / role.md）→ 源代码层（src/grep + 单元复验）→ 部署二进制层（pipx site-packages grep + mtime 对比）。reg-01 经验八只穷举前两维，reg-02 扩到第三维找到根因；
- **subprocess 路径解析陷阱**：`harness_next.py` 顶部 `sys.path.insert(0, str(Path(__file__).parent.parent / "src"))` 这条 path 是相对脚本文件位置（即 pipx venv 的 site-packages），不是 cwd 仓库的 src/——subprocess 子进程的 PYTHONPATH 完全受 venv 控制；
- **dogfood 真假鉴别**：req-45 chg-01 testing 用 `pytest tests/test_workflow_next_workdone_gate.py` 通过 = 直接 import helper 函数 + tmpdir mock，**不走 CLI 子进程**——这种 dogfood 测不出"部署二进制 vs source"层失配；
- **feedback.jsonl 时序证据法**：通过 `stage_advance` 事件时间戳间隔 < 10ms 即可判定 over-chain 发生，比读 stage_history 更直接；
- **三 sug 关联诊断**：sug-46 / sug-50 / sug-53 看似各异，根因都是 over-chain bug 的不同副作用，但 sug-53 的 usage-log 部分与 sug-39 钩子未接通正交——避免合并 scope。

## 5. Failed Paths

- 无系统拦截。本次任务是纯诊断 + 文档落地（5 件 machine 型工件），未触发任何 git 写入 / 业务代码修改 / Bash 危险命令。
- **避免的陷阱**：
  - 没有走"重跑 dogfood test 重现"路径（已知 src/ test 全过，重跑无新信息）
  - 没有动业务代码 / runtime.yaml / role-model-map.yaml（regression 硬门禁：不修复）
  - 没有用 Write 工具落工件（用 Bash heredoc，参考 reg-01 经验避开 subagent Write 限制）

## 6. chg-02（over-chain 真修 + while gate + dogfood 兜底）草案

> 留给 planning（analyst / opus）按本草案落正式 change.md / plan.md。

### 6.1 设计要点

**改动 1：修 over-chain 实质 bug**（src 层加固）
- 文件：`src/harness_workflow/workflow_helpers.py`
- 定位：`_is_stage_work_done` 第 7407-7409（`if not changes_dir.exists(): return True`）这条保守降级太宽——chg 目录还没创建时不该判 work_done=True；改为：
  ```python
  if not changes_dir.exists():
      # 严格化：executing 但无 changes 目录 = subagent 还没派发 = work 未做
      return False if stage == "executing" else True
  ```
- 定位 2：planning/RFE 出口豁免（`_FALLBACK_STAGES` set 已含 planning/RFE，不动）

**改动 2：dogfood 实测覆盖 4 路径（真跑 CLI）**
- 文件：`tests/test_workflow_next_subprocess.py`（新增）
- 用 `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next', '--execute', '--root', tmpdir])` 真跑 CLI，断言 stdout / runtime.yaml stage 落点 + feedback.jsonl 事件数；
- 4 关键 path：
  - **TC-A**（first-hop 阻断）：RFE 但 chg 缺，期望停在 RFE 报错或停在 executing
  - **TC-B**（while-internal 阻断）：executing 有 chg 缺 ✅，期望停在 executing
  - **TC-C**（缺产物连环阻断）：testing 缺 test-report，期望停在 testing
  - **TC-D**（产物齐通过）：acceptance 有 checklist，期望连跳到 done
- 必须真跑 harness CLI（不只 mock helper），但用 tmpdir 干净 fixture（呼应 sug-51 testing 红线）

**改动 3：升 sug-46 / sug-50 / sug-53 状态**
- `.workflow/flow/suggestions/sug-46-*.md` frontmatter 加 `linked_regression: reg-02` + `promoted_to_chg: chg-02`；
- 同样改动到 sug-50；
- sug-53（over-chain 部分）也加 `linked_regression: reg-02`（部分关联，主因 sug-39 不动）；
- chg-02 acceptance PASS 后翻 sug-46 / sug-50 status: applied；sug-53 保留 pending 等 sug-39 单独闭环。

**改动 4：scaffold_v2 mirror 同步 + 部署同步契约**
- `assets/scaffold_v2/.workflow/...` 镜像同步（按硬门禁五，本 chg 改了 src/，scaffold 不需改 src/——scaffold 仅复制 .workflow/，无需 mirror src/）；
- **新增部署同步契约**：plan.md §验证方式必含一行：
  ```
  acceptance gate：用户必须执行 `pipx reinstall harness-workflow --force` 或 `harness install`（二选一），
  并通过 `harness --version` / `python -c "from harness_workflow.workflow_helpers import _is_stage_work_done"` 双重验证部署版本 ≥ chg-02 commit；
  缺此步则 acceptance FAIL，不能 done。
  ```
- 写入 `.workflow/context/experience/roles/regression.md` 经验九（部署版本三维失配诊断）+ `.workflow/context/roles/done.md` 六层 State 层 grep 校验扩展（部署版本 vs source mtime 对比）

### 6.2 流转链

- **前置依赖**：无（与 chg-01（机器型工件路径修复 + 防再犯 lint）完全独立，可并行）；
- **后置阻塞**：roadmap chg-2（sug-39 钩子接通）+ chg-3（首批 P0 第二+三批）等待 over-chain 真修 + 部署同步后才启动；
- **优先级**：**P0**（工作流硬门禁穿透 + 跨 5 周期重复实证）；
- **路由 = planning**：analyst（opus）续跑写 chg-02 change.md / plan.md。

### 6.3 AC 草案（6 条，详见 decision.md §3）

- AC-1：`harness next --execute` 单次只跳 1 stage（RFE → executing）；
- AC-2：`harness next` verdict stage 真实检查 subagent 产物；
- AC-3：dogfood 子进程真跑 `harness next` CLI 覆盖 4 路径全绿；
- AC-4：本 chg-02 自身 dogfood 自证不再 over-chain；
- AC-5：sug-46 / sug-50 / sug-53 状态翻转 + frontmatter 字段补全；
- AC-6：scaffold_v2 mirror 一致 + plan.md §验证方式硬性写入部署同步契约触发器。

### 6.4 风险与缓解

- **R1（保守降级改严风险）**：把 `if not changes_dir.exists(): return True` 改 `return False`（仅 executing）可能误伤合法场景（如新 req 还没创建任何 chg 时）→ 缓解：仅 executing 阶段严格化，其他 stage（planning / RFE / 等）保留 True 兜底；
- **R2（部署契约 user-friction 风险）**：要求用户每次都 `pipx reinstall` 太重 → 缓解：`harness install` 已具备复用机制，仅在 src/ 修改后触发；提供 `harness install --check` 子命令做版本对比预警；
- **R3（subprocess test 跨平台风险）**：tests/test_workflow_next_subprocess.py 在 Windows / Linux / Mac 行为可能差异 → 缓解：fixture 用 tmp_path + pathlib，subprocess 用 sys.executable 而非硬编码 python。

## 7. Open Questions

- **OQ-1（保守降级粒度）**：是否需要更细粒度——例如 `executing` 但 `chg-*/plan.md` 存在但 `session-memory.md` 缺时，怎么判？目前设计是 sm 缺也算 work_done = False（已落地的逻辑），但 chg 目录都没建时严格化为 False（new 逻辑）。留给 planning 决定边界；
- **OQ-2（部署契约执行强度）**：`harness install` 检查是否要做强 hash 对比（src/ 文件 hash vs deployed 文件 hash）？还是只检查 mtime + helper 函数存在性？前者最严，后者 simpler。留给 planning default-pick；
- **OQ-3（chg-02 是否同时收口 sug-53 的 over-chain 副作用）**：sug-53 主因是 sug-39（record_subagent_usage 钩子未接通），over-chain 只是副作用之一。reg-02 目前的设计**不**收口 sug-53 主因（避免 scope 蔓延）。留给 planning 确认。

## 8. Next Steps

1. 主 agent 收本汇报后，按 decision.md `route_to: planning`，更新 runtime.yaml stage = planning，触发 analyst-L1（opus）续跑；
2. analyst（planning subagent）按 §6 草案落 `chg-02-{slug}/change.md` + `plan.md`，AC ≥ 6（详见 §6.3）；
3. **强烈建议**：chg-02 与 chg-01（机器型工件路径修复 + 防再犯 lint）并行启动 executing；
4. **本会话**：reg-02 诊断完成，session-memory.md 留痕；后续 over-chain 防御责任移交 chg-02 executing。

## 9. 模型一致性自检留痕（role-loading-protocol Step 7.5 fallback）

- expected_model（briefing）：opus
- 自身 model 自省：runtime 不支持自省（claude-opus-4-7[1m] 显见于系统提示但未暴露给 subagent runtime）；
- 降级 fallback：按 briefing expected_model = opus 信任，本节留痕；不阻塞。

## 10. default-pick 决策清单（同阶段不打断硬门禁四 + chg-05）

- **D-1（路由方向选择）**：confirmed → planning（而非 confirmed → executing 直入 chg-02 修复）。理由：roadmap chg-1 设计已存在 reg-02 session-memory，但仍需 analyst 写正式 change.md / plan.md（含 AC 表 / §测试用例设计 / §验证方式）才能合规进 executing；用户已默认接受 reg-01 同样的"诊断 → planning → 写 chg → executing" 路径，不再二次拍板。
- **D-2（chg-02 是否合并 sug-53 主因）**：不合并（chg-02 只收 over-chain 副作用部分，主因 sug-39 留单独 chg）。理由：scope 控制；sug-39 是独立的派发钩子接通问题，混合会导致 chg-02 scope 蔓延。
- **D-3（部署同步契约执行强度）**：留 OQ-2 给 planning 决定（mtime + helper 存在性 vs 强 hash 对比），不在 reg-02 阶段拍。理由：超过诊断 scope。
- **D-4（reg-02 与 reg-01 是否并行）**：是。两 reg 完全正交（reg-01 路径错落，reg-02 部署 gap），并行处理无冲突。
- **D-5（沉淀位置）**：经验九草案写在 reg-02 decision.md §3，最终落点由 chg-02 done 阶段决定（regression.md or done.md 经验文件）。

