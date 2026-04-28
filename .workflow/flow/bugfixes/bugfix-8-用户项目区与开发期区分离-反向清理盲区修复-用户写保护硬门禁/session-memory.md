# Session Memory — bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）

## 1. Current Goal

- executing stage：实施 5 chg 完成 ✅

## 2. Current Status

- [x] runtime.yaml 状态确认：operation_type=bugfix / operation_target=bugfix-8 / stage=executing
- [x] 角色加载完成：base-role.md → stage-role.md → executing.md
- [x] 模型一致性自检：role-model-map.yaml::roles.executing = sonnet，与本 subagent 期望一致

### ✅ chg-01（真清理 usage-reporter.md）

改动文件清单：
- 删除 `./build/lib/harness_workflow/assets/scaffold_v2/.workflow/context/roles/usage-reporter.md`（build/ stale）
- 删除 `./.workflow/context/roles/usage-reporter.md`（dogfood 自身）
- `./.codex/harness/managed-files.json`：摘除 `.workflow/context/roles/usage-reporter.md` key
- `src/harness_workflow/workflow_helpers.py::LEGACY_CLEANUP_TARGETS`：追加 `usage-reporter.md` 路径（兜底防 mirror 被污染时仍能强制清理）

内部测试结果：
- `tests/test_build_cache_freshness.py::test_tc05c_current_repo_build_freshness` PASS（usage-reporter.md 不在 stale 输出）
- `tests/test_install_reverse_cleanup.py` 全量 PASS（TC-01 基础路径仍有效）

### ✅ chg-02（self-audit 白名单补 3 个业务态目录）

改动文件清单：
- `src/harness_workflow/workflow_helpers.py::_SCAFFOLD_V2_MIRROR_WHITELIST`：17 → 20 条，新增 `flow/bugfixes` / `context/experience/regression` / `context/experience/risk`

内部测试结果：
- `tests/test_install_whitelist_business_zones.py` 3 tests PASS

### ✅ chg-03（--force-managed 透传防御）

改动文件清单：
- `src/harness_workflow/workflow_helpers.py::install_repo`：入口加 `[install_repo] force_managed received: True/False` stderr
- `src/harness_workflow/workflow_helpers.py::_sync_requirement_workflow_managed_files`（行 ~3392）：skip 分支加 `if not force_managed` / `else` 防御
- `src/harness_workflow/workflow_helpers.py::_sync_scaffold_v2_mirror_to_live`（行 ~3492）：同上

内部测试结果：
- `tests/test_install_force_managed_defense.py` 4 tests PASS

### ✅ chg-04（user-write-protected-zones 硬门禁 + dev-mode 三层探测）

改动文件清单：
- `src/harness_workflow/validate_contract.py::_is_dev_repo`：新增（三层判定）
- `src/harness_workflow/validate_contract.py::check_user_write_protected_zones`：新增（保护区扫描）
- `src/harness_workflow/validate_contract.py::run_contract_cli`：注册 `user-write-protected-zones` 入口
- `src/harness_workflow/cli.py::validate choices`：加 `user-write-protected-zones`
- `src/harness_workflow/workflow_helpers.py::install_repo`：末尾接入 `check_user_write_protected_zones`

内部测试结果：
- `tests/test_user_write_protected_zones.py` 10 tests PASS

### ✅ chg-05（build/ 残留 lint）

改动文件清单：
- `src/harness_workflow/validate_contract.py::check_build_cache_freshness`：新增
- `src/harness_workflow/validate_contract.py::run_contract_cli`：注册 `build-cache-freshness` 入口
- `src/harness_workflow/cli.py::validate choices`：加 `build-cache-freshness`

内部测试结果：
- `tests/test_build_cache_freshness.py` 5 tests PASS

## 3. Validated Approaches

### 三维失配诊断（套用经验十 + 经验十一 + 经验十二）

| 维度 | 检查方式 | 实证结果 |
|------|---------|---------|
| L1 src/ | grep `_SCAFFOLD_V2_MIRROR_WHITELIST` + `_install_self_audit` + `validate_contract` | 白名单缺 3 条 + dev-mode 仅 env + 缺 user-write 契约 |
| L2 build/ + venv | `ls build/lib/.../scaffold_v2/.../usage-reporter.md` + `ls ~/.local/pipx/venvs/.../scaffold_v2/.../usage-reporter.md` | build/ 含 stale (mtime 2026-04-24) + venv mirror 受 build/ 污染 |
| L3 PetMall + 本仓 dogfood | PetMall log 12 drift（7 业务态误报）+ 本仓 .workflow/context/roles/usage-reporter.md 仍存在 | 本仓自身也是失配现场（dogfood 边界对偶） |

### 5 chg 拆分依据（用户拍板）

| chg | 修复目标 | 落地点 | 性质 |
|-----|---------|--------|------|
| chg-01 真清理 usage-reporter.md | 三处手工删除 + managed-files 摘除 + venv 重装 | 本仓手工 + chg-05 lint 防再犯 | 手工 + lint |
| chg-02 白名单补 3 条 | flow/bugfixes / experience/regression / experience/risk | workflow_helpers.py:180 | 代码 |
| chg-03 --force-managed 防御 | 显式 if not force_managed + 入口 stderr 提示 | workflow_helpers.py:3392, 3492 + harness_install.py | 代码 |
| chg-04 user-write-protected-zones 硬门禁 | 新 contract + dev-mode 三层探测 | validate_contract.py 新增 | 代码 |
| chg-05 build/ 残留 lint | 新 contract + 跑 build/lib vs src/ 差集 | validate_contract.py 新增 | 代码 |

## 4. Failed Paths

无失败路径（诊断阶段无尝试性写盘动作）。

## 5. Candidate Lessons（done 阶段写入 experience/roles/regression.md）

### 经验十四候选：本仓 vs 用户项目边界识别协议（dev-mode 三层探测）
- 场景：harness 工具 dogfood 仓 vs 用户项目共用同一套 install / lint 逻辑时
- 经验：三层判定（OR）：(i) pyproject.toml::name = "harness-workflow" (ii) src/harness_workflow/ 目录存在 (iii) HARNESS_DEV_REPO_ROOT env
- 反例：bugfix-7 chg-02 解锁 self-audit 触发面后仅保留 env 单通道 → 本仓 dogfood 时若忘 export env 就被当 user project 跑

### 经验十五候选：build/ 缓存污染 mirror 的部署链条问题（扩展经验十二）
- 场景：开发者 src/ 删文件 + commit + `pipx install --force /local/path`，但 setuptools 优先从 build/lib/ 取 → stale 进 venv → mirror 污染 → 反向清理差集恒空
- 经验：诊断方式 = `ls build/lib/.../scaffold_v2/` vs `ls src/.../scaffold_v2/` 差集；修复 = `rm -rf build/` 后重装；防再犯 = `harness validate --contract build-cache-freshness` 扫差集（chg-05）

### 经验十六候选：白名单设计原则（工具产出区 vs 模板态）
- 场景：每次新加 stage / 经验类型 / 命令分支，`_SCAFFOLD_V2_MIRROR_WHITELIST` 必须同步加新工具产出区路径
- 经验：白名单 = 工具运行时产出区；mirror = 模板态；二者对立；新加时必须同步加白名单（contract layer reviewer checklist 项）
- 反例：bugfix-2 引入 flow/bugfixes、reg-NN 引入 experience/regression、known-risks 引入 experience/risk 时，开发者均未同步加白名单 → 用户跑 install 后 self-audit drift 误报 7 条

## 6. Next Steps

- 本 stage 退出 → harness regression --confirm（路由 → executing）
- executing 阶段按 5 chg 顺序落地（chg-01 / chg-05 涉及手工清理 + lint，建议先做以释放 mirror 污染状态；chg-02 / chg-03 / chg-04 为代码层修复，可并行）
- testing 阶段按 §测试用例设计 TC-01 ~ TC-06 跑 dogfood + 子进程 CLI 验证（经验十三：三模式覆盖；经验十：子进程 dogfood 红线）

## 7. Open Questions

- 无（用户已拍板 5 chg，所有现象证据齐全，路由清晰）

## default-pick 决策清单（req-31 / chg-05 同阶段不打断协议）

- 无（本 stage 所有方案均按用户拍板的 5 chg 拆分推进，未触发新争议点）

## 模型一致性自检

- 期望 model：role-model-map.yaml::roles.regression = "opus" → opus 4.7
- 实际：本 subagent 运行于 Opus 4.7 (1M context)，与 role-model-map.yaml 声明一致 ✓

---

## redo 记录 ✅（2026-04-28）

### 触发原因

上一轮 testing subagent 违反 chg-01 of req-47 刚加的"破坏性 git 命令禁止"红线——为做 revert 抽样合规扫描跑了 `git revert + git checkout -- .`，把 working tree 里所有未 commit 的 src/ 改动**全部还原**。

### 重做摘要

- 4 个新测试文件已在（untracked，未受 git checkout 影响）；直接复用，不重写。
- 5 chg src/ 修改全部重做：
  1. **chg-01**：删除 `.workflow/context/roles/usage-reporter.md`；`LEGACY_CLEANUP_TARGETS` 追加 `usage-reporter.md` 路径兜底；`managed-files.json` 已无该 key（上一轮已完成）
  2. **chg-02**：`_SCAFFOLD_V2_MIRROR_WHITELIST` 追加 3 条（`flow/bugfixes` / `context/experience/regression` / `context/experience/risk`）
  3. **chg-03**：`install_repo` 入口加 `[install_repo] force_managed received: ...` stderr；`_sync_requirement_workflow_managed_files` + `_sync_scaffold_v2_mirror_to_live` 的 skip 分支加 `if not force_managed` / `else` 防御性日志
  4. **chg-04**：`validate_contract.py` 新增 `_is_dev_repo` + `check_user_write_protected_zones`；`run_contract_cli` 注册 `user-write-protected-zones`；`cli.py` choices 追加；`install_repo` 末尾接入
  5. **chg-05**：`validate_contract.py` 新增 `check_build_cache_freshness`；`run_contract_cli` 注册 `build-cache-freshness`；`cli.py` choices 追加

- **本次修复点**（对比上一轮实施说明）：
  - `check_user_write_protected_zones` 输出改为含英文 "violation"（测试要求）
  - `check_build_cache_freshness` 发现 stale 时返回 `len(stale)`（非 0），stderr 输出含 "WARNING"（测试要求）

### 测试结果

- 22 新增测试全 PASS：`pytest tests/test_install_whitelist_business_zones.py tests/test_install_force_managed_defense.py tests/test_user_write_protected_zones.py tests/test_build_cache_freshness.py`（22 passed in 2.76s）
- 全量 `pytest tests/`：688 passed + 13 pre-existing failures + 40 skipped（0 新增 fail）
- `harness validate --contract artifact-placement`：exit 0
- imports OK：`_is_dev_repo`, `check_user_write_protected_zones`, `check_build_cache_freshness`
- `validate --contract user-write-protected-zones`（本仓 dev mode）：PASS exit 0
- `validate --contract build-cache-freshness`（dev mode）：WARNING 1 stale file（artifacts-layout.md），exit 1（WARN 级别）
