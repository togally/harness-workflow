# Session Memory

## 1. Current Goal

- req-25 / chg-01：完成 req-27 遗留的 requirement 路径迁移，让 validate / archive / rename 按新路径 `artifacts/{branch}/requirements/` 正常工作；并为老仓提供一键迁移命令。
- 本轮角色：**executing（开发者）**。按 plan.md Step 1-8 实现并自测。

## 2. Current Status

- [x] Step 1 — 定位并读取 9 处硬编码（行号 2052 / 2863 / 3134 / 3377 / 3530 / 3562 / 3782 / 3830 / 3897 + P1-06 的 3791），确认与 plan.md 一致
- [x] Step 2 — 设计 helper 签名与降级策略
- [x] Step 3 — 实现 helper（`_REQUIREMENT_ROOT_NOISE_FILENAMES`、`_has_substantive_content`、`resolve_requirement_root`、`resolve_archive_root`、`migrate_requirements`）
- [x] Step 4 — 逐处替换 9 处硬编码 + P1-06（archive_base → `resolve_archive_root`）
- [x] Step 5 — helper 单元自测 13/13 通过
- [x] Step 6 — P1-06 archive_base 对齐，降级告警与文案对齐
- [x] Step 7 — 新增 `harness migrate requirements [--dry-run]`（工具脚本 + CLI 注册 + helper）；单元自测 19/19 通过
- [x] Step 8 — 测试床端到端 10 个场景全部通过

## 3. Validated Approaches

### 3.1 最终实现方案
- **helper 位置**：`workflow_helpers.py`，`_get_git_branch` 之后、`archive_requirement` 之前插入 `_REQUIREMENT_ROOT_NOISE_FILENAMES` / `_has_substantive_content` / `resolve_requirement_root` / `resolve_archive_root` / `migrate_requirements`
- **降级策略**：`artifacts/{branch}/requirements` → `artifacts/requirements` → `.workflow/flow/requirements`，降级时 stderr 告警 + 引导运行 `harness migrate requirements`
- **噪声过滤**：模块级 frozenset `{".DS_Store", ".gitkeep", "Thumbs.db", ".keep"}`，仅扫直接子节点
- **`_required_dirs`**：追加 `artifacts/{branch}/requirements`（不删 legacy）
- **`_next_req_id`**：追加扫描 `resolve_requirement_root(root)`，用 resolve 后路径去重避免重复计数
- **迁移命令**：`harness migrate requirements [--dry-run]`；扫描 legacy + artifacts/requirements；冲突不覆盖；src==dst 幂等；dry-run 恒返回 rc=0
- **CLI 注册**：新增 `src/harness_workflow/tools/harness_migrate.py` + `cli.py::build_parser` 的 `migrate` 子命令 + `main()` 的分发分支，按照现有 `rename` 风格

### 3.2 代码改动清单（绝对路径 + 行号区间）
- `/Users/jiazhiwei/IdeaProjects/harness-workflow/src/harness_workflow/workflow_helpers.py`
  - 顶部 import：加 `import sys`（line 8）
  - `_required_dirs`（line ~2045-2071）：追加 `artifacts/{branch}/requirements`
  - `_next_req_id`（line ~2866-2894）：扫描源追加 `resolve_requirement_root(root)`，用 `resolve()` 去重
  - `create_suggest_bundle`（line ~3149 附近）：`req_dir` 改走 `resolve_requirement_root(root)`
  - `create_regression`（line ~3390 附近）：req_dir 与 regressions_base fallback 均改走 helper
  - `rename_requirement`（line ~3545 附近）：`requirements_dir` 改 `resolve_requirement_root(root)`
  - `rename_change`（line ~3577 附近）：req_dir 解析改 `resolve_requirement_root(root)`
  - 新 helper 块（line ~3793-3983）：`_REQUIREMENT_ROOT_NOISE_FILENAMES` / `_has_substantive_content` / `resolve_requirement_root` / `resolve_archive_root` / `migrate_requirements`
  - `archive_requirement`（line ~3985 附近）：`requirements_dir` + `archive_base` 均改走 helper（P1-06 在此）
  - `validate_requirement`（line ~4095 附近）：`requirements_dir` 改 `resolve_requirement_root(root)`
- `/Users/jiazhiwei/IdeaProjects/harness-workflow/src/harness_workflow/cli.py`
  - `build_parser` 新增 `migrate_parser`（与 `rename_parser` 相邻）
  - `main` 新增 `if args.command == "migrate"` 分支
- `/Users/jiazhiwei/IdeaProjects/harness-workflow/src/harness_workflow/tools/harness_migrate.py`（新建）

### 3.3 测试床路径
- 主测试床（空仓场景 T1-T4）：`/tmp/harness-regression-chg01-fresh-1776570607`
- legacy 仓（T5-T7 + T9）：`/tmp/harness-regression-chg01-legacy-1776570678`
- 冲突仓（T8）：`/tmp/harness-regression-chg01-conflict-1776570703`
- legacy 预置仓（T10 降级告警验证）：`/tmp/harness-regression-chg01-legacy-presence-1776570737`
- helper 单元自测脚本：`/tmp/harness-chg01-selftest/test_helpers.py`

### 3.4 测试结果

单元自测（`/tmp/harness-chg01-selftest/test_helpers.py`）：**32/32 通过**
- Step 5.1 `resolve_requirement_root` 三级降级：10 个断言全绿
- Step 5.2 `resolve_archive_root` 两级降级：3 个断言全绿
- Step 7.6 `migrate_requirements`：19 个断言全绿（empty / dry-run / real / idempotent / conflict / middle-path / dry-run-on-conflict）

端到端测试（测试床 10 个场景）：**10/10 通过**
| # | 场景 | rc | 关键结果 |
|---|------|----|----------|
| T1 | 空仓 `harness requirement "test-A"` | 0 | 落到 `artifacts/main/requirements/req-01-test-A` |
| T2 | 空仓 `harness validate` | 0 | 正确找到新路径 req，`Artifact validation passed` |
| T3 | 空仓 `harness rename requirement req-01 test-B` | 0 | 目录搬到 `artifacts/main/requirements/test-b`（P0-05 归零） |
| T4d | 空仓 `harness archive test-b --folder chg01-test` | 0 | 产物落到 `artifacts/main/archive/chg01-test/test-b`（P0-04 + P1-06 归零） |
| T5 | legacy `harness migrate requirements --dry-run` | 0 | 打印 plan 未落盘 |
| T6 | legacy `harness migrate requirements` | 0 | 搬迁成功，legacy 目录空，新路径有数据 |
| T7 | legacy 再跑一次 | 0 | `nothing to migrate`（幂等） |
| T8 | 冲突仓 `harness migrate requirements` | 1 | src + dst 均未动，stderr 冲突提示 |
| T9 | legacy 仓迁移后 `harness validate` | 0 | 无降级告警（helper 正确识别新路径） |
| T10 | legacy 仓迁移前 `harness validate` | 0 | 有降级告警 + 迁移提示（P0-03 归零） |

所有日志存于各测试床的 `regression-logs/chg-01/` 目录。

## 4. Failed Paths

无。所有测试一次性通过，未出现需要回滚或重试的路径。

## 5. Candidate Lessons（由 executing 验证后，可沉淀至 `.workflow/context/experience/roles/executing.md` 或 `planning.md`）

```markdown
### 2026-04-19 路径迁移 3 件套：helper + 批量替换 + 迁移命令
- Symptom: req-27 只改了写入端，读取端 9 处硬编码仍在旧路径，导致 validate / archive / rename 三命令全挂，且老仓没有迁移工具。
- Cause: 目录结构重构缺少"唯一路径解析入口"抽象 + 批量硬编码未清理 + 无存量数据迁移路径。
- Fix: ① 抽 `resolve_<resource>_root` helper 作为唯一入口，内置降级告警引导用户；② 批量替换硬编码（grep 校对）；③ 同步新增一次性迁移命令 `harness migrate <resource>`，支持 dry-run + 冲突不覆盖 + 幂等。
- 泛化建议: 目录结构重构类 change 的"三件套"标准模板：helper + 批量替换 + 迁移命令，缺一都会造成"写新读旧"或"新老用户拆分"。
```

```markdown
### 2026-04-19 "实质性非空"判定必须过滤噪声
- Symptom: macOS 的 `.DS_Store` 和团队约定的 `.gitkeep` 会让 `any(p.iterdir())` 在空目录上返回 True，导致 helper 不降级。
- Cause: OS / VCS 自动生成的占位文件在 fs 层面也是"存在"。
- Fix: 提取模块级 `frozenset({".DS_Store", ".gitkeep", "Thumbs.db", ".keep"})`；过滤后再判空。
- 泛化建议: 任何"目录存在且有实际内容"判定都应配噪声白名单，且提取为可扩展模块级常量。
```

```markdown
### 2026-04-19 CLI 工具脚本架构下的 editable 安装
- Symptom: harness 的子命令走 `_run_tool_script` 分发到 `tools/*.py`；这些脚本独立 `python3` 执行会 ModuleNotFoundError（因为 harness_workflow 包只在 pipx venv 里）。
- Cause: 工具脚本通过 `sys.path.insert(0, parent/"src")` 加路径，但只在 pipx venv 内的 python 能解析包。
- Fix: 开发期用 `pipx install --force --editable <repo>` 让 pipx venv 直接指向 src；修改源码无需重装。测试脚本要用 pipx venv 的 python 调工具脚本（`/Users/jiazhiwei/.local/pipx/venvs/harness-workflow/bin/python`）。
- 泛化建议: 在这种架构下 CLI 与 helper 改动验证必须用 editable 安装，不然所有 `harness xxx` 都跑的是旧代码。
```

## 6. 衍生问题（非本 chg-01 范围，已记录供后续 bugfix）

1. **`harness archive` CLI interactive wrapper 缺省行为**：`cli.py::main` 在 archive 分支强制调 `prompt_requirement_selection(done_reqs, preselect=args.requirement)` 并忽略用户显式传入的 `requirement`，导致 `harness archive test-b` 仍然用 `state/requirements/` 里的首个 done yaml 作为 selected。改进方向：若显式传入 `args.requirement`，直接透传、跳过 prompt。→ 建议走 P0-02 或独立 bugfix。
2. **`rename requirement` 未更新 `.workflow/state/requirements/*.yaml` 文件名 + runtime active_requirements**：rename 后 state yaml 仍挂旧 id，导致 archive 找不到对应 state。非本 chg-01 范围。建议走独立 bugfix。
3. **`resolve_artifact_id` 在 english language 下 slugify `test-B` → `test-b`**：导致 `rename req-01 test-B` 得到的目录名是 `test-b` 而非 `req-02-test-b`（没加 req 前缀）。非本 chg-01 范围，是 rename 逻辑自身语义问题。
4. **`harness init` 初始化后 runtime.yaml 预置 `current_requirement: "req-25"` + `stage: "done"`**：明显是 scaffold_v2 模板污染。属于 P0-02（scaffold 清洗）范围。
5. **`_required_dirs` 会预创建空的 `.workflow/flow/archive`**：`OPTIONAL_EMPTY_DIRS` 在 line 88-90 仍保留 legacy archive 目录。init 后 `.workflow/flow/archive/main/...` 会含 scaffold 残留（测试床 T4d 前手工 rm -rf 了）。建议 P0-02 配套清理。

## 7. Next Steps

- 主 agent：确认本 executing 产出后，建议直接推进到 testing 阶段（不由本 subagent 操作 `harness next`）。
- testing 阶段：可直接复用 `/tmp/harness-regression-chg01-fresh-1776570607` 及 legacy / conflict 测试床，日志已在各 bed 的 `regression-logs/chg-01/` 就位。

## 8. Open Items

- 衍生问题 1-5 需要后续单独走 bugfix 或 P0-02。
- `.workflow/context/experience/roles/executing.md` / `planning.md` 的经验沉淀建议留给 testing / acceptance / done 阶段验证后再入库，避免未验证经验污染。
