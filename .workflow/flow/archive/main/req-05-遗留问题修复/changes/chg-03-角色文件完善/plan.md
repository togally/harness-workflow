# Plan: testing/acceptance 角色文件完善

## 执行步骤

### Step 1: 审查 testing.md

文件：`.workflow/context/roles/testing.md`

检查是否包含：
- 明确的 "自验证 checklist" 节——要求 executing agent 逐项检查所有 AC
- 退出条件：所有 AC 检查通过
- 流转规则：通过 → `harness next` → acceptance

如缺失，补充上述内容。

### Step 2: 审查 acceptance.md

文件：`.workflow/context/roles/acceptance.md`

检查是否包含：
- requirement.md 对齐检查 checklist（背景/目标/范围/AC 是否与实际交付一致）
- change.md 对齐检查（每个变更的 AC 是否满足）
- 退出条件：对齐检查通过 + 用户最终确认
- 流转规则：通过 → `harness next` → done；不通过 → regression

如缺失，补充上述内容。

### Step 3: 确认 context/index.md 路由

文件：`.workflow/context/index.md`

确认 Step 2 路由表中 testing 和 acceptance 已有对应条目，且 Step 3 经验加载也包含 testing/acceptance 阶段的分类。

## 产物

- `.workflow/context/roles/testing.md`（可能修改）
- `.workflow/context/roles/acceptance.md`（可能修改）
- `.workflow/context/index.md`（确认或修改）

## 风险评估

低风险：仅修改 .workflow/ 内的文档文件，可 git 回滚
