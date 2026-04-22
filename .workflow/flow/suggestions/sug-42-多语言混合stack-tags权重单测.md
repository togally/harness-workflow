---
id: sug-42
title: 多语言混合仓的 `stack_tags` 权重单测
status: pending
created_at: "2026-04-22"
priority: low
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-01（项目描述扫描器 + project-profile 落地）的 `ProjectScanner` 只测了单一语言场景（pyproject / package / pom / go / cargo 各一）。

现实中存在混合仓（如 python 后端 + node 前端 + go 工具链），`stack_tags` 应按什么规则排序 / 去重？当前实现可能产出 `[python+pyproject, node+package-json, go+mod]` 的无序堆，下游 CTO 派发做领域权重判断时命中不准。

# 建议

新增单测覆盖：

1. 双语混合（py + node）：断言 `stack_tags` 顺序稳定（比如按依赖文件被检测到的字典序）
2. 三语混合（py + node + go）：断言所有都被识别
3. 主语言判断：`language` 字段按哪个 tag 优先？（当前实现可能随机）

若发现权重规则缺失，明确"主语言 = 仓库根第一个匹配的语言"或"按 `pyproject.toml` > `package.json` > `pom.xml` > `go.mod` > `Cargo.toml` 固定优先级"，记入代码注释。

# 验收

- 新增 3-5 条单测
- ProjectScanner 明确权重规则（代码 or 注释）
- TDD 红绿
