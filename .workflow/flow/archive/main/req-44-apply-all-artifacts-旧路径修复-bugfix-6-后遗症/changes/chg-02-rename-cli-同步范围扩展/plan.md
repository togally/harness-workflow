# Change Plan — chg-02（rename CLI 同步范围扩展）

> 所属 req：req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））
> 关联 sug：sug-44（apply 取 content 头当 title + rename 不同步 runtime）/ sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/）
> 关联 bugfix：bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））

## 1. 目标

把 `harness rename requirement <old> <new>` 同步范围扩到 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 后新增的 `.workflow/flow/requirements/{slug}/` 目录，并把 `runtime.yaml` 的 `current_requirement_title` / `locked_requirement_title` 字段一并改写，闭环 AC-03。

## 2. 影响文件列表

- `src/harness_workflow/workflow_helpers.py`
  - `rename_requirement`（line 5338 起）：现仅 mv `resolve_requirement_root(root)/{old_dir_name}` + 改 state yaml；扩展为同时探测并 mv `.workflow/flow/requirements/{old_dir_name}` → `{new_dir_name}`（存在才动；与 artifacts/ 端对称）。
  - 同函数末尾追加 runtime 同步段：若 `runtime["current_requirement"] == old_id` → 写 `runtime["current_requirement_title"] = new_title`；若 `runtime["locked_requirement"] == old_id` → 写 `runtime["locked_requirement_title"] = new_title`。两字段缺失时新建。
- `tests/test_rename_helpers.py`：扩 5 条新用例（覆盖 flow/ 同步 + runtime title 同步 + locked 同步 + 不命中保留 + legacy 兼容）。

## 3. 实施步骤

1. **扩 `rename_requirement` 目录 mv**：在现有 `resolve_requirement_root(root)` mv 之后追加 `_flow_dir = root / ".workflow" / "flow" / "requirements" / old_dir_name`；`if _flow_dir.is_dir(): shutil.move(str(_flow_dir), str(root / ".workflow" / "flow" / "requirements" / new_dir_name))`。
2. **扩 runtime 同步**：在函数末尾读取 `.workflow/state/runtime.yaml`，按上述规则改写 `current_requirement_title` / `locked_requirement_title`，再 yaml.safe_dump 回写；其它字段 verbatim 保留（含 `active_requirements` 列表，仅存 id 不动）。
3. **不动**：`rename_change` / `rename_bugfix`（不在 AC-03 范围）；`active_requirements` 列表（id 不变）。
4. **跑 pytest**：`pytest tests/test_rename_helpers.py -v` 全绿；再跑 `pytest -q` 全量。
5. **手跑端到端**：本仓库 `harness rename requirement <current-old-slug> <new-title>` → 三处目录全改名 + `cat .workflow/state/runtime.yaml` 验 `current_requirement_title` 同步。
6. **commit**：commit message `fix(chg-02): rename CLI 同步 .workflow/flow/ + runtime title（req-44 / 修复 sug-44+sug-45）`。

## 4. 测试用例设计（bugfix-6 B1 强制段）

> regression_scope: targeted
> 波及接口清单：
> - `src/harness_workflow/workflow_helpers.py::rename_requirement`

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 rename 同步 .workflow/flow/ 目录 | req-id ≥ 41，flow/ + artifacts/ + state/ 三处目录都已建，rename old→new | 三处目录都改名；旧 slug 都不存在；新 slug 都存在 | AC-03 | P0 |
| TC-02 rename 同步 runtime current_requirement_title | rename 当前 active req（runtime.current_requirement 命中） | runtime.yaml 的 current_requirement_title = new_title；current_requirement id 不变 | AC-03 | P0 |
| TC-03 rename 同步 runtime locked_requirement_title | conversation_mode=harness + locked_requirement 命中本 req | runtime.yaml 的 locked_requirement_title = new_title | AC-03 | P1 |
| TC-04 rename 不命中 current 时不动 runtime title | rename 一个非 current_requirement 的旧 req | runtime.yaml current_requirement_title / locked_requirement_title 字段保持原值 | AC-03 | P1 |
| TC-05 rename legacy req-id（无 flow/ 目录）兼容 | req-id ≤ 40，仅 artifacts/ + state/ 两处目录 | exit 0；不报错；只改 artifacts/ + state/；flow/ 探测 miss 静默跳过 | AC-03 | P1 |

> AC 映射：AC-03 → TC-01..TC-05；AC-04（scaffold mirror）本 chg = no-op；AC-05（e2e 用例数）本 chg 贡献 5 条 ≥ 2 条。

## 5. 验证方式

- 静态：`pytest tests/test_rename_helpers.py -v` 5 条新用例全绿；`pytest -q` 全量无回归。
- 动态（端到端）：本仓库挑一条 active req → `harness rename requirement <old> <new>` → `ls .workflow/flow/requirements/ artifacts/main/requirements/ .workflow/state/requirements/` 三处都看到新 slug + `grep -E "current_requirement_title|locked_requirement_title" .workflow/state/runtime.yaml` 含 new_title。
- 契约：交付前必跑 `harness validate --human-docs` + `harness validate --contract test-case-design-completeness`，exit 0 才允许 PASS。

## 6. 回滚方式 + scaffold mirror + 契约 7 注意点

### 回滚

- `git revert <chg-02 commit sha>` 即可回到 bugfix-6 后未修复状态（rename 漏改 flow/ 与 runtime title，需手工 mv + 手工 Edit 补救）。
- 数据回滚：若已有目录被错改，可 git mv 反向操作；runtime.yaml 字段从 git checkout 历史版恢复。

### scaffold mirror（AC-04）

- 本 chg 仅改 `src/` + `tests/`，不动 `.workflow/` 文档树或 scaffold 模板；scaffold mirror = **no-op**，AC-04 在本 chg 范围内自动满足。

### 契约 7 + 硬门禁六注意点

- 本 plan.md / 同 chg 目录下 `change.md` / commit message / TaskList / session-memory 内首次引用 sug-44（apply 取 content 头当 title + rename 不同步 runtime）/ sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/）/ bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 必带括号简短描述；批量列举 ≥ 2 个 id 时禁止裸数字扫射。
- 风险 R-3（runtime 同步漏字段，未来扩 `pending_requirement_title` 类似字段）：在本 chg §回滚 注明"若未来扩 *_requirement_title 类字段需同步本处"，并在 done 阶段补一条 follow-up sug。
