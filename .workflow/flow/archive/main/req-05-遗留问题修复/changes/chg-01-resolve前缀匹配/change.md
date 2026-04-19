# Change: resolve_change_reference 前缀匹配

## 目标

为 `resolve_change_reference` 添加前缀匹配逻辑，使其与 `resolve_requirement_reference` 行为一致。修复后 `harness change --requirement req-xx`（短 ID）和 `harness archive req-xx`（短 ID）均能正确解析含标题的目录名。

## 范围

- 修改 `src/harness_workflow/core.py` 中的 `resolve_change_reference` 函数

## 验收标准

- [ ] `resolve_change_reference` 支持前缀匹配（如 `chg-01` 匹配 `chg-01-xxx`）
- [ ] 短 ID 引用在 `harness change` 和 `harness archive` 命令中正常工作

## 依赖

无
