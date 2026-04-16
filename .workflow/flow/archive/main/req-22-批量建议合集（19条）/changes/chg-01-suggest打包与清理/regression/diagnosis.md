# Regression Diagnosis: suggest --apply-all 错误拆分为 19 个独立需求

## 触发来源
用户执行 `harness suggest --apply-all` 后，发现系统创建了 19 个独立需求（req-22 ~ req-40），并质问："你不能合并成一个需求吗？我应该有这样的门禁吧"

## 问题描述
1. **req-31 原始 suggest 明确要求**："建议转化成需求要打包不要分开，打包成需求之后原有建议要清除"
2. **req-21 刚建立的硬门禁**（planning.md）："若本次 planning 拆分出的变更涉及新制品、新阶段或新角色，必须检查 `.workflow/context/checklists/review-checklist.md` 是否需要同步更新，并在相关 change.md 中记录。"
3. 但实际执行时，agent 使用自定义 Python 脚本将 19 条 suggest 逐一转换成了 19 个独立需求，严重违反了"打包不要分开"的原则。

## 根因分析
1. **未使用 harness CLI 的打包能力**：`harness suggest --apply-all` 本身就支持 `--pack-title` 参数，可以将所有 pending suggest 打包成一个需求。但 agent 未使用该参数，反而手写了一个遍历脚本逐个创建需求。
2. **忽略了 req-31 的原始意图**：req-31 明确说"打包不要分开"，agent 在批量转换前没有检查已有 suggest 中是否有相关约束性要求。
3. **硬门禁未被触发**：虽然 req-21 在 planning.md / done.md / executing.md 中追加了清单更新检查，但没有在"suggest 转需求"这个特定场景下设置硬门禁提示，agent 未意识到自己在做一个 planning/拆分动作。

## 实地检查结果
- 错误创建了 req-22 ~ req-40 共 19 个需求
- 每个需求的状态文件和需求目录均已生成
- suggest 池已被清空（`rm .workflow/flow/suggestions/*.md`）

## 问题分类
**流程违规 / 标准遗漏** — agent 未遵循已有的"打包不要分开"要求，错误拆分了 suggest。

## 路由决定
路由到 executing 阶段，任务：
1. 删除错误创建的 req-22 ~ req-40 的状态文件和需求目录
2. 重新创建一个打包需求（req-22），将 19 条 suggest 的内容聚合到单一 requirement.md 中
3. 更新 `runtime.yaml` 指向 req-22

## 修复记录（2026-04-15）
1. 已删除错误的 req-22 ~ req-40 状态文件和需求目录
2. 已创建聚合需求 `req-22-批量建议合集（19条）`，并将 19 条 suggest 的标题和目标写入 requirement.md
3. `runtime.yaml` 已重置为 open 状态，等待进入 req-22 的工作流

**修复完成。**
