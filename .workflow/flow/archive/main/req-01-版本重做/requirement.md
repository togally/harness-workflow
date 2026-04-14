# Requirement

## 1. Title

版本重做

## 2. Background

harness workflow 系统自 v0.2.0-refactor 存在以下问题：
- 上下文加载链路断裂，新会话无法从 runtime.yaml 正确恢复状态
- 状态管理混乱，runtime.yaml 缺少 stage 字段，角色路由无法正常工作
- 新旧文件结构并存，`.claude/skills/harness/` 旧版文件与新版命令系统冲突
- 需求文档目录（`flow/requirements/`）缺失，经验沉淀体系不完整

需要整体重构，迁移到基于需求管理的新架构。

## 3. Goal

1. 建立基于需求管理的新系统架构（取代版本管理）
2. 清理旧版 harness skill 文件，部署新版命令系统
3. 统一状态管理路径（`.workflow/state/`）
4. 建立完整的角色-阶段-约束-经验四层体系

## 4. Scope

**包含：**
- `.claude/skills/harness/` 目录下所有旧版文件的清理
- `.workflow/` 目录下所有文件的结构整理和补全
- `.workflow/state/runtime.yaml` 字段规范化（含 stage 字段）
- `.workflow/flow/requirements/` 目录及需求文档创建
- `.workflow/state/experience/` 经验沉淀体系建立
- 三端支持（codex/qoder/cc）：install 交互配置功能

**不包含：**
- 项目业务逻辑代码变更
- 非 workflow 系统的其他目录

## 5. Acceptance Criteria

1. 旧版 harness skill 文件物理清理完成，工作目录无残留（`.claude/skills/harness/` 中无旧版文件）
2. 经验沉淀体系可用：`.workflow/state/experience/` 各分类目录有内容可写，加载路径唯一无冲突
3. 正向研发流程可运行：`.workflow/context/index.md` 有完整加载规则，`runtime.yaml` 含 stage 字段，req-01 需求文档存在
4. 中断恢复可用：新会话可从 `runtime.yaml` 恢复当前 stage，req-01 状态文件和需求文档完整
5. **三端支持可用**：install 命令提供交互界面，用户可勾选支持的平台（codex/qoder/cc），按选择生成/备份对应配置
   - codex 配置：`AGENTS.md`
   - qoder 配置：`.qoder/agents.md`
   - cc 配置：`.claude/commands/` 目录
   - 备份策略：不支持的配置移动到 `.workflow/context/backup/` 保留
   - 恢复策略：用户重新勾选已移除的平台时，从备份中恢复配置（而非重新生成）
   - 同步策略：`harness update` 执行时，同步更新备份中的配置文件

6. **Slash command 文件修复**：全平台 slash command 文件与 CLI 实现一致，无幽灵命令，无缺失命令，broken-state 提示使用新版措辞
   - 删除 `.claude/commands/harness-exec.md`（CLI 无此命令）
   - 在 `.claude/commands/` 和 `.codex/skills/` 补充 `harness-plan` 文件
   - 三端（qoder/cc/codex）均补充 `harness-feedback` slash command 文件
   - 全部 slash command 文件的 broken-state 提示从 `harness active "<version>"` 更新为新版措辞

7. **灵活问题捕获机制**：任意阶段任意来源的问题（AI 主动识别或用户口头提出）均可被捕获和追踪，不依赖用户手动触发 `harness regression`
   - `.workflow/constraints/boundaries.md` 增加"职责外问题识别与上报"规则（各角色共享）
   - 各角色文件（`roles/*.md`）引用该规则，不自行处理职责外问题，交由主 agent 决策
   - `WORKFLOW.md` 主 agent 增加"接收上报并决策"规则：记录到 session-memory，并在合适时机询问用户是否升级为正式 regression
   - session-memory 增加 `## 待处理捕获问题` 区块格式，记录来源阶段、问题描述、处置状态（pending / 已升级 / 已忽略）

8. **workflow 目录重命名为 `.workflow/`**：整个工作流目录遵循 dotfile 约定，对用户工作区更干净
   - 物理目录：`.workflow/` → `.workflow/`（含所有子目录和文件）
   - Python 源码：`core.py`、`backup.py` 所有 `Path("workflow")` 常量更新
   - Scaffold：`scaffold_v2/.workflow/` → `scaffold_v2/.workflow/`
   - 模板文件：`assets/templates/` 中 17 个含 `.workflow/` 引用的文件全量更新
   - Slash command 文件：三端所有 Hard Gate 路径引用更新（~56 个文件）
   - 根目录文档：`WORKFLOW.md`、`AGENTS.md`、`CLAUDE.md` 路径引用更新
   - 向后兼容：`harness update` 自动检测并迁移已有仓库的 `.workflow/` → `.workflow/`
   - git 可见性：`harness install` 写入 `.gitignore` 规则，确保 `.workflow/` **不被**忽略（显式 `!.workflow/`）

## 6. Split Rules

- 每个验收标准对应一个独立可交付变更
- 变更完成后填写 `completion.md` 并记录验证结果
