# Change

## 1. Title

专业化反馈捕捉机制（analyst 首次运行抽检模板 + 退化回调 B）

## 2. Goal

- 为 req-40 方向 C 落地后的首次真实运行（req-40 自身 executing 或紧随 req-40 的下一新 req）提供"专业化损失抽检模板"；把 AC-11 的质量评估从"口头要求"转为"留痕产物"；若抽检发现明显退化，提供明确的回调方向 B（软合并 auto-advance 保留两 subagent）触发路径。

## 3. Requirement

- `req-40`（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

## 4. Scope

### Included

- **新建** `.workflow/context/experience/roles/analyst.md`（若已存在则追加）：
  - "## 首次运行抽检模板（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））"段；
  - 字段清单（固定 5 字段）：
    1. **抽检产物**（requirement.md 澄清质量 / chg 拆分粒度 / plan.md 详细度 / 风险识别完整度 / 依赖分析深度 任选 ≥ 1）；
    2. **质量评分**（A 明显优于原两步 / B 持平 / C 明显退化）；
    3. **退化点明细**（若 C：列出具体缺失或粗糙点，引用具体产物行号）；
    4. **是否触发 regression 回调方向 B**（是 → 开 reg-02 走 `harness regression "方向 C 退化，回调软合并 auto-advance 方向 B"`；否 → 留痕观察）；
    5. **抽检人 + 抽检时间 + 抽检 req 范围**（如 req-40 / req-41）；
  - 首次抽检样本：req-40 本 chg executing 阶段或 chg-05 dogfood 结论可直接作为首次填写输入；
- **session-memory 留痕约定**：所有后续 analyst 派发后，subagent 交接时的 session-memory 新增 `## analyst 专业化抽检反馈`段（空则写"无"），字段对齐上述 5 字段；
- **回调方向 B 触发路径文字**（与 chg-03 technical-director escape hatch 并列，但属于**反向机制**）：
  - 在 `.workflow/context/experience/roles/analyst.md` 末尾追加一段 "## 方向 B 回调触发路径"：
    > 若连续 ≥ 2 个 req 抽检结果为 "C 明显退化"，建议开 reg-02 走 `harness regression --requirement "方向 C 退化，回调软合并 auto-advance 方向 B"`；regression 阶段诊断师按 reg-01（planning 并入 requirement_review，用户只管需求确认，chg 拆分由 agent 自主）decision.md §2-3 四方向对比表重评估。
- **mirror 同步**（experience 目录属硬门禁五保护面）：
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/analyst.md` 同步；
  - 注意：`.workflow/context/experience/` 下的 requirement-scoped 经验文件在白名单，但 `roles/` 子目录**不在**白名单（参考 harness-manager §硬门禁五例外清单），按保护面同步。
- 涉及文件路径：
  - live：`.workflow/context/experience/roles/analyst.md`（新建或追加）
  - mirror：`src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/analyst.md`

### Excluded

- **不改** analyst.md / harness-manager.md / technical-director.md / stage-role.md（分别归 chg-01 / chg-03）；
- **不新增** pytest（抽检模板是人机协作留痕，不做自动化断言）；
- **不触发** 实际的 regression（只提供触发路径文字，实际 regression 由用户 / technical-director 按抽检结果决定是否发起）；
- **不回滚** 方向 C（本 chg 只做反馈捕捉 + 提供回调路径，不自动回滚）。

## 5. Acceptance

- Covers requirement.md **AC-11**（专业化损失评估）：
  - `.workflow/context/experience/roles/analyst.md` 存在，含"首次运行抽检模板"段 + 5 字段清单；
  - req-40 executing 后，该文件含至少 1 条抽检样本（填入 chg-05 dogfood t4 结论或 req-40 自身的观察）；
  - 方向 B 回调触发路径在文件末尾有明示文字；
  - mirror diff 零：`diff -rq .workflow/context/experience/roles/analyst.md src/harness_workflow/assets/scaffold_v2/.workflow/context/experience/roles/analyst.md` 无输出；
  - `.workflow/state/sessions/req-40/session-memory.md` 含 `## analyst 专业化抽检反馈` 段（值为具体评分或"无（首次运行尚未观察到退化）"）。

## 6. Risks

- **风险 1：抽检模板沦为走过场，后续 req 无人填**。缓解：在 stage-role.md 的"经验文件加载规则"段追加一条提示（可选在 chg-03 协同；本 chg 若需则补一条注释行），让 analyst subagent 被加载时默认读取 experience/roles/analyst.md 抽检模板；减少遗忘概率。
- **风险 2：模板字段过多导致填写成本高 → 实际留痕字段被敷衍**。缓解：5 字段已经是最小集（产物 / 评分 / 退化点 / 回调 / 人时间），评分用 A/B/C 三档简化判断；退化点仅在 C 档填写，持平 / 优于档可省略。
- **风险 3：方向 B 回调路径与 reg-01 decision.md 冲突**。缓解：reg-01 已明示"方向 C 被用户选定"为最终决策；方向 B 回调是"方向 C 失败后的 fallback 路径"，不是否决 reg-01；回调需走正式 `harness regression` 新开 reg，不直接回滚。
- **风险 4：experience/roles/ 子目录 mirror 同步范围争议**。缓解：按 harness-manager §硬门禁五保护面明确——experience/roles/ 属通用角色经验（非 requirement-scoped），走 mirror 同步；与 white-list 中的 `requirement-scoped 经验文件` 区别对待。若 pytest test_scaffold_v2_mirror_drift 失败则回退。
- **风险 5：chg-06 被 chg-05 合并（seed default-pick D-2=A）但本 plan 推荐独立保留**。缓解：planning 决策已翻转 D-2 = B 独立保留（见 DAG 说明）；理由：AC-11 含"触发 regression 回调 B 方向"条件分支，与 chg-05 单向收束语义不同，独立归档更清晰。
