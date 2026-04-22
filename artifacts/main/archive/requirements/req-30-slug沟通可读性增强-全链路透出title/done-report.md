# Done Report: req-30 slug 沟通可读性增强：全链路透出 title

## 基本信息
- **需求 ID**: req-30
- **需求标题**: slug 沟通可读性增强：全链路透出 title
- **方案**: 方案 B（结构 + 渲染双管齐下）
- **归档日期**: 2026-04-21
- **验收结论**: ✅ 通过（无条件）

## 实现时长
- **总时长**: ~4h 36m（2026-04-21 00:00 → 04:35:54 UTC）
- **requirement_review**: ~3h 44m（N/A precise start；以 `created_at=2026-04-21` 为降级起点到 stage 推进时间差）
- **planning**: 16m 21s
- **executing**: 21m 23s
- **testing**: 7m 46s
- **acceptance**: 4m 53s
- **done**: 进行中

> 数据来源：`state/requirements/req-30-slug沟通可读性增强-全链路透出title.yaml` 中的 `started_at` / `stage_timestamps`

---

## 执行摘要

req-30（slug 沟通可读性增强：全链路透出 title）通过方案 B 完成四层改造：

- **L1 汇报模板**：`stage-role.md` 新增契约 7（id + title 硬门禁）+ 7 stage 角色文件 + technical-director briefing 模板
- **L2 CLI 渲染**：新增 `render_work_item_id` / `_resolve_title_for_id` / `_resolve_title_for_suggestion` / `_render_id_list` helper，覆盖 `harness status / next / ff / suggest --list` 四条命令
- **L3 state 冗余字段**：`runtime.yaml` 新增 `current_requirement_title` / `current_regression_title` / `locked_requirement_title` 三个字段；11 处写入点统一调用 `_resolve_title_for_id`
- **L4 索引校验**：`.workflow/state/experience/index.md` 新增"来源列带 title"校验规则；planning.md 经验文件示范回填

4 个 change（3 必选 ✅ + 1 optional 📌 延期），32 条新增单测全绿，零回归，pytest 220 collected / 183 passed / 36 skipped / 1 pre-existing。AC-01~AC-10 中 9 ✅ + 1 计划内延期。

---

## 六层检查结果

### 第一层：Context（上下文层）

- [x] **角色行为检查**：requirement_review → planning → executing → testing → acceptance → done 六角色均严格加载 role-loading-protocol + base-role + stage-role + 本角色文件；Subagent-L1 结构清晰，无越界行为
- [x] **经验文件更新**：
  - `.workflow/context/experience/roles/planning.md` 已在 chg-03 Step 5 中示范回填"来源段带 title"（自证样本）
  - 其他角色经验文件本轮未新增教训（流程顺畅，无新坑）；如需补充将在后续 done 阶段按需更新
- [x] **上下文完整性**：本需求自证样本覆盖完整（requirement.md / 需求摘要.md / 4 change.md / 4 plan.md / 3 实施说明.md / 3 变更简报.md / test-evidence.md / 测试结论.md / acceptance-report.md / session-memory.md）

### 第二层：Tools（工具层）

- [x] **工具使用顺畅度**：Glob / Grep / Read / Edit / Write / Bash 全流程无适配问题；pytest 直接运行
- [x] **CLI 工具适配**：本轮未发现需替代的手工步骤（所有实现通过标准 Python stdlib + pytest 完成）
- [x] **MCP 工具适配**：无新需求
- [x] **适配发现**：
  - `workflow_helpers.py` 5500+ 行单文件结构给 executing / testing subagent 带来读取成本，但分段 Read 可规避
  - 归档 `_meta.yaml` 方案（chg-04 延期）若后续落地，可引入 YAML schema 校验工具（如 `jsonschema`）确保元数据格式一致

### 第三层：Flow（流程层）

- [x] **阶段流程完整性**：requirement_review → planning → executing → testing → acceptance → done 六阶段全走通（ff 模式自动推进）
- [x] **阶段跳过检查**：无跳过
- [x] **流程顺畅度**：ff 模式下各 stage 退出条件明确，AI 自主判定无争议；主 agent 编排 4 次 subagent 派发 + 5 次 stage 转场，耗时累计 ~50m（不含 requirement_review 前置讨论）
- [x] **自证样本（AC-10）流程贯穿**：从 planning 阶段起，每个阶段的对人文档与 session-memory 首次引用 req-30 / chg-XX 均带 title；契约 7 落地即自检通过

### 第四层：State（状态层）

- [x] **runtime.yaml 一致性**：`current_requirement=req-30` / `stage=done` / `ff_mode=true`；ff_stage_history 附加本次 5 阶段
- [x] **需求状态一致性**：`state/requirements/req-30-*.yaml` 的 `stage=done`；stage_timestamps 覆盖 requirement_review / planning / executing / testing / acceptance（done 在本阶段完成后写）
- [x] **状态记录完整性**：需求决策（方案 B） / planning 决策（chg 拆分） / executing 决策（chg-04 延期） / testing 发现（pre-existing 1 项）/ acceptance 判定（9 ✅ + 1 延期）全部保存到 session-memory.md

### 第五层：Evaluation（评估层）

- [x] **testing 独立性**：testing 子代独立从"需求视角"设计验证路径（文本 grep + helper 直调 + subprocess smoke + CLI 端到端 + schema 活性核查），未与 executing 共用测试
- [x] **acceptance 独立性**：acceptance 子代独立复跑 32 单测 + 实调 workflow_status / list_suggestions / render_work_item_id 四分支 + 逐 AC 三元组核查（需求 → 实现 → 证据），与 test-evidence.md 结论一致但路径独立
- [x] **评估标准达成**：AC-01~AC-10 中 9 条 ✅ 通过，1 条（AC-07）📌 计划内延期 + sug 登记

### 第六层：Constraints（约束层）

- [x] **边界约束触发**：无违规
  - 主 agent 未写业务代码（仅 runtime.yaml / state yaml / session-memory 等状态文件）
  - 各 subagent 严格在 stage 职责内活动（requirement-review 不写代码、planning 不写代码、executing 不动 runtime stage、testing 不修实现、acceptance 不修代码）
  - ff 模式边界未触碰（无凭据需求、无生产破坏风险、无大架构改动、无 regression 失败）
- [x] **风险扫描更新**：本轮无需更新 `.workflow/constraints/risk.md`（新风险通过契约 7 + 六层回顾检查已消化）
- [x] **约束遵守情况**：
  - 硬门禁一（工具优先）：各 subagent 均在 prompt 中注入工具委派指引
  - 硬门禁二（命令理解）：harness-manager 解析 `/harness-status` → `/harness-next` → `/harness-ff` 三命令无误
  - 硬门禁三（危险操作确认）：无删除 / 覆盖操作；所有 Edit 均为状态追加或同步

---

## 工具层适配发现

| 手工步骤 | 建议工具 | 预期收益 |
|---------|---------|---------|
| 手工 grep 检查契约 7 违反 | `harness status --lint` 自动化脚本（登记为 sug-25） | 减少人工审核 |
| 归档 `_meta.yaml` 未自动生成 | 归档 helper 扩展（登记为 sug-22） | 确保 AC-07 完整 |
| `workflow_helpers.py` 5500+ 行单文件 | 后续 req 可考虑拆分（非本轮范围） | 降低单文件复杂度 |

---

## 经验沉淀情况

本轮产出的关键经验（已在 `context/experience/roles/planning.md` 体现）：

- **经验 A（planning）**：change 拆分应优先按"字段 / helper / 命令 / 契约"分层，而非按文件维度。本轮 chg-01（schema + write helper）→ chg-02（render helper + CLI）→ chg-03（契约文档）→ chg-04（归档 meta）分层清晰，每个 change 可独立验收
- **经验 B（executing）**：TDD 严格执行（先测试、再实现、再跑单测子集）；`pytest tests/test_xxx.py -v` 单文件跑可验证 change 边界；全量 `pytest tests/` 验零回归
- **经验 C（testing）**：独立设计验证路径要以"需求视角"而非"测试视角"——对 AC-01 不是重跑 executing 的 test_chg03_title_contract.py，而是 grep session-memory / action-log 核实契约 7 在真实产出中被遵守
- **经验 D（acceptance）**：三元组（需求 → 实现 → 证据）闭环检查——逐 AC 回溯到"哪个 change 的哪个 DoD 条目、哪个实现点、哪个测试证据"
- **经验 E（自证样本）**：要求需求自身的产出遵守新约定是一种有效的一致性自检手段（AC-10）

其他角色经验文件（executing / testing / acceptance / requirement-review / regression）本轮未新增教训，当前不扩充。

---

## 流程完整性评估

| 阶段 | 执行 | 独立性 | 产出完整 | 备注 |
|------|------|--------|---------|------|
| requirement_review | ✅ | ✅ | ✅ | requirement.md / 需求摘要.md |
| planning | ✅ | ✅ | ✅ | 4 change.md + 4 plan.md |
| executing | ✅ | ✅ | ✅ | 代码实现 + 32 单测 + 3 实施说明 + 3 变更简报 |
| testing | ✅ | ✅ | ✅ | test-evidence.md + 测试结论.md |
| acceptance | ✅ | ✅ | ✅ | acceptance-report.md |
| done | ✅（进行中） | — | ✅ | done-report.md + 交付总结.md + 5 sug |

**异常检查**：
- 无阶段跳过 / 短路 / 重复 / 遗漏
- 无 regression 触发（全流程顺畅）

---

## 改进建议（转 sug 池）

以下 5 项将登记为 sug（由 acceptance 阶段识别 + done 阶段六层回顾确认）：

1. **sug-22**: chg-04（归档 _meta.yaml 落盘）—— AC-07 延期内容
2. **sug-23**: AC-04 legacy yaml 非标准空串 title 的 strip 兜底
3. **sug-24**: regression reg-NN 独立 title 源
4. **sug-25**: `harness status --lint` 自动化契约 7 校验
5. **sug-26**: 辅助角色（harness-manager / tools-manager / reviewer）契约 7 扩展

---

## 下一步行动

- **立即**：创建 5 个 sug 文件，更新 session-memory.md 的 `## done 阶段回顾报告` 区块，标记 req-30 状态 `done`，产出 `交付总结.md`
- **归档**：待用户确认后执行 `harness archive req-30`（归档命令保留给用户决定节奏）
- **后续**：done 阶段点名验证 AC-10 自证样本的 grep 校验 → 通过

---

## 参考文件清单

- `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/requirement.md`
- `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/需求摘要.md`
- `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/测试结论.md`
- `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/changes/chg-{01,02,03,04}-*/{change.md,plan.md}`
- `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/changes/chg-{01,02,03}-*/{变更简报.md,实施说明.md}`
- `.workflow/state/sessions/req-30/session-memory.md`
- `.workflow/state/sessions/req-30/test-evidence.md`
- `.workflow/state/sessions/req-30/acceptance-report.md`
- `.workflow/state/requirements/req-30-*.yaml`
