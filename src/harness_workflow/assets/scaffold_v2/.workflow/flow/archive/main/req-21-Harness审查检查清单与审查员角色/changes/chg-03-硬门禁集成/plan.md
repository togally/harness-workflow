# chg-03-硬门禁集成 执行计划

## 执行步骤

1. **确认前置产物已就绪**
   - 确认 `chg-01` 产出的 `.workflow/context/checklists/review-checklist.md` 已存在
   - 确认 `chg-02` 产出的 `.workflow/context/roles/reviewer.md` 已存在
   - 记录两个文件的绝对路径，用于在角色文件中引用

2. **定位插入点**
   - 读取 `.workflow/context/roles/done.md`，找到“完成前必须检查”区块
   - 读取 `.workflow/context/roles/planning.md`，找到“完成前必须检查”区块
   - 读取 `.workflow/context/roles/executing.md`，找到“完成前必须检查”区块

3. **植入硬门禁提示**
   - 在 `done.md` 的“完成前必须检查”列表末尾追加检查项：
     > 若本轮 done 阶段的回顾发现新的产出标准、阶段变更或角色行为调整，必须检查 `.workflow/context/checklists/review-checklist.md` 是否需要同步更新。
   - 在 `planning.md` 的“完成前必须检查”列表末尾追加检查项：
     > 若本次 planning 拆分出的变更涉及新制品、新阶段或新角色，必须检查 `.workflow/context/checklists/review-checklist.md` 是否需要同步更新，并在相关 change.md 中记录。
   - 在 `executing.md` 的“完成前必须检查”列表末尾追加检查项：
     > 若执行过程中发现现有审查检查清单无法覆盖的新风险或新产出要求，必须检查 `.workflow/context/checklists/review-checklist.md` 是否需要同步更新。

4. **内部验证**
   - 重新读取三个角色文件，确认硬门禁提示已正确插入
   - 对照 change.md 验收条件逐条核对
   - 确认措辞一致、路径引用正确、格式无破坏

## 产物清单
- 修改后的 `.workflow/context/roles/done.md`
- 修改后的 `.workflow/context/roles/planning.md`
- 修改后的 `.workflow/context/roles/executing.md`

## 依赖关系
- 依赖 chg-01（需要 review-checklist.md 的路径确定）
- 依赖 chg-02（需要 reviewer.md 的存在以在后续执行中由审查员角色使用清单）

## 执行顺序
第 2 顺位（必须在 chg-01 和 chg-02 完成后执行）
