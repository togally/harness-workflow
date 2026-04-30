# Session Memory — req-51（项目级规则-经验-工具支持从制品引入）/ analysis stage

## 1. Current Goal

- Phase 1 需求澄清：填充 `requirement.md` 的 Background / Goal / Scope / Acceptance Criteria 四段。
- Phase 2（chg 拆分 + plan.md）**未启动**，等用户对 §OQ 拍板后由 analyst 主控者继续。

## 2. Context Chain

- Level 0: 主 agent → analysis stage 主控
- Level 1: Subagent-L1（analyst / opus 4.7）→ Phase 1 需求澄清

## 3. Completed Tasks

- [x] 加载 base-role.md / stage-role.md / analyst.md（按 role-loading-protocol Step 1-7.5）
- [x] 模型自检：`role-model-map.yaml::roles.analyst.model = "opus"` 与本 subagent 运行 model 一致（Opus 4.7 1M context）
- [x] 读 `.workflow/evaluation/acceptance.md` / `.workflow/flow/repository-layout.md` 现有契约
- [x] 调研现状：`.workflow/context/{constraints,experience,tools}` 全局子树 + 已有 `.workflow/context/{team,project,checklists}` 项目独有子树 + 硬门禁五例外白名单
- [x] 调研冲突点：`bugfix-8`（用户项目区与开发期区分离）chg-04 `check_user_write_protected_zones` 实现读 `validate_contract.py:1107-1165`
- [x] 调研触发线索：`bugfix-11`（PetMallPlatform-artifacts 误放机器型流程文档）/ `sug-21` / `sug-15` / `req-34` / `req-36` 漂移系列
- [x] 写入 `requirement.md` 4 段：Background / Goal / Scope（含 §OQ）/ Acceptance Criteria（8 条 AC）

## 4. Phase 1 需求澄清

### 4.1 识别的核心痛点（向用户原话验证）

1. **下游用户仓（PetMallPlatform / uav 等）需要项目独有规则/经验/工具承载层**：当前 `.workflow/context/{team,project,checklists}` 已豁免，但 constraints / experience / tools 三大主力位置仍受硬门禁五守护，下游不可写。
2. **`harness install --force-managed` 升级覆盖项目级数据**：mirror sync 是 force 模式，下游做的改动会被回滚。
3. **`artifacts/` 字面贴合"制品包"但契约层禁止机器型入**：用户原话"放到制品包内"与 repository-layout §1/§3 正面冲突。
4. **`check_user_write_protected_zones` 把整个 `.workflow/` 列为写保护区**：下游手写 `.workflow/context/roles/my-rule.md` 直接 ABORT，提示"放 artifacts/" 但 artifacts 又禁机器型 —— **真空地带**。

### 4.2 识别的核心矛盾点（已落 §OQ）

- **OQ-1（路径选型）**：用户字面"制品包内" → `artifacts/`，但 repository-layout.md §1/§3 明文禁止机器型入 artifacts/，bugfix-11 / req-41 / chg-01 刚把这条契约升格为底座。**矛盾点最大**，default-pick = A（`.workflow/project/` 子树），需用户拍板是否接受这一字面理解的偏移。
- **OQ-2（冲突解决）**：项目级 vs 全局同名时谁优先；default-pick = 项目级覆盖全局。
- **OQ-3（覆盖面）**：是否包含 `roles/`；default-pick = 不含（只 constraints / experience / tools）。
- **OQ-4（升级保护实现）**：mirror + protected-zones 双豁免 vs managed-files 登记 + skip vs 新 flag；default-pick = 双豁免（最小改动）。
- **OQ-5（项目级 lint 边界）**：是否需"项目级不删全局硬门禁字段"lint；default-pick = 不增（followup sug 入池）。

### 4.3 default-pick 决策清单（按硬门禁四同阶段不打断 + stage-role.md 字段 3 留痕）

| OQ | 决策点 | default-pick | 一句话理由 |
|----|------|--------------|----------|
| OQ-1 | 项目级承载路径 | A：`.workflow/project/{constraints,experience,tools}/` | 不破坏 §1/§3 三大子树契约；与现有 `.workflow/context/project/` 同子树语义自然延伸 |
| OQ-2 | 冲突解决策略 | A：项目级覆盖全局 | 用户诉求"项目自己有规范"——若全局优先则项目级形同虚设 |
| OQ-3 | 项目级化覆盖面 | A：constraints / experience / tools 三类（不含 roles/） | 用户原话三类对齐；roles/ 影响调度链与硬门禁，风险高 |
| OQ-4 | 升级保护实现 | A：mirror + protected-zones 双豁免（不进 managed_state） | 复用 `_SCAFFOLD_V2_MIRROR_WHITELIST` + `protected_zones`，三处 helper 改动 |
| OQ-5 | 项目级 lint 边界 | A：不增 lint，文档警告 + done 抽查 | 优先解决路径承载，lint 作为 followup sug 入池 |

### 4.4 阻塞性矛盾点（用户必拍板）

- **OQ-1 是阻塞性矛盾**：与 `repository-layout.md` §1/§3 / bugfix-11 / req-41 chg-01 的契约底座正面冲突；analyst 已用 default-pick A（路径放 `.workflow/project/`，非 `artifacts/`）规避，但需用户**显式拍板接受**这一字面理解偏移；若坚持 B（落 `artifacts/`），需另开 req 推翻 §1/§3 底座，本 req 必须同步阻塞。
- 其他 OQ-2 ~ OQ-5 非阻塞，可按 default-pick 推进 Phase 2，用户在 Phase 1 ~ Phase 2 转交时一次性确认即可。

### 4.5 已识别的下游连带 sug（不在本 req 范围）

- 角色（roles/）项目级化（OQ-3 排除部分）→ 后续 req 单独评估
- role-model-map.yaml 项目级覆盖 → 后续 req 单独评估
- src/ 层 Python 工具实现的项目级注入 → 超出 .workflow/ 承载层范围
- 项目级数据 schema 演进 / 跨版本迁移工具 → 后续 sug
- "项目级不得删全局硬门禁字段" lint（OQ-5 = A 时入池）

## 5. Results

- `requirement.md`：填完 Background / Goal / Scope（含 §OQ 5 条）/ Acceptance Criteria（8 条 AC）。
- 本 `session-memory.md`：Phase 1 痛点 / 矛盾点 / OQ / default-pick 决策清单 + 阻塞点 + 连带 sug。
- **未**产出 `change.md` / `plan.md`（Phase 2 不在本任务范围）。
- **未**改动 src / 其他 req / runtime.yaml / role 文件 / 其他 .workflow/ 文件。

## 6. Next Steps

- 用户对 §OQ 5 条决策点逐条 / 一次性拍板（特别是 OQ-1 阻塞点）；
- 用户拍板后由 analyst 主控者按用户最终决策调整 requirement.md（如有修订）；
- Phase 2（chg 拆分 + plan.md）由 analyst 主控者继续，本 subagent 任务结束。

## 7. analyst 专业化抽检反馈（按 experience/roles/analyst.md 模板填）

| 字段 | 内容 |
|------|------|
| 抽检产物 | req-51（项目级规则-经验-工具支持从制品引入）/ analysis Phase 1 / requirement.md（Background + Goal + Scope + AC + §OQ） |
| 质量评分 | B（持平）—— Phase 1 需求澄清单元，争议点一次性汇总到 §OQ 含 default-pick + 拍板请求 |
| 退化点明细 | 无（持平档）；Phase 2 chg 拆分质量待 analyst 主控者后续抽检 |
| 是否触发 regression 回调 B | 否 |
| 抽检人 + 时间 + req 范围 | Subagent-L1 analyst / 2026-04-29 / req-51 Phase 1 |

## 8. 待处理捕获问题

- bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）虽已修，但其根因之一（下游用户仓的"项目自身规约 vs 工具自身规约"边界感缺失）正是本 req-51 要从契约层补齐的；本 req 落地后下游路径冲突类问题（PetMallPlatform 类）会在源头减少。
- sug-62（_next_req_id 跨 branch 不扫归档）与本 req 无直接耦合，独立处理。

---

**模型自检备注**：本 subagent 运行于 Opus 4.7 (1M context)，与 `role-model-map.yaml::roles.analyst.model = "opus"` 声明一致，无告警。

---

## Phase 2 + Phase 3 决策清单（2026-04-29 23:55 续跑落盘，本节由 analyst Phase 2/3 主控者追加）

### 9.1 chg 拆分结果（4 个 chg；3-5 区间内偏少粒度，避免碎片化）

| chg-id | 标题 | 一句话 scope |
|--------|------|------------|
| chg-01（契约底座-artifacts-project-豁免） | 契约底座：artifacts/{branch}/project/ 豁免段 + 硬门禁五例外白名单 + scaffold_v2 mirror 同步 | repository-layout.md §1 / §2 / §3 / §3.2 加 4 处契约段；harness-manager.md 硬门禁五例外白名单加 1 条；scaffold_v2 mirror 同步两文件；artifacts/main/project/ 占位 README + 3 .gitkeep |
| chg-02（升级保护-mirror-protected-双豁免） | 升级保护 helper：mirror 白名单 + protected-zones 双豁免（artifacts/{branch}/project/） | _SCAFFOLD_V2_MIRROR_WHITELIST 加 1 条；_install_self_audit / _sync_scaffold_v2_mirror_to_live / check_user_write_protected_zones docstring 加 req-51 豁免说明；新增 tests/test_req51_project_level_protection.py（6 TC） |
| chg-03（加载层覆盖-tools-项目级合并） | 加载层：role-loading-protocol 项目级合并段 + tools-manager 项目级合并/优先匹配 | role-loading-protocol.md 加 Step 7.6（项目级覆盖加载段）；tools-manager.md Step 2 加 Step 2.0（项目级合并段）；scaffold_v2 mirror 同步两文件；新增 helper _merge_project_level_files；新增 tests/test_req51_project_level_loading.py（≥ 6 TC） |
| chg-04（dogfood端到端-ac07-08验证） | dogfood 端到端 TC + AC-07/08 验证脚本（tmpdir 完整链路 + PetMallPlatform 真实仓引导） | 新增 tests/test_req51_project_level_dogfood.py（fixture + 7 TC）；artifacts/main/project/README.md 升级为 AC-08 PetMallPlatform 引导手册（约 60 行 runbook） |

### 9.2 整体 plan 关键决策

- **chg 数量 = 4**（在 3-5 拍板区间内偏少粒度）：理由 = 契约 / helper / 加载层 / dogfood 是天然四象限，强行切到 5 个会产生"chg-01a + chg-01b" 类伪边界；切到 3 个会让 chg-02 / chg-03 合并后跨 src + 文档两类改动，executing 单次实施难度偏大。
- **chg 间依赖关系**（最小依赖原则）：

  ```
  chg-01（契约底座）
       ├─→ chg-02（升级保护 helper）  [可并行]
       ├─→ chg-03（加载层）          [可并行]
       └─→ chg-04（dogfood 收口）   [前置：chg-01 + chg-02 + chg-03 全 ship]
  ```

  - chg-02 与 chg-03 改动文件不交叉（chg-02 改 src/，chg-03 改 .workflow/context/roles/ + 末尾 helper），可平行 ship；
  - chg-04 是 req-51 收口，必须在前三个 chg 全部 ship 后再 ship，否则 dogfood TC FAIL；
- **范围红线遵守**：所有 chg plan.md 全部使用 `artifacts/{branch}/project/`（具象示例 `artifacts/main/project/`）作为项目级承载路径，**未**回退为 `.workflow/project/`。chg-01 plan.md §1 变更点 A / B / C 全部以"OQ-1 = B-modified"为契约锚点，符合用户 2026-04-29 22:50 拍板。
- **contract 7 / 硬门禁六合规**：每个 chg.md / plan.md 首次引用 req-51 / chg-XX / sug-XX 时均采用 `{id}（{title}）` 形式（如 "req-51（项目级规则-经验-工具支持从制品引入）" / "chg-01（契约底座-artifacts-project-豁免）" / "sug-52（dogfood 实跑流程模板）" / "bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）"）；批量列举（如 chg-01 / chg-02 / chg-03 / chg-04）全部带 ≤ 15 字描述。
- **测试用例数总览**（每 chg ≥ 3 用例硬门禁）：
  - chg-01：5 TC（TC-01 ~ TC-05），覆盖 AC-01 / AC-04；
  - chg-02：7 TC（TC-Dogfood-01 ~ TC-Dogfood-03 + TC-04 ~ TC-07），覆盖 AC-02 / AC-03 / AC-04；
  - chg-03：7 TC（TC-01 ~ TC-07），覆盖 AC-04 / AC-05 / AC-06；
  - chg-04：7 TC（TC-Dogfood-01 ~ TC-Dogfood-07），覆盖 AC-02 / AC-03 / AC-05 / AC-07 / AC-08；
  - **合计 26 TC**，全部含对应 AC 字段非空，每个 dogfood TC 含 sug-52 必填字段（tmpdir / 子进程 / stdout / runtime / feedback / AC / P0）。
- **关键 lint 命令清单**（executing 不得偷换关键词，按 plan.md §4 字面）：
  - L1（contract 段）：`grep -c "artifacts/{branch}/project/" .workflow/flow/repository-layout.md` ≥ 3；`grep -nE "OQ-2 = A|OQ-3 = A" .workflow/context/roles/role-loading-protocol.md`
  - L2（白名单常量）：`grep -nE '"artifacts/main/project/"' src/harness_workflow/workflow_helpers.py` 命中 1 行
  - L3（protected_zones 不退化）：`grep -A 3 "protected_zones = \[" src/harness_workflow/validate_contract.py | grep -c "artifacts"` 期望 = 0
  - L4（mirror 字节同源）：`diff -q live mirror` 双双 silent（chg-01 / chg-03 各 2 文件）
  - L5（pytest）：`pytest tests/ -k "req51" -v` 期望全 PASS（≥ 19 TC：6 + 6 + 7）
  - L6（契约自检）：`harness validate --contract all` exit 0；`harness validate --human-docs` exit 0

### 9.3 跨 module / 跨契约风险（需主 agent 拍板？）

**无需主 agent 额外拍板**。所有跨契约改动均落在 OQ-1 ~ OQ-5 用户已拍板的边界内：

- chg-01 跨 `repository-layout.md` + `harness-manager.md`：在 OQ-1 = B-modified 拍板路径 + 现有硬门禁五例外白名单结构内扩展，不破坏底座；
- chg-02 跨 `workflow_helpers.py` + `validate_contract.py`：仅改 1 个常量 + 3 处 docstring，不改主流程逻辑；
- chg-03 跨 `role-loading-protocol.md` + `tools-manager.md` + 末尾 helper：均在文档新增段 + 30 行可选 helper 范围内，OQ-3 = A 已明确不动 roles/ 与 role-model-map.yaml；
- chg-04 端到端串联：仅消费前三个 chg 的成果，无新契约面。

如用户对 chg 数量 / 边界有异议，可一次性回 analyst 调整；否则按上表派发 executing。

### 9.4 写盘文件清单（本次 Phase 2/3 落盘）

```
.workflow/flow/requirements/req-51-项目级规则-经验-工具支持从制品引入/
├── analysis/
│   └── session-memory.md  ← 本节追加（## 9 Phase 2 + Phase 3 决策清单）
└── changes/
    ├── chg-01-契约底座-artifacts-project-豁免/
    │   ├── change.md
    │   ├── plan.md
    │   └── session-memory.md（占位）
    ├── chg-02-升级保护-mirror-protected-双豁免/
    │   ├── change.md
    │   ├── plan.md
    │   └── session-memory.md（占位）
    ├── chg-03-加载层覆盖-tools-项目级合并/
    │   ├── change.md
    │   ├── plan.md
    │   └── session-memory.md（占位 + decision-1：新增 _merge_project_level_files helper）
    └── chg-04-dogfood端到端-ac07-08验证/
        ├── change.md
        ├── plan.md
        └── session-memory.md（占位 + decision-1/2：feedback 软断言 + runbook 5 关键字）
```

**未改动**：
- `requirement.md`（Phase 1 + OQ Verdicts 已锁定，本次未碰）
- `runtime.yaml`（未推 next）
- 任何 src / tests / .workflow/ 上下文文件（plan.md per chg 是 plan，不是实施）

### 9.5 经验沉淀检查（base-role 经验沉淀规则）

本次 Phase 2 + Phase 3 触发的可泛化经验：**无新增**。

理由：req-51 chg 拆分模板（契约 / helper / 加载 / dogfood 四象限）已在历史 req（req-41 / req-32 / req-34 等）反复出现；本次未踩新坑，不沉淀。

