# Done Report: req-28-批量建议合集（7条）

## 基本信息
- **需求 ID**: req-28
- **需求标题**: 批量建议合集（7条）— harness CLI 闭环修复 + 对人文档 SOP 收束
- **归档日期**: 2026-04-19

## 实现时长
- **总时长**: 0d 1h 22m（changes_review 起 → done 止，单日内完成）
- **requirement_review**: N/A（前置阶段，未记录 started_at 精细点位）
- **planning**: 0h 17m（13:46:40 → 14:03:56，changes_review → plan_review）
- **executing**: 0h 47m（14:11:43 → 14:58:50）
- **testing**: 0h 6m（14:58:50 → 15:05:32）
- **acceptance**: 0h 3m（15:05:32 → 15:08:56）
- **done**: ≈0h 10m（15:08:56 → 六层回顾完成）

> 数据来源：`state/requirements/req-28-批量建议合集（7条）.yaml` 中的 `started_at`、`completed_at`、`stage_timestamps`

---

## 执行摘要

req-28 是"批量建议合集"需求，聚焦两档目标：
- **档 1（硬阻塞）**：修复 harness CLI 在 bugfix / archive / suggest 三条链路的 4 个闭环 bug（sug-12/13/14/15 → chg-02/04/03/01）。
- **档 2（必做但非硬阻塞）**：补齐对人文档 SOP 的 3 个遗留（sug-09/10/11 → chg-05/06/07）。

**交付成果**：
- 7 个 change 全部落地，134 → 137 条测试全绿，对人文档 18/18 真实落盘。
- `harness bugfix → next → archive → suggest` 的闭环打通，cycle-detection 从 smoke 恢复为 24 条完整用例。
- 一次性 sweep 了 bugfix-3/4/5/6 四个历史受害者的归档。
- 首次端到端示范对人文档产出链（AC-11）。

**顺带暴露的新遗留**：
- AC-14 物理归档路径落 legacy `.workflow/flow/archive/main/bugfixes/`（`resolve_archive_root` 在 legacy 非空时降级），已起 sug-08 承接。

---

## 六层检查结果

### 第一层：Context（上下文层）
- [x] 7 条 sug 到 7 个 change 的拆解准确；AC-09~AC-15 一一对应。
- [x] `.workflow/context/experience/roles/executing.md` 新增"经验六：runtime.yaml 新增字段要 load 懒回填 + save 白名单双保"。
- [x] `.workflow/context/experience/tool/harness.md` 新增"create_suggestion 跨 archive+current 单调递增 + filename fallback"。
- [x] base-role.md / stage-role.md / done.md 的对人文档契约与 sug frontmatter 硬门禁均正确继承。

### 第二层：Tools（工具层）
- [x] `harness validate --human-docs --requirement req-28` 新 CLI 运行顺畅，从 0 → 16 → 17 → 18 逐步递进，缺失文件路径清晰可见。
- [x] `harness suggest` 三处 filename fallback 生效，对老无 frontmatter sug 友好。
- [x] `harness archive` 首次支持 bugfix 目录。
- **CLI 适配性问题**：`resolve_archive_root` 在 legacy 非空时降级为唯一路径不一致根因（sug-08 承接）。

### 第三层：Flow（流程层）
- [x] 7 个 change 的依赖拓扑 chg-01 → chg-02 → chg-03 → (chg-04/05/06 并行) → chg-07 完整走通，无阶段跳过。
- [x] 完整走 requirement_review → planning → executing → testing → acceptance → done 六阶段。
- [x] sug-12 修复后 bugfix 闭环正式打通，sweep 了 bugfix-3/4/5/6 4 个历史受害者；sug-15 修复后老 sug 能被操作；sug-08 的新建本身现场验证了编号单调递增修复。

### 第四层：State（状态层）
- [x] `runtime.yaml` 中 `active_requirements` 仅剩 req-28，bugfix-3/4/5/6 已清理干净。
- [x] `state/requirements/req-28-…yaml` 的 stage / status 随推进同步刷新（AC-12 扩展项）。
- [x] 新增字段 `operation_type` / `operation_target` 经 5 次 round-trip 验证仍在。

### 第五层：Evaluation（评估层）
- [x] testing 独立：`tests/test_req28_independent.py` 新增 3 条独立补测（round-trip / force-done 幂等 / 编号跨档单调），testing subagent 未被 executing 影响。
- [x] acceptance 独立：对照 AC-09~AC-15 逐条核查，AC-11 / AC-14 诚实标记"有条件通过"，未降低标准。
- [x] 7 AC 中 5 条通过（AC-09/10/12/13/15）+ 2 条有条件通过（AC-11 原缺交付总结、AC-14 path 偏差）。**AC-11 在本 done 阶段已通过 交付总结.md 产出完成闭环，最终达 18/18**。

### 第六层：Constraints（约束层）
- [x] 未触碰 `.workflow/flow/` 下现存 agent 过程文档（双轨不迁移契约 1）。
- [x] 对人文档全部落 `artifacts/main/requirements/req-28-…/`（契约 2 路径同构）。
- [x] 新 sug-08 带完整 YAML frontmatter（契约 6 / AC-15 硬门禁，虽然 title/priority 被 `create_suggestion` 简化为三字段，属 chg-01 已知限制，由 reviewer 软拦截）。

---

## 工具层适配发现

- `[手工 cat yaml 看 stage 进度]` → `[harness status / harness validate --human-docs]`：本 req 已消费 chg-05 产物，后续不再手工核对。
- `[合并建议的字段残缺]` → `create_suggestion` 目前只写 id/created_at/status 三字段，title/priority 缺失；建议下游 sug 新增时补 `harness suggest --priority high --title "..."` 入参，可新开 sug 承接（低优先）。

---

## 经验沉淀情况

| 经验文件 | 更新状态 | 内容 |
|---------|---------|------|
| `experience/roles/executing.md` | 已新增经验六 | runtime.yaml 新增字段 load 懒回填 + save 白名单双保 |
| `experience/tool/harness.md` | 已新增 | create_suggestion 跨 archive+current 单调递增 + filename fallback |
| `experience/roles/planning.md` | 无需更新 | 本轮拆分方案沿用主 agent 建议，未出现新风险 |
| `experience/roles/testing.md` | 无需更新 | 测试套路无新范式 |
| `experience/roles/acceptance.md` | 无需更新 | "有条件通过 + 起 sug 承接"已是现有 SOP |
| `experience/risk/known-risks.md` | 无需更新 | AC-14 路径偏差由 sug-08 单独承接 |

---

## 流程完整性评估

| 阶段 | 状态 | 备注 |
|------|------|------|
| requirement_review | 通过 | 7 sug 全部识别，AC-09~AC-15 完整 |
| planning | 通过 | 7 change 拆分合理，依赖拓扑清晰 |
| executing | 通过 | 14 份 变更简报 + 实施说明 齐全 |
| testing | 通过 | 137 全绿，独立补测 3 条 |
| acceptance | 通过 | 诚实标"有条件通过"，起 sug-08 承接 |
| done | 通过 | 18/18，六层回顾无遗漏 |

---

## 改进建议

> 建议：新开 bugfix-7 消费 sug-08，修 `resolve_archive_root` 判据（legacy 非空时新 bugfix 仍应落 primary 路径 `artifacts/{branch}/archive/bugfixes/`），可选追加 `harness migrate --archive` 子命令迁移 legacy 历史归档。

> 建议：后续 sug 新增时补 `create_suggestion` 对 title / priority / stage 字段的完整写入，或在 SOP 层强制 subagent 手动追加 frontmatter 后再调 CLI，避免契约 6 的字段残缺问题被 reviewer 重复拦截。

> 建议：sug-01-ff-auto 仍在 pending，与下一轮 ff 模式相关，可在新 req 周期内 apply 消费。

---

## 下一步行动

- **行动**：主 agent 决策是否立即执行 `harness archive req-28`；建议路径是先开 bugfix-7 消费 sug-08 修完 archive 路径偏差，再归档 req-28，这样 req-28 的归档产物能直接落在 primary 路径上，避免再次进入 legacy。
- **行动**：如主 agent 决定先归档再修，则 req-28 归档物也将落 legacy，后续需在 bugfix-7 中一并迁移。
