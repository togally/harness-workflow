---
id: bugfix-7
title: pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件
created_at: 2026-04-28
---

# Problem Description

用户使用 `pipx reinstall harness-workflow` 后，再到目标项目下跑 `harness install --agent <agent>`，结果出现两类异常：

1. **未更新到最新**：本应同步到目标项目的最新 scaffold 内容（如 chg-01 / chg-02 落地的 testing.md / done.md / acceptance.md / analyst.md）实际没有同步到本机两个真实项目（`PetMallPlatform`、`uav`）。
2. **多余文件残留**：目标项目 `.workflow/` 下存在 scaffold 已不再包含的旧文件（如 `usage-reporter.md`），多次 install 都不会被清理。

触发条件：
- 本地仓库改动已 commit 但未 push 到 GitHub 远程
- 目标项目历史经过多轮 install，managed-files.json 累积了已被 scaffold 删除的文件登记
- 当前 venv 装的是 `git+https://github.com/togally/harness-workflow.git`（远程 main 头部）

影响范围：
- 任何用 GitHub URL 安装 harness-workflow 的目标项目
- 历经多个版本 install 的项目（PetMall / uav 都中招）

# Root Cause Analysis

> 详见 `regression/diagnosis.md` §3 三维失配定位（L1/L2/L3 联动）+ §6 路由决策。

**根本根因（一句话）**：本仓库 HEAD 改动**未 push 到 GitHub 远程**（L2 部署层失配） + **install 缺反向清理多余文件机制**（L1 源码层根因 A/B/D：`_install_self_audit` 只警告不删 + `LEGACY_CLEANUP_TARGETS` 是硬编码白名单 + managed-files 反向同步缺位）双因素叠加。

**结论**：真实问题，路由 → executing。

# Fix Scope

涉及文件 / 模块：

- `src/harness_workflow/workflow_helpers.py`：
  - `_sync_scaffold_v2_mirror_to_live`（增反向清理分支）
  - `_install_self_audit`（drift > 0 时强提示 / 非零 exit 或显著 stderr）
  - `LEGACY_CLEANUP_TARGETS`（迁移到从 mirror diff 自动派生，移除手工维护）
  - `_load_managed_state` / `_refresh_managed_state`（dead entries 反向清理）
- `src/harness_workflow/tools/harness_install.py`：
  - `--check` 强化：始终输出 venv 安装源 commit_id（来自 `direct_url.json`）+ 本地 HEAD commit + diff hint，旧版 venv 也能跑（不依赖 venv 含 helper）
- `pyproject.toml`：
  - `version` 字段升级机制（每次 chg / archive 时 bump 或注入 git short sha）
- `tests/test_install_reverse_cleanup.py`（新增）：
  - 覆盖 TC-01 ~ TC-07 的 dogfood 测试
- 文档（README / docs/install.md）：
  - 强提示"GitHub 远程 vs 本地未 push" 部署链条断裂的常见踩坑

明确**不在范围**：
- 不修改 PetMall / uav 两个目标项目（用户要按正常流程亲自验证）
- 不改动现有归档（archive/）
- 不重写 `harness change` / `harness next` 等其它 CLI（聚焦 install / update 同步契约）

# Fix Plan

> 详见 `regression/diagnosis.md` §7 配套修复方案 (Fix-A ~ Fix-E)。
> 用户已拍板 5 chg 拆分（chg-03 取消、chg-05 新增、chg-06 contingency），如下落地。

executing 阶段按以下顺序拆 chg：

1. **chg-01（反向清理 + check 对比）**：Fix-A 反向清理多余文件 + Fix-B `harness install --check` 强化
   - `_install_self_audit` 加 reverse-cleanup 分支（不再只 stderr WARN，按 managed_state 反向 diff 走清理）
   - `_sync_scaffold_v2_mirror_to_live` 增 dead-file 删除分支（移到 LEGACY_CLEANUP_ROOT 备份，不直删）
   - `LEGACY_CLEANUP_TARGETS` 从硬编码白名单迁移到从 mirror diff 自动生成
   - `harness install --check` stdout 输出 venv 安装源 commit_id（来自 `direct_url.json`）vs 本地 HEAD commit 的对比，旧版 venv 也能跑（不依赖 venv 含 helper，由 CLI 子进程独立跑 git log）

2. **chg-02（版本号差异化）**：Fix-C
   - `pyproject.toml::version` 升级机制（每次 chg / archive bump，或 build 时注入 git short sha）
   - `managed-files.json::tool_version` 同步更新
   - install 检测到 venv tool_version 与目标项目 managed-files.json tool_version mismatch 时 → 触发 full re-sync

3. **chg-03（取消）**：~~Fix-E `harness install --from-local <path>`~~
   - 用户决策：取消该 escape hatch（pipx 用户可直接 `pipx install --force /local/path` 达成同效果，不必新增 CLI 子命令）

4. **chg-04（文档强提示 + check stdout 协同）**：Fix-D
   - README / docs/install.md 加部署链条说明：pipx 安装源是 GitHub 远程；本地未 push 的改动 reinstall 拿不到，必须 push 后再 reinstall
   - `harness install --check` stdout 输出 venv 安装源 commit_id + 本地 HEAD commit_id 对比（与 chg-01 Fix-B 协同；文档侧解释如何读这份对比报告）

5. **chg-05（install 平台 prompt UX 修，新增）**：
   - 用户原话："install 的时候会卡一下必须手动按一下 enter 才会显示"
   - 根因：`src/harness_workflow/cli.py:46-90 prompt_platform_selection` 弹 `questionary.checkbox`，即便 `runtime.yaml` 已有 `active_list` 也强制交互
   - 修法：`prompt_platform_selection` 在已有 `active_list` 时跳过 `questionary.checkbox` 交互；或新增 `--no-prompt` flag 显式跳过

6. **chg-07（executing gate bugfix 模式支持，紧急修复）**：
   - 落地点：`workflow_helpers.py::_is_stage_work_done` executing 分支
   - 触发原因：bugfix-7 自身落地时发现 executing gate 强要求 `changes/` 目录，导致所有 bugfix 永远无法推进（reg-02/chg-02 严格化遗漏 bugfix 路径）
   - 修法：按 `operation_type` 分两路——bugfix 模式检查 `session-memory.md` 含 ✅；requirement/suggestion 模式保留原有逻辑
   - 新增 TC-09 / TC-10：_is_stage_work_done bugfix 路径分别断言 True / False
   - 对应 AC-09：TC-09 / TC-10 PASS

7. **chg-06（LLM 兜底派发，contingency / experimental，本周期不强求）**：
   - 用户原话："如果 install 单独难以处理增量以及旧文件，可以搭配大型来派发模型处理"
   - 触发条件：chg-01 落地后 testing 阶段如发现"反向清理 + 正向同步"仍有覆盖不到的边界 case（如用户业务态文件与 scaffold 文件名冲突 / 用户局部修改与 scaffold 升级冲突），可派发 LLM subagent 做语义判断
   - 实现思路：install 检测到"模糊状态"（managed_state diff 里同名文件 hash 既不等于 mirror 也不等于历史 managed hash）时输出诊断报告，提示用户调用 `harness install --smart` 或人工启动 subagent 分析
   - **本 bugfix 周期不强求实现**：留给后续 sug 池或下个 req 推进；如 chg-01 dogfood 充分覆盖、testing PASS 则本 contingency 不触发，仅作为 follow-up 候选记入 §同 bugfix-7 关联建议

注意事项：
- **必跑 dogfood 子进程测试**（不能只调 helper）：所有反向清理逻辑必须在 tmpdir 模拟"已删 + 已登记"双状态触发；
- **PetMall / uav 全程 read-only 不动**，executing 阶段也禁止修改这两个项目；
- bumped 后第一次 install 必须保留 `--check` dry-run 通路（让用户能看到将删什么）；
- chg-05 修 `prompt_platform_selection` 时不可破坏首次 install（无 `active_list`）的交互入口。

# Validation Criteria

> 详见 `regression/diagnosis.md` §测试用例设计 TC-01 ~ TC-07。
> 每个 chg 对应明确 AC（chg-03 取消、chg-06 contingency 不强求本周期收敛）。

## chg ↔ AC 对应矩阵

| chg | 对应 Fix | 对应 TC | 退出 AC |
|-----|---------|---------|---------|
| chg-01（反向清理 + check 对比，≤15字） | Fix-A + Fix-B | TC-01 / TC-02 / TC-03 / TC-05 | AC-01 / AC-02 / AC-03 / AC-05 |
| chg-02（版本号差异化，≤15字） | Fix-C | TC-06 | AC-06 |
| chg-03（取消，≤15字） | ~~Fix-E~~ | — | — |
| chg-04（文档强提示 check stdout，≤15字） | Fix-D + 协同 Fix-B | TC-03（文档侧验证） | AC-04 |
| chg-05（install 平台 prompt UX 修，≤15字） | 新增 | TC-08（新增） | AC-08 |
| chg-07（executing gate bugfix 模式支持，≤15字） | 新增 gate 修复 | TC-09 / TC-10 | AC-09 |
| chg-06（LLM 兜底派发，contingency，≤15字） | 新增 contingency | 不强求；testing 触发时再补 | 不强求 |

## 退出标准（按 chg 分组）

### chg-01 反向清理 + check 对比
- [ ] AC-01：TC-01 反向清理多余文件 PASS（dogfood 在 tmpdir 模拟"mirror 已删 + managed-files 仍登记"双状态，stdout 含 `removed/archived stale (mirror)`，managed-files.json 移除该 key）
- [ ] AC-02：TC-02 用户业务态文件保留不删 PASS（白名单覆盖：`flow/requirements/`、`state/sessions/`、`context/experience/regression/` 等业务态全部保留；只动 scaffold 模板态）
- [ ] AC-03：TC-03 `harness install --check` 输出 venv 安装源 commit_id（`direct_url.json::vcs_info.commit_id`）+ 本地 HEAD commit_id + diff hint PASS（旧版 venv 也能跑，由 CLI 子进程独立跑 git log）
- [ ] AC-05：TC-05 self-audit drift > 0 时强提示 PASS（非零 exit 或 stderr 红字 WARNING，不可静默）

### chg-02 版本号差异化
- [ ] AC-06：TC-06 `pyproject.toml::version` bump + `managed-files.json::tool_version` 同步 PASS；install 检测到 mismatch 触发 full re-sync PASS

### chg-04 文档强提示 + check stdout
- [ ] AC-04：README / docs/install.md 含"pipx 安装源是 GitHub 远程；本地未 push 的改动 reinstall 拿不到"段落；`harness install --check` stdout 显式输出 venv vs HEAD 对比报告（chg-01 Fix-B 已实现，chg-04 验文档可读 + 用户能据此自查）

### chg-05 install 平台 prompt UX 修
- [ ] AC-08：TC-08（新增）已有 `runtime.yaml::active_list` 时 `harness install` 不弹 `questionary.checkbox`、不需手按 Enter；首次 install（无 `active_list`）仍走交互入口

### chg-07 executing gate bugfix 模式支持
- [ ] AC-09：TC-09（bugfix session-memory.md 含 ✅ → True）PASS；TC-10（不含 ✅ → False）PASS

### chg-06 LLM 兜底派发（contingency，本周期不强求）
- 触发条件：chg-01 testing 阶段发现"反向清理 + 正向同步"覆盖不到的边界 case（用户业务态文件与 scaffold 同名 / 用户局部改动与 scaffold 升级冲突）
- 触发后再补 AC；如 testing 全 PASS 则本 chg 不进入本 bugfix 周期，转入 sug 池或下个 req

## 综合退出标准

- [ ] 在 dogfood tmpdir 完整复现 bugfix-7 场景：先伪造 PetMall 状态（含 usage-reporter.md + 旧 testing.md），跑 `harness install` 后 → 多余文件被清理 / testing.md 被同步 / 日志清晰
- [ ] 真实验证（用户验证）：用户在 PetMall 和 uav 项目跑 `pipx reinstall harness-workflow`（前提是开发者已 push HEAD）+ `harness install --agent <agent>` 后，文件树与 scaffold_v2 一致（除业务态白名单外），且 `harness install` 不再卡 Enter

## 人工验证步骤（用户）

1. 开发者 `git push origin main` 把 chg-01 / chg-02 / chg-04 / chg-05 推到远程
2. 用户 `pipx reinstall harness-workflow`
3. 用户 `cd /path/to/PetMall && harness install --agent claude --check`（先 dry-run 看 venv vs HEAD 对比 + 将删什么）
4. 用户 `cd /path/to/PetMall && harness install --agent claude`（真同步；不应再卡 Enter）
5. 检查 `.workflow/context/roles/usage-reporter.md` 已被移到 `.workflow/context/backup/legacy-cleanup/`
6. 检查 `.workflow/evaluation/testing.md` / `done.md` / `acceptance.md` 内容含最新 sug 段落
7. 检查 uav `.workflow/context/role-model-map.yaml` 升级到 v2 schema、`context/index.md` 更新到 analyst 角色合并版
