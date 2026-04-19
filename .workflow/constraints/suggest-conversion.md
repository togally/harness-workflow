# Suggest 批量转换约束

## 约束标题
Suggest 批量转换约束

## 适用范围
`harness suggest --apply-all` 命令及任何等效的批量 suggest 转换操作。

## 核心规则

1. `harness suggest --apply-all` 必须将所有 pending suggest 打包为**单一需求**。禁止产生多个并行的需求目录。
2. 禁止逐条创建独立需求（无论是通过脚本、循环还是其他自动化方式）。所有 pending suggest 必须在同一个 `requirement.md` 中被统一承接。
3. 打包后的 `requirement.md` 必须包含所有 suggest 的标题和摘要列表，确保需求范围可追溯。
4. 违反本约束视为触发 regression，必须记录到 `regression/diagnosis.md`，并视情况回滚错误创建的多余需求目录。

## 例外情况
无例外。即使 suggest 数量再多、主题差异再大，也必须打包为一个需求，在需求内部通过变更拆分来处理。

## 检查点
执行 `suggest --apply-all` 前，agent 必须确认自己正在使用 `--pack-title` 或接受默认打包行为，并明确知晓本约束的存在。
