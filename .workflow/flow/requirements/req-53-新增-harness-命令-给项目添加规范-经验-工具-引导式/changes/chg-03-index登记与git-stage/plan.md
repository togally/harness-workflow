---
id: chg-03-plan
parent: chg-03（index.md 自动登记 + git auto-stage + 加载链活证）
created_at: 2026-04-29
---

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `src/harness_workflow/workflow_helpers.py`

#### 1.1.1 新增 helper `_pad_register_index`

文件末尾追加：

```python
def _pad_register_index(root: Path, kind: str, scope: str, slug: str, title: str) -> Path | None:
    """req-53 / chg-03：往对应 index.md 追加新条目，按 kind schema 分类。

    - kind=rule → artifacts/project/constraints/index.md 表格末追加
                  `| {scope}/{slug}.md | {title} | {scope} | always | (空) |`
    - kind=experience → artifacts/project/experience/{scope}/index.md 表格末追加
                  `| {slug}.md | {title} | experience-{scope} | always | (空) |`
    - kind=tool → artifacts/project/tools/index.md「## 项目级工具清单」段末追加 `- {slug}.md — {title}`

    返回：被修改的 index.md 路径（用于 git add）；解析失败返回 None。
    """
    base = root / "artifacts" / "project"
    if kind == "rule":
        idx = base / "constraints" / "index.md"
        new_row = f"| {scope}/{slug}.md | {title} | {scope} | always | (空) |"
        return _append_table_row(idx, new_row)
    if kind == "experience":
        idx = base / "experience" / scope / "index.md"
        new_row = f"| {slug}.md | {title} | experience-{scope} | always | (空) |"
        return _append_table_row(idx, new_row)
    if kind == "tool":
        idx = base / "tools" / "index.md"
        new_line = f"- {slug}.md — {title}"
        return _append_tool_list_item(idx, new_line)
    return None


def _append_table_row(idx_path: Path, new_row: str) -> Path | None:
    """往 markdown 表格 index.md 末尾追加一行；若表头不存在自动补齐。

    幂等：如果 new_row 已存在则不再追加。
    """
    if not idx_path.parent.exists():
        idx_path.parent.mkdir(parents=True, exist_ok=True)
    if not idx_path.exists():
        # 创建带表头的 index.md
        idx_path.write_text(
            f"| path | title | scope | when_load | 备注 |\n"
            f"|------|-------|-------|-----------|------|\n"
            f"{new_row}\n",
            encoding="utf-8",
        )
        return idx_path
    text = idx_path.read_text(encoding="utf-8")
    # 幂等：若 new_row 已存在 skip
    if new_row.strip() in text:
        return idx_path
    lines = text.splitlines()
    # 找表头位置
    header_idx = -1
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("| path") and "title" in s and "scope" in s:
            header_idx = i
            break
    if header_idx == -1:
        # 表头缺失 → 在文件末尾补全表
        lines.append("")
        lines.append("| path | title | scope | when_load | 备注 |")
        lines.append("|------|-------|-------|-----------|------|")
        lines.append(new_row)
    else:
        # 找表格末尾（第一个不以 | 开头的行）
        end_idx = len(lines)
        for j in range(header_idx + 2, len(lines)):  # +2 跳过表头 + 分隔行
            if not lines[j].strip().startswith("|"):
                end_idx = j
                break
        lines.insert(end_idx, new_row)
    idx_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return idx_path


def _append_tool_list_item(idx_path: Path, new_line: str) -> Path | None:
    """往 tools/index.md「## 项目级工具清单」段末追加列表项；段不存在则创建。

    幂等：如果 new_line 已存在则不再追加。
    """
    if not idx_path.parent.exists():
        idx_path.parent.mkdir(parents=True, exist_ok=True)
    if not idx_path.exists():
        idx_path.write_text(
            f"# Project-level Tools Index\n\n## 项目级工具清单\n\n{new_line}\n",
            encoding="utf-8",
        )
        return idx_path
    text = idx_path.read_text(encoding="utf-8")
    if new_line.strip() in text:
        return idx_path
    if "## 项目级工具清单" not in text:
        # 段不存在 → 文件末尾追加段
        if not text.endswith("\n"):
            text += "\n"
        text += f"\n## 项目级工具清单\n\n{new_line}\n"
    else:
        lines = text.splitlines()
        section_idx = -1
        for i, line in enumerate(lines):
            if line.strip() == "## 项目级工具清单":
                section_idx = i
                break
        # 找段末尾（下一个 ## 标题或文件末尾）
        end_idx = len(lines)
        for j in range(section_idx + 1, len(lines)):
            if lines[j].startswith("## "):
                end_idx = j
                break
        # 段尾插入新列表项（保持空行格式）
        # 简化：在 end_idx 前插入
        lines.insert(end_idx, new_line)
        text = "\n".join(lines) + "\n"
    idx_path.write_text(text, encoding="utf-8")
    return idx_path


def _pad_git_stage(root: Path, paths: list[Path]) -> bool:
    """req-53 / chg-03：调 git add 把指定路径加入 stage。

    返回：True = 全部成功；False = 任一失败 / 非 git 仓 / git 缺失。
    失败时 stderr 警告但不抛异常（OQ-5 决策：silent skip 不阻塞）。
    """
    import subprocess
    if not (root / ".git").exists():
        print("[harness pad] (info) 非 git 仓，跳过 git add", file=sys.stderr)
        return False
    try:
        for p in paths:
            rel = p.relative_to(root).as_posix()
            result = subprocess.run(
                ["git", "add", rel],
                cwd=str(root),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(
                    f"[harness pad] (warn) git add {rel} failed: {result.stderr.strip()}",
                    file=sys.stderr,
                )
                return False
        return True
    except FileNotFoundError:
        print("[harness pad] (warn) git 命令缺失，跳过 git add", file=sys.stderr)
        return False
```

#### 1.1.2 增强 `_pad_add`（在 chg-02 实现基础上追加 3 块）

在 chg-02 的 `_pad_add` 实现末尾，**写盘成功后**追加：

```python
    # —— chg-03 新增 ——
    # 1) index.md 自动登记
    idx_path = _pad_register_index(root, kind, scope, slug, title)

    # 2) git auto-stage（OQ-5 决策）
    paths_to_stage = [target]
    if idx_path:
        paths_to_stage.append(idx_path)
    git_ok = _pad_git_stage(root, paths_to_stage)

    # 3) 加载链 stderr 活证（复用 _log_project_level_load）
    scope_for_log = {
        "rule": "constraints",
        "experience": "experience",
        "tool": "tools",
    }[kind]
    # 计当前 scope 目录下文件数（不含 index.md 自身的"行数"，这里复用 install 同款 hits=count files）
    scope_dir_map = {
        "rule": root / "artifacts" / "project" / "constraints",
        "experience": root / "artifacts" / "project" / "experience" / scope,
        "tool": root / "artifacts" / "project" / "tools",
    }
    scope_dir = scope_dir_map[kind]
    hits = sum(1 for f in scope_dir.rglob("*") if f.is_file()) if scope_dir.exists() else 0
    _log_project_level_load(root, scope_for_log, hits, fallback_used=False)

    # 4) stdout 末尾提示 commit
    if git_ok:
        print(f"✓ git staged. 提示 git commit -m \"feat: 项目级 {kind}-{title}\"")
    else:
        print(f"提示 git add + git commit -m \"feat: 项目级 {kind}-{title}\"")
    return 0
```

注：`_log_project_level_load` 的 scope 参数当前接受 `{constraints, experience, tools}`（不含 experience 子分类），保持现有签名兼容。experience 5 子分类对应同一 stderr 标签（`from artifacts/project/experience/`）符合 install 同款语义。

## 2. 实施步骤（顺序）

```
# Step 1：新增 4 个 helper（_pad_register_index / _append_table_row / _append_tool_list_item / _pad_git_stage）
$ vim src/harness_workflow/workflow_helpers.py

# Step 2：在 _pad_add 末尾追加 3 块（index 登记 + git stage + stderr 活证）
$ vim src/harness_workflow/workflow_helpers.py

# Step 3：直跑验证（独立核查 — 硬门禁九）
$ rm -rf /tmp/req53-chg03-dogfood && mkdir -p /tmp/req53-chg03-dogfood
$ cd /tmp/req53-chg03-dogfood && git init && python3 -m harness_workflow.cli install
$ cd /tmp/req53-chg03-dogfood && python3 -m harness_workflow.cli pad rule coding "禁止-API-硬编码" 2>&1 | tee /tmp/pad-out.log
# 期望:
#   stdout 含 "[harness pad] added artifacts/project/constraints/coding/...md ✓"
#   stdout 含 "✓ git staged. 提示 git commit -m"
#   stderr 含 "[harness] project-level loaded: N files from artifacts/project/constraints/"
$ grep -q "coding/禁止-api-硬编码.md" /tmp/req53-chg03-dogfood/artifacts/project/constraints/index.md
$ cd /tmp/req53-chg03-dogfood && git diff --cached --name-only
# 期望含 artifacts/project/constraints/coding/禁止-api-硬编码.md + artifacts/project/constraints/index.md

# Step 4：experience 验证
$ cd /tmp/req53-chg03-dogfood && python3 -m harness_workflow.cli pad experience stage "executing-虚报教训"
$ grep -q "executing-虚报教训.md" /tmp/req53-chg03-dogfood/artifacts/project/experience/stage/index.md

# Step 5：tool 验证（不同 schema）
$ cd /tmp/req53-chg03-dogfood && python3 -m harness_workflow.cli pad tool "petmall-deployer"
$ grep -q "petmall-deployer.md" /tmp/req53-chg03-dogfood/artifacts/project/tools/index.md
$ grep -q "## 项目级工具清单" /tmp/req53-chg03-dogfood/artifacts/project/tools/index.md

# Step 6：非 git 仓 silent skip 验证
$ rm -rf /tmp/req53-chg03-nogit && mkdir -p /tmp/req53-chg03-nogit
$ cd /tmp/req53-chg03-nogit && python3 -m harness_workflow.cli install  # install 内部不依赖 git
$ rm -rf /tmp/req53-chg03-nogit/.git  # 移除 git
$ cd /tmp/req53-chg03-nogit && python3 -m harness_workflow.cli pad rule coding "测试" 2>&1 | grep -q "非 git 仓，跳过 git add"

# Step 7：幂等验证
$ cd /tmp/req53-chg03-dogfood && python3 -m harness_workflow.cli pad rule coding "禁止-API-硬编码"
$ grep -c "coding/禁止-api-硬编码.md" /tmp/req53-chg03-dogfood/artifacts/project/constraints/index.md
# 期望 = 1（不重复登记）

# Step 8：跑配套 pytest（chg-03 测试用例 ≥ 5 条）
$ pytest tests/test_req53_pad_index.py -v

# Step 9：契约 lint 不回归
$ python3 -m harness_workflow.cli validate --contract artifact-placement
$ python3 -m harness_workflow.cli validate --contract user-write-protected-zones
$ python3 -m harness_workflow.cli validate --human-docs

# Step 10：mirror / install 不覆盖验证（AC-04）
$ cd /tmp/req53-chg03-dogfood && python3 -m harness_workflow.cli install --force-managed
$ test -f /tmp/req53-chg03-dogfood/artifacts/project/constraints/coding/禁止-api-硬编码.md
$ grep -q "coding/禁止-api-硬编码.md" /tmp/req53-chg03-dogfood/artifacts/project/constraints/index.md
```

## 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - `src/harness_workflow/workflow_helpers.py::_pad_register_index`（新增）
> - `src/harness_workflow/workflow_helpers.py::_append_table_row`（新增）
> - `src/harness_workflow/workflow_helpers.py::_append_tool_list_item`（新增）
> - `src/harness_workflow/workflow_helpers.py::_pad_git_stage`（新增）
> - `src/harness_workflow/workflow_helpers.py::_pad_add`（在 chg-02 基础上增强）

新增测试文件 `tests/test_req53_pad_index.py`，至少 7 条 TC：

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-index-rule-表格追加 | tmpdir + install + `pad rule coding "代码风格"` | constraints/index.md 含行 `| coding/{slug}.md | 代码风格 | coding | always |` | AC-02 | P0 |
| TC-02-index-experience-子目录追加 | `pad experience stage "虚报"` | experience/stage/index.md 含行 `| {slug}.md | 虚报 | experience-stage | always |` | AC-02 | P0 |
| TC-03-index-tool-列表追加 | `pad tool "deployer"` | tools/index.md「## 项目级工具清单」段含 `- deployer.md — deployer` | AC-02 | P0 |
| TC-04-stderr-活证 | TC-01 后 `result.stderr` | 含 `[harness] project-level loaded: \d+ files from artifacts/project/constraints/（fallback=n/a）` | AC-03 | P0 |
| TC-05-stdout-git-commit-提示 | TC-01 后 `result.stdout` | 含 `✓ git staged. 提示 git commit -m "feat: 项目级 rule-代码风格"` | AC-09 | P0 |
| TC-06-git-add-staged | TC-01 后 `git diff --cached --name-only` | 含两条 path：内容文件 + index.md | AC-09 | P0 |
| TC-07-非git仓-silent-skip | tmpdir 无 .git + 跑 pad | exit=0 + stderr 含 "非 git 仓，跳过 git add" + 文件正常落位 | G-06 | P0 |
| TC-08-幂等-不重复登记 | TC-01 后重跑同命令 | index.md 中目标行计数 = 1（grep -c）+ exit=0 | G-04 | P0 |
| TC-09-表头缺失-自动补 | tmpdir + 手动写入空 index.md（无表头）+ pad rule | index.md 自动补齐表头 + 新行追加 | G-07 | P1 |
| TC-10-install-不覆盖-AC04 | TC-01 后跑 `install --force-managed` | constraints/coding/{slug}.md 仍存在 + index.md 行仍在 | AC-04 | P0 |

实现 fixture：`tmp_path` + `subprocess.run` 跑 install → pad → 文件断言 + 子进程 stderr/stdout 抓取。

## 4. 验收 lint 命令字面（grep + pytest）

```bash
# 4.1 4 个新 helper 全部签名落地
grep -nE "^def (_pad_register_index|_append_table_row|_append_tool_list_item|_pad_git_stage)\b" src/harness_workflow/workflow_helpers.py

# 4.2 _pad_add 中已接入 3 块（不再是 chg-02 stub-of-write-only）
grep -n "_pad_register_index" src/harness_workflow/workflow_helpers.py
grep -n "_pad_git_stage" src/harness_workflow/workflow_helpers.py
grep -nE "_log_project_level_load.*scope_for_log" src/harness_workflow/workflow_helpers.py

# 4.3 配套 pytest 全绿
pytest tests/test_req53_pad_index.py -v

# 4.4 现有契约不回归
python3 -m harness_workflow.cli validate --contract artifact-placement
python3 -m harness_workflow.cli validate --contract user-write-protected-zones
python3 -m harness_workflow.cli validate --human-docs

# 4.5 mirror / install 不覆盖验证（AC-04）
# 已在 Step 10 dogfood 中落地，pytest TC-10 覆盖
```

## 5. scaffold_v2 mirror 同步清单

- 仅触及 `src/harness_workflow/workflow_helpers.py`，**不在** scaffold_v2 mirror 范围。
- **重要 contract docs 同步（在 mirror 范围内）**：
  - 【可选 / 推迟】`assets/scaffold_v2/.workflow/flow/repository-layout.md` 中如有 `artifacts/project/` 路径表，本 chg 不动（结构未变）。
  - 【必做】`assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md` Step 7.6 已写到 index.md schema，本 chg 不破坏（path 字段允许相对路径含 `/` 子目录）—— 仅需在 chg-04 总收时 grep 确认未漏改。
  - 【**新增**】constraints/index.md 模板（`src/harness_workflow/assets/templates/project-skeleton/constraints/index.md`）schema 说明文字应说明 path 可含子目录（如 `coding/my-rule.md`）。本 chg 加 1 行说明，避免 user 困惑。

## 6. 已知风险与缓解

- **风险 1：`_log_project_level_load` scope 参数当前签名只识别 3 个值**（constraints / experience / tools）。本 chg 用 `experience` 标签覆盖 5 子分类，stderr 输出 `from artifacts/project/experience/`（不带子分类）—— 与 install 同款；user 看到的活证可能"路径不够细"。缓解：scope 字段保持现有签名向后兼容，不破 install 流程；若将来需要细分，单独 sug。
- **风险 2：constraints/index.md 表格新行的 path 字段含 `/` 子目录**（如 `coding/x.md`），现有 `_parse_index_md` 只按 `|` 切 cells，不解析 path 内部 → 兼容。但 `_load_project_level_index` 加载链取出 path 后是否会按相对路径正确读到子目录文件？回查代码：`_load_project_level_index` 只返回 list[dict]，**不实际读文件内容**（agent 自行加载），故 path = `coding/x.md` 在 agent 端表现为相对 index.md 同目录的子路径，加载链兼容。
- **风险 3：tool kind 用「## 项目级工具清单」段而非表格** —— schema 与 constraints/experience 不一致。缓解：`_load_project_level_index` 当前 scope_map 不含 "tools" key（它是 `experience-tool` / `experience-roles` 等），tools 的加载实际靠 tools-manager 自己扫 `tools/` 目录，不走 `_load_project_level_index`，故两套 schema 共存合规。
- **风险 4：git add 在 user 已 `git rm` 缓冲区时报错** —— `_pad_git_stage` 中 try/except 已 silent skip。
- **风险 5：subprocess.run cwd 参数与 root.relative_to 兼容性** —— 用 `cwd=str(root)` + `rel = p.relative_to(root).as_posix()`，跨平台兼容。
