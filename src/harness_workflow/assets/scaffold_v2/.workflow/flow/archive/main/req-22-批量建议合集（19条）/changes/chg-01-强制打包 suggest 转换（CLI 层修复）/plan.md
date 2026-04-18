# chg-01-强制打包 suggest 转换（CLI 层修复）执行计划

## 执行步骤

### Step 1：分析现有 `apply_all_suggestions` 实现
- 读取 `src/harness_workflow/core.py` 中 `apply_all_suggestions()` 的完整代码
- 确认 `create_requirement()` 调用点以及 requirement.md 模板渲染机制
- 确认 `load_requirement_runtime()` 在创建需求后返回的 `req_id`

### Step 2：设计 requirement.md 增强内容写入方案
- 检查 `create_requirement()` 使用的模板 `requirement.md.tmpl`
- 决定是在模板中预留 suggest 列表占位符，还是在 `apply_all_suggestions()` 中后处理追加内容到生成的 `requirement.md`
- 确保追加内容包含：每条 suggest 的 ID 和标题/摘要

### Step 3：修改 `core.py`
- 调整 `apply_all_suggestions()`：
  - 保留现有的 pending suggest 收集逻辑
  - 保留 pack_title 处理逻辑（显式标题 > 默认标题）
  - 在 `create_requirement()` 成功后，获取新生成的 requirement 目录
  - 将 suggest 清单追加写入该目录的 `requirement.md`
  - 保留删除 suggest 文件的逻辑

### Step 4：修改 `cli.py`
- 更新 `suggest_parser` 的 help 文本：
  - `--apply-all`：改为 "Apply all pending suggestions as a single packed requirement."
  - `--pack-title`：改为 "Title for the packed requirement when using --apply-all (defaults to '批量建议合集（{n}条）')."

### Step 5：更新或补充测试
- 检查 `tests/test_cli.py` 或相关测试文件中是否有 `apply_all_suggestions` 的测试
- 若有，更新断言以匹配新的强制打包行为
- 若缺少覆盖，补充最小测试确保打包后只生成 1 个 requirement

### Step 6：本地验证
- 运行 `python -m pytest tests/test_cli.py`（或对应测试文件）
- 手动执行 `harness suggest --apply-all` 的等价调用验证行为

## 产物清单
- `src/harness_workflow/core.py`（修改）
- `src/harness_workflow/cli.py`（修改）
- `tests/test_cli.py` 或新增测试文件（修改/新增）

## 预计消耗
- 文件读取：3-5 次（core.py、cli.py、模板文件、测试文件）
- 工具调用：约 10 次
- 风险：低（逻辑改动范围小，已有函数结构清晰）
