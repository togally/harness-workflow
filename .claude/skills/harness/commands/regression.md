# harness regression

## 子命令

### harness regression "<issue>"
触发 regression 诊断流程

**前置条件：** 有 current_requirement

**执行步骤：**
1. 记录触发前的 stage 到 `state/requirements/{req-id}.yaml`（regression_from 字段）
2. 更新 stage 为 `regression`
3. 创建 `workflow/flow/requirements/{req-id}/changes/{chg-id}/regression/diagnosis.md`（模板）
4. 创建 `required-inputs.md`（模板，如需人工输入）
5. 加载 regression 角色文件和 evaluation/regression.md
6. 引导诊断师开始分析

---

### harness regression --confirm
确认是真实问题，执行路由

**前置条件：** 当前 stage 是 regression，diagnosis.md 已完成

**执行步骤：**
1. 读 diagnosis.md 的路由决定
2. 更新 stage：
   - 需求/设计问题 → `requirement_review`
   - 实现/测试问题 → `testing`
3. 将 regression 记录写入 `state/requirements/{req-id}.yaml` 的 regression_ids
4. 加载新 stage 的角色文件

---

### harness regression --reject
否认问题，回到触发前 stage

**执行步骤：**
1. 读 regression_from 字段
2. 恢复 stage 为 regression_from 的值
3. 在 session-memory 记录：误判，原因：{xxx}

---

### harness regression --cancel
取消 regression，回到触发前 stage（不记录为误判）

**执行步骤：**
1. 读 regression_from 字段
2. 恢复 stage
3. 在 session-memory 记录：regression 已取消
