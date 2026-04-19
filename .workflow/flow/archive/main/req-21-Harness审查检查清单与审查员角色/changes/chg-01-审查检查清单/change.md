# chg-01-审查检查清单

## 变更目标
建立一份标准化的《Harness 审查检查清单》，作为各阶段（尤其是 requirement_review、planning、testing、acceptance、done）审查工作的统一产出标准依据，防止因缺少统一清单而导致关键制品（如 artifacts/requirements/）被遗漏。

## 变更范围
- 新建 `.workflow/context/checklists/review-checklist.md`
- 清单内容需覆盖 Harness 六层架构（Context、Tools、Flow、State、Evaluation、Constraints）的关键审查项
- 明确各阶段必须检查的制品、角色行为、状态一致性项
- 清单应具备可扩展性，后续新增阶段或制品时可按结构追加

## 验收条件
- [ ] `.workflow/context/checklists/review-checklist.md` 文件存在且可被读取
- [ ] 清单包含六层检查框架，每层至少列出 3 项核心检查点
- [ ] 明确列出 requirement_review、planning、executing、testing、acceptance、done 各阶段的关键审查项
- [ ] 包含“制品完整性检查”专节，覆盖 artifacts/requirements/、changes/、session-memory 等关键产出位置
- [ ] 文件格式统一使用 Markdown，检查项使用 `- [ ]` 可勾选格式
