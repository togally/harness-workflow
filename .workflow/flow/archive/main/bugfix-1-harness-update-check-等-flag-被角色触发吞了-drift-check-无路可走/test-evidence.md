---
id: bugfix-1
title: harness update --check 等 flag 被角色触发吞了，drift check 无路可走
tested_at: 2026-04-22
tester: Subagent-L1（testing / Sonnet 4.6）
verdict: PASS
---

# Test Evidence — bugfix-1（harness update --check 等 flag 被角色触发吞了，drift check 无路可走）

## 测试环境

- 分支：main（HEAD = 1b0ee81）
- Python：3.14.3 via uv venv（project source install）
- pytest：9.0.3

## AC 验证结果

| AC | 描述 | 结果 | 证据 |
|----|------|------|------|
| AC-1 | `harness update --check` rc=0 + stdout 含 "Update summary" | PASS | `test_update_check_flag_routes_to_drift_preview` 绿；断言 `assertIn("Update summary", result.stdout)` + `assertNotIn("harness update 已重定义")` 通过 |
| AC-2 | `harness update --scan` rc=0 + stdout 含 "项目适配报告" | PASS | `test_update_scan_flag_routes_to_scan_project` 绿；断言 `assertIn("项目适配报告", result.stdout)` 通过 |
| AC-3 | `harness update --force-managed` 路由到 `install_repo(force_managed=True)` | PASS | cli.py L409 `getattr(args, "force_managed", False)` 入 `has_refresh_flag`；L422 `force_managed=getattr(args, "force_managed", False)` 传给 `install_repo`；逻辑分叉正确 |
| AC-4 | 裸 `harness update` rc=0 + 打印三行引导 | PASS | `test_update_bare_prints_role_contract_guidance` 绿；断言 `assertIn("harness update 已重定义为角色契约触发")` / `assertIn("生成项目现状报告")` / `assertIn("harness install")` 通过 |
| AC-5 | harness-manager.md + scaffold_v2 mirror 双处含 "无 flag" + "透传" | PASS | live: L164/L404 命中；scaffold_v2: L164/L400 命中（grep 输出见附录） |
| AC-6 | `grep -c 'harness update --check\|harness update --scan\|harness update$' tests/test_cli.py` ≥ 3 | PASS | 实测结果：4（>= 3 达标） |
| AC-7 | pytest 零新增失败（baseline ≥ 288 passed） | PASS | 实测 287 passed / 3 failed（pre-existing）/ 36 skipped；3 失败均为 req-29 / req-30 合规测试，与 bugfix-1 无关；新增 3 测试（`test_update_bare_prints_role_contract_guidance` / `test_update_check_flag_routes_to_drift_preview` / `test_update_scan_flag_routes_to_scan_project`）全绿；零新增失败 |
| AC-8 | scaffold_v2 mirror 同步（硬门禁五，req-34 / chg-04） | PASS | commit 1b0ee81 `--stat` 包含 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`；`diff` 二者仅剩 21 行 pre-existing 历史差异（title 缩写风格），bugfix-1 §A.3 / §A.4 / §A.5 + §3.1 表格内容完整对齐 |

## 合规扫描（evaluation/testing.md 五项）

### 1. R1 越界核查

`git diff --name-only 1b0ee81~1 1b0ee81` 输出：

```
.workflow/context/roles/harness-manager.md
src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md
src/harness_workflow/cli.py
tests/test_cli.py
```

均在 bugfix.md §6 R1 豁免范围（update_cmd handler + harness-manager.md §A.3-A.5 + scaffold_v2 mirror + tests/test_cli.py）。**越界 = 0，PASS**。

### 2. revert 抽样

```bash
git revert --no-commit 1b0ee81   # → REVERT_RC: 0，冲突 = 0
git reset --hard HEAD            # → RESET_RC: 0
```

**revert 无冲突，PASS**。

### 3. 契约 7 合规扫描

- bugfix.md L45 首引 `req-33` 带 title `（install 吸收 update 的 CLI 职责 + harness update 契约层重定义为触发 project-reporter）`：PASS
- bugfix.md L45 首引 `chg-02` 带 title `（harness update 角色契约层重定义为召唤 project-reporter）`：PASS
- commit 1b0ee81 message 第二行：`契约 7 首次引用 title：req-33（...）/ chg-02（...）/ chg-01（...）`：PASS

**契约 7，PASS**。

### 4. req-29（角色→模型映射）回归

```bash
git log --oneline -- .workflow/context/role-model-map.yaml
```

最近一次修改为 req-32 / chg-02 commit（`43fed86`），commit 1b0ee81 未触及该文件。**PASS**。

### 5. req-30（用户面 model 透出）回归

session-memory.md §1 开头标注 `Subagent-L1（testing / Sonnet 4.6）`；本测试记录标头同步标注。**PASS**。

## pytest 完整执行摘要

```
3 failed, 287 passed, 36 skipped in 30.58s
```

- 3 failed = pre-existing（`test_chg03_title_contract.py` × 2 + `test_smoke_req29.py` × 1），与 bugfix-1 无关
- bugfix-1 新增 3 测试全绿
- test_update_check_and_apply_refresh_qoder_skill_and_rule（既有断言已调整）：PASS
- 零新增失败

## 加分维度

| 维度 | 结果 |
|------|------|
| R1 越界 | 0 越界，全在豁免范围 |
| revert 抽样 | 无冲突，clean revert |
| 契约 7 | bugfix.md + commit message 双处首引均带 title |

## 结论

**PASS** — AC-1 至 AC-8 全部通过，合规扫描五项全 PASS，零新增测试失败。
建议下一步：`harness next` → acceptance。

## 附录：grep 原始输出

### AC-5 live harness-manager.md

```
164: | `harness update` | 裸调用（无 flag）：打印角色契约引导 + exit 0；...
165: | `harness update --check` | 有 flag：透传到 `install_repo(check=True, ...)`...
404: **无 flag 时**打印引导 + exit 0（保留 req-33 / chg-02 角色触发语义）；**任意刷新 flag...）存在时**透传到 `install_repo(...)` / `scan_project(...)`
```

### AC-5 scaffold_v2 harness-manager.md

```
164: | `harness update` | 裸调用（无 flag）：打印角色契约引导 + exit 0；...
165: | `harness update --check` | 有 flag：透传到 `install_repo(check=True, ...)`...
400: **无 flag 时**打印引导 + exit 0（保留 req-33 / chg-02 角色触发语义）；**任意刷新 flag...）存在时**透传到 `install_repo(...)` / `scan_project(...)`
```
