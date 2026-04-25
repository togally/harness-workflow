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
