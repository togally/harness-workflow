---
id: chg-02
title: "升级保护 helper：mirror 白名单 + protected-zones 双豁免（artifacts/{branch}/project/）"
requirement: req-51
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `src/harness_workflow/workflow_helpers.py`

**变更点 A：`_SCAFFOLD_V2_MIRROR_WHITELIST` 常量**（第 172-196 行）

- 在 tuple 末尾追加 1 行：

```python
    # req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）：
    # artifacts/main/project/{constraints,experience,tools}/ 三类项目级机器型文档承载层
    # （chg-01（契约底座-artifacts-project-豁免）已在 repository-layout.md §2.1 / §3 顶部豁免段落地）。
    # 跨项目语义不通用，不纳入 scaffold_v2 mirror；harness install / update / force-managed 全流程跳过。
    "artifacts/main/project/",
```

**位置**：紧接 `"context/experience/risk",` 行后（文件第 195-196 行附近，tuple 闭合 `)` 之前）。

**by-substring 匹配语义**：现有 `_SCAFFOLD_V2_MIRROR_WHITELIST` 由 `_sync_scaffold_v2_mirror_to_live` / `_install_self_audit` 通过 `any(white in relative for white in ...)` 模式判断，故 `"artifacts/main/project/"` 作为前缀子串可命中 `artifacts/main/project/constraints/x.md` / `experience/y.md` / `tools/z.md`。

**变更点 B：`_install_self_audit`**（第 8118-8172 行）

- **不改逻辑**，仅在 docstring（第 8120 行起）追加一句：

```python
    """req-36（...）/ chg-02 + chg-06（解锁 _install_self_audit 触发面）：
    install 末尾自检 helper。chg-02 落地时锁在本仓库自身（pyproject.toml `name = "harness-workflow"`
    锚点）；chg-06 删除 pyproject 锚点段，触发面默认全开（任何 install 都跑），仅保留
    ``HARNESS_DEV_REPO_ROOT`` env 作开发期 escape hatch（env 设置 + 路径不匹配时跳过）。

    req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）注：
    本 helper "反向：live 多出 mirror 没有的非白名单文件" 分支（约第 8152 行）只扫 `.workflow/`，
    天然不扫 `artifacts/`；项目级三类目录在 artifacts/ 下，故无需在本 helper 内单独豁免。
    `_SCAFFOLD_V2_MIRROR_WHITELIST` 新加的 "artifacts/main/project/" 条目仅用于
    `_sync_scaffold_v2_mirror_to_live` 的反向清理 stale_keys 分支兜底。

    返回：drift 计数。命中差异时 stderr 逐条 + 末尾 WARNING；零差异时静默 return 0。
    """
```

**变更点 C：`_sync_scaffold_v2_mirror_to_live`**（第 3401-3539 行）

- **不改逻辑**：现有反向清理 stale_keys 分支（第 3506-3531 行）已有 `if not relative.startswith(".workflow/"): continue`，artifacts/ 路径天然被过滤；
- 仅在 docstring（第 3407 行起）追加一句注释：

```python
    """req-36（...）/ chg-05（install_repo 末尾追加 mirror→live 全量同步）：
    全量遍历 scaffold_v2 mirror dict，对漏写 / 内容不一致的文件做最后一轮同步。
    ...

    req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）注：
    本 helper 反向清理 stale_keys 分支（约第 3506-3531 行）已通过 `if not relative.startswith(".workflow/"):
    continue` 天然过滤 artifacts/ 路径；scaffold_v2 mirror 本身不含 `artifacts/main/project/` 文件
    （chg-01（契约底座-artifacts-project-豁免）已自证），故不会进入 stale_keys 集合；
    `_SCAFFOLD_V2_MIRROR_WHITELIST` 新加的 "artifacts/main/project/" 条目作 defense-in-depth 兜底。
    ...
    """
```

**变更点 D：`_managed_file_contents` / `_scaffold_v2_file_contents`**

- **不改逻辑、不改 docstring**：这两个 helper 从 `TEMPLATE_ROOT / SCAFFOLD_V2_TEMPLATE_ROOT`（即 `src/harness_workflow/assets/scaffold_v2/`）读 mirror，**该 mirror 树中天然不含** `artifacts/main/project/`（chg-01 自证：scaffold_v2 mirror 树只镜像 `.workflow/` 子树）；
- 仅在新测试 `tests/test_req51_project_level_protection.py::TC-02-mirror-dict-not-contain-project-path` 中断言 `_scaffold_v2_file_contents(tmp_path, ...)` 返回的 dict 中无任何 key 以 `artifacts/main/project/` 开头，作为回归防御。

### 1.2 `src/harness_workflow/validate_contract.py`

**变更点 E：`check_user_write_protected_zones`**（第 1107-1165 行）

- **不改 `protected_zones = [".workflow"]` 常量**（保持仅扫 `.workflow/`，artifacts/ 天然不扫）；
- 仅在 docstring（第 1108-1110 行）追加 req-51 豁免说明：

```python
def check_user_write_protected_zones(root: Path) -> int:
    """硬门禁：用户项目模式下扫描 .workflow/ + skill/commands 目录，识别野文件。

    返回：违规文件数（0 = PASS / >0 = ABORT）。

    req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）注：
    `protected_zones` 仅含 `.workflow`，天然不扫 `artifacts/`；req-51 OQ-4 = A 的"protected-zones
    豁免"语义即"扫描范围本身不含 artifacts/{branch}/project/"。下游用户在 `artifacts/main/project/
    {constraints,experience,tools}/` 手写文件不命中本 helper；同时 `.workflow/context/roles/x.md`
    等手写仍命中保护区（豁免精准，不放大保护面）。本注释存在的目的是防止后续 chg 回退性地把
    `artifacts/` 加入 `protected_zones`，从而误伤 req-51 项目级承载层。
    """
```

### 1.3 `tests/test_req51_project_level_protection.py`（新增）

新增独立测试文件，覆盖 chg-02 全部行为。

```python
"""req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）dogfood 测试。

覆盖范围：
- TC-01-install-preserve-project-files：tmpdir 写 artifacts/main/project/constraints/my-rule.md → harness install → 文件保留
- TC-02-mirror-dict-not-contain-project-path：_scaffold_v2_file_contents 返回 dict 不含 artifacts/main/project/
- TC-03-force-managed-not-overwrite-project：harness install --force-managed 不覆盖 artifacts/main/project/
- TC-04-self-audit-not-report-project-drift：_install_self_audit 不报 artifacts/main/project/ drift
- TC-05-protected-zones-exempt-project：check_user_write_protected_zones 在用户项目模式下对 artifacts/main/project/ exit 0；同时对 .workflow/context/roles/x.md 仍 ABORT
- TC-06-whitelist-constant-grep：_SCAFFOLD_V2_MIRROR_WHITELIST 含 "artifacts/main/project/" 条目
"""
```

### 1.4 mirror 同步（硬门禁五合规）

- `workflow_helpers.py` 不在 scaffold_v2 mirror 范围（src/ 不被 mirror）；
- `validate_contract.py` 不在 scaffold_v2 mirror 范围（src/ 不被 mirror）；
- `tests/` 不在 scaffold_v2 mirror 范围；
- **本 chg 无 scaffold_v2 mirror 同步要求**（与 chg-01 强制 mirror 同步不同；硬门禁五保护面是 `.workflow/{context,tools,evaluation,flow,state/experience}/`，src/ + tests/ 不在）。

## 2. 实施步骤（顺序 + 命令）

### Step 1：编辑 `_SCAFFOLD_V2_MIRROR_WHITELIST`

- Edit `src/harness_workflow/workflow_helpers.py` 第 195 行附近（`"context/experience/risk",` 后，tuple 闭合 `)` 前）插入 5 行注释 + 1 行 `"artifacts/main/project/",`；
- 自检：

```bash
grep -n "artifacts/main/project/" src/harness_workflow/workflow_helpers.py
# 期望：第 196 行附近命中 1 次（_SCAFFOLD_V2_MIRROR_WHITELIST tuple 内）
```

### Step 2：在 `_install_self_audit` / `_sync_scaffold_v2_mirror_to_live` docstring 加注

- Edit 两处 docstring，添加 req-51 / chg-02 注释段（见 1.1 变更点 B / C）；
- 不改逻辑代码，仅文档；
- 自检：

```bash
grep -n "req-51（项目级规则-经验-工具支持从制品引入）/ chg-02" src/harness_workflow/workflow_helpers.py
# 期望：≥ 3 处命中（whitelist 注释 + _install_self_audit docstring + _sync_scaffold_v2_mirror_to_live docstring）
```

### Step 3：在 `check_user_write_protected_zones` docstring 加注

- Edit `src/harness_workflow/validate_contract.py` 第 1108-1110 行 docstring，追加 req-51 豁免说明；
- 不改 `protected_zones = [".workflow"]` 常量；
- 自检：

```bash
grep -n "req-51（项目级规则-经验-工具支持从制品引入）/ chg-02" src/harness_workflow/validate_contract.py
# 期望：1 处命中（check_user_write_protected_zones docstring）
```

### Step 4：写新测试 `tests/test_req51_project_level_protection.py`

- 6 个 TC，使用 `tmp_path` fixture + `subprocess.run([sys.executable, "-m", "harness_workflow.cli", "install", ...])` 子进程子链路，参考 `tests/test_user_write_protected_zones.py` / `tests/test_install_force_managed_defense.py` 模板；
- 关键约束：用户项目模式（tmp_path 不创建 pyproject.toml + 不创建 src/harness_workflow + 不设 HARNESS_DEV_REPO_ROOT），确保 `_is_dev_repo` 返回 False；
- 自检：

```bash
pytest tests/test_req51_project_level_protection.py -v
# 期望：6 PASS / 0 FAIL
```

### Step 5：契约自检全绿

```bash
harness validate --contract all   # exit 0
pytest tests/ -k "req51 or protected_zone or force_managed" -v   # 期望全 PASS（防回归既有测试）
```

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（本 chg 改动收敛在 helper docstring + 1 个常量 + 1 个新测试文件，破坏面小）
> 波及接口清单：
> - `src/harness_workflow/workflow_helpers.py`（`_SCAFFOLD_V2_MIRROR_WHITELIST` 常量 + 2 处 docstring）
> - `src/harness_workflow/validate_contract.py`（`check_user_write_protected_zones` docstring）
> - `tests/test_req51_project_level_protection.py`（新增）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-Dogfood-01-install-preserve-project-files | tmp_path（用户项目模式）写 `artifacts/main/project/constraints/my-rule.md` 内容 "PROJECT_LOCAL_RULE"，跑 `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install'], cwd=tmp_path)` | exit 0；my-rule.md 内容仍为 "PROJECT_LOCAL_RULE"；mtime 保持（或用断言 read_text 一致即可） | AC-02 | P0 |
| TC-Dogfood-02-force-managed-not-overwrite | 同 TC-01 fixture，跑 `harness install --force-managed`（或 `harness update --force-managed`） | exit 0；my-rule.md 内容仍为 "PROJECT_LOCAL_RULE"；stderr 不含 "overwrote user-modified" 关于 my-rule.md 的行 | AC-02 | P0 |
| TC-Dogfood-03-self-audit-not-report-drift | 同 TC-01 fixture，跑 `harness install`，捕获 stderr | stderr 中**不含** `[install_repo:self-audit] drift detected` 关于 `artifacts/main/project/` 的行 | AC-02 / AC-04 | P0 |
| TC-04-protected-zones-exempt-project | tmp_path 用户项目模式（无 pyproject.toml / 无 src/harness_workflow）写 `artifacts/main/project/constraints/x.md` + `artifacts/main/project/experience/y.md` + `artifacts/main/project/tools/z.md`，调 `check_user_write_protected_zones(tmp_path)` | 返回 0（PASS） | AC-03 | P0 |
| TC-05-protected-zones-still-block-roles | 同 TC-04 fixture，**额外**写 `.workflow/context/roles/my-custom-role.md`，调 `check_user_write_protected_zones(tmp_path)` | 返回 ≥ 1（仍命中保护区，不放大豁免面） | AC-03 | P0 |
| TC-06-whitelist-constant-grep | grep `_SCAFFOLD_V2_MIRROR_WHITELIST` 内容 | 含字符串 `"artifacts/main/project/"` | AC-04 | P1 |
| TC-07-mirror-dict-not-contain-project-path | tmp_path（任意），调 `_scaffold_v2_file_contents(tmp_path, include_agents=False, include_claude=False, language='cn')` | 返回 dict 不含任何以 `artifacts/main/project/` 开头的 key | AC-04（mirror 不污染） | P1 |

**dogfood TC 必填字段（sug-52 落地）说明**：

- TC-01 / TC-02 / TC-03 均使用 `tmp_path` fixture + `subprocess.run([sys.executable, '-m', 'harness_workflow.cli', ...])` 子进程；
- 含 stdout / stderr 断言；
- 不依赖 `runtime.yaml` stage 字段（本 chg 不涉及 stage 流转），故 stage 断言豁免；
- 含 `feedback.jsonl` 事件数断言（install 命令通常 emit ≥ 1 条 install 事件）；
- 对应 AC 字段非空；优先级 P0。

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：常量改动落地
grep -nE '"artifacts/main/project/"' src/harness_workflow/workflow_helpers.py
# 期望：1 行命中（_SCAFFOLD_V2_MIRROR_WHITELIST 内）

# L2：docstring 注释落地
grep -cE "req-51（项目级规则-经验-工具支持从制品引入）/ chg-02" src/harness_workflow/workflow_helpers.py
# 期望：≥ 3 命中

grep -cE "req-51（项目级规则-经验-工具支持从制品引入）/ chg-02" src/harness_workflow/validate_contract.py
# 期望：≥ 1 命中（check_user_write_protected_zones docstring）

# L3：protected_zones 常量保持仅 .workflow（防回退误加 artifacts）
grep -A 3 "protected_zones = \[" src/harness_workflow/validate_contract.py | grep -c "\".workflow\""
# 期望：1（仅 .workflow，无 artifacts）
grep -A 3 "protected_zones = \[" src/harness_workflow/validate_contract.py | grep -c "artifacts"
# 期望：0（artifacts/ 不进 protected_zones，与 chg-01 § 项目级豁免段一致）

# L4：新测试全 PASS
pytest tests/test_req51_project_level_protection.py -v
# 期望：6 PASS / 0 FAIL

# L5：既有测试无回归
pytest tests/test_user_write_protected_zones.py tests/test_install_force_managed_defense.py tests/test_install_repo_sync_contract.py -v
# 期望：全 PASS（无回归）

# L6：契约自检全绿
harness validate --contract all
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

**本 chg 不触发硬门禁五**：

- 改动文件全在 `src/harness_workflow/`（workflow_helpers.py / validate_contract.py）+ `tests/`（test_req51_project_level_protection.py），不在硬门禁五保护面（`.workflow/{context,tools,evaluation,flow,state/experience}/`）内；
- 故无 mirror 同步要求；reviewer 阶段无 mirror diff 检查项。

**自检**（reviewer 复核）：

```bash
git diff --name-only | grep -E "^\.workflow/(context|tools|evaluation|flow|state/experience)/"
# 期望：本 chg 无命中
```
