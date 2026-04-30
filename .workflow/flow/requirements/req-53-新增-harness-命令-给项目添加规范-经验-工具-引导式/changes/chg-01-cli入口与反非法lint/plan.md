---
id: chg-01-plan
parent: chg-01（CLI 入口 harness pad + 反非法 lint）
created_at: 2026-04-29
---

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `src/harness_workflow/workflow_helpers.py`

- **新增模块级常量（紧邻 `_SCAFFOLD_V2_MIRROR_WHITELIST` 之后，约 line 209 附近）**：

  ```python
  # req-53（新增-harness-命令-给项目添加规范-经验-工具-引导式）/ chg-01：
  # harness pad 子命令的 kind / scope 固定枚举（user 不能发明）。
  # rule scope 5 类（OQ-Verdicts），experience scope 5 类（沿用 req-51/52 既有），
  # tool 不分 scope（直接落 artifacts/project/tools/{slug}.md）。
  PAD_KINDS: dict[str, list[str]] = {
      "rule": ["coding", "architecture", "api", "database", "security"],
      "experience": ["roles", "stage", "regression", "risk", "tool"],
      "tool": [],  # 不分 scope
  }
  ```

- **新增 stub helper（文件末尾，约 line 8523 之后）**：

  ```python
  def _pad_add(root: Path, kind: str, scope: str, title: str) -> int:
      """req-53 / chg-01 stub：参数解析与 dispatch 验证。
      真实落位（路径解析 / 模板渲染 / write_if_missing）在 chg-02 接入。
      """
      print(f"[harness pad] (stub) parsed kind={kind} scope={scope} title={title}")
      return 0


  def _pad_list(root: Path) -> int:
      """req-53 / chg-01 stub。真实扫描 + 分组在 chg-04 接入。"""
      print("[harness pad list] (stub) scan artifacts/project/{constraints,experience/*,tools}/")
      return 0


  def _pad_interactive(root: Path) -> int:
      """req-53 / chg-01 stub。questionary 三步引导在 chg-04 接入。"""
      print("[harness pad] (stub) interactive mode placeholder")
      return 0


  def _validate_pad_kind(kind: str) -> str | None:
      """非法 kind → 返回错误信息字符串；合法 → 返回 None。"""
      if kind not in PAD_KINDS:
          return "kind 必须是 rule/experience/tool 之一"
      return None


  def _validate_pad_scope(kind: str, scope: str) -> str | None:
      """非法 scope → 返回错误信息字符串；合法 → 返回 None。
      tool 不分 scope，传任何 scope 都报错（除非空字符串）。
      rule / experience：scope 必须在白名单内。
      """
      if kind == "tool":
          if scope:
              return "tool 不分 scope，请直接 `harness pad tool <title>`"
          return None
      allowed = PAD_KINDS.get(kind, [])
      if scope not in allowed:
          return f"{kind} scope 必须是 {'/'.join(allowed)} 之一"
      return None
  ```

### 1.2 `src/harness_workflow/cli.py`

- **新增 subparser 注册（紧邻 `feedback_parser` 之后，约 line 374 附近）**：

  ```python
  pad_parser = subparsers.add_parser(
      "pad",
      help="Project-add：往 artifacts/project/ 加规则 / 经验 / 工具（kind ∈ rule/experience/tool）。",
  )
  pad_parser.add_argument("kind", nargs="?", default="", help="rule / experience / tool / list（list 子命令）。")
  pad_parser.add_argument("scope", nargs="?", default="", help="rule/experience 时的 scope；tool 不需要。")
  pad_parser.add_argument("title", nargs="?", default="", help="条目标题。")
  pad_parser.add_argument("--root", default=".", help="Repository root.")
  ```

- **新增 dispatch 分支（紧邻 `feedback` 分支之后，约 line 700 附近，`return 0` 之前）**：

  ```python
  if args.command == "pad":
      from harness_workflow.workflow_helpers import (
          _pad_add, _pad_list, _pad_interactive,
          _validate_pad_kind, _validate_pad_scope,
      )
      kind_raw = (args.kind or "").strip()
      scope_raw = (args.scope or "").strip()
      title_raw = (args.title or "").strip()

      # list 子命令分流（kind 位置参数被复用为 list 关键字）
      if kind_raw == "list":
          return _pad_list(root)

      # 裸跑（无任何参数）→ interactive
      if not kind_raw:
          return _pad_interactive(root)

      # 非法 kind / scope → ABORT
      err = _validate_pad_kind(kind_raw)
      if err:
          print(f"[harness pad] ABORT: {err}", file=sys.stderr)
          return 2
      err = _validate_pad_scope(kind_raw, scope_raw)
      if err:
          print(f"[harness pad] ABORT: {err}", file=sys.stderr)
          return 2

      # title 缺失（位置参数推断：tool 时 scope 位即是 title）
      if kind_raw == "tool":
          # `harness pad tool <title>`：title 实际在 scope_raw 位
          title_effective = scope_raw or title_raw
          scope_effective = ""
      else:
          title_effective = title_raw
          scope_effective = scope_raw
      if not title_effective:
          print("[harness pad] ABORT: title 必须提供（或裸跑进入 interactive）", file=sys.stderr)
          return 2

      return _pad_add(root, kind_raw, scope_effective, title_effective)
  ```

> 注意：`tool` kind 时位置参数语法为 `harness pad tool <title>`（scope 位被 title 占用），dispatch 中已做 normalize。argparse 不能轻易表达"kind=tool 时 scope 不存在 title 前移"的非对称语义，故在 dispatch 层用启发式 normalize 处理。

## 2. 实施步骤（顺序）

```
# Step 1：在 workflow_helpers.py 加 PAD_KINDS + 5 个 helper（4 个 stub + 2 个 validator）
$ vim src/harness_workflow/workflow_helpers.py
# 定位 _SCAFFOLD_V2_MIRROR_WHITELIST 末尾 → 加 PAD_KINDS
# 定位文件末尾 → 加 _pad_add / _pad_list / _pad_interactive / _validate_pad_kind / _validate_pad_scope

# Step 2：在 cli.py 加 pad_parser + dispatch 分支
$ vim src/harness_workflow/cli.py
# 定位 feedback_parser → 紧随其后加 pad_parser
# 定位 `if args.command == "feedback":` 分支末尾 → 紧随其后加 pad 分支

# Step 3：直跑验证（独立核查 — 硬门禁九）
$ python3 -m harness_workflow.cli pad rule coding "测试-rule"
# 期望 stdout 含 `[harness pad] (stub) parsed kind=rule scope=coding title=测试-rule`

$ python3 -m harness_workflow.cli pad foo bar "..."
# 期望 exit ≠ 0，stderr 含 "kind 必须是 rule/experience/tool 之一"

$ python3 -m harness_workflow.cli pad rule standards "..."
# 期望 exit ≠ 0，stderr 含 "rule scope 必须是 coding/architecture/api/database/security 之一"

$ python3 -m harness_workflow.cli pad list
# 期望 stdout 含 stub list 输出，exit = 0

$ python3 -m harness_workflow.cli pad
# 期望 stdout 含 stub interactive 输出，exit = 0

# Step 4：跑配套 pytest（chg-01 测试用例 ≥ 4 条）
$ pytest tests/test_req53_pad_cli.py -v

# Step 5：契约 lint 自检（无回归）
$ python3 -m harness_workflow.cli validate --contract artifact-placement
$ python3 -m harness_workflow.cli validate --human-docs
```

## 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - `src/harness_workflow/cli.py`（新增 pad subparser + dispatch 分支）
> - `src/harness_workflow/workflow_helpers.py`（新增 PAD_KINDS + 5 个 helper）

新增测试文件 `tests/test_req53_pad_cli.py`，至少 5 条 TC：

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-cli-rule-coding-parsed | `python3 -m harness_workflow.cli pad rule coding "禁止硬编码"`（subprocess） | exit=0，stdout 含 `parsed kind=rule scope=coding` | AC-01 | P0 |
| TC-02-cli-experience-stage-parsed | `pad experience stage "executing-虚报教训"` | exit=0，stdout 含 `parsed kind=experience scope=stage` | AC-01 | P0 |
| TC-03-cli-tool-no-scope-parsed | `pad tool "petmall-deployer"` | exit=0，stdout 含 `parsed kind=tool scope= title=petmall-deployer`（scope 留空，title 来自 scope 位 normalize） | AC-01 | P0 |
| TC-04-cli-illegal-kind-abort | `pad foo bar baz` | exit≠0，stderr 含 "kind 必须是 rule/experience/tool 之一" | 反非法 lint | P0 |
| TC-05-cli-illegal-rule-scope-abort | `pad rule standards "X"` | exit≠0，stderr 含 "rule scope 必须是 coding/architecture/api/database/security 之一" | 反非法 lint | P0 |
| TC-06-cli-illegal-experience-scope-abort | `pad experience standards "X"` | exit≠0，stderr 含 "experience scope 必须是 roles/stage/regression/risk/tool 之一" | 反非法 lint | P0 |
| TC-07-cli-list-stub | `pad list` | exit=0，stdout 含 stub `[harness pad list]` 标识 | AC-06（前置） | P1 |
| TC-08-cli-empty-interactive-stub | `pad`（无参数） | exit=0，stdout 含 stub interactive 标识 | AC-08（前置） | P1 |

实现走 `subprocess.run([sys.executable, "-m", "harness_workflow.cli", "pad", ...])`，不直接调 main()，避免 argparse SystemExit 干扰 pytest。

## 4. 验收 lint 命令字面（grep + pytest，禁止 executing 偷换）

```bash
# 4.1 PAD_KINDS 常量已落地
grep -nE "^PAD_KINDS\s*[:=]" src/harness_workflow/workflow_helpers.py

# 4.2 dispatch 分支已落地
grep -nE 'args\.command\s*==\s*"pad"' src/harness_workflow/cli.py

# 4.3 5 个 helper 全部签名落地
grep -nE "^def (_pad_add|_pad_list|_pad_interactive|_validate_pad_kind|_validate_pad_scope)\b" src/harness_workflow/workflow_helpers.py

# 4.4 反非法 lint 错误信息字符串可被 grep
grep -n "kind 必须是 rule/experience/tool" src/harness_workflow/workflow_helpers.py
grep -n "rule scope 必须是" src/harness_workflow/workflow_helpers.py

# 4.5 配套 pytest 全绿
pytest tests/test_req53_pad_cli.py -v

# 4.6 现有契约不回归
python3 -m harness_workflow.cli validate --contract artifact-placement
python3 -m harness_workflow.cli validate --human-docs
```

## 5. scaffold_v2 mirror 同步清单

- `cli.py` / `workflow_helpers.py` 是 src 实现，**不在** mirror 范围（scaffold_v2 mirror 仅 `.workflow/` 树）。
- 本 chg **不**新增 contract docs；现有契约文档（repository-layout.md / role-loading-protocol.md）保持不动。
- 本 chg **不**触及 `assets/scaffold_v2/.workflow/` 任何文件。
- pyproject.toml `package-data` 不需更新（src/ 下纯代码无新资产）。

## 6. 已知风险与缓解

- **风险 1：argparse 位置参数 nargs="?" 三连**容易被解析歧义。缓解：dispatch 层做 normalize（kind=tool 时 scope 位实际为 title），并加 TC-03 / TC-08 显式覆盖。
- **风险 2：sys.stderr 在 subprocess 中以 UTF-8 输出中文**。缓解：测试用 `result = subprocess.run(..., capture_output=True, text=True, encoding="utf-8")`，并用 `result.stderr` 子串断言。
- **风险 3：dev mode 仓库 `harness validate` 不报错但不在 user-write-protected-zones 范围**。缓解：本 chg 不动保护区，AC-04 / AC-05 在 chg-02 / chg-04 真实落地后再验。
