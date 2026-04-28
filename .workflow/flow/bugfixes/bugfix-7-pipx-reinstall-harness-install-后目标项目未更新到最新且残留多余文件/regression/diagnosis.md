# Regression Diagnosis — bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件）

## 1. 问题描述（用户报告原文摘要）

> "当我们使用 pipx reinstall harness-workflow，然后在项目下去 install 之后，实际应该并没有更新成最新的，文件也有很多多余的。"

参考目标项目（read-only 扫描）：
- `/Users/jiazhiwei/claudeProject/PetMallPlatform`
- `/Users/jiazhiwei/claudeProject/uav`

## 2. 现象（实证）

### 2.1 "未更新到最新"维度

- **L2 部署层 vs L1 源码层**：pipx venv 装的是 commit `a801820`（archive: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）），但本地仓库 HEAD = `83bb612`（同 archive，仅多 1 个 archive commit）。两个 commit 之间在 `src/` 维度差 4724 字节、123 个 workflow_helpers 行；`scaffold_v2/.workflow/` 中 4 个文件**内容不同**：
  - `context/roles/analyst.md`（chg-01 sug-52 dogfood TC 字段）
  - `context/roles/done.md`（chg-01 sug-31 commit revert dry-run）
  - `evaluation/acceptance.md`
  - `evaluation/testing.md`（chg-01 破坏性 git 红线 + tmpdir 红线 + dogfood 标准模板）
- **pipx 安装源**：`pipx_metadata.json::main_package.package_or_url = "git+https://github.com/togally/harness-workflow.git"`；`direct_url.json::vcs_info.commit_id = a801820`。pipx reinstall 会从 GitHub 远程拉，但 chg-01 / chg-02 等改动尚未 push 到远程，因此即便 reinstall 也只能拿到 a801820。
- **L3 现场层 vs L1 源码层（HEAD）**：
  - PetMall `evaluation/testing.md` diff 47 行，缺 sug-51 / sug-52 红线段落（即 chg-01 内容）
  - PetMall `context/roles/done.md` diff 117 行，缺 Step 2.5 commit revert dry-run + 效率与成本聚合段
  - uav `context/index.md` 仍是 **req-40 之前**的版本（含 `requirement-review` + `planning` 两独立角色），HEAD 已合并为 `analyst`
  - uav `context/role-model-map.yaml` 仍是 **v1 schema**（HEAD = v2 schema，bugfix-5 stages 字段）
  - uav 完全缺失 4 个 HEAD scaffold 含有的文件：`context/roles/analyst.md` / `context/experience/roles/analyst.md` / `flow/repository-layout.md` / `tools/protocols/mcp-precheck.md`

### 2.2 "残留多余文件"维度（白名单过滤后真正的"非业务多余"）

PetMall：
- `.workflow/context/roles/usage-reporter.md`（在 scaffold 中曾存在，于 commit `c191ea5` "archive: req-42（archive 重定义：对人不挪 + 摘要废止）" **被删**；但目标项目仍保留旧文件，且 managed_files.json 里仍登记着 hash）

uav：
- `.workflow/context/experience/risk/frontend-readonly.md`（业务态用户经验，不在任何 scaffold 历史中；属用户业务态，**不算 scaffold 残留多余**）

PetMall `context/experience/regression/reg-05.md` / `reg-06.md` 经核对内容是 PetMall 项目自身需求 regression 沉淀的业务经验（非 scaffold 文件），属用户业务态，**不算 scaffold 残留多余**。

### 2.3 install_repo dogfood 实证（在 tmpdir，不污染目标项目）

在空 tmpdir 故意造 `usage-reporter.md`（多余）+ 改写 `evaluation/testing.md`（旧版），跑 `harness install --agent claude`：

| 现象 | 实际行为 | 期望行为 |
|------|---------|---------|
| `usage-reporter.md`（venv scaffold 也没有的文件） | self-audit stderr WARN `drift detected (only in live)`，但**保留不删** | 应清理或至少提示用户清理 |
| `testing.md`（user-modified，非 managed） | 实际被覆盖为新版（managed sync `_sync_requirement_workflow_managed_files` 走 "adopted" 路径） | 行为符合预期，但 mirror sync 阶段又日志 `skipped user-modified (mirror)`，前后矛盾的日志会让用户以为没更新 |

## 3. 根因分析（三维失配定位）

### L1 源码层（src/）失配

**根因 A — `_install_self_audit` 只警告不清理多余文件**（`workflow_helpers.py:8206-8257`）：

```python
# 4) 反向：live 多出 mirror 没有的非白名单文件
for live_path in sorted(live_workflow.rglob("*")):
    ...
    if relative not in mirror:
        print(f"[install_repo:self-audit] drift detected (only in live): {relative}", file=sys.stderr)
        drift_count += 1
```

只 stderr WARN + 计 drift_count，**无任何"reverse cleanup"分支**。`_sync_scaffold_v2_mirror_to_live` 的六分支也只覆盖正向：补齐 / 跳过 user-modified / 覆盖 force_managed，**没有 "live 有 mirror 无 → 删除"** 分支。

**根因 B — `LEGACY_CLEANUP_TARGETS` 是硬编码白名单**（`workflow_helpers.py:90-116`）：

只清理人工列出的 ~13 条"已知 legacy 路径"（如 `flow/`、`README.md`、`memory`、`runbooks` 等），**不基于 scaffold_v2 mirror 做 diff 反向清理**。当 scaffold 在某次 commit 中删除一个文件（如 req-42 删除 `usage-reporter.md`），开发者必须手工把它加进 `LEGACY_CLEANUP_TARGETS` 才能让旧项目同步删除——否则永久残留。

**根因 C — `tool_version` 字段无差异化版本号**（`pipx list` 输出 / `managed-files.json::tool_version`）：

```
package harness-workflow 0.1.0, installed using Python 3.14.3
```

`pyproject.toml::version = "0.1.0"` 自项目创建以来从未升级；managed-files.json 里 `tool_version: 0.1.0` 不变，**install 没有任何"目标项目当前 scaffold 版本 vs venv 自带 scaffold 版本"对比机制**——只能依赖 file-by-file hash diff，对"managed-files 已登记 + 模板被删"的情况盲区。

**根因 D — managed_files 反向同步缺位**：

`_sync_requirement_workflow_managed_files`（L3334+）按 `_scaffold_v2_file_contents` 当前 mirror 渲染 expected_files；当 mirror 中已不存在某文件、但 managed-files.json 里仍有该文件登记时（如 PetMall `usage-reporter.md`），代码**不进入 sync 循环**（mirror dict 不含此 key），**也不查询 managed-files 反向 dead entries**——同样无清理。

### L2 部署层（pipx venv）失配

**根因 E — pipx 装的是 GitHub 远程 main，本地仓 HEAD 未 push**：

- `direct_url.json::commit_id = a801820`（远程 main 头部）
- 本地 `git log a801820..HEAD` = `83bb612 archive: req-46...`（仅 1 个 archive commit，但 archive 之前的 chg-01 / chg-02 也未推到远程）

实际 chg-01 / chg-02 的源码改动（`_revert_dry_run_self_check` / scaffold testing.md / done.md / acceptance.md / analyst.md）已写到本地 src/，但**因为 archive commit 之前的链条**（req-46 / req-47 在 archive 时被一并 squash 到 archive commit）**也未 push**，所以 pipx 拉远程拿不到。这是部署层与源码层的**版本失配**根因。

**根因 F — pipx reinstall 不是 force-rebuild from local**：

如果用户在本地仓库根目录跑 `pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow`（指向本地 repo），可立即拿到 HEAD 版本；但当前 venv `package_or_url` 是 GitHub URL，`pipx reinstall harness-workflow` 默认走"按当前 spec 重装"，仍命中 GitHub。

**根因 G — `harness install --check` 的 `_print_venv_check` 只在 venv `harness_install.py` 含此 helper 时生效**：

`_print_venv_check` 是 chg-01 sug-55 的产物，**位于 venv 中的旧版 `harness_install.py` 没有此函数**（diff 实测 venv = 47 行，HEAD = 117 行）。所以即使用户跑 `harness install --check` 也不会看到任何 venv mtime vs HEAD 对比报告——这个"自检"功能本身也只能在已含本次更新的版本里生效，是个"先有鸡还是先有蛋"的部署问题。

### L3 现场层（目标项目 .workflow/）失配

**根因 H — 两类项目状态都被命中根因 A/B/D**：

- PetMall：上次 install 在 req-42 之前（`usage-reporter.md` 被 managed-files 登记 → 后续 install 看到 mirror 中已删但本地存在 → mirror sync 跳过、self-audit 仅警告、cleanup 不在白名单 → 永久残留）
- uav：上次 install 在 req-40 之前（无 `analyst.md` 登记，managed sync 走"create"分支应该补齐）；但 venv scaffold 也是 a801820，本身就缺 `analyst.md` 等 4 个文件，**install 拿什么也补不出来**——这是 L2 失配传导到 L3 的现场表现。

### 三维失配联动（`经验十：三维失配诊断模板`套用）

| 维度 | 检查方式 | 失配症状 |
|------|---------|---------|
| L1 契约/源码 | grep `workflow_helpers.py::_install_self_audit` + `_sync_scaffold_v2_mirror_to_live` | 只警告不清理；缺反向 dead-file 删除分支；`tool_version` 不差异化 |
| L2 部署 | `direct_url.json::commit_id` vs 本地 HEAD；venv mtime vs repo mtime | venv 拉自 GitHub a801820；repo 本地 HEAD = 83bb612；本地未 push（chg-01 / chg-02 改动未上远程） |
| L3 现场 | `diff -rq venv/scaffold_v2 vs target/.workflow/` | 用户感知"没更新"= L2 venv 滞后导致 mirror 也滞后；用户感知"多余"= L1 反向清理缺失 |

**根本根因（一句话）**：本仓库 HEAD 改动**未 push 到 GitHub 远程**（L2 失配） + **install 缺反向清理多余文件机制**（L1 失配根因 A/B/D）双因素叠加，才呈现用户报告的"reinstall + install 没更新且多余"现象。

## 4. 受影响范围

- 任何 `pipx install ... github.com/togally/harness-workflow.git` 安装的目标项目，且本次仓库改动未 push 时
- 历史经过多轮 install 的目标项目（managed-files.json 累积旧文件 hash 登记，scaffold 已删的文件不会被反向清理）
- 任何依赖 `tool_version` 做版本对比的工具链（实际无效，0.1.0 永不变）

## 5. 复现步骤（expected vs actual）

1. 在主仓库做改动（如修改 scaffold_v2/.workflow/evaluation/testing.md）
2. 改动**已 commit 但未 push**到 GitHub
3. `pipx reinstall harness-workflow`
4. `cd /path/to/target_project && harness install --agent claude`

**Expected**：目标项目的 `.workflow/evaluation/testing.md` 同步到本次 commit 的最新内容；scaffold 已删除的文件被清理。

**Actual**：
- `testing.md` 仍是 GitHub 远程版本（不含本次 commit 改动）—— 因为 venv 装的是远程 commit
- 此前历史 install 留下的"已被 scaffold 删除的文件"（如 `usage-reporter.md`）仍残留在目标项目
- `harness install` stdout/stderr 没有任何明显的"diff 概览/版本号对比"，用户只能通过逐文件对照才知道更新没生效

## 6. 路由决策

**判定：真实问题**（非误判，三维都有具体证据）。

**推荐路由：进入 executing 修复**。理由：
- 根因 A/B/D（install 反向清理 + tool_version 差异化）是**实现层**问题，无需重新规划需求；
- 根因 E/F（pipx 部署 vs 远程 push 节奏）是**操作流程**问题，可通过文档（README / harness install --check 强提示）+ 让 `harness install --check` 始终输出 venv vs HEAD 比对（即便 venv 是旧版没 helper，让 CLI 子命令自己跑 git log 对比）解决；
- 不需要 `requirement_review` 重写需求（用户报告即需求）。

**不需要 required-inputs**：所有诊断证据已收集完毕，不需要用户额外提供信息。

## 测试用例设计

> regression_scope: targeted
> 波及接口清单（修复将涉及）：
> - `src/harness_workflow/workflow_helpers.py::_install_self_audit`（加 reverse-cleanup 分支）
> - `src/harness_workflow/workflow_helpers.py::_sync_scaffold_v2_mirror_to_live`（增 dead-file 分支或前置预检）
> - `src/harness_workflow/workflow_helpers.py::LEGACY_CLEANUP_TARGETS`（迁移到 mirror diff 自动生成）
> - `src/harness_workflow/workflow_helpers.py::_load_managed_state` / `_refresh_managed_state`（managed-files dead entries 反向清理）
> - `pyproject.toml::version`（从 0.1.0 升到差异化版本号，或在构建时注入 git sha）
> - `src/harness_workflow/tools/harness_install.py`（强化 `--check` 输出 venv vs git log 对比报告，使其在旧版 venv 也能跑）
> - 新增 dogfood 测试 `tests/test_install_reverse_cleanup.py`

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | 目标项目 .workflow/context/roles/usage-reporter.md 存在（mirror 已删除该文件，managed-files.json 仍登记） + 跑 `harness install --agent claude` | 该文件被删除（或 archived 到 LEGACY_CLEANUP_ROOT），stdout 含 `removed stale (mirror) .workflow/context/roles/usage-reporter.md`；managed-files.json 移除该 key | AC-01 反向清理多余文件 | P0 |
| TC-02 | 目标项目存在用户业务态文件（如 `flow/requirements/req-99/...`、`state/sessions/...`、`context/experience/regression/reg-99.md`） + 跑 `harness install` | 用户业务态文件**保留不动**；只清理 scaffold 已删的"模板态多余" | AC-02 业务态保留 | P0 |
| TC-03 | tmpdir 创建空 repo + `harness install --check` | stdout 输出当前 venv 安装源 commit_id（来自 `direct_url.json`）+ 本地 HEAD commit（如可访问）+ diff hint；旧版 venv（无 `_print_venv_check`）也走子进程或 fallback 输出 | AC-03 版本对比强提示 | P0 |
| TC-04 | tmpdir + 故意改 `evaluation/testing.md`（user-modified，未在 managed-files 登记） + `harness install` | 一致行为：要么始终覆盖（`_sync_requirement_workflow_managed_files` adopted 路径），要么始终跳过（`_sync_scaffold_v2_mirror_to_live` skipped user-modified）；不可前后矛盾的双份日志 | AC-04 文件冲突日志一致性 | P1 |
| TC-05 | `harness install` 后 self-audit drift > 0 → exit code | 非零 exit code 或必有 stderr 红色 WARNING（用户必能感知）；非静默警告 | AC-05 drift 强提示 | P1 |
| TC-06 | bumped `pyproject.toml::version`（如 `0.2.0`） + 跑 dogfood install | `harness --version` 反映新版本；managed-files.json::tool_version 同步；`harness install` 触发"detected new tool_version → full re-sync" | AC-06 tool_version 差异化 | P1 |
| TC-07 | dogfood 在 tmpdir 跑 `pipx install --force /path/to/local/repo` 安装 | venv `direct_url.json` 指向本地路径；`harness install` 立即拿 HEAD scaffold 内容 | AC-07 本地 force install 路径 | P2 |

> AC 字段对应 bugfix.md §Validation Criteria 段（待 executing 阶段填写明细）。

## 7. 配套修复方案（写到 bugfix.md §Fix Plan 供 executing 消费）

### Fix-A：反向清理多余文件（核心）

在 `_sync_scaffold_v2_mirror_to_live` 的循环之外加一段反向遍历：

```python
# 反向：live 中存在但 mirror 没有 + 不在白名单 + 在 managed_state 中（说明历史 install 写过的） → 清理
for relative in sorted(set(managed_state.keys()) - set(mirror.keys())):
    if any(w in relative for w in _SCAFFOLD_V2_MIRROR_WHITELIST):
        continue
    live = root / relative
    if live.exists():
        if check:
            actions.append(f"would remove stale (mirror) {relative}")
        else:
            # 移到 LEGACY_CLEANUP_ROOT 备份（不直接删，保留 git 可恢复路径）
            backup_destination = _unique_backup_destination(root, Path(relative))
            backup_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(live), str(backup_destination))
            actions.append(f"archived stale (mirror) {relative} → {backup_destination.relative_to(root).as_posix()}")
        # 同步从 managed_state 删除
        refreshed_state.pop(relative, None)
```

### Fix-B：`harness install --check` 显式输出 venv vs git 对比

`_print_venv_check` 已存在，但只在含本次更新的 venv 中。让 CLI **子进程跑 git log + venv mtime 对比**，不依赖 helper：在 `tools/harness_install.py::main` 中新增独立的 git 子进程检查，输出 venv 安装源 commit + repo HEAD commit + diff hint。

### Fix-C：版本号差异化

修改 `pyproject.toml::version`，每次 chg 完成时 bump（或在 build 时注入 git short sha）；`managed-files.json::tool_version` 跟随更新；install 时如果检测到 mismatch → 触发 full re-sync。

### Fix-D：文档强提示（README）

在 README 或 `docs/install.md` 加一段："本仓库使用 GitHub 远程作为 pipx 安装源；本地未 push 的改动 reinstall 后不会生效，请确保 push 完成。"

### Fix-E（可选）：`harness install --from-local <path>` 命令

让用户能直接从本地 repo 路径 force-reinstall，绕过 GitHub 远程。

## 8. 经验沉淀候选

### 经验候选：pipx 远程安装 vs 本地 repo HEAD 的部署链条断裂

**场景**：开发者在本地仓库做 chg、commit 但未 push，然后让用户跑 `pipx reinstall harness-workflow`，用户拿不到本地未 push 的改动。

**经验内容**：pipx 安装源由 `pipx_metadata.json::main_package.package_or_url` 决定；当 `package_or_url` 是 git URL（如 `git+https://github.com/...`）时，reinstall 走的是远程头部，本地未 push 的 commit 永远到不了 venv。诊断 install 类问题时，`direct_url.json::vcs_info.commit_id` 是 venv 实际安装的 commit；与本地 `git rev-parse HEAD` 的 diff 是 L2 部署失配的第一证据。

**反例**：直接 grep src/ 看到代码已修，然后断定"已修复"——忽略 pipx venv 还在远程旧 commit 上，用户跑出来的还是旧版本。

**沉淀路径**：`.workflow/context/experience/roles/regression.md` 经验十"三维失配诊断模板"扩展（增加 pipx git URL 这条）

### 经验候选：install 反向清理盲区（mirror 已删 + managed-files 仍登记）

**场景**：scaffold_v2 中删除了某个文件（如 req-42 删除 `usage-reporter.md`），多次 install 后该文件在用户项目中永久残留。

**经验内容**：install 同步契约只覆盖"正向"（mirror 有 → live 写入）和"覆盖"（mirror 与 live 不同 → 写覆盖），没有"反向"（mirror 无但 managed-files 有 → 删除）。诊断 "harness install 留下多余文件" 类问题，应当首先 `diff -rq venv/scaffold vs target/.workflow/` + `python3 -c "import json; print(set(managed_files.json::managed_files) - set(scaffold mirror keys))"` 找 dead entries。

**反例**：把多余文件归到"用户业务态"忽略——业务态有白名单（state/, flow/archive/, flow/requirements/ 等），白名单外的"manage-files 登记过且 mirror 已无"的就是真残留。

**沉淀路径**：`.workflow/context/experience/roles/regression.md` 新增"经验十一"（待 executing 阶段沉淀）

## 9. 同 bugfix-7 关联建议（建议转 suggest 池，不阻塞本 bugfix）

- sug 候选：`harness install --check` 默认输出 venv 安装源 commit + repo HEAD diff hint（让用户可视化"这次 install 实际拉的是哪个版本"）
- sug 候选：`pyproject.toml::version` 升级机制（done 阶段或 archive 时自动 bump patch / minor）
- sug 候选：scaffold_v2 文件删除时强制写入 `LEGACY_CLEANUP_TARGETS`（reviewer lint）

---

> 诊断完成时间：2026-04-28
> 诊断师：regression（opus）
> 路由决定：confirm → executing
> 三维失配定位：L1（src 反向清理缺失） + L2（pipx 远程 commit 滞后） + L3（用户项目混合状态）联动
