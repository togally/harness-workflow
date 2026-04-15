# chg-05 Session Memory — 归档完整迁移

## 执行状态
- [x] 步骤 1：分析 archive_requirement 执行顺序
- [x] 步骤 2：增加 sessions 迁移逻辑（state/sessions/req-xx/ → target/sessions/）
- [x] 步骤 3：增加 state.yaml 迁移逻辑（在 for 循环内 save_simple_yaml 之后 shutil.move）

## 关键决策
- state.yaml 迁移在 save_simple_yaml 之后、break 之前执行（确保 status=archived 已写入）
- sessions 迁移在 runtime 更新之后执行（archived_req_id 必须已赋值）
- sessions 目录不存在时静默跳过（不报错），兼容旧需求
- 移动目标：`target / "state.yaml"` 和 `target / "sessions"`

## 修改位置
- `src/harness_workflow/core.py`：`archive_requirement()` 函数中
  - for 循环内 save_simple_yaml 后加 shutil.move(req_file, target/"state.yaml")
  - save_requirement_runtime 后加 sessions 迁移块
