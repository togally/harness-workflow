# Plan: 批量更新所有 stage 角色文件

## 步骤

1. 读取更新后的 `stage-role.md`，确认通用 SOP 模板和继承执行清单
2. 逐一读取 7 个 stage 角色文件：executing, testing, planning, acceptance, regression, requirement-review, done
3. 为每个角色文件重构 SOP：
   - 在原有 Step 1 之前插入"Step 0：初始化（自我介绍 + 前置加载确认）"
   - 在执行业务步骤中嵌入"工具优先查询"和"操作日志"要求
   - 在 SOP 中明确增加"60% 上下文评估"的检查点
   - 在退出条件前增加"经验沉淀检查"步骤
4. 更新每个角色的"上下文维护职责"，增加 60% 阈值监控
5. 保持各角色原有业务语义不变
6. 全部修改完成后做一致性核对
