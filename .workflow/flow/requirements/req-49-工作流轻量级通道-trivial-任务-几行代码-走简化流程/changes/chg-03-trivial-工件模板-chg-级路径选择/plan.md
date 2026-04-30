# Plan — chg-03（trivial 工件模板 + chg 级路径选择）

## 1. Steps（按硬序排列）

### Step 1：trivial-spec.md 模板落地
- 创建 `.workflow/flow/requirements/_templates/trivial-spec.md`（仓库根模板）：
  ```markdown
  ---
  type: trivial-spec
  ---

  ## 1. 问题
  <!-- ≤ 200 字，一句话描述问题 -->

  ## 2. 修复
  <!-- ≤ 200 字，一行 / 几行代码 + 改动文件清单 -->

  ## 3. 验证
  <!-- ≤ 200 字，pytest 命令 + 关键断言 -->
  ```
- 在 `workflow_helpers.py` 新增 `create_trivial_spec(req_dir: Path)` helper：拷贝模板到 `{req_dir}/trivial-define/trivial-spec.md`；
- 单测 `tests/test_create_trivial_spec.py`：3 用例（创建成功 / 已存在不覆盖 / wc -c ≤ 1024）。

### Step 2：scaffold_v2 mirror 同步
- 复制 `.workflow/flow/requirements/_templates/trivial-spec.md` → `scaffold_v2/.workflow/flow/requirements/_templates/trivial-spec.md`；
- 跑 `diff -rq` 断言无差异；
- 单测 `tests/test_scaffold_mirror_trivial.py`：1 用例（mirror diff 归零）。

### Step 3：chg 级 trivial frontmatter 校验
- 在 `workflow_helpers.py` 新增 `read_change_trivial_flag(change_md_path: Path) -> bool`：
  - 解析 change.md YAML frontmatter；
  - 返回 `trivial` 字段值（默认 False）；
- 单测 `tests/test_read_change_trivial_flag.py`：3 用例（True / False / 字段缺失默认 False）。

### Step 4：CLI dispatch trivial / 标准 executing
- 修改 `cli.py` 的 `harness next` 流转逻辑：
  - 在 stage = executing 入口处，读取当前活跃 chg 的 change.md frontmatter；
  - 若 `trivial: true` → dispatch trivial executing 模式（briefing 注入 trivial=true 标识）；
  - 否则 → 标准 executing；
- 单测 `tests/test_harness_next_chg_trivial_dispatch.py`：4 用例（trivial=true / trivial=false / 字段缺失 / mixed bugfix 内 chg-01 trivial / chg-02 标准）。

### Step 5：executing.md 加 §trivial 模式段
- 编辑 `.workflow/context/roles/executing.md` 末尾加：
  ```markdown
  ## §trivial 模式（req-49 chg-03）
  
  当 briefing 含 `trivial: true` 时：
  - 工件仅产出 `trivial-spec.md`（3 段 ≤ 1 KB），不产出 session-memory.md / test-evidence.md / acceptance-report.md；
  - 跳过 plan.md §4 测试用例设计校验；
  - 仅要求新增 1 unit test 断言 fix；
  - 完成后 runtime stage 流转到 done（无 testing / acceptance）。
  ```
- grep 自检：`grep "trivial 模式" .workflow/context/roles/executing.md` 命中。

### Step 6：repository-layout.md 加 trivial 子树段
- 编辑 `.workflow/flow/repository-layout.md` §3 加 §3.3：
  ```markdown
  ## 3.3 trivial 任务工件落位（req-49 chg-03）
  
  trivial 任务（task_type=trivial 或 chg 级 trivial=true）工件落位：
  - 整任务 trivial（task_type=trivial）：`.workflow/flow/requirements/{req-id}-{slug}/trivial-define/trivial-spec.md`；
  - chg 级 trivial（change.md frontmatter trivial=true）：复用既有 `changes/{chg-id}-{slug}/` 子目录，仅 plan.md / change.md 走 trivial 模板规则（plan.md §4 可省）。
  ```
- 单测 `tests/test_artifact_placement_trivial.py`：覆盖 trivial 通道工件落位 lint exit 0。

### Step 7：硬门禁六 / 七 / 契约 7 自检
- 所有新增 stdout / 文档：grep 自检带 ≤ 15 字描述；
- artifact-placement lint 全绿。

## 2. 验证

### Unit 测试
- `tests/test_create_trivial_spec.py`：3 用例；
- `tests/test_scaffold_mirror_trivial.py`：1 用例；
- `tests/test_read_change_trivial_flag.py`：3 用例；
- `tests/test_harness_next_chg_trivial_dispatch.py`：4 用例；
- `tests/test_artifact_placement_trivial.py`：3 用例。

### Manual 测试
- 创建 trivial 任务 → 检查 trivial-spec.md ≤ 1 KB；
- 在 bugfix 内 chg-01 标 trivial=true → `harness next` 推进 → 检查 briefing 是否含 trivial 标识。

### AC mapping
- AC-N1 → Step 3 + Step 4 + tests/test_read_change_trivial_flag.py + tests/test_harness_next_chg_trivial_dispatch.py；
- AC-N3 → Step 1 + Step 2 + Step 5 + tests/test_create_trivial_spec.py + tests/test_scaffold_mirror_trivial.py；
- AC-10 → Step 6 + tests/test_artifact_placement_trivial.py。

## 3. 硬序约束

- Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7（线性硬序）；
- 本 chg 完成后才允许进入 chg-04；
- 本 chg 依赖 chg-01（TRIVIAL_SEQUENCE）+ chg-02（validate_trivial_eligibility 可被 chg 级 flag 校验复用）。

## 4. 测试用例设计

> regression_scope: targeted  # 改动局限于新增模板 + frontmatter 解析 + harness next dispatch 分支；不改既有 sequence / state machine
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - .workflow/flow/requirements/_templates/trivial-spec.md（新增）
> - scaffold_v2/.workflow/flow/requirements/_templates/trivial-spec.md（新增 mirror）
> - src/harness_workflow/workflow_helpers.py（新增 create_trivial_spec / read_change_trivial_flag）
> - src/harness_workflow/cli.py（harness next 分支扩 trivial dispatch）
> - .workflow/context/roles/executing.md（新增 §trivial 模式段）
> - .workflow/flow/repository-layout.md（§3.3 新增）
> - 间接波及：所有 change.md 解析路径（确保 frontmatter 字段缺失时 default=False 不打破现有 chg）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | `create_trivial_spec(tmpdir/req-49)` | trivial-define/trivial-spec.md 存在 + wc -c ≤ 1024 | AC-N3 | P0 |
| TC-02 | `create_trivial_spec` 已存在文件 | 不覆盖 + 抛 FileExistsError 或返回 False | AC-N3 | P0 |
| TC-03 | scaffold_v2 mirror diff -rq | 0 输出 | AC-N3 | P0 |
| TC-04 | `read_change_trivial_flag(change_md_with_trivial_true)` | True | AC-N1 | P0 |
| TC-05 | `read_change_trivial_flag(change_md_with_trivial_false)` | False | AC-N1 | P0 |
| TC-06 | `read_change_trivial_flag(change_md_no_trivial_field)` | False（默认） | AC-N1 | P0 |
| TC-Dogfood-01 | tmpdir bugfix + chg-01 frontmatter trivial=true + `harness next` | briefing 注入 trivial=true 标识 + executing 走 trivial 模式 | AC-N1 | P0 |
| TC-Dogfood-02 | tmpdir bugfix + chg-01 trivial=true + chg-02 trivial=false + `harness next` 两次 | chg-01 dispatch trivial executing；chg-02 dispatch 标准 executing | AC-N1 | P0 |
| TC-07 | grep `executing.md` 含 §trivial 模式段 | 命中 ≥ 1 | AC-N3 | P1 |
| TC-08 | grep `repository-layout.md` 含 §3.3 trivial 任务工件落位 | 命中 ≥ 1 | AC-10 | P1 |
| TC-09 | `harness validate --contract artifact-placement` 在 trivial 任务 fixture 下 | exit 0 | AC-10 | P0 |
| TC-Dogfood-03 | tmpdir 创建 trivial 任务 + 走完 trivial-define stage | trivial-spec.md ≤ 1 KB + 不产出 session-memory.md（或产出 ≤ 500 字） | AC-N3 | P0 |
| TC-10（反例） | trivial-spec.md 写超 1 KB 内容 | wc -c 断言失败（lint 报警 / 但不阻塞，仅警告） | AC-N3 | P1 |
| TC-11（反例） | change.md frontmatter trivial 值非 bool（如 `"yes"` 字符串） | read_change_trivial_flag 抛 ValueError 或视为 False | AC-N1 | P2 |
