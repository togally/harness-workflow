# Session Memory — req-47 planning

## 1. Current Goal

执行 req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）planning stage Part B，承接 req_review Part A 已确认的 5 个默认决策（D-1 = A 复核 39 条 / D-2 = C 增量校准 / D-3 = B 首批 K + 留尾 / D-4 = A K=1 chg-7 / D-7 = A 必含 chg-7），产出 sug-audit-r2.md（39 条复核）+ roadmap-r2.md（chg 拆分 + 首批推荐）+ chg-01 工件（change.md / plan.md / 测试用例 §4）+ 池清理 5 条 sug 出池。

## 2. Context Chain

- Level 0: 主 agent → harness-manager (opus, harness next planning)
- Level 1: analyst-L1 (opus, req-47 planning Part B)

## 3. 已做工作

### 3.1 角色加载与上下文

- 读 runtime.yaml 确认 current_requirement = req-47, stage = planning, conversation_mode = harness（锁定）
- 读背景文件：tools/index.md / project-overview.md / context/index.md
- 加载角色链：base-role.md → stage-role.md → analyst.md
- 读经验文件：experience/roles/analyst.md
- 读约束文件：constraints/risk.md
- 模型一致性自检：role-model-map.yaml roles.analyst.model = opus，与 briefing 期望一致 ✓

### 3.2 关键产物读取

- 读 req-47 已有产物：requirement.md（5 节完整）+ requirement_review/session-memory.md（11 default-pick）
- 读 req-46 关键产物：sug-audit.md（45 条 round-1 验证表）+ roadmap.md（10 chg + DAG）+ chg-01/-02 change.md / plan.md（已落地参考）+ artifacts/main/.../交付总结.md（含 chg-7 testing 红线 P0 推荐 + 后续建议）
- 读 repository-layout.md §3 机器型路径表（防 chg-01 路径修复回归）
- 读 6 条新增 sug：sug-54（marker）/ sug-55（dev mode）/ sug-56（mirror dup）/ sug-57（partial_*）/ sug-58（chg-7 承接 marker）/ sug-59（路径漂移）
- 读 testing.md 现状：chg-02 已落"子进程 dogfood 红线"段；testing-no-destructive-git lint + tmpdir mock 红线 + commit revert dry-run 自动化 + dev mode flag 均**未做**
- 读 workflow_helpers.py:7438-7460 确认 chg-02 `_is_stage_work_done` executing 严格化（return False if not changes_dir.exists() / no session-memory.md）已落地
- 读 validate_contract.py 确认 artifact-placement lint 已落 `_MACHINE_TYPE_FILENAMES` 含 sug-audit.md / roadmap.md（chg-01 落地）

### 3.3 任务 1：sug-audit-r2.md（39 条复核）

- 落地：`.workflow/flow/requirements/req-47-{slug}/planning/sug-audit-r2.md`
- 覆盖：33 live + 6 新增 = 39 条全量
- 复核结果：34 live / 4 applied-out / 1 dup-of（sug-56） / 0 stale
- 关键变化：sug-38 由 applied-partial → applied-out（chg-02 已 dogfood 复验）；sug-35 由 live → applied-out（chg-01 已落 reviewer checklist）；6 条新 sug 全部归簇
- 主题簇变化：C-1 收尾（chg-02 吸收）；C-2 加 sug-59；C-4 加 sug-56；C-5 换血（移 sug-35，加 sug-54 / -57）；C-7 加 sug-55 / -58

### 3.4 任务 2：池清理执行落地

- **翻转滞留 + 双份残留** 4 条 + sug-46 双份处理：
  - sug-25（applied） → archive/（git mv）
  - sug-35（archived） → archive/（git mv）
  - sug-46 live 副本 → 删除（archive 副本保留 round-1 留痕）
  - sug-50（archived） → archive/（git mv）
- **新判 applied-out**（sug-38）：翻 frontmatter（`status: archived` + `applied_by_chg: chg-02` + `applied_at: 2026-04-28`）→ git mv 到 archive/
- 池容量数字：live 51 → 46（-5）；archive 9 → 13（+4）；total 60 → 59
- partial archive（sug-53）：保留 live + partial_* 字段不动（主因 sug-39 钩子未接通仍 pending）

### 3.5 任务 3：roadmap-r2.md

- 落地：`.workflow/flow/requirements/req-47-{slug}/planning/roadmap-r2.md`
- §1 校准 req-46 8 chg 现状（C-1 收尾；C-2 加 sug-59；C-4 加 sug-56；C-5 换血；C-7 加 sug-55 / sug-58）
- §2 6 条新 sug 归簇（sug-54 → chg-5 / sug-55 → chg-7 / sug-56 → chg-4 / sug-57 → chg-5 / sug-58 → chg-7 / sug-59 → chg-2）
- §3 完整 chg 列表：本 req 1 chg（首批）+ 留尾 8 chg
- §4 首批 chg-01 推荐 + AC 预览（≥ 6 条）+ DAG
- §5 留尾承接建议（下个 req K=2 chg-2 + chg-9）
- §6 工作量估算（本 req ~80-180k；留尾总量 ~700-1700k）
- §7 4 条 default-pick D-rm-1 ~ D-rm-4
- §8 风险 R1-R5

### 3.6 任务 4：chg-01 工件

- CLI 创建：`harness change "testing 红线 + safer dogfood + commit revert dry-run"` → CLI 实分配 chg-01（req-47 内首个）
- 落地：
  - `.workflow/flow/requirements/req-47-{slug}/changes/chg-01-testing-红线-safer-dogfood-commit-revert-dry-run/change.md`：7 节完整（Title / Background / Requirement / Scope Included+Excluded / Acceptance ≥ 7 AC / Risks ≥ 6 / Dependencies）
  - 同目录 `plan.md`：§1 9 Steps / §2 验证（unit + manual + AC mapping）/ §3 6 硬序约束 / §4 测试用例（10 TC，TC-01 ~ TC-10）
- §4 测试用例设计：
  - regression_scope: targeted（理由：文档 + lint + CLI 子命令，不动 _is_stage_work_done / runtime schema 等核心结构）
  - 波及接口清单：14 个文件（4 文档 + 5 src + 5 test + 4 mirror + sug 池清理）
  - 10 用例覆盖：lint 命中（TC-01）/ lint 白名单（TC-02）/ lint 边界（TC-03）/ archive revert 正例（TC-04）/ archive revert 反例（TC-05）/ dev mode 豁免（TC-06）/ 严格模式（TC-07）/ dogfood TC 字段 lint（TC-08）/ install --check subprocess（TC-09）/ 自身 dogfood feedback（TC-10）
  - 每个波及文件至少 1 条用例（≥ 1 覆盖原则）

### 3.7 chg-N1 → chg-01 命名同步

- roadmap-r2.md 中所有 chg-N1 引用更新为 chg-01（CLI 实分配）
- 表格中"对应 req-46 簇 = chg-7（C-7 簇）"标注保留簇语义追溯

## 4. Default-pick 决策清单

> 承接 req_review D-1 ~ D-11 + sug-audit-r2 D-r2-1 ~ D-r2-8；本 §列 planning Part B 新增决策。

### 4.1 sug-audit-r2 决策（已落产物 §5）

| 决策点 | default-pick | 状态 |
|-------|-------------|-----|
| D-r2-1 sug-38 archive 时机 | A（立即 archive）| 已落（任务 2 完成）|
| D-r2-2 sug-56 dup-of sug-21 | A（归 chg-4）| 已落 roadmap-r2 §2 |
| D-r2-3 sug-55 dev mode flag 归簇 | B（chg-7）| 已落 roadmap-r2 §2 |
| D-r2-4 sug-54 marker 契约归簇 | A（chg-5）| 已落 roadmap-r2 §2 |
| D-r2-5 sug-57 partial_* 字段语义化归簇 | A（chg-5）| 已落 roadmap-r2 §2 |
| D-r2-6 sug-46 双份残留处理 | A（删 live 留 archive）| 已落（任务 2 完成）|
| D-r2-7 partial archive 是否扩 sug 池语义 | A（保留 partial_*，待 chg-5 lint 化）| 已落 roadmap-r2 §3（chg-5 范围加 sug-57）|
| D-r2-8 sug-58 自动 archive | A（chg-01 acceptance PASS 后自动 archive）| 已落 chg-01 plan.md Step 7 |

### 4.2 roadmap-r2 决策（已落产物 §7）

| 决策点 | default-pick | 状态 |
|-------|-------------|-----|
| D-rm-1 chg-01 是否拆 chg-7a/-7b | A（单 chg 5 sug 一次性）| 已落 roadmap-r2 §3 |
| D-rm-2 chg-3 / chg-10 合并 | A（合并）| 已落 roadmap-r2 §3 |
| D-rm-3 首批 K 范围确认 | A（K=1）| 已落 roadmap-r2 §3 + §4 |
| D-rm-4 chg-01 与 chg-2 是否互锁 | A（独立可并行）| 已落 roadmap-r2 §4.3 + §5 |

## 5. 关键约束 / 假设

- **不重判 round-1 已结案 11 条**：D-1 = A 锁定（sug-09 / -12 / -17 / -25 / -32 / -40 / -44 / -45 / -46 / -49 / -50）
- **不动 sug 文件 priority frontmatter**：避免 churn（与 req-46 同款）；新优先级仅落 sug-audit-r2 / roadmap-r2
- **首批 K = 1**：D-4 = A 锁定 chg-01 = req-46 chg-7 簇；不与 chg-2（大）一起做避免超标
- **chg 编号方案**：本 req CLI 实分配 chg-01；roadmap-r2 标注"对应 req-46 chg-7 簇"语义追溯
- **路径自检硬门禁**：所有产物落 `.workflow/flow/requirements/req-47-{slug}/`（非 artifacts/）；chg-01 工件由 CLI 创建落正确路径
- **池清理时机分两阶段**：
  - 本 stage（planning）：仅做 D-1 未覆盖的"翻转滞留 4 条 + sug-46 双份 + sug-38 applied-out"5 条物理动作
  - chg-01 acceptance PASS 后：再清 sug-31 / -51 / -52 / -55 / -58 = 5 条（由 chg-01 plan.md Step 7 落地）

## 6. 模型一致性 + 上下文负载

- 模型一致性：role-model-map.yaml roles.analyst = opus；本 subagent 运行 model = claude-opus-4-7[1m]，一致 ✓
- 上下文负载评估：
  - 当前用量约 80-95k tokens（读完 base-role / stage-role / analyst.md 大文件 + sug-audit.md / roadmap.md / chg-01-02 plan.md / 39 条 sug frontmatter / repository-layout.md），未达 70% 阈值
  - 无需 /compact 或 /clear；可继续完成退出条件验证

## 7. analyst 专业化抽检反馈（experience/roles/analyst.md 模板）

| 字段 | 内容 |
|------|------|
| 抽检产物 | req-47 sug-audit-r2.md（§1 复核全量 39 条 + §3 归簇 + §5 决策）+ roadmap-r2.md（§3 chg 列表 + §4 首批 + §5 留尾）+ chg-01/change.md（§4 ≥ 5 AC + §6 ≥ 6 风险）+ chg-01/plan.md（§4 10 TC + §3 6 硬序约束）|
| 质量评分 | **B（持平）**——拆分粒度合理（5 sug 同根因合 1 chg）；依赖分析完整（DAG + 硬序约束）；风险识别覆盖 6 条 + 缓解措施；测试用例 10 条覆盖 7 AC；与 req-46 round-1 决策连贯（继承 D-1 ~ D-10 + 新增 D-r2 / D-rm）|
| 退化点明细 | 无明显退化；轻微瑕疵：roadmap-r2 §3 表格中"对应 req-46 簇"列标注 chg-7（C-7 簇），CLI 实分配 chg-01 与簇编号不同源；语义清晰但首读者需对照 |
| 是否触发 regression 回调 B | 否 |
| 抽检人 + 时间 + req 范围 | analyst-L1（opus）/ 2026-04-28 / req-47 |

## 8. 待处理捕获问题

- **sug-46 archive 副本 frontmatter 不一致**：archive 副本旧 status: applied（round-1 留痕）vs round-2 chg-02 落地是 archived；语义略乱但 D-r2-6 已选 A 保留现状；建议 chg-5（契约 lint 套件）落地时加 sug 池 frontmatter 一致性 lint
- **partial_* 字段尚无 lint**：sug-53 / sug-57 共同信号；chg-5 范围内已捕捉
- **chg-01 范围细节**（5 sug 五合一）：粒度可控（中工作量），plan.md §1 9 Steps 已细分；不再二次拆 chg-1a / chg-1b
- **chg-2 / chg-9 顺序**（sug-59 路径漂移 vs sug-39 钩子）：chg-2 plan.md 拆 step 时需明确顺序，本 req 不在首批，留下个 req

## 9. 退出条件 checklist

Part B（planning）退出条件（按 analyst.md §退出条件）：

- [x] 所有 chg 都有 `change.md`（目标 / 范围 / 验收）—— chg-01/change.md 7 节完整
- [x] 所有 chg 都有 `plan.md`（步骤 / 产物 / 依赖）—— chg-01/plan.md §1-§4 完整
- [x] 每个 plan.md 含 §4. 测试用例设计章节，波及接口有对应用例 —— chg-01/plan.md §4 含 14 个波及接口 + 10 TC（每个文件 ≥ 1 覆盖）
- [ ] `harness validate --contract test-case-design-completeness` exit code = 0（待 §10 验证执行）
- [x] 执行顺序已明确 —— chg-01/plan.md §3 6 硬序约束
- [ ] `harness validate --human-docs` exit code = 0（待 §10 验证执行；按 D-11 = B 留痕放行 raw_artifact 同 case）
- [ ] `harness validate --contract artifact-placement` exit code = 0（待 §10 验证执行）

经验沉淀检查：
- [x] 本 stage 主要复用 req-46 经验 + 既有契约（base-role / stage-role / analyst.md），无新可泛化经验需要沉淀（与 req-46 同模式）

上下文负载：
- 当前 ~80-95k tokens，未达 70%

## 10. 退出 validate 执行（已执行）

| validate 命令 | exit code | 处理 |
|--------------|----------|-----|
| `harness validate --human-docs` | **1** | raw_artifact + 交付总结都是 done 阶段产物（D-11 = B 留痕放行，与 req-43 / req-44 / req-45 / req-46 同 case；工具未做 stage 感知，历史 case 已批量放行）|
| `harness validate --contract artifact-placement` | **0** ✓ | PASS（强制硬门禁通过；artifacts/ 下无机器型文件）|
| `harness validate --contract test-case-design-completeness` | **1** | FAIL 项全部为 legacy（req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 8 chg + bugfix-5（同角色跨 stage 自动续跑硬门禁））；本 req-47 chg-01/plan.md 已含 §4 测试用例设计（line 197 `## 4. Test Case Design` + line 199 `regression_scope: targeted`），不在 FAIL 清单内；按 D-11 = B 留痕放行（lint 工具不区分 stage / 不区分 active vs legacy req）|

**自检结论**：本 req-47 维度三个 validate 全部合规；非本 req 范围的 legacy / 历史档 FAIL 项与 req-46 / req-43 ~ -45 同 case 留痕放行（不在 chg-01 工作范围；属 chg-5 契约 lint 套件落地范围 — 留尾下个 req 处理）。

## 11. Results

**verdict: PASS**。req-47 planning Part B 产出完整：

- sug-audit-r2.md（39 条复核 + 池清理 5 条出池数字 + D-r2-1 ~ D-r2-8）
- roadmap-r2.md（本 req 1 chg + 留尾 8 chg + 首批推荐 + DAG）
- chg-01/change.md + plan.md（含 §4 10 TC，targeted 范围）
- 池清理 5 条物理动作落地（live 46 / archive 13）
- 三个 validate：artifact-placement exit 0；human-docs / test-case-design-completeness 留痕放行（与 req-46 同 case）
- 等用户拍板首批 chg-01 范围后由主 agent / harness next 推 ready_for_execution / executing 阶段
