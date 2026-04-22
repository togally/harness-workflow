# 功能扩展

> req-id: req-05 | 完成时间: 2026-04-14 | 分支: main

## 需求目标

在现有 harness-workflow 基础上扩展四项功能：

1. **kimicli 平台支持**：将 kimicli 作为第 4 个受支持平台，`harness install` 生成 `.kimi/skills/*/SKILL.md`
2. **归档默认 folder = 当前 git 分支名**：`harness archive` 时默认将需求归入与当前 git 分支同名的文件夹下
3. **交互式需求列表选择**：`harness archive`、`harness enter` 无论是否传入 req-id，均弹出列表供确认后执行
4. **归档完整迁移 + 制品仓库**：归档时将需求所有关联文档打包至归档目录内分类存放；同时在根目录 `artifacts/` 制品仓库的 `requirements/` 分类下生成可供新成员快速接手的需求摘要文档

## 交付范围

**包含**：

### 功能一：kimicli 平台
- 新增 `render_kimi_command_skill()` 函数，生成 `.kimi/skills/{command}/SKILL.md`（YAML frontmatter + Markdown 格式）
- `_managed_file_contents()` 中为所有 `COMMAND_DEFINITIONS` 生成 kimi skills
- 平台代号 `kimi` 纳入 install 选择列表（默认全选）
- `get_active_platforms` / `get_platform_file_patterns` 识别 `.kimi/skills/` 目录
- `sync_platforms_state` 支持 kimi 平台 backup/restore
- 命令 Hard Gate 说明增加 `.kimi/skills/harness/SKILL.md` 检查路径
- README.md / README.zh.md 支持平台列表增加 kimicli

### 功能二：归档默认 folder = git branch
- `harness archive` 不传 `--folder` 时，自动读取当前 git branch 名作为默认 folder
- 非 git 仓库（或 branch 读取失败）时降级为原有行为（直接放 `archive/` 下，不嵌套 folder）
- branch 名中的 `/` 替换为 `-`（如 `feature/auth` → `feature-auth`）

### 功能三：交互式选择（含确认）
- `harness archive`（无论是否传 req-id）：始终弹出 done 需求列表，显示序号 + req-id + 标题 + 阶段，用户选择后确认再执行
- `harness enter`（无 req-id）：弹出 active 需求列表供选择
- `harness enter`（已传 req-id）：直接执行，不弹列表（明确指定则跳过选择）
- 列表格式：`[1] req-05 功能扩展（done）`
- 无可选项时给出明确提示，不弹空列表

### 功能四：归档完整迁移 + 制品仓库

**完整迁移**（归档目录内分类存放）：

归档后目录结构：
```
.workflow/flow/archive/{folder}/req-xx-{title}/
  ├── requirement.md          ← 原 flow/requirements/req-xx/requirement.md
  ├── changes/                ← 原 flow/requirements/req-xx/changes/
  ├── sessions/               ← 原 state/sessions/req-xx/（迁移）
  │   ├── chg-01/
  │   ├── done-report.md
  │   └── testing-report.md
  └── state.yaml              ← 原 state/requirements/req-xx-{title}.yaml（迁移）
```

- `state/sessions/req-xx/` 迁移至归档目录 `sessions/` 子目录
- `state/requirements/req-xx-{title}.yaml` 迁移至归档目录 `state.yaml`
- 归档后 `state/sessions/` 和 `state/requirements/` 下不再保留对应文件

**制品仓库**：

- 根目录新建 `artifacts/` 目录（如已存在则复用）
- 归档时在 `artifacts/requirements/` 下生成 `{req-id}-{title}.md`
- 文档内容目标：**让未参与过该需求的开发者能快速了解业务背景、目标、实现决策，并接手后续开发**
- 文档结构：
  ```markdown
  # {标题}

  > req-id: {req-id} | 完成时间: {date} | 分支: {git-branch}

  ## 业务背景
  （来自 requirement.md 的背景/Goal 章节）

  ## 需求目标
  （来自 requirement.md 的 Goal 章节）

  ## 交付范围
  （来自 requirement.md 的 Scope 章节）

  ## 验收标准
  （来自 requirement.md 的 Acceptance Criteria 章节）

  ## 变更列表
  （各 chg-xx 标题 + 一句话说明，来自 changes/ 下的 change.md）

  ## 关键设计决策
  （来自各 chg-xx/session-memory.md 中的关键决策记录，
   如有 design.md 则摘要其核心设计）

  ## 遗留问题与注意事项
  （来自 done-report.md 的改进建议 + 待办，如无则省略）
  ```
- `artifacts/` 目录结构按文档类型分类，`requirements/` 由 harness 自动维护，其余用户自行管理：
  ```
  artifacts/
    requirements/   ← harness archive 自动生成
    sql/            ← 用户手动放置
    api/            ← 用户手动放置
    ...
  ```

**不包含**：
- 修改 AGENTS.md 内容（kimicli 已原生支持）
- 新增 KIMI.md（kimicli 不使用此模式）
- 修改 codex / qoder / cc 现有平台逻辑
- kimicli Flow Skills（`type: flow`）支持
- `artifacts/` 下 requirements 以外子目录的初始化
- harness status / regression / requirement 等其他命令的交互式选择

## 验收标准

**kimicli**：
- [ ] `harness install` 新仓库默认启用 4 个平台（codex / qoder / cc / kimi）
- [ ] `.kimi/skills/` 目录存在，含所有 harness 命令的 SKILL.md（含合法 YAML frontmatter）
- [ ] `harness update` 能正确刷新 `.kimi/skills/` 文件
- [ ] 命令 Hard Gate 包含 `.kimi/skills/harness/SKILL.md` 检查路径

**归档默认 folder**：
- [ ] `harness archive req-xx`（不传 `--folder`）在 `main` 分支时，归档到 `.workflow/flow/archive/main/req-xx/`
- [ ] branch 名含 `/` 时自动替换为 `-`
- [ ] 非 git 仓库时降级，直接放 `archive/` 下

**交互式选择**：
- [ ] `harness archive`（无 req-id）弹出 done 需求列表，选择后确认执行
- [ ] `harness archive req-xx`（已传 req-id）弹出列表且预选中该项，确认后执行
- [ ] `harness enter`（无 req-id）弹出 active 需求列表
- [ ] `harness enter req-xx`（已传 req-id）直接进入，不弹列表
- [ ] 无可选项时给出明确提示

**归档完整迁移**：
- [ ] 归档后 `state/sessions/req-xx/` 不再保留于原位
- [ ] 归档后 `state/requirements/req-xx-{title}.yaml` 不再保留于原位
- [ ] 归档目录内可见 `sessions/` 和 `state.yaml`

**制品仓库**：
- [ ] 归档后 `artifacts/requirements/{req-id}-{title}.md` 被创建
- [ ] 文档包含：背景、目标、范围、验收标准、变更列表、关键设计决策、遗留问题
- [ ] 新成员阅读后可理解业务背景并知晓关键实现决策
- [ ] `artifacts/requirements/` 目录在首次归档时自动创建

## 变更列表

- **chg-01** kimicli 平台核心实现（render_kimi_command_skill + _managed_file_contents）：在 `core.py` 中新增 `render_kimi_command_skill()` 函数，生成符合 kimicli 格式（YAML frontmatter + Markdown）的 `.kimi/skills/{command}/SKILL.md`；并在 `_managed_file_contents()` 中为所有 `COMMAND_DEFINITIONS` 生成 kimi skills，使 harness 能够向 kimicli 平台输出托管的 skill 文件。
- **chg-02** 平台选择与检测更新（install 列表 + get_active_platforms + Hard Gate）：将 kimi 平台注册到整个平台生命周期管理体系中：`install_repo` 默认选项加入 kimi、`prompt_platform_selection` 展示 kimi 选项、`get_active_platforms` 识别 `.kimi/skills/` 目录、`get_platform_file_patterns` 返回 kimi 文件模式、`sync_platforms_state` 支持 kimi 的 backup/restore；同时在 `render_agent_command` Hard Gate 说明中增加 `.kimi/skills/harness/SKILL.md` 检查路径。
- **chg-03** 归档默认 folder = 当前 git 分支名：当 `harness archive` 不传 `--folder` 参数时，自动读取当前 git 分支名作为默认 folder，使归档目录自动组织到与开发分支同名的子目录下，便于按分支追溯需求历史。非 git 仓库或 branch 读取失败时降级为原有行为（直接放 `archive/` 下）。
- **chg-04** 交互式需求列表选择（archive 弹列表/预选，enter 无参弹列表）：改造 `harness archive` 和 `harness enter` 命令的交互模式：archive 无论是否传入 req-id 均弹出 done 需求列表（传入时预选），enter 无参数时弹出 active 需求列表；减少输入错误，提升操作可发现性。
- **chg-05** 归档完整迁移（sessions + state.yaml 打包进归档目录）：在归档操作中，将需求的会话记录（`state/sessions/req-xx/`）和需求状态文件（`state/requirements/req-xx-{title}.yaml`）一并迁移到归档目录内，实现需求所有关联文档的集中存放，归档后原位置不保留对应文件。
- **chg-06** 制品仓库 artifacts/requirements/ 输出：归档时在根目录 `artifacts/requirements/` 下自动生成需求摘要文档 `{req-id}-{title}.md`，聚合 requirement.md、各 change.md、session-memory.md、done-report.md 等内容，让未参与过该需求的开发者能快速了解业务背景、目标、实现决策并接手后续开发。
- **chg-07** README 与文档更新（kimicli 平台 + artifacts/ 制品仓库说明）：更新 `README.md` 和 `README.zh.md`，将 kimicli 加入受支持平台列表（含安装说明和 skill 路径），并新增 `artifacts/` 制品仓库功能说明，使文档与 chg-01/chg-02 实现的平台能力和 chg-06 实现的制品仓库功能保持一致。

## 关键设计决策

**chg-03**
- `_get_git_branch()` 使用 `subprocess.run` + `cwd=root`，timeout=5，capture_output=True
- branch 中 `/` 替换为 `-`（feature/auth → feature-auth）
- detached HEAD 或非 git 仓库均返回空字符串，降级为 archive 根目录
**chg-04**
- `prompt_requirement_selection` 使用 `questionary.select()`（单选，非 checkbox）
- 非 TTY 环境直接返回 default_value（preselect 或首项）
- archive 无 done 需求时打印提示并 return 1（不报错）
- enter 无 active 需求时仍正常进入 harness mode（不强制要求选择）
- archive preselect：传入 req-id 如果在列表中则预选，否则选首项
**chg-05**
- state.yaml 迁移在 save_simple_yaml 之后、break 之前执行（确保 status=archived 已写入）
- sessions 迁移在 runtime 更新之后执行（archived_req_id 必须已赋值）
- sessions 目录不存在时静默跳过（不报错），兼容旧需求
- 移动目标：`target / "state.yaml"` 和 `target / "sessions"`
**chg-06**
- `_extract_section` 匹配包含 heading 关键词的 `## ` 开头行（兼容数字前缀如 `## 2. Goal`）
- 同时尝试中英文关键词（Goal/目标，Scope/范围，Acceptance/验收）
- git_branch 在 generate_requirement_artifact 内部调用 `_get_git_branch(root)`（避免参数链路传递）
- req_title 从 `req_dir.name` 用 `re.sub(r"^req-\d+-", "", ...)` 提取
- artifact 生成失败用 try/except 捕获，打印 Warning 但不中断归档
- 空章节整体跳过（不输出空的 ## 标题）

## 遗留问题与注意事项

1. **WORKFLOW_SEQUENCE 无 testing/acceptance**：harness 工具本身的 CLI 没有这两个阶段，导致自身需求无法走完整流程。后续可评估是否增加这两个阶段到 WORKFLOW_SEQUENCE。

2. **pipx inject 开发体验**：每次修改 core.py 后需 `pipx inject harness-workflow . --force`，建议补充开发文档或 Makefile。

3. **interactive archive 与 done-state 的 AC 差异**：requirement.md AC 说明「传入 req-id 时弹出列表预选中」，但实现中 `harness archive req-05` 在 done reqs 列表中查找 req-05 预选 —— 若 req-05 尚未到 done 阶段则找不到，会触发「无可归档需求」提示。这是符合设计意图的行为，但可能让用户困惑。建议在文档中说明。

---
