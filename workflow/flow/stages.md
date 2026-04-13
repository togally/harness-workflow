# Stage 定义与流转规则

## 完整流转图

```
requirement_review          ← 第三层管辖
      ↓ harness next
   planning                 ← 第三层管辖
      ↓ harness next
   executing                ← 第三层管辖
      ↓ harness next
   testing                  ← 第五层管辖（evaluation/testing.md）
      ↓ harness next
  acceptance                ← 第五层管辖（evaluation/acceptance.md）
      ↓ harness next
    done

任意阶段 ──harness regression──→ regression ← 第五层管辖
                                      ↓
                         ┌────────────┴────────────┐
                   需求/设计问题              实现/测试问题
                         ↓                          ↓
               requirement_review               testing
```

---

## 第三层 Stage 定义

### requirement_review
- **角色**：需求分析师（`context/roles/requirement-review.md`）
- **进入条件**：`harness requirement "<title>"` 创建需求
- **退出条件**：requirement.md 包含背景、目标、范围、验收标准，用户确认
- **必须产出**：`flow/requirements/{req-id}/requirement.md`
- **下一步**：`harness next` → `planning`

### planning
- **角色**：架构师（`context/roles/planning.md`）
- **进入条件**：requirement_review 退出条件满足
- **退出条件**：所有变更有 change.md + plan.md，执行顺序明确，用户确认
- **必须产出**：每个变更的 `change.md` + `plan.md`
- **下一步**：`harness next` → `executing`

### executing
- **角色**：开发者（`context/roles/executing.md`）
- **进入条件**：planning 退出条件满足
- **退出条件**：所有变更实现完成，内部测试通过，session-memory 全部 ✅
- **必须产出**：代码/文件变更 + session-memory 执行日志
- **下一步**：`harness next` → `testing`（进入第五层）

### done
- **进入条件**：acceptance 通过（第五层判定）
- **动作**：触发经验沉淀最终检查；需求可归档
- **归档命令**：`harness archive "<req-id>" [--version "<v>"]`

---

## 需求目录规范

```
flow/requirements/
└── req-{两位数字}-{title}/
    ├── requirement.md
    └── changes/
        └── chg-{两位数字}-{title}/
            ├── change.md
            ├── plan.md
            └── regression/
                ├── diagnosis.md
                └── required-inputs.md
```

## 归档目录规范

```
flow/archive/
└── {version}/             # 可选，归档时指定，可复用
    └── req-{id}-{title}/  # 结构与活跃需求一致
```

归档规则：
- 只有 `done` 状态的需求可以归档
- 从 `flow/requirements/` 移动到 `flow/archive/{version}/`
- `state/requirements/{req-id}.yaml` 标记为 `archived`
- `state/sessions/{req-id}/` 保留不删（历史可查）

---

## 命令与 Stage 对应关系

| 命令 | 作用 | 适用 Stage |
|------|------|-----------|
| `harness requirement` | 创建需求，进入 requirement_review | 任意 |
| `harness change` | 创建变更文档 | planning |
| `harness plan` | 创建变更计划 | planning |
| `harness next` | 推进到下一 stage | 任意（满足退出条件） |
| `harness ff` | 跳过讨论门，直达执行确认 | requirement_review / planning |
| `harness archive` | 归档已完成需求 | done |
| `harness regression` | 进入 regression | 任意 |
