# Session Memory — chg-02（CLI 路径迁移 flow layout）

## 1. Current Goal

chg-02 执行完毕。新增 FLOW_LAYOUT_FROM_REQ_ID 常量 + _use_flow_layout helper + 四个 handler 改写 + pytest 覆盖三层级。

## 2. Current Status

全部步骤已完成 ✅。

## 3. Validated Approaches

### 步骤完成情况

- ✅ Step 1: 盘点既有 layout 常量与 handler 调用链
  - 定位 LEGACY_REQ_ID_CEILING=38 / FLAT_LAYOUT_FROM_REQ_ID=39 / `_use_flat_layout`
  - 所有调用点：lines 4193/4361/4424/4486/4519/5879（含 _next_chg_id）

- ✅ Step 2: 新增 `FLOW_LAYOUT_FROM_REQ_ID = 41` + `_use_flow_layout` helper
  - 位置：workflow_helpers.py line ~80（常量） + line ~3790（helper）
  - helper 注释明确 `flow ⊂ flat` 语义

- ✅ Step 3: 改写 create_requirement（flow 分支插入 flat 分支前）
  - flow: `.workflow/flow/requirements/{req-id}-{slug}/requirement.md`

- ✅ Step 4: 改写 create_change（含 req_dir 解析路径分流）
  - flow: `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/`
  - 变更简报 placeholder 仅 flat 分支生成，flow 分支不生成

- ✅ Step 5: 改写 create_regression（req_dir 解析 + 三分支）
  - flow: `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/`

- ✅ Step 6: 改写 archive_requirement（`is_flow_req` + 独立 target_parent 路径）
  - flow: `.workflow/flow/archive/{branch}/req-{req-id}-{slug}/`
  - sessions 迁移跳过（flow 子树已内嵌）

- ✅ Step 7: 扩展 _next_chg_id（flow 分支：扫 flow req_dir/changes/）
  - 三分支互斥顺序：flow → flat → legacy

- ✅ Step 8: 新增 pytest
  - `tests/test_use_flow_layout.py`：23 用例全绿
  - 覆盖 AC-03/04/05/06

- ✅ Step 9: 自检
  - `grep -c "FLOW_LAYOUT_FROM_REQ_ID"` → 3 (定义 + helper + 注释)
  - `grep -c "_use_flow_layout"` → 11
  - 全量 pytest：428 passed, 1 pre-existing fail (test_smoke_req28 README)

## 4. Failed Paths

- 初始写法使 req-99（虚拟测试占位）用于 flat 测试但 req-99 >= 41 触发 flow → 4 个已有测试失败
  - 修复：将 `tests/test_create_requirement_flat.py` / `test_regression_independent_title.py` / `test_ff_mode_auto_reset.py` 中 req-99（虚拟测试占位）改为 req-40（阶段合并与用户介入窄化）

## 5. Default-pick 清单

- test_use_flow_layout.py 并入新文件（非 append 进既有文件），方便独立维护
- `_next_chg_id` for flow layout 扫 `req_dir/changes/`（即 flow req dir 的 changes/ 子目录），不扫 state/sessions/（因为 flow 下没有 state/sessions 机器型文档）

## 6. Next Steps

- 交 testing 独立复核
- chg-03（validate_human_docs 重写删四类 brief）并行已完成

## 7. Open Questions

- 无

---

本阶段已结束。
