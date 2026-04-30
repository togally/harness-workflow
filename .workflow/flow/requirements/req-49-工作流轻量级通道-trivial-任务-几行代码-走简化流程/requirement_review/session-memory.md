# Session Memory — req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ requirement_review

## 1. Current Goal

为 trivial 任务（几行代码、单一明确改动、零新增依赖、零 API/契约面变更）开辟显式 3 stage 轻量通道（`harness trivial`），与现有 4 类路径并列，端到端 ≤ 5 次派发。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）→ stage = requirement_review
- Level 1: 本 subagent（analyst / opus）→ task = req-49 requirement.md 起草 + 6 维度 brainstorm batched-report

## 3. Completed Tasks

- [x] 读 runtime.yaml / WORKFLOW.md / context/index.md / role-loading-protocol.md
- [x] 加载 base-role.md / stage-role.md / analyst.md / repository-layout.md
- [x] 模型一致性自检（analyst → opus，与运行 model 一致）
- [x] 对照 4 类既有路径（requirement / bugfix / suggest --apply / ff）确认痛点边界
- [x] 编写 requirement.md（§1~§5 + 附录 A default-pick 清单 + 附录 B 风险）落 `.workflow/flow/requirements/req-49-{slug}/requirement.md`

## 4. Results

### 4.1 关键拍板（default-pick 清单）

| 编号 | 决策点 | default-pick | 理由 |
|------|--------|--------------|------|
| D-1 | trivial 通道载体形态 | A. 新命令 `harness trivial` | 新命令显式语义最清晰，与 4 类既有路径并列 |
| D-2 | trivial 准入判据 | D. 组合判据（≤ 10 行 + ≤ 2 文件 + 改动类型白名单 + 影响面零增） | 单一阈值有 corner case，组合 machine-checkable |
| D-3 | trivial_define 是否新设角色 | A. 复用 executing 角色 | 控制角色蔓延 |
| D-4 | sug 池建议走 trivial 路径 | C. `harness suggest --apply --trivial` flag 增强 | 用户痛点是步骤多，flag 直通最省心 |
| D-5 | 测试 / 验收跳过的兜底 | B + C 组合（不写新测试但跑全量 pytest + 测试红强制升级 bugfix） | A 太弱、D 风险过高；trivial-guard 双保险 |
| D-6 | done 阶段如何精简 | A. 跳六层回顾，仅产 ≤ 200 字交付总结 | sug 直接处理路径已有先例可复用 |
| D-7 | 本 req 产出边界 | C. 设计 + 完整代码 + dogfood 活证 | 与 req-46 / req-41 收口模式一致 |

### 4.2 推荐 chg 拆分（5 个 chg DAG）

```
chg-01（trivial 准入判据 + helper + 单测）
   ↓
chg-02（CLI 入口 + harness-manager 路由）
   ↓
chg-03（trivial_define stage + executing trivial 模式 + 工件落位）
   ↓
chg-04（trivial-guard 自动升级护栏 + done 精简版）
   ↓
chg-05（dogfood 活证 + 契约 lint 覆盖）
```

### 4.3 与既有路径关系

- 新增第 5 类 task_type = "trivial"，不替换 req / bugfix / sug / ff 中任一；
- ff 模式与 trivial 维度正交（trivial 减少 stage 数；ff 跳 stage 内确认），可叠加 `harness trivial --ff`（本 req 不做）；
- sug 直接处理路径与 trivial 通道概念区分：suggestion = 建议入池待 triage；trivial_define = 已决定要做的小改动入口。

## 5. 待用户确认（一次性 batched-report，6 维度）

> 按硬门禁四同阶段不打断 + req-40 stage 流转点豁免子条款，requirement_review → planning 默认静默推进；本批次仅在 stage 流转**前**留出一次拍板窗口，已用 default-pick 推进，可由用户 override。

详见 `requirement.md §附录 A` default-pick 决策清单 D-1 ~ D-7（已就地落痕，不再外置选项表）。

## 6. 待处理捕获问题

- 无（job 范围内全部决策已 default-pick 推进）。

## 7. 经验沉淀候选（done 阶段再决定是否写入 experience/）

- **经验候选 1**：trivial 通道概念与 sug 直接处理路径有相似结构（3 stage 精简 + 跳过 testing/acceptance 但保留 done 轻量版 + 兜底升级）。可在 done 阶段抽象为"轻量任务通道"统一模式，减少新通道引入成本。
- **经验候选 2**：`harness validate --trivial-guard` 是首个"流转点自动跑硬门禁"模式（区别于既有"stage 入口校验"），可推广到 ff 模式 / sug 直接处理路径。

## 8. 上下文消耗评估

- 本 subagent 累计读取 ≈ 8 大文件（含 base-role / stage-role / analyst / repository-layout / runtime / 部分 workflow_helpers.py 节选 + experience/analyst.md 节选）；估计 ~15% 上下文占用，远低于 70% 评估阈值，无需维护。

## 9. 退出检查

- [x] requirement.md 含 §1 标题 + §2 目标 + §3 范围 + §4 验收标准 + §5 拆分规则
- [x] requirement.md 落点 `.workflow/flow/requirements/req-49-{slug}/requirement.md`（机器型，非 artifacts/）
- [x] session-memory.md 落点本目录 `requirement_review/session-memory.md`
- [x] default-pick 清单已沉淀到 requirement.md 附录 A + 本 session-memory §4.1（双留痕）
- [x] 模型一致性自检通过（analyst → opus，与运行 model 一致）
- [x] `harness validate --contract artifact-placement` exit 0（已跑：`PASS: artifact-placement lint — artifacts/ 下无机器型文件`）
- [x] `harness validate --human-docs` 按 D-11=B 留痕放行模式：exit 1（0/2 present）— **预期 pending**：`raw_artifact requirement.md` 由 done 阶段 copy 产出；`交付总结.md` 由 done 阶段产出。requirement_review stage 不应也无能力产出这两份文件，按 briefing D-11=B 留痕放行，不阻塞 stage 推进。
- [x] 经验沉淀候选已记录（候选 1 / 2，done 阶段最终决定）
