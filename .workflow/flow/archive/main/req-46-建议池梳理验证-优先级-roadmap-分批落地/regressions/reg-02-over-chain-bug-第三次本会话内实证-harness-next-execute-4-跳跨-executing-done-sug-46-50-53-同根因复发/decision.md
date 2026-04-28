---
# bugfix-3: diagnostician fills the next-stage routing here.
# reg-02 路由：planning（让 analyst 续跑写 chg-02 change.md / plan.md）
route_to: "planning"
---

# Regression Decision — reg-02（over-chain bug 第三次本会话内实证（harness next --execute 4 跳跨 executing→done）— sug-46/-50/-53 同根因复发）

## 1. Decision Status

- `confirmed`

**判定理由**：见 analysis.md §1 + §2.1 / §2.2 / §2.4。

- 五次跨周期/会话内实证（sug-38 → sug-46 → sug-50 → sug-53 + 本会话内 4 次 over-chain）已构成不可辩驳的证据链；
- 部署版本 vs source 不一致是**真实 root cause**——pipx site-packages 下 `workflow_helpers.py` 无 `_is_stage_work_done` helper（grep 验证无命中），mtime 早于 chg-01 修复 commit；
- 不是误判（multi-witness 重现）/ 不是预期不一致（user 期望 work-done gate 阻断）/ 不是用法理解错（用法符合 plan.md 设计）。

## 2. Final Notes

### 为何"已修复声明"和"现场实证"打架

req-45（harness next over-chain bug 修复（紧急）） chg-01（verdict stage work-done gate + workflow_next 集成） test-report.md 9/9 PASS + dogfood tmpdir mock PASS 是**真实有效的**——但都是**直接调用 `from harness_workflow.workflow_helpers import _is_stage_work_done`** 测的源代码层 helper。

实际 `harness next` CLI 是经 pipx 安装的 site-packages，subprocess 进入子进程后 PYTHONPATH 解析到 venv 路径（不是当前仓库 src/）。**testing 阶段从未真跑 `harness next` 子命令并断言 over-chain 不发生**——dogfood 设计盲点。

### 三 sug 同根因关联说明

- **sug-46（req-44 二次实证）**：当时 chg-01 都还没立项，pipx 部署版本就是 over-chain 版本——属第一阶段证据；
- **sug-50（chg-01 gate gap）**：直觉判断"while 循环内 gate 缺失"，源代码层错判（while gate 实际存在 line 7580）；本质是部署版本没刷——sug-50 是部署 gap 的二次证据；
- **sug-53（usage-log 缺失）**：over-chain → stage 跳过 → subagent 没派发 → record_subagent_usage 没触发——over-chain 副作用之一，但与 sug-39 钩子接通问题正交，**不并入 chg-02 scope**（避免 scope 蔓延）。

### 与既有 sug 池的处理

- **sug-46** + **sug-50** 升 P0 + 标 `linked_regression: reg-02` + `promoted_to_chg: chg-02`（chg-02 落地后翻 status: applied）；
- **sug-53**（usage-log 部分）保留 medium；其 over-chain 副作用部分由 chg-02 间接消解，但 sug-39 主因不动；
- **sug-38** / **sug-40**：保留 pending，等 chg-02 acceptance PASS 后整体翻 archived。

## 3. Follow-Up

### chg-02 概要

**chg-02 名（≤ 15 字）**：`over-chain 真修 + while gate + dogfood 兜底`

**改动 4 项**（详见 session-memory.md §chg-02 草案）：
1. **修 over-chain 实质 bug**：在 source 层加保守降级修正（`changes_dir not exists` 时不再无脑返回 True，而是返回 False 阻断；planning/RFE 出口豁免）；
2. **dogfood 实测覆盖 4 路径**：unit + integration test **直接子进程跑 harness CLI**（不是 mock helper），覆盖 first-hop / while-internal / 缺产物 / 有产物；
3. **升 sug-46 / sug-50 / sug-53 状态**：frontmatter 加 `linked_regression: reg-02` + `promoted_to_chg: chg-02`；chg-02 acceptance PASS 后 sug-46 / sug-50 翻 applied；
4. **scaffold_v2 mirror 同步**（按硬门禁五）+ **部署同步契约**（plan.md §验证方式必含 `pipx reinstall` / `harness install` 之一作为 acceptance gate）。

### chg-02 流转

- **前置依赖**：无（与 chg-01（机器型工件路径修复 + 防再犯 lint）完全独立，可并行）；
- **后置阻塞**：roadmap chg-2（sug-39 record_subagent_usage 钩子接通）/ chg-3（roadmap 首批 P0 第二+三批） 等待 over-chain 真修 + 部署同步后才启动——避免后续 chg 也踩 over-chain；
- **优先级**：**P0**（工作流硬门禁穿透 = 任何后续 chg 都被影响 + 跨 5 周期重复实证）；
- **路由 = planning**：让 analyst 续跑写 chg-02 的 change.md + plan.md（roadmap chg-1 的设计已存在 reg-02 session-memory，analyst 把内容落到 chg-02 文档）。

### chg-02 AC 草案（≥ 6 条）

- **AC-1**：`harness next --execute` 单次只跳 1 stage（RFE → executing），其余 stage 由 work-done gate 阻断；
- **AC-2**：`harness next` 在 verdict stage 真实检查 subagent 产物（缺则 ABORT 并 stderr 输出明确诊断信息）；
- **AC-3**：dogfood 测试**子进程真跑 `harness next` CLI**，覆盖 4 路径全绿（first-hop / while-internal / 缺产物 / 有产物）；
- **AC-4**：本 chg-02 自身 dogfood 自证（chg-02 走 workflow 时不再发生 over-chain，stage_advance 事件流符合 stage_policies）；
- **AC-5**：sug-46 / sug-50 / sug-53 状态翻转（promoted_to_chg / linked_regression frontmatter 字段补全）；
- **AC-6**：scaffold_v2 mirror diff 一致 + plan.md §验证方式硬性写入 `pipx reinstall harness-workflow --force`（或 `harness install`，二选一）作为部署同步契约触发器，acceptance 阶段必查。

### 经验沉淀（regression.md 经验八扩展）

**经验九草案：契约层 vs 源代码层 vs 部署二进制层 三维失配诊断模板**

经验八（契约层 vs 实现层失配诊断）穷举二维矩阵；reg-02 表明应扩到三维：

| 维度 | 检查方式 | 失配症状 |
|------|---------|---------|
| 契约（自然语言文档） | 读 role.md / WORKFLOW.md | 行为说明 vs 实际行为对不上 |
| 源代码层（src/） | grep + 单元测试 | helper 缺失或逻辑错 |
| 部署二进制层（pipx / npm / docker） | grep 部署路径 + mtime + 在线 CLI 行为对比 | helper 在 src/ 存在但 deploy 缺失 |

**修复模式新增**：dogfood 必须**子进程真跑 CLI 命令**，不能只调 helper 函数（mock helper 测不出部署 gap）。沉淀位：`.workflow/context/experience/roles/regression.md` 经验九（chg-02 done 阶段沉淀）。

