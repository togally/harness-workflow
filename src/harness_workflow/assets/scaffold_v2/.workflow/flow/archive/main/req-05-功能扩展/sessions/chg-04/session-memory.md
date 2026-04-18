# chg-04 Session Memory — 交互式需求列表选择

## 执行状态
- [x] 步骤 1：分析 enter_workflow 和 archive 现有实现
- [x] 步骤 2：新增 list_done_requirements 和 list_active_requirements（core.py）
- [x] 步骤 3：新增 prompt_requirement_selection（cli.py）
- [x] 步骤 4：修改 archive_parser requirement 为 nargs="?"
- [x] 步骤 5：修改 enter_parser 增加可选 req_id
- [x] 步骤 6：更新 enter_workflow 函数签名增加 req_id=""

## 关键决策
- `prompt_requirement_selection` 使用 `questionary.select()`（单选，非 checkbox）
- 非 TTY 环境直接返回 default_value（preselect 或首项）
- archive 无 done 需求时打印提示并 return 1（不报错）
- enter 无 active 需求时仍正常进入 harness mode（不强制要求选择）
- archive preselect：传入 req-id 如果在列表中则预选，否则选首项

## 修改位置
- `src/harness_workflow/core.py`：`list_done_requirements()`、`list_active_requirements()`、`enter_workflow()` 签名
- `src/harness_workflow/cli.py`：`prompt_requirement_selection()`、archive/enter parser、main() 逻辑
