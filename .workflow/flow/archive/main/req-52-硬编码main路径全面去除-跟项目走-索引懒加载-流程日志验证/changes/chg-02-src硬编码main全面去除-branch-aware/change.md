---
id: chg-02
title: "src 硬编码 main 全面去除：validate_contract.py + workflow_helpers.py 关键点改 branch-aware + 反例 lint 防回归"
requirement: req-52
operation_type: change
---

# Change Definition

## Why（动机）

req-52 P4（用户原话："硬编码 main 路径要全面去除"）实证清单（req requirement.md §Background §P4 表）共扫到 11+ 处硬编码 `main` 字面值；其中 4 处是**核心病灶**（直接影响下游用户切非 main 分支时的功能正确性），其余是注释 / docstring 字面值（属契约口径同步）。本 chg 把 src 树硬编码 `main` 全面 branch-aware 化，并新增反例 lint 防止后续回归。

历史上下文：PetMallPlatform / uav 等下游项目 git branch 常为 `v1.0.0` / `app_interface` / `member` / `release-2.0`，硬编码 `main` 直接失配 —— 这是 reg-01 路由到 req-52 的核心驱动。

本 chg 是 **chg-01 契约前置后**的源代码层落地：契约（chg-01）→ src（chg-02）→ 索引懒加载（chg-03）→ 主流程接入 + 日志（chg-04）的 DAG 中第二位。

## Scope（范围）

### In Scope

#### 核心病灶（4 处，直接影响功能）

1. **`src/harness_workflow/validate_contract.py:551`** `str(artifacts_dir / "main" / "archive")`：archive 历史豁免目录硬编码 main →
   改为 `glob`-based：`set(str(d) for d in artifacts_dir.glob("*/archive") if d.is_dir())`，覆盖任意 branch 下的历史 archive 子目录；

2. **`src/harness_workflow/validate_contract.py:552`** `str(artifacts_dir / "main" / "regressions")`：reg 历史豁免目录硬编码 main →
   改为 `glob`-based：`set(str(d) for d in artifacts_dir.glob("*/regressions") if d.is_dir())`；

3. **`src/harness_workflow/validate_contract.py:562`** `req_base = artifacts_dir / "main" / "requirements"`：规则 0 stage-name 子目录扫描根 →
   改为 `for branch_dir in artifacts_dir.iterdir(): if branch_dir.is_dir(): req_base = branch_dir / "requirements"; ...`，覆盖任意 branch 下的 requirements 树；

4. **`src/harness_workflow/workflow_helpers.py:201`** `_SCAFFOLD_V2_MIRROR_WHITELIST` 字面值 `"artifacts/main/project/"` →
   chg-01 OQ-A 双轨：改为两条
   - `"artifacts/project/"`（主路径，无 branch）
   - `"artifacts/{branch}/project/"` 作为 substring 不可行（白名单匹配是 `any(white in relative for white in WHITELIST)`），改为更通用的 substring `"/project/"` 兜底捕获任意 `artifacts/<anything>/project/...` 路径；
   - 同步注释从 `req-51 / chg-02` 升级为 `req-51 / chg-02 + req-52 / chg-02`。

#### 同源处（4 处，id 唯一性 / 历史 archive 扫描）

5. **`src/harness_workflow/workflow_helpers.py:4153`** `_next_req_id` 扫描归档树 `root / ".workflow" / "flow" / "archive" / "main"` →
   改为 `glob` `root / ".workflow" / "flow" / "archive"` 下所有子目录递归扫 `req-NN`；

6. **`src/harness_workflow/workflow_helpers.py:4187`** `_next_bugfix_id` 同上；

7. **`src/harness_workflow/workflow_helpers.py:6548`** docstring 注释 `artifacts/main/archive/main/req-xx`（双层 branch 反例说明）→
   注释更新为 `artifacts/{branch}/archive/{branch}/req-xx`，明确双层 branch 是历史 reg 残留语义；

8. **`src/harness_workflow/workflow_helpers.py:3426 / 3428 / 8140`** docstring 含 `"artifacts/main/project/"` 字面示例 →
   同步更新为 `"artifacts/project/"`（chg-01 主路径）+ 注明 legacy 兼容。

#### 反例 lint 防回归（新增 1 份 test）

9. 新增 `tests/test_req52_no_main_hardcode.py`：
   - **TC-01**：grep src 树 `"main"` 字面值，命中数 ≤ 白名单（白名单仅 `ff_auto.py:210` `return "main"` + `_get_git_branch(root) or "main"` 兜底默认值；其他字面 `"main"` 全部 FAIL）；
   - **TC-02**：grep src 树 `/ "main" /` Path 拼接形态，命中数 = 0（防 `validate_contract.py:551 / 552 / 562` 同型病再现）；
   - **TC-03**：grep src 树 `"artifacts/main/"` 字面值，命中数 = 0（防 `_SCAFFOLD_V2_MIRROR_WHITELIST` 同型病再现）；
   - **TC-04**：白名单豁免单测（确认 `ff_auto.py:return "main"` + `_get_git_branch(root) or "main"` 形态被白名单豁免）。

#### 不动项（豁免范围内）

- `ff_auto.py:210` `return "main"` —— `_get_git_branch` 失败 fallback 默认值，合理；
- `workflow_helpers.py` 中所有 `_get_git_branch(root) or "main"` 形态 —— 同上 fallback；

### Out of Scope

- 契约文档（`repository-layout.md` / `harness-manager.md` / 等）路径改写 → 归 chg-01（契约层路径迁移-无branch项目级-双轨过渡）；
- 子目录 `index.md` 模板 + `_load_project_level_index` helper → 归 chg-03（索引懒加载-index-md与加载链改造）；
- `_merge_project_level_files` 接入主流程 + stderr 日志 + 端到端 CLI test → 归 chg-04（接入主流程-stderr日志-端到端CLI验证）；
- 下游 PetMallPlatform 路径迁移 → 不在本 req 范围（红线）；
- `_SCAFFOLD_V2_MIRROR_WHITELIST` 数据结构改型（如改为 frozenset）→ 不在本 chg 范围。

## 接口面（对外约束）

- **`validate_contract.py:check_artifact_placement`**：函数签名不变；行为变化：archive / regression / requirements 子目录扫描从 main-only 扩为任意 branch glob；
- **`workflow_helpers.py:_SCAFFOLD_V2_MIRROR_WHITELIST`**：tuple 类型不变；新增 1 ~ 2 个元素；
- **`workflow_helpers.py:_next_req_id` / `_next_bugfix_id`**：函数签名不变；扫描覆盖面扩大；
- **`tests/test_req52_no_main_hardcode.py`**：新增文件，pytest 反例 lint。

## 影响面

- **直接影响**：`validate_contract.py` 1 处函数体改动（约 10 行）；`workflow_helpers.py` 5 处改动（行 201 / 4153 / 4187 + 3 段注释）；新增 1 份 test 文件；
- **间接影响**：
  - `harness validate --contract artifact-placement` 在非 main 分支仓上的扫描覆盖面改变（之前可能漏扫，现在覆盖）；
  - 下游用户切非 main 分支后 `harness install --force-managed` 不再覆盖 `artifacts/<其他 branch>/project/` 路径（同时 `artifacts/project/` 主路径也豁免）；
- **现有 5 份 req-51 tests 影响**：`test_req51_project_level_protection.py:238` 断言 `"artifacts/main/project/" in _SCAFFOLD_V2_MIRROR_WHITELIST` —— 本 chg 改白名单字面值时需**同步更新**该断言为新主路径 + legacy substring（**不破坏**测试，仅同步字面值）。

## 验收边界（chg 级 PASS 条件）

- AC-03（src 硬编码 main 全面去除）：
  - `grep -rn '"main"' src/harness_workflow/` 命中数 ≤ 白名单（含 ff_auto.py:210 + workflow_helpers.py 中 `_get_git_branch(root) or "main"` 形态共约 12 ~ 14 处兜底默认值）；
  - validate_contract.py:551 / 552 / 562 改为 glob-based；
  - workflow_helpers.py:201 改为新主路径 + legacy substring；
  - workflow_helpers.py:4153 / 4187 改为 glob-based；
- AC-04（反例 lint 防回归）：`pytest tests/test_req52_no_main_hardcode.py -v` 全 PASS（≥ 4 用例）；
- 现有 5 份 req-51 tests 同步更新断言后全 PASS（无回归）；
- `harness validate --contract all` exit 0；`harness validate --contract artifact-placement` 在 dev branch（非 main）仓 exit 0。
