# 经验：分析师（analyst）

> 溯源：req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））/ chg-06（专业化反馈捕捉机制（analyst 首次运行抽检模板 + 退化回调 B））

## 首次运行抽检清单

每次 analyst 承接一个 req 完成 requirement + chg 拆分后，subagent / 用户在 session-memory.md 追加一条抽检记录。人工验证要点如下：

1. **合并后 chg 拆分质量**：合并后 analyst 独立完成 requirement_review + planning 的 chg 拆分质量是否不差于原两步流程（粒度合理、依赖分析完整、风险识别到位）；
2. **用户是否被不必要打扰**：需求澄清是否做到"一次性汇总"（争议点 + 推荐 + 可选项），没有在单个 req 内触发多轮打断；
3. **争议点是否清晰**：模糊点 / 潜在冲突是否在一次性汇报中明示，还是被 default-pick 静默吸收（default-pick 须在 session-memory 留痕）；
4. **escape hatch 路径是否可用**：用户触发"我要自拆"时，analyst 是否正确退化为"只出推荐，最终决定权归用户"；
5. **harness validate 执行**：两 stage 交接前是否各执行一次 `harness validate --human-docs` 且 exit code = 0。

## 回调 B 方向触发条件

若观察到以下任一具体退化判据，且连续 ≥ 2 个 req 抽检结果均为"C 明显退化"，建议触发 regression 回调方向 B（软合并 auto-advance 保留两 subagent）：

- **判据 1（chg 拆分粗糙）**：change.md 的"Scope / Acceptance"字段平均行数 < 原 planning 阶段基线的 50%，或依赖分析缺失（plan.md 无"Dependencies"段）；
- **判据 2（风险识别缺失）**：requirement.md 的"风险"节为空或只有 1 条泛化条目（如"实现复杂"），缺乏具体可操作缓解措施；
- **判据 3（用户被迫多次介入）**：单个 req 内用户修正 analyst 产物 ≥ 2 次（含"退回重写"、"补充遗漏依赖"、"重新拆分"类操作）。

触发路径：
```
harness regression --requirement "方向 C 退化，回调软合并 auto-advance 方向 B"
```
regression 阶段诊断师按 reg-01（planning 并入 requirement_review，用户只管需求确认，chg 拆分由 agent 自主）decision.md §2-3 四方向对比表重评估，产出新 decision.md。不自动回滚 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））角色合并产物；回滚动作由新 decision.md 决定。

## 样本记录模板

每个 req 完成后，在 session-memory.md 追加 `## analyst 专业化抽检反馈` 段，字段固定如下：

| 字段 | 说明 | 样例 |
|------|------|------|
| 抽检产物 | 被抽检的产物名（requirement.md / chg-NN/change.md / plan.md / 风险节 / 依赖节） | `req-41/chg-02/plan.md §3` |
| 质量评分 | A（明显优于原两步） / B（持平） / C（明显退化） | `B` |
| 退化点明细 | 若评分 C：列具体缺失或粗糙点，引用产物行号；A / B 可省略 | `依赖分析只有 2 句，原 planning 阶段平均 5 句` |
| 是否触发 regression 回调 B | 是 / 否；"是"即开 reg-NN 走 harness regression | `否` |
| 抽检人 + 时间 + req 范围 | 人名 / 日期 / 涉及 req id | `用户 / 2026-04-25 / req-41` |

### 首次抽检样本（req-40 自身）

- **抽检产物**：req-40 chg-01~chg-06 完整 change.md + plan.md 集；
- **质量评分**：B（持平）；
- **退化点明细**：（持平档，无需列举；轻微瑕疵：requirement.md 存在 5 处历史写入的首次裸 id 引用，属契约 7 legacy fallback 覆盖范围，不计入退化判据）；
- **是否触发 regression 回调 B**：否（留痕观察，下一真实用户 req 作为方向 C 首次真实活证）；
- **抽检人 + 时间 + req 范围**：chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）封存时间 2026-04-23 / req-40。

---

## 经验：planning §测试用例设计章节实操要点（bugfix-6 / B1 引入）

### 场景

req-id ≥ 41 起，analyst 在 planning stage 必须按 `Step B2.5` 在 `plan.md` 末尾追加 §4. 测试用例设计章节，覆盖**所有波及接口**对应的 AC 用例。lint `harness validate --contract test-case-design-completeness` 在 stage 流转前必跑。

### 经验内容

**判定波及接口的方法**：

1. **机器型起点**：`git diff --name-only HEAD..` 拿到当前 chg 的所有改动文件清单，作为"波及接口清单"骨架。
2. **人工补全调用链**：对每个改动文件，grep 跨模块 import / 跨模块函数调用，把所有"间接波及的接口契约 / 配置项 / CLI 子命令"补到清单。
3. **不漏 helper 改动**：如果改动是 helper 内部行为，要把"调用 helper 的所有上游入口"也列入波及（如 `_use_flow_layout` 改动 → `create_requirement / create_bugfix / create_change` 三个入口都波及）。

**用例粒度建议**：

- **每条 AC 至少 1 条 P0 用例**：覆盖正常路径；
- **每条 AC 至少 1 条 P0 反例**：覆盖关键失败路径（如 lint FAIL case / 路径冲突 case）；
- **波及接口的"对外契约边界"必须 P0**：如 `_use_flow_layout_for_bugfix(bugfix_id) -> bool` 的边界（bugfix-5 → False / bugfix-6 → True），属对外契约必 P0；
- **内部辅助函数走 P1 / P2**：纯实现细节（如字符串拼接 helper）不必每个分支都 P0，按风险加权。

**`regression_scope` 字段决策**：

- **default = targeted**：plan.md 段头默认写 `regression_scope: targeted`；
- **改 full 触发条件**：(a) 改动跨核心 helper（`workflow_helpers.py` / `cli.py` 的入口分发逻辑）；(b) 改动 lint 规则本身；(c) 改动状态格式（runtime.yaml / state yaml schema）；以上三类建议显式标 `full`；
- **bugfix 流程同款**：regression.md Step 4.5 在 bugfix 模式下产出的 diagnosis.md §测试用例设计 段同样使用 `regression_scope` 字段，语义一致。

### 反例

- 只列改动文件不列调用链 → testing 跑 targeted 后用户 acceptance 时发现"间接波及的接口"未被覆盖 → 二次 regression。
- 把所有用例都标 P0 → testing 时长膨胀 + 缺陷优先级判定混乱（什么都 P0 = 什么都不 P0）。
- 不写 `regression_scope` 字段 → testing subagent 默认按 targeted 跑但主 agent briefing 又写"全量回归" → 触发 sug-33（briefing 话术 lint）后置项识别的 over-instructing 反模式。

### 来源

bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））— B1 修复点（analyst.md Step B2.5 测试用例设计前移到 planning）+ bugfix-6 自身 diagnosis.md §测试用例设计 18 条用例样本（dogfood 活证）

---

## 经验：planning §测试用例设计 — 波及接口清单的多 chg 协同实操

### 场景

req 拆 ≥ 5 chg 时，每个 chg plan.md §测试用例设计段均需独立列「波及接口清单」，且互相之间存在数据通路 / helper 复用 / scaffold mirror 文件交叉。

### 经验内容

实操要点：

1. **波及接口清单必须含**：`workflow_helpers.py::{function}` 函数粒度（不是文件粒度）+ `.workflow/context/roles/{role}.md` §段粒度 + `scaffold_v2/...` mirror 文件路径列表 + suggestion / state yaml 等关联制品；
2. **跨 chg helper 共用 → regression_scope=targeted 仍有效**：req-43（交付总结完善）的 5 chg 共用 `record_subagent_usage` / `done_efficiency_aggregate` / `_sync_stage_to_state_yaml` 三个 helper，但每个 chg 在 §测试用例设计段独立列对应函数 → testing 角色（bugfix-6 B2 新契约消费侧）按 chg 粒度跑用例 = 39 条，targeted 跑后通过 5 项合规扫描即可保证回归覆盖；
3. **dogfood 用例（如 TC-06）必须落 §测试用例设计段**：req-43 chg-01 plan.md TC-06 = 「派发链路端到端 dogfood」，testing 实测发现 dogfood 失败（usage-log.yaml 未写入），由此暴露 L-01 followup → 转 sug-39（chg-01 派发钩子真实接通 record_subagent_usage）；若 dogfood 用例不落 plan.md，testing 阶段会漏判此问题。

### 反例

- 波及接口清单只列文件不列函数 → testing 跑覆盖时按文件粒度断言 → 同文件内的辅助函数被默认覆盖但实际未测，留下隐性回归窟窿。
- 多 chg 共用 helper 时省略 §测试用例设计段 → testing 阶段需要重新推断接口边界，违反 bugfix-6 B2 契约「testing 直接消费 plan.md 用例」精神。

### 来源

req-43（交付总结完善）— 5 chg plan.md §测试用例设计段 39 用例 + testing 阶段消费验证（test-report.md）

---

## 经验：小 scope req（单 sug 衍生 / bugfix 后遗症修复）默认拆 1-2 chg

### 场景

某条 sug 直接 apply 衍生为单 req，或某 bugfix 落地后留下少量后遗症 CLI 路径修复型 req（如 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）））。req scope 集中在少数几个 helper 或 CLI 子命令上，AC ≤ 5。

### 经验内容

analyst 拆分粒度判断要点：

1. **default-pick 拆 2 chg**：当 req 涉及 ≥ 2 个 CLI 子命令（如 apply / apply-all 一组 + rename 一组）或 ≥ 2 个独立 helper 模块时，默认按"模块物理分离 + 责任边界清晰"拆 2 chg；
2. **合 1 chg 风险**：单 commit 跨多模块 → 回归面过广 + revert 颗粒粗 + git log 颗粒度模糊；
3. **拆 3+ chg 风险**：当多个 chg 共用同源 helper 时（如 `_append_sug_body_to_req_md` 被 apply / apply_all 共用），硬拆增加测试隔离 fixture 重复 + 回归点漂移；
4. **AC 与 chg 不必 1:1**：req-44 5 个 AC 只拆 2 chg（chg-01 合 AC-01+AC-02 / chg-02 单承 AC-03 / AC-04 两 chg 各 no-op / AC-05 拆到 §测试用例设计），AC 是验收口径，chg 是实施口径；
5. **§测试用例设计 用例数底线**：每 chg ≥ 5 用例（覆盖 P0 核心 + P1 兼容 + 边界），小 scope req 总用例数 10-15 即可达到 AC-05"e2e 用例 ≥ 2 per 类"超额。

### 反例

- 把 sug-43（单点 abort bug）+ sug-44（rename 同步 bug）+ sug-45（apply 不真填）三 sug 强拆 3 chg → apply / apply_all 共用 helper 被硬拆到两 chg，测试同源 helper 时 fixture 重复；
- 三 sug 合 1 chg → 单 commit 同时改 apply / apply_all / rename 三函数 + 跨 helper 路径 + runtime 字段 → 回归面失控。

### 来源

req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） — 3 sug 衍生 5 AC，default-pick 拆 2 chg（chg-01 apply 合一 + chg-02 rename 单一），11 用例 + 4 反例 + 2 dogfood 全 PASS
