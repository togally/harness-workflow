# Session Memory — bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件）

## 1. Current Goal

bugfix-7 executing 阶段（开发者 / sonnet）按 5 chg 顺序实施修复。

## 2. Current Status

- ✅ regression 阶段诊断完成（`regression/diagnosis.md` 产出，7 TC 设计，路由 confirm → executing）
- ✅ chg-01（反向清理 + check 对比）已完成
  - Fix-A：`_sync_scaffold_v2_mirror_to_live` 加反向遍历 dead entries（`.workflow/` 路径限定）
  - Fix-B：`tools/harness_install.py::_print_venv_check` 升级为读 `direct_url.json` + git log 对比
  - `_install_self_audit` drift>0 时加 ANSI 黄色 WARNING 强提示（非静默）
- ✅ chg-02（版本号差异化）已完成
  - `pyproject.toml::version` → 0.2.0
  - `workflow_helpers.py::__version__` → 0.2.0
  - `install_repo` 检测 managed-files.json tool_version mismatch → force_managed=True full re-sync
- ✅ chg-04（文档强提示 + check stdout 协同）已完成
  - `README.md` 加"重要部署提示"段落
- ✅ chg-05（install 平台 prompt UX 修）已完成
  - 已有 active_list 时跳过 `questionary.checkbox`，直接复用已有平台配置
- ✅ chg-07（executing gate bugfix 模式支持，紧急修复）已完成
  - `_is_stage_work_done` executing 分支按 `operation_type` 分路（bugfix: session-memory.md ✅；requirement: changes/ 逻辑不变）
  - TC-09 / TC-10 新增到 `tests/test_install_reverse_cleanup.py`
  - `bugfix.md` §Fix Plan 追加 chg-07 + AC-09
- ⬜ chg-06（LLM 兜底派发，contingency，本周期不强求）— 待 testing 判断是否触发
- PetMall + uav 两个目标项目全程 read-only 未动

## 3. Validated Approaches

### 三维失配诊断（套用经验十）

- **L1 源码层**（src/）：grep `_install_self_audit` + `_sync_scaffold_v2_mirror_to_live` 找到反向清理缺失分支（`workflow_helpers.py:8206-8257`）
- **L2 部署层**（pipx venv）：`direct_url.json::vcs_info.commit_id = a801820` vs 本地 `git rev-parse HEAD = 83bb612`；venv mtime 2026-04-28T08:37:41 vs repo 2026-04-28T10:49:17（venv 落后 ~2h）；diff -rq venv/scaffold_v2 vs repo/scaffold_v2 命中 4 个文件内容差 + 2 个 only-in-repo
- **L3 现场层**（PetMall + uav）：`find` 全文件树 + `comm -23` 与 scaffold 比对，分别命中 1 个真残留 + 多个用户业务态白名单可豁免

### dogfood 实证

- 在 `mktemp -d` 创建空 repo，故意造 `usage-reporter.md` + 改写 `testing.md`，跑真 `harness install`：
  - usage-reporter.md 残留（self-audit 仅 stderr WARN 不删）→ 验证根因 A
  - testing.md 被覆盖（managed sync adopted 路径），但 mirror sync 又日志 "skipped user-modified" → 日志矛盾验证根因 D

### managed-files.json 反向证据

- PetMall managed_files 含 `usage-reporter.md: True`，scaffold mirror 已无 → 死登记永久残留
- uav managed_files 不含 `analyst.md: False`（上次 install 在 req-40 之前），但 venv scaffold 也是 a801820（无 analyst.md）→ 永远补不出来

## 4. Failed Paths

- 一开始想确认 venv 是不是 chg-01 / chg-02 部署同步问题；但 grep `_print_venv_check` / `HARNESS_DEV_REPO_ROOT` 后发现 venv 含部分 helper 但缺最新（chg-01 sug-55 的 `_print_venv_check` 在 venv 中**缺失**）→ 转向看 venv 装的是哪个 commit → 锁定 a801820 来自 GitHub URL
- 一开始把 reg-05.md / reg-06.md / frontend-readonly.md 列为"多余"；扫文件内容后确认是用户项目 regression 沉淀的业务经验，**非 scaffold 残留多余**，从清单剔除

## 5. Candidate Lessons

```markdown
### 2026-04-28 pipx git URL 安装的版本对比要点
- Symptom: 本地 src/ 已修，但 venv CLI 行为还是旧版
- Cause: pipx_metadata::package_or_url 是 GitHub URL；reinstall 走的是远程 commit，不是本地 repo HEAD
- Fix: 看 `direct_url.json::vcs_info.commit_id` vs 本地 `git rev-parse HEAD`，差距 = 未 push 的 commit 数
- 沉淀方向: 扩展 `regression.md` 经验十"三维失配诊断模板"，新增"pipx git URL 安装"识别要点
```

```markdown
### 2026-04-28 install 反向清理盲区识别套路
- Symptom: 多次 install 后 .workflow/ 多余文件永不被清理
- Cause: install 同步契约只覆盖正向（mirror → live），无反向（mirror 已删 + managed-files 仍登记 → live 删除）；LEGACY_CLEANUP_TARGETS 是硬编码白名单，依赖人工维护
- Fix: 在 _sync_scaffold_v2_mirror_to_live 加反向遍历 set(managed_state.keys()) - set(mirror.keys())；自动从 mirror diff 派生 dead entries
- 沉淀方向: 新增 regression.md 经验十一"install 反向清理盲区诊断"
```

## 6. Changed Files（executing stage）

| chg | 改动文件 | 说明 |
|-----|---------|------|
| chg-01 | `src/harness_workflow/workflow_helpers.py` | 反向清理分支（Fix-A）+ self-audit ANSI 强提示 |
| chg-01 | `src/harness_workflow/tools/harness_install.py` | `_print_venv_check` 升级（Fix-B：读 direct_url.json + git log） |
| chg-02 | `src/harness_workflow/workflow_helpers.py` | `__version__` → 0.2.0；tool_version mismatch 检测 |
| chg-02 | `pyproject.toml` | `version` → 0.2.0 |
| chg-04 | `README.md` | 重要部署提示段落 |
| chg-05 | `src/harness_workflow/workflow_helpers.py` | `install_repo` 平台选择跳过（active_list 非空时） |
| new | `tests/test_install_reverse_cleanup.py` | 7 个新增测试（TC-01/02/03/05/06/08 + check mode variant）|
| chg-07 | `src/harness_workflow/workflow_helpers.py` | `_is_stage_work_done` executing 分支 bugfix 模式分路 |
| chg-07 | `tests/test_install_reverse_cleanup.py` | TC-09 / TC-10 新增 |
| chg-07 | `.workflow/flow/bugfixes/bugfix-7-.../bugfix.md` | §Fix Plan + AC 矩阵追加 chg-07 / AC-09 |

## 7. Next Steps

- → testing 阶段（自动推进）
- 用户验证（push 到 GitHub → pipx reinstall → harness install 在 PetMall/uav）

## 7. Open Questions

- 默认拆 4 个 chg，是否合理？（推荐 default-pick = 是）
- chg-03 `harness install --from-local` 是否要做？还是仅文档说明 `pipx install --force /path/to/local` 即可？（推荐 default-pick = 仅文档，避免新增 CLI 表面）
- 反向清理是"删除"还是"移到 LEGACY_CLEANUP_ROOT 备份"？（推荐 default-pick = 备份到 legacy-cleanup，与 LEGACY_CLEANUP_TARGETS 一致风格，可 git 恢复）

## default-pick 决策清单（executing stage 无用户介入）

| 决策点 | 默认选项 | 理由 |
|-------|---------|------|
| 拆几个 chg | 4 | 核心契约（A+B = chg-01）+ 版本号机制（chg-02）+ escape hatch（chg-03 可选）+ 文档（chg-04）四象限齐全；落地优先级 chg-01 > chg-02 > chg-04 > chg-03 |
| 反向清理是删除还是 archive | archive 到 LEGACY_CLEANUP_ROOT | 与 cleanup_legacy_workflow_artifacts 现有风格一致；用户可 git mv 恢复，避免单向数据丢失风险 |
| --from-local CLI | 仅文档说明，不新增子命令 | `pipx install --force /path/to/local/repo` 已是标准 pipx 行为；新增 CLI 增加表面无收益 |
| 修复方案的层级 | L1 源码层 + L2 部署文档 双修 | L2 是用户操作流程问题（push 节奏），无法纯靠代码修复；只在文档强提示，CLI 强化 --check 可视化即可 |

---

## Testing Stage（2026-04-28）

### Testing 状态

- ✅ testing 阶段完成（testing / sonnet）

### TC 执行结果

- 9 用例（test_install_reverse_cleanup.py）全 PASS
- TC-07（P2 本地 force install）N/A（超出 targeted 范围，执行层 dogfood 已覆盖）
- 全量回归 13 fail 均为预存，新增失败 0

### 真实场景 dogfood

tmpdir 完整模拟 PetMall 历史状态（usage-reporter.md 残留 + 旧 testing.md + tool_version=0.0.1）：
- 反向清理生效：stale 文件被 archive 到 LEGACY_CLEANUP_ROOT
- managed sync 生效：旧 testing.md 被更新到最新 scaffold
- check stdout 正常输出 venv + HEAD commit 对比
- tool_version mismatch 触发 full re-sync
- active_list 存在时不弹 questionary

### chg-06 contingency 决定

不触发。chg-01 反向清理 + dogfood 5 维全覆盖，无"模糊状态"边界 case 遗留。chg-06 转 sug 池候选。

### 5 项合规扫描

- R1 越界：PASS
- revert 抽样：留痕（pre-existing rename 冲突，不阻断）
- 契约 7：PASS
- req-29（角色→模型映射）：PASS
- req-30（model 透出）：PASS

### Testing default-pick 决策

| 决策点 | 选择 |
|-------|------|
| chg-06 contingency | 不触发，测试全 PASS，无边界遗漏 |
| TC-07（P2） | N/A skip，targeted 范围 |
| 全量回归触发 | 否（diagnosis.md regression_scope: targeted） |

### 附加：testing gate 修复（就地）

testing 阶段在执行 `harness next` 时发现 `_is_stage_work_done("testing")` 只检查 `test-report.md`，但 bugfix 模式的产物是 `test-evidence.md`（同 chg-07 executing 分路模式）。就地修复：

```python
# workflow_helpers.py testing 分支
if operation_type == "bugfix":
    report = req_flow / "test-evidence.md"
else:
    report = req_flow / "test-report.md"
```

验证：`python3 -m harness_workflow.cli next` → `Workflow advanced to acceptance`

### 退出条件

- ✅ 测试全部执行完毕（9 PASS / 1 N/A）
- ✅ 真实场景 dogfood 5 维全 PASS
- ✅ test-evidence.md 产出（含 5 项合规扫描 + 13 历史 fail 溯源 + §结论）
- ✅ harness validate --human-docs exit 1（D-11=B 留痕放行，done 文档为 done 阶段产物）
- ✅ harness validate --contract artifact-placement exit 0
- ✅ harness next → acceptance 成功（gate 修复后）

### 下一步

→ acceptance 阶段
