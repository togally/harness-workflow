# Session Memory: req-12 / chg-01

## 变更目标
在 `harness suggest` 中新增 `--apply-all` 选项，批量将所有 pending suggest 转为正式需求。

## 执行日志

- [x] Step 1: 读取 `cli.py`，在 `suggest_parser` 中新增 `--apply-all` 参数
- [x] Step 2: 读取 `core.py`，在 `create_suggestion` 附近新增 `apply_all_suggestions(root)` 函数
- [x] Step 3: 在 `cli.py` 的 `suggest` 命令分支中增加 `--apply-all` 的处理
- [x] Step 4: 实现输出格式（Applied N suggestion(s): ...）
- [x] Step 5: 本地测试验证（临时项目验证通过）

## 产出文件
- `src/harness_workflow/cli.py`
- `src/harness_workflow/core.py`

## 关键决策
- 复用现有的 `create_requirement` 函数，逐条创建需求
- 成功后通过字符串替换将 suggest 的 `status: pending` 更新为 `status: applied`
- 返回 0 当全部成功，返回 1 当有任何失败

## 遇到的问题
- 无

## 下一步
- 进入 chg-02：文档更新与验证
