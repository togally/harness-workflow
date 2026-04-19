# Requirement

## 1. Title

所有的 regression 命令必须沉淀经验，因为 regression 无论作为问题还是需求都说明流程存在可改进之处

## 2. Goal

在 regression 流程结束（确认、取消、回退 testing、转 change/req）时，自动在经验目录生成沉淀文件，确保每个 regression 都有经验记录。

## 3. Scope

**包含**：
- 修改 `core.py` 的 `regression_action` 函数
- 在 regression 结束时自动创建/检查经验文件 `.workflow/context/experience/regression/{regression_id}.md`
- 文件不存在时生成标准模板并提示用户后续补充
- `confirm` 操作现在会结束 regression（清除 `current_regression`）

**不包含**：
- 强制交互式输入经验内容（先生成模板，允许用户后续编辑）
- 对历史 regression 的追溯补录

## 4. Acceptance Criteria

- [ ] regression 结束时（confirm / cancel / reject / testing / change / requirement）自动检查经验文件
- [ ] 若经验文件不存在，自动生成模板文件并提示
- [ ] `confirm` 操作正确结束 regression 并沉淀经验
- [ ] 文档已更新

## 5. Split Rules

### chg-01 regression 经验沉淀强制化
- 修改 `regression_action`，在每个结束分支前插入 `_ensure_regression_experience`
- 新增 `_ensure_regression_experience(root, regression_id)` 核心函数
- 生成模板路径 `.workflow/context/experience/regression/{regression_id}.md`

### chg-02 文档与验证
- 更新 README 中 regression 命令的说明
- 本地验证 regression 流程
- pipx inject 重新安装
