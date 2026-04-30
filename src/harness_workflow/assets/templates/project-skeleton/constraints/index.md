---
schema_version: 1
scope: constraints
created_by: req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-03（索引懒加载-index-md与加载链改造）
---

# 项目级 constraints 索引

| path | title | scope | when_load | 备注 |
|------|-------|-------|-----------|------|
| <!-- 示例：my-rule.md --> | <!-- 示例：项目独有的代码风格约束 --> | constraints | always | <!-- 加载时机：always / on-stage:executing / on-keyword:lint --> |

> **schema 说明**：
> - `path`：相对本 index.md 同目录的文件路径；
> - `title`：≤ 20 字简短描述（与硬门禁六口径一致）；
> - `scope`：固定 `constraints`（本 index 限本目录）；
> - `when_load` ∈ `{always, on-stage:{stage}, on-keyword:{kw}}`：加载时机控制；
> - `备注`：任意补充说明，可空。
>
> agent 按 `when_load` 解析后按需加载条目（详见 `.workflow/context/roles/role-loading-protocol.md` Step 7.6.1）。
