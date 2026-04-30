---
id: chg-03
title: "索引懒加载：项目级子目录 index.md 模板 + role-loading-protocol Step 7.6 改按需加载 + _load_project_level_index helper"
requirement: req-52
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 6 份 `index.md` 模板（新建占位）

#### 1.1.1 `artifacts/project/constraints/index.md`

```markdown
---
schema_version: 1
scope: constraints
created_by: req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-03（索引懒加载-index-md与加载链改造）
---

# 项目级 constraints 索引

| path | title | scope | when_load | 备注 |
|------|-------|-------|-----------|------|
| <!-- 示例：my-rule.md --> | <!-- 示例：项目独有的代码风格约束 --> | constraints | always | <!-- 加载时机：always / on-stage:executing / on-keyword:lint --> |

> **schema 说明**：
> - `path`：相对本 index.md 同目录的文件路径；
> - `title`：≤ 20 字简短描述（与硬门禁六口径一致）；
> - `scope`：固定 `constraints`（本 index 限本目录）；
> - `when_load` ∈ `{always, on-stage:{stage}, on-keyword:{kw}}`：加载时机控制；
> - `备注`：任意补充说明，可空。
>
> agent 按 `when_load` 解析后按需加载条目（详见 `.workflow/context/roles/role-loading-protocol.md` Step 7.6.1）。
```

#### 1.1.2 `artifacts/project/experience/roles/index.md`、`tool/index.md`、`risk/index.md`、`regression/index.md`、`stage/index.md`

5 份模板与 1.1.1 同 schema，仅 `scope` 字段对应改为 `experience-roles` / `experience-tool` / `experience-risk` / `experience-regression` / `experience-stage`；标题改对应。

### 1.2 `src/harness_workflow/workflow_helpers.py` 新增 helper

**变更点 A：在 `_merge_project_level_files` 函数后（约第 8307 行末尾）新增**：

```python
def _load_project_level_index(
    root: Path,
    scope: str,
) -> list[dict]:
    """req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-03（索引懒加载-index-md与加载链改造）：
    解析项目级子目录 index.md，返回清单（不读取条目内容，由 agent 按 when_load 决定是否加载）。

    入参：
    - root: 项目根目录
    - scope: ∈ {"constraints", "experience-roles", "experience-tool", "experience-risk",
                "experience-regression", "experience-stage"}

    行为：
    1. 主路径 = artifacts/project/{scope_subpath}/index.md（chg-01 主路径，无 branch）
    2. legacy fallback = artifacts/{branch}/project/{scope_subpath}/index.md（chg-01 双轨过渡）
    3. 解析 markdown 表格，提取 (path, title, scope, when_load) 四字段；
    4. 主路径 + legacy 均不存在 → 返回 []（agent fallback 到全量 rglob）。

    返回：list[dict]，每项含 {"path", "title", "scope", "when_load", "source"}（source ∈ "main" | "legacy"）。
    """
    # scope → 子目录映射
    scope_map = {
        "constraints": Path("constraints"),
        "experience-roles": Path("experience") / "roles",
        "experience-tool": Path("experience") / "tool",
        "experience-risk": Path("experience") / "risk",
        "experience-regression": Path("experience") / "regression",
        "experience-stage": Path("experience") / "stage",
    }
    if scope not in scope_map:
        return []
    sub = scope_map[scope]

    # 主路径优先（chg-01 OQ-A 主路径，无 branch）
    main_idx = root / "artifacts" / "project" / sub / "index.md"
    if main_idx.is_file():
        return _parse_index_md(main_idx, source="main")

    # legacy fallback（chg-01 双轨过渡）
    branch = _get_git_branch(root) or "main"
    legacy_idx = root / "artifacts" / branch / "project" / sub / "index.md"
    if legacy_idx.is_file():
        return _parse_index_md(legacy_idx, source="legacy")

    return []


def _parse_index_md(idx_path: Path, source: str) -> list[dict]:
    """解析 index.md markdown 表格，返回 list[dict]。仅取 (path, title, scope, when_load) 4 字段。"""
    try:
        text = idx_path.read_text(encoding="utf-8")
    except OSError:
        return []
    rows: list[dict] = []
    in_table = False
    for line in text.splitlines():
        s = line.strip()
        # 表头识别
        if s.startswith("| path") and "title" in s and "scope" in s:
            in_table = True
            continue
        if in_table and s.startswith("|---"):
            continue  # 分隔行
        if in_table:
            if not s.startswith("|"):
                in_table = False  # 表格结束
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 4:
                continue
            path_cell, title_cell, scope_cell, when_load_cell = cells[0], cells[1], cells[2], cells[3]
            # 跳过示例占位行（含 HTML 注释）
            if "<!--" in path_cell or not path_cell:
                continue
            rows.append({
                "path": path_cell,
                "title": title_cell,
                "scope": scope_cell,
                "when_load": when_load_cell,
                "source": source,
            })
    return rows
```

### 1.3 `.workflow/context/roles/role-loading-protocol.md` 新增 Step 7.6.1

**变更点 B：Step 7.6 段尾追加 Step 7.6.1 索引懒加载子段**：

```markdown
#### Step 7.6.1：索引懒加载（req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-03（索引懒加载-index-md与加载链改造））

> 溯源：req-52 OQ-B = A（YAML frontmatter + Markdown 表 schema）。

加载顺序：

1. **先调 helper**：`_load_project_level_index(root, scope)`（scope ∈ `{constraints, experience-roles, experience-tool, experience-risk, experience-regression, experience-stage}`），拿清单；
2. **按 `when_load` 过滤**：
   - `always` → 立即加载条目；
   - `on-stage:{stage}` → 当前 stage 匹配时才加载；
   - `on-keyword:{kw}` → 当前任务描述含 keyword 时才加载（agent 自判）；
3. **全量 rglob fallback**：当且仅当 `index.md` 不存在时，回退到 Step 7.6 既有 `_merge_project_level_files` 的全量 `rglob("*")` 行为（向后兼容存量项目）；
4. **路径优先级**：`_load_project_level_index` 内部已实现"主路径优先 + legacy fallback"（chg-01 双轨），agent 无需关心；命中 legacy 时 helper 在返回值中标 `source="legacy"`，agent 在首条输出追加 `（fallback=artifacts/{branch}/project/）` 提示。

**自检**（角色加载完成后）：

- 在首条输出（与硬门禁三自我介绍并列）追加一句："项目级索引懒加载：{命中文件数 / 0}（scope={scope}）"，便于用户感知是否生效。
```

### 1.4 scaffold_v2 mirror 同步

- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md`：完全镜像 1.3 变更点 B；
- 6 份 `artifacts/project/{...}/index.md` 模板**不**纳入 mirror（artifacts/ 子树，与 chg-01 同口径）。

### 1.5 新增 `tests/test_req52_lazy_index_loading.py`

```python
"""req-52 / chg-03：项目级索引懒加载测试。

用例：
- TC-01-index-parsing：解析 index.md markdown 表，返回 4 字段
- TC-02-when-load-filter：when_load 过滤行为（always / on-stage:executing / on-keyword:foo）
- TC-03-fallback-main-path：主路径不存在时 fallback 到 legacy artifacts/{branch}/project/
- TC-04-empty-when-no-index：主路径 + legacy 均无 index.md 时返回 []（向后兼容）
- TC-05-skip-placeholder-row：跳过含 HTML 注释的占位行
"""
import os
from pathlib import Path

import pytest

from harness_workflow.workflow_helpers import _load_project_level_index, _parse_index_md


def _write_index(target: Path, rows: list[dict]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "schema_version: 1",
        "scope: constraints",
        "---",
        "",
        "# 项目级 constraints 索引",
        "",
        "| path | title | scope | when_load | 备注 |",
        "|------|-------|-------|-----------|------|",
    ]
    for r in rows:
        lines.append(f"| {r['path']} | {r['title']} | {r['scope']} | {r['when_load']} | |")
    target.write_text("\n".join(lines), encoding="utf-8")


def test_index_parsing(tmp_path):
    """TC-01：解析 index.md 表格，返回 4 字段。"""
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    _write_index(idx, [
        {"path": "rule-a.md", "title": "项目独有规则 A", "scope": "constraints", "when_load": "always"},
        {"path": "rule-b.md", "title": "项目独有规则 B", "scope": "constraints", "when_load": "on-stage:executing"},
    ])
    rows = _load_project_level_index(tmp_path, "constraints")
    assert len(rows) == 2
    assert rows[0]["path"] == "rule-a.md"
    assert rows[0]["when_load"] == "always"
    assert rows[1]["when_load"] == "on-stage:executing"
    assert all(r["source"] == "main" for r in rows)


def test_when_load_filter(tmp_path):
    """TC-02：when_load 过滤行为（agent 调用方按 stage 自行 filter，本 helper 仅返回 list）。"""
    idx = tmp_path / "artifacts" / "project" / "experience" / "roles" / "index.md"
    _write_index(idx, [
        {"path": "x.md", "title": "x", "scope": "experience-roles", "when_load": "always"},
        {"path": "y.md", "title": "y", "scope": "experience-roles", "when_load": "on-stage:executing"},
        {"path": "z.md", "title": "z", "scope": "experience-roles", "when_load": "on-keyword:lint"},
    ])
    rows = _load_project_level_index(tmp_path, "experience-roles")
    assert len(rows) == 3
    when_loads = [r["when_load"] for r in rows]
    assert "always" in when_loads
    assert "on-stage:executing" in when_loads
    assert "on-keyword:lint" in when_loads


def test_fallback_main_to_legacy(tmp_path, monkeypatch):
    """TC-03：主路径不存在时 fallback 到 legacy artifacts/{branch}/project/。"""
    # 仅在 legacy 路径写 index.md
    legacy_idx = tmp_path / "artifacts" / "main" / "project" / "constraints" / "index.md"
    _write_index(legacy_idx, [
        {"path": "legacy-rule.md", "title": "legacy", "scope": "constraints", "when_load": "always"},
    ])
    # mock _get_git_branch -> "main"
    import harness_workflow.workflow_helpers as wh
    monkeypatch.setattr(wh, "_get_git_branch", lambda root: "main")
    rows = _load_project_level_index(tmp_path, "constraints")
    assert len(rows) == 1
    assert rows[0]["path"] == "legacy-rule.md"
    assert rows[0]["source"] == "legacy"


def test_empty_when_no_index(tmp_path, monkeypatch):
    """TC-04：主路径 + legacy 均无 index.md 时返回 []。"""
    import harness_workflow.workflow_helpers as wh
    monkeypatch.setattr(wh, "_get_git_branch", lambda root: "main")
    rows = _load_project_level_index(tmp_path, "constraints")
    assert rows == []


def test_skip_placeholder_row(tmp_path):
    """TC-05：跳过含 HTML 注释的占位行（与本 chg index.md 模板内置示例行匹配）。"""
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        "---\nscope: constraints\n---\n\n"
        "| path | title | scope | when_load | 备注 |\n"
        "|------|-------|-------|-----------|------|\n"
        "| <!-- 示例：my-rule.md --> | <!-- 示例 --> | constraints | always | |\n"
        "| real-rule.md | real | constraints | always | |\n",
        encoding="utf-8",
    )
    rows = _load_project_level_index(tmp_path, "constraints")
    assert len(rows) == 1
    assert rows[0]["path"] == "real-rule.md"
```

## 2. 实施步骤（顺序 + 命令）

### Step 1：创建 6 份 `index.md` 模板

```bash
# 用 Write 工具按 §1.1 内容落 6 份模板：
# - artifacts/project/constraints/index.md
# - artifacts/project/experience/{roles,tool,risk,regression,stage}/index.md
mkdir -p artifacts/project/experience/roles artifacts/project/experience/tool artifacts/project/experience/risk artifacts/project/experience/regression artifacts/project/experience/stage
# 然后用 Write 落 6 份 index.md
```

### Step 2：编辑 `workflow_helpers.py` 新增 helper

- 用 Edit 工具按 §1.2 在 `_merge_project_level_files` 后插入 `_load_project_level_index` + `_parse_index_md` 两个 helper；
- 自检：

```bash
grep -n "^def _load_project_level_index" src/harness_workflow/workflow_helpers.py   # 期望 1 命中
grep -n "^def _parse_index_md" src/harness_workflow/workflow_helpers.py   # 期望 1 命中
python3 -c "from harness_workflow.workflow_helpers import _load_project_level_index; print(_load_project_level_index.__doc__[:50])"
```

### Step 3：编辑 `role-loading-protocol.md` 新增 Step 7.6.1

- 用 Edit 工具按 §1.3 在 Step 7.6 段尾插入 Step 7.6.1 索引懒加载子段；
- 自检：

```bash
grep -n "Step 7.6.1：索引懒加载" .workflow/context/roles/role-loading-protocol.md   # 期望 1 命中
grep -n "_load_project_level_index" .workflow/context/roles/role-loading-protocol.md   # 期望 ≥ 1 命中
```

### Step 4：同 commit 编辑 scaffold_v2 mirror

- 镜像 Step 3 改动到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md`；
- 自检：

```bash
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md   # silent
```

### Step 5：新增 `tests/test_req52_lazy_index_loading.py`

```bash
pytest tests/test_req52_lazy_index_loading.py -v   # 期望 ≥ 5 用例 PASS
```

### Step 6：契约 + 5 份 req-51 tests 全绿

```bash
harness validate --human-docs           # exit 0
harness validate --contract all         # exit 0
pytest tests/test_req51_project_level_*.py -v   # 全 PASS（无回归）
```

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（破坏面收敛在 workflow_helpers.py 新增 helper + role-loading-protocol.md + 新建 6 份 index.md 模板 + 新增 1 份 test）
> 波及接口清单（git diff --name-only 预估）：
> - `src/harness_workflow/workflow_helpers.py`（新增 2 个 helper）
> - `.workflow/context/roles/role-loading-protocol.md`（新增 7.6.1 子段）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md`（mirror）
> - `tests/test_req52_lazy_index_loading.py`（新建）
> - `artifacts/project/{constraints,experience/*}/index.md`（6 份新建）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-index-parsing | `pytest tests/test_req52_lazy_index_loading.py::test_index_parsing` | PASS：返回 list[dict] 含 path / title / scope / when_load / source | AC-05 | P0 |
| TC-02-when-load-filter | `pytest tests/test_req52_lazy_index_loading.py::test_when_load_filter` | PASS：3 种 when_load 形态都被解析（always / on-stage / on-keyword） | AC-05 | P0 |
| TC-03-fallback-main-to-legacy | `pytest tests/test_req52_lazy_index_loading.py::test_fallback_main_to_legacy` | PASS：主路径不存在时 fallback 命中 legacy `artifacts/main/project/`，source="legacy" | AC-02 / AC-05 | P0 |
| TC-04-empty-when-no-index | `pytest tests/test_req52_lazy_index_loading.py::test_empty_when_no_index` | PASS：返回空 list（向后兼容存量项目） | AC-05 | P0 |
| TC-05-skip-placeholder-row | `pytest tests/test_req52_lazy_index_loading.py::test_skip_placeholder_row` | PASS：占位行（含 `<!--` 注释）被跳过 | AC-05 | P1 |
| TC-06-protocol-doc-section | grep `role-loading-protocol.md` 含 "Step 7.6.1：索引懒加载"段 | grep 命中 ≥ 1 | AC-05 | P0 |
| TC-07-mirror-sync | `diff -q` live vs scaffold_v2 mirror | silent | AC-08 | P0 |

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：索引懒加载单测全 PASS
pytest tests/test_req52_lazy_index_loading.py -v

# L2：helper 注册确认
grep -n "^def _load_project_level_index" src/harness_workflow/workflow_helpers.py
grep -n "^def _parse_index_md" src/harness_workflow/workflow_helpers.py
python3 -c "from harness_workflow.workflow_helpers import _load_project_level_index, _parse_index_md; print('OK')"

# L3：role-loading-protocol Step 7.6.1 段
grep -n "Step 7.6.1：索引懒加载" .workflow/context/roles/role-loading-protocol.md
grep -n "_load_project_level_index" .workflow/context/roles/role-loading-protocol.md

# L4：6 份 index.md 模板存在
test -f artifacts/project/constraints/index.md
test -f artifacts/project/experience/roles/index.md
test -f artifacts/project/experience/tool/index.md
test -f artifacts/project/experience/risk/index.md
test -f artifacts/project/experience/regression/index.md
test -f artifacts/project/experience/stage/index.md

# L5：scaffold mirror 同源
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md

# L6：契约自检 + 5 份 req-51 tests 无回归
harness validate --human-docs
harness validate --contract all
pytest tests/test_req51_project_level_protection.py tests/test_req51_project_level_loading.py tests/test_req51_project_level_dogfood.py -v
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

| live 文件 | mirror 文件 | 同步动作 |
|-----------|------------|---------|
| `.workflow/context/roles/role-loading-protocol.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md` | 同 commit 镜像变更点 B |

**注意**：
- `src/harness_workflow/workflow_helpers.py` 是 Python 源码，不进 mirror（同 chg-02 口径）；
- 6 份 `artifacts/project/{...}/index.md` 不进 mirror（artifacts/ 子树，同 chg-01 口径）；
- `tests/test_req52_lazy_index_loading.py` 不进 mirror。
