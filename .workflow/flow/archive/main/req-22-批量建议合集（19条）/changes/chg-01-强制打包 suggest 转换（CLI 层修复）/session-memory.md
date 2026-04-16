# chg-01 执行记录

## 修改步骤

1. **定位源码**：测试脚本通过 `PYTHONPATH=src` 使用的是项目源码 `src/harness_workflow/`，因此实际修改了：
   - `/Users/jiazhiwei/claudeProject/harness-workflow/src/harness_workflow/core.py`
   - `/Users/jiazhiwei/claudeProject/harness-workflow/src/harness_workflow/cli.py`

2. **core.py 修改**：
   - 在 `apply_all_suggestions()` 函数开头添加注释：`# 本函数强制将所有 pending suggest 打包为单一需求`
   - 在 `create_requirement()` 调用后添加注释：`# 强制只创建 1 个需求，无论 pending 数量多少`
   - 在创建需求成功后，向生成的 `requirement.md` 追加 `## 合并建议清单` 段落，列出所有被合并的 suggest ID 和标题

3. **cli.py 修改**：
   - 将 `--apply-all` 的 help 文本从英文改为中文说明：`"将所有 pending suggest 打包为单一需求并创建."`
   - `--pack-title` 保留作为标题定制参数

4. **同步 pipx venv**：
   - 将修改后的 `core.py` 和 `cli.py` 复制到 pipx venv 对应路径，确保 `harness suggest --apply-all` 运行时行为一致

## 验证结果

- `python3 /tmp/test_apply_all.py`：3 个 pending suggest 执行 `--apply-all` 后只创建 1 个需求目录 `req-11-批量建议合集（3条）`，suggest 文件全部被删除 — **通过**
- `python3 /tmp/test_apply_all_title.py`：自定义 `--pack-title "My Custom Pack"` 正确生效 — **通过**
- `python3 /tmp/test_apply_all_content.py`：生成的 `requirement.md` 末尾包含 `## 合并建议清单` 及所有 suggest 条目 — **通过**
- `PYTHONPATH=src python3 -m pytest tests/test_cli.py`：17 passed, 36 skipped — **通过**

## 修改的文件路径

- `/Users/jiazhiwei/claudeProject/harness-workflow/src/harness_workflow/core.py`
- `/Users/jiazhiwei/claudeProject/harness-workflow/src/harness_workflow/cli.py`
- `/Users/jiazhiwei/.local/pipx/venvs/harness-workflow/lib/python3.14/site-packages/harness_workflow/core.py`
- `/Users/jiazhiwei/.local/pipx/venvs/harness-workflow/lib/python3.14/site-packages/harness_workflow/cli.py`
