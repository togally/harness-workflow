# Session Memory — req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 1. Current Goal

为 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））seed requirement.md；按 req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））/ chg-01（req-40 的 analyst.md 角色文件新建 + 合并 requirement-review planning）产出的 analyst 新规，一次性产出 requirement + 推荐 chg 拆分（planning-ready 模式），不展开 AC 澄清对话，不派发下层 subagent，不推进 stage。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus，harness-manager 路由后常驻）
- Level 1: analyst / opus（本次 subagent；req-40 方向 C 合并 req_review + planning 两 stage 于同一角色）

## 3. 模型自检（req-29（角色-模型映射）/ chg-03（req-29 的角色映射更新变更）+ role-loading-protocol Step 7.5）

- `expected_model: opus`（briefing 要求）
- `.workflow/context/role-model-map.yaml` → `analyst: "opus"`（req-40 chg-01 落地）
- 自省：本 subagent 由 harness-manager 以 `model=opus` 派发；无法程序性自省具体子版本（Opus 4.7[1m]）时，按 Step 7.5 记录降级留痕 —— 本次不降级，直接按 opus 续跑。
- 降级留痕位：本区块已留痕；无需额外进入 FAIL 路径。

## 4. 用户最终共识（reg-01（artifacts 布局语义复核）→ req-41（机器型工件回 flow）seed 依据，权威意图留痕）

**方向选择**：reg-01（artifacts 布局语义复核：需求文档归属 + `.workflow/flow/requirements` 应否复用） `regression.md` §4 用户选**方向 C**（整体回退 + 关注点分离 + 废四类 brief，激进解读 A 的进化版）。

**四 scope 概览**（用户 briefing 原话锁死）：

1. **Scope-共骨架**：顶层契约扩管所有文档归属；角色文件去路径化。
2. **Scope-C 迁移**：机器型工件从 `.workflow/state/requirements/` + `.workflow/state/sessions/` 搬回 `.workflow/flow/requirements/req-XX/`；`.workflow/state/` 只存 runtime 数据。
3. **Scope-废 brief**：废止 `需求摘要.md` / `变更简报.md` / `实施说明.md` / `回归简报.md` 四类；artifacts 只留 raw `requirement.md` 副本 + 真·对外产物。
4. **Scope-效率字段**：接入 `record_subagent_usage` 到派发链路硬门禁化；扩 `交付总结.md` 模板加 "## 效率与成本"段；废独立耗时报告；`usage-reporter` 废止。

**不邀用户决策的事项**（按 req-40 analyst 新规 + reg-01 方向 C 用户"只管需求"精神，analyst 自主决定）：
- chg 拆分粒度（本次拆 7 chg，见 requirement.md §5）
- DAG 依赖结构
- 常量命名（`FLOW_LAYOUT_FROM_REQ_ID = 41`、`BRIEF_DEPRECATED_FROM_REQ_ID = 41`）
- 文件重命名（`artifacts-layout.md → repository-layout.md`）
- usage-reporter 是"收窄为 helper"还是"直接废止" → 选"直接废止"（let done subagent 直接聚合，更精简，符合方向 C 关注点分离精神）

## 5. Completed Tasks

- [x] 读取硬前置：runtime.yaml / base-role.md / stage-role.md / analyst.md / role-model-map.yaml
- [x] 读取权威设计输入：reg-01 regression.md / artifacts-layout.md / workflow_helpers.py 关键段（`LEGACY_REQ_ID_CEILING` / `FLAT_LAYOUT_FROM_REQ_ID` / `_use_flat_layout` / `create_*` / `record_subagent_usage`） / validate_human_docs.py / done.md / usage-reporter.md / harness-manager.md §3.6
- [x] 按 req-40 analyst 新规覆写 `.workflow/state/requirements/req-41/requirement.md`：§1 Title 保留（CLI 填）/ §2 Goal 动机 + 四 scope 概览 + dogfood 声明 / §3 Scope 四 scope 详细 Included + Excluded / §4 AC 16 条（覆盖四 scope + dogfood + 契约 7 + scaffold mirror + 汇报模板 + pytest 回归）/ §5 Split Rules 7 chg 推荐拆分 + DAG 图 + escape hatch
- [x] 写本 session-memory（seed 留痕 + 模型自检降级留痕）
- [x] 契约 7 + 硬门禁六 + 批量列举子条款自检：requirement.md §2 Goal 首次引用 reg-01（artifacts 布局语义复核）/ req-40（阶段合并与用户介入窄化）/ req-41（本需求）/ req-39（对人文档家族契约化）/ req-31（角色功能优化整合与交互精简）均带 title；§5 chg 拆分描述每条带 ≤ 15 字描述；无 `chg-01/02/03` 裸数字扫射

## 6. default-pick 决策清单（base-role 硬门禁四 + stage-role 同阶段不打断）

本次 analyst seed 阶段（requirement_review 部分）内部按默认推进的决策：

- **D-1**：contract 文件命名 —— `artifacts-layout.md` 是否重命名为 `repository-layout.md`？
  - default-pick = A（重命名）
  - 理由：原名语义锁在 artifacts 子树，本 req 扩管到三大子树，命名必须升格；`git mv` 保留 history。
- **D-2**：`.workflow/flow/requirements/` 路径是否全新启用？还是复用 `.workflow/state/requirements/`？
  - default-pick = 全新启用 `.workflow/flow/requirements/`
  - 理由：用户原话 "为什么任务中没有在 `.workflow/flow/requirements` 中" —— 直接还原用户心智模型；state/ 收窄为 runtime。
- **D-3**：双轨过渡期 req-id 范围？
  - default-pick = req-39/40 保留 state/ legacy fallback，req-41+ 新 flow/ 路径
  - 理由：不破坏已归档 req-39 / 活跃 req-40；LEGACY_REQ_ID_CEILING (=38) 不动，新增 FLOW_LAYOUT_FROM_REQ_ID (=41) 叠加层。
- **D-4**：`usage-reporter` 废止 or 收窄为 helper？
  - default-pick = 直接废止
  - 理由：done subagent（opus）自身可做 YAML 聚合，不需额外 subagent；方向 C 的"关注点分离"精神是合并同类项，不是再起一层。
- **D-5**：chg 拆分粒度 6-8 chg？
  - default-pick = 7 chg（契约底座 / CLI 迁移 / validate 重写 / 角色去路径化 + brief 删除 / done 模板扩 / harness-manager Step 4 硬门禁 / dogfood 收口）
  - 理由：chg-01（repository-layout 契约底座）必须单独先落（契约先行）；chg-04（角色去路径化 + brief 删除 + usage-reporter 废止）合并"去路径化 + brief 删除 + usage-reporter 废止"三件事因都是同一批角色文件改动；chg-07（dogfood 活证 + scaffold_v2 mirror 收口）单独 dogfood 自证收口。
- **D-6**：四类 brief 历史存量是否迁移 / 删除？
  - default-pick = 不迁移不删除
  - 理由：用户 briefing 明写"历史存量（req-02（workflow 分包结构修复）~ req-40（阶段合并与用户介入窄化））artifacts/ 下已产出的 brief 不迁移不删（git log 自带分水岭）"。
- **D-7**：本 req seed 阶段 requirement.md 写在何处？
  - default-pick = `.workflow/state/requirements/req-41/requirement.md`（按当前 CLI 落位）
  - 理由：req-41（本需求）CLI 机器型落位反转要等 chg-02（CLI 路径迁移）落地才生效；seed 阶段 CLI 还按 FLAT_LAYOUT_FROM_REQ_ID 规则落 state/；本 req 落地后 executing 再把 seed 搬到 flow/（不视为 seed 违约，视为过渡期最后一次 state/ 落位）。

（以上 7 条 default-pick 归并到交接汇报字段 3 "开放问题 / default-pick"，若用户不打断即视为按默认推进。）

## 7. 待处理捕获问题

- **Q-1（职责外）**：chg-07 dogfood 验证时，本 req-41 seed 阶段留在 state/ 的 requirement.md 是否要在 executing 阶段"回搬"到 flow/requirements/？还是维持 state/ 作为"过渡期脚注"？建议交 executing 阶段 open 讨论（影响 AC-13 (a) 严格度）。
- **Q-2（职责外）**：usage-reporter 废止后，是否需要同步清理 `.workflow/context/experience/roles/usage-reporter.md`（若存在）？建议 executing chg-04 顺手 grep 清理。

## 8. Results

- `.workflow/state/requirements/req-41/requirement.md`：§1/§2/§3/§4/§5 全填（planning-ready seed 模式）
- `.workflow/state/sessions/req-41/session-memory.md`：本文件（seed 留痕 + 模型自检 + default-pick 清单 + 待处理问题捕获）

## 9. Next Steps

- 交接给主 agent：按 analyst Part A 退出条件（requirement.md 五节齐全 / 未产出 `需求摘要.md`（方向 C 本 req 自身就要废止这类 brief，analyst 不自相矛盾地产出）/ `harness validate --human-docs` 当前对 req-41 尚无新扫描规则）批次汇报
- 用户拍板点：本 seed 产出一次性合并"需求 + 推荐拆分"，按 stage-role.md "stage 流转点豁免子条款" + req-40 新规，`requirement_review → planning` 流转默认静默；`planning → ready_for_execution` 保留拍板，但本 seed 还没进 planning，故本次只邀用户对 requirement.md + chg 拆分整体评审一次
- analyst 本阶段（req_review seed）完成后停下，不派发下层，不推进 stage

---

## 10. Planning 第 2 轮：拆分决策（承接用户强化规则 + CLI 已创建 8 chg 工作区）

### 10.1 上下文承接

- Seed（第 1 轮）产出 §5 Split Rules 推荐 7 chg；本轮（planning）吸收用户强化要求（对人呈现场景禁裸 id，覆盖 TaskList / 进度条 / stdout / 归档 commit message / git log 等此前漏网路径），将推荐拆分从 7 chg 升为 8 chg。
- CLI 当前未过 `FLOW_LAYOUT_FROM_REQ_ID = 41` 分水岭（chg-02（CLI 路径迁移 flow layout）未落地），`harness change` 仍按 `FLAT_LAYOUT_FROM_REQ_ID = 39` 落到 `.workflow/state/sessions/req-41/chg-XX/`；本 chg 拆分工作区路径符合当前 CLI 行为，chg-07（dogfood + scaffold_v2 mirror 收口）dogfood 阶段再搬到 `.workflow/flow/requirements/req-41-{slug}/`。

### 10.2 用户强化规则吸收决策（default-pick P-8）

- **P-8：用户追加的硬门禁六扩展（TaskList / 进度条 / stdout / 归档 commit / git log 禁裸 id）吞进哪个 chg？**
  - **default-pick = 独立 chg-08（硬门禁六扩 TaskList + stdout + 提交信息）**
  - 理由：
    1. chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）已合并三件事（去路径化 + brief 模板删 + usage-reporter 废止），都是"业务角色文件的对人文档契约清洗"；把"硬门禁六文字扩展"再塞进去，会使 chg-04 跨 base-role.md / stage-role.md 两 meta 文件 + 6 业务角色文件，改动范围爆炸；
    2. chg-08 改动目标是 `base-role.md` / `stage-role.md` / 可能 `harness-manager.md` 三 meta 文件，**语义自洽**（都是"硬门禁六文字覆盖面扩展"）；与 chg-04（角色业务层）不同抽象层；
    3. DAG 不增加深度：chg-08（硬门禁六扩 TaskList + stdout + 提交信息）与 chg-02（CLI 路径迁移 flow layout）+ chg-03（validate_human_docs 重写删四类 brief）+ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）并列依赖 chg-01（repository-layout 契约底座），共骨架后 4 路并行（原 3 路 + 1 路），收口仍由 chg-07（dogfood + scaffold_v2 mirror 收口）做；
    4. 符合契约 7 "关注点分离"精神（方向 C 本 req 的核心价值主张），避免 chg-04 臃肿。

### 10.3 8 chg 最终拆分 + 覆盖 AC + 依赖

| chg | title | 覆盖 AC | 前置依赖 |
|-----|-------|--------|---------|
| chg-01（repository-layout 契约底座） | git mv + 三大子树 §2 重写 | AC-01 / AC-07 起点 / AC-15 起点 / AC-14 起点 | 无（DAG 根） |
| chg-02（CLI 路径迁移 flow layout） | FLOW_LAYOUT_FROM_REQ_ID + create_*/archive_ 改写 | AC-03 / AC-04 / AC-05 / AC-06 | chg-01 |
| chg-03（validate_human_docs 重写删四类 brief） | BRIEF_DEPRECATED_FROM_REQ_ID + 扫描精简 | AC-08 / AC-09 / AC-06 | chg-01 |
| chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止） | 六角色文件 + stage-role 契约 3/4 + usage-reporter 废止 | AC-02 / AC-07 / AC-12 / AC-15 | chg-01 |
| chg-05（done 交付总结扩效率与成本段） | §效率与成本四子字段 + Step 6 聚合 | AC-10 (done 部分) / AC-11 / AC-13 (d) 起点 / AC-15 | chg-01 + chg-04 |
| chg-06（harness-manager Step 4 派发硬门禁） | §3.6 Step 4 硬门禁 + 召唤词清理 + base-role State 层自检 | AC-10 (hm 部分) / AC-12 / AC-13 (c) 起点 / AC-15 | chg-01 + chg-04 |
| chg-07（dogfood + scaffold_v2 mirror 收口） | 搬 state/→flow/ + 清 artifacts brief + usage-log 活证 + 交付总结 + mirror + 最终验证 | AC-13 (a)(b)(c)(d) / AC-14 / AC-15 / AC-16 / AC-06 | chg-01 ~ chg-06 + chg-08 |
| chg-08（硬门禁六扩 TaskList + stdout + 提交信息） | base-role 硬门禁六扩触发场景 + stage-role 契约 7 反向豁免扩 + 自检方法扩 | AC-14 (文字扩展部分) / AC-15 / AC-06 | chg-01 |

### 10.4 最终 DAG

```
chg-01（repository-layout 契约底座）
   ├─→ chg-02（CLI 路径迁移 flow layout）
   ├─→ chg-03（validate_human_docs 重写删四类 brief）
   ├─→ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）
   │       ├─→ chg-05（done 交付总结扩效率与成本段）
   │       └─→ chg-06（harness-manager Step 4 派发硬门禁）
   └─→ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）
                    ↓
              chg-07（dogfood + scaffold_v2 mirror 收口）
```

- 共骨架（chg-01（repository-layout 契约底座））后 **4 路并行**：chg-02（CLI 路径迁移 flow layout）+ chg-03（validate_human_docs 重写删四类 brief）+ chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）+ chg-08（硬门禁六扩 TaskList + stdout + 提交信息）；
- chg-05（done 交付总结扩效率与成本段）+ chg-06（harness-manager Step 4 派发硬门禁）等 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）完成后并行；
- chg-07（dogfood + scaffold_v2 mirror 收口）等全部完成后单点收口。

### 10.5 default-pick 决策清单（planning 新增，承接 seed §6）

- **P-8**（见 §10.2）：独立 chg-08 承载用户强化规则。default-pick = 独立 chg-08。
- **P-9**：chg-04 内角色文件改动顺序（串行 vs 并行）？
  - default-pick = 串行（analyst → executing → regression → done → testing → acceptance → stage-role → usage-reporter 废止）
  - 理由：六文件相互耦合（都引用同一套路径契约），串行避免 cross-file 漏改 + diff 冲突。
- **P-10**：chg-07 dogfood 搬运 state/→flow/ 的原子性？
  - default-pick = 单 subagent 单 commit 完成（`git mv` 批量 + 最终 `git status` 验证）
  - 理由：避免搬一半 runtime 读写冲突；原子性优先。
- **P-11**：chg-05 pytest 是否依赖 LLM 触发 done subagent？
  - default-pick = 抽取轻量 Python 聚合 helper 给 pytest 直接调
  - 理由：避免 pytest 依赖 LLM runtime；helper 可复用，done subagent 自身也调。
- **P-12**：chg-06 base-role State 层自检规则段落归属（加到"经验沉淀规则"段末 vs 独立新段）？
  - default-pick = 独立新段（`## done 六层回顾 State 层自检`）
  - 理由：语义与经验沉淀不同（这是硬门禁级校验），独立成段清晰易读 + 未来扩展灵活。
- **P-13**：chg-08 CLI 代码层 render_work_item_id 审计是否纳入本 chg？
  - default-pick = 不纳入（仅在 session-memory 标为 TODO 给后续 req）
  - 理由：本 chg 语义聚焦"文字契约扩展"，CLI 代码审计是独立工作量，避免范围蔓延；不阻塞 req-41 落地。

### 10.6 契约 7 + 硬门禁六 + 批量列举子条款自检（本轮）

- 本轮 8 份 change.md + plan.md 首次引用 `req-41` / `chg-01`~`chg-08` / `reg-01` / `req-40` / `req-35` / `req-37` / `req-38` / `req-39` / `req-31` 等 id 均带 title 或 ≤ 15 字描述；
- DAG 表（§10.3）每行带完整 title；
- 批量列举场景（如依赖关系 "chg-01 + chg-04" / "chg-02 / chg-03 / chg-04 / chg-08"）每条带描述，无 `chg-01/02/03` 裸数字扫射；
- 本 session-memory 第 10 节自身自检：grep 命中行每条合规。

## 11. Results（Planning Part B 更新）

- `.workflow/state/sessions/req-41/chg-01..chg-08/{change.md, plan.md}`：8 chg × 2 文件 = 16 文件全填，按 analyst.md "对人文档产出契约" 中 change.md / plan.md 字段齐全；
- 本 session-memory：新增 §10 规划第 2 轮拆分决策 + §11 Results 更新；
- **不产出** `chg-NN-变更简报.md`：方向 C 本 req 自身就要废止四类 brief，analyst 不自相矛盾；artifacts 侧 CLI 自动生成的 8 个 `chg-NN-变更简报.md` 空壳由 chg-07（dogfood + scaffold_v2 mirror 收口）统一清理；
- **不产出** `需求摘要.md`（seed 阶段已决定不产，delivery_link 由 done.md 交付总结反向引用 requirement.md，无需独立摘要）。

## 12. Next Steps（Planning Part B 交接）

- 本 analyst subagent（planning 部分）本阶段完成后停下，不派发下层，不推进 stage，不 commit git；
- 按 briefing 要求：batched-report 每 chg 一行（id + title + 覆盖 AC + 依赖）+ default-pick（强化规则如何吞）+ DAG + 末尾收「本阶段已结束。」；
- 等待用户对"需求（seed 第 1 轮）+ 推荐拆分（planning 第 2 轮，8 chg + DAG）"整体评审 + 拍板一次（stage-role.md "stage 流转点豁免子条款" → `planning → ready_for_execution` 保留用户拍板）。

---

## 13. chg-07 dogfood 收口记录（executing 阶段最终汇报）

所有 8 个 chg（chg-01（repository-layout 契约底座）~ chg-08（硬门禁六扩 TaskList + stdout + 提交信息））已执行完毕，chg-07（dogfood 活证 + scaffold_v2 mirror 收口）自检全通：

- 机器型工件迁移：state/ → flow/ ✅
- 四类 brief 清理（artifacts/ req-41 范围）✅
- scaffold_v2 mirror diff = 0（context/ 子树）✅
- 契约 7：0 violations（37 文件）✅
- pytest：441 passed，1 pre-existing failure（test_smoke_req28）✅
- `harness validate --human-docs --requirement req-41`：2/2 present，exit 0 ✅
- usage-log 活证：flow/requirements/{slug}/usage-log.yaml ≥ 1 真实 entry ✅
- 本阶段已结束计数：9 个 session-memory 文件含本阶段已结束短语（AC-16 ≥ 4 ✅）

---

本阶段已结束。
