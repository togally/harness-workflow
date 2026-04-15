# 工具：Bash

**类型：** 内置工具
**状态：** active

## 适用场景
- 执行编译命令（mvn compile、npm build 等）
- 运行测试命令
- 查看日志文件（tail、cat 大文件）
- 文件系统操作（mkdir、mv、rm）
- Git 操作

## 不适用场景
- 读取文件内容（用 Read）
- 搜索文件（用 Glob）
- 搜索内容（用 Grep）
- requirement_review / planning / acceptance 阶段

## 注意事项
- 删除操作（rm -rf）属于高风险，执行前必须触发风险扫描
- regression 阶段只允许只读命令（查日志、查状态），不得修改文件
- 命令超时默认 120s，长命令设置 timeout 参数

## 迭代记录
