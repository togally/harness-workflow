# 开发阶段经验

> 进入开发阶段（development / planning / execution）时自动加载。
> 置信度：low — 新沉淀经验，验证后逐步提升。

## 核心约束

- 每个完成的 change 必须执行并记录 `mvn compile`
- 每个完成的 requirement 必须执行并记录成功的项目启动验证
- 编译失败或启动失败时，进入 regression 流程，先填写 `regression/required-inputs.md`

## 最佳实践

- 开始阶段任务前重新索引经验（re-index experience）
- 本地有编译输出、启动日志、测试失败信息时，AI 应先检查这些信息
- 每个阶段完成后检查是否有成熟经验可以沉淀

## 常见错误

- 未在阶段完成时执行编译验证
- 启动失败后直接要求用户提供信息，而非先检查本地日志
- 经验沉淀遗漏，导致同类问题重复出现
