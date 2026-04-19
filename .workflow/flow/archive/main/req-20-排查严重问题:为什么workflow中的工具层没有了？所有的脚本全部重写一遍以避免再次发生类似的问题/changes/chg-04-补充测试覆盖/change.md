# Change: 补充测试覆盖

## 变更目标

在现有测试基础上新增/更新测试用例，验证 `.workflow/tools/` 目录在 `harness init` 和 `harness update` 生命周期中不会被误清理，且 scaffold 同步能正确创建 tools 目录及其核心文件。

## 范围

### 包含
- 修改 `tests/test_cli.py`：
  - 新增一个测试用例，验证 `harness init` 创建的新仓库中包含 `.workflow/tools/` 及关键文件
  - 新增一个测试用例，验证在已存在 `.workflow/tools/` 的仓库中运行 `harness update` 不会将 tools 目录移入 backup
  - 如有必要，更新现有 `test_update_check_and_apply_refresh_skills_and_missing_files` 等测试，增加对 tools 目录存在性的断言
- 运行 `pytest` 确保全部测试通过

### 不包含
- 不修改被测的业务代码（core.py 等）
- 不修改 scaffold 模板目录的内容
- 不引入新的测试框架或依赖

## 验收标准

- [ ] `pytest tests/test_cli.py` 全部通过
- [ ] 至少新增一个测试用例验证 `harness init` 会创建 `.workflow/tools/`
- [ ] 至少新增一个测试用例验证 `harness update` 不会将 `.workflow/tools/` 移入 backup
