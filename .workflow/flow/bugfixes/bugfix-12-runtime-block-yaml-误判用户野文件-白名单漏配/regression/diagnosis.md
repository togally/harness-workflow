---
id: bugfix-12
title: "runtime-block.yaml-误判用户野文件-白名单漏配"
created_at: 2026-04-30
operation_type: bugfix
stage: regression
---

## 问题描述

非 dev_repo 用户仓（如 PetMallPlatform）在任意触发 `raise_harness_block` 的执行路径之后，再跑 `harness validate --contract user-write-protected-zones`（或 `harness status --lint` 派生的硬门禁链路），会得到：

```
[user-write-protected-zones] ABORT: 1 violation(s) — 用户野文件命中保护区:
  - .workflow/state/runtime-block.yaml
Hint: 用户自定义内容请放 artifacts/ 下；保护区仅 harness 工具能写。
```

`runtime-block.yaml` 实际上是 harness CLI 自家在 HARNESS_BLOCK 错误协议里运行时创建的状态文件（`raise_harness_block` 写入），不是用户野文件，但被硬门禁误判为侵入保护区。

## 证据（独立复核 — 不盲信主 agent 4 条结论）

### 复核 1：runtime-block.yaml 写入源是 harness 自家代码

```
$ grep -n "runtime-block" src/harness_workflow/workflow_helpers.py
8206: """发出 HARNESS_BLOCK 协议信号，写 runtime-block.yaml，返回 exit code。
8211: 3. .workflow/state/runtime-block.yaml：结构化状态文件
8237: # 2) 写 runtime-block.yaml（recovery_attempts 累加）
8238: block_path = root / ".workflow" / "state" / "runtime-block.yaml"
```

`raise_harness_block`（line 8198）唯一写盘点 line 8238，路径写死 `.workflow/state/runtime-block.yaml`。**结论 1 成立**。

### 复核 2：check_user_write_protected_zones 三级豁免链

```
src/harness_workflow/validate_contract.py:1107  def check_user_write_protected_zones(...)
src/harness_workflow/validate_contract.py:1152          # 三级豁免
src/harness_workflow/validate_contract.py:1153          if relative in mirror: continue
src/harness_workflow/validate_contract.py:1155          if relative in managed: continue
src/harness_workflow/validate_contract.py:1157          if any(w in relative for w in _SCAFFOLD_V2_MIRROR_WHITELIST): continue
```

dev_repo 短路在 line 1120 (`if _is_dev_repo(root): return 0`)。**结论 2 成立**。

### 复核 3：_SCAFFOLD_V2_MIRROR_WHITELIST 现状（21 条 + runtime-block.yaml 不命中）

直接跑 Python 验证：

```python
$ PYTHONPATH=src python3 -c "
from harness_workflow.workflow_helpers import _SCAFFOLD_V2_MIRROR_WHITELIST
hit = [w for w in _SCAFFOLD_V2_MIRROR_WHITELIST if w in 'state/runtime-block.yaml']
print(hit)"
[]   # ← 21 条白名单零命中
```

而 `state/runtime.yaml` 命中：`['state/runtime.yaml']`。**结论 3 成立**：白名单漏 `state/runtime-block.yaml`。

### 复核 4：本仓 dev_repo 探测命中所以本地不复现

```
$ grep -n 'name\s*=\s*"harness-workflow"' pyproject.toml
2: name = "harness-workflow"
```

`_is_dev_repo` Layer 1 命中（validate_contract.py:1086-1090）→ `check_user_write_protected_zones` line 1121 `return 0` 直接短路。所以本仓跑 contract 永远不扫，本地不复现，用户报告来自非 dev 用户仓。**结论 4 成立**。

### 复核 5（mirror 第一级豁免）：runtime-block.yaml 不在 scaffold mirror

```python
$ PYTHONPATH=src python3 -c "
from pathlib import Path
from harness_workflow.workflow_helpers import _scaffold_v2_file_contents
mirror = _scaffold_v2_file_contents(Path('/tmp'), include_agents=False, include_claude=False, language='cn')
keys = sorted(k for k in mirror.keys() if 'state/' in k)
print(keys)"
['.workflow/state/action-log.md', '.workflow/state/experience/index.md',
 '.workflow/state/platforms.yaml', '.workflow/state/runtime.yaml']
```

mirror 仅 4 文件，无 runtime-block.yaml。**第一级豁免 miss**。

### 复核 6（managed 第二级豁免）：runtime-block.yaml 不在 managed-files.json

`_save_managed_state` 仅记录 `_sync_scaffold_v2_mirror_to_live` / `_install_self_audit` 推送过的 mirror 文件 hash；`raise_harness_block` 直接 `block_path.write_text(...)`（workflow_helpers.py:8264 附近）从不写 managed_files。**第二级豁免 miss**。

三级豁免全部 miss → 误报落定。

## 真伪判定

**判定 = real（真实问题）**。
- 主 agent 4 条结论独立复核全部成立；
- 三级豁免 mirror（第一级）/ managed（第二级）/ WHITELIST（第三级）经实证均不命中 `state/runtime-block.yaml`；
- 用户报告的 ABORT 输出与 `check_user_write_protected_zones` line 1163 字面一致（`[user-write-protected-zones] ABORT: 1 violation(s) — 用户野文件命中保护区:`）。

非误判，非部分真，是纯白名单漏配。

## 同型病扫描（重点）

逐个判定 harness 自家在 `.workflow/state/...` 下写盘的运行时文件，是否被三级豁免链至少一级覆盖：

| 文件路径 | 写盘者 | mirror 命中 | managed 命中 | WHITELIST substring 命中 | 判定 |
|---------|--------|------------|------------|------------------------|------|
| `state/runtime.yaml` | 各路 update_runtime | 是 | 是 | `state/runtime.yaml` | 已覆盖 ✅ |
| `state/runtime-block.yaml` | `raise_harness_block` | **否** | **否** | **否** | **漏配 ❌**（本 bugfix 修复对象） |
| `state/action-log.md` | append_action_log | 是 | 是 | `state/action-log.md` | 已覆盖 ✅ |
| `state/platforms.yaml` | `_persist_active_agent` | 是 | 是 | （无独立子串，靠 mirror 兜底）| 已覆盖 ✅ |
| `state/experience/index.md` | `_refresh_experience_index` | 是 | 是 | （无独立子串，靠 mirror 兜底）| 已覆盖 ✅ |
| `state/sessions/{id}/usage-log.yaml` | `record_subagent_usage` | 否 | 否 | `state/sessions` | 已覆盖 ✅ |
| `state/sessions/{id}/task-context/*.md` | task-context snapshot | 否 | 否 | `state/sessions` | 已覆盖 ✅ |
| `state/requirements/{id}-{slug}.yaml` | requirement_init | 否 | 否 | `state/requirements` | 已覆盖 ✅ |
| `state/bugfixes/{id}-{slug}.yaml` | bugfix_init | 否 | 否 | `state/bugfixes` | 已覆盖 ✅ |
| `state/feedback/feedback.jsonl` | append_feedback_event | 否 | 否 | `state/feedback` | 已覆盖 ✅ |

**结论：同型病只此 1 例（runtime-block.yaml）。** 其它 9 类要么本身在 mirror（前四类），要么有 WHITELIST 父目录子串兜底（后五类）。漏配仅 1 条。

## 根因分析

`raise_harness_block`（req-48 / chg-01）落地时新增了一个运行时态产物 `.workflow/state/runtime-block.yaml`，但**没有同步更新** `_SCAFFOLD_V2_MIRROR_WHITELIST`：

- mirror 维度：runtime-block.yaml 是按 error 触发才写、跨项目不共享，本就**不应**进 scaffold mirror（语义正确）；
- managed 维度：mirror 不进 → managed-files.json 也不进（语义自洽）；
- WHITELIST 维度：白名单设计意图就是兜底"运行时态 / 业务态、跨项目独立、不能从 mirror 覆盖回去"的文件（见 workflow_helpers.py:170 注释），**runtime-block.yaml 完全符合该语义但被遗忘登记**。

直接根因 = req-48 / chg-01 实施时漏改 `_SCAFFOLD_V2_MIRROR_WHITELIST`。
深层根因 = 新增 harness 自写运行时文件时，缺乏"必须同步白名单"的代码评审清单（属于流程问题，不在本 bugfix 范围内）。

## 影响范围

- **触发面**：所有非 dev_repo 用户仓 + 任意触发过 `raise_harness_block` 的历史路径（如 fix-checklist lint 过的项目，PetMallPlatform 即落入此面）；
- **症状**：`harness validate --contract user-write-protected-zones` / `harness status --lint` 直接 ABORT exit 1，阻塞用户后续 harness 命令；
- **数据影响**：无（误报，未损坏数据，未误删文件）；
- **回滚成本**：低（白名单加一条字符串）。

## 路由决定

- 真实问题 → 路由 **executing**（实现层修复，纯白名单加条目 + 反例测试）；
- 不路由 requirement_review（无需求 / 设计变更，纯实现遗漏）；
- 不路由 testing（不是测试断言错而是源码漏配）。

## 修复方案（fix plan，供 executing 抄）

### 必改 1：白名单加 1 条

文件：`src/harness_workflow/workflow_helpers.py`
位置：`_SCAFFOLD_V2_MIRROR_WHITELIST` 元组（line 172-201）内 `# 运行时 / 业务态` 段
插入位置建议：紧贴 `"state/runtime.yaml"` 下一行，便于人眼配对（runtime + runtime-block 同源同区）。
插入内容：

```python
    "state/runtime-block.yaml",      # bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）：raise_harness_block 运行时按需创建，跨项目独立，不入 scaffold mirror
```

**严禁**改任何其他白名单条目顺序、严禁动 `# req-51 / chg-02` 段、严禁碰 `_is_dev_repo` 三层探测、严禁碰 `check_user_write_protected_zones` 三级豁免主体逻辑。**纯加 1 行**。

### 必加 2：反例测试（≥ 4 条 TC）

文件：`tests/test_bugfix_12_runtime_block_whitelist.py`（新建）

模板与命名参照 `tests/test_user_write_protected_zones.py`（同 helper 同 tmp_path 模式）。

| TC | 场景 | 期望 |
|----|------|------|
| TC-01 | 非 dev_repo（tmp_path 无 pyproject + 无 src/harness_workflow + 无 env）+ `.workflow/state/runtime-block.yaml` 存在 → `check_user_write_protected_zones(tmp_path)` | `rc == 0`（白名单命中，不误报） |
| TC-02 | 非 dev_repo + 同时存在 runtime-block.yaml 和真正的野文件（如 `.workflow/context/roles/my-custom.md`）→ 调 helper | `rc == 1` 且 stderr 仅列 `my-custom.md`，**不**列 `runtime-block.yaml` |
| TC-03 | 直接断言 `'state/runtime-block.yaml' in _SCAFFOLD_V2_MIRROR_WHITELIST`（防御性，防止后续 chg 误删） | `True` |
| TC-04 | dev_repo（写 pyproject `name = "harness-workflow"`）+ runtime-block.yaml 存在 → 调 helper | `rc == 0`（dev 短路，与既有 TC-04b 不冲突） |

每个 TC 用 `monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)` 隔离 env 干扰。

### 必同步 3：scaffold_v2 mirror 不需要动

`workflow_helpers.py` 不在 `src/harness_workflow/assets/scaffold_v2/` 下（已实证：`find scaffold_v2 -name workflow_helpers.py` 零命中）；scaffold_v2 mirror 只镜像 `.workflow/`、根级 README/CLAUDE/AGENTS/WORKFLOW.md 等，不含 src/。所以白名单改完**不需要**额外同步。

但 executing 必须**反向核查**：
```
find src/harness_workflow/assets/scaffold_v2 -name "workflow_helpers.py"
```
返回空 → 跳过 mirror 同步；返回非空 → 视为契约破坏立即上报。

### 不做的事（范围红线 — 与主 agent briefing 一致）

- **不**动 PetMallPlatform 任何文件；
- **不**动 req-51 任何文件；
- **不**动 `_is_dev_repo` 三层探测逻辑；
- **不**动 `check_user_write_protected_zones` 三级豁免主体；
- **不**改 `raise_harness_block` 写盘路径或行为；
- **不**新增 helper / 新概念 / 新契约。

## 完成判据 lint 命令清单（字面 — 吸取 bugfix-11 教训，executing 不允许偷换）

executing 完工自检 + testing 复核 + acceptance 终验，**严格**按下三条字面命令执行：

### Lint 1：白名单条目实证

```
grep -n "state/runtime-block.yaml" src/harness_workflow/workflow_helpers.py
```

**期望**：恰命中 1 行，行内含 `"state/runtime-block.yaml"`（带引号），且 grep 输出行号 ∈ [172, 201]（即落在 `_SCAFFOLD_V2_MIRROR_WHITELIST` 元组内）。
**违规判定**：0 行 → 没改 / ≥ 2 行 → 误改了别处 / 行号超出 [172, 201] → 改在了错误位置。

### Lint 2：新增反例测试 PASS

```
pytest tests/test_bugfix_12_runtime_block_whitelist.py -v
```

**期望**：`4 passed`（或 ≥ 必加表 4 条），无 fail / no error。

### Lint 3：全量回归不增 fail

```
pytest tests/ --tb=no -q | tail -5
```

**期望末两行**（baseline = 51 failed / 729 passed / 40 skipped，本 regression stage 实测于 2026-04-29）：
```
51 failed, <≥ 733> passed, 40 skipped, ...
```
即 fail 数 **≤ 51**（不允许新增回归）+ passed 数 **≥ 729 + 4**（新增 4 条 TC 全 PASS）。

### Lint 4（可选 / 推荐）：契约自身 dogfood

```
PYTHONPATH=src python3 -c "
from pathlib import Path
import tempfile, os
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    block = root / '.workflow' / 'state' / 'runtime-block.yaml'
    block.parent.mkdir(parents=True, exist_ok=True)
    block.write_text('error_type: dummy\nseverity: FAIL\n', encoding='utf-8')
    os.environ.pop('HARNESS_DEV_REPO_ROOT', None)
    from harness_workflow.validate_contract import check_user_write_protected_zones
    rc = check_user_write_protected_zones(root)
    print('rc=', rc)
    assert rc == 0, f'expected rc=0 (whitelisted), got {rc}'
print('PASS')
"
```

**期望**：stdout 包含 `rc= 0` 和 `PASS`。

## 是否阻塞

**不阻塞**。
- 路由方向已定（confirm → executing）；
- 修法明确（纯白名单加 1 条字符串）；
- 测试方案明确（4 条 TC，模板已存在）；
- 完成判据 4 条 lint 字面命令已落定；
- 无未决 OQ（见 required-inputs.md）。

## 测试用例设计

> regression_scope: targeted
> 波及接口清单（基于本次 fix plan 推导）：
> - src/harness_workflow/workflow_helpers.py（_SCAFFOLD_V2_MIRROR_WHITELIST 元组加 1 条）
> - tests/test_bugfix_12_runtime_block_whitelist.py（新建 4 条 TC）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | 非 dev_repo tmp_path + `.workflow/state/runtime-block.yaml` 存在（无 pyproject / 无 src/harness_workflow / monkeypatch delenv HARNESS_DEV_REPO_ROOT） | `check_user_write_protected_zones(tmp_path) == 0`，stderr 不含 `runtime-block.yaml` | AC-01（非 dev_repo 下 runtime-block.yaml 不再误报） | P0 |
| TC-02 | 非 dev_repo tmp_path + runtime-block.yaml + 真野文件 `.workflow/context/roles/my-custom.md` | `rc == 1`，stderr 列 `my-custom.md` 但**不**列 `runtime-block.yaml` | AC-01 + AC-02（豁免精准、不放大） | P0 |
| TC-03 | 直接 `from harness_workflow.workflow_helpers import _SCAFFOLD_V2_MIRROR_WHITELIST` | `'state/runtime-block.yaml' in _SCAFFOLD_V2_MIRROR_WHITELIST` 为 True | AC-03（白名单条目防御性 lock） | P1 |
| TC-04 | dev_repo（pyproject name=harness-workflow）+ runtime-block.yaml 存在 | `rc == 0`（dev 短路，与既有 TC-04b 行为一致，回归保护） | AC-04（dev_repo 行为不被本 fix 改变） | P1 |

每用例对应 AC 字段非空，覆盖所有波及接口（workflow_helpers.py whitelist 改动 + helper 函数行为）。
