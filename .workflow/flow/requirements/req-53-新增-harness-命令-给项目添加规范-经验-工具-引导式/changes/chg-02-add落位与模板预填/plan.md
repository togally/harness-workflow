---
id: chg-02-plan
parent: chg-02（_pad_add 真实落位 + 三份 .tmpl 模板预填）
created_at: 2026-04-29
---

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 新增 3 份模板文件（落 src/ assets/）

新建目录 `src/harness_workflow/assets/templates/project-add/`，含 3 文件：

#### 1.1.1 `rule.md.tmpl`

```markdown
---
id: {{ slug }}
kind: rule
scope: {{ scope }}
title: {{ title }}
created_at: {{ created_at }}
when_load: always
---

# {{ title }}

## 内容

> 在此填写规则的具体条款（≤ 5 条要点，每条 1-2 句）。

## 适用范围

> 在此说明规则生效范围（哪些模块 / 哪些场景）。

## 例外

> 在此列已知例外（如有），无则写"无"。

## 来源

req / chg / human review，按场景填写。
```

#### 1.1.2 `experience.md.tmpl`

```markdown
---
id: {{ slug }}
kind: experience
scope: {{ scope }}
title: {{ title }}
created_at: {{ created_at }}
when_load: always
---

# {{ title }}

## 场景

> 描述什么情况下会遇到本经验。

## 经验内容

> 描述应该怎么做（do / don't 各列要点）。

## 来源

> req / bugfix / regression 编号 + 一句话事实。
```

#### 1.1.3 `tool.md.tmpl`

```markdown
---
tool_id: {{ slug }}
keywords: []
scope: tools
title: {{ title }}
created_at: {{ created_at }}
when_load: always
---

# {{ title }}

## 用途

> 一句话描述本工具解决的问题。

## 输入 / 输出

> 输入字段 + 输出字段 + 异常处理。

## 调用示例

```bash
# 在此填写最小调用示例
```

## 来源

> 项目内沉淀 / 外部引入，按场景填写。
```

### 1.2 `src/harness_workflow/workflow_helpers.py`

替换 chg-01 落地的 `_pad_add` stub 为真实实现：

```python
def _pad_add(root: Path, kind: str, scope: str, title: str) -> int:
    """req-53 / chg-02：把条目落到 artifacts/project/{kind}/{scope}/{slug}.md。

    - kind=rule → artifacts/project/constraints/{scope}/{slug}.md
    - kind=experience → artifacts/project/experience/{scope}/{slug}.md
    - kind=tool → artifacts/project/tools/{slug}.md
    - slug 由 title 经 _path_slug 转换
    - 渲染对应 .tmpl 模板（assets/templates/project-add/{kind}.md.tmpl）
    - 调 write_if_missing 写盘（幂等，不覆盖）
    """
    from datetime import date
    slug = _path_slug(title) or title  # _path_slug 退化到 title 本身（CN 场景保留中文）
    target = _resolve_pad_target(root, kind, scope, slug)
    if target is None:
        print(f"[harness pad] ABORT: 无法解析路径 kind={kind} scope={scope}", file=sys.stderr)
        return 2

    # 模板渲染
    tmpl_name = {"rule": "rule", "experience": "experience", "tool": "tool"}[kind]
    tmpl_path = PACKAGE_FS_ROOT / "assets" / "templates" / "project-add" / f"{tmpl_name}.md.tmpl"
    if not tmpl_path.exists():
        print(f"[harness pad] ABORT: 模板缺失 {tmpl_path}", file=sys.stderr)
        return 2
    content = tmpl_path.read_text(encoding="utf-8")
    content = content.replace("{{ slug }}", slug)
    content = content.replace("{{ scope }}", scope or "tools")  # tool kind 写 tools
    content = content.replace("{{ title }}", title)
    content = content.replace("{{ created_at }}", date.today().isoformat())

    # 写盘（幂等）
    created: list[str] = []
    skipped: list[str] = []
    write_if_missing(target, content, created, skipped)
    rel = target.relative_to(root).as_posix()
    if created:
        print(f"[harness pad] added {rel} ✓")
    else:
        print(f"[harness pad] {rel} 已存在，跳过", file=sys.stderr)
    return 0


def _resolve_pad_target(root: Path, kind: str, scope: str, slug: str) -> Path | None:
    """req-53 / chg-02：按 kind + scope + slug 算 artifacts/project/ 下的目标文件路径。

    - kind=rule → artifacts/project/constraints/{scope}/{slug}.md
    - kind=experience → artifacts/project/experience/{scope}/{slug}.md
    - kind=tool → artifacts/project/tools/{slug}.md
    """
    base = root / "artifacts" / "project"
    if kind == "rule":
        if not scope:
            return None
        return base / "constraints" / scope / f"{slug}.md"
    if kind == "experience":
        if not scope:
            return None
        return base / "experience" / scope / f"{slug}.md"
    if kind == "tool":
        return base / "tools" / f"{slug}.md"
    return None
```

### 1.3 `pyproject.toml`

更新 `[tool.setuptools.package-data]` 段加入 project-add 模板（必须，否则 wheel 不打包）：

```toml
"assets/templates/project-add/*.tmpl",
```

紧邻 `assets/templates/project-skeleton/**/*` 之后加入。

## 2. 实施步骤（顺序）

```
# Step 1：新建 3 份模板
$ mkdir -p src/harness_workflow/assets/templates/project-add
$ vim src/harness_workflow/assets/templates/project-add/rule.md.tmpl
$ vim src/harness_workflow/assets/templates/project-add/experience.md.tmpl
$ vim src/harness_workflow/assets/templates/project-add/tool.md.tmpl

# Step 2：替换 _pad_add stub + 加 _resolve_pad_target helper
$ vim src/harness_workflow/workflow_helpers.py

# Step 3：更新 pyproject.toml package-data
$ vim pyproject.toml

# Step 4：直跑验证（独立核查 — 硬门禁九）
$ rm -rf /tmp/req53-chg02-dogfood && mkdir -p /tmp/req53-chg02-dogfood
$ cd /tmp/req53-chg02-dogfood && git init && python3 -m harness_workflow.cli install
$ cd /tmp/req53-chg02-dogfood && python3 -m harness_workflow.cli pad rule coding "禁止-API-硬编码"
# 期望 stdout 含 `[harness pad] added artifacts/project/constraints/coding/...md ✓`
$ test -f /tmp/req53-chg02-dogfood/artifacts/project/constraints/coding/禁止-api-硬编码.md
$ grep -q "kind: rule" /tmp/req53-chg02-dogfood/artifacts/project/constraints/coding/禁止-api-硬编码.md
$ grep -q "scope: coding" /tmp/req53-chg02-dogfood/artifacts/project/constraints/coding/禁止-api-硬编码.md
$ grep -q "## 内容" /tmp/req53-chg02-dogfood/artifacts/project/constraints/coding/禁止-api-硬编码.md

# Step 5：幂等验证
$ cd /tmp/req53-chg02-dogfood && python3 -m harness_workflow.cli pad rule coding "禁止-API-硬编码"
# 期望 exit=0 + stderr 含 "已存在，跳过"

# Step 6：跑配套 pytest（chg-02 测试用例 ≥ 4 条）
$ pytest tests/test_req53_pad_add.py -v

# Step 7：契约 lint 自检
$ python3 -m harness_workflow.cli validate --contract artifact-placement
$ python3 -m harness_workflow.cli validate --contract user-write-protected-zones
$ python3 -m harness_workflow.cli validate --human-docs

# Step 8：mirror / package-data 自检
$ python3 -c "from harness_workflow.workflow_helpers import PACKAGE_FS_ROOT; \
  import os; \
  p = PACKAGE_FS_ROOT / 'assets' / 'templates' / 'project-add' / 'rule.md.tmpl'; \
  assert p.exists(), f'模板未打包：{p}'; \
  print('OK')"
$ pytest tests/test_package_data_completeness.py -v
```

## 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - `src/harness_workflow/workflow_helpers.py::_pad_add`（替换 stub）
> - `src/harness_workflow/workflow_helpers.py::_resolve_pad_target`（新增）
> - `src/harness_workflow/assets/templates/project-add/{rule,experience,tool}.md.tmpl`（3 新模板）
> - `pyproject.toml`（package-data 新增 1 行）

新增测试文件 `tests/test_req53_pad_add.py`，至少 6 条 TC：

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-add-rule-coding-落位 | tmpdir + harness install + `pad rule coding "禁止-API-硬编码"` | 文件存在于 `artifacts/project/constraints/coding/{slug}.md`，含 `kind: rule` + `scope: coding` + `## 内容` | AC-01 | P0 |
| TC-02-add-experience-stage-落位 | `pad experience stage "虚报教训"` | 文件存在 `artifacts/project/experience/stage/{slug}.md`，含 `kind: experience` + `scope: stage` | AC-01 | P0 |
| TC-03-add-tool-不分scope-落位 | `pad tool "petmall-deployer"` | 文件存在 `artifacts/project/tools/petmall-deployer.md`，含 `tool_id` + `scope: tools` | AC-01 | P0 |
| TC-04-add-frontmatter-字段完整 | TC-01 落地后读文件 | frontmatter 含 6 字段：id / kind / scope / title / created_at / when_load: always | AC-01 | P0 |
| TC-05-add-write_if_missing-幂等 | TC-01 后重跑同命令 | exit=0 + stderr 含 "已存在，跳过"，文件 mtime 不变 | G-04 | P0 |
| TC-06-add-illegal-kind-不落位 | `pad foo bar baz` | exit≠0 + 文件不创建（ABORT 在 chg-01 dispatch 层） | 反非法 lint | P1 |
| TC-07-add-tool-frontmatter-tool_id | TC-03 frontmatter | 含 `tool_id: petmall-deployer` + `keywords: []` | G-03 | P0 |
| TC-08-Dogfood-add-fresh-repo | tmpdir + git init + harness install + 跑 3 条 pad（rule/experience/tool）| 3 文件全部落位正确，install --check 不报错 | AC-07 | P0 |

实现走 `subprocess.run([sys.executable, "-m", "harness_workflow.cli", "install"], cwd=tmp)` + 第二个 subprocess 跑 `pad`，文件断言用 `Path(tmp / "artifacts" / "project" / ...).exists()`。

## 4. 验收 lint 命令字面（grep + pytest）

```bash
# 4.1 _pad_add 真实实现已落地（不再是 stub）
grep -nE "tmpl_path = PACKAGE_FS_ROOT" src/harness_workflow/workflow_helpers.py
grep -nE "def _resolve_pad_target" src/harness_workflow/workflow_helpers.py

# 4.2 三份模板存在
test -f src/harness_workflow/assets/templates/project-add/rule.md.tmpl
test -f src/harness_workflow/assets/templates/project-add/experience.md.tmpl
test -f src/harness_workflow/assets/templates/project-add/tool.md.tmpl

# 4.3 模板含必要字段占位
grep -q "{{ slug }}" src/harness_workflow/assets/templates/project-add/rule.md.tmpl
grep -q "kind: rule" src/harness_workflow/assets/templates/project-add/rule.md.tmpl
grep -q "when_load: always" src/harness_workflow/assets/templates/project-add/rule.md.tmpl

# 4.4 pyproject 已配 package-data
grep -q "assets/templates/project-add" pyproject.toml

# 4.5 配套 pytest 全绿
pytest tests/test_req53_pad_add.py -v
pytest tests/test_package_data_completeness.py -v

# 4.6 现有契约不回归
python3 -m harness_workflow.cli validate --contract artifact-placement
python3 -m harness_workflow.cli validate --contract user-write-protected-zones
python3 -m harness_workflow.cli validate --human-docs
```

## 5. scaffold_v2 mirror 同步清单

- 新增 3 份 `.tmpl` 文件落 `src/harness_workflow/assets/templates/project-add/`，**不在** scaffold_v2 mirror 范围（mirror 仅 `assets/scaffold_v2/.workflow/` 树）。
- `pyproject.toml` package-data 必须更新（1 行新增），属于 wheel 打包契约（与既有 `project-skeleton/**/*` 同型）；配套 `tests/test_package_data_completeness.py` 已有断言扫 `assets/templates/`，需让其覆盖新目录。
- 本 chg **不**触及 `assets/scaffold_v2/.workflow/` 任何文件。

## 6. 已知风险与缓解

- **风险 1：title 含中文 → `_path_slug` 走 `slugify_preserve_unicode` 保留中文**。需要确认 unicode 中文文件名在 macOS/Linux 路径表现一致。缓解：TC-01 用 ASCII 风格 title（"禁止-API-硬编码" 含中文 + 英文），断言路径存在性不依赖具体编码点。
- **风险 2：tool kind 时模板里 `{{ scope }}` 替换为 "tools"**（硬编码）；如果未来 tool 加 scope 维度需改 helper。缓解：注释说明，后续 v2 加 tool scope 时同步改。
- **风险 3：`_path_slug` 返回空字符串**（极端非法 title）。缓解：fallback `slug = _path_slug(title) or title`，让中文 title 仍能落位。
- **风险 4：constraints/{scope}/ 子目录是新建结构**，可能与现有 constraints/index.md（顶层表格）schema 冲突。缓解：本 chg 只创建子目录文件，不动 index.md（chg-03 处理 index 登记）。
