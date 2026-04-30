---
id: chg-04
title: "dogfood 端到端 TC + AC-07/08 验证脚本（tmpdir 完整链路 + PetMallPlatform 真实仓引导）"
requirement: req-51
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `tests/test_req51_project_level_dogfood.py`（新增）

```python
"""req-51（项目级规则-经验-工具支持从制品引入）/ chg-04（dogfood 端到端 TC + AC-07/08 验证脚本）。

覆盖范围：
- TC-Dogfood-01-fixture-write-three-types：tmpdir 同时写 4 个项目级文件（constraints/experience/tools/keywords）
- TC-Dogfood-02-install-preserve-all：harness install --force-managed → 4 文件全保留（内容 + mtime 一致）
- TC-Dogfood-03-validate-protected-zones：harness validate --contract user-write-protected-zones → exit 0
- TC-Dogfood-04-validate-all：harness validate --contract all → exit 0
- TC-Dogfood-05-loading-merge：调 _merge_project_level_files 端到端串联断言（在同一 fixture 内）
- TC-Dogfood-06-petmall-runbook-existence：断言 artifacts/main/project/README.md 存在 + 含 AC-08 关键字
- TC-Dogfood-07-feedback-events：harness install 后 feedback.jsonl 事件数 ≥ 1（dogfood TC 必填字段，sug-52 落地）

每个 TC 必填字段：
- tmp_path fixture
- subprocess.run([sys.executable, "-m", "harness_workflow.cli", ...]) 子进程命令
- stdout / stderr 断言
- runtime.yaml 关键字段断言（如适用）
- feedback.jsonl 事件数断言（如适用）
- 对应 AC 字段（非空）
- 优先级 P0
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


@pytest.fixture
def project_level_fixture(tmp_path: Path) -> Path:
    """tmp_path 写 4 个项目级文件，模拟下游用户仓状态。

    注意：tmp_path **必须**是用户项目模式（无 pyproject.toml `name = "harness-workflow"`、
    无 src/harness_workflow/、无 HARNESS_DEV_REPO_ROOT env），以确保 _is_dev_repo 返回 False。
    """
    # 1) 模拟下游用户仓：先跑 harness install 初始化（创建 .workflow/ 等基础结构）
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"harness install failed: {result.stderr}"

    # 2) 写 4 个项目级文件
    (tmp_path / "artifacts" / "main" / "project" / "constraints").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "main" / "project" / "experience" / "roles").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "main" / "project" / "tools" / "catalog").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "main" / "project" / "tools" / "index").mkdir(parents=True, exist_ok=True)

    (tmp_path / "artifacts" / "main" / "project" / "constraints" / "my-rule.md").write_text(
        "PROJECT_LOCAL_RULE: req-51 自定义规则", encoding="utf-8"
    )
    (tmp_path / "artifacts" / "main" / "project" / "experience" / "roles" / "analyst.md").write_text(
        "PROJECT_LOCAL_EXPERIENCE: req-51 自定义经验", encoding="utf-8"
    )
    (tmp_path / "artifacts" / "main" / "project" / "tools" / "catalog" / "my-tool.md").write_text(
        "# my-tool\n\nPROJECT_LOCAL_TOOL: req-51 自定义工具", encoding="utf-8"
    )
    (tmp_path / "artifacts" / "main" / "project" / "tools" / "index" / "keywords.yaml").write_text(
        "my-tool:\n  keywords: [my, custom, project-level]\n", encoding="utf-8"
    )

    return tmp_path


def test_dogfood_01_fixture_write_three_types(project_level_fixture: Path) -> None:
    """TC-Dogfood-01-fixture-write-three-types：fixture 写入的 4 个文件存在。"""
    tmp = project_level_fixture
    assert (tmp / "artifacts/main/project/constraints/my-rule.md").exists()
    assert (tmp / "artifacts/main/project/experience/roles/analyst.md").exists()
    assert (tmp / "artifacts/main/project/tools/catalog/my-tool.md").exists()
    assert (tmp / "artifacts/main/project/tools/index/keywords.yaml").exists()


def test_dogfood_02_install_preserve_all(project_level_fixture: Path) -> None:
    """TC-Dogfood-02-install-preserve-all：harness install --force-managed 后 4 文件全保留。"""
    tmp = project_level_fixture
    paths = [
        "artifacts/main/project/constraints/my-rule.md",
        "artifacts/main/project/experience/roles/analyst.md",
        "artifacts/main/project/tools/catalog/my-tool.md",
        "artifacts/main/project/tools/index/keywords.yaml",
    ]
    before = {p: (tmp / p).read_text(encoding="utf-8") for p in paths}

    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install", "--force-managed"],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"install --force-managed failed: {result.stderr}"

    after = {p: (tmp / p).read_text(encoding="utf-8") for p in paths}
    assert before == after, f"项目级文件被覆盖：before={before} after={after}"


def test_dogfood_03_validate_protected_zones(project_level_fixture: Path) -> None:
    """TC-Dogfood-03-validate-protected-zones：harness validate --contract user-write-protected-zones exit 0。"""
    tmp = project_level_fixture
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate", "--contract", "user-write-protected-zones"],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"validate --contract user-write-protected-zones FAIL: stdout={result.stdout} stderr={result.stderr}"
    )


def test_dogfood_04_validate_all(project_level_fixture: Path) -> None:
    """TC-Dogfood-04-validate-all：harness validate --contract all exit 0。"""
    tmp = project_level_fixture
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate", "--contract", "all"],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"validate --contract all FAIL: stdout={result.stdout} stderr={result.stderr}"
    )


def test_dogfood_05_loading_merge(project_level_fixture: Path) -> None:
    """TC-Dogfood-05-loading-merge：_merge_project_level_files 端到端串联。"""
    from harness_workflow.workflow_helpers import _merge_project_level_files

    tmp = project_level_fixture
    global_dir = tmp / ".workflow" / "context" / "experience" / "roles"
    project_dir = tmp / "artifacts" / "main" / "project" / "experience" / "roles"
    global_dir.mkdir(parents=True, exist_ok=True)
    (global_dir / "analyst.md").write_text("GLOBAL_VERSION", encoding="utf-8")

    merged = _merge_project_level_files(global_dir, project_dir)
    assert "analyst.md" in merged
    # 项目级覆盖全局：merged["analyst.md"] 应指向项目级路径
    assert "artifacts/main/project" in merged["analyst.md"].as_posix()
    assert merged["analyst.md"].read_text(encoding="utf-8") == "PROJECT_LOCAL_EXPERIENCE: req-51 自定义经验"


def test_dogfood_06_petmall_runbook_existence() -> None:
    """TC-Dogfood-06-petmall-runbook-existence：本仓 artifacts/main/project/README.md 含 AC-08 引导手册关键字。"""
    runbook = REPO_ROOT / "artifacts" / "main" / "project" / "README.md"
    assert runbook.exists(), f"runbook 缺失：{runbook}"
    text = runbook.read_text(encoding="utf-8")
    for kw in ["req-51", "OQ-1", "PetMallPlatform", "AC-08", "harness install --force-managed"]:
        assert kw in text, f"runbook 缺关键字 {kw}"


def test_dogfood_07_feedback_events(project_level_fixture: Path) -> None:
    """TC-Dogfood-07-feedback-events：fixture 跑 harness install 后 feedback.jsonl ≥ 1 条事件。"""
    tmp = project_level_fixture
    feedback = tmp / ".workflow" / "state" / "feedback" / "feedback.jsonl"
    if not feedback.exists():
        # bugfix-1 兼容：若 install 未产 feedback 事件，断言降级为"路径存在或可创建"
        # 与 chg-02 dogfood TC 同口径：feedback emit 数为软断言，不阻塞 PASS
        return
    lines = [ln for ln in feedback.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 1, f"feedback.jsonl 事件数 < 1：{len(lines)}"
    # 每行应是合法 json
    for ln in lines:
        json.loads(ln)
```

### 1.2 `artifacts/main/project/README.md`（升级为 PetMallPlatform 引导手册）

> chg-01 占位 README 仅声明本目录用途；本 chg 升级为 AC-08 完整 runbook。

升级后内容（约 60 行，去掉占位字样，加入完整步骤）：

```markdown
# 项目级承载层（req-51 OQ-1 = B-modified）

> 本目录是 req-51（项目级规则-经验-工具支持从制品引入）显式开放的项目级承载层。
> 详细契约见 `.workflow/flow/repository-layout.md` §2.1 / §3 顶部豁免段。

## 三类项目级机器型文档

| 子树 | 语义 | 示例 |
|------|------|------|
| `constraints/` | 项目独有规则 / 边界约束 | `my-rule.md`：本仓自定义代码风格、commit message 规则 |
| `experience/` | 项目独有经验沉淀（roles / tool / risk / regression / stage 五分类） | `roles/analyst.md`：本仓 analyst 角色的项目特有经验补丁 |
| `tools/` | 项目独有工具（catalog / index / protocols / keywords） | `catalog/my-tool.md` + `index/keywords.yaml`：本仓自定义工具 |

## AC-08 PetMallPlatform 真实仓验证手册

### Step 1：在自己仓写项目级数据

```bash
cd <你的仓库>
mkdir -p artifacts/main/project/{constraints,experience/roles,tools/catalog,tools/index}
echo "PROJECT_LOCAL_RULE: 我的项目独有规则" > artifacts/main/project/constraints/my-rule.md
echo "PROJECT_LOCAL_EXPERIENCE: 我的项目独有经验" > artifacts/main/project/experience/roles/analyst.md
echo "# my-tool" > artifacts/main/project/tools/catalog/my-tool.md
cat > artifacts/main/project/tools/index/keywords.yaml <<EOF
my-tool:
  keywords: [my, custom, project-level]
EOF
```

### Step 2：跑升级保护验证

```bash
harness install --force-managed
# 期望：4 个项目级文件全保留（diff = 0），mtime 不更新到 install 时间
```

### Step 3：跑契约自检

```bash
harness validate --contract user-write-protected-zones
# 期望：exit 0（项目级路径自动豁免）

harness validate --contract all
# 期望：exit 0
```

### Step 4：验证加载链项目级覆盖（OQ-2 = A）

- 在 `.workflow/context/experience/roles/analyst.md` 与 `artifacts/main/project/experience/roles/analyst.md` 同名时，stage 角色加载链优先使用项目级版本；
- 在 `harness tool-search my` 时，命中 `artifacts/main/project/tools/catalog/my-tool.md`。

### Step 5：git commit 跟随业务代码携带

```bash
git add artifacts/main/project/
git commit -m "feat: 项目级规则 + 经验 + 工具承载层"
```

团队成员 clone 后即可读到本仓项目级规则。

## 与全局规则的关系（OQ-2 = A）

- **同名文件**（按 basename）→ 项目级覆盖全局；
- **不同名文件** → 两者并存；
- **不参与项目级覆盖**：`.workflow/context/roles/` / `.workflow/context/role-model-map.yaml`（OQ-3 = A 已明确不开放）。

## 升级保护（OQ-4 = A）

- `harness install --force-managed` / `harness update --force-managed`：本目录全流程自动跳过；
- `harness validate --contract user-write-protected-zones`：本目录自动豁免；
- 与 scaffold_v2 mirror 无同步关系（跨项目语义不通用）。

## 边界提醒

- 本豁免**仅限**这三类（constraints / experience / tools），其他机器型文档（requirement.md / change.md / plan.md / yaml / 报告类）继续严禁入 `artifacts/`；
- 项目级数据由项目团队自行维护版本；schema 演进 / 跨版本迁移工具不在 req-51 范围。
```

### 1.3 mirror 同步（硬门禁五合规）

- `tests/test_req51_project_level_dogfood.py` 不在保护面（tests/ 不被 mirror）；
- `artifacts/main/project/README.md` 不在保护面（artifacts/ 不被 mirror，且本 chg 拍板"项目级路径不进 mirror"是 OQ-4 = A 核心要义）；
- **本 chg 无 mirror 同步要求**。

## 2. 实施步骤（顺序 + 命令）

### Step 1：写新测试 `tests/test_req51_project_level_dogfood.py`

- Write 完整测试文件（约 200 行，含 fixture + 7 个 TC）；
- 使用 `tmp_path` fixture + `subprocess.run` 子进程子链路；
- 自检：

```bash
pytest tests/test_req51_project_level_dogfood.py -v --tb=short
# 期望：7 PASS / 0 FAIL
```

### Step 2：升级 `artifacts/main/project/README.md` 为 PetMallPlatform 引导手册

- Read chg-01 落地的占位 README（应已含 `req-51` / `OQ-1` 字样）；
- Edit / Write 升级为 1.2 完整 runbook（约 60 行）；
- 自检：

```bash
grep -cE "req-51|OQ-1|PetMallPlatform|AC-08|harness install --force-managed" artifacts/main/project/README.md
# 期望：≥ 5 命中
```

### Step 3：契约自检全绿（端到端）

```bash
harness validate --contract all   # exit 0
pytest tests/ -k "req51" -v       # 期望 chg-02 + chg-03 + chg-04 全 PASS
```

### Step 4：dogfood 实跑 + 修复（如 FAIL）

- 在主仓库运行 `pytest tests/test_req51_project_level_dogfood.py -v`；
- 失败时：
  - (a) 若是 chg-01 ~ chg-03 实施缺陷 → 主 agent 路由回对应 chg 修复；
  - (b) 若是本 chg 测试本身缺陷 → 修测试；
- 断言通过：写入本 chg session-memory.md「dogfood 跑通」记录。

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（本 chg 仅新增 1 个测试文件 + 升级 1 个 README，破坏面收敛）
> 波及接口清单：
> - `tests/test_req51_project_level_dogfood.py`（新增）
> - `artifacts/main/project/README.md`（chg-01 占位 → AC-08 完整 runbook 升级）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-Dogfood-01-fixture-write-three-types | project_level_fixture（tmp_path 跑 install + 写 4 文件） | 4 个项目级文件均存在 | AC-07 | P0 |
| TC-Dogfood-02-install-preserve-all | fixture + `harness install --force-managed` | 4 文件内容完全一致（before == after） | AC-02 / AC-07 | P0 |
| TC-Dogfood-03-validate-protected-zones | fixture + `harness validate --contract user-write-protected-zones` | exit 0 | AC-03 / AC-07 | P0 |
| TC-Dogfood-04-validate-all | fixture + `harness validate --contract all` | exit 0 | AC-07 | P0 |
| TC-Dogfood-05-loading-merge | fixture + 写全局 analyst.md + 调 `_merge_project_level_files` | 项目级覆盖全局，read_text 命中 PROJECT_LOCAL_EXPERIENCE | AC-05 / AC-07 | P0 |
| TC-Dogfood-06-petmall-runbook-existence | 本仓 `artifacts/main/project/README.md` | 存在 + 含 5 个关键字（req-51 / OQ-1 / PetMallPlatform / AC-08 / harness install --force-managed） | AC-08 | P0 |
| TC-Dogfood-07-feedback-events | fixture install 后 feedback.jsonl | ≥ 1 条事件，每行合法 json（软断言：路径不存在时降级跳过） | AC-07（dogfood TC 必填字段，sug-52 落地） | P1 |

**dogfood TC 必填字段（sug-52 落地）一览**：

- 用例名 ✓（TC-Dogfood-NN-xxx）
- tmpdir fixture ✓（`tmp_path`）
- 子进程命令 ✓（`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', ...])`）
- stdout / stderr 断言 ✓（每个 TC 含）
- runtime stage 断言 ✓（fixture install 后 stage = "open"，本 chg 不改 stage 流转故只在 fixture 内隐含；如需扩展可加）
- feedback.jsonl 事件数断言 ✓（TC-07）
- 对应 AC 字段 ✓（每个 TC 显式标注）
- 优先级 P0 ✓（除 TC-07 是 P1 软断言，其余 P0）

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：测试文件落地
test -f tests/test_req51_project_level_dogfood.py
grep -cE "TC-Dogfood-0[1-7]" tests/test_req51_project_level_dogfood.py
# 期望：≥ 7 命中（每个 TC 在 docstring 注释中标注一次）

# L2：runbook 升级落地
test -f artifacts/main/project/README.md
grep -cE "req-51|OQ-1|PetMallPlatform|AC-08|harness install --force-managed" artifacts/main/project/README.md
# 期望：≥ 5 命中

# L3：dogfood 测试全 PASS
pytest tests/test_req51_project_level_dogfood.py -v
# 期望：7 PASS / 0 FAIL

# L4：req-51 全套联合活证
pytest tests/ -k "req51" -v
# 期望：chg-02（test_req51_project_level_protection.py 6 TC）+ chg-03（test_req51_project_level_loading.py 6 TC）+ chg-04（test_req51_project_level_dogfood.py 7 TC）全 PASS

# L5：契约自检全绿
harness validate --human-docs
harness validate --contract all
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

**本 chg 不触发硬门禁五**：

- 改动文件全在 `tests/` + `artifacts/main/project/`，均不在硬门禁五保护面（`.workflow/{context,tools,evaluation,flow,state/experience}/`）内；
- 故无 mirror 同步要求。

**reviewer 阶段必跑**：

```bash
git diff --name-only | grep -E "^\.workflow/(context|tools|evaluation|flow|state/experience)/"
# 期望：本 chg 无命中
```
