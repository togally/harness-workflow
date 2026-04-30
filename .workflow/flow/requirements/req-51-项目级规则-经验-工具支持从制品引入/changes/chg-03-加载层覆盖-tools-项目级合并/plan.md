---
id: chg-03
title: "加载层：role-loading-protocol 项目级合并段 + tools-manager 项目级合并/优先匹配"
requirement: req-51
operation_type: plan
---

# Change Plan

## 1. Scope 与变更点（精确文件 / 行号 / 函数名）

### 1.1 `.workflow/context/roles/role-loading-protocol.md`（live）

**变更点 A：新增 Step 7.6**（紧接现有 Step 7.5 模型一致性自检段后，约第 124 行 `---` 分隔符前插入新段）

```markdown
### Step 7.6：项目级覆盖加载（req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并））

> 溯源：req-51 OQ-2 = A（项目级覆盖全局）/ OQ-3 = A（仅 constraints / experience / tools 三类，不含 roles/）。

加载完 Step 7 全局附加上下文后、Step 7.5 模型一致性自检前，所有角色（含顶级角色 Director、辅助角色、stage 角色）**必须**额外按项目级覆盖加载链处理：

#### 项目级承载路径

固定为 `artifacts/{branch}/project/{constraints,experience,tools}/`（chg-01（契约底座-artifacts-project-豁免）已在 `repository-layout.md` §2.1 / §3 顶部豁免段权威落定，OQ-1 = B-modified）。

#### 加载顺序

| 阶段 | 路径 | 处理方式 |
|------|------|---------|
| 1 | `.workflow/context/constraints/` / `.workflow/context/experience/` / `.workflow/tools/` | 先按 Step 7 全局加载链加载（不变） |
| 2 | `artifacts/{branch}/project/constraints/` / `experience/` / `tools/` | 后加载项目级版本，**文件级覆盖**全局同名文件 |

#### 覆盖语义（OQ-2 = A）

- **同名文件**（按 basename 匹配，如 `experience/roles/analyst.md`）→ 项目级覆盖全局（项目级生效，全局忽略）；
- **不同名文件** → 两者并存（全局 + 项目级合并）；
- **段落级 merge 不支持**（markdown 无结构化 schema，merge 复杂度高，OQ-2 default-pick 已明确"覆盖而非合并"）。

#### 不参与项目级覆盖的子类（OQ-3 = A）

- `.workflow/context/roles/` 角色规范（项目级化风险高，下次 req 单独评估）；
- `.workflow/context/role-model-map.yaml` 模型映射（影响成本与质量，下游一般不需要改）。

#### fallback

- 项目级路径不存在 → 静默跳过，**不报错**（与 task_context_index 回退语义一致）；
- 项目级路径存在但内容为空 / 损坏 → 记录到 `session-memory.md`"待处理捕获问题"段，不阻塞加载。

#### 自检（角色加载完成后）

- 在首条输出（与硬门禁三自我介绍并列）追加一句："项目级加载：{命中数 / 0}（路径：artifacts/{branch}/project/）"，便于用户感知是否生效。
```

**变更点 B：流程速查图更新**（约第 132 行 mermaid 图）

在 `加载自己的角色文件` → `按需加载附加上下文（evaluation、experience、constraints 等）` → `模型一致性自检（Step 7.5）` 之间插入新节点：

```
按需加载附加上下文（Step 7）
    ↓
项目级覆盖加载（Step 7.6，artifacts/{branch}/project/）
    ↓
模型一致性自检（Step 7.5）
    ↓
[开始执行]
```

### 1.2 `.workflow/context/roles/tools-manager.md`（live）

**变更点 C：Step 2 顶部插入项目级合并段**（约第 14 行 `### Step 2: 读取本地工具索引` 章节标题后）

```markdown
### Step 2: 读取本地工具索引

#### 2.0 项目级合并（req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并））

> 溯源：req-51 OQ-2 = A（项目级覆盖全局）/ OQ-3 = A（tools 在三类项目级化范围内）。

读取全局 `.workflow/tools/index/keywords.yaml` 前，**先**检测项目级路径：

```python
project_keywords = artifacts/{branch}/project/tools/index/keywords.yaml
project_ratings  = artifacts/{branch}/project/tools/ratings.yaml
project_catalog  = artifacts/{branch}/project/tools/catalog/
project_protocols = artifacts/{branch}/project/tools/protocols/
```

合并语义：

| 资源 | 全局路径 | 项目级路径 | 合并策略 |
|------|---------|-----------|---------|
| `keywords.yaml` | `.workflow/tools/index/keywords.yaml` | `artifacts/{branch}/project/tools/index/keywords.yaml` | 项目级 dict 覆盖全局 dict（同 `tool_id` key 项目级胜出） |
| `ratings.yaml` | `.workflow/tools/ratings.yaml` | `artifacts/{branch}/project/tools/ratings.yaml` | 同上 |
| `catalog/{tool_id}.md` | `.workflow/tools/catalog/` | `artifacts/{branch}/project/tools/catalog/` | 优先项目级，未命中 fallback 全局 |
| `protocols/{name}.md` | `.workflow/tools/protocols/` | `artifacts/{branch}/project/tools/protocols/` | 优先项目级，未命中 fallback 全局 |

fallback：

- 项目级 `keywords.yaml` / `ratings.yaml` / `catalog/` / `protocols/` 任一缺失 → 静默跳过该资源，不影响其他资源加载；
- 全部缺失（`artifacts/main/project/tools/` 整目录不存在）→ 退化为 Step 2 现有"仅读全局"行为（向后兼容）。

输出（`Step 4 格式化输出` 的 `**toolsManager 查询结果**`）若推荐的工具来自项目级，必须在 `**catalog**` 字段标注项目级路径（`artifacts/main/project/tools/catalog/{tool_id}.md`），便于主 agent 识别工具来源。

#### 2.1 全局加载（保持不变）

读取全局 `.workflow/tools/index/keywords.yaml` 与 `.workflow/tools/ratings.yaml` ...（原有 Step 2 内容保持不变）
```

### 1.3 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md`（mirror）

- **完全镜像变更点 A / B**，与 live 字节级一致；
- 硬门禁五合规：与 live 必须同一 commit ship。

### 1.4 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md`（mirror）

- **完全镜像变更点 C**，与 live 字节级一致。

### 1.5 `tests/test_req51_project_level_loading.py`（新增）

```python
"""req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并）dogfood 测试。

覆盖范围：
- TC-01-loading-protocol-step76-grep：role-loading-protocol.md 含 "Step 7.6：项目级覆盖加载" 段
- TC-02-tools-manager-step20-grep：tools-manager.md 含 "项目级合并" 段，明确路径
- TC-03-experience-override-by-name：tmp_path 写 .workflow/context/experience/roles/analyst.md（content="GLOBAL"）+ artifacts/main/project/experience/roles/analyst.md（content="PROJECT_LOCAL"），按加载链解析后项目级版本生效（PROJECT_LOCAL 命中）
- TC-04-tools-keywords-merge：tmp_path 写 .workflow/tools/index/keywords.yaml（含 tool_id "global-tool"）+ artifacts/main/project/tools/index/keywords.yaml（含 tool_id "global-tool" + "project-tool"），按合并语义解析后 "global-tool" 用项目级版本 + "project-tool" 来自项目级
- TC-05-fallback-when-project-missing：tmp_path 不创建 artifacts/main/project/，加载链解析仍正常（无项目级也不报错）
- TC-06-mirror-byte-equal：scaffold_v2 mirror 与 live 字节比对 silent
"""
```

注：因 role-loading-protocol.md 是文档型契约（实际加载逻辑由 agent 按文档执行，无 Python helper），TC-01 / TC-02 用 grep 验证文档落地；TC-03 / TC-04 / TC-05 通过模拟一个最小 helper（如 `harness_workflow.workflow_helpers._merge_project_level_files(global_path, project_path)`）验证合并语义——若 helper 不存在，本 chg 同时新增该 helper（详见 1.6）。

### 1.6 `src/harness_workflow/workflow_helpers.py` 新增 helper（可选，见下方决策点）

**决策点 1（default-pick = A）**：是否新增 Python helper `_merge_project_level_files(global_root, project_root, subtree)` 用于测试断言？

| 选项 | 决策 |
|------|------|
| **A**（default-pick） | 新增 helper（30 行内），简单实现"按文件名 dict merge + 项目级覆盖"，不接入 install_repo 主流程，仅供测试与未来扩展用 |
| B | 不新增 helper，TC-03/04/05 用 Python 直接 fixture 模拟 merge 行为，但每个测试都要重写一遍 merge 逻辑 |

**default-pick = A**。理由：30 行 helper 既支撑测试，又为未来 OQ-3 = B（roles/ 项目级化）扩展提供基础设施；不接入主流程意味着不影响 install / update / validate 行为，零回归风险。

新增 helper 位置：`src/harness_workflow/workflow_helpers.py` 文件末尾（紧接 `raise_harness_block` 后）。

```python
def _merge_project_level_files(
    global_dir: Path,
    project_dir: Path,
) -> dict[str, Path]:
    """req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并）：
    把全局子树与项目级子树按 basename 合并，同名时项目级覆盖全局。

    返回：dict[basename, Path]，basename 为相对 global_dir / project_dir 的路径字符串。

    fallback：
    - global_dir 不存在 → 仅返回 project_dir 内容（如有）；
    - project_dir 不存在 → 仅返回 global_dir 内容（向后兼容）；
    - 两者都不存在 → 返回 {}。

    本 helper 不接入 install_repo / update_repo 主流程；仅供 role-loading-protocol Step 7.6 与
    tools-manager Step 2.0 的加载链按文档 SOP 解析使用，以及 tests/test_req51_project_level_loading.py 断言。
    """
    merged: dict[str, Path] = {}
    if global_dir.exists():
        for f in global_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(global_dir).as_posix()
                merged[rel] = f
    if project_dir.exists():
        for f in project_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(project_dir).as_posix()
                merged[rel] = f  # 同名覆盖全局
    return merged
```

## 2. 实施步骤（顺序 + 命令）

### Step 1：编辑 live `role-loading-protocol.md`

- Edit 在 Step 7.5 段后插入新 Step 7.6（变更点 A），同步更新流程速查图（变更点 B）；
- 自检：

```bash
grep -n "Step 7.6：项目级覆盖加载" .workflow/context/roles/role-loading-protocol.md
# 期望：1 行命中
grep -c "artifacts/{branch}/project/" .workflow/context/roles/role-loading-protocol.md
# 期望：≥ 2（Step 7.6 段 + 流程图）
```

### Step 2：编辑 live `tools-manager.md`

- Edit 在 Step 2 标题后插入 Step 2.0 项目级合并段（变更点 C）；
- 不破坏 Step 1 / Step 3 / Step 4 等其他段；
- 自检：

```bash
grep -n "项目级合并" .workflow/context/roles/tools-manager.md
# 期望：1 行命中
grep -c "artifacts/main/project/tools/" .workflow/context/roles/tools-manager.md
# 期望：≥ 4（4 张资源表行）
```

### Step 3：同 commit 同步 mirror（硬门禁五合规）

- 镜像 Step 1 / Step 2 改动到两个 scaffold_v2 mirror 文件；
- 自检：

```bash
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
diff -q .workflow/context/roles/tools-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md
# 期望：双双 silent
```

### Step 4：新增 helper `_merge_project_level_files`

- Edit `src/harness_workflow/workflow_helpers.py` 文件末尾追加 helper（约 30 行）；
- 自检：

```bash
grep -n "def _merge_project_level_files" src/harness_workflow/workflow_helpers.py
# 期望：1 行命中
python3 -c "from harness_workflow.workflow_helpers import _merge_project_level_files; print(_merge_project_level_files.__doc__)"
# 期望：打印 docstring 含 "req-51"
```

### Step 5：写新测试 `tests/test_req51_project_level_loading.py`

- 6 个 TC，使用 `tmp_path` fixture + `_merge_project_level_files` helper 直调 + grep 断言文档落地；
- 不依赖子进程子链路（与 chg-02 dogfood TC 区分），单元测试粒度；
- 自检：

```bash
pytest tests/test_req51_project_level_loading.py -v
# 期望：6 PASS / 0 FAIL
```

### Step 6：契约自检全绿

```bash
harness validate --contract all   # exit 0
pytest tests/ -k "req51" -v       # 期望全 PASS
```

## 3. 测试用例设计（≥ 3 用例）

> regression_scope: targeted（本 chg 改 2 个文档 + 2 个 mirror + 1 个 helper + 1 个新测试，破坏面收敛）
> 波及接口清单：
> - `.workflow/context/roles/role-loading-protocol.md`
> - `.workflow/context/roles/tools-manager.md`
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md`
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md`
> - `src/harness_workflow/workflow_helpers.py`（_merge_project_level_files 末尾追加）
> - `tests/test_req51_project_level_loading.py`（新增）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-loading-protocol-step76-grep | grep `role-loading-protocol.md` | 含 "Step 7.6：项目级覆盖加载" 标题；含 "artifacts/{branch}/project/" ≥ 2 命中；含 "OQ-2 = A" / "OQ-3 = A" 引用 | AC-05 | P0 |
| TC-02-tools-manager-merge-section | grep `tools-manager.md` | 含 "项目级合并" 标题；含 "artifacts/main/project/tools/" ≥ 4 命中（4 张资源表行）；含 "OQ-2 = A" 引用 | AC-06 | P0 |
| TC-03-experience-override-by-name | tmp_path 写 `.workflow/context/experience/roles/analyst.md`（content="GLOBAL"）+ `artifacts/main/project/experience/roles/analyst.md`（content="PROJECT_LOCAL"），调 `_merge_project_level_files(global_dir, project_dir)` | 返回 dict 中 `roles/analyst.md` 的 Path 指向**项目级路径**；读取该 Path 内容 == "PROJECT_LOCAL" | AC-05 | P0 |
| TC-04-tools-keywords-merge | tmp_path 写 `.workflow/tools/index/keywords.yaml`（含 `global-tool: [k1, k2]`）+ `artifacts/main/project/tools/index/keywords.yaml`（含 `global-tool: [k1-overridden]` + `project-tool: [k3]`），调 `_merge_project_level_files(global_dir, project_dir)` | 返回 dict 含 `index/keywords.yaml` Path 指向项目级（覆盖语义）；下游测试可独立 yaml.load 验证 dict merge | AC-06 | P0 |
| TC-05-fallback-when-project-missing | tmp_path 仅写 `.workflow/context/experience/roles/analyst.md`（无 artifacts/main/project/），调 `_merge_project_level_files(global_dir, project_dir)` | 返回 dict 中 `roles/analyst.md` Path 指向全局路径；不报错；无 KeyError | AC-05（fallback） | P0 |
| TC-06-fallback-when-global-missing | tmp_path 仅写 `artifacts/main/project/experience/roles/custom.md`，调 helper | 返回 dict 中 `roles/custom.md` Path 指向项目级；全局 dir 不存在不报错 | AC-05（fallback） | P1 |
| TC-07-mirror-byte-equal | live + mirror 字节比对 | `diff -q` 对 role-loading-protocol.md 与 tools-manager.md 双双 silent | AC-04（mirror 同步） | P0 |

## 4. 验收 lint 命令字面（grep / pytest，executing 不得偷换关键词）

```bash
# L1：role-loading-protocol Step 7.6 落地
grep -n "Step 7.6：项目级覆盖加载" .workflow/context/roles/role-loading-protocol.md
grep -c "artifacts/{branch}/project/" .workflow/context/roles/role-loading-protocol.md
grep -nE "OQ-2 = A|OQ-3 = A" .workflow/context/roles/role-loading-protocol.md

# L2：tools-manager Step 2.0 项目级合并段
grep -n "项目级合并" .workflow/context/roles/tools-manager.md
grep -c "artifacts/main/project/tools/" .workflow/context/roles/tools-manager.md

# L3：scaffold mirror 字节级同源
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
diff -q .workflow/context/roles/tools-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md

# L4：helper 落地
grep -n "def _merge_project_level_files" src/harness_workflow/workflow_helpers.py
python3 -c "from harness_workflow.workflow_helpers import _merge_project_level_files; assert callable(_merge_project_level_files)"

# L5：新测试全 PASS
pytest tests/test_req51_project_level_loading.py -v
# 期望：≥ 6 PASS / 0 FAIL

# L6：契约自检全绿
harness validate --contract all
pytest tests/ -k "req51" -v   # 期望 chg-02 + chg-03 测试全 PASS
```

## 5. scaffold_v2 mirror 同步清单（硬门禁五）

| live 文件 | mirror 文件 | 同步动作 |
|-----------|------------|---------|
| `.workflow/context/roles/role-loading-protocol.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md` | 同 commit 镜像变更点 A / B |
| `.workflow/context/roles/tools-manager.md` | `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md` | 同 commit 镜像变更点 C |

**reviewer 阶段必跑**：

```bash
diff -q .workflow/context/roles/role-loading-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/role-loading-protocol.md
diff -q .workflow/context/roles/tools-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/tools-manager.md
# 双双 silent；任一非 silent → reviewer FAIL
```

**注意**：

- `src/harness_workflow/workflow_helpers.py` 不在硬门禁五保护面，无需 mirror（与 chg-02 同口径）；
- `tests/test_req51_project_level_loading.py` 不在保护面。
