# Change

## 1. Title

完成 requirement 路径迁移到 artifacts/{branch}

## 2. Background

- req-27 启动了一次 artifacts 根目录重构（目标：requirement 产出统一落到 `artifacts/{branch}/requirements/`），但**只完成了写入端**：`create_requirement` 已在 `workflow_helpers.py:3174` 写入新路径，`create_change` 在 `3341` 也已对齐。
- 读取端未迁移。regression subagent（诊断文件：`.workflow/flow/regressions/req-25-6-p0/analysis.md` 与 `decision.md`）确认这是 req-25 测试床中 P0-03 / P0-04 / P0-05 的共同根因：
  - **P0-03**：`harness validate` 在 `workflow_helpers.py:3897` 到 `.workflow/flow/requirements` 查找 → 写入端新路径，读取端旧路径 → `Requirement not found`
  - **P0-04**：`harness archive` 在 `3782` 解析 req_dir、`3830` 做残留清理，均指向旧路径 → 归档完全不可用
  - **P0-05**：`harness rename` 在 `3530`（rename_requirement）、`3562`（rename_change）解析旧路径 → `Requirement does not exist`
- 诊断还列出 9 处硬编码 `.workflow/flow/requirements`（行号：`2052 / 2863 / 3134 / 3377 / 3530 / 3562 / 3782 / 3830 / 3897`）。当前验证结果：`3830` 位置实际为残留清理时复用 `requirements_dir` 变量，随主路径迁移即可一并修复；根本硬编码落在其余 8 处。

## 3. Goal

让 `validate` / `archive` / `rename_requirement` / `rename_change` 以及它们的下游路径解析逻辑，按 req-27 约定的新路径 `artifacts/{branch}/requirements/` 正确读写，并为后续命令留出统一的解析入口，彻底消除"写新路径、读旧路径"的错位；同时为已有 legacy 数据的老仓提供**一键迁移命令**，一次性把 `.workflow/flow/requirements/*` 安全搬到新路径。

## 4. Scope

### 4.1 包含

1. **新建公共 helper**：`resolve_requirement_root(root: Path) -> Path`，位于 `src/harness_workflow/workflow_helpers.py`（与 `_get_git_branch` 相邻，便于复用分支解析）。
   - 优先返回 `artifacts/{branch}/requirements`（存在时）
   - 其次返回 `artifacts/requirements`（兼容未启用 branch 的过渡形态）
   - 最后回退 `.workflow/flow/requirements`（legacy，仅兼容老仓）
   - 降级时必须打印一行告警日志（stderr），提示用户所在仓库仍使用 legacy 路径
2. **替换以下硬编码**（共 9 处；其中 `3830` 属于 `requirements_dir` 变量的复用点，随主行替换一并修复）：
   | # | 行号 | 函数 | 当前写法 | 替换动作 |
   |---|------|------|---------|---------|
   | 1 | 2052 | `_required_dirs` | 固定创建 `.workflow/flow/requirements` | 保留 legacy 路径，同时追加新路径 `artifacts/{branch}/requirements`（确保 init 后两侧目录都存在，不阻断过渡期工具） |
   | 2 | 2863 | `_next_req_id` | 只扫描 `state/requirements` 与 `.workflow/flow/requirements` | 追加扫描 `resolve_requirement_root(root)`，确保 id 递增不回滚 |
   | 3 | 3134 | `create_suggest_bundle` 追加建议清单 | 用旧路径定位新创建的 req 目录 | 改为 `resolve_requirement_root(root)` |
   | 4 | 3377 | `create_regression` | 解析 `current_requirement` 的 req_dir | 改为 `resolve_requirement_root(root)`；`3379` 的 `regressions_base` fallback 随之改为 `resolve_requirement_root(root).parent / "regressions"` 等价形态（保持原 fallback 语义） |
   | 5 | 3530 | `rename_requirement` | `requirements_dir = .workflow/flow/requirements` | 改为 `resolve_requirement_root(root)` |
   | 6 | 3562 | `rename_change` | 解析 req_dir 的根 | 改为 `resolve_requirement_root(root)` |
   | 7 | 3782 | `archive_requirement` | `requirements_dir = .workflow/flow/requirements` | 改为 `resolve_requirement_root(root)` |
   | 8 | 3830 | `archive_requirement` 残留清理 | 基于 `requirements_dir` 变量复用 | 随 #7 自动生效（仅验证，无单独改动） |
   | 9 | 3897 | `validate_requirement` | `requirements_dir = .workflow/flow/requirements` | 改为 `resolve_requirement_root(root)` |
3. **老仓一键迁移命令**：新增 `harness migrate requirements`（CLI 入口命名见下文 §4.4），一次性把 `.workflow/flow/requirements/*` 与 `artifacts/requirements/*`（若存在）搬到 `artifacts/{branch}/requirements/`，支持 `--dry-run` 空跑，幂等执行，目标冲突时报错而非覆盖。
4. **回归验证**：在 req-25 测试床（或等价新空仓）重跑 `validate` / `archive` / `rename` + 迁移命令，日志落到 `regression-logs/` 对应子目录，确认 P0-03 / P0-04 / P0-05 均归零，且迁移命令在空仓 / 新仓 / legacy 仓三种场景下行为正确。

### 4.2 排除

- **P0-01**（install 空仓应自动 init）不在本 change 范围 → 单独走 bugfix
- **P0-02**（scaffold 清洗）不在本 change 范围 → 单独走 bugfix
- **P0-06**（kimi skill + install_agent 一致性）不在本 change 范围 → 单独走 bugfix
- 不改 cli 层其他命令的入口签名（仅新增一个 `migrate` 子命令）、不改 CLAUDE.md / WORKFLOW.md 文档
- 不改 `.workflow/context/**` 角色文档
- 不动 `runtime.yaml`（本 change 只修 helper、路径解析与新增迁移命令）
- **不做 archive 目录的自动迁移**（archive 旧数据原地保留，由 `resolve_archive_root` 降级告警提醒）

### 4.4 迁移命令规格

- **CLI 入口**：`harness migrate requirements [--dry-run]`
  - 命名理由：动词 `migrate` + 资源 `requirements` 与现有 `harness archive <req>` / `harness rename <req> <new>` 的资源定位风格一致；为后续扩展（例如 `harness migrate archive`）预留命名空间
- **扫描源**：
  1. `.workflow/flow/requirements/*`（legacy 路径）
  2. `artifacts/requirements/*`（req-27 中间过渡路径）
- **目标**：`artifacts/{branch}/requirements/`（branch 由 `_get_git_branch` 解析，失败兜底 `main`）
- **冲突策略**：若某个源目录在目标下已存在同名目录 → 报错并打印手动处理提示，**不覆盖**，本次迁移中止当前条目但继续处理其他条目（最终按是否有冲突决定整体 rc）
- **幂等性**：若源目录已为空或不存在 → 跳过；二次运行为 no-op
- **`--dry-run`**：仅打印"计划迁移的目录清单 + 冲突清单"，不落盘，rc=0
- **日志**：每条迁移在 stdout 输出 `[migrate] <src> -> <dst>`；冲突在 stderr 输出 `[migrate] conflict: <dst> already exists, skipped`
- **出口码**：无冲突且迁移成功 → 0；有冲突 → 非 0 且打印汇总

### 4.3 P1-06（archive_base 对齐）决策

**结论：纳入本 change，作为独立 Step（plan.md Step 6）执行；但与 9 处硬编码的主修复解耦，如时间不足可单独回滚。**

**理由**：
1. `3791 archive_base = .workflow/flow/archive` 与 req-27 既定方向（`artifacts/{branch}/archive`）不一致，且 `archive_requirement` 是 P0-04 的同一函数；一次性收口可避免下次回归再测一遍 archive。
2. 对应的 helper 命名可复用同一抽象：`resolve_archive_root(root) -> Path`，与 `resolve_requirement_root` 同门同宗，维护成本低。
3. 风险可控：archive 目录迁移本身是新建操作（旧归档文件原地保留），不存在破坏历史数据的场景。
4. 若验证阶段发现问题，回滚只需撤掉 Step 6 的 archive_base 一行改动，不影响主路径的 9 处修复。

## 5. Definition of Done (DoD)

- [ ] 新建 `resolve_requirement_root(root: Path) -> Path`：支持 `artifacts/{branch}/requirements` → `artifacts/requirements` → `.workflow/flow/requirements` 三级降级，降级时有 stderr 告警
- [ ] **helper 的"非空"判定必须过滤噪声文件**：过滤列表包含 `.DS_Store` / `.gitkeep` / `Thumbs.db` / `.keep`（以常量形式提取，可扩展）；仅当目录存在实质性内容（过滤后仍 ≥1 条）时才判定为"非空"
- [ ] 9 处硬编码（`2052 / 2863 / 3134 / 3377 / 3530 / 3562 / 3782 / 3830 / 3897`）全部替换完毕，代码中 `root / ".workflow" / "flow" / "requirements"` 只允许出现在 helper 内部作为 legacy 回退
- [ ] **新增迁移命令** `harness migrate requirements`：
  - 能把 `.workflow/flow/requirements/*` 与 `artifacts/requirements/*` 安全搬到 `artifacts/{branch}/requirements/`
  - 目标已存在 → 报错不覆盖
  - 幂等：二次运行对已迁移目录为 no-op
  - 支持 `--dry-run`（打印计划，不落盘，rc=0）
  - 冲突 → 非 0 退出并打印汇总
- [ ] 在 req-25 测试床（或新建空仓等价床）重跑 P0-03 / P0-04 / P0-05 对应命令：
  - `harness validate` 返回 `0`
  - `harness archive <req>` 产出落到新路径且 `active_requirements` 正确收敛
  - `harness rename <req> <new>` 三种引用形式（id / title / 完整目录名）全部成功
  - 所有日志入 `regression-logs/` 对应子目录
- [ ] 在 legacy 模拟仓（预置 `.workflow/flow/requirements/` 内容）跑 `harness migrate requirements --dry-run` 与正式迁移，验证迁移后目录搬迁正确、再跑一次为 no-op
- [ ] P1-06 `archive_base` 对齐 `artifacts/{branch}/archive`（纳入本 change）；若独立回滚 → **completion.md 明确记录 `archive_base` 未对齐作为延期项**
- [ ] `_required_dirs` 在 init 时同时创建 legacy 与新路径，过渡期内两条路径共存（仅 init 时创建；运行时读取只用 `resolve_requirement_root`）
- [ ] 未破坏 req-27 已通过的 `create_requirement` / `create_change` 用例
- [ ] 沉淀经验：如有可泛化的路径迁移教训，写入 `.workflow/context/experience/roles/planning.md` 或 `executing.md`

## 6. Non-Goals（明示非范围）

- 不修 P0-01 / P0-02 / P0-06
- 不动 scaffold_v2 内容
- 不新增除 `harness migrate requirements` 以外的 CLI 命令
- 不重写 `resolve_requirement_reference`（继续复用）
- 不引入新的配置字段（branch 解析沿用 `_get_git_branch`）
- 不做 archive 目录的自动迁移（archive 数据原地保留，由 `resolve_archive_root` 降级告警提醒）
- 不在迁移命令中合并同名冲突（一律报错提示人工处理）

## 7. 相关 P0 / P1 索引

| 编号 | 内容 | 在本 change 的对应步骤 |
|------|------|---------------------|
| P0-03 | `harness validate` 找不到新路径 req | 主修（Step 4.3） |
| P0-04 | `harness archive` 找不到新路径 req，归档失败 | 主修（Step 4.5） |
| P0-05 | `harness rename` 找不到新路径 req | 主修（Step 4.4） |
| P1-06 | `archive_base` 对齐 `artifacts/{branch}/archive` | 纳入本 change，Step 6；独立回滚时在 completion.md 记延期 |
| 诊断衍生 | 老仓 legacy 数据无迁移工具 | 新增 `harness migrate requirements`，Step 7 |

## 8. Next

- `plan.md`：分步执行计划
- `regression/required-inputs.md`：保持空白（诊断已明确无需人工输入）
