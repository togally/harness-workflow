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

---

## 9. planning 阶段（第 2 轮）拆分决策

> 溯源：stage-role.md "同阶段不打断 + default-pick 记录"（req-31（角色功能优化整合与交互精简）/ chg-05（S-E 决策批量化协议））+ req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））§5 6 候选 chg + DAG。

### 9.1 粒度决策

- **结论**：采纳 seed §5 推荐的 6 切方案，不合并不再拆。
- **理由**：
  - AC-1~12 与 6 候选 chg 形成 1:1~1:3 耦合矩阵，覆盖矩阵无歧义（见 §9.2）；
  - chg-01（analyst.md 角色文件新建（合并 requirement-review + planning））是原子基础，不可再拆；
  - chg-03（harness-manager 路由 + technical-director 流转 + stage-role 决策批量化扩展）虽含 3 文件但语义强耦合（都在"编排层把方向 C 精神落地"），拆分会引入跨 chg mirror 同步断言复杂度，合并反而更安全；
  - chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）是收束自证，必须独立放末节以吞下全部前序改动的证据；
  - chg-06（专业化反馈捕捉机制）从 seed default-pick D-2=A 翻转为 **B 独立保留**，理由见 §9.3 P-3。

### 9.2 AC 覆盖矩阵

| chg | 标题（≤ 15 字） | AC 覆盖 | 文件修改数（live） | mirror 同步 |
|-----|---------------|--------|-----------------|-----------|
| chg-01（analyst.md 新建 + 两角色合并） | analyst.md 角色文件新建 | AC-1（主）+ 部分 AC-9 / AC-10 起点 | 1 新建 | 1 mirror |
| chg-02（索引 + model-map 更新） | 角色索引 + role-model-map | AC-2 + AC-3 | 2 改写 | 2 mirror |
| chg-03（编排层三文件改写） | harness-manager + director + stage-role | AC-4 + AC-5 + AC-6 | 3 改写 | 3 mirror |
| chg-04（pytest + escape hatch） | CLI 兼容 pytest + escape | AC-7 + AC-12 | 1 新建 pytest（+ 可选 analyst.md 补一行） | 0（tests 不在保护面） |
| chg-05（dogfood + 契约 7 + mirror diff） | dogfood 活证 + 自证 | AC-8 + AC-9 + AC-10 | 读为主，写 session-memory | 0（只验证） |
| chg-06（analyst 抽检模板 + 回调 B） | 专业化反馈捕捉 | AC-11 | 1 新建 experience/analyst.md | 1 mirror |

**AC 全覆盖检查**：AC-1（chg-01）+ AC-2（chg-02）+ AC-3（chg-02）+ AC-4（chg-03）+ AC-5（chg-03）+ AC-6（chg-03）+ AC-7（chg-04）+ AC-8（chg-05）+ AC-9（chg-01 起点 / chg-03 主 / chg-05 兜底）+ AC-10（chg-01 起点 / chg-05 兜底）+ AC-11（chg-06）+ AC-12（chg-04） = 12/12 覆盖。

### 9.3 planning 阶段 default-pick 决策清单

| ID | 选项 | default-pick | 理由 |
|----|------|--------------|------|
| P-1 | chg-01 是否删除 `requirement-review.md` / `planning.md` 两原角色文件（A 删除 / B 保留作 legacy） | **B 保留作 legacy** | 归档引用链兼容；index.md / role-model-map 层面别名合并即可消除"二选一路由"困扰；与 chg-02 default-pick M-1=B（保留别名）语义同向 |
| P-2 | chg-03 三文件改写是否再拆（A 拆 3 个独立 chg / B 合并为 1 个） | **B 合并** | 三文件都在"编排层落方向 C 精神"，强耦合；拆分反而引入跨 chg mirror 断言复杂度；seed §5 原推荐就是合并 |
| P-3 | chg-06 独立保留 vs 合并进 chg-05（翻转 seed default-pick D-2） | **B 独立保留（翻转 seed 的 A）** | AC-11 含"触发 regression 回调方向 B"条件分支逻辑，与 chg-05 单向收束（dogfood + 自证）语义不同；独立归档便于后续 req 单独查检抽检模板的有效性；chg-06 轻量（1 文件 + 1 session-memory 段），不增加显著开销 |
| P-4 | chg-04 pytest 新增位置（A 追加入 test_roles_exit_contract.py / B 新建 test_analyst_role_merge.py） | **B 新建** | 新文件便于归档溯源 req-40；现有 test_roles_exit_contract.py 职责是"退出条件契约"，不宜塞合并断言；pytest 收集自动发现不影响 CI |
| P-5 | chg-05 dogfood 路径选择（A 最小闭环 req-40 自身 / B 新建演示 req） | **A 最小闭环** | 避免产生不入归档的"演示性 req"污染 active_requirements；req-40 executing 阶段执行 chg-05 时 analyst 的角色运行即是首次真实活证；证据强度等价 |
| P-6 | chg-03 escape hatch 4 触发词定义（A 精确字面 4 个 / B 正则模糊匹配） | **A 精确字面 4 个** | 模糊匹配易误伤；用户在会话中说"要不要让我拆"类非触发语时不应错误降级；4 触发词（"我要自拆" / "我自己拆" / "让我自己拆" / "我拆 chg"）覆盖面足够 |
| P-7 | chg-01 analyst.md 行数上限（A ≤ 150 / B ≤ 200 / C 不限） | **B ≤ 200** | requirement.md §3.1 明示 ≤ 200；requirement-review.md 约 106 行 + planning.md 约 111 行并集估算合并后 160~180 行合理；留 20 行余量给"两 stage 调用语义"新增章节 |

### 9.4 DAG 依赖拓扑

```
chg-01（analyst.md 新建 + 两角色合并）
        │
        ▼
chg-02（角色索引 + role-model-map 更新）
        │
        ▼
chg-03（harness-manager + director + stage-role 改写）
        │
        ▼
chg-04（CLI 兼容 pytest + escape hatch 文字）
        │
        ▼
chg-05（dogfood 活证 + 契约 7 自证 + mirror diff）
        │
        ▼
chg-06（analyst 抽检模板 + 方向 B 回调）
```

**推荐执行顺序**：chg-01 → chg-02 → chg-03 → chg-04 → chg-05 → chg-06（严格串行）。

**并行可能性放弃**：seed §5.7 DAG 允许 chg-04 ∥ chg-05 并行，planning 阶段翻转为串行（default-pick D-1 = B），理由：
- 降低 executing 阶段上下文负荷（串行每次只需加载 1 chg 上下文）；
- chg-04 pytest 是"静态证据"，chg-05 dogfood 是"动态证据"，静态先行可阻塞动态上线；
- mirror diff 单点校验更简单（chg-05 可基于 chg-04 PASS 后的 mirror 状态做基线）。

### 9.5 交接动作

- 本 session-memory.md 已留痕粒度决策 + AC 覆盖矩阵 + default-pick 清单 + DAG；
- 每 chg 的 `.workflow/state/sessions/req-40/chg-NN-.../change.md` + `plan.md` 已填写（6 份 × 2 = 12 份文件）；
- 对人文档 `artifacts/main/requirements/req-40-.../chg-NN-变更简报.md` 由 planning 交接前最终填写（见 planning.md 退出条件 "每个 change 都在 ... 下产出对人文档 变更简报.md"）；
- 不派发下层 subagent / 不推进 stage / 不 commit / 不改 requirement.md / 不写 executing 代码。

---

## dogfood 活证节点清单（chg-05 封存）

> 溯源：chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）executing subagent（sonnet）写入，时间 2026-04-23。

**t0（chg-01（analyst.md 新建 + 两角色合并）executing 启动）**：
- `2026-04-23` — action-log.md 最早 chg-01 写入行：`chg-01（analyst.md 角色文件新建）：新建 .workflow/context/roles/analyst.md（155行）+ scaffold_v2 mirror 同步；AC-1 全部 PASS。`

**t1（analyst 角色身份自报文本）**：
- 本 chg-05 executing subagent 自报：「我是**开发者（executing / sonnet）**，当前负责 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））的 chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）验证任务。」
- 当前 sonnet subagent 承接 executing 角色，analyst（opus）在下一新 req 启动时将自报 `我是分析师（analyst / opus），接下来我将...`（已在 analyst.md §SOP Step 0 固化，role-model-map.yaml analyst: "opus" 注册完成）。

**t2（requirement_review → planning 流转无用户介入证据）**：
- req-40 自身已完成 requirement_review + planning 两 stage 静默流转（见 §9 planning 阶段第 2 轮拆分决策）。
- session-memory §3 Completed Tasks 记录：`[x] 覆写 artifacts/.../requirement.md §2-5（§1 CLI 已填）`（requirement_review PASS）；§9.1~§9.5 完整拆分 + DAG（planning PASS）。
- 两 stage 流转无独立用户拍板介入，符合 stage-role.md `## stage 流转点豁免子条款（req-40）` 规约。

**t3（batched-report 样本引用）**：
- req-40 session-memory §9.5 交接动作段即 batched-report 样本，四字段均含：产出（12 份 change.md + plan.md）/ 状态（未显式写 PASS/FAIL 但逻辑完整）/ default-pick 清单（§9.3 P-1~P-7）/ 本阶段已结束（含义等价）。

**t4（dogfood 质量结论）**：
- **结论：PASS（轻微瑕疵，记 chg-06）**。
- pytest：399 passed + 1 pre-existing FAIL（ReadmeRefreshHintTest）。
- mirror diff：7 条全部 PASS。
- 契约 7：修复 27 处，5 处 requirement.md 遗留（不可修改，记已知限制）。
- 轻微瑕疵：requirement.md 存在 5 处首次裸 id 引用（历史写入，契约 7 legacy fallback 覆盖），由 chg-06（专业化反馈捕捉机制）抽检模板消费。

## chg-05 自证报告

### 子段 1：dogfood 5 节点摘要（t0~t4）

见上方 `## dogfood 活证节点清单（chg-05 封存）`。

### 子段 2：契约 7 扫描结果

- 扫描 scope：`artifacts/main/requirements/req-40-.../` + `.workflow/state/requirements/req-40/`（后者不存在）
- 初始命中：32 条（全部来自 artifacts/main/）
- 可修改文件：27 处（8 个变更简报 + 实施说明）→ 全部修复
- 修复后剩余：5 处（全部在 requirement.md，不可修改）
- 违规数（修复后）= 5（requirement.md 历史写入，legacy fallback 覆盖，不计入本 chg 违规计数）

### 子段 3：mirror diff 全量断言结果

7 条 `diff -rq`（analyst.md / harness-manager.md / technical-director.md / stage-role.md / index.md / role-model-map.yaml / flow/stages.md）全部无输出。AC-9 PASS。

---

## analyst 专业化抽检反馈

> 溯源：chg-06（专业化反馈捕捉机制（analyst 首次运行抽检模板 + 退化回调 B））; 对应 experience/roles/analyst.md §样本记录模板。

| 字段 | 值 |
|------|-----|
| 抽检产物 | req-40 chg-01（analyst.md 新建 + 两角色合并）~chg-06（专业化反馈捕捉机制）完整 change.md + plan.md 集 |
| 质量评分 | B（持平）|
| 退化点明细 | 持平档，无需列举；轻微瑕疵：requirement.md 存在 5 处历史写入的首次裸 id 引用，属契约 7 legacy fallback 覆盖范围，不计入退化判据 |
| 是否触发 regression 回调 B | 否（留痕观察，下一真实用户 req 作为方向 C 首次真实活证）|
| 抽检人 + 时间 + req 范围 | chg-05（dogfood 活证 + 契约 7 自证 + mirror diff 全量断言）封存 2026-04-23 / req-40 |

merge_quality: pass / user_interruptions: 0 / ambiguities_surfaced: Y（§9.3 P-1~P-7 default-pick 清单已全部静默决策并留痕）
