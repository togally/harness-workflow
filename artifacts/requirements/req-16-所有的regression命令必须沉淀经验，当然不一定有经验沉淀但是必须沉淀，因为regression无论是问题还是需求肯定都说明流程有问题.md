# 所有的regression命令必须沉淀经验，当然不一定有经验沉淀但是必须沉淀，因为regression无论是问题还是需求肯定都说明流程有问题

> req-id: req-16 | 完成时间: 2026-04-15 | 分支: main

## 需求目标

在 regression 流程结束（确认、取消、回退 testing、转 change/req）时，自动在经验目录生成沉淀文件，确保每个 regression 都有经验记录。

## 交付范围

**包含**：
- 修改 `core.py` 的 `regression_action` 函数
- 在 regression 结束时自动创建/检查经验文件 `.workflow/context/experience/regression/{regression_id}.md`
- 文件不存在时生成标准模板并提示用户后续补充
- `confirm` 操作现在会结束 regression（清除 `current_regression`）

**不包含**：
- 强制交互式输入经验内容（先生成模板，允许用户后续编辑）
- 对历史 regression 的追溯补录

## 验收标准

- [ ] regression 结束时（confirm / cancel / reject / testing / change / requirement）自动检查经验文件
- [ ] 若经验文件不存在，自动生成模板文件并提示
- [ ] `confirm` 操作正确结束 regression 并沉淀经验
- [ ] 文档已更新

## 变更列表

- **chg-01** regression 经验沉淀强制化：在 regression 流程的任意结束分支中，自动确保存在对应的经验沉淀文件。
- **chg-02** 文档与验证：更新 README 中 regression 命令的说明，本地验证回归流程，并重新安装包。
