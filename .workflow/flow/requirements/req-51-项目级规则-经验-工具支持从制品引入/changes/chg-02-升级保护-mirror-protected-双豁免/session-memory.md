# Session Memory — req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护 helper：mirror 白名单 + protected-zones 双豁免（artifacts/{branch}/project/））

> 本 session-memory.md 由 analyst Phase 3 占位创建；executing 阶段接手时按 `## 1. Current Goal` 与 plan.md 步骤填充实施记录。

## 1. Current Goal

按 chg-02 plan.md §1 / §2：在 `_SCAFFOLD_V2_MIRROR_WHITELIST` tuple 末尾追加 `"artifacts/main/project/"` + `_install_self_audit` / `_sync_scaffold_v2_mirror_to_live` / `check_user_write_protected_zones` 三处 docstring 加 req-51 豁免说明 + 新增 `tests/test_req51_project_level_protection.py`（6 个 TC）。

## 2. Context Chain

- Level 0: 主 agent → req-51 / executing stage（待派发）
- Level 1: analyst（opus）→ Phase 2 + Phase 3 落盘（已完成）
- Level 2: executing（sonnet）→ 按 plan.md 实施（待派发，本 chg 依赖 chg-01 已 ship）

## 3. Completed Tasks

- Step 1: 编辑 `_SCAFFOLD_V2_MIRROR_WHITELIST` 末尾追加 `"artifacts/main/project/"` + 5 行注释（line 200）
- Step 2: `_install_self_audit` docstring 追加 req-51 / chg-02 注释段
- Step 3: `_sync_scaffold_v2_mirror_to_live` docstring 追加 req-51 / chg-02 注释段
- Step 4: `check_user_write_protected_zones` docstring 追加 req-51 豁免说明
- Step 5: 写新测试 `tests/test_req51_project_level_protection.py`（7 个 TC）

## 4. Results（完整 lint stdout）

```
=== L1: 常量改动落地 ===
grep -nE '"artifacts/main/project/"' src/harness_workflow/workflow_helpers.py
200:    "artifacts/main/project/",
3427:    `_SCAFFOLD_V2_MIRROR_WHITELIST` 新加的 "artifacts/main/project/" 条目作 defense-in-depth 兜底。
8139:    `_SCAFFOLD_V2_MIRROR_WHITELIST` 新加的 "artifacts/main/project/" 条目仅用于

=== L2: docstring 注释落地 ===
grep -cE "req-51（项目级规则-经验-工具支持从制品引入）/ chg-02" src/harness_workflow/workflow_helpers.py
3

grep -cE "req-51（项目级规则-经验-工具支持从制品引入）/ chg-02" src/harness_workflow/validate_contract.py
1

=== L3: protected_zones 保持仅 .workflow ===
grep -A 3 "protected_zones = \[" src/harness_workflow/validate_contract.py | grep -c '".workflow"'
1
grep -A 3 "protected_zones = \[" src/harness_workflow/validate_contract.py | grep -c "artifacts"
0

=== L4: 新测试全 PASS ===
pytest tests/test_req51_project_level_protection.py -v
7 passed in 3.95s
```

## 5. Next Steps

chg-03（加载层覆盖）接手。

## 6. default-pick 决策清单

（无争议点）

✅ chg-02 完成

---

## Round-2 Fix（subprocess python 路径硬编码 → sys.executable + PYTHONPATH）

**问题**：test_tc01 和 test_tc03 的 subprocess.run 调用使用 `sys.executable`，但 `sys.executable`（系统 python）无法找到 `harness_workflow` 模块，导致 2 个 FAIL。

**修复**：在 `test_req51_project_level_protection.py` 中新增 `_subprocess_env()` helper + `import os`；test_tc01（2 处 subprocess.run）+ test_tc03（2 处 subprocess.run）共 4 处加 `env=_subprocess_env()` 参数。

**验证**：修复后 `pytest tests/test_req51_project_level_protection.py -v` → 7 passed（含 round-2 修复的 tc01/tc03）。
