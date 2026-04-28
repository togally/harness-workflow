---
id: bugfix-7
stage: acceptance
created_at: 2026-04-28
---

# Acceptance Checklist — bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件）

## AC 校验矩阵

| AC | 描述（≤15字） | 判定 | 证据 |
|----|------------|------|------|
| AC-01 | 反向清理多余文件 | ✅ PASS | `workflow_helpers.py:3508` `stale_keys = set(managed_state.keys()) - set(mirror.keys())` 反向遍历 + `archived stale (mirror)` 日志；TC-01 PASS（test-evidence.md TC 覆盖矩阵第 1 行）；TC-01-check check 模式 dry-run PASS |
| AC-02 | 业务态保留不删 | ✅ PASS | `_SCAFFOLD_V2_MIRROR_WHITELIST` 白名单覆盖 flow/requirements/ / state/sessions/ / context/experience/regression/ 等；TC-02 PASS（test-evidence.md TC 覆盖矩阵第 3 行） |
| AC-03 | check 输出 venv vs HEAD | ✅ PASS | `harness_install.py:21-155` `_print_venv_check` 读 direct_url.json + git log 对比；TC-03 PASS（test-evidence.md TC 覆盖矩阵第 4 行）；dogfood ③ check stdout 正常含 `[install --check]` + venv info + HEAD commit（test-evidence.md §真实 dogfood 验证维度③） |
| AC-04 | 文档强提示 + check stdout | ✅ PASS | `README.md:46-58` 含"重要部署提示"段落："pipx 安装源是 GitHub 远程…本地未 push 的改动 reinstall 后拿不到最新内容"；TC-04 文档扫描 PASS（test-evidence.md TC 覆盖矩阵 TC-04 行） |
| AC-05 | drift>0 强提示 | ✅ PASS | `workflow_helpers.py` `_install_self_audit` ANSI 黄色 WARNING 非静默；TC-05 PASS（test-evidence.md TC 覆盖矩阵第 5 行） |
| AC-06 | tool_version 差异化 + mismatch 触发 full re-sync | ✅ PASS | `pyproject.toml:7` version=0.2.0；`workflow_helpers.py:23` `__version__="0.2.0"`；`workflow_helpers.py:3860-3866` mismatch 检测 `force_managed=True`；TC-06 PASS（test-evidence.md TC 覆盖矩阵第 6 行）；dogfood ④ tool_version mismatch 触发 full re-sync PASS（test-evidence.md §真实 dogfood 验证维度④） |
| AC-08 | active_list 非空跳过 prompt | ✅ PASS | `workflow_helpers.py:3797-3804` 已有 active_list 时直接 `selected = active_list` 跳过 questionary；TC-08 PASS（test-evidence.md TC 覆盖矩阵第 8 行）；dogfood ⑤ PASS（test-evidence.md §真实 dogfood 验证维度⑤） |
| AC-09 | _is_stage_work_done bugfix 模式 | ✅ PASS | `workflow_helpers.py:7622-7631` executing bugfix 分路检查 session-memory.md 含 ✅；`7602-7612` testing bugfix 分路检查 test-evidence.md；TC-09 PASS / TC-10 PASS（test-evidence.md TC 覆盖矩阵第 9-10 行） |
| chg-06 contingency | 不触发，转 sug 池 | ✅ PASS（不强求）| testing 判定不触发：chg-01 反向清理 + dogfood 5 维全覆盖，无"模糊状态"遗漏；diagnosis.md §9 记入 3 条 sug 候选（sug 池候选：harness install --smart / version bump 机制 / reviewer lint）（session-memory.md §chg-06 contingency 决定） |

**所有 AC 全部 PASS（chg-06 不强求，contingency 正常不触发）。**

---

## 部署同步检查（evaluation/acceptance.md §部署同步契约）

| 检查项 | 结果 |
|-------|------|
| `_is_stage_work_done` import 成功 | ✅ `python3 -c "from harness_workflow.workflow_helpers import _is_stage_work_done; print(_is_stage_work_done.__module__)"` → `harness_workflow.workflow_helpers` |
| venv mtime ≥ HEAD commit ts | ✅ venv_mtime=1777350372，HEAD_commit_ts=1777346904，diff=+3468s（venv 新于 HEAD，通过） |
| pipx local force install 验证 | ✅ testing 阶段 dogfood：`pipx install --force /local/path` 升级到 0.2.0；harness next 从 executing 推进到 testing 成功（session-memory.md §Testing Stage 附加：testing gate 修复） |

---

## validate 门禁

| 命令 | 结果 | 说明 |
|-----|------|------|
| `harness validate --human-docs --bugfix bugfix-7` | exit 1（D-11=B 留痕放行） | 缺 `回归简报.md`/`实施说明.md`/`交付总结.md`/`bugfix-交付总结.md`，均为后续阶段产物（regression-summary = done 阶段；实施说明/交付总结 = done 阶段），工具未做 stage 感知；与 req-43/44/45/46/47 同 case 留痕放行 |
| `harness validate --contract artifact-placement` | exit 0 PASS | `artifacts/` 下无机器型文件 |

---

## 人工验证等待项

以下项目需用户在 push + reinstall 后人工触发：

1. `git push origin main` 把 bugfix-7 改动推到 GitHub 远程
2. `pipx reinstall harness-workflow`（用户侧）
3. `cd /path/to/PetMallPlatform && harness install --agent claude --check`（dry-run 确认 venv vs HEAD）
4. `cd /path/to/PetMallPlatform && harness install --agent claude`（真同步，确认 usage-reporter.md 被清理、testing.md 更新到最新）
5. `cd /path/to/uav && harness install --agent claude`（同上，确认 analyst.md 等 4 个缺失文件补齐）

---

## §结论

**verdict: PASS**

AC-01 ~ AC-09 全部满足（chg-06 contingency 正常不触发，转 sug 池候选）。部署同步检查通过。validate --contract artifact-placement exit 0。human-docs exit 1 按 D-11=B 留痕放行（done 阶段产物）。

路由：→ `done`（`harness next`）
