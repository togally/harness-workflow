---
id: chg-03
title: trivial 工件模板（含 chg 级路径选择 + 模板压缩到 ≤ 1.5 KB）
req: req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）
trivial: false
---

# chg-03（trivial 工件模板 + chg 级路径选择）

## 1. Goal

把 trivial 通道的工件模板从 uav bugfix-6 实测的 44 KB 压缩到 ≤ 1.5 KB，并支持单 bugfix / req 内**chg 级路径选择**（chg-01 走 trivial / chg-02 走标准），与 §2.3 实证活样本完全对齐。

## 2. Scope

### In-Scope

1. **trivial-spec.md 模板**（替代 bugfix.md）：≤ 1 KB，3 段固定结构：
   ```markdown
   ## 1. 问题（≤ 200 字）
   {一句话描述 trivial 改动针对的问题}

   ## 2. 修复（≤ 200 字）
   {一行代码 / 几行代码 + 改动文件清单}

   ## 3. 验证（≤ 200 字）
   {pytest 命令 + 关键断言}
   ```
   落点：`.workflow/flow/requirements/{req-id}-{slug}/trivial-define/trivial-spec.md`。
2. **session-memory.md 跳过**（default-pick D-8 = A）：trivial 通道 trivial_define / executing stage **不强制产出** session-memory.md；保留可选写入路径但 ≤ 500 字硬限。
3. **test-evidence.md 跳过**：trivial 通道不产出 test-evidence.md；pytest stdout 由 done 阶段直接 echo 到 `交付总结.md` §测试段（≤ 500 字）。
4. **acceptance-report.md 不产出**：trivial 通道无 acceptance stage，自然不产出（与 chg-01 状态机一致）。
5. **scaffold_v2 mirror 同步**：把 `trivial-spec.md` 模板加到 `scaffold_v2/.workflow/flow/requirements/_templates/trivial-spec.md`；确保 `harness install` 能 mirror 同步到新仓库。
6. **chg 级 trivial frontmatter**：`change.md` 加 `trivial: true|false` frontmatter 字段：
   - **default-pick D-10 = A**：frontmatter 字段而非文件名前缀或独立子目录；
   - **校验**：`workflow_helpers.py` 新增 `read_change_trivial_flag(change_md_path) -> bool`；
   - **CLI 行为**：`harness next` 在 req / bugfix 流转到 executing 时，先读当前 chg 的 trivial flag：
     - True → dispatch trivial executing 模式（跳 §4 测试用例设计校验，工件用 trivial 模板，跑 trivial-guard）；
     - False → 标准 executing 模式。
7. **executing trivial 模式**：在 `.workflow/context/roles/executing.md` 加 §trivial 模式段：
   - 不要求产出 session-memory.md / test-evidence.md / acceptance-report.md；
   - 工件落 `trivial-spec.md`（3 段 ≤ 1 KB）；
   - 跳过 plan.md §4 测试用例设计校验（仅要求新增 1 unit test，由 chg-04 trivial-guard 兜底）；
   - 完成后 stage 自动流转到 done（无 testing / acceptance）。
8. **trivial 路径硬规则文档**：在 `repository-layout.md` §3 加"trivial 任务子树"段：
   - 落位：`.workflow/flow/requirements/{req-id}-{slug}/trivial-define/`（与 bugfix 子树 `.workflow/flow/bugfixes/` 形态对齐，但用 req-id 编号空间，避免命名分裂）；
   - 工件清单：`trivial-spec.md`（必产）+ session-memory.md / test-evidence.md（可选 / 跳过）。

### Out-of-Scope

- trivial-guard 自动升级护栏（chg-04）；
- done 阶段交付总结模板精简（chg-04）；
- dogfood + reviewer 加项（chg-05）。

## 3. Acceptance（对应 req-49 AC）

- AC-N1（chg 级 trivial 判定可选 + change.md frontmatter `trivial: true|false` + CLI dispatch trivial / 标准 executing）；
- AC-N3（trivial-spec.md ≤ 1 KB / session-memory ≤ 500 字或跳过 / test-evidence ≤ 500 字或跳过 / acceptance-report 不产出 + scaffold mirror 同步）；
- AC-10（artifact-placement lint 对 trivial 通道工件落位 exit 0）。

## 4. Dependencies

- 前置：chg-01（task_type 枚举 + TRIVIAL_SEQUENCE 已落）+ chg-02（validate_trivial_eligibility helper 可被复用）；
- 后续：chg-04（trivial-guard 在 trivial executing 完成后自动跑）+ chg-05（dogfood 验证混合 chg 级路径）。

## 5. Risk

- **风险**：chg 级 trivial flag 与整任务 task_type=trivial 语义重叠（task_type=trivial 的 req 内所有 chg 是否都自动 trivial？）。**缓解**：明确语义——task_type=trivial 时整个任务走 TRIVIAL_SEQUENCE 不分 chg；task_type=bugfix / req 时 change.md frontmatter trivial=true 才单 chg 走 trivial executing；两路径互斥，用文档 + 单测覆盖边界。
- **风险**：scaffold_v2 mirror 同步遗漏 → 新仓库 `harness install` 后无 trivial-spec.md 模板。**缓解**：执行时跑 `diff -rq scaffold_v2/.workflow/flow/requirements/_templates/ .workflow/flow/requirements/_templates/` 断言无差异（chg-05 dogfood 兜底）。
