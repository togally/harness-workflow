---
# bugfix-3: diagnostician fills the next-stage routing here
# (planning / executing / testing / acceptance / done / requirement_review / ready_for_execution).
# `harness next` reads this field first; if empty, falls back to text markers
# ("Route: xxx" / "harness next -> xxx"); otherwise default sequence.
route_to: "planning"
---

# Regression Decision

## 1. Decision Status

`confirmed`

诊断师独立判断结论：reg-01（analyst 机器型工件误落 artifacts/） 是真实问题，违规事实存在，契约文字 + lint 实现 + 角色文件 + checklist + briefing 五层都有缺口。属本 req-46（建议池梳理验证 + 优先级 roadmap + 分批落地） 范围内，用户已明确要求"在本次需求中优先修复"。

## 2. Final Notes

- 违规事实硬证据：`harness validate --contract artifact-placement` 现场命中 req-46 4 个文件中的 2 个（session-memory ×2）；剩余 2 个（sug-audit.md / roadmap.md）lint 漏命中，证明 lint 规则本身也有缺口（_MACHINE_TYPE_FILENAMES 集合不覆盖工作产出类）。
- 历史回溯：req-42 ~ req-45 全部正确落位，req-46 是**反例首例**，证明 req-46 复杂度突破契约边界，需要操作层硬门禁兜底。
- 关联 sug-35（reviewer checklist 扩 artifact-placement / test-case-design-completeness 三类 lint 条目补全）：本 reg-01 即 sug-35 未落地的实证，chg-0 应含 sug-35 落地。

## 3. Follow-Up

**路由**：`route_to: planning` → 回到 planning stage 让 analyst 设计 chg-0。

**新工件**：将由主 agent 用 `harness change "机器型工件路径修复 + 防再犯 lint"` 创建 chg-0（实际 id 由 harness change CLI 分配，期望命名模式 chg-0-机器型工件路径修复-防再犯-lint）。chg-0 **前置于** roadmap 已规划的 chg-1（按 priority 落地首批）/ chg-2（同上其他批） / chg-7（同上） 等首批。

**chg-0 设计要点**（详细草案见 session-memory.md §6 chg-0 草案，留待 analyst 在 planning stage 写正式 change.md / plan.md）：

1. **物理修文件**（4 个 git mv） — artifacts/main/requirements/req-46-.../{requirement-review,planning}/* → .workflow/flow/requirements/req-46-.../{requirement-review,planning}/*；清理空目录。
2. **briefing 注入路径条款** — harness-manager.md §3.6 派发协议加："派发 stage 角色时 briefing 必须显式列出该 stage 工件期望落点路径"。
3. **角色文件加硬门禁** — analyst.md / stage-role.md 加："产出任何 stage 工件前必读 repository-layout.md §3，对照路径表确认落点"。
4. **lint 接入退出门禁** — analyst.md 退出条件 + harness next 退出 gate 加 `--contract artifact-placement` 必跑；同时升级 lint 规则（路径模式 + 白名单豁免）。
5. **reviewer checklist 落 sug-35** — review-checklist.md 制品完整性章节加反向检查项 + sug-35 状态翻转 archived。
6. **scaffold_v2 mirror 同步** — 上述 .workflow/context/ + .workflow/flow/ 改动按 harness-manager.md 硬门禁五同步到 src/harness_workflow/assets/scaffold_v2/.workflow/。

**优先级**：P0（数据一致性 + 契约保护），**前置于** chg-1 / chg-2 / chg-7 首批。

**修复时序**：
1. analyst（planning stage 续跑）写 chg-0 的 change.md + plan.md；
2. 主 agent `harness change "机器型工件路径修复 + 防再犯 lint"` 创建 chg-0；
3. 进入 executing 跑 chg-0 全 6 改动 + scaffold_v2 mirror 同步 + 测试；
4. acceptance 通过后再回 planning 推进 chg-1 / chg-2 / chg-7 首批（chg-0 必须先 done）。

**Decision Status**：confirmed。
