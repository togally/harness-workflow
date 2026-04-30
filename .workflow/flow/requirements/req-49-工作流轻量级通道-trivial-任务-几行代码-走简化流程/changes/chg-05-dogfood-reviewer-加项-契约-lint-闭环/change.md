---
id: chg-05
title: dogfood 活证 + reviewer 加项 + 契约 lint 闭环
req: req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）
trivial: false
---

# chg-05（dogfood 活证 + reviewer 加项 + 契约 lint 闭环）

## 1. Goal

用 `harness trivial` 修一处真 typo 跑通端到端（tmpdir + 子进程），验证 chg-01 ~ chg-04 全链路；扩 reviewer.md / review-checklist.md 加"trivial 通道边界检查"项；扩 `harness validate --contract all` 覆盖 trivial 通道路径，硬门禁六 / 七 / 契约 7 grep 自检全绿。

## 2. Scope

### In-Scope

1. **dogfood 活证场景**：在本仓库（harness-workflow）内挑选 1 处真实 typo（如某个 .md 文件中的拼写错误 / 标点错误），用 `harness trivial "<title>"` 跑端到端：
   - 创建 trivial 任务 → 编写 trivial-spec.md（3 段 ≤ 1 KB）→ 改 1 行代码 + 加 1 unit test → `harness next` 流转 done → 产 ≤ 200 字 `交付总结.md`；
   - 全链路 ≤ 5 次主 agent ↔ subagent 派发；
   - 落 session-memory 记录 dogfood 5 节点（创建 / executing / trivial-guard / done / 归档）；
   - dogfood TC：tmpdir 子进程版（独立测试 fixture）+ 真实 repo 版（dogfood log 记录）。
2. **dogfood 升级路径活证**：第 2 个 dogfood 场景：故意改 15 行（破阈值）→ 验证 trivial-guard 触发升级到 bugfix；落 dogfood log。
3. **dogfood 混合 chg 级活证**：第 3 个 dogfood 场景：在某真 bugfix 内拆 chg-01 trivial=true / chg-02 trivial=false → 验证 CLI dispatch 正确分流；落 dogfood log。
4. **reviewer.md 加 §trivial 通道边界检查段**：编辑 `.workflow/context/roles/reviewer.md` 加：
   ```markdown
   ## §trivial 通道边界检查（req-49 chg-05）

   reviewer 在审查含 trivial 路径的 chg 时，逐项核对：
   - trivial-guard 是否触发？若触发，升级路径是否完整（runtime upgraded_from 留痕 / bugfix.md 已创建）；
   - 工件 KB 限额：trivial-spec.md ≤ 1 KB / session-memory 跳过或 ≤ 500 字 / test-evidence 跳过 / acceptance-report 不产出；
   - chg 级 trivial flag 一致性：change.md frontmatter trivial 与 plan.md / executing 行为一致；
   - 升级路径数据保留：trivial-spec.md 在升级后保留（不删除），与 bugfix.md 共存。
   ```
5. **review-checklist.md 加 trivial 检查项**：编辑 `.workflow/context/team/review-checklist.md`（如不存在则创建）加 5 行 trivial 通道清单条目。
6. **扩 `harness validate --contract all`**：新增 `harness validate --contract trivial-channel` 覆盖：
   - trivial 任务工件 KB 限额；
   - chg 级 trivial flag 一致性；
   - upgraded_from 字段语义校验；
   - artifact-placement lint 对 trivial 通道路径 exit 0；
   - test-case-design-completeness lint 对 trivial 通道豁免（不要求 plan.md §4）。
7. **硬门禁六 / 七 / 契约 7 全仓 grep 自检**：所有 chg-01 ~ chg-05 落地的 stdout / 文档 / commit message：grep `(trivial|req-49|chg-NN)` 命中 = 0 裸 id。
8. **req-49 自身归档时跑通 dogfood**：归档前再次跑全链路活证（验证归档兼容 trivial 通道）。

### Out-of-Scope

- 任何 chg-01 ~ chg-04 的功能变更（chg-05 仅做收尾验证 + 文档加项）；
- 跨仓库 dogfood（仅本仓库 + tmpdir 子进程）。

## 3. Acceptance（对应 req-49 AC）

- AC-07（dogfood 活证：本 req 自带 1 个 `harness trivial` 端到端样例 + 所有产物落地 + 护栏通过 + `harness validate --contract all` exit 0）；
- AC-08（端到端节拍数 ≤ 5 次派发 + 无 testing/acceptance/planning 派发）；
- AC-09（硬门禁六 / 七 / 契约 7 全覆盖）；
- AC-10（artifact-placement lint exit 0）。

## 4. Dependencies

- 前置：chg-01 / chg-02 / chg-03 / chg-04 全部已落地；
- 后续：req-49 done 阶段六层回顾 + 归档。

## 5. Risk

- **风险**：dogfood 场景 1（真 typo 修复）找不到合适真实 typo → 改造成 fake typo 失去 dogfood 含义。**缓解**：dogfood 前先扫一遍 .md 文件 grep `\b(占行|的的|tmpdr|exsiting)\b` 等常见拼写错误；找不到时改用"补一个标点"作为 trivial 改动（同样符合白名单）。
- **风险**：trivial-guard 在本仓库全量 pytest 时长 > 30 秒（当前 ~600 用例）。**缓解**：dogfood 用 `--fast` flag（仅跑改动相关 test 模块），但需在 dogfood log 注明降级理由。
- **风险**：reviewer 加项可能与既有 review-checklist 冲突（重复检查）。**缓解**：先读 `.workflow/context/team/review-checklist.md` 现状，trivial 加项采用 §独立段而非穿插现有清单。
