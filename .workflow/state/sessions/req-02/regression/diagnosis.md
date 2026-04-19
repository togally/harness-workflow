## 问题描述（第二轮更新）

用户纠正：`context/experience/tool/` 价值存疑的真正原因不是目录多余，而是 `.workflow/` 中丢失了整个 `tools/` 工具层。`context/experience/tool/` 是工具使用**经验**的正确位置，缺失的是工具**定义与规则**的独立目录。

---

## 问题描述（第一轮）

用户在 requirement_review 阶段反映：当前 .workflow/ 结构中"好像多了一个versions目录和一个tools层"，认为这些目录是多余的。

## 证据

**versions/ 目录：**
- 位置：`.workflow/versions/active/v0.2.0-refactor/`
- 文件：`meta.yaml`（含 locked_version, locked_stage, active_versions 等字段）、`progress.yaml`（含 stage 进度追踪）
- 这两个文件均为 harness CLI 内部生成的执行状态文件
- `context/index.md` 加载规则中无任何对 `versions/` 的引用

**tool/ 层：**
- 位置：`.workflow/context/experience/tool/harness.md`
- 内容：空占位符（"Placeholder experience file."）
- `state/experience/index.md` 中有引用（executing 阶段）
- 但仅一个空文件，`tool/` 子目录作为独立分类层级价值有限

## 根因分析

两个问题均为设计层面的分包合理性问题：

1. `versions/` 是 harness CLI 内部状态追踪目录，与 `context/rules/workflow-runtime.yaml` 性质相同（CLI 产物放入了 .workflow/ 知识结构），不是 agent 需要读取的知识内容，但 context/index.md 也未引用它。

2. `context/experience/tool/` 是否值得作为独立分类与 `stage/`、`risk/` 并列，尚未经过设计审查。目前只有一个空文件，该层级是否继续保留、合并或废弃是需求层面的决策。

## 结论（第二轮）

- [ ] 误判为 regression
- [x] 真实问题（需求范围遗漏）

`tools/` 工具层在 req-01 迁移时被整体丢弃，未在新 `.workflow/` 中建立对应结构。这是结构性遗漏，需补入 req-02 需求范围。`context/experience/tool/` 目录本身是正确的，不应质疑其存在。

## 路由决定（第二轮）

- 问题类型：需求/设计层面（迁移遗漏）
- 目标阶段：requirement_review（当前所在阶段）
- 操作：更新 req-02 requirement.md，新增 tools/ 工具层恢复任务

---

## 结论（第一轮）

- [x] 误判为 regression
- [ ] 真实问题

两个问题均是**需求范围遗漏**，应在 req-02 requirement_review 阶段更新需求文档，而非开启独立 regression。

## 路由决定（第一轮）

- 问题类型：需求/设计层面
- 目标阶段：requirement_review（当前所在阶段）
- 操作：harness regression --reject，更新 req-02 requirement.md 以涵盖这两个问题
