# Done Report: req-11-done阶段建议自动转suggest

## 基本信息
- **需求 ID**: req-11
- **需求标题**: done阶段建议自动转suggest
- **归档日期**: 2026-04-15

## 实现时长
- **总时长**: 0d 0h 0m
- **requirement_review**: 0h 0m
- **planning**: 0h 0m
- **executing**: 0h 0m
- **testing**: 0h 0m
- **acceptance**: 0h 0m
- **done**: 0h 0m

> 数据来源：`state/requirements/req-11-done阶段建议自动转suggest.yaml` 中的 `started_at`、`completed_at`、`stage_timestamps`

---

## 执行摘要

完成了 done 阶段建议自动转 suggest 的功能：
- `done.md` 和 `WORKFLOW.md` 已更新，明确主 agent 在 done 阶段需将改进建议写入 suggest 池
- `core.py` 中新增 `extract_suggestions_from_done_report`，自动解析 `done-report.md` 中的建议并调用 `create_suggestion`
- `workflow_next` 在 stage 推进到 done 时自动触发建议提取
- 端到端测试验证：4 条不同格式的建议被正确提取为 suggest 文件

**顺带修复的重要 bug**：
- `save_simple_yaml` / `load_simple_yaml` 不支持 `dict` 类型，导致 `stage_timestamps` 保存和读取异常
- `_migrate_state_files` 对旧版字符串 `stage_timestamps` 的处理缺陷

---

## 六层检查结果

### Context
- [x] 文档更新完整

### Tools
- [x] CLI 自动行为扩展正常

### Flow
- [x] ff 模式自动推进顺畅

### State
- [x] state yaml 的 dict 支持已修复

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

执行 `harness archive req-11-done阶段建议自动转suggest`。
