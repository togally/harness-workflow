# chg-02-审查员角色定义

## 变更目标
定义“审查员”角色的完整行为约束，使其在 requirement_review、planning、testing、acceptance、done 等阶段有明确的职责边界、可用动作和退出标准，避免审查工作无人负责或标准不一。

## 变更范围
- 新建 `.workflow/context/roles/reviewer.md`
- 定义审查员的角色定位（独立于执行者、测试者的第三方视角）
- 明确审查员在各阶段的任务、允许行为、禁止行为
- 明确审查员必须使用的检查清单来源（引用 chg-01 产出的 review-checklist.md）
- 定义审查员的退出条件（通过 / 驳回 / 要求补充）

## 验收条件
- [ ] `.workflow/context/roles/reviewer.md` 文件存在且可被读取
- [ ] 文件包含“角色定义”“本阶段任务”“允许行为”“禁止行为”“退出条件”五个必备章节
- [ ] 明确引用 `.workflow/context/checklists/review-checklist.md` 作为审查依据
- [ ] 定义审查结论的三种状态：通过（pass）、驳回（reject）、要求补充（needs_rework）
- [ ] 说明审查员与 planning、executing、testing 角色的协作边界，避免职责重叠
