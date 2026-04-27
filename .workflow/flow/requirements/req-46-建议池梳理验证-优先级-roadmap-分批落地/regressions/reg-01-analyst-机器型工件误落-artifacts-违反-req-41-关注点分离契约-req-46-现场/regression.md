# Regression Intake

## 1. Issue Title

analyst 机器型工件误落 artifacts/ 违反 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 关注点分离契约（req-46（建议池梳理验证 + 优先级 roadmap + 分批落地） 现场）

## 2. Reported Concern

req-46（建议池梳理验证 + 优先级 roadmap + 分批落地） 在 requirement_review + planning 两 stage 期间，analyst 把 4 份机器型工件（`session-memory.md` ×2 / `sug-audit.md` / `roadmap.md`）误落到 `artifacts/main/requirements/req-46-.../requirement-review/` 与 `artifacts/main/requirements/req-46-.../planning/` 子目录，**直接违反** `.workflow/flow/repository-layout.md` §1（三大子树语义）/ §1.2（artifacts/ 下无 stage 子目录）/ §2（对人文档白名单不含 session-memory / sug-audit / roadmap）三条契约硬约束。

req-41 / chg-01 已立契约 + bugfix-6 / A4 已加固"任意任务类型均遵守此约束" + `artifact-placement` lint **已实现**（`src/harness_workflow/validate_contract.py:493`），仍然违反——契约存在 + lint 存在 + 角色未触发 = 流程层断点。

## 3. Current Behavior

**违规落点**（artifacts/ 下机器型）：

- `artifacts/main/requirements/req-46-.../requirement-review/session-memory.md`
- `artifacts/main/requirements/req-46-.../requirement-review/sug-audit.md`
- `artifacts/main/requirements/req-46-.../planning/session-memory.md`
- `artifacts/main/requirements/req-46-.../planning/roadmap.md`

**正确落点**（按 §1 / §3 应在）：

- `.workflow/flow/requirements/req-46-.../requirement-review/session-memory.md`
- `.workflow/flow/requirements/req-46-.../requirement-review/sug-audit.md`
- `.workflow/flow/requirements/req-46-.../planning/session-memory.md`
- `.workflow/flow/requirements/req-46-.../planning/roadmap.md`

**已正确落位（保留）**：

- `.workflow/flow/requirements/req-46-.../requirement.md`（机器型权威）
- `artifacts/main/requirements/req-46-.../requirement.md`（对人 raw 副本，§2 白名单）

**复现路径**：执行 `python3 -m harness_workflow.cli validate --contract artifact-placement` → 命中 4 条 req-46 违规（同时命中 reg-01..05 / bugfix-2/3/6 archive 历史脏数据，但本次焦点在 req-46 现场）。

**影响范围**：

1. 数据一致性：req-46 机器型与对人产物双写、相互漂移；artifacts/ 子树语义被污染（不再纯对人）。
2. 契约保护失效：req-41 + bugfix-6 立的契约成纸面，下一次 req 仍可能复发。
3. 链路下游：done 阶段六层回顾 State 层 grep 校验 / `harness archive` 行为 / `交付总结.md` 跨文档引用 frontmatter 都假设机器型在 flow/，会出现"找不到"或"双源歧义"。

## 4. Expected Outcome

1. 4 个误落文件物理回归 `.workflow/flow/requirements/req-46-.../{requirement-review,planning}/`，artifacts/ 子目录清空。
2. 加防再犯三层闸（briefing 注入路径 + 角色文件硬门禁 + lint 接入 stage 退出条件）。
3. scaffold_v2 mirror 同步上述角色文件改动（避免 `harness install` 把脏契约推到下游项目）。
4. 修复优先级 P0：必须**前置于** chg-1 / chg-2 / chg-7 首批，否则首批仍在违规面上工作。

## 5. Next Step

- analyst（路径回 planning）按本 reg-01 诊断结论 + chg-0 草案设计新 chg：路径修复 + 防再犯 lint。
- 主 agent 用 `harness change "机器型工件路径修复 + 防再犯 lint"` 创建 chg，前置于已规划的 chg-1 / chg-2 / chg-7。
- 修复落地前**禁止**继续 chg-1 等首批工作（避免在违规面上叠新工件）。
