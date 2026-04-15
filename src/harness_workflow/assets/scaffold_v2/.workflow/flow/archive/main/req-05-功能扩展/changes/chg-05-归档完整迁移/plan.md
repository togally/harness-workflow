# 执行计划

## 依赖关系
- **前置依赖**：chg-04（交互式选择已完成，archive 流程稳定）
- **后置依赖**：chg-06（制品仓库读取归档后的 sessions/ 和 state.yaml）

## 执行步骤

### 步骤 1：分析现有 archive_requirement 执行顺序
1. 阅读 `core.py` 第 2988 行起的 `archive_requirement()` 函数
2. 记录关键执行顺序：
   a. `shutil.move(str(req_dir), str(target))` — 移动 flow/requirements/req-xx/ 到归档目录（第 3000 行）
   b. 扫描 `state/requirements/*.yaml` 更新 status（第 3002-3012 行）
   c. 更新 runtime 的 active_requirements（第 3014-3019 行）
3. 确认 `target` 变量为最终归档目录路径（如 `.workflow/flow/archive/main/req-05-功能扩展/`）
4. 确认 `archived_req_id` 变量在步骤 b 中被赋值

### 步骤 2：增加 sessions 迁移逻辑
1. 在 `archive_requirement()` 中，在更新 state/requirements YAML 之后（第 3012 行之后）增加：
   ```python
   # 迁移 state/sessions/req-xx/ 到归档目录
   sessions_src = root / ".workflow" / "state" / "sessions" / archived_req_id
   if sessions_src.exists():
       sessions_dst = target / "sessions"
       shutil.move(str(sessions_src), str(sessions_dst))
   ```

### 步骤 3：增加 state.yaml 迁移逻辑
1. 在 sessions 迁移之后，增加 state.yaml 迁移逻辑：
   - 注意：现有逻辑已找到 `req_file`（`state/requirements/req-xx-{title}.yaml`），在更新 status 后需要将文件移动而非保留
   - 修改现有循环：在 `save_simple_yaml(req_file, state)` 之后，将 req_file 移动到 `target / "state.yaml"`
   ```python
   # 将 state YAML 迁移至归档目录
   state_dst = target / "state.yaml"
   shutil.move(str(req_file), str(state_dst))
   break
   ```
   - 注意：移动后 `req_file` 原位不再存在，runtime 中对该需求的 status 更新需在移动前完成

### 步骤 4：处理 archived_req_id 依赖关系
1. 确认 `archived_req_id` 在步骤 b 中赋值，sessions 迁移需在此之后执行
2. 若 `archived_req_id` 为空（未找到匹配的 state YAML），sessions 迁移通过扫描目录名匹配：
   - `sessions_src = root / ".workflow" / "state" / "sessions" / req_dir.name.split("-")[0]`（取 req-xx 前缀）
   - 或解析 `req_dir.name` 获取 req-id（`re.match(r"(req-\d+)", req_dir.name)`）

### 步骤 5：更新打印信息
1. 归档成功后打印迁移摘要：
   ```python
   if sessions_src.exists():  # 已在迁移前检查，此处可打印
       print(f"Migrated sessions: {sessions_dst}")
   print(f"Migrated state: {state_dst}")
   ```

## 预期产物
1. `archive_requirement()` 在现有逻辑后增加 sessions 和 state.yaml 迁移步骤
2. 归档目录结构完整：`requirement.md`、`changes/`、`sessions/`、`state.yaml`

## 验证方法
1. 准备含 sessions 和 state YAML 的需求（正常 done 流程后的 req-xx）
2. 执行 `harness archive req-xx`，确认：
   - `.workflow/state/sessions/req-xx/` 不存在
   - `.workflow/state/requirements/req-xx-{title}.yaml` 不存在
   - `.workflow/flow/archive/{folder}/req-xx-{title}/sessions/` 存在
   - `.workflow/flow/archive/{folder}/req-xx-{title}/state.yaml` 存在
3. 对没有 sessions 目录的旧需求执行归档，确认不报错

## 注意事项
1. `shutil.move` 在同一文件系统上执行 rename，跨文件系统时会先 copy 再 delete，均能正确工作
2. state YAML 的 `status` 字段更新必须在文件移动之前完成（先写，再 move）
3. `target` 目录在 `shutil.move(req_dir → target)` 之后已存在，sessions 和 state.yaml 可直接放入
4. 若 `archived_req_id` 为空（边缘情况），sessions 目录名需要从 `req_dir.name` 解析 req-id，避免迁移错误目录
5. 不得删除 `state/requirements/` 目录本身，只移动单个文件
