---
id: chg-01
title: "CLI --fallback 参数 + req-state.yaml office_hours_mode schema + agent 兼容性兜底"
parent_req: req-56
operation_type: plan
---

## 1. Scope（精确文件 + 改动点）

### F1：`src/harness_workflow/cli.py`

- `req_parser`（约 L277-L281）后追加：
  ```python
  req_parser.add_argument(
      "--fallback",
      dest="fallback",
      action="store_true",
      help="跳过 gstack /office-hours 强映射，analyst 走原生 Step A2 手工 SOP（req-56）。",
  )
  ```
- dispatch 块（L539-L547）`if args.command == "requirement":` 内追加：
  ```python
  if args.fallback:
      cmd_args.append("--fallback")
  ```

### F2：`src/harness_workflow/tools/harness_requirement.py`

- argparse 加 `--fallback`：
  ```python
  parser.add_argument("--fallback", dest="fallback", action="store_true",
                      help="opt-out gstack office-hours 强映射 (req-56)")
  ```
- 调用 `create_requirement(...)` 透传：
  ```python
  return create_requirement(root, title, requirement_id=args.id, title=title, fallback=args.fallback)
  ```

### F3：`src/harness_workflow/workflow_helpers.py`

- `create_requirement` 签名增参：
  ```python
  def create_requirement(root, name, requirement_id=None, title=None, fallback: bool = False) -> int:
  ```
- 函数体内（state yaml save 之前）插入：
  ```python
  runtime_state = load_requirement_runtime(root)
  gstack_status = runtime_state.get("gstack_status") or {}
  compat = bool(gstack_status.get("agent_kind_compatible", False))
  if fallback or not compat:
      office_hours_mode = "fallback"
  else:
      office_hours_mode = "required"
  if not compat and not fallback:
      print("[gstack] agent 不兼容，本 req 自动 fallback 模式")
  if fallback:
      print("[mode] fallback")
  ```
- `save_simple_yaml(state_file, {...}, ordered_keys=[...])` 调用：
  - dict 内追加 `"office_hours_mode": office_hours_mode`
  - ordered_keys 末尾追加 `"office_hours_mode"`

### F4：测试 `tests/installer/test_requirement_fallback_flag.py`（新增 ~120 行）

- fixture：`tmp_path` 作 root，预填 `.workflow/state/runtime.yaml` 含 / 不含 `gstack_status.agent_kind_compatible`。
- 6 用例 P0：
  - TC-01：无 flag + compat=true → state=required + 无警告
  - TC-02：无 flag + compat=false → state=fallback + stdout 含 `[gstack] agent 不兼容`
  - TC-03：--fallback + compat=true → state=fallback + stdout 含 `[mode] fallback`
  - TC-04：--fallback + compat=false → state=fallback + stdout 含两条
  - TC-05：gstack_status 字段不存在 → 视同 compat=false → state=fallback
  - TC-06：老 req 缺 office_hours_mode 字段 → load_simple_yaml 后 dict.get default=required（断言不抛异常）
- 4 用例 P1：
  - TC-07：state yaml round-trip（save → load → 字段还在）
  - TC-08：ordered_keys 含 `office_hours_mode`
  - TC-09：CLI subprocess `python -m harness_workflow.cli requirement "X" --fallback` 端到端
  - TC-10：CLI subprocess 无 flag + mock compat=true → required

## 2. 实施步骤

1. **Step 1**：F3 改 workflow_helpers.create_requirement（核心改造）+ ordered_keys。
2. **Step 2**：F2 改 harness_requirement.py 透传。
3. **Step 3**：F1 改 cli.py argparse + dispatch 透传。
4. **Step 4**：F4 写单元测试 10 用例。
5. **Step 5**：自检：
   - 5.1 `pipx install --force ~/path/to/harness-workflow` 后跑 `harness requirement "test --fallback"` 真活；端到端 grep state.yaml 含 `office_hours_mode: fallback`
   - 5.2 `pytest tests/installer/test_requirement_fallback_flag.py -v` 10/10
   - 5.3 既有套件不回归：`pytest tests/ -x --ignore=tests/integration` 全绿
   - 5.4 `harness validate --human-docs` exit 0 + `harness validate --contract artifact-placement` exit 0

## 3. 依赖

- 上游：req-55/chg-01 落地的 `runtime.yaml.gstack_status.agent_kind_compatible` 字段（已上线 c7aefc1 vendor）。
- 下游：chg-02（analyst.md 读 office_hours_mode 字段）/ chg-03（skill 文档 + dogfood TC）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/harness_workflow/cli.py（requirement subparser）
> - src/harness_workflow/tools/harness_requirement.py
> - src/harness_workflow/workflow_helpers.py（create_requirement / save_simple_yaml ordered_keys）
> - .workflow/state/requirements/{req-id}.yaml schema

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | mock runtime gstack_status.agent_kind_compatible=true; create_requirement(root, "X") | state.yaml.office_hours_mode == "required"; stdout 无 [gstack] | AC-01 | P0 |
| TC-02 | mock compat=false; create_requirement(root, "X") | state=fallback; stdout 含 `[gstack] agent 不兼容` | AC-03 | P0 |
| TC-03 | mock compat=true; create_requirement(root, "X", fallback=True) | state=fallback; stdout 含 `[mode] fallback` | AC-02 | P0 |
| TC-04 | mock compat=false; fallback=True | state=fallback; stdout 含两条 | AC-02+AC-03 | P0 |
| TC-05 | runtime.yaml 无 gstack_status 字段 | state=fallback（视同 compat=false） | AC-03 | P0 |
| TC-06 | 老 req state.yaml 不含 office_hours_mode | dict.get("office_hours_mode", "required") 不抛异常 | AC-04 | P0 |
| TC-Dogfood-07 | tmp_path 跑 subprocess `python -m harness_workflow.cli requirement "test req" --fallback`；预置 runtime.yaml | returncode=0; stdout 含 [mode] fallback; state.yaml 含 office_hours_mode: fallback; runtime.stage=analysis; feedback.jsonl 至少 1 条事件 | AC-02+AC-05 | P0 |
| TC-08 | save_simple_yaml({...}) round-trip | load 后字段还在 | AC-04 | P1 |
| TC-09 | grep ordered_keys 含 office_hours_mode | 命中 | AC-04 | P1 |
| TC-10 | subprocess 无 flag + 预置 compat=true | state=required; stage=analysis | AC-01 | P1 |

## 5. 验收 lint 命令字面

```bash
# AC-01 / AC-02：CLI argparse --fallback 存在
python3 -m harness_workflow.cli requirement --help | grep -- '--fallback'   # 期望 == 1

# AC-04：ordered_keys 含 office_hours_mode
grep -c '"office_hours_mode"' src/harness_workflow/workflow_helpers.py   # 期望 ≥ 2（dict 写入 + ordered_keys）

# AC-05：单元测试全绿
pytest tests/installer/test_requirement_fallback_flag.py -v   # 期望 10 passed

# AC-06：契约 / human-docs 不破坏
harness validate --human-docs        # exit 0
harness validate --contract artifact-placement   # exit 0
```
