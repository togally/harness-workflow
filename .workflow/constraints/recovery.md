# 失败恢复规则

## 失败三条路径

### 路径一：重试（同路径，修正错误）
**适用：** 方案可行，执行出错（命令参数错误、文件路径写错等）
```
1. 记录错误到 session-memory（失败路径记录）
2. 找出具体错误原因
3. 修正后重新执行该步骤
4. 不超过 3 次重试，超过则切路径
```

### 路径二：切路径（换方案）
**适用：** 当前方案不可行，需要换一种实现方式
```
1. 记录放弃原因到 session-memory
2. 回到 planning 讨论替代方案
3. 更新 plan.md，再进入执行
```

### 路径三：回滚（恢复稳定状态）
**适用：** 文件/状态已损坏，无法通过重试或切路径修复
```
1. 停止所有操作
2. 记录损坏范围到 session-memory
3. 通过 git 恢复到最近稳定状态（git stash / git checkout）
4. 在 session-memory 标记："已回滚，原因：{xxx}"
5. 触发 harness regression 评估是否需要转为新变更
```

---

## 上下文爆满 / 任务切换处理

**适用：** context 接近上限、需要切换到其他需求、会话被中断

```
Step 1  识别需要交接的时机
        - context 接近上限（对话轮次多、文件读取多）
        - 用户运行 harness use 切换需求
        - 任何原因导致的会话中断

Step 2  写 handoff.md
        路径：state/sessions/{req-id}/[chg-id/]handoff.md
        内容：
          ## 触发原因
          ## 当前状态（需求、阶段、当前变更）
          ## 已完成的步骤（✅ 列表）
          ## 正在进行（中断点，▶ 标记的步骤）
          ## 下一步
          ## 已知约束与失败路径
          ## 接管注意事项

Step 3  新 agent 启动
        → session-start hook 检测到 handoff.md
        → 读取 handoff.md 内容接管工作
        → 从中断点继续，不重复已完成步骤

Step 4  完成后清理
        → 工作完成后删除 handoff.md
        → session-memory 保留（历史记录）
```

---

## 恢复检测逻辑（session-start hook 执行）

```
读 session-memory.md
    ├── 发现 handoff.md 存在 → 优先读 handoff.md，按交接内容接管
    ├── 发现 ▶ 未完成标记（无 handoff.md）→ 从该步骤重新执行
    └── 全部 ✅ → 正常继续下一步
```
