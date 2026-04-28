# Acceptance Checklist — bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）

**验收官**：acceptance / sonnet
**日期**：2026-04-28

---

## 部署同步检查（acceptance.md §硬条目）

| 项 | 结果 |
|----|------|
| `_is_stage_work_done` import 成功 | ✅ module = `harness_workflow.workflow_helpers` |
| venv mtime vs HEAD commit ts | ✅ venv mtime 1777365027.1 ≥ HEAD commit ts 1777364092（差值 +935s） |
| HARNESS_DEV_MODE | 未设置（prod 路径），部署同步检查完整执行 |

---

## AC 校验矩阵

### chg-01（init_repo force_managed 透传修复）

| AC | 描述 | 签字 | 证据 |
|----|------|------|------|
| TC-A1 | `init_repo(force_managed=True)` → `_sync_requirement_workflow_managed_files(force_managed=True)`，用户改过的 managed 文件被覆盖，无 `skipping user-modified` stderr | ✅ | test-evidence.md TC-A1（正向）PASS；src grep 确认 `init_repo` L3678-3684 直接透传 `force_managed` 到 `_sync_requirement_workflow_managed_files` |
| TC-A1 反向 | `init_repo(force_managed=False)` 保留用户改动（语义保护对照组） | ✅ | test-evidence.md TC-A1（反向对照）PASS |
| TC-A2 | grep `workflow_helpers.py` 所有 `init_repo(` call site：`install_repo` 的调用含 `force_managed=force_managed`，无硬编码 `False` | ✅ | src 直接 grep 确认：L3851 = `init_repo(..., force_managed=force_managed)`；L8075 / harness_init.py L24 为 init 类调用，保持默认 `False`（正确语义），无任何 `force_managed=False` 显式硬编码 |
| dogfood-a | `harness install --check --force-managed`：stderr 首行含 `force_managed received: True`，全程无 `force_managed=False` skip 输出 | ✅ | 本次 acceptance dogfood 实测：`[install_repo] force_managed received: True`；grep `force_managed=False` 无结果 |

### chg-02（user-write-protected-zones 移除 skill/commands 扫描列表）

| AC | 描述 | 签字 | 证据 |
|----|------|------|------|
| TC-B1 | tmpdir user project + `.claude/skills/harness/SKILL.md`（工具产出）→ `check_user_write_protected_zones` exit 0（不报 violation） | ✅ | test-evidence.md TC-B1（unit + subprocess）均 PASS；src 直接核查 `validate_contract.py` L957-959 `protected_zones = [".workflow"]`，已移除所有 skill/commands 条目 |
| TC-B2 | tmpdir user project + `.workflow/context/roles/my-custom.md`（野文件）→ exit 1，stderr 含 violation + 路径（保护语义无损） | ✅ | test-evidence.md TC-B2（unit + subprocess）均 PASS；`.workflow` 仍在 protected_zones 中，真野文件仍被拦截 |
| dogfood-b | 本仓 `harness validate --contract user-write-protected-zones` exit 0（dev mode 豁免） | ✅ | 本次 acceptance 实测：`PASS: user-write-protected-zones`，exit 0 |

### 全量回归 + 合规扫描

| AC | 描述 | 签字 | 证据 |
|----|------|------|------|
| 全量 pytest 0 新增 fail | `pytest tests/` 0 新增 fail | ✅ | test-evidence.md：`13 failed, 695 passed, 40 skipped`，全部 13 fail 为 pre-existing 历史失败，与 bugfix-9 无关 |
| R1 越界 | chg-01 / chg-02 修改文件均在 bugfix.md §Fix Scope 指定范围内 | ✅ | test-evidence.md §R1 PASS |
| revert 抽样 | N/A（chg 在 working tree，无 commit sha，硬门禁禁止破坏性 git 命令） | N/A | test-evidence.md §revert 留痕 |
| 契约 7 | bugfix-9 产物目录内 id 首次引用均带描述 | ✅ | test-evidence.md §契约 7 PASS |
| req-29（角色→模型映射） | role-model-map.yaml 未变更，testing.model = "sonnet" 一致 | ✅ | test-evidence.md §req-29 PASS |
| req-30（用户面 model 透出） | testing 自我介绍含 `testing / sonnet` | ✅ | test-evidence.md §req-30 PASS |

---

## 归档前 Gate

| 检查项 | 结果 |
|--------|------|
| `harness validate --human-docs` | exit 1（4 pending：regression/executing/done/acceptance_done 文档，属 D-11=B 留痕放行；这些文档在 acceptance 及后续阶段产出，本阶段正常） |
| `harness validate --contract artifact-placement` | exit 0 PASS |
| runtime.yaml stage = acceptance | ✅ 与当前阶段一致 |

**human-docs pending 说明**：4 项 pending 文件（回归简报.md / 实施说明.md / 交付总结.md / bugfix-交付总结.md）均属后续阶段（executing/done/acceptance_done）产出，acceptance 阶段无法产出，按 D-11=B 留痕放行，不阻塞本次验收。

---

## 结论

**verdict = PASS**

- chg-01（init_repo force_managed 透传修复）：全部 TC 通过，源码核查一致，dogfood 实证有效。
- chg-02（user-write-protected-zones 移除 skill/commands 扫描列表）：全部 TC 通过，源码核查一致，dogfood 实证有效。
- 0 新增 fail，合规扫描全 PASS（revert N/A 豁免）。
- 部署同步检查：venv mtime ≥ HEAD commit ts，helper import 成功。

**建议人工 gate：通过，推进 `harness next` → done。**
