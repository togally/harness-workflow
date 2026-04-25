# Change Plan — chg-04（CLI 兼容 pytest + escape hatch 文字落地）

## 1. Development Steps

### Step 1: 记录基线 pytest passed 数

- 跑 `pytest -q --tb=no 2>&1 | tail -20` 记录当前基线 passed 数（记入 session-memory.md）；
- 确认 chg-01 / chg-02 / chg-03 已落地（live + mirror）后再启动；否则断言 FAIL。

### Step 2: 新建 `tests/test_analyst_role_merge.py`

- 参考 `tests/test_roles_exit_contract.py` / `tests/test_assistant_role_contract7.py` 现有 pytest 风格（pathlib + yaml + re）；
- 编写以下 8 条测试函数（每条独立，互不依赖）：

```python
# tests/test_analyst_role_merge.py
# req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））/ chg-04（CLI 兼容 pytest 补强 + escape hatch 文字落地）
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / ".workflow"
MIRROR = ROOT / "src/harness_workflow/assets/scaffold_v2/.workflow"


def test_role_model_map_has_analyst():
    m = yaml.safe_load((LIVE / "context/role-model-map.yaml").read_text(encoding="utf-8"))
    assert m["roles"]["analyst"] == "opus"


def test_role_model_map_legacy_aliases():
    m = yaml.safe_load((LIVE / "context/role-model-map.yaml").read_text(encoding="utf-8"))
    assert m["roles"]["requirement-review"] == "opus"
    assert m["roles"]["planning"] == "opus"


def test_analyst_file_exists_and_sections():
    p = LIVE / "context/roles/analyst.md"
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    # ≥ 6 个二级节（^## ）
    assert body.count("\n## ") >= 5  # 首节不含前导 \n，+1 = 6


def test_analyst_file_mirror_sync():
    live = (LIVE / "context/roles/analyst.md").read_bytes()
    mirror = (MIRROR / "context/roles/analyst.md").read_bytes()
    assert live == mirror


def test_role_model_map_mirror_sync():
    live = (LIVE / "context/role-model-map.yaml").read_bytes()
    mirror = (MIRROR / "context/role-model-map.yaml").read_bytes()
    assert live == mirror


def test_harness_manager_routes_to_analyst():
    body = (LIVE / "context/roles/harness-manager.md").read_text(encoding="utf-8")
    # §3.4 harness requirement / harness change 两行派发目标已改为 analyst
    assert body.count("analyst") >= 2
    # §3.4 行引用 analyst
    assert re.search(r"harness requirement.*analyst", body, re.DOTALL) or \
        re.search(r"加载\s*analyst", body)


def test_technical_director_auto_advance_clause():
    body = (LIVE / "context/roles/directors/technical-director.md").read_text(encoding="utf-8")
    assert "requirement_review" in body and "planning" in body
    assert "自动" in body or "静默" in body
    # escape hatch 4 触发词至少 1 处命中
    assert re.search(r"我要自拆|我自己拆|让我自己拆|我拆 chg", body)


def test_stage_role_flow_exemption_clause():
    body = (LIVE / "context/roles/stage-role.md").read_text(encoding="utf-8")
    assert "req-40" in body
    assert "stage 流转点豁免" in body or "相邻同类型 stage" in body


def test_index_md_has_analyst_row():
    body = (LIVE / "context/index.md").read_text(encoding="utf-8")
    assert "analyst" in body
    assert "roles/analyst.md" in body
    # 合并注释行
    assert "原 requirement-review" in body or "原 planning" in body
```

### Step 3: （可选）analyst.md 补 escape hatch 引用段

- 若 chg-01 analyst.md 未明示 escape hatch 文字，在 "流转规则" 节末追加一行：
  > escape hatch：用户明确说出 `我要自拆` / `我自己拆` / `让我自己拆` / `我拆 chg` 任一触发词时，analyst 退化为只产 `requirement.md` + §5 推荐拆分；详见 `.workflow/context/roles/directors/technical-director.md` §6.2。
- 同步 mirror。

### Step 4: 跑 pytest 全量

- `pytest tests/test_analyst_role_merge.py -v`（本 chg 新增 8 条全部 pass）；
- `pytest -q --tb=no`（全量，现有 67 文件零回归 + 新增 1 文件通过）；
- 对比 Step 1 记录的基线 passed 数，确认只增加 8 条，未减少。

### Step 5: 自检 + 交接

- 更新 chg-04 `session-memory.md`：记录基线 passed 数 + 新增 passed 数；
- 更新 `artifacts/main/requirements/req-40-.../chg-04-变更简报.md`；
- 按硬门禁二追加 `action-log.md`。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_analyst_role_merge.py -v`（8 条全部 passed）
- `pytest -q --tb=no` 全量（passed 数 ≥ 基线 + 8，failed = 0）
- `test -f tests/test_analyst_role_merge.py`（新文件存在）

### 2.2 Manual smoke / integration verification

- 手工跑一遍 `harness status` / `harness next` / `harness change "<test title>"` 并确认 CLI 行为未改（预期 stdout 不变）；
- 肉眼扫 `tests/test_analyst_role_merge.py`，确认每条测试函数独立、不依赖 runtime.yaml 状态；
- 对照 AC-7 / AC-12 逐条核对断言覆盖面。

### 2.3 AC Mapping

- AC-7（CLI 兼容性零回归） -> Step 2（新增 pytest） + Step 4（全量跑通） + 2.1 pytest 断言 + 2.2 CLI 手工 smoke；
- AC-12（escape hatch 路径） -> Step 2（`test_technical_director_auto_advance_clause` 断言）+ Step 3 analyst.md 补引用（可选）+ 2.1 grep 命中 4 触发词之一。

## 3. Dependencies & Execution Order

- **前置依赖**：chg-01（analyst.md live + mirror 落地）+ chg-02（role-model-map + index.md 落地）+ chg-03（harness-manager + technical-director + stage-role 落地）；以上三者全部 PASS 才能启动本 chg；
- **后置依赖**：chg-05（dogfood 活证需要本 chg 的 pytest 断言作为"规约落地"证据）；
- **与 chg-05 关系**：default-pick D-1 = B 串行（chg-04 先于 chg-05），理由：pytest 是"静态证据"，dogfood 是"动态证据"，静态先行可阻塞动态上线；
- **本 chg 内部顺序**：Step 1 → Step 2 → Step 3 → Step 4 → Step 5 强制串行；Step 3 可选（若 chg-01 已明示 escape hatch 引用则跳过）。
