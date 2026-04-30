# Plan — chg-05（dogfood 活证 + reviewer 加项 + 契约 lint 闭环）

## 1. Steps（按硬序排列）

### Step 1：dogfood 场景 1（trivial 通过路径）
- 在本仓库扫一处真 typo（grep `\b(的的|占行|tmpdr|exsiting)\b` 等启发式）；
- 用 `harness trivial "<title>"` 跑：
  1. 创建 trivial 任务；
  2. 编写 trivial-spec.md（3 段 ≤ 1 KB）；
  3. 改 1 行代码 + 加 1 unit test 断言修正后行为；
  4. `harness next` → 流转 executing → trivial-guard 全绿 → done；
  5. 产 ≤ 200 字 `交付总结.md`；
- 落 dogfood log 到 chg-05 session-memory.md `## dogfood 场景 1` 段；
- 单测 `tests/test_dogfood_trivial_pass.py`（tmpdir 子进程版）：覆盖 5 节点全绿。

### Step 2：dogfood 场景 2（trivial-guard 升级路径）
- 创建 trivial 任务 → 故意改 15 行（破阈值）→ `harness next` → 验证：
  - runtime stage 回切 executing；
  - task_type=bugfix；
  - upgraded_from=trivial 留痕；
  - stdout 含升级提示句；
- 落 dogfood log；
- 单测 `tests/test_dogfood_trivial_upgrade.py`（tmpdir 子进程版）。

### Step 3：dogfood 场景 3（混合 chg 级 trivial flag）
- 创建一个 fake bugfix（tmpdir）→ 拆 chg-01 trivial=true / chg-02 trivial=false → `harness next` 推进 chg-01 → 验证 dispatch trivial executing；推进 chg-02 → 验证 dispatch 标准 executing；
- 落 dogfood log；
- 单测 `tests/test_dogfood_mixed_chg_trivial.py`（tmpdir 子进程版）。

### Step 4：reviewer.md 加 §trivial 通道边界检查段
- 编辑 `.workflow/context/roles/reviewer.md` 末尾加 §trivial 通道边界检查段（4 项清单）；
- grep 自检命中。

### Step 5：review-checklist.md 加 trivial 检查项
- 检查 `.workflow/context/team/review-checklist.md` 是否存在，不存在则创建；
- 加 §trivial 通道清单（5 行）；
- grep 自检命中。

### Step 6：harness validate --contract trivial-channel 实现
- 在 `validate_contract.py`（或同等 lint 模块）新增 `validate_trivial_channel(repo_path) -> tuple[bool, list[str]]`：
  - 扫所有 trivial 任务（task_type=trivial 或 chg trivial=true）；
  - 校验工件 KB 限额（trivial-spec.md ≤ 1 KB）；
  - 校验 upgraded_from 字段语义（若有则必须配套 bugfix.md）；
  - 校验 chg 级 trivial flag 一致性（plan.md 是否含 §4 的话需有 trivial 豁免标识）；
- 在 `cli.py` 的 `validate --contract` choices 加 `trivial-channel` + `all`；
- 单测 `tests/test_validate_trivial_channel.py`：5 用例（全绿 / KB 超 / upgraded_from 不一致 / chg flag 不一致 / 路径错位）。

### Step 7：硬门禁六 / 七 / 契约 7 全仓 grep 自检
- 跑 `grep -nE "(req-49|chg-(01|02|03|04|05)|trivial-[0-9]+)" --include=*.md -r` → 命中行核对带 ≤ 15 字描述；
- 修复任何裸 id 引用；
- 再跑断言命中 = 0 裸 id。

### Step 8：req-49 端到端 dogfood log + 归档预演
- 在 chg-05 session-memory.md `## req-49 端到端 dogfood log` 段记录：
  - 派发次数（≤ 5 次符合 AC-08）；
  - 各 stage 时长；
  - 工件 KB 总量；
  - trivial-guard 触发情况；
- 跑 `harness validate --human-docs` + `harness validate --contract all` exit 0。

## 2. 验证

### Unit 测试
- `tests/test_dogfood_trivial_pass.py`：3 用例（端到端通过 + 工件存在 + 字数限额）；
- `tests/test_dogfood_trivial_upgrade.py`：3 用例（升级触发 + runtime 字段 + 数据保留）；
- `tests/test_dogfood_mixed_chg_trivial.py`：4 用例（chg-01 dispatch trivial / chg-02 dispatch 标准 / 切换正确 / 工件落位）；
- `tests/test_validate_trivial_channel.py`：5 用例。

### Manual 测试
- 在本仓库挑真 typo 跑 `harness trivial` → 检查全链路；
- 跑 `harness validate --contract all` exit 0。

### AC mapping
- AC-07 → Step 1 + Step 2 + Step 3 + tests/test_dogfood_*.py；
- AC-08 → Step 8（dogfood log 派发次数断言）；
- AC-09 → Step 7 grep 自检；
- AC-10 → Step 6 + tests/test_validate_trivial_channel.py。

## 3. 硬序约束

- Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7 → Step 8（线性硬序）；
- 本 chg 完成后 req-49 进入 done 阶段；
- 本 chg 依赖 chg-01 / chg-02 / chg-03 / chg-04 全部已落地。

## 4. 测试用例设计

> regression_scope: full  # dogfood 场景跨整个 trivial 通道全链路 + 跨 chg 边界，触发 full 回归
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - .workflow/context/roles/reviewer.md（加 §trivial 通道边界检查段）
> - .workflow/context/team/review-checklist.md（加 §trivial 通道清单）
> - src/harness_workflow/validate_contract.py（新增 validate_trivial_channel + trivial-channel choice）
> - src/harness_workflow/cli.py（validate --contract choices 扩 trivial-channel）
> - tests/test_dogfood_trivial_pass.py / test_dogfood_trivial_upgrade.py / test_dogfood_mixed_chg_trivial.py / test_validate_trivial_channel.py（新增 4 测试模块）
> - 间接波及：所有 trivial 通道功能（chg-01 ~ chg-04 已落代码端到端测试）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-Dogfood-01（场景 1） | tmpdir 子进程 trivial 任务 + 1 行 fix + 1 unit test + `harness next` 全链路 | runtime stage 流转 trivial_define → executing → done + trivial-spec.md ≤ 1 KB + 交付总结.md ≤ 200 字 + feedback.jsonl 5 事件 | AC-07 / AC-08 | P0 |
| TC-Dogfood-02（场景 2） | tmpdir 子进程 trivial 任务 + 15 行改动 + `harness next` | runtime stage 回切 executing + task_type=bugfix + upgraded_from=trivial + trivial-spec.md 保留 + bugfix.md 创建 | AC-07 | P0 |
| TC-Dogfood-03（场景 3） | tmpdir 子进程 bugfix + chg-01 trivial=true + chg-02 trivial=false + `harness next` 各 1 次 | chg-01 走 trivial executing（briefing 含 trivial=true）；chg-02 走标准 executing | AC-07 / AC-N1 | P0 |
| TC-01 | `validate_trivial_channel(tmpdir_clean_trivial)` | `(True, [])` | AC-10 | P0 |
| TC-02 | `validate_trivial_channel(tmpdir_with_2KB_trivial_spec)` | `(False, ["trivial-spec.md > 1 KB 限额"])` | AC-10 | P0 |
| TC-03 | `validate_trivial_channel(tmpdir_with_inconsistent_chg_flag)` | `(False, ["chg-01 trivial=true 但产出 plan.md §4"])` | AC-10 | P0 |
| TC-04 | `validate_trivial_channel(tmpdir_with_orphan_upgraded_from)` | `(False, ["upgraded_from=trivial 但无 bugfix.md"])` | AC-10 | P0 |
| TC-05 | `harness validate --contract all` 在干净仓库跑 | exit 0 | AC-10 | P0 |
| TC-06 | grep `reviewer.md` 含 §trivial 通道边界检查 | 命中 ≥ 1 | AC-09 | P1 |
| TC-07 | grep `review-checklist.md` 含 trivial 通道清单条目 | 命中 ≥ 5 行 | AC-09 | P1 |
| TC-08 | dogfood log 派发次数断言 | ≤ 5 次（AC-08） | AC-08 | P0 |
| TC-09 | grep `(req-49\|chg-0[1-5])` 全仓 markdown 命中行 | 全部带 ≤ 15 字描述（裸 id 命中数 = 0） | AC-09 | P1 |
| TC-Dogfood-04 | 真仓库（本仓库非 tmpdir）执行 `harness trivial` 修真 typo | 端到端走通 + commit log 含 `trivial: <title>` 形态 | AC-07 | P0 |
| TC-10（反例） | trivial 任务 stdout 出现 A/B/C 选项 | 0 命中 | AC-09 | P1 |
| TC-11（反例） | trivial 任务 done 阶段交付总结无「本阶段已结束」 | lint 警告 | AC-09 | P1 |
