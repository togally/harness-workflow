# Experience Index

## 经验分类与加载规则

| Stage | 加载分类 |
|-------|---------|
| `requirement_review` / `planning` | `flow/` |
| `executing` | `flow/` + `tools/` |
| `testing` / `acceptance` | `evaluation/` + `flow/` |
| `regression` | `evaluation/` + `constraints/` |

## 目录说明

| 目录 | 内容 |
|------|------|
| `context/` | 上下文管理、索引设计、加载策略相关经验 |
| `tools/` | 工具使用技巧、prompt 模式、工具选择经验 |
| `flow/` | 执行编排、需求拆分、计划制定相关经验 |
| `state/` | 状态管理、恢复机制、session-memory 使用经验 |
| `evaluation/` | 测试设计、验收判定、regression 诊断经验 |
| `constraints/` | 风险识别、失败恢复、约束执行相关经验 |

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
