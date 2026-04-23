# Experience Index

## 经验分类与加载规则

实际经验内容存储于 `.workflow/context/experience/`（roles/, tool/, risk/ 等子目录）。
本文件（`.workflow/state/experience/index.md`）是加载规则索引，指向 context/experience/ 的实际文件。

| 角色 | 加载分类 |
|------|---------|
| `requirement-review` | `context/experience/roles/requirement-review.md` |
| `planning` | `context/experience/roles/planning.md` |
| `executing` | `context/experience/roles/executing.md` + `context/experience/tool/harness.md` |
| `testing` / `acceptance` | `context/experience/roles/testing.md` + `context/experience/roles/acceptance.md` |
| `regression` | `context/experience/roles/regression.md` + `context/experience/risk/known-risks.md` |
| `done` | 按需加载同阶段相关经验 |
| `toolsManager` | `context/experience/tool/` 下相关工具经验 |

## 目录说明

经验内容的实际存储位置为 `.workflow/context/experience/`，包含以下分类：

| 目录 | 内容 |
|------|------|
| `context/experience/roles/` | 各角色（需求分析、架构师、开发者、测试、验收、回归）相关经验 |
| `context/experience/tool/` | 工具使用技巧、prompt 模式、工具选择经验 |
| `context/experience/risk/` | 风险识别、已知风险、失败恢复相关经验 |

## 经验沉淀规范

### 触发时机
- after-task hook 执行后
- 每个角色任务完成时
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

### 来源字段校验规则（req-30（slug 沟通可读性增强：全链路透出 title）/ chg-03 契约 7）

本规则**只作用于本次提交之后的新增 / 修改经验条目**；存量条目按需补，不做强制回溯（AC-08 策略）。

**规则**：新增经验文件的"来源"段必须写到 `{req-id}（{title}）` 及后续 `chg-XX` / `sug-XX` 粒度；单独裸 `req-XX` 视为违规。

**示范**：

- 正例：`req-29（批量建议合集 2 条）— sug-01（ff --auto）+ sug-08（archive 判据）合集`
- 反例：`req-29 chg-04`（裸 id，缺 title）

> 注：经验内容存储于 `.workflow/context/experience/`，本文件仅为加载规则索引。
