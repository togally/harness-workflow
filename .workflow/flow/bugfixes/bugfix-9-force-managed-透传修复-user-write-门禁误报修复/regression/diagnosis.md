# Regression Diagnosis — bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）

> ff 模式跳过 regression，本文件由 executing 阶段补写（最小可读形态）。

## Issue

PetMall 用户 `harness install --force-managed` 实测发现两个 bugfix-8 后遗症：
1. Bug A：`--force-managed` 在 `install` 路径下透传断链，用户改过的 managed 文件未被强制覆盖
2. Bug B：`user-write-protected-zones` 将 269 个 skill 工具产出文件误报为野文件

## Root Cause Analysis

**Bug A 根因**：
`install_repo`（`force_skill=False` 分支）调用 `init_repo(root, write_agents=..., write_claude=...)`，`init_repo` 签名无 `force_managed` 参数，内部硬编码 `force_managed=False` 传给 `_sync_requirement_workflow_managed_files`。chg-03 of bugfix-8 只在 skip 分支加了"透传防御" stderr 暴露问题，但没修 `init_repo` 透传链路。

关键代码路径（修复前）：
```
install_repo(force_managed=True)                # ← 入口收到 True
  → init_repo(write_agents, write_claude)       # ← 无 force_managed 参数
      → _sync_requirement_workflow_managed_files(..., force_managed=False)  # ← 硬编码 False
          → "skipping user-modified file ... (force_managed=False)"        # ← 误跳过
```

**Bug B 根因**：
`check_user_write_protected_zones` 的 `protected_zones` 包含 `.claude/skills`、`.codex/skills` 等 8 个 skill/commands 目录。这些目录是 `install_local_skills()` 纯工具产出，三级豁免（mirror / managed-files / whitelist）全部失效（mirror 用 `include_agents=False`，managed-files 只跟踪 `.workflow/`，whitelist substring 不匹配），导致所有 skill 文件误报为野文件。

## Routing Direction

- [x] Real issue → proceed to fix
- [ ] False positive → revert to previous stage

## 修复方案

- chg-01：`init_repo` 加 `force_managed: bool = False` 参数 + `install_repo` 调用透传
- chg-02：`protected_zones` 只保留 `.workflow`，删除所有 skill/commands 路径

## 测试用例设计

| ID | 描述 | 预期 |
|----|------|------|
| TC-A1 | `init_repo(root, ..., force_managed=True)` 调用链：用户改过的 managed 文件不出现 `skipping user-modified` | 覆盖成功，无误跳过 stderr |
| TC-A2 | grep `workflow_helpers.py` 所有 `init_repo(` call site，`install_repo` 的调用含 `force_managed=force_managed` | grep 验证通过 |
| TC-B1 | tmpdir user project + `.claude/skills/harness/SKILL.md` 工具产出 → `check_user_write_protected_zones` | exit 0，无 violation |
| TC-B2 | tmpdir user project + `.workflow/context/roles/my-custom.md` 野文件 → `check_user_write_protected_zones` | exit 1，报 violation |
