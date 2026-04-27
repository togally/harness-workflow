# Regression Analysis — reg-02（over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done）— sug-46/-50/-53 同根因复发）

> 诊断师：regression（regression / opus）
> 诊断日期：2026-04-27
> 隶属：req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）
> 关联前作：req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）

## 1. Problem Assessment

**判定**：**真实问题（confirmed）**。三次跨周期实证（sug-46 / sug-50 / sug-53）+ 一次本会话第三次实证（feedback.jsonl 09:25:35.78 4 跳事件链）+ 一次本诊断在线复现验证（pipx 二进制无 `_is_stage_work_done` helper），已构成充分证据链，**不是误判，不是预期不一致**。

req-45 chg-01 修复声称已落地（commit b64bcd7 / 2026-04-27 14:54:13），test-report.md 标 9/9 PASS + dogfood gate tmpdir mock 验证通过；但**实际运行的 `harness next` CLI 仍走 over-chain 路径**——根因在调用栈而非门禁逻辑本身。

## 2. Evidence

### 2.1 现场实证（本会话内三次复发）

读取 `.workflow/state/feedback/feedback.jsonl`，过滤本会话相关事件（2026-04-27）：

| 时间戳 | 事件链 | 总耗时 | 解读 |
|--------|-------|--------|------|
| 02:00:28.576 ~ 02:00:28.585 | RFE → executing → testing → acceptance → done | **9 ms** | 第二次实证：5 条 stage_advance 几乎同时发出，executing/testing/acceptance 全部 0.001~0.005s |
| 06:49:32.548 ~ 06:49:32.553 | testing → acceptance → done | **5 ms** | 第三次实证（短链）：testing 完成后 acceptance/done 全跳 |
| 07:03:22.724 ~ 07:03:22.728 | testing → acceptance → done | **4 ms** | 第四次实证（短链） |
| **09:25:35.779 ~ 09:25:35.787** | **RFE → executing → testing → acceptance → done** | **8 ms** | **第五次实证（4 跳完整链）：本次 reg-02 触发，最完整证据** |

**reg-02 诊断聚焦的 09:25 事件链原始证据**（feedback.jsonl 第 -10 ~ -1 行）：
```
{"ts": "2026-04-27T09:25:35.779239+00:00", "event": "stage_duration", "data": {"stage": "ready_for_execution", "duration_seconds": 2618.43}}
{"ts": "2026-04-27T09:25:35.780017+00:00", "event": "stage_advance", "data": {"from_stage": "ready_for_execution", "to_stage": "executing"}}
{"ts": "2026-04-27T09:25:35.783899+00:00", "event": "stage_duration", "data": {"stage": "executing", "duration_seconds": 0.003755}}
{"ts": "2026-04-27T09:25:35.784002+00:00", "event": "stage_advance", "data": {"from_stage": "executing", "to_stage": "testing"}}
{"ts": "2026-04-27T09:25:35.785594+00:00", "event": "stage_duration", "data": {"stage": "testing", "duration_seconds": 0.001504}}
{"ts": "2026-04-27T09:25:35.785829+00:00", "event": "stage_advance", "data": {"from_stage": "testing", "to_stage": "acceptance"}}
{"ts": "2026-04-27T09:25:35.787305+00:00", "event": "stage_duration", "data": {"stage": "acceptance", "duration_seconds": 0.001391}}
{"ts": "2026-04-27T09:25:35.787389+00:00", "event": "stage_advance", "data": {"from_stage": "acceptance", "to_stage": "done"}}
```

### 2.2 部署一致性核查（本次诊断关键发现）

| 路径 | mtime | 关键 helper `_is_stage_work_done` | gate 行号 |
|------|-------|--------------------------------|----------|
| `src/harness_workflow/workflow_helpers.py` | 当前（commit d8237fe 后） | **存在**（line 7338-7429） | 7548（first-hop）+ 7580（while 内） |
| `~/.local/pipx/venvs/harness-workflow/lib/python3.14/site-packages/harness_workflow/workflow_helpers.py` | **2026-04-26 23:35:05**（pipx install 时点） | **缺失**（grep 无命中） | 无 |

`grep -n "_is_stage_work_done\|def workflow_next" pipx_path` 输出：
```
7271:def workflow_next(root: Path, execute: bool = False) -> int:
```
**只命中 workflow_next 一行**——`_is_stage_work_done` helper 在 pipx 二进制中**完全不存在**。

行数对比：
- src/: 8079 行（含 chg-01 修复）
- pipx/: 7894 行（修复前，少 185 行——刚好覆盖 helper + 双 gate + validate_contract 分支）

### 2.3 修复时间线时序错位

| 事件 | 时间戳 | 备注 |
|------|--------|------|
| pipx 当前部署版本 build 时间 | 2026-04-26 23:35:05 | mtime 对应 |
| req-45 chg-01 修复 commit b64bcd7 落地 | 2026-04-27 14:54:13 | 实际写入 src/ 时间 |
| req-45 archive commit d8237fe | 2026-04-27 14:55+ | 写 done-report 后 |
| 本 reg-02 触发（09:25 over-chain）| 2026-04-27 09:25:35 | **早于 chg-01 commit**——这次 over-chain 时甚至 chg-01 都还没合并 |

**修正解读**：09:25:35 实证 **本身就是 chg-01 修复合并之前的 dogfood**。但即使现在（22:09）已 commit b64bcd7，pipx 部署版本仍未刷新——下次任何 `harness next --execute` 仍走 over-chain。

### 2.4 在线复验

通过 Python 直调 src 模块执行 gate 函数：
```python
_is_stage_work_done('executing', Path('.'), 'req-46', 'requirement') == False
_is_stage_work_done('testing',   Path('.'), 'req-46', 'requirement') == False
_is_stage_work_done('acceptance',Path('.'), 'req-46', 'requirement') == False
```

→ src 层 helper 工作正常，gate 应当阻断；CLI 实际运行的 pipx 版本无此 helper，over-chain 直接发生。

## 3. Recommended Action — 根因 4 维 + 调用栈 + req-45 修复 gap 定位

### 3.1 直接原因（"`harness next --execute` 单次为何 4 跳？"）

**调用栈**：
```
$ harness next --execute
  → /Users/jiazhiwei/.local/bin/harness  (pipx shim)
  → /Users/jiazhiwei/.local/pipx/venvs/harness-workflow/.../bin/harness  (entrypoint)
  → cli.py:main → cli.py:511 args.command == "next"
  → _run_tool_script("harness_next.py", ["--execute"], root)
    → subprocess.run([python, tools/harness_next.py, --execute, --root .])
      → harness_next.py:13 from harness_workflow.workflow_helpers import workflow_next
      ⚠️ 这里 import 的是 pipx site-packages 下的 OLD workflow_helpers.py
      → workflow_helpers.py:7271 (PIPX 旧版！) workflow_next(root, execute=True)
        → 进入连跳 while 循环（无 _is_stage_work_done 检查）
        → 一次性 advance 4 格到 done
```

**核心机制**：subprocess 子进程的 PYTHONPATH 受 pipx venv 控制；`harness_next.py` 顶部 `sys.path.insert(0, str(Path(__file__).parent.parent / "src"))` 这条 path 注入指向**当前文件所在 venv 的 src/**（即 pipx venv 的 site-packages 路径），而**不是**当前 cwd 的 `/Users/jiazhiwei/claudeProject/harness-workflow/src/`。所以 src/ 修复对 pipx 部署完全不生效。

### 3.2 req-45 chg-01 修复 gap 定位（"commit b64bcd7 改了哪两个 gate？本次哪个 gate 没拦住？"）

**chg-01 实际改动**（plan.md §3 Step 1-2 + b64bcd7 diff）：
1. **新增 helper** `_is_stage_work_done(stage, root, req_id, op_type)` → workflow_helpers.py 7338-7429
2. **第一格 gate**（first-hop） → workflow_helpers.py 7545-7554：
   ```python
   if (_first_hop_exit in _AUTO_JUMP_DECISIONS  # auto/verdict
       and not _first_hop_same_role
       and not _is_stage_work_done(current_stage, root, op_target, op_type)):
       print("Stage X 工作未完成", file=stderr)
       return 0
   ```
3. **while 循环内 gate** → workflow_helpers.py 7580-7581：
   ```python
   if no_user_decision and not same_role and not _is_stage_work_done(from_s, root, op_target, op_type):
       break
   ```

**两个 gate 在 src 层都存在且行为正确**（在线复验 §2.4 全通过）。但本次 over-chain 不是因为 gate 漏检，而是 **gate 整段代码不在运行时二进制里**——pipx 部署的是 2026-04-26 23:35（修复前一天）的版本。

**真正的 gap**：**没有"修复 commit ↔ 用户机器实际运行版本"的同步契约**。req-45 chg-01 的 testing 用 `pytest tests/test_workflow_next_workdone_gate.py` 跑直接调用 `from harness_workflow.workflow_helpers import _is_stage_work_done`——pytest 用的是 src/ 版本，**和实际 `harness next` CLI 走的 pipx 版本不是同一个二进制**。dogfood "tmpdir mock" 也是直接调 helper 函数，不走 CLI 子进程，所以测试链条没有覆盖 "CLI 实际部署版本" 这个维度。

### 3.3 执行路径完整性（调用栈标 gate 应在位置）

```
[harness next --execute] (用户输入)
    │
    ▼
/Users/jiazhiwei/.local/bin/harness  ← pipx shim
    │
    ▼
cli.py::main → cli.py:511 args.command == "next"
    │
    ▼
_run_tool_script("harness_next.py", cmd_args, root)  ← 进 subprocess
    │
    ▼ (新进程)
harness_next.py:23 workflow_next(root, execute=True)
    │
    ▼
workflow_helpers.py::workflow_next
    │
    ├─ pending gate (line 7437-7446) ← 检查 stage_pending_user_action
    │
    ├─ regression route gate (line 7467-7470) ← reg 路由覆盖
    │
    ├─ ready_for_execution + not execute (line 7479) ← --execute flag 检查
    │
    ├─ ★ FIRST-HOP GATE (line 7545-7554) ← 应在位置 ★
    │   condition: exit ∈ {auto, verdict} && !same_role && !work_done
    │   ⚠️ 当前 RFE→executing 时 RFE.exit=explicit，gate **不命中第一格**（设计如此）
    │
    ├─ _write_stage_transition(RFE, executing) ← 第一格写入
    │
    ▼ (进 while 循环)
while walk_idx >= 0 and walk_idx + 1 < len(sequence):
    │
    ├─ exit=explicit → break （RFE 不会进 while，因为已经第一格）
    │
    ├─ for from_s=executing: exit=auto, !same_role, no_user_decision=True
    │   ★ WHILE GATE (line 7580-7581) ← 应阻断 executing→testing 跳跨 ★
    │   condition: no_user_decision && !same_role && !work_done
    │   src/ 该 gate 存在并工作；pipx/ 该 gate 不存在 → 直跳
    │
    ├─ for from_s=testing: 同上 → 应阻断 testing→acceptance
    │
    ├─ for from_s=acceptance: exit=verdict, no_user_decision=True
    │   ★ WHILE GATE 应阻断 acceptance→done ★
    │   src/ 工作；pipx/ 缺失 → 直跳到 done
```

**结论**：4 个潜在 gate 检查点（first-hop + 3 个 while 内），src/ 都覆盖，pipx/ 都缺失。

### 3.4 历史回溯（"sug-46 / sug-50 / sug-53 三次实证后未真正修，本次第四次"）

| sug | 触发周期 | 实证内容 | 当前状态 | 与 reg-02 关系 |
|-----|---------|---------|---------|----------------|
| sug-38 | req-43 / req-44 cycle | 首次提出 over-chain bug | pending | 本 sug 升 P0 → req-45 立项修复 |
| sug-40 | req-43 cycle 末 | sug-38 meta-followup | pending | 同根因 |
| sug-46 | req-44 cycle 末 | req-44 cycle 二次实证 --execute → done | pending | sug-38 升 P0 凭证 |
| sug-50 | req-45 chg-01 dogfood 期 | 第一格修了但 while 内 gate 缺失 | pending | **本质问题**：源代码 while 内 gate 已写（line 7580），但**部署版本没刷新**——sug-50 现场判定为"实现 gap"，实际是部署 gap |
| sug-53 | req-45 done cycle | usage-log.yaml 缺失（State 层校验） | pending | 同 over-chain 影响：因 stage 跳过没派 subagent → 无 usage 采集 |
| **reg-02** | req-46 cycle | **第五次实证**（最完整 4 跳链 + 调用栈定位部署 gap） | analysis | 本次诊断 |

**升级判定**：
- sug-50 / sug-46 **应直接升 P0** 并标记 `linked_regression: reg-02`，作为部署 gap 的活体证据；
- sug-53 部分（State 层 usage-log 缺失）也部分相关——over-chain 跳过 stage → 无 subagent 派发 → 无 usage_record → done State 层校验缺失；与 sug-39（record_subagent_usage 派发钩子未接通）的根因是**正交**的，不应合并；
- 三 sug 的诊断都没穷举到"部署版本 vs source"维度——属于 **regression.md 经验八（契约层 vs 实现层失配诊断模板）的扩展案例**：从二维（契约/实现）扩到三维（契约/source 实现/部署 binary）。

## 4. Discussion Outcome

- 与主 agent 确认：reg-02 路由 `confirmed → planning`，写 chg-02（over-chain 真修 + dogfood 兜底加固 + **部署同步契约**），与 chg-01（机器型工件路径修复 + 防再犯 lint）并行；
- 用户已默认接受"本 req-46 内优先修 over-chain"路径（reg-02 briefing 明示）；
- chg-02 设计要点已写入 session-memory.md §草案，AC 6 条覆盖：source 层加固 + dogfood 真跑 CLI + 部署契约 + sug 状态翻转 + scaffold mirror + 自证 dogfood。

## 5. Recommended Action

**confirmed → planning 路由**：

1. **本 stage 退出**：诊断结论 + 路由决定写入 `decision.md`，同步 `meta.yaml` `decision: confirmed` / `route_to: planning` / `created_chg_id_hint: chg-02`；
2. **下一 stage**（planning，analyst / opus 接手）：把 session-memory.md §草案落正式 `chg-02-{slug}/change.md` + `plan.md`，AC 至少 6 条（详见 session-memory.md §chg-02 草案）；
3. **并行执行**：chg-02 与 chg-01（机器型工件路径修复）完全独立，分别进 executing 即可；
4. **修复落地后**强制：`harness install` / `pipx reinstall harness-workflow --force` 二选一作为同步契约触发器，写入 chg-02 plan.md §验证方式 + done 阶段六层 commit 校验。

