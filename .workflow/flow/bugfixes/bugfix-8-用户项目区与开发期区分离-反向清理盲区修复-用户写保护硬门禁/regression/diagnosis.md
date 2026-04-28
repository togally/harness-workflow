# Regression Diagnosis — bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）

> 诊断师：regression（opus）
> 诊断日期：2026-04-28
> 路由决定：confirm → executing
> 三维失配定位：L1 src（白名单缺业务态目录 / dev-mode 边界识别缺失）+ L2 deploy（build/ 缓存污染 venv → mirror 仍含 stale → 反向清理失效）+ L3 现场（PetMall managed_state 与污染 mirror 的差集恒空 + 用户写保护无门禁）联动

## 1. 问题描述（用户报告原文摘要）

bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件）落地（chg-01 反向清理 + chg-02 tool_version 失配 + chg-04 文档强提示 + chg-05 prompt UX 修 + chg-07 executing gate bugfix 模式支持）后，用户在两个真实项目（PetMall / uav）跑 `pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow` + `harness install --agent claude --force-managed` 实测，仍暴露 5 类残留问题：

1. **现象 1 / chg-01 真清理 usage-reporter.md**：本仓库 working tree `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md` 已删除，但 `~/.local/pipx/venvs/harness-workflow/lib/python*/site-packages/.../usage-reporter.md` 仍存在 + 本仓 `./build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md` 残留 + 本仓 `./.workflow/context/roles/usage-reporter.md` dogfood 自身未清；PetMall `.codex/harness/managed-files.json` 仍登记 `usage-reporter.md`，`set(managed_state.keys()) - set(mirror.keys())` 在 mirror 被污染（venv 仍含 stale 副本）时差集为空 → 反向清理永不触发。
2. **现象 2 / chg-02 self-audit 白名单补 3 个业务态目录**：PetMall `harness install` log 中 `[install_repo:self-audit] drift detected (only in live)` 命中 12 条，其中 7 条是用户业务态文件（`flow/bugfixes/bugfix-2-mcp-接口-userid-...`、`context/experience/regression/reg-05.md`、`context/experience/regression/reg-06.md`、`context/experience/risk/frontend-readonly.md` 等），均为 PetMall 跑 `harness regression` / `harness bugfix` 命令产生的工具产出，应当 silent skip 不算 drift；`_SCAFFOLD_V2_MIRROR_WHITELIST`（17 条）当前缺 `flow/bugfixes/`、`context/experience/regression/`、`context/experience/risk/` 三条。
3. **现象 3 / chg-03 `--force-managed` 透传修**：bugfix-7 实测 PetMall log 显示用户加了 `--force-managed` 后 install 末尾仍有 11 条 `[update_repo] skipping user-modified file ...; pass --force-managed to overwrite.` 的 stderr 输出，说明流程内某处 sync 调用没拿到 force_managed=True，或 stderr 输出分支条件判断不严密。
4. **现象 4 / chg-04 硬门禁 `--contract user-write-protected-zones`**：当前 install / next 流程没有任何 lint 拦截"用户在 `.workflow/` 或 skill / commands 目录手写文件"的违规；如用户在 PetMall `.workflow/context/roles/` 下手写 `my-custom-role.md`，没有任何报错，下次 install 也不会清理也不会警告，破坏"用户项目区只读 / 工具产出区可写"的边界。
5. **现象 5 / chg-05 lint：扫 build/ 残留**：本仓 `./build/lib/harness_workflow/assets/scaffold_v2/` 持有完整 stale 副本（含已删除的 `usage-reporter.md`，mtime = 2026-04-24 16:50）；`pipx install --force /local/path` 走 setuptools build 时优先从 `build/` 拿 → 装出来的 venv 仍含 stale → 现象 1 复发。dev mode 不命中（开发期豁免）也要检测并提示清理，防止 build/ 中 stale 文件污染下次 pipx install。

参考目标项目（read-only 扫描）：
- `/Users/jiazhiwei/claudeProject/PetMallPlatform`
- `/Users/jiazhiwei/claudeProject/uav`

## 2. 现象（实证 / 证据链）

### 2.1 现象 1 实证：usage-reporter.md 在四处的状态分裂

| 位置 | 是否含 usage-reporter.md | 备注 |
|------|------------------------|------|
| 本仓 working tree `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` | ❌ 已删 | 期望状态（src/ 是 SSOT） |
| 本仓 `./build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` | ✅ 存在（mtime = 2026-04-24 16:50） | setuptools 上次 build 副本，未跟随 src 删除 |
| `~/.local/pipx/venvs/harness-workflow/lib/python*/site-packages/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` | ✅ 存在 | venv mirror 受 build/ 污染（pipx install --force /local 路径取的是 build/） |
| 本仓 `./.workflow/context/roles/`（dogfood 自身） | ✅ 存在 | 历史 install 写入，本仓自身从未跑反向清理 |

**验证命令**（read-only）：
```bash
ls /Users/jiazhiwei/claudeProject/harness-workflow/src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/ | grep usage-reporter
# (空，已删)
ls /Users/jiazhiwei/claudeProject/harness-workflow/build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md
# (存在)
ls ~/.local/pipx/venvs/harness-workflow/lib/python*/site-packages/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md
# (存在)
ls /Users/jiazhiwei/claudeProject/harness-workflow/.workflow/context/roles/usage-reporter.md
# (存在)
```

**反向清理失效链路**（`workflow_helpers.py:3500-3532`）：
- mirror = `_scaffold_v2_file_contents(root)` 从 venv 安装的 `harness_workflow.assets.scaffold_v2` 包读
- venv 中 mirror 仍含 `usage-reporter.md`（被 build/ 污染）→ `mirror.keys()` 含此 key
- `stale_keys = set(managed_state.keys()) - set(mirror.keys())` 不含 `usage-reporter.md`
- **结论**：bugfix-7 chg-01 反向清理逻辑虽然实现了，但因 mirror 被 build/ 缓存污染传导到 venv，差集恒空 → 永不触发

### 2.2 现象 2 实证：白名单缺 3 个业务态目录

`_SCAFFOLD_V2_MIRROR_WHITELIST`（`workflow_helpers.py:180-200`）现含 17 条：

```python
"state/sessions", "state/requirements", "state/bugfixes", "state/feedback",
"state/runtime.yaml", "state/action-log.md",
"flow/archive", "flow/requirements", "flow/suggestions",
"context/backup", "context/experience/stage",
"workflow/archive", "tools/index/missing-log.yaml",
"context/experience/index.md", "context/project-profile.md", "CLAUDE.md", "AGENTS.md",
```

**缺三条**：
- `flow/bugfixes/`（已有 `flow/requirements/` / `flow/archive/` / `flow/suggestions/`，**漏 bugfixes**）
- `context/experience/regression/`（reg-NN 工具产出经验沉淀目录）
- `context/experience/risk/`（known-risks.md 等用户业务态风险经验）

**PetMall 命中证据**（log 摘录）：
```
[install_repo:self-audit] drift detected (only in live): .workflow/context/experience/regression/reg-05.md
[install_repo:self-audit] drift detected (only in live): .workflow/context/experience/regression/reg-06.md
[install_repo:self-audit] drift detected (only in live): .workflow/flow/bugfixes/bugfix-2-mcp-接口-userid-...
... (12 drift 中 7 条是用户业务态)
```

这些是用户跑 `harness regression "<issue>"` / `harness bugfix "<issue>"` 命令产生的**工具产出**（`reg-NN-{slug}.md` / `bugfix-NN-{slug}/`），属"工具运行时产出区"语义，应当 silent skip 不算 drift。

### 2.3 现象 3 实证：`--force-managed` 透传链路核查

CLI 透传链路核查（grep `force_managed` 全链路）：

| 层 | 文件 / 行号 | force_managed 处理 |
|---|---|---|
| L1 入口 | `cli.py:416-417` | `if getattr(args, "force_managed", False): extra_args.append("--force-managed")` ✓ |
| L2 子进程 | `tools/harness_install.py:174-178, 196` | argparse 接收 + 传给 `install_repo(force_managed=args.force_managed, ...)` ✓ |
| L3 主流程 | `workflow_helpers.py::install_repo:3729, 3866, 3876, 3901` | 透传给 `_sync_requirement_workflow_managed_files` 与 `_sync_scaffold_v2_mirror_to_live` ✓ |
| L4 sync 内部 | `workflow_helpers.py:3357` `if managed_state.get(relative) == current_hash or force_managed:` | 已登记 + hash 改过 + force_managed=True 时走 update 分支 ✓（理论闭合） |
| L4 fallback 分支 | `workflow_helpers.py:3392-3403` `actions.append(f"skipped modified {relative}")` + stderr | **进入此分支的前提**：行 3357 OR 条件不满足 → `not force_managed` 隐含；**理论上 force_managed=True 时不可能到这** |

**矛盾**：用户报告"加了 --force-managed 后仍 11 条 stderr"。可能的根因：
- **假说 A（最可能）**：用户跑的是 `pipx install --force /local/path` 后**未传 --force-managed flag**，而是默认 install_repo（force_managed=False）；用户记忆混淆。
- **假说 B（次可能）**：venv 装的是 bugfix-7 之前的旧版本（未 push 时 GitHub 远程仍是旧 commit），旧版 force_managed 透传链路有缺口。
- **假说 C（架构问题）**：行 3392 `skipped modified` 输出条件未明确判 force_managed；虽然在当前 OR 短路下不会被 force_managed=True 命中，但若未来添加 `_is_user_authored` 类似前置判定（见 line 3373-3391 的 adopt-as-managed 分支），分支条件可能漏判。

**chg-03 的本质修复方向**：
- 不论假说 A/B/C，都需要 install 入口加一段 stderr 输出"force_managed received: True/False"，让用户能明确感知 flag 是否生效；
- 在所有 stderr "skipping user-modified" 输出处加 `assert not force_managed`（或显式 `if not force_managed`）防御，避免未来 OR 短路被破坏；
- dogfood 加 TC：`force_managed=True` 时不应出现任何 `skipping user-modified` stderr。

### 2.4 现象 4 实证：用户写保护无硬门禁

当前 lint 体系（`validate_contract.py::run_contract_cli`，行 904+）已含 contracts：`7 / regression / triggers / role-stage-continuity / artifact-placement / test-case-design-completeness / testing-no-destructive-git`。**缺 `user-write-protected-zones` 契约**——没有任何 lint 扫描"用户在 `.workflow/**` 或 `.{agent}/skills/harness/` 或 `.{agent}/commands/harness/` 目录手写文件"的违规。

**测试样本**（理论）：用户在 PetMall `.workflow/context/roles/my-custom-role.md` 手写一个文件 → install / next / status 均无任何报错或警告 → 该文件持续累积（既不被反向清理，也不被白名单豁免，每次 install self-audit 都报 "only in live" drift），破坏"用户项目区只读"边界。

**dev-mode 自动豁免要求**（用户拍板）：
- 本仓识别：`pyproject.toml::name == "harness-workflow"` **OR** 存在 `src/harness_workflow/` 源码目录 **OR** `HARNESS_DEV_REPO_ROOT` env 命中
- 命中 = dev mode → 门禁 silent skip
- 未命中 = user project → 门禁强制激活

### 2.5 现象 5 实证：build/ 残留

```bash
ls -la /Users/jiazhiwei/claudeProject/harness-workflow/build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md
# -rw-r--r--@ 1 jiazhiwei  staff  5322 Apr 24 16:50 ...
```

`pyproject.toml::version = "0.2.0"`（bugfix-7 chg-02 已 bump），但 `build/` 目录从 req-42（archive 时删 usage-reporter.md）至今未清理。`pipx install --force /local/path` 时 setuptools 默认从 `build/lib/` 复制源码到 venv（避免重新编译），导致 stale 文件复活进 venv。

## 3. 三维失配定位（套用经验十：三维失配诊断模板 + 经验十一：反向清理盲区 + 经验十二：pipx 部署链条断裂）

### L1 源代码层（src/）失配

**根因 A — 白名单缺业务态目录（现象 2）**：`_SCAFFOLD_V2_MIRROR_WHITELIST`（`workflow_helpers.py:180-200`）只覆盖了 `flow/requirements/` / `flow/archive/` / `flow/suggestions/` / `state/{sessions,requirements,bugfixes}` / `context/experience/stage` / `context/experience/index.md` / `context/backup` 等十七条，**缺三条**：`flow/bugfixes/`（用户跑 harness bugfix 产生）、`context/experience/regression/`（reg-NN 沉淀）、`context/experience/risk/`（用户风险经验）。新加一种工具产出 stage / 经验类型时必须同步加白名单——现状是开发者新加 stage（如 reg-02 经验十扩展、bugfix-7 chg-04 文档段落）时漏掉白名单同步。

**根因 B — dev-mode 边界识别仅 env-based 单一通道（现象 4）**：`_install_self_audit`（行 8278+）只通过 `HARNESS_DEV_REPO_ROOT` env 判断 dev mode，没有 `pyproject.toml::name == "harness-workflow"` / `src/harness_workflow/` 目录探测的回退；用户在本仓跑命令时若忘了 export env，self-audit 仍按 user project 模式触发，drift 12 条全报。换言之，本仓自身 dogfood 时也踩这个坑。

**根因 C — 用户写保护无 lint（现象 4）**：`validate_contract.py::run_contract_cli` 不含 `user-write-protected-zones` 契约；用户在 `.workflow/**` 或 `.{agent}/skills/harness/**` 或 `.{agent}/commands/harness/**` 目录手写文件，无任何 lint 拦截。

**根因 D — `--force-managed` stderr 输出未防御性 assert（现象 3）**：`_sync_requirement_workflow_managed_files:3392-3403` 与 `_sync_scaffold_v2_mirror_to_live:3492-3498` 的 "skipped user-modified" stderr 分支虽然依赖前置 `not force_managed` 隐含，但代码层面未显式 `assert not force_managed`；未来若有人在 OR 链路前再加一个 `_is_user_authored` 类前置判定，可能 force_managed=True 时仍漏掉刷新。

### L2 部署二进制层（pipx venv / build/ 缓存）失配

**根因 E — build/ 缓存污染 mirror 的部署链条（现象 1 + 现象 5）**：`pipx install --force /local/path` 时 setuptools 优先从 `./build/lib/` 取已有副本（避免重新编译），不管 src/ 是否已删该文件。后果：
1. src/ 删了 `usage-reporter.md`（commit `c191ea5` "archive: req-42"），但 `build/lib/.../usage-reporter.md` 留存
2. `pipx install --force /local/path` 拷贝 `build/lib/` → venv → venv 中 `harness_workflow.assets.scaffold_v2` 仍含 `usage-reporter.md`
3. `_scaffold_v2_file_contents` 读 venv mirror → mirror 包含 stale → `set(managed_state.keys()) - set(mirror.keys())` 差集恒空 → 反向清理失效
4. 每次 `harness install --agent claude` 都"看到 mirror 有 → 不删；看到 live 也有 → 不动" → 永久残留

这是经验十二（pipx git URL 安装 vs 本地 HEAD）的**新变种**：从"远程 commit 滞后"扩展到"本地 build/ 缓存污染"。

**根因 F — 本仓 dogfood `.workflow/context/roles/usage-reporter.md` 自身未清（现象 1）**：本仓 dogfood 时跑过历史 install（managed_state 登记），但 src/ 删 usage-reporter.md 后没有人手工跑反向清理；本仓自身 build/lib/ + venv 也都污染——**本仓也是 user project 视角的现场失配**。

### L3 现场层（用户项目 / 本仓 dogfood）失配

**根因 G — PetMall managed_state 与污染 mirror 的差集恒空（现象 1）**：PetMall `.codex/harness/managed-files.json` 仍含 `.workflow/context/roles/usage-reporter.md` 登记，但因 mirror 被根因 E 污染，反向清理 stale_keys 恒空，文件永远残留。

**根因 H — 用户业务态文件 12 drift 中 7 条误报（现象 2）**：PetMall 跑 harness regression / harness bugfix 产出的 reg-NN-*.md / bugfix-NN-{slug}/ 都被算成"only in live drift"，破坏 `harness install` stdout 可读性，让用户误以为同步失败。

### 三维失配联动

| 维度 | 检查方式 | 失配症状 | 对应 chg |
|------|---------|---------|---------|
| L1 源码 | grep `_SCAFFOLD_V2_MIRROR_WHITELIST` + `_install_self_audit` + `validate_contract` | 白名单缺 3 条 / dev-mode 仅 env / 缺 user-write 契约 | chg-02 / chg-04 |
| L2 部署 | `ls build/lib/.../scaffold_v2/.workflow/context/roles/` + venv mirror | build/ 残留 stale → venv mirror 污染 → 反向清理差集恒空 | chg-01 / chg-05 |
| L3 现场 | PetMall log + diff venv mirror vs PetMall live | usage-reporter.md 永驻 + 7 条业务态文件误报 drift | chg-01 / chg-02 |
| L1 + L4 | 用户报告 "--force-managed 仍 skip" | force_managed 透传链路 OK 但 stderr 输出无防御性 assert | chg-03 |

**根本根因（一句话）**：bugfix-7 chg-01 反向清理逻辑虽实现，但 **mirror 数据源（venv 中 scaffold_v2 包）受 build/ 缓存污染，导致差集恒空**（L2 部署链条扩展失配，新变种），叠加**白名单缺业务态目录**（L1 源码层）+ **用户写保护无门禁**（L1 lint 缺位）+ **dev-mode 边界识别弱**（仅 env 单通道）四因素并发。

## 4. 受影响范围

- **任何用 pipx 安装 harness-workflow 的目标项目**：本仓 build/ 残留 stale 时，无论从 GitHub URL 还是 `pipx install --force /local/path` 安装，venv mirror 都被污染 → 反向清理失效（现象 1 / 5）
- **任何已用 `harness regression` / `harness bugfix` 产出经验或工具产出的项目**：每次 install 都报 7+ 条 drift WARNING（现象 2），破坏 stdout 可读性
- **任何用户在 `.workflow/**` 手写文件的项目**：无任何拦截，污染累积（现象 4）
- **本仓 dogfood 自身**：根因 F 决定本仓 .workflow/ 也含 stale，这是 dev mode 自动豁免必须解决的对偶问题

## 5. 复现步骤（expected vs actual）

### 现象 1 + 5 复现（usage-reporter.md 残留）

1. 在 PetMall 跑过历史 install（managed-files.json 登记 `usage-reporter.md`）
2. 开发者本地仓库删了 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`
3. 本仓 build/lib/ 仍有 stale 副本（commit 之后未清 build/）
4. `pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow`
5. 在 PetMall 跑 `harness install --agent claude`

**Expected**：PetMall `.workflow/context/roles/usage-reporter.md` 被 archive 到 LEGACY_CLEANUP_ROOT（chg-01 反向清理生效）；managed-files.json 移除该 key。

**Actual**：文件仍残留；managed-files.json 仍含 key；反向清理 silent skip（差集恒空）。

### 现象 2 复现（self-audit 误报 7 条用户业务文件）

1. PetMall 历史跑过 `harness regression "..."` 产生 `reg-05.md` / `reg-06.md`
2. PetMall 历史跑过 `harness bugfix "..."` 产生 `flow/bugfixes/bugfix-2-mcp-接口-userid-...`
3. 跑 `harness install --agent claude`

**Expected**：self-audit silent skip 这些用户业务态文件（与 `flow/requirements/` / `state/sessions/` 同语义豁免）。

**Actual**：12 drift 中 7 条是用户业务态被误报。

### 现象 3 复现（--force-managed 仍 skip）

1. PetMall 历史 `evaluation/testing.md` 被用户改过（managed_state 登记 + hash 不匹配）
2. 跑 `harness install --agent claude --force-managed`

**Expected**：`evaluation/testing.md` 被 force 覆盖；无 stderr `skipping user-modified`。

**Actual**：用户报告 11 条 `[update_repo] skipping user-modified file ...; pass --force-managed to overwrite.` stderr。需要 chg-03 加防御性 assert + dogfood 测试 force_managed=True 不应出现 stderr。

### 现象 4 复现（用户写保护无门禁）

1. 用户在 PetMall 手写 `.workflow/context/roles/my-custom-role.md`
2. 跑 `harness install --agent claude` / `harness next` / `harness validate --contract all`

**Expected**：lint 报错 `user-write-protected-zones violation: .workflow/context/roles/my-custom-role.md is in protected zone; use harness commands to produce artifacts`，install ABORT。

**Actual**：无任何报错；文件持续累积；只在 self-audit drift WARNING 中露脸。

## 6. 路由决策

**判定：真实问题**（5 现象均有具体证据，非误判）。

**推荐路由：confirm → executing**。理由：
- 根因 A/B/C/D 均为**实现层**问题（白名单 / dev-mode 探测 / lint / 防御性 assert），无需重新规划需求；
- 根因 E/F/G/H 是 L2 / L3 现场表现，由 L1 修复 + chg-05 build/ 残留 lint 联动覆盖；
- 用户已拍板 5 chg 拆分（chg-01 ~ chg-05），无新需求点。

**不需要 required-inputs**：诊断证据全部从本仓 src/ + build/ + venv + PetMall log 收集完毕，用户无需补充。

## 7. 配套修复方案（写到 bugfix.md §Fix Plan 供 executing 消费）

> 5 chg 拆分依据用户拍板（详见 §1）。所有 chg 落地点均在 `src/harness_workflow/`，禁碰 PetMall / uav。

### chg-01：真清理 usage-reporter.md（含 build/ stale + 本仓 .workflow 自身）

**落地点**：
- 删除 `build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`（手工 + 加 lint 防再犯）
- 删除本仓 dogfood `./.workflow/context/roles/usage-reporter.md`（手工，由本 chg 手工执行）
- 同步删除本仓 dogfood `./.codex/harness/managed-files.json` 中 `usage-reporter.md` 登记（reset hash 重建或手动 pop key）

**伪代码**（手工 cleanup）：
```bash
# Step 1：清 build/ 残留
rm /Users/jiazhiwei/claudeProject/harness-workflow/build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md

# Step 2：清本仓 dogfood
rm /Users/jiazhiwei/claudeProject/harness-workflow/.workflow/context/roles/usage-reporter.md

# Step 3：从 managed-files.json 摘除登记（手工或 jq）
jq 'del(.managed_files.".workflow/context/roles/usage-reporter.md")' \
  ./.codex/harness/managed-files.json > /tmp/m.json && mv /tmp/m.json ./.codex/harness/managed-files.json

# Step 4：跑 pipx install --force /local/path 让 venv 也跟随
pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow
```

**配套 dogfood TC**：在 tmpdir 模拟"build/lib/ + venv mirror 都含 stale → 跑 `harness install` → 反向清理触发"完整链路。

### chg-02：self-audit 白名单补 3 个业务态目录

**落地点**：`src/harness_workflow/workflow_helpers.py:180-200` `_SCAFFOLD_V2_MIRROR_WHITELIST`

**修改**：在元组中增加三条：
```python
_SCAFFOLD_V2_MIRROR_WHITELIST: tuple[str, ...] = (
    # 运行时 / 业务态（17 → 20 条）
    "state/sessions",
    ...
    "flow/archive",
    "flow/requirements",
    "flow/suggestions",
    "flow/bugfixes",                          # 新增（chg-02）：用户跑 harness bugfix 产出
    "context/backup",
    "context/experience/stage",
    "context/experience/regression",          # 新增（chg-02）：reg-NN 经验沉淀
    "context/experience/risk",                # 新增（chg-02）：known-risks.md 用户业务风险
    ...
)
```

**配套 dogfood TC**：在 tmpdir 创建 `flow/bugfixes/bugfix-99-test/`、`context/experience/regression/reg-99.md`、`context/experience/risk/test.md`，跑 `harness install --agent claude` → self-audit silent skip 三者；drift count 不增。

**契约文档配套**：在白名单上方注释"新加 stage / 新加经验类型时必须同步加白名单"（contract layer reviewer checklist 项），将经验沉淀到 `regression.md` 经验十五（见 §8）。

### chg-03：`--force-managed` 透传防御 + 实证测试

**落地点**：
- `src/harness_workflow/workflow_helpers.py:3392-3403` `_sync_requirement_workflow_managed_files` skip 分支
- `src/harness_workflow/workflow_helpers.py:3492-3498` `_sync_scaffold_v2_mirror_to_live` skip 分支
- `src/harness_workflow/tools/harness_install.py::main` 入口

**修改**：
1. install_repo 入口加一段 stderr 输出 `[install_repo] force_managed received: True/False`，让用户能感知 flag 是否生效。
2. 两个 skip 分支前加防御性 assert：
   ```python
   if not force_managed:  # 防御性显式判定
       actions.append(f"skipped modified {relative}")
       if not check:
           print(
               f"[update_repo] skipping user-modified file {relative}; "
               f"pass --force-managed to overwrite.",
               file=sys.stderr,
           )
   else:
       # force_managed=True 时不应到达本分支（OR 短路保证），加日志兜底
       print(f"[update_repo] WARNING: force_managed=True but reached skip branch for {relative}", file=sys.stderr)
   ```
3. 新增 dogfood TC：tmpdir 模拟"managed_state 登记 + hash 改过"双状态，跑 `harness install --force-managed` → assert stdout 无 `skipped modified` + stderr 无 `skipping user-modified`。

### chg-04：硬门禁 `--contract user-write-protected-zones`

**落地点**：
- 新增 `src/harness_workflow/validate_contract.py::check_user_write_protected_zones`
- 注册到 `run_contract_cli`：`if contract in ("all", "user-write-protected-zones"):`
- 集成到 `harness next` / `harness install` 前置 lint（按 default-pick 决策，可在 executing 阶段商定）

**伪代码**：
```python
def check_user_write_protected_zones(root: Path) -> int:
    """扫 .workflow/** + skill/commands 目录，识别非工具产出的野文件 → ABORT。"""
    # 1) dev-mode 自动豁免（三层判定）
    if _is_dev_repo(root):
        return 0  # silent skip
    
    violations = []
    protected_zones = [
        ".workflow",
        ".claude/skills/harness", ".claude/commands/harness",
        ".codex/skills/harness", ".codex/commands/harness",
        ".qoder/skills/harness", ".qoder/commands/harness",
        ".kimi/skills/harness", ".kimi/commands/harness",
    ]
    managed_state = _load_managed_state(root)
    mirror = _scaffold_v2_file_contents(root, ...)
    whitelist = _SCAFFOLD_V2_MIRROR_WHITELIST
    
    for zone in protected_zones:
        zone_path = root / zone
        if not zone_path.exists():
            continue
        for f in zone_path.rglob("*"):
            if not f.is_file():
                continue
            relative = f.relative_to(root).as_posix()
            # 工具产出区豁免
            if any(w in relative for w in whitelist):
                continue
            # managed 模板态文件豁免
            if relative in mirror:
                continue
            if relative in managed_state:
                continue
            # 真野文件 → ABORT
            violations.append(relative)
    
    if violations:
        for v in violations:
            print(f"[user-write-protected-zones] violation: {v}", file=sys.stderr)
        print(f"[user-write-protected-zones] {len(violations)} violation(s); use harness commands to produce artifacts", file=sys.stderr)
        return 1
    return 0


def _is_dev_repo(root: Path) -> bool:
    """三层判定：pyproject name / src/ 目录 / env"""
    # Layer 1: pyproject.toml::name == "harness-workflow"
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        if 'name = "harness-workflow"' in text:
            return True
    # Layer 2: src/harness_workflow/ 源码目录
    if (root / "src" / "harness_workflow").is_dir():
        return True
    # Layer 3: HARNESS_DEV_REPO_ROOT env
    dev_root_env = os.environ.get("HARNESS_DEV_REPO_ROOT")
    if dev_root_env and Path(dev_root_env).resolve() == root.resolve():
        return True
    return False
```

**配套 dogfood TC**：
- TC: user project 模式手写 `.workflow/context/roles/my-custom.md` → ABORT
- TC: dev mode（本仓）跑 → silent skip
- TC: 工具产出区文件（`flow/requirements/req-99/...`）→ silent skip

### chg-05：lint：扫 build/ 残留

**落地点**：
- 新增 `src/harness_workflow/validate_contract.py::check_build_cache_freshness`（或集成到 `check_user_write_protected_zones` 副流程）
- 注册到 `run_contract_cli`：`if contract in ("all", "build-cache-freshness"):`

**伪代码**：
```python
def check_build_cache_freshness(root: Path) -> int:
    """dev mode 不命中也要检测 build/ 中 stale 文件，提示清理。"""
    build_scaffold = root / "build" / "lib" / "harness_workflow" / "assets" / "scaffold_v2"
    src_scaffold = root / "src" / "harness_workflow" / "assets" / "scaffold_v2"
    
    if not build_scaffold.is_dir() or not src_scaffold.is_dir():
        return 0  # 无 build/ 或非本仓，跳过
    
    stale_files = []
    for f in build_scaffold.rglob("*"):
        if not f.is_file():
            continue
        relative = f.relative_to(build_scaffold).as_posix()
        src_counterpart = src_scaffold / relative
        if not src_counterpart.exists():
            stale_files.append(relative)
    
    if stale_files:
        print(f"[build-cache-freshness] WARNING: {len(stale_files)} stale file(s) in build/lib/ not in src/:", file=sys.stderr)
        for s in stale_files:
            print(f"  - {s}", file=sys.stderr)
        print(f"[build-cache-freshness] hint: run `rm -rf build/` before next `pipx install --force /local/path`", file=sys.stderr)
        return 1  # 非零提示，但不 ABORT install（仅警告）
    return 0
```

**配套 dogfood TC**：tmpdir 模拟 build/lib/.../scaffold_v2/ 含 src/ 已删的 `usage-reporter.md` → lint 命中 + 输出 hint。

## 测试用例设计

> regression_scope: targeted
> 波及接口清单（修复将涉及）：
> - `src/harness_workflow/workflow_helpers.py::_SCAFFOLD_V2_MIRROR_WHITELIST`（chg-02 加 3 条）
> - `src/harness_workflow/workflow_helpers.py::_install_self_audit`（chg-04 dev-mode 探测扩展）
> - `src/harness_workflow/workflow_helpers.py::_sync_requirement_workflow_managed_files` 行 3392-3403（chg-03 防御性 assert）
> - `src/harness_workflow/workflow_helpers.py::_sync_scaffold_v2_mirror_to_live` 行 3492-3498（chg-03 防御性 assert）
> - `src/harness_workflow/validate_contract.py::run_contract_cli`（chg-04 / chg-05 注册新 contract）
> - `src/harness_workflow/validate_contract.py::check_user_write_protected_zones`（chg-04 新增）
> - `src/harness_workflow/validate_contract.py::check_build_cache_freshness`（chg-05 新增）
> - `src/harness_workflow/tools/harness_install.py::main`（chg-03 入口 stderr 显式 force_managed received 提示）
> - 本仓 dogfood `./.workflow/context/roles/usage-reporter.md`（chg-01 手工删除）
> - 本仓 `./build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`（chg-01 手工删除）
> - 本仓 `./.codex/harness/managed-files.json`（chg-01 摘除 usage-reporter.md key）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | tmpdir 模拟 venv mirror 含 `usage-reporter.md`（被 build/ 污染） + managed_state 登记该文件 + live 中存在 → 跑 `harness install --agent claude` | mirror 含 → 不触发反向清理（chg-01 仅靠手工 + chg-05 lint 兜底；本 TC 仅断言现状不退化）；同时手工跑清理脚本（chg-01）后再跑 install → live 文件被 archive 到 LEGACY_CLEANUP_ROOT | AC-01 真清理 usage-reporter.md | P0 |
| TC-02 | tmpdir 创建 `flow/bugfixes/bugfix-99-test/bugfix.md` + `context/experience/regression/reg-99.md` + `context/experience/risk/test.md` → 跑 `harness install --agent claude` | self-audit silent skip 三者；drift count 不增 | AC-02 白名单补 3 条 | P0 |
| TC-03 | tmpdir 模拟 managed_state 登记 + hash 改过 + 跑 `harness install --agent claude --force-managed` | stdout 无 `skipped modified`；stderr 无 `skipping user-modified`；stderr 含 `[install_repo] force_managed received: True` | AC-03 force_managed 透传防御 | P0 |
| TC-04a | tmpdir 模拟 user project 手写 `.workflow/context/roles/my-custom-role.md` → 跑 `harness validate --contract user-write-protected-zones` | exit 1；stderr 含 `[user-write-protected-zones] violation: .workflow/context/roles/my-custom-role.md` | AC-04 用户写保护硬门禁 | P0 |
| TC-04b | 本仓（dev mode：pyproject name = "harness-workflow"）跑 `harness validate --contract user-write-protected-zones` | exit 0；silent skip；无任何输出 | AC-04 dev-mode 自动豁免 | P0 |
| TC-04c | tmpdir + 工具产出区文件（`flow/requirements/req-99/requirement.md`） → 跑 `harness validate --contract user-write-protected-zones` | exit 0；silent skip | AC-04 工具产出区豁免 | P1 |
| TC-04d | 三层 dev-mode 探测分别命中：(i) pyproject name (ii) src/harness_workflow/ 目录 (iii) HARNESS_DEV_REPO_ROOT env | 三种情况均触发 dev mode 豁免 | AC-04 三层探测 | P1 |
| TC-05a | tmpdir 模拟 `build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md` 存在但 src/ 无 → 跑 `harness validate --contract build-cache-freshness` | exit 1；stderr 含 `[build-cache-freshness] WARNING: 1 stale file(s)` + `hint: run rm -rf build/` | AC-05 build/ 残留 lint | P0 |
| TC-05b | tmpdir 无 build/ 目录 → 跑 `harness validate --contract build-cache-freshness` | exit 0；silent skip | AC-05 build 不存在豁免 | P1 |
| TC-06 | 本仓 `.workflow/context/roles/usage-reporter.md` 实际清理 + `.codex/harness/managed-files.json` 摘除 + build/ 清理 + pipx install --force 重装 → 跑 `harness install --agent claude` | self-audit drift count 减少（不再含 usage-reporter.md 误报） | AC-01 / AC-02 联动 | P1 |

> AC 字段对应 bugfix.md §Validation Criteria 段。

## 8. 经验沉淀候选（在 done 阶段写入 `experience/roles/regression.md`）

### 经验十四候选：本仓 vs 用户项目边界识别协议

**场景**：harness 工具自身是开发期 dogfood 仓库（src/ + scaffold_v2 + .workflow/ 共存），与用户项目（仅 .workflow/ + skill/commands 由 harness 工具产出，不含 src/）共用同一套 install / lint 逻辑时，必须识别"本仓 vs 用户项目"以决定门禁是否激活。

**经验内容**：三层判定（OR 关系）：
1. `pyproject.toml::name == "harness-workflow"`（最稳）
2. 存在 `src/harness_workflow/` 源码目录（次稳，覆盖 fork / 重命名场景）
3. `HARNESS_DEV_REPO_ROOT` env 命中当前 root（escape hatch）

任一命中 = dev mode → 门禁 silent skip；全否 = user project → 门禁强制激活。dogfood 自检时三种判定各跑一遍 TC（chg-04 TC-04d）。

**反例**：bugfix-7 chg-02 解锁 `_install_self_audit` 触发面后，仅保留 env 单通道，本仓自身 dogfood 时若忘 export env 就被当 user project 跑 → drift 12 条全报。

**沉淀路径**：`.workflow/context/experience/roles/regression.md` 经验十四（done 阶段写入）

### 经验十五候选：build/ 缓存污染 mirror 的部署链条问题

**场景**：开发者在本地仓库做 src/ 删文件改动 + commit + `pipx install --force /local/path`，但因 setuptools 优先从 `build/lib/` 取已编译副本（避免重新编译），src/ 已删文件仍以 stale 状态进入 venv → venv 中 scaffold_v2 包仍含已删文件 → install 时 mirror 包含 stale → `set(managed_state.keys()) - set(mirror.keys())` 差集恒空 → 反向清理永不触发。

**经验内容**：扩展经验十二（pipx git URL 安装 vs 本地 HEAD），新增"本地 build/ 缓存"维度的 L2 失配：
1. **诊断方式**：`ls build/lib/.../scaffold_v2/` vs `ls src/.../scaffold_v2/`，差集 = stale 候选；同理 venv 中 mirror 内容 vs src/。
2. **修复路径**：`rm -rf build/` 后再 `pipx install --force /local/path`，保证 setuptools 从 src/ 重新拷贝。
3. **lint 防再犯**：`harness validate --contract build-cache-freshness` 扫 build/lib/ 与 src/ 差集，命中即 stderr WARNING + hint 清理（chg-05 落地）。

**反例**：bugfix-7 chg-01 实现反向清理后只测 mirror 干净的场景，没测 mirror 被 build/ 污染的边界 → 用户实际跑出 reg-08 同根因复发。本经验作为经验十二的扩展。

**沉淀路径**：`.workflow/context/experience/roles/regression.md` 经验十五（done 阶段写入），与经验十二并列。

### 经验十六候选：白名单设计原则（工具产出区 vs 模板态）

**场景**：每次新加 stage / 新加经验类型 / 新加 reg / bugfix 命令分支时，`_SCAFFOLD_V2_MIRROR_WHITELIST` 必须同步加新工具产出区路径，否则 self-audit 会误报为 drift。

**经验内容**：
- **白名单 = 工具运行时产出区**（`flow/requirements/` / `flow/bugfixes/` / `state/sessions/` / `context/experience/{stage,regression,risk}/` 等）
- **mirror = 模板态**（src/.../scaffold_v2/ 中所有非白名单文件）
- **二者对立**：白名单中文件 install 不动；mirror 中文件 install 同步覆盖。
- **新加 stage / 经验类型时必须同步加白名单**（contract layer reviewer checklist 项；建议 chg-02 落地后加 review 模板更新）。

**反例**：bugfix-2 引入 `flow/bugfixes/`、reg-NN 引入 `context/experience/regression/`、known-risks.md 引入 `context/experience/risk/` 时，开发者均未同步加白名单 → 用户跑 install 后 self-audit drift 误报 7 条 → bugfix-8 chg-02 修复。

**沉淀路径**：`.workflow/context/experience/roles/regression.md` 经验十六（done 阶段写入） + reviewer.md checklist 加"新加白名单时核对工具产出区清单"硬条目。

---

> 诊断完成时间：2026-04-28
> 诊断师：regression（opus）
> 路由决定：confirm → executing
> 5 chg 拆分确认：chg-01（真清理 usage-reporter.md）+ chg-02（self-audit 白名单补 3 条）+ chg-03（--force-managed 透传防御）+ chg-04（user-write-protected-zones 硬门禁）+ chg-05（build/ 残留 lint）
