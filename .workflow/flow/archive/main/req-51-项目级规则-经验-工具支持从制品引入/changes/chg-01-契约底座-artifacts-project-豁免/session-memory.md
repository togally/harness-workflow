# Session Memory — req-51（项目级规则-经验-工具支持从制品引入）/ chg-01（契约底座：artifacts/{branch}/project/ 豁免段 + 硬门禁五例外白名单 + scaffold_v2 mirror 同步）

> 本 session-memory.md 由 analyst Phase 3 占位创建；executing 阶段接手时按 `## 1. Current Goal` 与 plan.md 步骤填充实施记录。

## 1. Current Goal

按 chg-01 plan.md §1 / §2：在 `repository-layout.md` §1 / §2 / §3 / §3.2 落 4 处契约段落 + `harness-manager.md` 硬门禁五例外白名单加 1 条 + scaffold_v2 mirror 同步 + `artifacts/main/project/` 占位 README + 3 个 .gitkeep。

## 2. Context Chain

- Level 0: 主 agent → req-51 / executing stage（待派发）
- Level 1: analyst（opus）→ 完成 Phase 2 chg 拆分 + Phase 3 plan.md（已落盘，本文件由 analyst 占位）
- Level 2: executing（sonnet）→ 按 plan.md 实施（待派发）

## 3. Completed Tasks

- Step 1: 编辑 live `.workflow/flow/repository-layout.md`
  - §1 表中 artifacts 行追加注脚（变更点 A）
  - §2 白名单后追加 §2.1 项目级机器型豁免段（变更点 B）
  - §3 顶部插入豁免说明（变更点 C）
  - §3.2 顶部插入 bugfix 子树豁免澄清注（变更点 D）
- Step 2: 编辑 live `.workflow/context/roles/harness-manager.md`
  - 硬门禁五例外白名单追加 `artifacts/{branch}/project/` 条目（变更点 E）
- Step 3: 同步 scaffold_v2 mirror（硬门禁五合规）
  - `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md` 同步变更点 A/B/C/D
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` 同步变更点 E
- Step 4: 创建 `artifacts/main/project/` 占位
  - README.md + constraints/.gitkeep + experience/.gitkeep + tools/.gitkeep

## 4. Results（完整 lint stdout）

```
=== L1: 契约段落落地 ===
grep -c "artifacts/{branch}/project/" .workflow/flow/repository-layout.md
8

grep -n "项目级机器型豁免段" .workflow/flow/repository-layout.md
93:### 2.1 项目级机器型豁免段（req-51 OQ-1 = B-modified）

grep -n "OQ-1 = B-modified" .workflow/flow/repository-layout.md
93:（见上）
119:> **req-51 OQ-1 = B-modified 豁免说明**

=== L2: 硬门禁五白名单扩展 ===
grep -n "artifacts/{branch}/project/" .workflow/context/roles/harness-manager.md
48:- `artifacts/{branch}/project/`（req-51 OQ-1 = B-modified ...）
[注] plan.md L2 grep -B 3 语义不匹配（条目在 **例外白名单** 段第 11 行），白名单条目已在第 37-48 行之间，已在白名单段内。

=== L3: scaffold mirror 字节级同源 ===
diff -q .workflow/flow/repository-layout.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md
(silent — 完全一致)
diff -q .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
(silent — 完全一致)

=== L4: harness validate --contract all ===
(exit 0 — contract-7 warnings 为历史存量，非本 chg 引入)

=== L5: 占位 README + .gitkeep ===
artifacts/main/project/README.md: OK
artifacts/main/project/constraints/.gitkeep: OK
artifacts/main/project/experience/.gitkeep: OK
artifacts/main/project/tools/.gitkeep: OK
README.md 含 req-51 / OQ-1: OK
```

## 5. Next Steps

chg-02（升级保护 helper）接手。

## 6. default-pick 决策清单

- L2 lint grep -B 3 语义偏差：plan.md 中期望 grep -B 3 找到 "例外白名单" 3 行内，但实际条目在第 48 行、段头在第 37 行。白名单条目已确实在 **例外白名单** 段内。此为 plan.md 验收命令的计数偏差，非实施缺陷。已在 session-memory.md 显式记录。

✅ chg-01 完成
