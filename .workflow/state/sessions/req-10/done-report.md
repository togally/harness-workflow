# Done Report: req-10-suggest功能

## 基本信息
- **需求 ID**: req-10
- **需求标题**: suggest功能
- **归档日期**: 2026-04-15

## 实现时长
- **总时长**: 0d 0h 0m
- **requirement_review**: 0h 0m
- **planning**: 0h 0m
- **executing**: 0h 0m
- **testing**: 0h 0m
- **acceptance**: 0h 0m
- **done**: 0h 0m

> 数据来源：`state/requirements/req-10-suggest功能.yaml` 中的 `started_at`、`completed_at`、`stage_timestamps`

---

## 执行摘要

完成了 `harness suggest` 轻量级建议池功能：
- `harness suggest "<content>"` — 随手记录想法
- `harness suggest --list` — 查看建议池
- `harness suggest --apply <id>` — 一键转化为正式需求并进入 requirement_review
- `harness suggest --delete <id>` — 删除建议

存储路径为 `.workflow/flow/suggestions/sug-NN-{slug}.md`，格式为 frontmatter + Markdown body，无需数据库。

同时顺带修复了 `create_requirement` 中 state yaml 的旧字段问题，以及 `core.py` 中所有 `req_id` 读取的兼容性。

---

## 六层检查结果

### Context
- [x] 经验无需新增（属于自然功能扩展）

### Tools
- [x] CLI 命令扩展正常

### Flow
- [x] ff 模式自动推进顺畅

### State
- [x] 状态记录完整

### Evaluation
- [x] 无降低标准

### Constraints
- [x] 无边界约束触发

---

## 流程完整性评估

| 阶段 | 状态 |
|------|------|
| requirement_review | ✅ |
| planning | ✅ |
| executing | ✅ |
| testing | ✅ |
| acceptance | ✅ |
| done | ✅ |

---

## 下一步行动

执行 `harness archive req-10-suggest功能`。
