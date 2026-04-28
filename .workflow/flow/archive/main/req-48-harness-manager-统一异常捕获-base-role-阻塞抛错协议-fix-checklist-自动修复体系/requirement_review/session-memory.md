# Session Memory — req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）/ requirement_review

## 1. Current Goal

Part A：编写 `requirement.md`（§1 标题 / §2 目标 / §3 范围 / §4 验收标准 / §5 拆分规则），明确 6 大落地点 + 3 chg 拆分骨架，stage 流转前一次性 batched-report 给用户拍板。

## 2. Context Chain

- Level 0: 主 agent（technical-director）→ requirement_review stage 派发
- Level 1: 本 subagent（analyst / opus / Opus 4.7）→ Part A req_review

## 3. Completed Tasks

- [x] 读取 runtime.yaml / index.md / role-loading-protocol.md / base-role.md / stage-role.md / analyst.md
- [x] 模型一致性自检：role-model-map.yaml `analyst.model = opus` ✓ 与 Opus 4.7 一致
- [x] 自我介绍（按 base-role 硬门禁三模板）
- [x] 读取 req-48 当前骨架 + harness-manager.md / validate_contract.py 现状
- [x] 写 requirement.md（背景 / 目标 / 范围 / 验收标准 8 条 / 拆分规则 3 chg）
- [x] 路径自检：requirement.md 落 `.workflow/flow/requirements/req-48-{slug}/requirement.md`（机器型工件路径，符合 req-46 chg-01）

## 4. default-pick 决策清单

> 按 base-role 硬门禁四，本 stage 内争议点全部按 default-pick 推进，stage 流转前 batched-report 给用户。

| 决策点 | 选项 | default-pick | 理由 |
|-------|------|-------------|------|
| **S-1 chg 拆分粒度** | A. 3 chg（契约 + checklist 套件 + reviewer/dogfood）<br>B. ≥ 5 chg（每项独立）<br>C. 1 大 chg | **A** | 与 req-46 / req-47 同款"首批 K + 留尾"模式；3 chg 形成"协议底座 → 工程主菜 → 反馈闭环"递进，每 chg 独立可发版；≥ 5 chg 粒度过碎，1 chg 粒度过粗 reviewer 难审 |
| **C-1 错误协议载体形式** | A. stderr 文本协议（解析复杂）<br>B. JSON 结构化（需 parser）<br>C. exit code + 状态文件落点<br>D. **三层混合：stderr 文本 + 退出码 ≥ 64 + 状态文件 `.workflow/state/runtime-block.yaml`** | **D** | stderr 文本人眼可读 / 退出码机器可判 / 状态文件做权威记录三者互补；D 兼顾 A+B+C 的全部优势；harness-manager 解析时优先读状态文件，stderr 仅作日志；与 base-role 硬门禁二"操作日志"天然互通；细节落到 chg-01 的 error-protocol.md |
| **F-1 fix-checklist 一期范围** | A. 6 个全做<br>B. **首批 3 个（artifact-placement / schema-audit / missing-document）实战验证 + 留尾 3 个**<br>C. 仅 1 个最小验证 | **B** | 首批 3 个覆盖 PetMall 实证最高频痛点（150 文件迁移 / 旧目录迁移 / 文档缺失）；先打通端到端再补全；与 §AC-08 分批落地原则一致；6 个全做易在单 req 内超载，1 个验证不足以闭环 |
| **HM-2 修复路由权限** | A. **harness-manager 派发 fix-subagent 自动执行**<br>B. 仅给主 agent 提示自决<br>C. 加用户确认门禁 | **A** | 用户原话"由 harness-manager 捕获后..找到对应的修复方案..去修复"明确点 harness-manager 自动修复；fix-checklist 内置回退路径已是用户面 fallback；C 加用户确认违反 base-role 硬门禁四同阶段不打断；B 让主 agent 自决会失去统一捕获的意义 |
| **L-1 lint 改造范围** | A. 全部 10+ 个 contract 都改造<br>B. **仅首批 3 个（已写 fix-checklist 的）**<br>C. 仅 artifact-placement 1 个 | **B** | 与 F-1 配套（先写 checklist 再改 contract 输出，缺一不可）；剩余 contract 在留尾 chg 按需补；A 范围过大破坏分批；C 仅 1 个无法验证统一捕获机制 |
| **R-1 落地批次** | A. **首批 3 chg + 留尾 roadmap.md（与 req-46/47 同款）**<br>B. 一次性全做 6 个落地点 | **A** | 与现有 req-46 / req-47 实践一致；roadmap.md 在 done 阶段输出留尾给 req-49 / req-50；用户已习惯本模式；B 易超载且 reviewer 难审 |

## 5. Results

- **req-48 requirement.md** ≤ 1 屏（含背景 / 目标 / 6 大落地点 / 8 条 AC / 3 chg 拆分）已落地 `.workflow/flow/requirements/req-48-{slug}/requirement.md`；
- **3 chg 拆分骨架**：
  - chg-01（错误协议契约 + base-role 硬门禁八 + harness-manager 捕获职责）
  - chg-02（fix-checklist 套件首批 3 个 + lint 输出加 fix-checklist 指针 + 端到端协议跑通）
  - chg-03（reviewer 加项 + 端到端 dogfood pytest + roadmap 留尾输出）
- 路径自检通过，无机器型工件落到 artifacts/。

## 6. Next Steps

- 主 agent batched-report 给用户拍板：是否同意 default-pick 决策清单（S-1 / C-1 / F-1 / HM-2 / L-1 / R-1 共 6 项）；
- 用户确认后 → analyst 在同一会话续跑 Part B（planning），按 default-pick HM-1 = A 自主拆 chg；
- 退出条件自检见 §7。

## 7. 退出条件 checklist 自检

- [x] requirement.md 含 §1 标题 + §2 目标 + §3 范围 + §4 验收标准 + §5 拆分规则
- [x] session-memory.md 落 `.workflow/flow/requirements/req-48-{slug}/requirement_review/session-memory.md`（路径自检通过）
- [ ] `harness validate --contract artifact-placement` exit 0（待主 agent 触发执行）
- [ ] `harness validate --human-docs` exit 0（按 D-11=B 留痕放行模式，待主 agent 触发执行）

## 8. 经验沉淀候选

- "提示无工具"反模式可统一收敛为「检测 → state 留痕 → 抛标准化错误 → 上层捕获 → 按 checklist 修复」范式——已纳入 chg-01 的 error-protocol.md，不另开经验文件。
- contract lint 输出加 fix-checklist 指针字段是廉价改造（仅一行 print），但闭环价值巨大——经验沉淀到 `context/experience/roles/analyst.md`（拆分粒度章节），具体内容由 done 阶段六层回顾时统一回填。

## 9. 待处理捕获问题

- 无（所有争议点已收敛到 §4 default-pick 决策清单）。

## 10. 上下文消耗评估

- 当前会话累计读入：runtime.yaml / index.md / role-loading-protocol.md / base-role.md / stage-role.md / analyst.md / harness-manager.md / validate_contract.py 关键段 / req-48 旧 requirement.md
- 估算 ≈ 35–40k tokens（< 70% 阈值），无需 /compact，直接续 Part B 安全。
