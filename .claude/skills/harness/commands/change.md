# harness change "<title>"

## 前置条件
- 当前 stage 是 `planning`

## 执行步骤
1. 生成变更 ID：`chg-{两位数字}-{title}`
2. 创建目录：`workflow/flow/requirements/{req-id}/changes/chg-{id}-{title}/`
3. 创建目录：`workflow/flow/requirements/{req-id}/changes/chg-{id}-{title}/regression/`
4. 创建文件：`change.md`（模板）
5. 更新 `state/requirements/{req-id}.yaml` 的 `change_ids` 列表

## change.md 初始模板
```markdown
# 变更：{title}

**ID:** chg-{id}
**需求:** {req-id}
**状态:** draft

## 目标
## 变更内容
## 吸收参考
## 验收
## 依赖
```
