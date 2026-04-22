# Regression Diagnosis · bugfix-3

> 范围：两个独立用户报告
> 1. install/update 仅应更新"当前选定 agent"
> 2. `.harness/feedback.jsonl` 落位错误
>
> 本文件由诊断师独立产出，只读诊断，不动代码 / 不搬家。

---

## 问题 1：install/update 跨 agent 全量刷新（真实问题）

### 1.1 现象

用户原话："install 和 update 命令仅仅更新当前正在使用的 agent，也就是我在 install 中选择的，可以通过在状态层记录实现"。

预期：`harness install --agent claude` 选定后，后续无 `--agent` 的 `harness install` / `harness update` 只刷新 `.claude/skills/harness/` + `.claude/commands/`，不再触碰 `.codex/` / `.qoder/` / `.kimi/`。

实测：PetMallPlatform 仅当目标 agent 是 claude，但 `.codex/skills/harness/`、`.qoder/skills/harness/`、`.kimi/skills/harness/` 仍齐全；`.workflow/state/platforms.yaml` 启用集合保持 `[codex, qoder, cc, kimi]` 不变。

### 1.2 代码证据（按调用栈）

#### A. CLI 路由层 — `src/harness_workflow/cli.py:309-321`

```python
if args.command == "install":
    if args.agent:
        return _run_tool_script("harness_install.py", ["--agent", args.agent], root)
    agent = prompt_agent_selection()      # questionary.select 单选
    if not agent:
        ...
    return _run_tool_script("harness_install.py", ["--agent", agent], root)
```

→ `harness install` **永远** 走 `harness_install.py` 脚本，**永远** 带 `--agent`。看似已经"作用域到单 agent"。

#### B. 工具脚本 — `src/harness_workflow/tools/harness_install.py:16-23`

```python
parser.add_argument("--agent", required=True, ...)
return install_agent(root, args.agent)
```

→ 强制要求 `--agent`，调用 `install_agent`。

#### C. `install_agent` — `workflow_helpers.py:5116-5281`

只往 `get_agent_skill_path(root, agent)` 写：`.{agent}/skills/harness/`。**未** 触碰其它 agent 目录。**未** 写 `.workflow/state/platforms.yaml`。**未** 写任何"激活 agent"字段到 `runtime.yaml` / `config.json`。

→ install 路径本身是干净的（已"按 agent 收敛"），但其作用域信号**没有**被持久化到状态层。

#### D. `update_repo` — `workflow_helpers.py:2869-2912`（**真正缺陷点**）

```python
install_local_skills(root, force=True)            # ← 见下面 E
actions.append("refreshed .codex/skills/harness")  # ← 硬编码打印，无视实际作用域
actions.append("refreshed .claude/skills/harness")
actions.append("refreshed .qoder/skills/harness")
_, sync_actions = _sync_requirement_workflow_managed_files(
    root,
    include_agents=True,    # ← 写死 True
    include_claude=True,    # ← 写死 True
    ...
)
```

`update_repo` 没有 `--agent` 参数，没有读取任何"上次选定 agent"的状态字段。

#### E. `install_local_skills` + `_project_skill_targets` — `workflow_helpers.py:1989-2002 / 2155-2167`

```python
def _project_skill_targets(root):
    enabled = read_platforms_config(root).get("enabled", [])
    targets = []
    if "codex" in enabled: targets.append(root / ".codex/skills/harness")
    if "cc" in enabled:    targets.append(root / ".claude/skills/harness")
    if "qoder" in enabled: targets.append(root / ".qoder/skills/harness")
    # kimi 走另一路径
    return targets
```

→ 跨 agent 范围由 `platforms.yaml.enabled` 决定。**install_agent 不会修改 platforms.yaml**，所以一次 `harness install --agent claude` 之后，`platforms.yaml` 仍然是历史值（PetMall 实测 = 全部四个），下一次 `harness update` 仍刷新所有平台。

#### F. `_managed_file_contents` — `workflow_helpers.py:2120-2139`（**第二个无视作用域的写入点**）

```python
for command in COMMAND_DEFINITIONS:
    managed[f".qoder/commands/{command['name']}.md"] = ...
    managed[f".claude/commands/{command['name']}.md"] = ...
    managed[f".codex/skills/{command['name']}/SKILL.md"] = ...
    managed[f".kimi/skills/{command['name']}/SKILL.md"] = ...
```

→ 不论 `include_agents` / `include_claude` / `platforms.yaml`，**16 条 COMMAND_DEFINITIONS × 4 个 agent 的命令/skill 文件总是被写**。`include_agents` / `include_claude` 仅控制项目根的 `AGENTS.md` / `CLAUDE.md`（见 `_scaffold_v2_file_contents:392-408`）。

### 1.3 现行状态层"激活 agent"字段盘点

| 位置 | 现有字段 | 是否表达"当前激活 agent" |
|------|---------|-----------------------|
| `.workflow/state/runtime.yaml` | `operation_type` / `current_requirement` / `stage` / `conversation_mode` / `locked_*` / `current_regression` / `ff_mode` / `ff_stage_history` / `active_requirements` | 否 |
| `.workflow/state/platforms.yaml` | `enabled[]` / `disabled[]` / `last_updated` | **多选集合**，不是单选"激活" |
| `.codex/harness/config.json` | `language` | 否 |
| `.workflow/state/sessions/` | 各需求 session-memory 散文 | 否 |

→ **状态层完全缺失"active agent"字段**。用户提议（"通过在状态层记录实现"）属于**新增能力**，不是"接线未接通"。

### 1.4 根因（一句话）

`install_agent` 已按 agent 收敛，但它的作用域信号没有被持久化；`update_repo` 与 `_managed_file_contents` 的写入范围分别由"硬编码 + `platforms.yaml` 集合"决定，二者都不感知"用户当前用哪一个 agent"，导致跨 agent 全量刷新。

### 1.5 修复方向建议（供 testing/executing 阶段评估）

**新增字段**：在 `.workflow/state/platforms.yaml` 增加 `active_agent: <kimi|claude|codex|qoder>`（与 `enabled[]` 解耦：enabled 是兼容池，active_agent 是用户实际操作的那一个）。

**写入点**：`install_agent(root, agent)` 末尾追加一行 `update_active_agent(root, agent)`，统一通过 `backup.py` 新增 helper 写入。

**消费点**（必须同时改）：

| 文件 | 函数 | 改法 |
|------|------|------|
| `workflow_helpers.py:2120` | `_managed_file_contents` | 接收 `active_agent` 参数；只为该 agent 写入对应的 `.{agent}/commands/...` / `.{agent}/skills/...` |
| `workflow_helpers.py:1989` | `_project_skill_targets` | 优先读 `active_agent`，回退 `enabled[]`（向后兼容旧仓） |
| `workflow_helpers.py:2869` | `update_repo` | 读 `active_agent` 并传给下游；硬编码 print 改成按实际写入路径输出 |
| `tools/harness_update.py` | CLI | 可选 `--agent X` 覆盖（一次性） / `--all-platforms` 显式回退到旧行为（迁移期 escape hatch） |

**数据迁移**：旧仓 `platforms.yaml` 无 `active_agent` 字段时，`update_repo` 报一行警告 "active agent 未设定，将刷新 enabled 集合（兼容模式）"；下次 `harness install --agent X` 自动补齐。**不破坏旧仓**。

---

## 问题 2：`.harness/feedback.jsonl` 落位错误（真实问题，但**不能直接删**）

### 2.1 现象

文件位置：
- `/Users/jiazhiwei/claudeProject/PetMallPlatform/.harness/feedback.jsonl`（28 行）
- `/Users/jiazhiwei/IdeaProjects/harness-workflow/.harness/feedback.jsonl`（182 行）

二者都已被 git 跟踪（`git ls-files .harness/` 命中）。`.gitignore` 既不忽略 `.harness/`、也未为它加 `!` 例外。

### 2.2 写入点（5 处，全在 `workflow_helpers.py`）

| 行号 | 调用方 | 事件 |
|------|--------|------|
| 3566 | `create_regression`（`harness regression "<title>"`） | `regression_created` |
| 4993 | `workflow_advance`（`harness next`） | `stage_duration` |
| 4997 | 同上 | `stage_advance` |
| 5029 | `workflow_fast_forward`（`harness ff`） | `stage_skip` |
| 5030 | 同上 | `ff` |

底层 helper：`record_feedback_event(root, event_type, data)`（`workflow_helpers.py:2294-2307`）。

常量定义（`workflow_helpers.py:136-137`）：
```python
FEEDBACK_DIR = Path(".harness")
FEEDBACK_LOG = FEEDBACK_DIR / "feedback.jsonl"
```

注意：`HARNESS_DIR = Path(".codex") / "harness"`（line 39）是**另一个**目录，与 `.harness/` 没关系——后者是 reactor 之外独立创建的"反馈数据"根。

### 2.3 消费者（**有真实消费**，不能简单删）

`harness feedback` CLI（`cli.py:529-538`）→ `tools/harness_export_feedback.py:1-88`：

```python
log_path = root / ".harness" / "feedback.jsonl"   # 直接读
...
out_path = root / "harness-feedback.json"          # 输出汇总到根目录
```

逻辑：聚合 `stage_skip` 计数 / `stage_duration` 平均 / `regression_created` 计数 → 写到项目根 `harness-feedback.json`，可选 `--reset` 清空 jsonl。

**结论**：`.harness/feedback.jsonl` 是**有用的**审计/统计数据，不能删。问题不是"误产物"，而是"产物落错层"。

### 2.4 与 `state/{requirements,bugfixes}/*.yaml` 的 `stage_timestamps` 字段关系

`stage_timestamps`（`workflow_helpers.py:4148-4155`）：

```python
if "stage_timestamps" in target_state:
    existing[new_stage] = datetime.now(timezone.utc).isoformat()
```

→ 按"requirement / bugfix × stage"维度，**只记进入时间戳**（一条/stage）。落 `.workflow/state/{requirements,bugfixes}/<id>.yaml`。

`feedback.jsonl` 的 `stage_advance` / `stage_duration` 维度不同：

| 维度 | `stage_timestamps` (yaml) | `feedback.jsonl` |
|------|--------------------------|------------------|
| 归属 | 单 requirement / bugfix | 全仓库（无 requirement_id） |
| 粒度 | 当前 stage 入场时间（一次/stage） | 每次 next 都打一条（含 from→to / 时长） |
| 用途 | 给 done-report 做时长计算 | 给 `harness feedback` 做跨 requirement 平均/计数 |
| 历史 | 仅"最近一次进入"，被 `harness next` 覆盖 | append-only 全量审计流 |

→ **不重复**，是两套互补的观测。`.harness/feedback.jsonl` 是"跨需求长流水"，`stage_timestamps` 是"当前需求快照"。两者都应保留，但 feedback 的归属层是错的。

### 2.5 六层定位（按 `project-overview.md`）

> 一层 context / 二层 tools / 三层 flow / 四层 **state**（运行时状态、需求进度、会话记忆） / 五层 **evaluation**（测试规则、验收规则、回归诊断） / 六层 constraints。

`feedback.jsonl` 是"运行时观测流水"——既不是评估规则、也不是已结案的诊断，而是**持续累积的状态数据**。最合理归位：**四层 state**。

具体路径建议：`.workflow/state/feedback/feedback.jsonl`

理由：
1. 与 `.workflow/state/sessions/`、`.workflow/state/action-log.md` 同层、同性质（"工作流运行过程的足迹"）。
2. 不与 `state/requirements/` / `state/bugfixes/` 平级冲突——feedback 不属于任何单一 requirement。
3. 单独一个 `feedback/` 子目录便于将来扩展（如分流到 `feedback-by-stage/`、`feedback-by-month/` 滚动归档）。
4. 配合 `harness-feedback.json` 输出（目前写在仓库根），可以一并搬到 `.workflow/state/feedback/feedback-summary.json`，仓库根更干净。

**反例**：放五层 evaluation 不合适——evaluation 是"如何评估"的规则定义，不是被评估的原始数据。

### 2.6 根因（一句话）

`FEEDBACK_DIR = Path(".harness")` 这一常量在六层架构成型前先行落地，从未被纳入"工作流数据 = `.workflow/`"的统一归位规则；之后 `harness-export-feedback` 工具继承了同一路径，导致 `.harness/` 长期游离于六层之外。

### 2.7 迁移路径建议（供 executing 阶段）

最小破坏迁移（不删历史）：

1. 修改 `workflow_helpers.py:136-137`：
   ```python
   FEEDBACK_DIR = Path(".workflow") / "state" / "feedback"
   FEEDBACK_LOG = FEEDBACK_DIR / "feedback.jsonl"
   ```
2. 同步 `tools/harness_export_feedback.py:20`：`log_path = root / ".workflow" / "state" / "feedback" / "feedback.jsonl"`。
3. 同步 `assets/scaffold_v2/.workflow/context/roles/harness-manager.md:537` 文档路径。
4. 同步 `assets/scaffold_v2/.workflow/tools/catalog/harness-export-feedback.md:8` 文档路径。
5. 在 `update_repo` 加一段一次性迁移：
   ```python
   old = root / ".harness" / "feedback.jsonl"
   new = root / ".workflow" / "state" / "feedback" / "feedback.jsonl"
   if old.exists() and not new.exists():
       new.parent.mkdir(parents=True, exist_ok=True)
       shutil.move(str(old), str(new))
       # 若 .harness/ 空目录则一并 rmdir
   ```
6. **保留**主仓和 PetMall 现有 182 + 28 行历史数据，迁移后位置变更，内容不动。
7. 主仓 `.gitignore` 不需要改（`.workflow/` 本身已强制保留）。

**风险低**：写入点只有 5 个、消费者只有 1 个、文件就一个 jsonl，灰度无意义，原子迁移即可。

---

## 综合路由决策

### 是否真实问题
- 问题 1：✅ **真实**（跨 agent 全量刷新）
- 问题 2：✅ **真实**（六层架构外残留 + 写入点常量错置）

### 推荐路由：`harness regression --confirm` → `testing`

理由：

1. **两条都是实现/工程问题**，无需求 / 设计层冲突，按 `regression.md:100-103` 走 testing 路线。
2. 两条问题修复后都需要"端到端可重放"验证：
   - 问题 1：在新临时仓 `harness install --agent X` → `harness update` → 校验只刷新 `.X/` 目录。
   - 问题 2：迁移前后 `harness next` / `harness feedback` 输出不变；旧 `.harness/feedback.jsonl` 数据连续。
3. 当前测试基线（180 tests 全绿）需要补 ≥3 个用例：
   - `test_install_agent_persists_active_agent`
   - `test_update_repo_only_refreshes_active_agent`
   - `test_feedback_jsonl_writes_under_state_feedback`（含 `.harness/` → `.workflow/state/feedback/` 迁移）
4. 一并修，不拆分——两条问题在 `update_repo` 的核心改造期会反复触碰相同代码段（常量 / 路径 / 写入点），拆开会引入合并冲突。

### 衍生发现（不在本 bugfix 范围）

- **bugfix ID 复用缺陷**：`artifacts/main/archive/bugfixes/` 已有 4 个历史 `bugfix-3-*` 目录（`bugfix-3-install 在空仓自动 init` / `bugfix-3-pipx-重装后...` / `bugfix-3-修复 suggest apply...` / 当前活跃 `bugfix-3-install-update-...`）。`harness bugfix` 的 ID 分配器只看活跃 `state/bugfixes/`，不扫 `artifacts/main/archive/bugfixes/`。建议主 agent 将其登记为新独立缺陷（暂记 `bugfix-? 编号扫归档`）。

---

## 附：已完成检查项

- [x] 现象确认（用户原话 + 实际目录证据）
- [x] 代码证据（函数名 + 行号）
- [x] 状态层字段盘点
- [x] 根因（一句话）
- [x] 修复方向（字段 + 写入点 + 消费点 + 迁移路径）
- [x] 路由决策（testing）
- [x] 衍生发现登记
