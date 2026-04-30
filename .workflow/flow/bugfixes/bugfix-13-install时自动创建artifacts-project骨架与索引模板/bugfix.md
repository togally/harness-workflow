---
id: bugfix-13
title: "install时自动创建artifacts-project骨架与索引模板"
created_at: 2026-04-30
operation_type: bugfix
stage: regression
---

## Problem Description

- Symptom：用户仓执行 `harness install`（或带 `--force-managed`）后，`artifacts/project/` 主路径承载层（`constraints/` / `experience/{roles,tool,risk,regression,stage}/` / `tools/` 三个目录骨架 + 6 份 `index.md` 索引模板 + 顶层 `README.md`）**不会被创建**。
- 复现：拿一个未跑过本仓的全新用户仓，跑 `pip install harness-workflow && harness install` → ls `artifacts/project/` → 目录不存在；agent 加载链 `_load_project_level_index(root, scope=…)` 走"主路径不存在 → legacy fallback 不存在 → 返回 []"，落地 `_merge_project_level_files` 全量 rglob fallback 命中 0 文件。
- Impact：
  1. **req-51（项目级规则-经验-工具支持从制品引入）** + **req-52（硬编码 main 路径全面去除-跟项目走-索引懒加载）** 设计的"项目级覆盖能力"对全新用户仓**零可发现性**——用户连"该往哪个目录写自己的项目级 rule / experience / tool"都不知道；
  2. agent 加载链的项目级覆盖功能虽在 `role-loading-protocol.md` Step 7.6 / 7.6.1 已契约化，但**用户没有写入坑位**，等于该能力对存量项目失效；
  3. req-52 chg-04 已让 `_merge_project_level_files` 接入 install_repo + stderr 日志（日志侧能告诉用户"加载了 0 文件"），但**漏了"主动创建骨架 + 写 index.md 模板 + 写 README"**这一步，半截工程。

## Root Cause Analysis

- Root cause：`install_repo()`（`src/harness_workflow/workflow_helpers.py:3745+`）的项目级合并循环（L3781-L3806）只在 `if _main_project.exists():` 分支下走读路径，**主路径不存在时只是记 0 命中（_log_project_level_load(hits=0)）后默默放过**，没有任何"骨架自举（scaffold-bootstrap）"逻辑；scaffold_v2 mirror（`src/harness_workflow/assets/scaffold_v2/`）按契约不含 `artifacts/project/` 任何文件（仅含 `.workflow/` 树，由 `_SCAFFOLD_V2_MIRROR_WHITELIST` 双兜底"artifacts/project/" + "/project/"明文豁免，避免 mirror sync 反向覆盖用户写入），所以 mirror→live 同步链路也不会"顺手"创建这个骨架——属于 req-51 / req-52 设计落地时遗留的**install 写盘缺口**。
- Confirmed real issue：yes。已独立复核主 agent 4 条结论：
  1. 自身仓 `artifacts/project/` 已存在（含 `README.md` + 6 份 `index.md`：`constraints/index.md` + `experience/{roles,tool,risk,regression,stage}/index.md` + 3 份 `.gitkeep`）✅；
  2. `find scaffold_v2 -name "*project*"` 仅命中 `.workflow/context/project/`（project-overview 无关树），mirror 内**无** `artifacts/project/` 模板 ✅；
  3. `grep "artifacts/project/" workflow_helpers.py install_repo 上下文`（L3745-L4145）只命中读路径（`_main_project.exists()` 走 `_merge_project_level_files`），**无**写盘代码 ✅；
  4. `_SCAFFOLD_V2_MIRROR_WHITELIST` 含 "artifacts/project/" + "/project/" 双兜底（L172-L208），契约"artifacts/ 不入 mirror"成立、不可破 ✅。

## Fix Scope

- Affected files / modules（实施时）：
  - `src/harness_workflow/assets/templates/project-skeleton/`（新增模板树，非 mirror 范围；详细落位见 diagnosis.md fix plan）；
  - `src/harness_workflow/workflow_helpers.py::install_repo()`（在 L3777 项目级合并循环之前/之后插入 `_bootstrap_project_skeleton(root)` 调用，幂等 `write_if_missing`）；
  - `tests/test_bugfix_13_project_skeleton_bootstrap.py`（新增 e2e + 幂等性 + 不覆盖用户改动 3 类用例）。
- Out of scope（红线）：
  - **不动** PetMallPlatform / req-52 / req-51 / bugfix-11 / bugfix-12 已落地内容；
  - **不破** "artifacts/ 不入 mirror" 契约——模板树**必须**放 `assets/templates/project-skeleton/`（mirror 外），不放 `assets/scaffold_v2/`；
  - **不动** `_SCAFFOLD_V2_MIRROR_WHITELIST` 的 "artifacts/project/" + "/project/" 双豁免条目；
  - **不动** legacy fallback 逻辑（`artifacts/{branch}/project/` 双轨过渡仍按 chg-01 OQ-A = D-modified 保持）；
  - **不动** scope 枚举（`tools` 不参与索引懒加载，仅 6 个 experience-* / constraints scope 走 `_load_project_level_index`，按现状保留 `tools/` 仅 `.gitkeep` 无 index.md）。

## Fix Plan

详见 `regression/diagnosis.md` §Fix Plan 段。摘要：

1. 新增模板树 `src/harness_workflow/assets/templates/project-skeleton/`，复刻自身仓 `artifacts/project/` 1:1（README + 6 份 index.md + 3 份 .gitkeep）；
2. 新增 `_bootstrap_project_skeleton(root: Path) -> list[str]` helper，复用 `write_if_missing` 实现幂等写入（已有用户改动**绝不覆盖**）；
3. 在 `install_repo()` 入口（`_migrate_workflow_dir` + `_ensure_workflow_dir_gitignore` 之后、项目级合并循环 L3777 之前）调用 helper，stderr 输出 `[install_repo] project skeleton: created N files / skipped M files`；
4. `check=True`（dry-run）模式下不写盘，仅 actions.append("would create artifacts/project/ skeleton: …")。

## Validation Criteria

- 单元 / 集成（必跑）：
  - [x] `pytest tests/test_bugfix_13_project_skeleton_bootstrap.py -v` 全绿（10 用例全 PASS）；
  - [x] `pytest tests/test_req51_project_level_protection.py tests/test_req52_e2e_log.py tests/test_install_whitelist_business_zones.py -v` 全绿（13 用例，零回归）；
  - [x] `pytest tests/ -k "install" -v` 整体回归 PASS。
- CLI dogfood（必跑，子进程真跑）：
  - [x] `python3 -m harness_workflow.cli install` 在 tmpdir fresh repo 中落地 → `project skeleton: created 10 files / skipped 0 files`；`artifacts/project/{constraints,experience,tools}/` 三目录 + 6 份 `index.md` + 顶层 `README.md` + 3 份 `.gitkeep` 全部存在；find count=10；
  - [x] 幂等：第二次 `harness install` → `project skeleton: created 0 files / skipped 10 files`（TC-02 覆盖）；
  - [x] 用户写入保留：my-rule.md + 自定义 README 均字节级保留（TC-03/TC-04 覆盖）。
- 契约 lint（必跑）：
  - [x] `harness validate --contract user-write-protected-zones` PASS（exit=0）；
  - [x] `harness validate --contract all` 仅含预存在历史 contract-7 violations，**无新增违反**（executing 阶段改动未引入新 violation）。
- 完成判据（lint 命令字面，complete after fix）：
  ```
  pytest tests/test_bugfix_13_project_skeleton_bootstrap.py -v
  pytest tests/test_req51_project_level_protection.py tests/test_req52_e2e_log.py -v
  python3 -m harness_workflow.cli validate --contract all
  python3 -m harness_workflow.cli validate --contract user-write-protected-zones
  ```
