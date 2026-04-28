# Regression Intake — reg-02（over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done）— sug-46/-50/-53 同根因复发）

## 1. Issue Title

over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done）— sug-46（sug-38（harness next over-chain bug）升 P0：req-44 二次实证）/ sug-50（chg-01 gate gap：第一格修了但 while 循环内 gate 缺失）/ sug-53（req-45 done 六层 State 层校验：usage-log.yaml 仍缺）同根因复发

## 2. Reported Concern

req-46（建议池梳理验证 + 优先级 roadmap + 分批落地） 周期内 `harness next --execute` 第三次实证 over-chain bug：单次调用 4 跳跨 ready_for_execution → executing → testing → acceptance → done，跳过 executing/testing/acceptance 三个 stage 的 subagent 工作。req-45（harness next over-chain bug 修复（紧急））chg-01（verdict stage work-done gate + workflow_next 集成）声称已修双 gate（首格 + while 循环内），dogfood test PASS（9/9 + tmpdir mock），但本次实证仍发生。三次同根因实证（sug-46 / sug-50 / sug-53 各为 req-44 / req-45 chg-01 dogfood / req-45 done State 三个不同 stage 节点的复发证据），强烈表明**实际部署的 CLI 二进制与 source 修复脱钩**。

## 3. Current Behavior

- **本次实证**（feedback.jsonl 09:25:35.78）：5 条 stage_advance event 在 4ms 内连续发出——`ready_for_execution → executing` / `executing → testing` / `testing → acceptance` / `acceptance → done`，stage_duration 全部 0.001~0.005s（明显机器自动跳，无 subagent 工作产物落地）
- **历史复发**：
  - 02:00:28：第二次（同 req-46 周期，RFE→done 5ms）
  - 14:18:29（昨日）：第一次（req-46 RFE→executing 进入正常）
  - 06:49:32 + 07:03:22：第三+四次 testing→acceptance→done 跳（短链）
- **手工 workaround**：每次发生后由人工 `Edit .workflow/state/runtime.yaml` 把 stage 滚回正确格再派发 subagent；本会话内累计执行 ≥ 5 次，已触发 sug-46 / sug-50 / sug-53 三次升 P0 凭证。
- **复现路径**：从 `ready_for_execution`（任意 req）执行 `harness next --execute`，且 `executing` 阶段 subagent 工作未落地（chg session-memory 缺 ✅）→ 期望停在 executing，实测 4 跳到 done。

## 4. Expected Outcome

- `harness next --execute` 单次只跳 1 stage（RFE → executing），其余 3 stage 应被 work-done gate 阻断；
- gate 阻断时 stderr 输出 `Stage executing 工作未完成，请先完成当前阶段工作再推进。`，rc=0；
- runtime.yaml 落点应停在 `executing`，subagent 派发后 `executing → testing` 由 subagent 完成 ✅ 标记后再触发；
- 本会话内不再出现需要手工 Edit runtime 兜底的场景。

## 5. Next Step

- 路由 confirmed → planning：写 chg-02（over-chain 真修 + dogfood 兜底加固）；与 chg-01（机器型工件路径修复 + 防再犯 lint）并行执行；
- 不直接动业务代码（regression 角色仅诊断，不修复）；
- 关键诊断结论：**source 层 req-45 chg-01 修复存在但 pipx 部署版本未同步**（详见 analysis.md §3 调用栈），chg-02 必须把"修复 + 部署同步契约"一并交付。
