# artifacts/project/ — 项目级机器型文档承载层（主路径）

> 本目录由 req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-01（契约层路径迁移-无branch项目级-双轨过渡）OQ-A = D-modified 开放。

## 用途

本目录是项目级机器型文档的**主路径承载层**（无 branch 维度，跟项目走）。下游用户把项目独有的规则、经验、工具写入此处，所有 git branch 均可读取，不再因 `{branch}` 切换而消失。

## 子目录结构

```
artifacts/project/
├── constraints/      # 项目独有规则 / 边界约束（agent 加载链覆盖全局 .workflow/context/constraints/）
├── experience/       # 项目独有经验沉淀（roles / tool / risk / regression / stage 五分类）
└── tools/            # 项目独有工具 catalog / index / protocols / keywords
```

## OQ-A = D-modified（双轨过渡）

- **主路径（本目录）**：`artifacts/project/{constraints,experience,tools}/`（无 branch 维度，跟项目走）；新建一律入此；
- **branch-path 兼容路径**：`artifacts/{branch}/project/`（req-51（项目级规则-经验-工具支持从制品引入）OQ-1 = B-modified 原路径）作为加载链兼容存量；
- **退役计划**：legacy 路径在后续 req（一次大版本归档）统一退役为只读，不在本 req 内删除。

## 契约引用

- `repository-layout.md` §2.1 双轨过渡 fallback 段
- `harness-manager.md` 硬门禁五例外白名单
- `role-loading-protocol.md` Step 7.6 项目级覆盖加载
- `tools-manager.md` Step 2.0 项目级合并
