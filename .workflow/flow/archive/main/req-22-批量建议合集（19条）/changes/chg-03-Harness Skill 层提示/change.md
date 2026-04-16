# chg-03-Harness Skill 层提示

## 目标
在 Harness Skill 文档中增加关于 `harness suggest --apply-all` 强制打包的显式提示，确保 agent 在执行批量 suggest 转换前能够识别并遵守打包约束。

## 范围
- 修改 `.claude/skills/harness/SKILL.md`
- 仅涉及 `harness-suggest` 相关章节的补充说明

## 变更内容
1. 在 `SKILL.md` 的 `harness suggest` 说明区域（或 Command Model 的对应位置）增加提示：
   - 执行 `harness suggest --apply-all` 前，必须检查 suggest 池中是否有"打包不要分开"类的约束
   - 优先使用 `--pack-title` 参数将所有 pending suggest 打包为单一需求
   - 禁止手写脚本逐条将 suggest 转换为独立需求
2. 保持 SKILL.md 的整体结构和语气一致，不破坏现有命令模型描述

## 验收标准
- [ ] `.claude/skills/harness/SKILL.md` 中已增加 suggest 打包提示
- [ ] 提示内容明确包含"优先使用 `--pack-title`"和"禁止逐条拆分"
- [ ] 未引入与其他命令描述冲突的语义

## 依赖
- chg-01：建议先完成 CLI 层修复，确保 Skill 提示与最终 CLI 行为一致
- chg-02：建议先完成约束文档，确保 Skill 提示引用的约束已存在

## 阻塞
无。
