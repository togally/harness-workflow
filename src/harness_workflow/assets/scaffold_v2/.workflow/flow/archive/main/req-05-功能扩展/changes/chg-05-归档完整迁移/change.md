# Change

## 1. Title
归档完整迁移（sessions + state.yaml 打包进归档目录）

## 2. Goal
在归档操作中，将需求的会话记录（`state/sessions/req-xx/`）和需求状态文件（`state/requirements/req-xx-{title}.yaml`）一并迁移到归档目录内，实现需求所有关联文档的集中存放，归档后原位置不保留对应文件。

## 3. Requirement
- req-05-功能扩展

## 4. Scope
**包含**：
- `src/harness_workflow/core.py`：`archive_requirement()` 函数中增加 sessions 迁移逻辑
  - `state/sessions/req-xx/` → `{archive_target}/sessions/`（目录级迁移）
- `src/harness_workflow/core.py`：`archive_requirement()` 函数中增加 state.yaml 迁移逻辑
  - `state/requirements/req-xx-{title}.yaml` → `{archive_target}/state.yaml`（文件重命名迁移）
- 迁移后从原位置删除（`shutil.move` 实现移动语义）

**不包含**：
- `.workflow/flow/requirements/req-xx/` 的迁移（已由现有 `shutil.move` 处理）
- `state/requirements/*.yaml` 中的 `status` 字段更新（已由现有逻辑处理，迁移后文件已不在原位）
- 制品仓库生成（属于 chg-06）

## 5. Acceptance Criteria
- [ ] 归档后 `.workflow/state/sessions/req-xx/` 不存在于原位
- [ ] 归档后 `.workflow/state/requirements/req-xx-{title}.yaml` 不存在于原位
- [ ] 归档目录 `{archive_target}/sessions/` 存在且包含原 sessions 内容
- [ ] 归档目录 `{archive_target}/state.yaml` 存在且内容来自原 requirements YAML
- [ ] sessions 或 state 文件不存在时静默跳过（不报错）

## 6. Dependencies
- **前置**：chg-04（交互式选择已确保 archive 流程的 req-id 来源清晰）
- **后置**：chg-06（制品仓库生成读取归档后的目录结构，需此迁移完成后才能访问 sessions/）
