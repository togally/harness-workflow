# Session Memory — reg-05（archive 行为重定义：对人文档保留原位 + 不再生成摘要 md）

## 1. Current Goal

诊断 reg-05（archive 行为重定义：对人文档保留原位 + 不再生成摘要 md）：判定真实问题性 → 三层根因 → 三条候选方向 → 路由建议（含候选标题 ≤ 30 字）+ 残留冗余清理建议。诊断阶段不修代码 / 不修契约。

## 2. Current Status

- 已读：runtime.yaml / base-role.md / stage-role.md / regression.md / role-model-map.yaml / repository-layout.md。
- 已读：`workflow_helpers.py::archive_requirement`（line 6015~6234）+ `generate_requirement_artifact`（line 5311~5387）。
- 已盘点：`artifacts/main/requirements/` 顶层 16 份摘要 .md + 1 个 req-29 孤儿 folder（共 17 件冗余）；`artifacts/main/archive/requirements/` 14 个历史归档；`.workflow/flow/archive/main/` 已存在 req-41+ flow 归档子树。
- 已产出：regression.md（覆写）/ analysis.md（覆写）/ decision.md（覆写，含 frontmatter `route_to: requirement`）/ session-memory.md（追加，本文件）。

## 3. Validated Approaches

- `grep "archive_requirement\|def archive\|# archive" workflow_helpers.py` 准确定位入口（line 6015）。
- `ls artifacts/main/archive/requirements/req-37*` vs `ls .workflow/flow/archive/main/` 对比验证 req-41 chg-02 已落地 flow archive 路径，但 `archive_requirement` 内未对"对人 folder 是否挪"做区分。
- `ls artifacts/main/requirements/` 直接证实 17 件冗余（裸 16 份摘要 + 1 个 req-29 孤儿 folder），与用户截图一致。

## 4. Failed Paths

- 无（首轮诊断未走死路）。

## 5. Candidate Lessons

```markdown
### 2026-04-25 archive 行为与方向 C 关注点分离的错位
- Symptom: artifacts/main/requirements/ 顶层堆 17 件冗余（16 摘要 + 1 孤儿 folder）；用户反馈"对人文档不用归档"
- Cause: archive_requirement 实现停留在 req-39 时代"全搬走 + 生成摘要"假设；req-41（方向 C 关注点分离）落地后该假设已失效，但 helper 未同步重写
- Fix: 推荐方向 A——helper 改写为"对人不挪 + 摘要废止 + 机器型仍迁 .workflow/flow/archive/"；layout §3 / §4 微扩 archive 时落位表；用 req-42（archive 重定义：对人不挪 + 摘要废止）承接
- 通用经验: 当跨 req 重构关注点分离时（如 req-41），凡是涉及"打包 / 迁移 / 归档"的 helper 都应作为收口检查项，避免老 helper 残留旧时代假设；本经验不沉淀进 roles/regression.md（reg 级特异性高），但可在 done 阶段六层回顾"State 层"补一条"archive_* helper 是否同步关注点分离"
```

## 6. Next Steps

- 主 agent 走 batched-report：判决一行 + 三层根因 + 三方向 A/B/C（推荐 A，★★★★★）+ 路由建议 `--requirement`（候选标题 `archive 重定义：对人不挪 + 摘要废止`，22 字）+ 17 件冗余清理建议（执行阶段触发，需用户拍板）。
- 不派发下层 / 不推进 stage / 不 git commit / 不 `git rm` 17 件冗余。
- 收尾「本阶段已结束。」

## 7. Open Questions

- E-3（机器型归档去向）用户未明说；本诊断按方向 C 精神默认 `.workflow/flow/archive/`，若执行阶段（req-42 chg-01）发现需澄清，由 analyst 在 requirement_review 阶段对用户确认一次（不阻塞本 reg-05 路由）。

## 8. default-pick 决策清单（chg-05 决策批量化协议）

| # | 决策点 | 选项 | default-pick | 理由 |
|---|-------|------|-------------|------|
| 1 | 路由 `--bugfix` vs `--requirement` | `--bugfix` / `--requirement` | `--requirement` | 涉及 layout 契约扩 + helper 改 + 清理三面正交，超出 bugfix 单一改动颗粒 |
| 2 | 候选标题（≤ 30 字） | 三条候选 | `archive 重定义：对人不挪 + 摘要废止`（22 字） | 最贴用户原话 + 覆盖 A + B 诉求 |
| 3 | 推荐方向 A/B/C | A / B / C | A（★★★★★） | 最贴用户原话 + 改动面最小 + 完美契合方向 C 关注点分离 |
| 4 | 17 件冗余是否本阶段删 | 删 / 不删 | 不删 | 诊断师不修代码不删文件；交执行阶段触发数据销毁前用户拍板（硬门禁四例外 (i)） |
| 5 | E-3 机器型归档去向澄清 | 本阶段问 / 路由后再说 | 路由后再说 | 不阻塞本 reg-05 路由；执行阶段 analyst 在 requirement_review 顺带向用户确认 |
