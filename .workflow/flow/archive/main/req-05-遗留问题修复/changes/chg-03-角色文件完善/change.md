# Change: testing/acceptance 角色文件完善

## 目标

确认并完善 `context/roles/testing.md` 和 `context/roles/acceptance.md` 的内容，使其包含明确的结构化自验证 checklist：
- testing.md：每条 AC 逐项检查的 checklist
- acceptance.md：requirement.md 对齐检查的 checklist

同时确认 `context/index.md` 路由表已包含 testing/acceptance 阶段的加载规则。

## 范围

- 审查并完善 `.workflow/context/roles/testing.md`
- 审查并完善 `.workflow/context/roles/acceptance.md`
- 确认 `.workflow/context/index.md` 路由正确

## 验收标准

- [ ] `context/roles/testing.md` 包含明确的自验证 checklist（每条 AC 逐项检查）
- [ ] `context/roles/acceptance.md` 包含 requirement.md 对齐检查 checklist
- [ ] `context/index.md` 中 testing/acceptance 阶段的路由和加载规则完整

## 依赖

chg-02（testing/acceptance 阶段在 WORKFLOW_SEQUENCE 中定义后，角色文件才有实际使用场景）
