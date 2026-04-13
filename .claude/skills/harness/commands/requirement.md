# harness requirement "<title>"

## 前置条件
- 无（任何时候均可创建新需求）

## 执行步骤
1. 生成需求 ID：`req-{两位数字}-{title}`（按现有需求数量递增）
2. 创建目录：`workflow/flow/requirements/req-{id}-{title}/`
3. 创建目录：`workflow/flow/requirements/req-{id}-{title}/changes/`
4. 创建文件：`requirement.md`（使用模板，填入 title）
5. 创建状态文件：`workflow/state/requirements/req-{id}.yaml`
6. 更新 `workflow/state/runtime.yaml`：
   - `current_requirement: req-{id}`
   - `active_requirements` 中添加 req-{id}
7. 进入 `conversation_mode: harness`，锁定到 requirement_review

## requirement.md 初始模板
```markdown
# 需求：{title}

**ID:** req-{id}
**状态:** draft
**创建时间:** {date}

## 背景
## 目标
## 范围
### 包含
### 不包含
## 验收标准
## 风险与约束
## 讨论记录
```

## state/requirements/req-{id}.yaml 初始结构
```yaml
id: req-{id}
title: {title}
stage: requirement_review
current_change: ""
pending_tasks: []
completed_tasks: []
change_ids: []
regression_ids: []
created_at: {date}
updated_at: {date}
```

## 完成后输出
告知用户：需求已创建，当前阶段 requirement_review，角色：需求分析师。
引导讨论：背景是什么？目标是什么？
