# Plan: chg-01

## Steps

1. 评估现有状态文件结构（`state/requirements/*.yaml`、`runtime.yaml`）
2. 对比三种采集方案：
   - 方案 A：在 `state/requirements/{id}.yaml` 中增加 `started_at` 和 `stage_timestamps` 字段
   - 方案 B：在 `runtime.yaml` 中记录当前需求的 `started_at` 和 `completed_at`
   - 方案 C：从 `session-memory.md` 或 `git log` 中间接推算
3. 评估各方案的优缺点：
   - 方案 A：需求级别持久化，支持分阶段时长，归档后仍可查
   - 方案 B：全局状态文件，简单但需求切换时可能覆盖
   - 方案 C：不可靠，session-memory 可能缺失，git log 粒度粗
4. **选定主方案**：方案 A（`state/requirements/{id}.yaml` 作为需求元数据中心），辅以 `runtime.yaml` 的当前需求快速访问
5. 设计字段：
   - `started_at`: ISO 8601 格式，记录 requirement_review 阶段开始时间
   - `completed_at`: ISO 8601 格式，记录 done 阶段完成时间
   - `stage_timestamps`: 对象，键为 stage 名，值为进入该阶段的时间戳
6. 定义降级策略：
   - 如果 `started_at` 缺失，尝试从 `created_at` 降级
   - 如果 `completed_at` 缺失，使用报告生成时的当前时间
   - 如果分阶段时间缺失，总时长仍可用，分阶段显示 "N/A"
7. 更新 `state/requirements/{id}.yaml` 的示例说明（在哪个文档中补充说明，如 `stages.md` 或单独的 state 规范文档）
8. 检查与现有 `state/` 结构的兼容性

## Artifacts

- `stages.md` 或 `state/` 相关文档中的时长定义和采集方案说明
- 更新的 `state/requirements/{id}.yaml` 字段规范（文档层面）

## Dependencies

- 无
