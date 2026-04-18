# chg-03-硬门禁集成

## 变更目标
在现有角色文件中植入硬门禁提示：每次需求或任务发生变更后，必须检查《Harness 审查检查清单》是否需要更新，确保清单与流程实践同步演进，防止再次出现因清单缺失导致的审查遗漏。

## 变更范围
- 修改 `.workflow/context/roles/done.md`
- 修改 `.workflow/context/roles/planning.md`
- 修改 `.workflow/context/roles/executing.md`
- 在以上角色的“完成前必须检查”或“退出条件”附近增加一条硬门禁：
  > “若本轮工作导致需求范围、阶段流程、产出标准或角色行为发生变化，必须检查 `.workflow/context/checklists/review-checklist.md` 是否需要同步更新。”
- 在 planning.md 中额外增加提示：拆分变更时若引入新制品或新阶段，应在 change.md 中明确是否需要更新审查检查清单。

## 验收条件
- [ ] `done.md` 的“完成前必须检查”或等效位置包含上述硬门禁提示
- [ ] `planning.md` 的“完成前必须检查”或等效位置包含上述硬门禁提示
- [ ] `executing.md` 的“完成前必须检查”或等效位置包含上述硬门禁提示
- [ ] 所有提示均使用一致的措辞，并明确引用 `.workflow/context/checklists/review-checklist.md` 路径
- [ ] 未修改任何代码文件，未创建 change.md / plan.md 以外的文件
