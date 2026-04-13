# Experience Index

## 经验分类与加载规则

实际经验内容存储于 `workflow/context/experience/`（stage/, tool/, risk/ 等子目录）。
本文件（`workflow/state/experience/index.md`）是加载规则索引，指向 context/experience/ 的实际文件。

| Stage | 加载分类 |
|-------|---------|
| `requirement_review` / `planning` | `context/experience/stage/requirement.md` |
| `executing` | `context/experience/stage/development.md` + `context/experience/tool/harness.md` |
| `testing` / `acceptance` | `context/experience/stage/testing.md` + `context/experience/stage/acceptance.md` |
| `regression` | `context/experience/stage/regression.md` + `context/experience/risk/known-risks.md` |

## 目录说明

经验内容的实际存储位置为 `workflow/context/experience/`，包含以下分类：

| 目录 | 内容 |
|------|------|
| `context/experience/stage/` | 各阶段（需求、开发、测试、验收、回归）相关经验 |
| `context/experience/tool/` | 工具使用技巧、prompt 模式、工具选择经验 |
| `context/experience/risk/` | 风险识别、已知风险、失败恢复相关经验 |

## 经验沉淀规范

### 触发时机
- after-task hook 执行后
- 每个 stage 完成时
- 发现通用规律时（任何时候）

### 沉淀标准
- 可泛化：不只适用于当前任务，对未来类似场景有参考价值
- 具体：有明确的场景描述和操作建议，不是泛泛而谈
- 非显而易见：不记录常识，只记录踩过的坑和发现的技巧

### 文件格式
每个经验文件命名：`{topic}.md`

```markdown
# {经验标题}

## 场景
<!-- 什么情况下适用 -->

## 经验内容
<!-- 具体做法或规律 -->

## 反例（可选）
<!-- 什么做法会出问题 -->

## 来源
<!-- req-id / chg-id，便于追溯 -->
```

### 更新规则
- 同一主题的新经验 → 追加到已有文件，不新建
- 发现旧经验有误 → 修正并注明修正原因
- 经验过时 → 标记为 deprecated，保留历史

> 注：经验内容存储于 `workflow/context/experience/`，本文件仅为加载规则索引。
