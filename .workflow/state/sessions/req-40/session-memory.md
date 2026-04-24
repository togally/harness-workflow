# Session Memory — req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

## 1. Current Goal

- Stage：`requirement_review`（seed 轮次，planning-ready 定稿，不展开完整 AC 澄清）。
- 上游：reg-01（planning 并入 requirement_review，用户只管需求确认，chg 拆分由 agent 自主）`decision.md` §3.2 "方向 C 角色合并 + stage 保留" 被用户选定；本 req-40 由 `harness regression --requirement` 转出，直接落 §2-5 planning-ready 版。
- 直接输入：reg-01 `regression.md` / `analysis.md` / `decision.md`（权威设计输入，analysis §3.3 方向 C 实现路径 + §4 横切隐患已内化）。

## 2. Context Chain

- Level 0：主 agent（technical-director / opus）执行 `harness regression --requirement "阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）"` 转出 req-40，设定 stage = requirement_review。
- Level 1：requirement-review subagent（opus，本轮），做 seed 定稿。

## 3. Completed Tasks

- [x] 硬前置加载（runtime.yaml / WORKFLOW.md / .workflow/context/index.md / base-role.md / stage-role.md / requirement-review.md / planning.md / stages.md / role-model-map.yaml / reg-01 三文件）。
- [x] 读取权威设计输入：reg-01 `regression.md` / `analysis.md` / `decision.md`（四方向对比 + 方向 C 细节已内化）。
- [x] 参照 req-39（对人文档家族契约化 + artifacts 扁平化）requirement.md 的密度锚点（约 180 行），本 req §2-5 覆盖到 12 条 AC + 6 候选 chg + DAG。
- [x] 覆写 `artifacts/main/requirements/req-40-阶段合并与用户介入窄化-方向-c-角色合并-analyst-md/requirement.md` §2-5（§1 CLI 已填）。
- [x] 新建本 session-memory，seed 轮次留痕。

## 4. Results

### 4.1 requirement.md §2 Goal 要点

- 动机：req_review + planning 两阶段两介入 ≥ 80% 走过场；近 5 个 req（req-22（批量建议合集（19条））/ req-29（角色→模型映射）/ req-31（角色功能优化整合）/ req-34（新增 api-document-upload 工具）/ req-38（api-document-upload 工具闭环））零 override 价值。
- 意图：一次介入（需求拍板）+ 一次产出（requirement + 推荐拆分 + change/plan 全集）。
- 方向 C 实现路径：角色合并 `analyst.md`，stage 命名保留，CLI 零破坏。

### 4.2 requirement.md §3 Scope 九条线

- Scope-A（analyst.md 新建）
- Scope-B（index + role-model-map）
- Scope-C（harness-manager 路由）
- Scope-D（technical-director 流转 + escape hatch）
- Scope-E（stage-role 决策批量化扩流转点）
- Scope-F（CLI 零破坏）
- Scope-G（scaffold_v2 mirror + 存量豁免）
- Scope-H（dogfood 自证）
- §3.9 不在 Scope（executing~done 五 stage 零动 / 归档与辅助 CLI 零动 / req-28~req-39 产物零动）

### 4.3 requirement.md §4 AC 12 条

- AC-1（analyst.md 存在 + ≥ 6 节 + mirror 零）
- AC-2（role-model-map analyst: opus + legacy 别名保留）
- AC-3（index.md analyst 条目 + 合并注释）
- AC-4（harness-manager 派发目标 = analyst）
- AC-5（technical-director 自动流转条款 + escape hatch）
- AC-6（stage-role 决策批量化扩 stage 流转点）
- AC-7（CLI 零回归 + 新 pytest 断言）
- AC-8（dogfood 活证 + session-memory 留痕）
- AC-9（scaffold_v2 mirror 跨文件 diff 归零）
- AC-10（契约 7 + 硬门禁六自证）
- AC-11（专业化损失评估 + 退化回调 B）
- AC-12（escape hatch 路径 "我要自拆"）

### 4.4 requirement.md §5 Split Rules 6 候选 chg + DAG

- chg-01 候选（analyst.md 角色文件新建）→ AC-1 / 部分 AC-10 / 部分 AC-9
- chg-02 候选（角色索引 + role-model-map）→ AC-2 / AC-3
- chg-03 候选（harness-manager + director + stage-role）→ AC-4 / AC-5 / AC-6
- chg-04 候选（CLI 兼容 pytest + escape hatch 文字）→ AC-7 / AC-12
- chg-05 候选（dogfood + 契约 7 + mirror diff）→ AC-8 / AC-9 / AC-10
- chg-06 候选（专业化反馈捕捉）→ AC-11；可合并入 chg-05

**DAG**：chg-01 → chg-02 → chg-03 → (chg-04 ∥ chg-05) → chg-06（或 chg-05 吞 chg-06）。

## 5. default-pick 决策清单

> 溯源：stage-role.md "同阶段不打断 + default-pick 记录"（req-31（角色功能优化整合与交互精简）/ chg-05（S-E 决策批量化协议））。

本 stage 本轮 seed 未触发打断级争议点，以下 default-pick 为 §3-5 内预置，供 planning 阶段复核或翻转：

| ID | 选项 | default-pick | 理由 |
|----|------|--------------|------|
| I-1 | index.md legacy 条目处理（A 合并 / B 保留别名条目 / C 加废弃标记） | **A 合并 + 注释** | 索引表简洁；注释记"合并来源 req-40"便于溯源；别名语义由 role-model-map 承载 |
| M-1 | role-model-map legacy key 处理（A 删除 / B 保留作别名指 opus / C 保留带 deprecated 标签） | **B 保留别名指 opus** | 避免 role-loading-protocol Step 7.5 模型自检对 legacy yaml key 误报；符合 req-29（角色→模型映射）/ chg-01 映射向后兼容语义 |
| HM-1 | harness-manager 派发实现路径（A 同一会话续跑 / B 两次派发 analyst） | **A 同一会话续跑** | 方向 C 精神是角色物理合并，上下文连贯；B 作 fallback |
| D-1 | chg-04 与 chg-05 依赖关系（A 并行 / B 串行） | **B 串行** | 降低上下文负荷 + 便于 mirror diff 单点校验 |
| D-2 | chg-06 独立 vs 合并入 chg-05（A 合并 / B 独立） | **A 合并** | 反馈模板轻量；减少 chg 数量便于归档 |

以上均可在 planning 阶段由 analyst（或 planning subagent）按需翻转，翻转时在 planning session-memory 留痕即可。

## 6. 模型自检（硬门禁三 + role-loading-protocol Step 7.5）

- 期望模型：`opus`（按 `role-model-map.yaml::requirement-review`）。
- 实际模型：Claude Opus 4.7（1M context）（运行期自报 `claude-opus-4-7[1m]`），符合期望；**无降级留痕需要**。
- 自我介绍：按 base-role 硬门禁三 + stage-role Session Start 约定执行，形如"我是需求分析师（requirement-review / opus），接下来我将为 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））seed planning-ready requirement.md"。

## 7. 待处理捕获问题 / TODO

- **TODO-1（req-38 limbo）**：req-40 与 req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）无直接耦合，不在本 req scope；待 req-39（对人文档家族契约化 + artifacts 扁平化）done 后手动解锁 req-38 acceptance → done → archive；本 req-40 不处理此 limbo。
- **TODO-2（req-39 AC-11 预存裸 id 遗留）**：req-39 cleanup 留下的 7 处 `实施说明.md` 遗留违规（裸 id），不在本 req-40 scope；由 req-39 acceptance-report / 后续 cleanup 处理。
- **TODO-3（analyst 命名争议）**：若用户偏好其他命名（`requirement-architect` / `proposal-author` / `reviewer-planner` / `need-analyst`）在 chg-01 executing 前提出，chg-01 执行时 default-pick N-1 = `analyst`（简洁通用，英文单词语义覆盖需求分析 + 架构拆分两职责）。
- **TODO-4（role-model-map 别名过渡期时长）**：`role-model-map.yaml` 保留 `requirement-review` / `planning` 作为 analyst 别名的时长（永久 / 到某 req / 到某归档里程碑），留到 chg-02 executing 时 default-pick（倾向永久保留，向后兼容历史归档 yaml）。
- **TODO-5（CLI 路径落位确认）**：按 req-39 的 chg-05（CLI 路径对齐扁平化 + scaffold mirror 同步）落地后的新契约，req-id ≥ 39 的机器型 `requirement.md` 应落到 `.workflow/state/requirements/{req-id}/requirement.md`；req-40 CLI 实际把 `requirement.md` 落到 `artifacts/main/requirements/req-40-.../requirement.md`（legacy 路径），`.workflow/state/requirements/req-40-....yaml` 存在但**无** `.workflow/state/requirements/req-40-.../` 目录。判定：CLI `create_requirement` 路径未按 req-39 新契约走，疑似 chg-05 未覆盖 `harness requirement` 命令（仅覆盖 `create_change` / `create_regression` / `archive_requirement`）。**本 seed 不自迁移**（禁止"不修改 requirement-review.md / planning.md / analyst.md / CLI"），留 TODO 供 planning / executing 阶段评估（可能由 req-40 chg-04 或新 bugfix 承接）。
- **TODO-6（方向 C 专业化退化回调）**：AC-11 要求 executing 阶段人工抽检产物质量；若发现明显退化（chg 拆分粒度粗 / 缺依赖分析 / 缺风险评估），触发新 regression 回调方向 B（软合并 auto-advance 保留两 subagent，用户感知一致但后端保留专业化）。

## 8. Next Steps

- 主 agent 接 seed 产出 → 若无澄清请求 → `harness next` 推 planning。
- planning 阶段按 §5 候选 chg-01 ~ chg-06 拆分 + 分配编号；AC-1~12 按 chg 归并覆盖矩阵；每 chg 产出 `change.md` + `plan.md` + `chg-NN-变更简报.md`（按 req-39 新扁平路径；若 CLI 未落新路径则按 TODO-5 评估）。
- 按方向 C 精神，planning 默认 auto-advance（若 req-40 自身已按方向 C 执行则形成 dogfood 闭环）；或按现状走正常 `harness next` 流转，在 req-40 落地后下一新 req 才开始应用方向 C。
