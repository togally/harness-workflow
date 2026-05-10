---
id: chg-03
title: "skill 文档透传 --fallback + 双路径 dogfood TC"
parent_req: req-56
operation_type: plan
---

## 1. Scope（精确文件 + 改动点）

### F1-F3：skill 文档三镜像

- `.claude/skills/harness-requirement/SKILL.md`（live）
- `.kimi/skills/harness-requirement/SKILL.md`（mirror）
- `.qoder/skills/harness-requirement/SKILL.md`（mirror）

在 ARGUMENTS 段下方追加固定段（三份字节级一致）：

```markdown
## --fallback 标志（req-56）

`harness requirement "<title>"` 默认行为已与 gstack `/office-hours` 强映射打通：
analyst 进入 Step A1.5 后会通过 batched-report 让你在主对话执行 `/office-hours`，
完成后把 design doc path 回传，由 analyst 按 adapter SOP 重组为 requirement.md。

如需跳过 office-hours 走原生 analyst 手工 SOP（小需求 / 已想清楚 / 不想多走一层），
追加 `--fallback`：

```
harness requirement "<title>" --fallback
```

CLI 会把 `office_hours_mode: fallback` 写到 `.workflow/state/requirements/{req-id}-{slug}.yaml`，
analyst 据此跳过 path α 直接 Step A2。

如果你用的是非 Claude Code agent（gstack /office-hours 不可用），
CLI 检测 `gstack_status.agent_kind_compatible=false` 时会自动 fallback +
stdout 警告 `[gstack] agent 不兼容，本 req 自动 fallback 模式`。

无论走 fallback 还是 office-hours 路径，最终 requirement.md 必须落到
`.workflow/flow/requirements/{req-id}-{slug}/requirement.md`，
含 frontmatter 5 字段（id / title / created_at / operation_type / stage）+ 4 章节
（Goal / Scope / Acceptance Criteria / Split Rules），
统一通过 `harness validate --human-docs` + `harness validate --contract artifact-placement` 双绿。
```

### F4：`tests/integration/test_req56_fallback_dogfood.py`（新增）

```python
# 概要（实际 plan 中无需放完整代码；这里是骨架示意）
import subprocess, sys, yaml
from pathlib import Path

def _bootstrap_tmp(tmp_path: Path, compat: bool):
    """tmp_path 下铺最小 .workflow 骨架 + runtime.yaml.gstack_status.agent_kind_compatible=compat。"""
    ...

def test_fallback_path_endtoend(tmp_path: Path):
    _bootstrap_tmp(tmp_path, compat=True)
    r = subprocess.run([sys.executable, "-m", "harness_workflow.cli",
                        "requirement", "测试 fallback", "--fallback",
                        "--root", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0
    assert "[mode] fallback" in r.stdout
    state_file = next((tmp_path / ".workflow/state/requirements").glob("req-*.yaml"))
    state = yaml.safe_load(state_file.read_text())
    assert state["office_hours_mode"] == "fallback"
    req_md = next((tmp_path / ".workflow/flow/requirements").glob("req-*/requirement.md"))
    text = req_md.read_text()
    for section in ("## Goal", "## Scope", "## Acceptance Criteria", "## Split Rules"):
        assert section in text
    fm_keys = ("id:", "title:", "created_at:", "operation_type:", "stage:")
    for key in fm_keys:
        assert key in text

def test_office_hours_path_compat_false_auto_fallback(tmp_path: Path):
    _bootstrap_tmp(tmp_path, compat=False)
    r = subprocess.run([sys.executable, "-m", "harness_workflow.cli",
                        "requirement", "agent 不兼容", "--root", str(tmp_path)],
                       capture_output=True, text=True)
    assert "[gstack] agent 不兼容" in r.stdout
    state_file = next((tmp_path / ".workflow/state/requirements").glob("req-*.yaml"))
    state = yaml.safe_load(state_file.read_text())
    assert state["office_hours_mode"] == "fallback"

def test_human_docs_and_artifact_placement_pass(tmp_path: Path):
    _bootstrap_tmp(tmp_path, compat=True)
    subprocess.run([sys.executable, "-m", "harness_workflow.cli",
                    "requirement", "double green test", "--fallback",
                    "--root", str(tmp_path)], check=True)
    r1 = subprocess.run([sys.executable, "-m", "harness_workflow.cli",
                         "validate", "--human-docs", "--root", str(tmp_path)],
                        capture_output=True, text=True)
    assert r1.returncode == 0
    r2 = subprocess.run([sys.executable, "-m", "harness_workflow.cli",
                         "validate", "--contract", "artifact-placement", "--root", str(tmp_path)],
                        capture_output=True, text=True)
    assert r2.returncode == 0
```

## 2. 实施步骤

1. **Step 1**：F1 写 .claude/skills/harness-requirement/SKILL.md 追加段。
2. **Step 2**：F2/F3 cp 到 .kimi / .qoder 镜像（三份内容字节级一致）。
3. **Step 3**：F4 写 dogfood TC 3 用例（fallback / compat=false 自动 fallback / 双绿验证）。
4. **Step 4**：本地 `pipx install --force` 后 `pytest tests/integration/test_req56_fallback_dogfood.py -v` 3/3。
5. **Step 5**：自检：
   - 5.1 `diff -q .claude/skills/harness-requirement/SKILL.md .kimi/skills/harness-requirement/SKILL.md` silent
   - 5.2 `diff -q .claude/skills/harness-requirement/SKILL.md .qoder/skills/harness-requirement/SKILL.md` silent
   - 5.3 三处 grep `--fallback` 各命中 ≥ 1
   - 5.4 `harness validate --human-docs` exit 0；`harness validate --contract artifact-placement` exit 0

## 3. 依赖

- 上游：chg-01（CLI flag + state schema）/ chg-02（analyst.md 行为）已落地。
- 下游：无（chg-03 是 req-56 终结 chg）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - .claude/skills/harness-requirement/SKILL.md
> - .kimi/skills/harness-requirement/SKILL.md
> - .qoder/skills/harness-requirement/SKILL.md
> - tests/integration/test_req56_fallback_dogfood.py（新增）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-Dogfood-01 | tmp_path bootstrap + subprocess `harness requirement "测试 fallback" --fallback` | returncode=0; stdout `[mode] fallback`; state.office_hours_mode=fallback; runtime.stage=analysis; feedback.jsonl 至少 1 事件; requirement.md 含 frontmatter 5 字段 + 4 章节 | AC-02+AC-05+AC-07 | P0 |
| TC-Dogfood-02 | tmp_path 预置 compat=false + subprocess 无 flag | stdout 含 `[gstack] agent 不兼容`; state.office_hours_mode=fallback | AC-03+AC-05 | P0 |
| TC-Dogfood-03 | TC-01 后跑 `harness validate --human-docs` + `--contract artifact-placement` | 双 exit 0 | AC-06+AC-07 | P0 |
| TC-04 | grep `--fallback` 三镜像 SKILL.md | 各命中 ≥ 1 | AC-05 | P0 |
| TC-05 | diff -q 三镜像两两对 | silent | AC-07 | P0 |

## 5. 验收 lint 命令字面

```bash
# AC-05：dogfood 测试全绿
pytest tests/integration/test_req56_fallback_dogfood.py -v   # 期望 3 passed

# AC-07：三镜像同步
diff -q .claude/skills/harness-requirement/SKILL.md .kimi/skills/harness-requirement/SKILL.md   # silent
diff -q .claude/skills/harness-requirement/SKILL.md .qoder/skills/harness-requirement/SKILL.md   # silent
grep -c -- '--fallback' .claude/skills/harness-requirement/SKILL.md   # 期望 ≥ 1
grep -c -- '--fallback' .kimi/skills/harness-requirement/SKILL.md     # 期望 ≥ 1
grep -c -- '--fallback' .qoder/skills/harness-requirement/SKILL.md    # 期望 ≥ 1

# AC-06：双绿（端到端兜底）
harness validate --human-docs                       # exit 0
harness validate --contract artifact-placement      # exit 0
```

## 6. 镜像同步清单

| Live 文件 | Mirror 路径（同 hash） | 同步语义 |
|-----------|-----------|---------|
| `.claude/skills/harness-requirement/SKILL.md` | `.kimi/skills/harness-requirement/SKILL.md` | 全文字节级一致 |
| `.claude/skills/harness-requirement/SKILL.md` | `.qoder/skills/harness-requirement/SKILL.md` | 全文字节级一致 |

实施约束：三镜像**同 commit** 落地。
