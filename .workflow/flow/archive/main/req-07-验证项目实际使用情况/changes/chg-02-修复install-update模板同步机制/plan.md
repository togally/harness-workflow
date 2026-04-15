# Plan: chg-02

## Steps

1. 使用 `python3 -c "import harness_workflow; print(harness_workflow.__file__)"` 找到已安装包位置
2. 读取 `harness_workflow` 包中的 scaffold 模板目录结构
3. 对比 scaffold 与 harness-workflow 仓库最新 `.workflow/` 的差距
4. 检查 `harness install` 的实现逻辑（通常是 `core.py` 或 `cli.py`）：
   - 是否使用了过时的模板路径？
   - 是否只复制了部分文件？
   - 是否有文件被硬编码排除？
5. 检查 `harness update` 的实现逻辑：
   - 是否只更新已知文件，不处理新增文件？
   - 是否有合并冲突处理不当的问题？
6. 修复代码问题
7. 使用 `pipx inject harness-workflow . --force` 重新安装包
8. 在一个临时目录运行 `harness install` 验证最新模板是否正确部署

## Artifacts

- 修复后的 `harness_workflow` 包源码
- 验证记录

## Dependencies

- 依赖 chg-01 的审计结论（确认哪些文件缺失）
