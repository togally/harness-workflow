# Change

## 1. Title

harness archive 支持 bugfix 目录 + 一次性 sweep bugfix-3/4/5/6

## 2. Goal

- 让 `harness archive` 识别并归档 bugfix：`list_done_requirements` / `archive_requirement` 扫 `bugfixes/` 目录并按 id 前缀分流到 `artifacts/{branch}/archive/bugfixes/<dir>`；并在本 change 内一次性把现存 active 的 bugfix-3/4/5/6 全部归档，`active_requirements` 不再含这 4 条。

## 3. Requirement

- `req-28`

## 4. Scope

### Included

- `src/harness_workflow/workflow_helpers.py`：
  - `list_done_requirements` 同时扫 `.workflow/state/requirements/` 与 `.workflow/state/bugfixes/`。
  - `archive_requirement` 按 id 前缀路由：`req-*` → `artifacts/{branch}/archive/requirements/<dir>`；`bugfix-*` → `artifacts/{branch}/archive/bugfixes/<dir>`。
  - `active_requirements` 清理逻辑保持不变（去掉被归档 id）。
- 一次性 sweep：脚本 `scripts/sweep_active_bugfixes.py` 或在 `harness archive --sweep-bugfixes` 子选项中实现——把 bugfix-3 / bugfix-4 / bugfix-5 / bugfix-6 归档。
  - 对 yaml 非 done 的 bugfix：若是 bugfix-6（依 chg-02 回填脚本已跑）走正常归档；bugfix-3/4/5 若其 yaml 并非 done 状态，则在 sweep 脚本中手动把 yaml stage 置为 done 再归档（或在数据可行时直接走正常路径，脚本内 fallback）。
- 扩展或新增 `tests/test_archive_bugfix.py`（可复用 `test_archive_path.py` 的 fixture）：断言 bugfix 归档路径 + active_requirements 清理。

### Excluded

- 不改归档产物的内部结构（只改落地根目录）。
- 不改 `harness next` 的 done 触发条件。
- 不回填已归档 req / bugfix 的历史目录结构。

## 5. Acceptance

- Covers requirement.md **AC-14**：bugfix 归档路径正确、`active_requirements` 清理干净，sweep 后 runtime.yaml 只剩 req-28 一条 active。

## 6. Risks

- 风险 A：`list_done_requirements` 扩了扫描范围后性能下降 → 缓解：限定目录层级、文件计数级别小（<100），影响可忽略。
- 风险 B：sweep bugfix-3/4/5 时其 yaml 真实 stage 与预期不符，导致误归档活跃工作 → 缓解：sweep 脚本默认 `--dry-run`，实际执行前输出目标列表 + 当前 stage，人工确认后再加 `--apply`。
- 风险 C：归档目标目录已存在同名 dir → 缓解：若冲突则在末尾加 `-YYYYMMDD` 时间戳，并在日志打印。
