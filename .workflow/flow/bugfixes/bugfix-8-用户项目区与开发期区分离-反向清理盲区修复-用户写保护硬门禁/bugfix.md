---
id: bugfix-8
title: 用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁
created_at: 2026-04-28
---

# Problem Description

bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件）落地（chg-01 反向清理 + chg-02 tool_version 失配 + chg-04 文档强提示 + chg-05 prompt UX 修 + chg-07 executing gate bugfix 模式支持）后，用户在 PetMall / uav 跑 `pipx install --force /local/path` + `harness install --agent claude --force-managed` 实测，仍暴露 5 类残留问题：

1. **现象 1（usage-reporter.md 残留）**：本仓 working tree 已删该文件，但 `build/lib/.../scaffold_v2/.workflow/context/roles/usage-reporter.md` + venv mirror + 本仓 `.workflow/context/roles/usage-reporter.md` 三处仍存在；PetMall managed-files.json 仍登记 → bugfix-7 chg-01 反向清理逻辑因 mirror 被污染而差集恒空 → 永不触发。
2. **现象 2（self-audit 误报 7 条用户业务文件 drift）**：`_SCAFFOLD_V2_MIRROR_WHITELIST`（17 条）漏 `flow/bugfixes/`、`context/experience/regression/`、`context/experience/risk/` 三条工具产出区路径，导致 PetMall 跑 `harness regression` / `harness bugfix` 产出的工具产物被误报为 drift。
3. **现象 3（--force-managed 透传仍 skip）**：用户加 `--force-managed` 后 PetMall log 仍含 11 条 `[update_repo] skipping user-modified file ...; pass --force-managed to overwrite.` stderr；CLI 透传链路理论闭合，但 stderr 输出分支无防御性 assert，用户也无法直观感知 flag 是否生效。
4. **现象 4（用户写保护无硬门禁）**：用户在 `.workflow/**` 或 `.{agent}/skills/harness/**` 或 `.{agent}/commands/harness/**` 目录手写文件无任何 lint 拦截；破坏"用户项目区只读 / 工具产出区可写"边界。
5. **现象 5（build/ 残留污染 mirror）**：本仓 `./build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md` 残留（mtime = 2026-04-24 16:50）；`pipx install --force /local/path` 走 setuptools build 时优先从 `build/lib/` 拿 → 装出来的 venv 仍含 stale → 现象 1 复发。

**触发条件**：
- 任何用 `pipx install --force /local/path` 安装的目标项目（开发者本仓 build/ 残留时）
- 任何已用 `harness regression` / `harness bugfix` 产出经验或工具产出的项目
- 任何用户在 `.workflow/**` 手写文件的项目
- 本仓 dogfood 自身（路径同时命中三种条件）

**影响范围**：
- 上述各类项目的 install 体验：`harness install` self-audit 误报 7 条 + usage-reporter.md 永驻 + force-managed 似乎不生效 + 用户写保护破坏"边界"
- 本仓 dogfood 自身：本仓 .workflow/ 也含 stale；build/ 缓存污染传导到 venv

# Root Cause Analysis

> 详见 `regression/diagnosis.md` §3 三维失配定位（L1/L2/L3 联动）+ §6 路由决策。

**根本根因（一句话）**：bugfix-7 chg-01 反向清理逻辑虽实现，但 **mirror 数据源（venv 中 scaffold_v2 包）受 build/ 缓存污染，导致差集恒空**（L2 部署链条扩展失配，新变种），叠加 **白名单缺业务态目录**（L1 源码层根因 A）+ **用户写保护无门禁**（L1 lint 缺位根因 C）+ **dev-mode 边界识别仅 env 单通道**（L1 弱探测根因 B）+ **--force-managed stderr 输出无防御性 assert**（L1 鲁棒性根因 D）四因素并发。

**结论**：真实问题，路由 → executing。

# Fix Scope

涉及文件 / 模块：

- `src/harness_workflow/workflow_helpers.py`：
  - `_SCAFFOLD_V2_MIRROR_WHITELIST`（chg-02 加 3 条业务态目录）
  - `_install_self_audit`（chg-04 dev-mode 三层探测扩展）
  - `_sync_requirement_workflow_managed_files` 行 3392-3403（chg-03 防御性 assert）
  - `_sync_scaffold_v2_mirror_to_live` 行 3492-3498（chg-03 防御性 assert）
- `src/harness_workflow/validate_contract.py`：
  - 新增 `check_user_write_protected_zones`（chg-04）
  - 新增 `check_build_cache_freshness`（chg-05）
  - 新增 `_is_dev_repo` helper（三层判定，chg-04）
  - `run_contract_cli` 注册 `user-write-protected-zones` / `build-cache-freshness` 两个 contract
- `src/harness_workflow/tools/harness_install.py::main`：
  - chg-03 入口加 stderr 显式 `force_managed received: True/False` 提示
- 本仓 dogfood / build/ 手工清理（chg-01）：
  - 删除 `./build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`
  - 删除 `./.workflow/context/roles/usage-reporter.md`
  - `./.codex/harness/managed-files.json` 摘除 `usage-reporter.md` 登记
  - `pipx install --force /local/path` 重装让 venv 也跟随
- 新增 dogfood 测试（chg-01 ~ chg-05 各自配套）：
  - `tests/test_install_whitelist_business_zones.py`（chg-02）
  - `tests/test_install_force_managed_defense.py`（chg-03）
  - `tests/test_user_write_protected_zones.py`（chg-04）
  - `tests/test_build_cache_freshness.py`（chg-05）
- 文档（reviewer.md / regression.md 经验沉淀）：
  - 经验十四（本仓 vs 用户项目边界识别协议）
  - 经验十五（build/ 缓存污染 mirror 的部署链条问题）
  - 经验十六（白名单设计原则：工具产出区 vs 模板态）

明确 **不在范围**：
- 不修改 PetMall / uav 两个目标项目（用户要按正常流程亲自验证；regression / executing / testing / acceptance 全程对这两个项目 read-only）
- 不改动现有归档（`flow/archive/`）
- 不重写 `harness change` / `harness next` 等其它 CLI（聚焦 install / validate 同步契约）
- LLM 兜底派发（bugfix-7 chg-06 contingency）不在本周期推进

# Fix Plan

> 详见 `regression/diagnosis.md` §7 配套修复方案（chg-01 ~ chg-05 详细伪代码）。
> 用户已拍板 5 chg 拆分（无新增决策点）。

executing 阶段按以下顺序拆 chg（chg-01 / chg-05 涉及手工清理 + lint 配套，建议先做以释放 mirror 污染状态；chg-02 / chg-03 / chg-04 为代码层修复，可并行）：

## chg-01（真清理 usage-reporter.md，含 build/ stale + 本仓 .workflow 自身）

落地点：本仓手工清理 + chg-05 lint 防再犯（双轨）

步骤：
1. **手工清理 build/ 残留**：
   ```bash
   rm /Users/jiazhiwei/claudeProject/harness-workflow/build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md
   ```
2. **手工清理本仓 dogfood**：
   ```bash
   rm /Users/jiazhiwei/claudeProject/harness-workflow/.workflow/context/roles/usage-reporter.md
   ```
3. **从本仓 managed-files.json 摘除登记**（`.codex/harness/managed-files.json` + 各 agent 平级 managed-files.json 同步）：
   ```bash
   jq 'del(.managed_files.".workflow/context/roles/usage-reporter.md")' \
     ./.codex/harness/managed-files.json > /tmp/m.json && mv /tmp/m.json ./.codex/harness/managed-files.json
   ```
4. **pipx 重装让 venv 也跟随**：
   ```bash
   pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow
   ```
5. **dogfood TC**（tests/test_install_reverse_cleanup_v2.py 新增）：tmpdir 模拟"build/lib/ + venv mirror 都含 stale → 跑 `harness install` → 反向清理触发"完整链路。

## chg-02（self-audit 白名单补 3 个业务态目录）

落地点：`src/harness_workflow/workflow_helpers.py:180-200` `_SCAFFOLD_V2_MIRROR_WHITELIST`

修改：
```python
_SCAFFOLD_V2_MIRROR_WHITELIST: tuple[str, ...] = (
    # 运行时 / 业务态（17 → 20 条）
    "state/sessions",
    "state/requirements",
    "state/bugfixes",
    "state/feedback",
    "state/runtime.yaml",
    "state/action-log.md",
    "flow/archive",
    "flow/requirements",
    "flow/suggestions",
    "flow/bugfixes",                          # 新增（chg-02）：用户跑 harness bugfix 产出
    "context/backup",
    "context/experience/stage",
    "context/experience/regression",          # 新增（chg-02）：reg-NN 经验沉淀
    "context/experience/risk",                # 新增（chg-02）：known-risks.md 用户业务风险
    "workflow/archive",
    "tools/index/missing-log.yaml",
    "context/experience/index.md",
    "context/project-profile.md",
    "CLAUDE.md",
    "AGENTS.md",
)
```

dogfood TC：在 tmpdir 创建 `flow/bugfixes/bugfix-99-test/`、`context/experience/regression/reg-99.md`、`context/experience/risk/test.md`，跑 `harness install --agent claude` → self-audit silent skip 三者；drift count 不增。

## chg-03（--force-managed 透传防御 + 实证测试）

落地点：
- `src/harness_workflow/workflow_helpers.py:3392-3403` skip 分支
- `src/harness_workflow/workflow_helpers.py:3492-3498` mirror skip 分支
- `src/harness_workflow/tools/harness_install.py::main` 入口

修改：
1. install_repo 入口加 stderr 输出 `[install_repo] force_managed received: {True|False}`，让用户感知 flag 是否生效。
2. 两个 skip 分支前加防御性显式判定（保险冗余，防 OR 链路被未来改动破坏）：
   ```python
   if not force_managed:
       actions.append(f"skipped modified {relative}")
       if not check:
           print(f"[update_repo] skipping user-modified file {relative}; "
                 f"pass --force-managed to overwrite.", file=sys.stderr)
   else:
       print(f"[update_repo] WARNING: force_managed=True but reached skip branch for {relative}", file=sys.stderr)
   ```
3. 新增 dogfood TC：tmpdir 模拟"managed_state 登记 + hash 改过"双状态，跑 `harness install --force-managed` → assert stdout 无 `skipped modified` + stderr 无 `skipping user-modified`。

## chg-04（硬门禁 `--contract user-write-protected-zones` + dev-mode 三层探测）

落地点：
- 新增 `src/harness_workflow/validate_contract.py::check_user_write_protected_zones`（保护区扫描）
- 新增 `src/harness_workflow/validate_contract.py::_is_dev_repo`（三层探测：pyproject name / src/ 目录 / env）
- `run_contract_cli` 注册 `user-write-protected-zones` 入口
- `_install_self_audit` 中也使用 `_is_dev_repo` 替代当前仅 env 单通道（增 pyproject + src/ 探测）

实现要点：
- 保护区清单：`.workflow`、`.{claude,codex,qoder,kimi}/skills/harness`、`.{claude,codex,qoder,kimi}/commands/harness`
- 豁免清单：`_SCAFFOLD_V2_MIRROR_WHITELIST` 工具产出区 + `mirror` 模板态文件 + `managed_state` 登记的 managed 文件
- dev-mode 命中（OR 关系）：(i) `pyproject.toml::name == "harness-workflow"` (ii) `src/harness_workflow/` 目录存在 (iii) `HARNESS_DEV_REPO_ROOT` env 指向 root → silent skip
- 命中违规 → exit 1 + stderr 逐条违规 + 提示 "use harness commands to produce artifacts"

dogfood TC：
- TC-04a: user project 手写违规 → ABORT
- TC-04b: dev mode（本仓）→ silent skip
- TC-04c: 工具产出区文件（`flow/requirements/req-99/...`）→ silent skip
- TC-04d: 三层 dev-mode 探测各自命中 → 都触发豁免

## chg-05（lint：扫 build/ 残留）

落地点：
- 新增 `src/harness_workflow/validate_contract.py::check_build_cache_freshness`
- `run_contract_cli` 注册 `build-cache-freshness` 入口
- 集成到 `harness validate --contract all` 流程（与现有 contracts 并列）

实现要点：
- 扫 `build/lib/harness_workflow/assets/scaffold_v2/` 与 `src/harness_workflow/assets/scaffold_v2/` 差集
- 命中 stale 文件（build/ 中存在但 src/ 中不存在）→ stderr WARNING + hint `rm -rf build/`
- 不存在 build/ 或非本仓 → silent skip
- dev mode 不命中也要检测（lint 用途为开发期防再犯，不与 dev-mode 豁免逻辑耦合）

dogfood TC：
- TC-05a: tmpdir 模拟 build/lib/.../scaffold_v2/ 含 src/ 已删的 `usage-reporter.md` → lint 命中 + 输出 hint
- TC-05b: tmpdir 无 build/ → silent skip

注意事项：
- **必跑 dogfood 子进程测试**（不能只调 helper）：所有 lint 都需 `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'validate', '--contract', '<name>'])` 验证；
- **PetMall / uav 全程 read-only 不动**，executing 阶段也禁止修改这两个项目；
- chg-04 _is_dev_repo helper 同时被 `_install_self_audit` 复用（替代当前仅 env 单通道），保证 dev-mode 边界识别在 install 与 validate 两条链路一致；
- chg-05 lint 命中只输出 WARNING，不 ABORT install（与 chg-04 user-write-protected-zones 的 ABORT 语义不同）；
- chg-01 手工清理产生的 commit 应当与 chg-05 lint 落地同 commit（让 lint 自身首跑就 PASS）。

# Validation Criteria

> 详见 `regression/diagnosis.md` §测试用例设计 TC-01 ~ TC-06。
> 每个 chg 对应明确 AC（5 现象一一映射）。

## chg ↔ AC ↔ TC 对应矩阵

| chg | 对应根因 | 对应 TC | 退出 AC |
|-----|---------|---------|---------|
| chg-01（真清理 usage-reporter.md） | 根因 E + F + G | TC-01 / TC-06 | AC-01 |
| chg-02（白名单补 3 条） | 根因 A | TC-02 | AC-02 |
| chg-03（force-managed 透传防御） | 根因 D | TC-03 | AC-03 |
| chg-04（user-write-protected-zones 硬门禁） | 根因 B + C | TC-04a / TC-04b / TC-04c / TC-04d | AC-04 |
| chg-05（build/ 残留 lint） | 根因 E（防再犯） | TC-05a / TC-05b | AC-05 |

## 退出标准（按 chg 分组）

### chg-01 真清理 usage-reporter.md
- [ ] AC-01-a：本仓 `./build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md` 已删除（手工 + commit 落地）
- [ ] AC-01-b：本仓 `./.workflow/context/roles/usage-reporter.md` 已删除
- [ ] AC-01-c：本仓 `./.codex/harness/managed-files.json` 不再含 `usage-reporter.md` key（含 agent 平级 managed-files.json）
- [ ] AC-01-d：`pipx install --force /local/path` 后 `~/.local/pipx/venvs/.../usage-reporter.md` 已不存在
- [ ] AC-01-e：TC-01 / TC-06 PASS（dogfood 在 tmpdir 模拟"mirror 含 stale + managed-files 仍登记"双状态，跑反向清理脚本后 → live 文件被 archive 到 LEGACY_CLEANUP_ROOT，managed-files.json 移除该 key）

### chg-02 白名单补 3 个业务态目录
- [ ] AC-02-a：`_SCAFFOLD_V2_MIRROR_WHITELIST` 含 `flow/bugfixes` / `context/experience/regression` / `context/experience/risk` 三条
- [ ] AC-02-b：TC-02 PASS（tmpdir 创建三类业务态文件后 `harness install` self-audit silent skip，drift count 不增）
- [ ] AC-02-c：本仓自审跑 `harness install` 后 PetMall 等价场景的 7 条 drift 误报消失（dogfood 在 tmpdir 模拟，不动 PetMall）

### chg-03 --force-managed 透传防御
- [ ] AC-03-a：install_repo 入口 stderr 含 `[install_repo] force_managed received: True/False` 输出
- [ ] AC-03-b：两个 skip 分支前显式判定 `if not force_managed`；force_managed=True 时进入 else 分支输出 WARNING（理论不应到达）
- [ ] AC-03-c：TC-03 PASS（tmpdir 跑 `--force-managed` 时 stdout 无 `skipped modified` + stderr 无 `skipping user-modified`）

### chg-04 user-write-protected-zones 硬门禁
- [ ] AC-04-a：`harness validate --contract user-write-protected-zones` 入口已注册
- [ ] AC-04-b：`_is_dev_repo` 三层判定 helper 已实现并被 `_install_self_audit` + `check_user_write_protected_zones` 共用
- [ ] AC-04-c：TC-04a PASS（user project 手写违规 → ABORT exit 1 + stderr violation 列表）
- [ ] AC-04-d：TC-04b PASS（本仓 dev mode → silent skip exit 0）
- [ ] AC-04-e：TC-04c PASS（工具产出区文件 → silent skip）
- [ ] AC-04-f：TC-04d PASS（三层 dev-mode 探测分别命中均触发豁免）

### chg-05 build/ 残留 lint
- [ ] AC-05-a：`harness validate --contract build-cache-freshness` 入口已注册
- [ ] AC-05-b：TC-05a PASS（tmpdir build/ 含 src 已删文件 → 命中 + hint）
- [ ] AC-05-c：TC-05b PASS（无 build/ → silent skip）
- [ ] AC-05-d：本仓自审跑 `harness validate --contract build-cache-freshness` 命中 0（chg-01 已清理 build/usage-reporter.md，跑 lint 应得绿）

## 综合退出标准

- [ ] 所有 5 chg 落地后跑 `harness validate --contract all` 全绿（含新增 user-write-protected-zones / build-cache-freshness 两个 contract）
- [ ] dogfood 完整复现 bugfix-8 场景：在 tmpdir 同时模拟 (i) build/ 含 stale (ii) managed_state 登记 stale (iii) 用户业务态文件 (iv) 用户写保护违规 (v) `--force-managed` 透传，跑 `harness install` + `harness validate --contract all` 后所有 5 类问题均被检测或修复
- [ ] 真实验证（用户验证）：用户在 PetMall 跑 `pipx install --force /local/path` + `harness install --agent claude` 后：
  - PetMall `.workflow/context/roles/usage-reporter.md` 被 archive（chg-01 反向清理生效）
  - self-audit drift WARNING 不再含 `flow/bugfixes/` / `context/experience/regression/` / `context/experience/risk/` 三类误报（chg-02 生效）
  - `--force-managed` 时 stderr 不再有 `skipping user-modified`（chg-03 生效）
  - PetMall 手写 `.workflow/context/roles/my-custom-role.md` 时 `harness validate --contract user-write-protected-zones` ABORT（chg-04 生效）
  - 本仓自身 `harness validate --contract build-cache-freshness` 全绿（chg-05 生效 + chg-01 完成清理）

## 人工验证步骤（用户）

1. 开发者完成 chg-01 ~ chg-05 + 跑本仓 `harness validate --contract all` 全绿 + git push 到远程
2. 用户跑 `pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow`（让 venv 拿到最新 + chg-01 已清 build/）
3. 用户 `cd /path/to/PetMall && harness install --agent claude --check`（先 dry-run 看会发生什么）
4. 用户 `cd /path/to/PetMall && harness install --agent claude`（真同步）
5. 检查 `.workflow/context/roles/usage-reporter.md` 已被移到 `.workflow/context/backup/legacy-cleanup/`
6. 检查 install stdout self-audit drift 不再含 `flow/bugfixes/` / `context/experience/regression/` / `context/experience/risk/` 三类
7. 用户故意 touch `.workflow/context/roles/my-custom.md` + 跑 `harness validate --contract user-write-protected-zones` → 命中 violation
8. 删除该测试文件 + 跑 `harness validate --contract all` → 全绿
