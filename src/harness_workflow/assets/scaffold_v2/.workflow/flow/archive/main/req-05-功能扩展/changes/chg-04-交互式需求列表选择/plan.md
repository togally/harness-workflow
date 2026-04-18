# 执行计划

## 依赖关系
- **前置依赖**：chg-03（archive_requirement 已支持 git branch 默认 folder）
- **后置依赖**：chg-05（归档完整迁移叠加到同一函数）

## 执行步骤

### 步骤 1：了解 enter_workflow 和 archive 现有实现
1. 阅读 `core.py` 中 `enter_workflow()` 函数实现，了解其如何读取 `runtime.yaml`
2. 阅读 `cli.py` 第 127-130 行 archive 子命令定义，确认当前参数结构
3. 查找 `state/requirements/` 下的 YAML 文件结构，了解 `req_id`、`title`、`stage`、`status` 字段

### 步骤 2：新增 list_done_requirements 和 list_active_requirements 辅助函数
1. 在 `core.py` 中新增 `list_done_requirements(root: Path) -> list[dict]`：
   - 扫描 `state/requirements/*.yaml`，筛选 `status == "done"` 或 `stage == "done"` 的条目
   - 返回 `[{"req_id": "req-05", "title": "功能扩展", "stage": "done"}, ...]`
2. 新增 `list_active_requirements(root: Path) -> list[dict]`：
   - 读取 `runtime.yaml` 中的 `active_requirements` 列表
   - 从 `state/requirements/` 补充 title 和 stage 字段

### 步骤 3：新增 prompt_requirement_selection 函数（cli.py）
1. 在 `cli.py` 的 `prompt_platform_selection` 之后新增 `prompt_requirement_selection(requirements, preselect=None) -> str | None`：
   - 若 `requirements` 为空，打印提示并返回 `None`
   - 构造选项列表：`[{"name": "req-xx 标题（阶段）", "value": "req-xx"}, ...]`
   - 使用 `questionary.select()` 展示单选列表，`default` 设为 `preselect`
   - 非 TTY 环境直接返回 `preselect`（或第一项）

### 步骤 4：修改 cli.py archive 参数定义
1. 将 `archive_parser.add_argument("requirement", ...)` 改为 `nargs="?"` 可选位置参数：
   ```python
   archive_parser.add_argument("requirement", nargs="?", default=None, help="Requirement title or id (optional, shows list if omitted).")
   ```
2. 在 `args.command == "archive"` 处理逻辑中：
   - 读取 done 需求列表
   - 若列表为空，打印提示并返回
   - 调用 `prompt_requirement_selection(done_reqs, preselect=args.requirement)`
   - 用选择结果调用 `archive_requirement(root, selected, folder=args.folder)`

### 步骤 5：修改 cli.py enter 参数定义
1. 在 `enter_parser` 增加可选位置参数：
   ```python
   enter_parser.add_argument("req_id", nargs="?", default=None, help="Requirement id to enter (optional).")
   ```
2. 在 `args.command == "enter"` 处理逻辑中：
   - 若 `args.req_id` 非空，直接调用 `enter_workflow(root, req_id=args.req_id)`
   - 否则读取 active 需求列表，调用 `prompt_requirement_selection`，再调用 `enter_workflow`

### 步骤 6：更新 enter_workflow 函数签名（core.py）
1. 若 `enter_workflow` 不支持 `req_id` 参数，增加 `req_id: str = ""` 参数
2. 传入 req_id 时，设置对应需求为 `current_requirement` 后进入 harness 模式

## 预期产物
1. `core.py`：`list_done_requirements()`、`list_active_requirements()` 辅助函数
2. `cli.py`：`prompt_requirement_selection()` 函数，archive/enter 命令参数更新
3. 交互式列表在支持 TTY 的终端中正常弹出

## 验证方法
1. 有 done 需求时：`harness archive` 弹出列表，用方向键选择，回车确认执行归档
2. 无 done 需求时：`harness archive` 打印 "没有可归档的需求" 类提示并退出
3. `harness archive req-05` 弹出列表且 req-05 预选中
4. `harness enter` 弹出 active 需求列表
5. `harness enter req-05` 直接进入，不弹列表
6. CI 环境（非 TTY）：`echo "" | harness archive` 不阻塞，使用第一个 done 需求或跳过

## 注意事项
1. 使用 `questionary.select()` 而非 `checkbox()`（单选）
2. `sys.stdin.isatty()` 检测非交互环境，降级行为：直接使用 preselect 或返回 None
3. archive 的 `requirement` 参数改为可选后，需确保 `harness archive req-xx` 的原有直接调用方式仍有效（`nargs="?"` 满足此需求）
4. 列表显示格式统一：`req-xx 标题（阶段）`，阶段来自 state YAML 的 `stage` 字段
5. `enter_workflow` 若需修改签名，确保现有调用位置（不传 req_id 的情况）不受影响
