# Change

## 1. Title

CLI 兼容 pytest 补强 + escape hatch 文字落地

## 2. Goal

- 新增 pytest 用例覆盖 "analyst 作为 req_review / planning 派发目标" + "legacy role key 作别名指 opus" + "escape hatch 触发词在角色文档中存在" 三条断言，守住 `harness next` / `harness change` / `harness ff` / `harness status` 在 req-40 之前的既有 req（legacy / mixed / flat 三类 fixture）行为零回归；同时把 escape hatch 文字在 `analyst.md`（chg-01 落地）或 `harness-manager.md`（chg-03 落地）二选一明示落地，确保用户端可触发。

## 3. Requirement

- `req-40`（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））

## 4. Scope

### Included

- **新增 pytest 文件** `tests/test_analyst_role_merge.py`（新建）：
  - `test_role_model_map_has_analyst()`：yaml.safe_load `.workflow/context/role-model-map.yaml` → 断言 `roles['analyst'] == 'opus'`；
  - `test_role_model_map_legacy_aliases()`：断言 `roles['requirement-review'] == 'opus'` + `roles['planning'] == 'opus'`（legacy 别名保留）；
  - `test_analyst_file_exists()`：断言 `.workflow/context/roles/analyst.md` 存在且章节数 ≥ 6；
  - `test_analyst_file_mirror_sync()`：断言 `.workflow/context/roles/analyst.md` 与 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 字节一致；
  - `test_harness_manager_routes_to_analyst()`：grep `.workflow/context/roles/harness-manager.md` 至少 2 处含 `analyst` 字面，且 §3.4 `harness requirement` / `harness change` 两行派发目标已改写；
  - `test_technical_director_auto_advance_clause()`：grep `technical-director.md` 含 "requirement_review → planning 自动" 或等价 + 4 触发词中至少 1 个（"我要自拆"）；
  - `test_stage_role_flow_exemption_clause()`：grep `stage-role.md` 含 "stage 流转点豁免" + "req-40"；
  - `test_index_md_has_analyst_row()`：grep `.workflow/context/index.md` 含 analyst 行 + 合并注释；
- **escape hatch 文字落地**（与 chg-03 协同，本 chg 负责 pytest 层断言 + 在 analyst.md 补一条 "escape hatch 触发词清单" 引用说明，指向 technical-director.md §6.2）；
- **零回归验证**：本 chg executing 阶段跑一次 `pytest` 全量，确认现有用例（67 个 test_*.py 文件）零回归。
- 涉及文件路径：
  - live：`tests/test_analyst_role_merge.py`（新建）+ 可选 `.workflow/context/roles/analyst.md` 补 escape hatch 引用段（与 chg-01 语义衔接，不冲突）
  - mirror：不涉及（tests/ 不在硬门禁五保护面）；如 analyst.md 有增量则同步 mirror。

### Excluded

- **不改** `workflow_helpers.py` / `core.py` 等 CLI 源码（req-40 scope 明示 CLI 零破坏）；
- **不改** `WORKFLOW_SEQUENCE` 常量 / `state/requirements/*.yaml` schema / `runtime.yaml` schema；
- **不跑** dogfood 活证（归属 chg-05）；
- **不做** mirror diff 全量断言（归属 chg-05）；
- **不写** 专业化反馈模板（归属 chg-06）。

## 5. Acceptance

- Covers requirement.md **AC-7**（CLI 兼容性零回归）：
  - `pytest -q` 全量通过（现有 67 个测试文件基线 passed 数 ≥ 当前 baseline，新增至少 8 条 `test_analyst_role_merge.py` 断言全部 passed）；
  - 新增至少 1 条 pytest 断言命中 "analyst 作为 req_review / planning 派发目标"（`test_harness_manager_routes_to_analyst`）；
  - 现有 `test_cli.py` / `test_cli_routing.py` / `test_harness_next_pending_gate.py` / `test_ff_auto.py` / `test_harness_status_pending_line.py` 等 CLI 行为测试零修改、全通过。
- Covers requirement.md **AC-12**（escape hatch 路径）：
  - `grep -q "我要自拆\|我自己拆\|让我自己拆\|我拆 chg" .workflow/context/roles/directors/technical-director.md` 命中（chg-03 落地）；
  - `test_technical_director_auto_advance_clause` 断言通过；
  - 可选 analyst.md 内补 "escape hatch 触发词" 引用段，让 analyst subagent 在运行时能查到用户触发词语义（与 chg-01 互补）。

## 6. Risks

- **风险 1：pytest 新增断言与 role-model-map yaml 结构不匹配**。缓解：先 `python -c "import yaml; print(yaml.safe_load(open('.workflow/context/role-model-map.yaml')))"` 验证结构再写断言；遵循现有 `test_roles_exit_contract.py` / `test_assistant_role_contract7.py` pytest 风格。
- **风险 2：chg-04 依赖 chg-01 / chg-02 / chg-03 落地才能跑通，但 DAG 中 chg-04 与 chg-05 并行**。缓解：default-pick D-1 = B 串行（chg-04 先于 chg-05，两者共同依赖 chg-03 完成）；若 executing 阶段 DAG 改并行，chg-04 必须在 chg-03 mirror diff 零之后启动。
- **风险 3：escape hatch 触发词 4 选 1 识别不一致**。缓解：pytest 用 regex `(我要自拆|我自己拆|让我自己拆|我拆 chg)` 至少命中 1 处即 pass；technical-director.md §6.2 明示 4 触发词字面清单（chg-03 Step 2 落地）。
- **风险 4：scaffold_v2 mirror 的 role-model-map.yaml 与 live 不同步导致 pytest mirror 断言 FAIL**。缓解：chg-02 已在 executing 阶段强制 `diff -rq` 自检；chg-04 pytest 补一条 `test_role_model_map_mirror_sync` 守门。
