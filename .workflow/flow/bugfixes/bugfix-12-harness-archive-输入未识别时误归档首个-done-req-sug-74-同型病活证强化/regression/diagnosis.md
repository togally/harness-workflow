---
id: bugfix-12
title: "harness archive 输入未识别时误归档首个 done req（sug-74 同型病活证强化）"
created_at: 2026-05-10
operation_type: bugfix
stage: regression
---

# 诊断报告

## 1. 问题描述（实证）

### 案例 A（本次活证，2026-05-10 dogfood 触发）

```
$ echo "N" | harness archive req-57 --skip-revert-check
[revert-dry-run] 警告（--skip-revert-check 模式）：revert 抽样发现冲突（2 / 5 个 commit）
  冲突 commit: 399cfbd57144
  冲突 commit: 744d1e397166
Archived requirement: req-53-新增-harness-命令-给项目添加规范-经验-工具-引导式
Archive path: .../archive/harness-gstack/req-53-...
```

输入 `req-57`，实际归档了 `req-53`（无视输入，无报错）。

### 案例 B（sug-74（harness archive bugfix-id 误归档 req CLI bug）历史活证，2026-05-08）

```
$ harness archive bugfix-11 --skip-revert-check
Archived requirement: req-53
```

输入 `bugfix-11`，同样误归档 `req-53`。

### 共同特征

- 输入的 id（req-57 / bugfix-11）**未匹配** done_reqs 列表中任何条目时，CLI **静默 fallback** 到 `done_reqs[0]`（首个 done req，即 req-53），无任何报错或警告
- 受影响场景：non-tty 环境（管道输入 / 自动化脚本）+ tty 环境（用户回车默认接受）
- 后果：`req-53` 文件被 mv 到 `.workflow/flow/archive/`；runtime.yaml current_requirement / active_requirements 被反写；如未及时发现，对真实需求工件造成实质损伤

## 2. 根因分析

### 直接根因：cli.py:143 silent fallback

`src/harness_workflow/cli.py` 函数 `prompt_requirement_selection`（L120-153）：

```python
def prompt_requirement_selection(requirements: list[dict], preselect: str | None = None) -> str | None:
    ...
    default_value = preselect if preselect and any(r["req_id"] == preselect for r in requirements) else requirements[0]["req_id"]   # L143

    if not sys.stdin.isatty():
        return default_value   # L146
    ...
```

**bug 行为**：
- L143：`preselect` 不在 `requirements` 时，**静默** fallback 到 `requirements[0]["req_id"]`（首个 done req）
- L146：non-tty 环境直接返回该 fallback 值，**完全跳过用户确认**
- tty 环境进入 questionary，default 已被改为 `requirements[0]`，用户回车即提交（"默认选项陷阱"）

### 调用链根因：cli.py:610-630 跳过 validate

`src/harness_workflow/cli.py` archive 子命令分发块（L588-641）：

```python
preselect_value = args.requirement   # = 用户输入（如 "req-57" / "bugfix-11"）
if not preselect_value:              # ← 仅在用户**没传**时才走 runtime fallback
    try:
        ...
        if preselect_value and not any(r["req_id"] == preselect_value for r in done_reqs):
            print("[archive] current_requirement {!r} 不在 done 列表中...", file=sys.stderr)
            preselect_value = None    # ← 仅 runtime.current_requirement 时显式 None
        ...
selected = prompt_requirement_selection(done_reqs, preselect=preselect_value)
```

**bug 行为**：用户**显式传入** id（args.requirement 非 None）时，**根本不进** L611 if 块，preselect_value 保留用户输入值；L619-627 的"不在 done 列表则置 None"的检查**只对 runtime.current_requirement 兜底路径生效**，对显式输入失效。

### 根因总结

> **silent fallback** + **validate 仅覆盖 runtime fallback 路径** 双重缺陷叠加，导致显式用户输入的不存在 id 被静默替换为首个 done req。

## 3. 真实问题判定

**真实问题**。
- 现象稳定可复现（本次 dogfood 触发 + sug-74 历史触发）
- 根因明确（cli.py 两处代码缺陷）
- 后果实质（fmv 误操作影响真实需求工件 + runtime 状态被反写）

## 4. 路由决定

**路由 → executing**（实现层 bug，cli.py 代码修复）。

无需求/设计层调整；测试层补 dogfood TC 防回归。

## 5. 修复方案

### 方案 A（推荐）：silent fallback → 显式报错

修两处：

**修改点 1**：`src/harness_workflow/cli.py` L143（`prompt_requirement_selection`）

```python
# 改前
default_value = preselect if preselect and any(r["req_id"] == preselect for r in requirements) else requirements[0]["req_id"]

# 改后
if preselect and not any(r["req_id"] == preselect for r in requirements):
    available = ", ".join(r["req_id"] for r in requirements)
    print(
        f"[archive] 输入的 {preselect!r} 不在 done 列表中。\n"
        f"  当前可归档候选: {available}\n"
        f"  请检查 id 拼写、确认 stage='done'、或不带参数运行 `harness archive` 看交互列表。",
        file=sys.stderr,
    )
    return None
default_value = preselect if preselect else requirements[0]["req_id"]
```

**修改点 2**：`src/harness_workflow/cli.py` L611（archive dispatch 块）

把 L619-627 的 validate 提到 if 外，无论 args.requirement 还是 runtime.current_requirement 都跑：

```python
preselect_value = args.requirement
if not preselect_value:
    try:
        runtime_path = root / ".workflow" / "state" / "runtime.yaml"
        if runtime_path.exists():
            rt_data = yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
            preselect_value = str(rt_data.get("current_requirement", "")).strip() or None
    except Exception:
        preselect_value = None

# 始终跑 validate（不区分 args / runtime 路径）
if preselect_value and not any(r["req_id"] == preselect_value for r in done_reqs):
    print(
        f"[archive] {preselect_value!r} 不在 done 列表中。\n"
        f"  当前可归档候选: {', '.join(r['req_id'] for r in done_reqs)}\n"
        f"  请检查 id 拼写或 stage='done'。",
        file=sys.stderr,
    )
    return 1
```

### 方案 B（不采用）：保留 silent fallback 但加 confirmation prompt

弊端：tty 环境多一次 prompt，自动化脚本被 break；non-tty 环境必须报错才安全。**不推荐**。

### Default-pick

方案 A。理由：silent fallback 是设计反模式，应当直接 fail-fast；输入未识别 fast fail 是正确语义；与 `harness archive`（无参数）走交互列表路径不冲突（无参数时 args.requirement=None，进 fallback 路径）。

## 6. 影响评估

- **现网影响**：sug-74 报告 + 本次活证共 2 次误归档（req-53 受冲击各 1 次）；可能存在未发现的历史误归档案例
- **修复后兼容**：用户输入合法 id 时行为不变；不合法 id 改为报错（现行是 silent，行为变更属于修 bug）
- **配套**：sug-74 完成后状态可改 `archived`（同型病修复）

---

## 测试用例设计

> regression_scope: targeted
> 波及接口清单（修复方案人工补全）：
> - src/harness_workflow/cli.py:120-153（prompt_requirement_selection）
> - src/harness_workflow/cli.py:588-641（archive 子命令分发块）
> - src/harness_workflow/tools/harness_archive.py（无修改，行为不变验证）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | non-tty `harness archive req-99` (req-99 不存在) | exit 1 + stderr 含 "不在 done 列表中" + 不修改任何文件 | AC-01（输入未识别报错不静默归档） | P0 |
| TC-02 | non-tty `harness archive bugfix-99` (bugfix-99 不存在) | exit 1 + stderr 含 "不在 done 列表中" + 不修改任何文件 | AC-01 | P0 |
| TC-03 | non-tty `harness archive bugfix-11` (bugfix-11 stage=done 在 done_reqs) | exit 0 + 实际归档 bugfix-11（**不是** req-53） | AC-02（合法输入正常归档） | P0 |
| TC-04 | non-tty `harness archive req-53` (req-53 stage=done 在 done_reqs) | exit 0 + 实际归档 req-53 | AC-02 | P0 |
| TC-05 | non-tty `harness archive` (无参数, runtime.current_requirement 不在 done_reqs) | exit 1 + stderr 含 "不在 done 列表中"（不静默 fallback 到 done_reqs[0]） | AC-03（runtime fallback 失败也应报错） | P0 |
| TC-06 | non-tty `harness archive` (无参数, runtime.current_requirement 在 done_reqs) | exit 0 + 归档 runtime.current_requirement | AC-04（合法 runtime fallback 路径不破坏） | P0 |
| TC-Dogfood-07 | tmp_path subprocess `harness archive req-99` | returncode=1 + stderr 含错误提示 + .workflow/flow/requirements/ 内容不变 | AC-01+AC-02 | P0 |
| TC-08 | prompt_requirement_selection 单测：preselect 不在 requirements + non-tty | return None | AC-01 | P0 |
| TC-09 | prompt_requirement_selection 单测：preselect 在 requirements + non-tty | return preselect | AC-02 | P0 |
| TC-10 | prompt_requirement_selection 单测：preselect=None + non-tty + requirements 非空 | return requirements[0]["req_id"]（保留无参数兜底逻辑） | AC-04 | P0 |

每个波及接口至少对应 1 条用例，`对应 AC` 字段非空。
