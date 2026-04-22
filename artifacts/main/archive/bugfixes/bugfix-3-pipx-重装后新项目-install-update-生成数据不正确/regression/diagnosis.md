# Regression Diagnosis — bugfix-3

## Issue
pipx 重装后，用户在目标项目 `/Users/jiazhiwei/claudeProject/PetMallPlatform` 运行 `harness install` + `harness update`，主观感受"生成的数据不对"。

## 问题描述

### 现象（实际观察到的 3 处异常）

1. **新增/更新的模板文件未被同步** —— 运行 `harness update` 后，目标项目中以下文件仍停留在旧版本（缺少仓库最新 scaffold_v2 中的"对人文档输出（req-26）"等章节）：
   - `.workflow/context/roles/{acceptance,done,executing,planning,regression,requirement-review,stage-role,testing}.md`
   - `.workflow/context/experience/roles/{acceptance,executing,planning,testing}.md`
   - `.workflow/context/experience/risk/known-risks.md`（另有用户项目自定义扩展，但模板部分也未刷新）

   证据：`diff -rq scaffold_v2/.workflow/ 目标项目/.workflow/` 报出 14 处 `differ`；`.codex/harness/managed-files.json` 中 **完全没有** 上述文件的哈希记录。

2. **`.workflow/context/experience/index.md` 每次 update 被循环归档** —— `cleanup_legacy_workflow_artifacts` 把 `experience/index.md` 列入 `LEGACY_CLEANUP_TARGETS`，每次 update 都会：
   - 先把现有 `experience/index.md` 搬到 `.workflow/context/backup/legacy-cleanup/.workflow/context/experience/index.md`
   - 再由 `_refresh_experience_index(root)` 在原位置重新生成

   证据：目标项目 `legacy-cleanup/.workflow/context/experience/` 下已有 `index.md` 和 `index.md-2` 两份旧副本（多次 update 累积），且 `_unique_backup_destination` 会持续追加 `-3/-4/...`。

3. **目标项目主线数据并未被主仓库污染** —— 排查"是否错误复用主仓库 req-02~11 / bugfix-3"：
   - 目标项目 `runtime.yaml` 为 `operation_target: req-02 / stage: done / active_requirements: []`，这是目标项目自己历史 req-02（会员/宠物档案）遗留的正常 open 模式收尾状态，**与主仓库 `bugfix-3 / regression` 无关**。
   - `.workflow/state/requirements/`、`state/sessions/`、`flow/requirements/`、`flow/suggestions/` 全部为空。未发现主仓库需求/变更被拷入。
   - pipx 实际安装为 **editable** 模式（`__editable__.harness_workflow-0.1.0.pth` → `/Users/jiazhiwei/IdeaProjects/harness-workflow/src`）。`harness` 执行的代码路径就是主仓库工作副本，版本字符串 `0.1.0` 与 `pyproject.toml` 一致；不存在"装旧包"问题。

### 复现步骤
1. `pipx reinstall harness-workflow`（editable 指向 `/Users/jiazhiwei/IdeaProjects/harness-workflow/src`）
2. `cd /Users/jiazhiwei/claudeProject/PetMallPlatform && harness install`（CLAUDE）
3. `harness update`
4. `diff -rq /Users/jiazhiwei/IdeaProjects/harness-workflow/src/harness_workflow/assets/scaffold_v2/.workflow/ ./.workflow/`

### 影响范围
- 所有"在 harness 某次发布前就已经 install 过、包含旧 scaffold 文件"的历史项目，执行 `harness update` 后都无法拿到模板新增章节（除非手工 `--force-managed`）
- `experience/index.md` 每次 update 必定累积一份历史副本在 `legacy-cleanup/` 下（磁盘污染 + 对人困惑）
- `.codex/harness/managed-files.json` 的 `managed_files` 字典 **漏登记** scaffold_v2 中的多数 `.md` 文件

## 证据

| 观察点 | 结论 | 证据路径 |
|-------|------|---------|
| editable 安装 | pipx 指向主仓库源码 | `/Users/jiazhiwei/.local/pipx/venvs/harness-workflow/lib/python3.14/site-packages/__editable__.harness_workflow-0.1.0.pth` |
| 目标项目 runtime 与主仓库不同 | 未发生数据污染 | 目标 runtime: `operation_target: req-02` vs 主仓: `bugfix-3` |
| 目标项目 state/sessions/requirements 为空 | 未拷入主仓历史 | `ls state/requirements state/sessions flow/requirements flow/suggestions` 皆为空 |
| managed-files.json 漏登记 | update 误判 skipped modified | `grep 'context/roles/executing\|context/roles/done\|...' managed-files.json` 无命中 |
| `experience/index.md` 被循环归档 | 语义错误 | `legacy-cleanup/.workflow/context/experience/index.md` 与 `index.md-2` 同时存在 |
| `context/roles/executing.md` 比模板短 28 行 | 缺最新章节 | `diff scaffold_v2/.../executing.md 目标项目/.../executing.md` 显示缺"对人文档输出（req-26）" |

## 根因分析

**一句话根因**：`update_repo` 的 managed-state 同步链路存在两处设计缺陷，导致用户误以为"数据不对"：

### 根因 A（主因）：`_sync_requirement_workflow_managed_files` + `_refresh_managed_state` 对"存量文件、未登记 hash"的处理不幂等

- `_load_managed_state()` 读不到某 scaffold 文件的历史 hash 时 → `managed_state.get(relative) == current_hash` 判定为 False；
- 第 2587 行分支命中 `skipped modified {relative}`，**不刷新文件内容**；
- 循环结束调用 `_refresh_managed_state()`（行 2140-2150）仅在"当前文件已等于模板"时才写入 hash；
- 既然文件不等于模板，hash 永远写不进去，下一次 update 仍然 `skipped modified`。
- 净效果：任何一次 install 之后 scaffold 新增/修改的文件（典型：req-26 "对人文档" 章节）都永远不会到达目标项目。

**合理修复方向**（只提出，不实施）：
- 第一次发现未登记但存在的 scaffold 文件时，视为 "adopt as managed"，直接覆盖并写入 hash；或
- 对 scaffold_v2 的所有文件，`_sync` 默认行为改为"总是 overwrite 并记录 hash"（`flow/`、`context/` 模板本就是受管部分），仅对用户真正自定义的 `development-standards.md` 等走 skip-on-modified。

### 根因 B（次因）：`LEGACY_CLEANUP_TARGETS` 把 `experience/index.md` 当成 legacy 归档

- `experience/index.md` 是由 `_refresh_experience_index` 每次 update 重生成的活跃文件，不是遗留产物。把它列入 `LEGACY_CLEANUP_TARGETS` 导致"搬家 → 重建 → 下次又搬家"循环。
- `_unique_backup_destination` 产生 `-2/-3/...` 递增，长期 update 会持续堆积垃圾。
- **合理修复方向**：从 `LEGACY_CLEANUP_TARGETS` 中移除 `.workflow/context/experience/index.md`；对目标项目已堆积的 `legacy-cleanup/.workflow/context/experience/index.md*` 做一次性清理即可。

### 非根因（已排除）
- 主仓库数据复用到目标项目：**未发生**。目标项目 runtime/sessions/requirements 皆为自身历史或空。
- pipx 装旧包：**不成立**。editable 模式，跑的就是最新源码。
- `.claude/skills/harness` 内容错乱：**一致**，`diff -rq` 仅多一层 `agent/` overlay（设计内）。

## 结论

- [x] **真实问题**（两个 update 侧 bug）
- [ ] 误判

## 路由决定

- 问题类型：**实现/测试有误**（非需求范围遗漏，也不是设计层面歧义）
- 目标阶段：**testing**
- 命令：`harness regression --confirm`（保留 current_regression） → `harness regression --testing`
- 理由：根因在 `workflow_helpers.py` 的 `_sync_requirement_workflow_managed_files` / `_refresh_managed_state` / `LEGACY_CLEANUP_TARGETS`，属于实现层 bug，需要回到 testing 阶段补齐"update 幂等性"与"index.md 不被循环归档"两条用例后进入 executing 修复。主 agent 据此解锁 bugfix-3 的修复流程。

## 需要人工提供的信息

详见 `required-inputs.md`：仅需用户确认"生成的数据不对"在主观层面具体指哪一面（现象 1 / 2 / 3 / 其他），以便确定 executing 阶段的测试用例优先级；如用户无更多补充，默认按上述根因 A+B 一并修复。
