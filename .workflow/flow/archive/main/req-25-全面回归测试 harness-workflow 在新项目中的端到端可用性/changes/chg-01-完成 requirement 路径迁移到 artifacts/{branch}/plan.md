# Change Plan

## 1. Development Steps

### Step 1：定位并读取 9 处硬编码

**目标**：为每处硬编码确认当前函数名、行号、完整上下文，形成"改前快照"。

| # | 行号 | 函数 | 当前逻辑摘要 | 分类 |
|---|------|------|-------------|------|
| 1 | 2052 | `_required_dirs(root)` | 返回 init 时需要创建的目录列表，包含 `.workflow/flow/requirements`；被 `init_repo` 调用 | **结构性**（init 时创建）|
| 2 | 2863 | `_next_req_id(root)` | 扫描 `state/requirements` + `.workflow/flow/requirements` 内 `req-NN` 目录名，取最大编号 +1 | **扫描类**（读多源）|
| 3 | 3134 | `create_suggest_bundle`（合并建议清单追加至 requirement.md） | 基于 `req_id + title` 拼 `.workflow/flow/requirements/{req_id}-{title}`，再读写 `requirement.md` | **定位新 req**（与 create_requirement 写入端不一致）|
| 4 | 3377 | `create_regression` | 通过 `resolve_requirement_reference(.workflow/flow/requirements, req_ref, language)` 解析当前 req 的目录；`3379` fallback 为 `.workflow/flow/regressions` | **解析类**（要改 root 参数）|
| 5 | 3530 | `rename_requirement` | `requirements_dir = .workflow/flow/requirements` → `resolve_requirement_reference(requirements_dir, current_name, language)` → `shutil.move` | **解析+移动**（P0-05 直接根因）|
| 6 | 3562 | `rename_change` | 同 #4，拿到 req_dir 后再定位其下 `changes/` | **解析类**（P0-05 根因之一）|
| 7 | 3782 | `archive_requirement` | `requirements_dir = .workflow/flow/requirements` → 解析 req_dir → `shutil.move` 到 `archive_base` | **解析类**（P0-04 主根因）|
| 8 | 3830 | `archive_requirement` 残留清理 | `residual_req_dir = requirements_dir / req_dir.name`，if exists → `rmtree` | **变量复用**（随 #7 同步修复，无独立改动）|
| 9 | 3897 | `validate_requirement` | `requirements_dir = .workflow/flow/requirements` → 解析 → 遍历 changes 校验 | **解析类**（P0-03 主根因）|

**附加（P1-06 纳入范围）**：

| # | 行号 | 函数 | 当前逻辑 |
|---|------|------|----------|
| 10 | 3791 | `archive_requirement` | `archive_base = root / ".workflow" / "flow" / "archive"` | **输出根**（P1-06）|

**执行动作**：Read 每处上下文 ±10 行，确认没有行号偏移；若行号已随代码演进偏移，以函数名为准。

---

### Step 2：设计 `resolve_requirement_root` 签名与降级策略

**函数签名**：
```python
def resolve_requirement_root(root: Path) -> Path:
    """返回当前仓库 requirement 产出的根目录，按优先级降级：
    1. artifacts/{branch}/requirements（branch 由 _get_git_branch 解析，失败时 'main'）
    2. artifacts/requirements（兼容未启用 branch 的过渡形态）
    3. .workflow/flow/requirements（legacy，仅老仓兼容；降级时 stderr 告警，
       并提示用户运行 `harness migrate requirements`）
    选择策略：返回"目录存在且实质性非空"的最高优先级路径；
    若全部不存在或全部仅含噪声文件，返回第 1 级路径（让调用方负责创建）。
    """
```

**"实质性非空"过滤规则**（用户决策 Q1：做过滤）：

- 引入常量 `_REQUIREMENT_ROOT_NOISE_FILENAMES: frozenset[str] = frozenset({".DS_Store", ".gitkeep", "Thumbs.db", ".keep"})`
- 放置位置：与 helper 相邻的模块级常量（便于后续扩展，且避免每次调用重新构造集合）
- "实质性非空" = `any(child.name not in _REQUIREMENT_ROOT_NOISE_FILENAMES for child in p.iterdir())`
- 仅过滤**直接子节点**的噪声文件名，不递归（避免性能问题）；噪声目录暂不处理，列表保持可扩展

**降级决策表**：

| artifacts/{branch}/requirements | artifacts/requirements | .workflow/flow/requirements | 返回值 | 告警 |
|---|---|---|---|---|
| 实质性非空 | - | - | 第 1 级 | 无 |
| 空 / 仅噪声 | 实质性非空 | - | 第 2 级 | stderr: "[harness] warning: using legacy path artifacts/requirements; run `harness migrate requirements`" |
| 空 / 仅噪声 | 空 / 仅噪声 | 实质性非空 | 第 3 级 | stderr: "[harness] warning: using legacy path .workflow/flow/requirements; run `harness migrate requirements`" |
| 全部空 / 仅噪声 | - | - | 第 1 级（创建时落到新路径） | 无 |

**为什么降级存在但不"强切"到第 1 级？** 老用户（req-27 之前的仓库）数据还在 `.workflow/flow/requirements`，helper 如果直接返回第 1 级，rename/archive 会查不到他们的历史目录。降级保证老仓**读操作**不炸。

**为什么降级不是"永久兜底"？** 本 change 同步提供 `harness migrate requirements` 命令（Step 7）。降级告警文案中明确提示用户运行该命令，一次性把 legacy 数据搬到第 1 级路径；迁移后 helper 自然返回第 1 级，不再触发降级。长期上，legacy 路径只作为"未迁移状态"的应急兜底，不作为支持的运行形态。

**配套 helper**（P1-06 用）：

```python
def resolve_archive_root(root: Path) -> Path:
    """返回归档产出根目录。
    新规：artifacts/{branch}/archive
    legacy：.workflow/flow/archive（同样降级，降级时告警，提示运行迁移命令）
    """
```

---

### Step 3：实现 helper

**落点**：`src/harness_workflow/workflow_helpers.py`，插入位置在 `_get_git_branch`（约 3763 行）**之后**、`archive_requirement`（约 3780 行）**之前**。理由：
1. 紧邻 `_get_git_branch`，便于阅读时理解依赖关系
2. 在第一个使用点（`archive_requirement`）之前定义，避免 Python 的 NameError（Path 注解 + 字符串延迟求值虽然可以绕过，但就近原则更清晰）
3. 不单独新建文件，避免增加 import 成本；`workflow_helpers.py` 已是 helper 聚合文件

**实现要点**：
- 使用 `sys.stderr` 打印告警（`print(..., file=sys.stderr)`），需在文件顶部补 `import sys`（若已有则复用）
- "实质性非空"判断：过滤 `_REQUIREMENT_ROOT_NOISE_FILENAMES` 后仍存在子项；短路 `p.exists()` 再 iterdir，避免无谓 IO
- branch 解析复用 `_get_git_branch(root)`，失败时兜底 `"main"`
- helper 不做 `mkdir`，创建责任留给调用方（与现有 `create_requirement:3174` 风格一致）
- 噪声文件名常量提升为模块级，便于未来扩展（风险表记录为可扩展常量）

**伪代码**：
```python
_REQUIREMENT_ROOT_NOISE_FILENAMES: frozenset[str] = frozenset({
    ".DS_Store",
    ".gitkeep",
    "Thumbs.db",
    ".keep",
})


def _has_substantive_content(p: Path) -> bool:
    """目录存在且过滤噪声后仍有子节点。"""
    if not p.exists():
        return False
    return any(
        child.name not in _REQUIREMENT_ROOT_NOISE_FILENAMES
        for child in p.iterdir()
    )


def resolve_requirement_root(root: Path) -> Path:
    branch = _get_git_branch(root) or "main"
    primary = root / "artifacts" / branch / "requirements"
    secondary = root / "artifacts" / "requirements"
    legacy = root / ".workflow" / "flow" / "requirements"

    if _has_substantive_content(primary):
        return primary
    if _has_substantive_content(secondary):
        print(
            f"[harness] warning: using legacy path "
            f"{secondary.relative_to(root)}; "
            f"run `harness migrate requirements` to consolidate.",
            file=sys.stderr,
        )
        return secondary
    if _has_substantive_content(legacy):
        print(
            f"[harness] warning: using legacy path "
            f"{legacy.relative_to(root)}; "
            f"run `harness migrate requirements` to consolidate.",
            file=sys.stderr,
        )
        return legacy
    return primary  # 新仓 / 空仓 / 仅噪声 → 落到新路径
```

---

### Step 4：逐处替换硬编码

**替换顺序**：按影响面从小到大，便于 bisect。

| 执行序 | 修改点 | 预期行为变化 |
|-------|-------|-------------|
| 4.1 | 顶部新增 `import sys` | 无行为变化；仅为 helper 告警做准备 |
| 4.2 | 新增 `resolve_requirement_root` + `resolve_archive_root`（Step 3 已写就） | 无调用 → 无行为变化 |
| 4.3 | `3897 validate_requirement` → 用 helper | `harness validate` 能找到新路径下的 req；老仓（legacy 目录）也能工作，带告警 |
| 4.4 | `3530 rename_requirement` + `3562 rename_change` → 用 helper | `harness rename` 三种引用形式（id / title / 完整目录）全部成功 |
| 4.5 | `3782 archive_requirement` → 用 helper；`3830` 随 `requirements_dir` 变量复用自动对齐 | `harness archive` 能归档新路径下的 req；残留清理不再指向 legacy |
| 4.6 | `3791 archive_base` → `resolve_archive_root(root)`（若纳入 P1-06）| `archive_requirement` 产出落到 `artifacts/{branch}/archive` |
| 4.7 | `3377 create_regression` + `3379` fallback → 用 helper | `harness regression` 可基于新路径 req 创建 regression |
| 4.8 | `3134 create_suggest_bundle` → 用 helper | suggest 合并后追加清单能正确找到新建的 req.md |
| 4.9 | `2863 _next_req_id` → 追加扫描 `resolve_requirement_root(root)` 返回的目录 | 编号递增同时看 state + legacy + 新路径，避免 id 回滚 |
| 4.10 | `2052 _required_dirs` → 追加 `artifacts/{branch}/requirements`（不删除 legacy）| init 后两套目录同时存在，过渡期无破坏 |

**每步完成后**：
- 对修改的函数跑最小 smoke（手动构造场景或用 `python -m py_compile` 先确认语法）
- 记录"哪些现有用例可能受影响"到 session-memory.md

---

### Step 5：helper 单元级 / 场景级自测

**目标**：在代码写就、进入大测试床重跑之前，单独验证 helper 降级与噪声过滤行为，避免测试床排障时把 helper bug 与上层 bug 混淆。

**执行动作**：
1. 构造临时仓（`tmp_path`）三级目录矩阵：
   - 仅第 1 级有 req 目录
   - 仅第 2 级有 req 目录
   - 仅第 3 级有 req 目录
   - 第 1 级只含 `.DS_Store` / `.gitkeep`，第 2 级有 req 目录 → 必须返回第 2 级
   - 全部不存在 → 返回第 1 级
2. 对 `resolve_archive_root` 做同等矩阵（两级即可）
3. 断言：返回值、stderr 是否包含预期告警字符串、是否提示 `harness migrate requirements`

本步骤可以用 `pytest` 或临时脚本实现（若仓库无测试目录，以脚本形式置于 `regression-logs/chg-01/helper-selftest.py`）。

---

### Step 6：P1-06 archive_base 对齐（纳入本 change）

**前置**：Step 4.6 已把 `3791 archive_base` 切到 `resolve_archive_root(root)`。

**本步骤动作**：
1. 补全 `resolve_archive_root` 的降级告警（与 `resolve_requirement_root` 对齐，同样提示运行迁移命令）
2. 追加测试：手动 archive 一个 req，确认产物落到 `artifacts/{branch}/archive/<req-NN-title>/`
3. 若老仓已有 `.workflow/flow/archive/` 内容，确认 helper 能读到（legacy 降级生效）
4. 记录：`_required_dirs` 是否需要同步加 `artifacts/{branch}/archive` 占位 — 决策为**不加**（archive 是运行时产物，init 时不应预创建，避免污染 tree）

**回滚与记录**：若 archive 验证失败，只撤 `3791` 一行与 `resolve_archive_root` 定义，主 9 处修复不受影响。**一旦独立回滚，executing 阶段必须在 chg-01 的 completion.md 中明确记录"archive_base 未对齐"作为延期项**（用户决策 Q2）。

---

### Step 7：实现 `harness migrate requirements` 命令（用户决策 Q3）

**目标**：为老仓提供一次性迁移入口，把 `.workflow/flow/requirements/*` 与 `artifacts/requirements/*` 搬到 `artifacts/{branch}/requirements/`，配合 Step 2 的降级告警文案形成"告警 → 动作"闭环。

#### 7.1 CLI 入口

- **命令形式**：`harness migrate requirements [--dry-run]`
- **注册位置**：CLI 入口层（通常在 `src/harness_workflow/cli.py` 或等价文件的 argparse / click 注册处）；具体行号需在 executing 阶段通过 Read 定位（诊断未覆盖 CLI 层行号）
- **命名理由**：动词 `migrate` + 资源 `requirements`，与现有 `harness archive <req>` / `harness rename <req> <new>` 的资源定位风格一致；为后续扩展（如 `harness migrate archive`）预留命名空间

#### 7.2 helper 函数设计

在 `workflow_helpers.py` 中新建：

```python
def migrate_requirements(root: Path, dry_run: bool = False) -> int:
    """把 legacy 路径下的 requirement 目录搬到 artifacts/{branch}/requirements。

    扫描源（按优先级）：
      1. root / ".workflow" / "flow" / "requirements"
      2. root / "artifacts" / "requirements"
    目标：
      root / "artifacts" / {branch} / "requirements"

    行为：
      - 源目录不存在或为空 → 跳过
      - 目标已有同名目录 → 报错、不覆盖，计入冲突
      - dry_run=True → 仅打印计划，不落盘
      - 返回 rc：0 无冲突且完成；非 0 表示存在冲突
    """
```

#### 7.3 扫描与搬迁策略

1. 解析 `branch = _get_git_branch(root) or "main"`
2. 目标目录 `dst_root = root / "artifacts" / branch / "requirements"`；非 dry-run 时先 `mkdir(parents=True, exist_ok=True)`
3. 依次遍历两个源：
   - `src_legacy = root / ".workflow" / "flow" / "requirements"`
   - `src_mid = root / "artifacts" / "requirements"`
4. 对每个源目录下的直接子目录（跳过噪声文件，复用 Step 2 的 `_REQUIREMENT_ROOT_NOISE_FILENAMES`）：
   - 计算目标路径 `dst = dst_root / src_child.name`
   - **如果 `dst == src_child`**（新仓 branch=main 且 src 已是目标） → 跳过（幂等）
   - **如果 `dst.exists()`** → 记为冲突，stderr 输出 `[migrate] conflict: <dst> already exists, skipped`，不覆盖
   - **否则**：stdout 输出 `[migrate] <src_child> -> <dst>`；非 dry-run 时 `shutil.move(src_child, dst)`
5. 迁移完成后，如果源目录变为空（过滤噪声后无子项） → 保留空目录（不自动 rmtree，避免 `_required_dirs` 后续 init 时重建空目录报错）
6. 返回 rc：冲突数 == 0 → 0；否则返回 1 并在 stdout 打印汇总（`[migrate] done: N migrated, M skipped (conflict), K dry-run`）

#### 7.4 冲突策略细节

- 冲突仅在"目标已存在同名子目录"时触发；源与目标路径指向同一物理目录（幂等场景）不算冲突
- 冲突后不中止整体迁移：继续处理后续条目，最终按是否有冲突决定 rc
- 冲突提示文案必须包含"请人工核对 `<src>` 与 `<dst>` 的内容差异后合并或重命名"
- 禁止在迁移命令内部实现"自动合并"或"时间戳冲突后缀"——用户决策明确要求冲突时停手

#### 7.5 幂等性

- 二次运行时，源目录已为空（过滤噪声后） → 所有条目跳过 → rc=0，打印 `[migrate] nothing to migrate`
- 对于 src == dst 的边界（新仓），应在扫描时跳过，而非搬迁后回头校验
- `--dry-run` 永远不落盘、rc=0（即使报告了潜在冲突，也是 0；冲突的真实非 0 仅在非 dry-run 时返回）

#### 7.6 单元级自测

在 Step 5 同一个 `helper-selftest.py`（或独立脚本）内追加：

1. 空仓：调用迁移 → rc=0，无输出
2. legacy 仓（预置 `.workflow/flow/requirements/req-99-foo/`）：
   - `--dry-run` → rc=0，stdout 有计划，目录未移动
   - 正式运行 → rc=0，目录搬到 `artifacts/main/requirements/req-99-foo/`
   - 再运行一次 → rc=0，nothing to migrate（幂等）
3. 冲突仓（同时 legacy 和 artifacts/{branch} 都有 `req-99-foo`）：
   - 正式运行 → rc!=0，stderr 有 conflict 提示，legacy 目录未被动过

---

### Step 8：测试床重跑（完整端到端验证，最后执行）

**前置**：Step 1-7 全部完成。本步是整体回归：helper + 9 处硬编码替换 + 迁移命令一起验证。

**测试床**：req-25 回归用的新建空仓（或等价新建）。需同时准备一个 **legacy 模拟仓**（预置 `.workflow/flow/requirements/` 内容）来验证迁移命令。

**命令与产物对应**：

| # | 命令 | 对应日志 | 预期 |
|---|------|---------|------|
| 1 | `harness install` + `harness init` + `harness requirement "<title>"` | `regression-logs/chg-01/01-setup.log` | 为后续测试准备一个 req |
| 2 | `harness validate` | `regression-logs/chg-01/02-validate.log` | rc=0，输出 `Validation passed` 或等效 |
| 3 | `harness change "<title>"` + `harness rename <chg-old> <chg-new>` | `regression-logs/chg-01/03-rename-change.log` | rename 成功，目录名更新 |
| 4 | `harness rename <req> <new-req>`（三种引用：id / title / 完整目录名） | `regression-logs/chg-01/04-rename-req-{mode}.log` | 三种形式都成功 |
| 5 | `harness next` 推进到 done 后 `harness archive <req>` | `regression-logs/chg-01/05-archive.log` | 归档到 `artifacts/{branch}/archive/`，`active_requirements` 移除该 req |
| 6 | 重跑 P0-03 / P0-04 / P0-05 原始用例 | `regression-logs/chg-01/06-p0-replay.log` | 0 失败 |
| 7 | **legacy 仓**：`harness migrate requirements --dry-run` | `regression-logs/chg-01/07-migrate-dry.log` | rc=0，打印计划但不落盘 |
| 8 | **legacy 仓**：`harness migrate requirements` | `regression-logs/chg-01/08-migrate-run.log` | rc=0，legacy 目录搬到 `artifacts/{branch}/requirements/` |
| 9 | **legacy 仓迁移后**：重跑 `harness validate` | `regression-logs/chg-01/09-post-migrate-validate.log` | rc=0，且不再触发降级告警 |
| 10 | **legacy 仓**：再跑一次 `harness migrate requirements` | `regression-logs/chg-01/10-migrate-idempotent.log` | rc=0，输出 `nothing to migrate` |
| 11 | **冲突仓**（手动构造）：`harness migrate requirements` | `regression-logs/chg-01/11-migrate-conflict.log` | rc!=0，stderr 含 conflict 提示，数据未动 |

**DoD 校验**：
- [ ] 所有 log 文件 rc 符合预期列
- [ ] `runtime.yaml` 字段变化符合预期
- [ ] 文件树：`artifacts/{branch}/requirements/<req-new>/` 存在、旧目录已移除
- [ ] legacy 目录（`.workflow/flow/requirements/`）只在"未迁移"场景下含数据；迁移后为空
- [ ] 迁移命令的幂等性、冲突保护、dry-run 均有对应 log 证据

---

## 2. Verification Steps

### 2.1 单元级
- [ ] `python -m py_compile src/harness_workflow/workflow_helpers.py` 通过
- [ ] helper 独立验证（Step 5）：构造三级目录场景 + 噪声文件场景，验证返回值与告警
- [ ] 迁移命令单元测试（Step 7.6）：空仓 / legacy 仓 / 冲突仓三种场景

### 2.2 集成级（测试床重跑，Step 8）
- [ ] Step 8 全部 11 条命令跑通，log 落到 `regression-logs/chg-01/`
- [ ] req-27 既有用例（`create_requirement` / `create_change`）不受破坏

### 2.3 交叉验证
- [ ] 老仓模拟（预置 `.workflow/flow/requirements/` 内容）：
  - 迁移前：validate / rename / archive 可跑通并带降级告警
  - 执行迁移：数据搬到 `artifacts/{branch}/requirements/`
  - 迁移后：validate / rename / archive 无降级告警
  - 再次运行迁移：幂等 no-op

---

## 3. 回滚策略

**触发条件**：
- 发现破坏 req-27 已通过的 `create_requirement` / `create_change` 用例
- helper 降级顺序错误导致读到旧数据、误迁移
- 迁移命令误覆盖现有数据或误删 legacy 目录

**回滚动作**：
1. **全量回滚**：`git revert` 本 change 全部提交；恢复 `.workflow/flow/requirements` 硬编码；记录失败原因到 `session-memory.md` 的"Failed Paths"
2. **部分回滚**：
   - 若仅 Step 6（archive_base）出错 → 撤 `3791` + `resolve_archive_root`，保留主 9 处；**在 completion.md 记延期**（用户决策 Q2）
   - 若仅 `_required_dirs`（Step 4.10）出错 → 撤 `2052` 修改，保留运行时读取侧
   - 若仅迁移命令（Step 7）出错 → 撤迁移命令 CLI 注册与 `migrate_requirements` helper，保留读取侧 helper；降级告警文案回落为"手动迁移"
3. 回滚后必须在 session-memory.md 列出具体问题，避免盲目重试

**禁止**：
- 不得在 helper 中"优先 legacy 路径"以规避问题 — 那会让写入端与读取端再次错位
- 不得通过删除 legacy 目录来规避降级 — 会炸老仓
- 不得在迁移命令中实现"自动覆盖冲突"——用户决策明确要求冲突时停手

---

## 4. 风险

| 风险 | 触发场景 | 缓解措施 |
|------|---------|---------|
| **降级顺序错误 → 读到旧数据** | helper 误把 legacy 放到最高优先级 | helper 内加日志（stderr），在 Step 5 自测和 Step 8 老仓场景中验证 |
| **branch 解析为空字符串** | `_get_git_branch` 返回 `""`（非 git 仓库或 HEAD 分离） | helper 内兜底为 `"main"`；与 `create_requirement:3174` 保持一致 |
| **`_required_dirs` 追加新路径后，legacy 目录被误清理** | 未来有人以为 legacy 不再需要，删掉 init 里的 legacy 行 | change.md "非范围"中明确不删 legacy；在 helper 注释中说明降级契约 |
| **`_next_req_id` 扫描顺序不确定** | 如果 helper 返回的目录下 id 大于 state，但 legacy 目录里还有更大 id → 编号回滚 | Step 4.9 显式"追加"扫描，不替换原有扫描源 |
| **archive 旧数据残留** | `archive_base` 切到新路径后，老仓 `.workflow/flow/archive` 文件不会自动迁移 | 本 change 不做自动迁移（范围外）；在 `resolve_archive_root` 降级时告警提醒 |
| **helper 命名冲突** | `resolve_requirement_reference` 已存在，名字相近易混淆 | helper 命名为 `_root`（根目录）、`_reference`（解析引用）语义区分清晰；在 helper docstring 明确区分 |
| **测试床污染** | req-25 测试床已有旧 log / 旧数据 | Step 8 用新建空仓或备份后清理；log 归档到 `regression-logs/chg-01/` 独立命名空间 |
| **迁移命令误覆盖现有数据**（新增） | 目标已存在同名目录，但命令仍执行搬迁 | Step 7.4 明确冲突时报错不覆盖；Step 8 的冲突仓用例验证；禁止实现自动合并 |
| **噪声过滤列表不全**（新增） | 未来出现 `.editorconfig` / IDE 缓存等新噪声 → 误判为"非空" | 过滤列表提取为模块级常量 `_REQUIREMENT_ROOT_NOISE_FILENAMES`，易扩展；在 helper docstring 说明列表位置；executing 阶段若发现新噪声 → 追加一项 |

---

## 5. 执行依赖与顺序

- Step 1 → Step 2 → Step 3 → Step 4（子步 4.1..4.10 串行）→ Step 5（helper 自测）→ Step 6（archive_base 对齐）→ Step 7（迁移命令）→ Step 8（测试床完整重跑）
- Step 5 与 Step 6 解耦，可并行；但 Step 8 必须在 Step 7 完成后执行，因其依赖迁移命令的存在
- 若 Step 8 某子步失败 → 先定位具体行号 / 源头（helper / 硬编码 / 迁移命令）→ 再决定局部回滚或全量回滚（回滚策略 §3）
- 若 P1-06（Step 6）需要独立回滚 → executing 阶段必须在 chg-01 的 completion.md 记延期（用户决策 Q2）
