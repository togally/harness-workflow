# Change: chg-05 灵活问题捕获机制

## 关联需求
req-01 — 版本重做，AC-7

## 问题描述
当前工作流仅支持通过 `harness regression` 命令主动触发问题记录。
用户口头提出的问题、AI 在执行中自行发现的问题，以及非 acceptance 阶段出现的问题，均无法被系统性捕获。

## 设计方向（已确认）

**职责边界驱动，而非命令驱动：**
- 各角色遇到职责外问题时，不自行处理，标记并上报给主 agent
- 主 agent 负责决策：轻量记录 / 询问用户是否升级为正式 regression
- 问题捕获不依赖用户手动输入命令

**积压+批量决策模式：**
- 捕获到的问题先记录到 session-memory `## 待处理捕获问题` 区块
- 在合适时机（阶段完成、用户操作间隙）询问用户对每条问题的处置意向
- 用户可选择：升级为正式 regression / 忽略 / 下次再说

## 变更范围

**新增/修改：**
- `.workflow/constraints/boundaries.md`
  - 增加"职责外问题识别与上报"规则（所有角色共享）
  - 定义触发条件：AI 主动识别 + 用户口头提出两种来源
  - 定义上报格式和处置流程
- `.workflow/context/roles/*.md`（全部角色文件）
  - 增加对 `constraints/boundaries.md` 职责外问题规则的引用
- `WORKFLOW.md`
  - 主 agent 增加"接收上报问题并决策"规则
  - 定义询问用户时机和选项格式
- session-memory 模板（`.workflow/state/sessions/*/session-memory.md` 格式规范）
  - 增加 `## 待处理捕获问题` 区块规范

## 验收条件
- [ ] `constraints/boundaries.md` 有完整的职责外问题识别与上报规则
- [ ] 各角色文件有对该规则的引用（不重复写，只引用）
- [ ] `WORKFLOW.md` 主 agent 有接收上报和询问用户的处理规则
- [ ] session-memory 格式包含 `## 待处理捕获问题` 区块
- [ ] 行为验证：在非 acceptance 阶段，AI 遇到职责外问题时，会记录到 session-memory 并在合适时机询问用户，而非忽略或擅自处理
