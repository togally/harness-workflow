---
id: chg-02
title: "升级保护 helper：mirror 白名单 + protected-zones 双豁免（artifacts/{branch}/project/）"
requirement: req-51
operation_type: change
---

# Change Definition

## Why（动机）

req-51（项目级规则-经验-工具支持从制品引入）OQ-4 = A 拍板：升级保护实现路径走"mirror 白名单 + protected-zones 双豁免"，最小改动 + 复用既有机制。chg-01（契约底座-artifacts-project-豁免）已落契约段落 + 硬门禁五例外白名单，但 helper 层若不配套打补丁：

1. `harness install` / `harness install --force-managed` / `harness update --check` 走到 `_sync_scaffold_v2_mirror_to_live` / `_install_self_audit` / `_managed_file_contents` / `_scaffold_v2_file_contents` 时，会把 `artifacts/{branch}/project/` 视为 mirror drift 并尝试覆盖（实际 mirror 不含该路径，会触发"only in live"反向清理路径，把项目级文件备份到 LEGACY_CLEANUP_ROOT）；
2. `check_user_write_protected_zones` 当前 `protected_zones = [".workflow"]`，**未覆盖** `artifacts/`；但 chg-01 把 `artifacts/{branch}/project/` 引入为合法机器型承载层后，下游用户在该路径手写文件时，**反而会被 § 现有契约的"机器型不入 artifacts/"判定为越界**——必须显式加豁免，让该三类目录路径被允许，且与现有"对人产物 artifacts/" 区分。

本 chg 是 AC-02（升级保护）/ AC-03（用户写保护豁免）/ AC-04（mirror 同步豁免）的真正落地点。

## Scope（范围）

### In Scope

1. **`workflow_helpers.py::_SCAFFOLD_V2_MIRROR_WHITELIST`**：新增 1 条 `artifacts/main/project/`（路径前缀，by-substring 匹配方式与现有条目一致）；
2. **`workflow_helpers.py::_install_self_audit`**：复用 `_SCAFFOLD_V2_MIRROR_WHITELIST` 已涵盖；同时验证"反向 live 多出"分支（约第 8152 行 `live_workflow.rglob`）只扫 `.workflow/`，已天然不扫 `artifacts/`，无需改动（plan.md §1 标注"无需改"理由）；
3. **`workflow_helpers.py::_sync_scaffold_v2_mirror_to_live`**：白名单复用 `_SCAFFOLD_V2_MIRROR_WHITELIST`，已涵盖；反向清理（约第 3506-3531 行 `stale_keys`）已 `if not relative.startswith(".workflow/"): continue` 过滤，已天然豁免 `artifacts/`，无需改动；
4. **`workflow_helpers.py::_managed_file_contents` / `_scaffold_v2_file_contents`**：mirror 数据源构建逻辑——这两个函数从 `src/harness_workflow/assets/scaffold_v2/` 读 mirror，scaffold_v2 mirror **本身不含** `artifacts/main/project/` 路径（chg-01 已自证），故这两个函数天然不会把项目级路径纳入 managed dict——无需改动，但需在测试 / 单测中显式断言以防回归；
5. **`validate_contract.py::check_user_write_protected_zones`**：`protected_zones` 当前仅 `[".workflow"]`，未覆盖 artifacts；本 chg **不**新增 artifacts/ 到保护区（与 chg-01 § 项目级豁免段策略一致），但需在文档注释中显式标注 "artifacts/{branch}/project/ 三类机器型目录由 §3 项目级豁免段允许，本 helper 不扫 artifacts/"，以防后续 chg 回退误加；
6. **新增** `tests/test_req51_project_level_protection.py`：覆盖 install / update / self-audit 全链路对 `artifacts/main/project/` 的保留行为。

### Out of Scope

- 契约文档段落（`repository-layout.md` / `harness-manager.md`）→ 已归 chg-01；
- 加载层（role-loading-protocol / tools-manager 项目级合并）→ 归 chg-03（加载层覆盖-tools-项目级合并）；
- 端到端 dogfood + AC-07 / AC-08 → 归 chg-04（dogfood端到端-ac07-08验证）；
- managed-files.json 登记机制改动 → OQ-4 = A 拍板"不进 managed_state"，本 chg 不动 `_load_managed_state` / `_save_managed_state` / `_refresh_managed_state` 数据流。

## 接口面（对外约束）

- **`_SCAFFOLD_V2_MIRROR_WHITELIST`**：tuple of substrings；新增 `artifacts/main/project/` 与现有"运行时态/业务态文件不同步"语义并列；
- **`check_user_write_protected_zones`**：返回 `int`（违规数）签名不变；豁免逻辑通过"扫描范围不含 artifacts/"天然实现；
- **`install_repo` / `update_repo` 主流程**：流程不变，仅依赖白名单 helper 自动跳过新条目；
- **新测试** `tests/test_req51_project_level_protection.py`：3 个核心 TC（安装保留 / force-managed 不覆盖 / self-audit 不报 drift）。

## 影响面

- **直接影响**：`workflow_helpers.py` 1 个常量改动（`_SCAFFOLD_V2_MIRROR_WHITELIST` 加 1 项）+ `validate_contract.py` 1 处文档注释 + 1 个新测试文件；
- **间接影响**：依赖 chg-01 已在 mirror 不含 `artifacts/main/project/` 路径（自动满足）；
- **下游用户感知**：本 chg 落地后，`harness install --force-managed` 在用户仓 `artifacts/main/project/constraints/my-rule.md` 等文件**真实保留**，AC-02 / AC-03 / AC-04 验证可绿。

## 验收边界（chg 级 PASS 条件）

- AC-02（升级保护）：tmpdir 写 `artifacts/main/project/constraints/my-rule.md` → `harness install --force-managed` → 文件 mtime / 内容不变；
- AC-03（用户写保护豁免）：tmpdir 用户项目模式（非 dev repo）下手写 `artifacts/main/project/{constraints,experience,tools}/x.md` → `harness validate --contract user-write-protected-zones` exit 0；同一 tmpdir 在 `.workflow/context/roles/x.md` 手写 → 仍 ABORT；
- AC-04（mirror 同步豁免）：`git diff --name-only` 含 `artifacts/main/project/` 路径时，scaffold_v2 mirror 路径不要求改动（本 chg 自身对照活证：grep `_SCAFFOLD_V2_MIRROR_WHITELIST` 命中新条目，无 mirror 同步要求）；
- `pytest tests/test_req51_project_level_protection.py -v` 全 PASS；
- `harness validate --contract all` exit 0。
