# Session Memory — req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ planning

## 1. Current Goal

Part B（planning）：基于修订后 requirement.md（吸收 uav bugfix-6（事件时间允许负值-人工提报放宽飞行记录校验）实证 + 4 条新洞察）拆 5 chg + 制定每 chg plan.md（含 §4 测试用例设计），交接 executing。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）→ stage = requirement_review（待自动转 planning）
- Level 1: 本 subagent（analyst / opus）→ task = req-49（trivial 通道）Part A 修订 + Part B 全量制定

## 3. Completed Tasks

### Part A：requirement.md 修订
- [x] 加 §2.3 实证活样本表（uav bugfix-6 数据：1 行 fix / 44 KB 文档 / 3+ 小时 / 30 分钟自评 6 倍超支）
- [x] §3.1 In-Scope 新增第 9-12 条（chg 级路径选择 + 主动识别 hint + 模板压缩 + 测试降级）
- [x] §4 验收标准新增 AC-N1 / AC-N2 / AC-N3 / AC-N4
- [x] §5.1 推荐 chg 拆分重构为 5 chg 新结构（chg-01 骨架 → chg-02 识别 → chg-03 模板 → chg-04 测试 → chg-05 dogfood）
- [x] 附录 A default-pick 清单新增 D-8 / D-9 / D-10 / D-11
- [x] `harness validate --contract artifact-placement` exit 0（PASS）

### Part B：planning（5 chg change.md + plan.md 全产出）
- [x] chg-01（trivial 通道命令骨架）change.md + plan.md（含 §4 / 15 用例 / regression_scope=full）
- [x] chg-02（trivial 准入判据 + 自动识别 hint）change.md + plan.md（含 §4 / 17 用例 / regression_scope=targeted）
- [x] chg-03（trivial 工件模板 + chg 级路径选择）change.md + plan.md（含 §4 / 13 用例 / regression_scope=targeted）
- [x] chg-04（trivial 测试降级 + trivial-guard 兜底护栏 + done 精简）change.md + plan.md（含 §4 / 17 用例 / regression_scope=full）
- [x] chg-05（dogfood + reviewer 加项 + 契约 lint 闭环）change.md + plan.md（含 §4 / 13 用例 / regression_scope=full）
- [x] 5 chg DAG 硬序：chg-01 → chg-02 → chg-03 → chg-04 → chg-05（线性）

## 4. Results

### 4.1 5 chg DAG 硬序结构

```
chg-01（trivial 通道命令骨架：CLI + state machine + harness-manager 路由）
   ↓
chg-02（trivial 准入判据 + 现有命令主动识别 hint）
   ↓
chg-03（trivial 工件模板 + chg 级路径选择 + 模板压缩）
   ↓
chg-04（trivial 测试降级 + trivial-guard 兜底护栏 + done 精简）
   ↓
chg-05（dogfood 活证 + reviewer 加项 + 契约 lint 闭环）
```

### 4.2 default-pick 决策清单（汇总 D-1 ~ D-11）

| 编号 | 决策点 | default-pick | 理由 |
|------|--------|--------------|------|
| D-1 | trivial 通道载体形态 | A. 新命令 `harness trivial` | 显式语义最清晰，与 4 类既有路径并列 |
| D-2 | trivial 准入判据 | D. 组合判据（行数 + 文件数 + 类型 + 影响面） | machine-checkable + 误判面最小 |
| D-3 | trivial_define 是否新设角色 | A. 复用 executing 角色 | 控制角色蔓延 |
| D-4 | sug 池建议走 trivial | C. `harness suggest --apply --trivial` flag | 步骤最省 |
| D-5 | 测试 / 验收跳过的兜底 | B + C 组合（不写新测试但跑全量 pytest + 测试红强制升级 bugfix） | trivial-guard 双保险 |
| D-6 | done 阶段如何精简 | A. 跳六层回顾 + ≤ 200 字交付总结 | 与 sug 直接处理路径同构 |
| D-7 | 本 req 产出边界 | C. 设计 + 完整代码 + dogfood 活证 | 与 req-46 / req-41 收口模式一致 |
| **D-8** | trivial 通道 session-memory 是否强制产出 | **A. 跳过**（保留可选 ≤ 500 字） | uav bugfix-6 实测 18 KB session-memory 与 1 行 fix 不成比例 |
| **D-9** | hint 形态（命令入口主动识别） | **A. stdout 提示不阻塞** | B 打断硬门禁四；C 越权剥夺用户选择 |
| **D-10** | chg 级 trivial 路径选择载体 | **A. change.md frontmatter `trivial: true`** | 机器可读 + 人可读，不污染命名 |
| **D-11** | 现有 hint 命令清单 | **A. 仅 `harness bugfix` + `harness requirement`** | 是用户选择"通道"的关键决策点 |
| **D-12**（chg-01 plan 内决策） | trivial 任务 id 编号空间 | **A. 复用 req-id 编号空间，prefix 保持 `req-`**（slug 体现 trivial 性质） | 避免 id 命名分裂；trivial 标识用 task_type 字段而非 id prefix |
| **D-13**（chg-04 plan 内决策） | trivial-guard pytest 是否全量 | **A. 全量 + `--fast` flag opt-in 提速** | 全量保险，用户责任自担降级 |

### 4.3 与既有路径关系（保持 §2.3 修订一致）

- 新增第 5 类 task_type = "trivial"，不替换 req / bugfix / sug / ff 中任一；
- chg 级 trivial（change.md frontmatter）支持单 bugfix / req 内混合走 trivial / 标准 executing；
- ff 模式与 trivial 维度正交（trivial 减少 stage 数；ff 跳 stage 内确认），可叠加；
- sug 直接处理路径与 trivial 通道概念区分：suggestion = 建议入池待 triage；trivial_define = 已决定要做的小改动入口。

## 5. 待用户确认（一次性 batched-report）

> 按硬门禁四同阶段不打断 + req-40（阶段合并与用户介入窄化方向 C）stage 流转点豁免子条款，requirement_review → planning 默认静默；planning → ready_for_execution 保留用户拍板（拍板对象 = 修订后需求 + 5 chg 拆分合并产物）。

详见 requirement.md §附录 A default-pick D-1 ~ D-11 + 本 session-memory §4.2（含本 stage 新增 D-12 / D-13 chg 内决策，已就地落痕到对应 chg plan.md / change.md §5 风险段，不外置）。

## 6. 待处理捕获问题

- 无（job 范围内全部决策已 default-pick 推进）。

## 7. 经验沉淀候选（done 阶段再决定是否写入 experience/）

- **经验候选 1**：trivial 通道概念与 sug 直接处理路径的 3 stage 精简结构高度同构；可在 done 阶段抽象为"轻量任务通道"统一模式（包含 task_type 扩枚举 + SEQUENCE 常量 + 跳 testing/acceptance + done 精简版 + 兜底升级 5 要素）。
- **经验候选 2**：`validate_trivial_eligibility` + `validate_trivial_guard` 两个 helper 形成"入口启发式 + 流转点强制"双层判据，可推广到 ff 模式 / sug 直接处理路径作为通用兜底护栏模式。
- **经验候选 3**：chg 级 trivial flag（change.md frontmatter）是首次实现的"任务内 chg 维度路径选择"机制；可推广到其他 chg 维度差异（如 chg-NN ff=true / chg-MM ff=false）。
- **经验候选 4**：uav bugfix-6 实证表（1 行 fix / 44 KB 文档 / 6 倍时间超支）是首个跨仓库（read-only）量化驱动 req 立项的样本；可在 analyst experience 加"实证驱动需求拆分"段。

## 8. 上下文消耗评估

- 本 subagent 累计读取 ≈ 12 大文件（Part A 修订 + Part B 5 chg × 2 文件产出 + 验证 lint）；估计 ~30% 上下文占用，远低于 70% 评估阈值，无需维护。

## 9. 退出检查

- [x] requirement.md 修订完成（§2.3 实证 + §3 新动作 + §4 新 AC + §5 重构 5 chg + 附录 A D-8 ~ D-11）
- [x] 5 chg 全部产出 change.md + plan.md（每 plan.md 含 §4. 测试用例设计）
- [x] DAG 硬序明确（chg-01 → chg-02 → chg-03 → chg-04 → chg-05 线性）
- [x] session-memory.md 落点 `.workflow/flow/requirements/req-49-{slug}/planning/session-memory.md`（机器型 in flow/）
- [x] default-pick D-1 ~ D-13 全部留痕（requirement.md 附录 A + 本 session-memory §4.2 + chg 内 plan.md / change.md 决策段）
- [x] 模型一致性自检通过（analyst → opus）
- [x] `harness validate --contract artifact-placement` exit 0（PASS：artifacts/ 下无机器型文件）
- [x] `harness validate --contract test-case-design-completeness` 自检：5 个 plan.md 全含 §4 测试用例设计章节（既有 req-41 / bugfix-5 历史违规与本 req 无关）
- [x] `harness validate --human-docs` 按 D-11=B 留痕放行模式：exit 1（0/2 present）— **预期 pending**：raw `requirement.md` + `交付总结.md` 由 done 阶段产出，planning stage 不应也无能力产出，按 briefing D-11=B 留痕放行
- [x] 经验沉淀候选已记录（候选 1 / 2 / 3 / 4，done 阶段最终决定）

## 10. analyst 专业化抽检反馈（req-40 chg-06 模板）

| 字段 | 值 |
|------|---|
| 抽检产物 | req-49 chg-01 ~ chg-05 完整 change.md + plan.md 集（含 §4 测试用例设计 75 用例） |
| 质量评分 | A（明显优于原两步） |
| 退化点明细 | 无；§4 测试用例设计完备（每 chg 13-17 用例覆盖 P0 + P1 + P2 + dogfood TC + 反例）；依赖分析完整（DAG 硬序 + chg 间依赖文字描述）；风险识别具体（每 chg §5 列 ≥ 2 个风险 + 缓解）；trivial 通道概念新设但与既有 4 类路径边界划分清晰 |
| 是否触发 regression 回调 B | 否（A 档活证，无需回调） |
| 抽检人 + 时间 + req 范围 | analyst（自评，子 subagent）/ 2026-04-29 / req-49 |
