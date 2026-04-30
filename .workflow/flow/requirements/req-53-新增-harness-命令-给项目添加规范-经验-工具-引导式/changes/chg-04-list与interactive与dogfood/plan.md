---
id: chg-04-plan
parent: chg-04（_pad_list + _pad_interactive + dogfood + slash command 同步）
created_at: 2026-04-29
---

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `src/harness_workflow/workflow_helpers.py`

#### 1.1.1 替换 `_pad_list` stub 为真实实现

```python
def _pad_list(root: Path) -> int:
    """req-53 / chg-04：扫 artifacts/project/{constraints,experience/*,tools}/ 6 份 index.md，
    按 kind / scope 分组打印；空段显示 (无)。
    """
    base = root / "artifacts" / "project"
    print("=== Project-level Catalog (artifacts/project/) ===\n")

    # rule（constraints/index.md，path 含 {scope}/{slug}.md 子路径）
    print("[rule] (artifacts/project/constraints/)")
    rule_idx = base / "constraints" / "index.md"
    rule_rows = _parse_index_md(rule_idx, source="main") if rule_idx.is_file() else []
    if not rule_rows:
        print("  (无)")
    else:
        # 按 scope 分组
        from collections import defaultdict
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rule_rows:
            groups[r.get("scope", "?")].append(r)
        for scope_name in PAD_KINDS["rule"]:
            scope_rows = sorted(groups.get(scope_name, []), key=lambda r: r["path"])
            print(f"  {scope_name}:")
            if not scope_rows:
                print("    (无)")
            for r in scope_rows:
                print(f"    - {r['path']} — {r['title']}")
    print()

    # experience（5 子目录 index.md）
    print("[experience] (artifacts/project/experience/{scope}/)")
    for scope_name in PAD_KINDS["experience"]:
        idx = base / "experience" / scope_name / "index.md"
        rows = _parse_index_md(idx, source="main") if idx.is_file() else []
        rows = sorted(rows, key=lambda r: r["path"])
        print(f"  {scope_name}:")
        if not rows:
            print("    (无)")
        for r in rows:
            print(f"    - {r['path']} — {r['title']}")
    print()

    # tool（tools/index.md「## 项目级工具清单」段，schema 不同）
    print("[tool] (artifacts/project/tools/)")
    tool_idx = base / "tools" / "index.md"
    tool_items = _parse_tool_list_section(tool_idx) if tool_idx.is_file() else []
    if not tool_items:
        print("  (无)")
    for line in sorted(tool_items):
        print(f"  - {line}")
    return 0


def _parse_tool_list_section(idx_path: Path) -> list[str]:
    """req-53 / chg-04：解析 tools/index.md「## 项目级工具清单」段下的 markdown 列表项。
    返回去掉前缀 `- ` 后的字符串列表。
    """
    if not idx_path.is_file():
        return []
    text = idx_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    section_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "## 项目级工具清单":
            section_idx = i
            break
    if section_idx < 0:
        return []
    items: list[str] = []
    for j in range(section_idx + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("## "):
            break  # 段结束
        if s.startswith("- "):
            items.append(s[2:])
    return items
```

#### 1.1.2 替换 `_pad_interactive` stub 为真实实现

```python
def _pad_interactive(root: Path) -> int:
    """req-53 / chg-04：questionary 三步引导（kind → scope → title），完成后调 _pad_add。

    非 TTY 环境直接报错（与 prompt_platform_selection 同款 isatty 守卫）。
    """
    if not sys.stdin.isatty():
        print(
            "[harness pad] ABORT: interactive 模式需要交互式终端；非 TTY 环境请用位置参数。",
            file=sys.stderr,
        )
        return 2
    import questionary

    # 步骤 1：选 kind
    kind = questionary.select(
        "选择类型（kind）:",
        choices=list(PAD_KINDS.keys()),  # ["rule", "experience", "tool"]
        default="rule",
    ).ask()
    if not kind:
        print("[harness pad] cancelled")
        return 1

    # 步骤 2：选 scope（仅 kind=rule/experience 时）
    scope = ""
    if PAD_KINDS[kind]:  # 非空 list 表示需要 scope
        scope = questionary.select(
            f"选择 {kind} 的 scope:",
            choices=PAD_KINDS[kind],
        ).ask()
        if not scope:
            print("[harness pad] cancelled")
            return 1

    # 步骤 3：输 title
    title = questionary.text(
        f"{kind}{('/' + scope) if scope else ''} 的标题（≤ 20 字）:",
        validate=lambda v: bool(v.strip()) or "title 不能为空",
    ).ask()
    if not title:
        print("[harness pad] cancelled")
        return 1

    # 调真实 _pad_add
    return _pad_add(root, kind, scope, title.strip())
```

### 1.2 新增 slash command `.claude/commands/harness-pad.md`

```markdown
---
description: Run harness pad and continue work inside the current Harness workflow state
argument-hint: "<kind> [<scope>] <title> | list"
---

This command maps to `harness pad`.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.
If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

Before acting:

1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md`
3. Then read `.workflow/state/runtime.yaml`
4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`
5. Prefer the root `AGENTS.md`
6. If `.kimi/skills/harness/SKILL.md`, `.qoder/skills/harness/SKILL.md` or `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill

Execution rules:

- center the task around `harness pad`
- kind ∈ {rule, experience, tool}; rule scope ∈ {coding, architecture, api, database, security};
  experience scope ∈ {roles, stage, regression, risk, tool}; tool 不分 scope
- 无参数裸跑进入 questionary 引导（kind → scope → title 三步）
- `harness pad list` 列出 artifacts/project/ 下已登记条目（按 kind / scope 分组）
- 落位后会自动 `git add` 内容文件 + 对应 index.md，stdout 提示 `git commit -m "feat: 项目级 ..."` 由 user 决定 commit 时机
- 命令不写代码 / 不跑测试 / 不替换 install / update / next 主流程

If the user adds more instruction, combine it with the current workflow state to decide the next step.
```

### 1.3 README 增补一段

`README.md` 末尾追加：

```markdown
## harness pad — 项目级承载层维护

往 `artifacts/project/` 加规则 / 经验 / 工具，命令封装"路径正确 + index 登记 + git stage"全套：

```bash
# 加规则（5 个 scope：coding / architecture / api / database / security）
harness pad rule coding "禁止-API-硬编码"

# 加经验（5 个 scope：roles / stage / regression / risk / tool）
harness pad experience stage "executing-虚报教训"

# 加工具（不分 scope）
harness pad tool "petmall-deployer"

# 列已有
harness pad list

# 无参数 → 交互引导
harness pad
```

落位规则（固定枚举，user 不能发明）：

| kind | 路径 |
|------|------|
| rule | `artifacts/project/constraints/{scope}/{slug}.md` |
| experience | `artifacts/project/experience/{scope}/{slug}.md` |
| tool | `artifacts/project/tools/{slug}.md` |

命令成功后会自动 `git add`；user 仅需 `git commit -m "..."`（按 stdout 提示）。
```

### 1.4 `README.zh.md` 同款中文段同步

与 `README.md` 同款，中文版本补一段。

## 2. 实施步骤（顺序）

```
# Step 1：替换 _pad_list stub 为真实实现 + 加 _parse_tool_list_section helper
$ vim src/harness_workflow/workflow_helpers.py

# Step 2：替换 _pad_interactive stub 为真实 questionary 引导
$ vim src/harness_workflow/workflow_helpers.py

# Step 3：新增 slash command（cc 平台）
$ vim .claude/commands/harness-pad.md

# Step 4：README 增补
$ vim README.md
$ vim README.zh.md

# Step 5：直跑验证（独立核查 — 硬门禁九）
$ rm -rf /tmp/req53-chg04-dogfood && mkdir -p /tmp/req53-chg04-dogfood
$ cd /tmp/req53-chg04-dogfood && git init && python3 -m harness_workflow.cli install
$ cd /tmp/req53-chg04-dogfood && python3 -m harness_workflow.cli pad rule coding "禁止-API"
$ cd /tmp/req53-chg04-dogfood && python3 -m harness_workflow.cli pad rule security "JWT-RS256"
$ cd /tmp/req53-chg04-dogfood && python3 -m harness_workflow.cli pad experience stage "教训-A"
$ cd /tmp/req53-chg04-dogfood && python3 -m harness_workflow.cli pad experience tool "apifox"
$ cd /tmp/req53-chg04-dogfood && python3 -m harness_workflow.cli pad tool "deployer"
$ cd /tmp/req53-chg04-dogfood && python3 -m harness_workflow.cli pad list 2>&1 | tee /tmp/list.log
# 期望 list.log 含三段（rule / experience / tool），rule 段下 coding + security 两 scope 各 1 项，
# experience 段下 stage + tool 两 scope 各 1 项，tool 段 1 项，其他 scope 段显示 (无)

# Step 6：interactive 非 TTY 守卫验证
$ echo "" | python3 -m harness_workflow.cli pad 2>&1
# 期望 stderr 含 "interactive 模式需要交互式终端"

# Step 7：跑配套 pytest（chg-04 测试用例 ≥ 6 条）
$ pytest tests/test_req53_pad_list.py -v
$ pytest tests/test_req53_pad_interactive.py -v
$ pytest tests/test_req53_pad_dogfood.py -v

# Step 8：契约 lint 不回归
$ python3 -m harness_workflow.cli validate --contract artifact-placement
$ python3 -m harness_workflow.cli validate --contract user-write-protected-zones
$ python3 -m harness_workflow.cli validate --human-docs

# Step 9：grep 自检 slash command + README
$ test -f .claude/commands/harness-pad.md
$ grep -q "argument-hint" .claude/commands/harness-pad.md
$ grep -q "harness pad" README.md
$ grep -q "harness pad" README.zh.md

# Step 10：4 chg 全完成后 mirror / package-data 全量验证
$ pytest tests/test_package_data_completeness.py -v
$ pytest tests/test_req53_pad_cli.py tests/test_req53_pad_add.py tests/test_req53_pad_index.py tests/test_req53_pad_list.py tests/test_req53_pad_interactive.py tests/test_req53_pad_dogfood.py -v
```

## 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - `src/harness_workflow/workflow_helpers.py::_pad_list`（替换 stub）
> - `src/harness_workflow/workflow_helpers.py::_pad_interactive`（替换 stub）
> - `src/harness_workflow/workflow_helpers.py::_parse_tool_list_section`（新增）
> - `.claude/commands/harness-pad.md`（新增）
> - `README.md` / `README.zh.md`（增补段）

新增 3 份测试文件，TC 总数 ≥ 12：

### 3.1 `tests/test_req53_pad_list.py`（4 条）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-list-空仓三段全无 | tmpdir + install + 立即 list | 三段 `[rule]` `[experience]` `[tool]`，每段含 `(无)` | AC-06 | P0 |
| TC-02-list-rule-按scope分组 | tmpdir + install + pad rule coding × 1 + pad rule security × 1 + list | output 含 `coding:` 段下 1 项 + `security:` 段下 1 项 + 其他 3 个 rule scope 显示 `(无)` | AC-06 | P0 |
| TC-03-list-experience-五子分类 | tmpdir + install + pad experience stage × 1 + pad experience tool × 1 + list | output 含 `stage:` + `tool:` 各 1 项 + 其他 3 个 experience scope `(无)` | AC-06 | P0 |
| TC-04-list-tool-列表段解析 | tmpdir + install + pad tool × 2 + list | output 含 `[tool]` 段下两条 `- {slug}.md — {title}` | AC-06 | P0 |

### 3.2 `tests/test_req53_pad_interactive.py`（3 条）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-interactive-非TTY-abort | 非 TTY subprocess 跑裸 `pad`（stdin closed） | exit≠0 + stderr 含 "interactive 模式需要交互式终端" | G-03 | P0 |
| TC-02-interactive-questionary-mock | monkeypatch `questionary.select` / `questionary.text` 模拟用户回答 → 调 `_pad_interactive(root)` | 返回 0 + 文件落位与对应位置参数版本一致 | AC-08 | P0 |
| TC-03-interactive-cancel | monkeypatch `questionary.select` 返回 None（user Ctrl-C） | exit=1 + stdout 含 "cancelled" | G-02 | P1 |

### 3.3 `tests/test_req53_pad_dogfood.py`（5 条 P0 dogfood TC）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-Dogfood-01-fresh-install-then-pad | tmpdir + git init + install（subprocess）+ pad rule coding（subprocess）| 文件落位 + index 登记 + git diff --cached 含 2 条 + stderr 含 `[harness] project-level loaded` | AC-07 | P0 |
| TC-Dogfood-02-多次pad-同scope-多条 | tmpdir + install + pad rule coding × 3（不同 title）| index.md 含 3 行 coding scope row（grep -c = 3）+ 文件 3 个 | AC-07 | P0 |
| TC-Dogfood-03-混合-rule-experience-tool | tmpdir + install + pad rule × 2 + pad experience × 2 + pad tool × 1（共 5 条）| 5 个文件 + 4 份 index.md 各被改（rule 1 + experience 2 + tools 1 = 4）+ git diff --cached 含 5 + 4 = 9 条（去重后） | AC-07 / AC-10 模拟 | P0 |
| TC-Dogfood-04-pad后install-不覆盖 | tmpdir + install + pad rule + install --force-managed + grep index.md | index.md 行仍存在 + 内容文件仍存在 | AC-04 | P0 |
| TC-Dogfood-05-feedback-jsonl-事件 | tmpdir + install + pad（subprocess）+ 检查 `.workflow/state/feedback.jsonl` | （若 _pad_add 调 record_feedback_event）含 `harness_pad_added` 事件；若不调，本 TC 改为只断言 install 后 feedback.jsonl 不被破坏 | sug-52 dogfood 必填 | P1 |

> 注：TC-Dogfood-05 是 sug-52（dogfood 实跑流程模板）落地项，若 `_pad_add` 不调 `record_feedback_event`（chg-02/03 实现选择），可降级为 "feedback.jsonl 文件存在性检查"，不强求事件登记（避免引入 telemetry 范围溢出）。

实现要点：dogfood TC 走 `subprocess.run([sys.executable, "-m", "harness_workflow.cli", ...], cwd=str(tmpdir), capture_output=True, text=True)`，**禁止**直接调内部函数（违反 dogfood 端到端原则）。

## 4. 验收 lint 命令字面（grep + pytest）

```bash
# 4.1 _pad_list / _pad_interactive 真实实现已落地
grep -nE "PAD_KINDS\[\"rule\"\]" src/harness_workflow/workflow_helpers.py  # _pad_list 中分组逻辑
grep -nE "questionary\.select" src/harness_workflow/workflow_helpers.py    # _pad_interactive 中
grep -nE "def _parse_tool_list_section" src/harness_workflow/workflow_helpers.py

# 4.2 slash command 落地
test -f .claude/commands/harness-pad.md
grep -q "harness pad" .claude/commands/harness-pad.md
grep -q "argument-hint" .claude/commands/harness-pad.md

# 4.3 README 增补
grep -q "^## harness pad" README.md
grep -q "^## harness pad" README.zh.md

# 4.4 pytest 全量绿
pytest tests/test_req53_pad_cli.py -v
pytest tests/test_req53_pad_add.py -v
pytest tests/test_req53_pad_index.py -v
pytest tests/test_req53_pad_list.py -v
pytest tests/test_req53_pad_interactive.py -v
pytest tests/test_req53_pad_dogfood.py -v

# 4.5 现有契约不回归
python3 -m harness_workflow.cli validate --contract artifact-placement
python3 -m harness_workflow.cli validate --contract user-write-protected-zones
python3 -m harness_workflow.cli validate --human-docs
python3 -m harness_workflow.cli validate --contract all  # 总闸

# 4.6 端到端 dogfood（命令链 + 文件断言 + git 状态断言）
pytest tests/test_req53_pad_dogfood.py -v --tb=long
```

## 5. scaffold_v2 mirror 同步清单

- `cli.py` / `workflow_helpers.py`：**不在** mirror 范围。
- `.claude/commands/harness-pad.md`：**不在** scaffold_v2 mirror 范围（commands/ 由 `install_local_skills` 渲染分发，不走 scaffold_v2 拷贝）；但需在 `render_agent_command` / `_get_agent_commands_dir` 等链路验证模板被识别（grep 现有 `harness-suggest.md` 处理逻辑，确认 pad 同款分发不需新代码）。
  - **注**：若 `install_local_skills` 走目录全量拷贝，则 `.claude/commands/harness-pad.md` 自动被分发；若走显式列表，需在列表中加 1 行 `"harness-pad"`。chg-04 实施时需先 grep `install_local_skills` 实现确认。
- README.md / README.zh.md：**不在** scaffold_v2 mirror 范围（位于 repo 根，非 scaffold_v2 内）。
- 不动 `assets/scaffold_v2/.workflow/` 任何文件。
- 不动 contract docs（repository-layout.md / role-loading-protocol.md / tools-manager.md），现有路径表 + 加载链兼容新 path schema（`{scope}/{slug}.md` 子路径）已在 chg-03 验证。

## 6. 已知风险与缓解

- **风险 1：questionary.text 的 validate 参数 API 在不同 questionary 版本可能不一致**。缓解：现有仓库 `pyproject.toml` 已锁 `questionary>=2.0.0`，2.x 系列 `validate` 参数稳定（与 `prompt_platform_selection` / `prompt_agent_selection` 同款 API）。
- **风险 2：interactive 测试用 monkeypatch 模拟 questionary 返回值**。缓解：用 `monkeypatch.setattr("questionary.select", lambda **kw: types.SimpleNamespace(ask=lambda: "rule"))`，已在仓库其他测试中有先例（grep `monkeypatch.*questionary` 找参考）。
- **风险 3：`install_local_skills` 不识别新 slash command**。缓解：实施时先 grep 既有 `harness-suggest` 在 `install_local_skills` / `_project_skill_targets` / `render_agent_command` 中如何被处理；如果是基于目录全量拷贝则零工作量，如果是显式 list 则加 1 行。
- **风险 4：`_pad_list` 在 constraints/index.md 中找不到 scope 字段（旧 schema 可能 path 不带 `/`）** —— 此情况发生在 chg-03 之前手工创建的旧数据。缓解：fallback `groups[r.get("scope", "?")].append(r)`，未识别 scope 显示在 `?` 段（`_pad_list` 不再循环 PAD_KINDS["rule"]，而应额外打印 unknown 段）。**default-pick = A**：当前实现仅打印 PAD_KINDS["rule"] 5 段，旧数据 unknown scope 静默丢弃；后续 sug 处理 backfill。
- **风险 5：dogfood TC 跨 subprocess 影响 stderr 编码**。缓解：`subprocess.run(..., text=True, encoding="utf-8")` + 子串断言不依赖具体字节序。
