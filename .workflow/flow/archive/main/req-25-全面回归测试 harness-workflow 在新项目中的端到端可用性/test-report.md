# req-25 端到端回归测试报告

## 测试元信息

| 项 | 值 |
|---|---|
| 测试床绝对路径 | `/tmp/harness-regression-20260419-104820` |
| harness CLI 路径 | `/Users/jiazhiwei/.local/bin/harness`（pipx 安装，指向源 `/Users/jiazhiwei/claudeProject/harness-workflow/src`） |
| 源仓绝对路径 | `/Users/jiazhiwei/IdeaProjects/harness-workflow`（主仓，未改动） |
| 执行日期 | 2026-04-19 |
| 执行角色 | executing subagent（req-25） |
| 日志根路径 | `artifacts/main/requirements/req-25-.../regression-logs/` |
| 总命令数 | 53 条日志（含 3 条结构化信息日志） |
| 通过数 | 36 |
| 失败数 | 14 |
| 信息日志（无退出码） | 3 |

## 分类覆盖摘要

| 类别 | 目录 | 命令数 | 通过 | 失败 |
|---|---|---|---|---|
| A. 安装更新 | `01-install-update/` | 10 | 9 | 1（空仓 install 失败，但 init 可绕过） |
| B. 会话控制 | `02-session-control/` | 7 | 5 | 2（validate 两次） |
| C. 工作流推进 | `03-workflow-advance/` | 0 | - | - (任务禁止 next/ff) |
| D. 工件管理 | `04-artifact-mgmt/` | 11 | 3 | 8（rename/archive 全失败） |
| E. 辅助功能 | `05-auxiliary/` | 17 | 14 | 3 |
| F. skill 安装 | `06-skill-install/` | 4 | 4 | 0（功能成功但产出不一致） |
| G. 结构校验 | `07-artifact-structure/` | 4 | 1 | 0（信息日志，发现多项问题） |

## 问题清单

### P0（阻断首次使用 / 核心产出缺失）

#### P0-01 空仓首次 `harness install` 被拒绝

- **重现步骤**：
  1. `mkdir /tmp/new-repo && cd /tmp/new-repo && git init`
  2. `harness install`
- **期望行为**：`install` 应在空仓库中自动初始化 `.workflow/` 骨架，然后继续安装 skill。README / WORKFLOW.md / SKILL.md 都强调 "Run `harness install` first"，所以这应是唯一首次入口。
- **实际行为**：退出码 1，输出 `Harness workspace is missing. Run 'harness install' or 'harness init' first. Missing: .../.workflow, .../.workflow/context`。建议语同语义矛盾（install 在提示 "run install"）。需要先额外执行 `harness init` 才能再 `harness install`。
- **证据**：`regression-logs/01-install-update/01-install.log`
- **优先级**：**P0**（绝大多数新用户会首先调 `install`；要求额外先调 `init` 是阻断性 UX 断裂，且现有文档没有提示这条路径）

#### P0-02 scaffold 模板携带老 repo 污染状态

- **重现步骤**：
  1. 空仓执行 `harness init`（或 `install` 在 init 之后的流程）
  2. `cat .workflow/state/runtime.yaml`
  3. `ls .workflow/state/sessions/`、`ls .workflow/flow/archive/`、`ls .workflow/flow/suggestions/archive/`
- **期望行为**：新仓 `runtime.yaml` 应为"干净空白"的初始值（比如 `current_requirement: ""`, `stage: "requirement_review"` 或对应空值，`active_requirements: []`），sessions / archive / suggestions/archive 应为空。
- **实际行为**：`runtime.yaml` 开箱即带 `current_requirement: "req-25"`, `stage: "done"`, `ff_mode: true`, `active_requirements: [req-25]`。此外：
  - `.workflow/state/sessions/` 包含 10 个他仓历史 `req-02` ~ `req-11`。
  - `.workflow/flow/archive/main/`、`.workflow/flow/archive/req-20-审查Yh-platform工作流与产出/` 预先存在。
  - `.workflow/flow/suggestions/archive/` 携 7 个他仓历史 `sug-01-executing-selftest-restart.md` 等。
  - `.workflow/archive/` 下 `v0.1.0-self-optimization/`、`v0.2.0-refactor/`、`legacy-cleanup/`、`qoder/` 等 harness-workflow 自身历史泄漏。
- **证据**：`regression-logs/01-install-update/09-status.log`（首次 status 即显示 req-25/done）、`regression-logs/07-artifact-structure/03-final-tree.log`、`regression-logs/07-artifact-structure/04-pollution.log`
- **根因**：`src/harness_workflow/assets/scaffold_v2/` 直接复制了主 repo 当前 .workflow 子树，未清洗私有历史。
- **优先级**：**P0**（状态不正确导致 `status` 等命令对新用户展示假信息，同时污染隐私与预期）

#### P0-03 `harness validate` 报 "Requirement not found"

- **重现步骤**：
  1. 空仓 `harness init`（或 install 后），`harness requirement "test"` 创建 req-01。
  2. `harness validate`
- **期望行为**：对当前 requirement (req-01) 返回校验结果（缺 testing-report / acceptance-report 等）。
- **实际行为**：退出码 1，输出 `Requirement not found: req-01`。即使 `artifacts/main/requirements/req-01-test/` 目录和 `.workflow/state/requirements/req-01-test.yaml` 都存在。
- **根因**（已定位）：`src/harness_workflow/workflow_helpers.py:3897` `validate_requirement` 在 `.workflow/flow/requirements` 目录下查找；而 req-27 之后 requirement 已移到 `artifacts/{branch}/requirements/`。
- **证据**：`regression-logs/02-session-control/03-validate.log`、`regression-logs/02-session-control/07-validate-existing.log`
- **优先级**：**P0**（核心 Acceptance 命令完全不可用）

#### P0-04 `harness archive` 报 "No done requirements available" 即便标记为 done

- **重现步骤**：
  1. 创建 req-01，手动把 state yaml 改为 `stage: done, status: done`。
  2. `harness archive req-01` 或 `harness archive`（list 模式）。
- **期望行为**：将 `artifacts/main/requirements/req-01-.../` 整体移动到 `artifacts/main/archive/{branch}/req-01-.../` 或对应 folder。
- **实际行为**：
  - 空参数形式：`No done requirements available to archive.`（rc=1）
  - 带参形式：`Requirement does not exist: req-01`（rc=1）
- **根因**：`archive_requirement` 同样使用 `.workflow/flow/requirements` 路径（`workflow_helpers.py:3782`），未迁移到 `artifacts/{branch}/requirements`。
- **证据**：`regression-logs/04-artifact-mgmt/05-archive-list.log`、`06-archive-req01.log`、`07-archive-folder.log`、`08-archive-after-done.log`、`09-archive-req01.log`
- **优先级**：**P0**（`archive` 是完整闭环的终点，断裂意味着需求永远无法归档）

#### P0-05 `harness rename` 对已存在的 requirement 一律报 "does not exist"

- **重现步骤**：
  1. 创建 req-01，`ls artifacts/main/requirements/` 确认 `req-01-test-regression-req` 存在。
  2. `harness rename requirement req-01 test-renamed`（或使用 title、完整目录名）。
- **期望行为**：在保留 id 前提下重命名目录和 state yaml 为新 title。
- **实际行为**：三种引用形式全部返回 `Requirement does not exist: {name}`，rc=1。
- **根因**：`rename` 代码路径（`workflow_helpers.py:3530`、`3562`）同样指向 `.workflow/flow/requirements`。
- **证据**：`regression-logs/04-artifact-mgmt/04-rename.log`、`04b-rename-title.log`、`04c-rename-fulldir.log`
- **优先级**：**P0**（rename 不可用，新用户无法修正命名错误）

#### P0-06 kimi agent skill 产出缺失关键子目录

- **重现步骤**：
  1. 空仓 init，`harness install --agent kimi`。
  2. 对比 `.kimi/skills/harness/` 与 `.codex/skills/harness/`、`.claude/skills/harness/`、`.qoder/skills/harness/`。
- **期望行为**：四个 agent 的 `skills/harness/` 子树应一致（至少包含 `SKILL.md`、`agent/`、`agents/`、`assets/templates/`、`references/`、`scripts/`、`tests/`）。
- **实际行为**：`.kimi/skills/harness/` 仅有 `SKILL.md` 和 `agent/`，缺失 `agents/`、`assets/`、`references/`、`scripts/`、`tests/`（codex / claude / qoder 都有这些目录）。这会导致 kimi agent 按 SKILL 引用 `references/harness-principles.md` 等文件时找不到。
- **证据**：`regression-logs/06-skill-install/03-install-kimi.log` + Tree 对比（见 07-artifact-structure/03-final-tree.log）
- **优先级**：**P0**（req-25 Acceptance 4 明确要求四 agent 一致安装可识别）

### P1（可绕过但明显影响体验）

#### P1-01 `harness enter` 行为不一致，语义多重

- **重现步骤**：
  1. `harness status` 显示 `current_requirement: bugfix-1, conversation_mode: open`。
  2. `harness enter`。
- **期望行为**：明确仅切换 `conversation_mode: harness`，不应同时更改 `current_requirement`。
- **实际行为**：同时静默地把 `current_requirement` 从 `bugfix-1` 改为 `req-01`（根据某个未文档化的优先级规则）。`enter` 同时输出 "No active requirements found." 和 "Entered harness mode." 两条矛盾提示。
- **证据**：`regression-logs/02-session-control/01-enter.log`、`05-enter-twice.log`
- **优先级**：**P1**（无日志说明会让用户困惑"为什么我的 current 换了"）

#### P1-02 `harness suggest --apply` 创建含空格的目录名

- **重现步骤**：
  1. `harness suggest "test suggestion content"` → sug-01。
  2. `harness suggest --apply sug-01`。
  3. `ls artifacts/main/requirements/`。
- **期望行为**：目录名应 slugify（如 `req-02-test-suggestion-content`）。
- **实际行为**：生成 `req-02-test suggestion content/`（含空格），对应 state yaml 也是 `req-02-test suggestion content.yaml`。后续所有 shell 操作都要注意 quoting。
- **证据**：`regression-logs/05-auxiliary/09-suggest-apply.log`
- **优先级**：**P1**

#### P1-03 `harness tool-rate` 接受任意未知 tool_id

- **重现步骤**：`harness tool-rate unknown-tool 3`。
- **期望行为**：应校验 tool_id 是否在 `.workflow/tools/catalog/` 中，否则报错。
- **实际行为**：rc=0，输出 `Rated unknown-tool: 3.0 (from 0 ratings)`，随意写入评分文件。
- **证据**：`regression-logs/05-auxiliary/16-tool-rate-unknown.log`
- **优先级**：**P1**（会把评分表污染）

#### P1-04 `harness install --agent xxx` 多次调用时反复 add/delete 同组管理文件

- **重现步骤**：依次 `harness install --agent codex`、`--agent claude`、`--agent kimi`、`--agent qoder`。
- **期望行为**：每次 install 只增量安装对应 agent 的文件。
- **实际行为**：每次都把 `scripts/harness.py`、`scripts/lint_harness_repo.py`、`tests/__pycache__/*.pyc`、`tests/test_harness_cli.py` 加入 `[delete]` 列表，再把 `agent/claude.md` 等加入 `[add]`。前后 install 有隐式反转行为，难以幂等。
- **证据**：`regression-logs/06-skill-install/01-install-codex.log` ~ `04-install-qoder.log`
- **优先级**：**P1**（功能仍成功但 changes 报告很吵）

#### P1-05 `scaffold_v2` 将 `.DS_Store` 和 `__pycache__/*.pyc` 打包分发

- **重现步骤**：空仓 init 后 `find . -name "*.pyc" -o -name ".DS_Store"`。
- **期望行为**：scaffold 不应包含这些 OS / Python 运行时产物。
- **实际行为**：
  - `.claude/skills/harness/assets/.DS_Store`、`.codex/...`、`.qoder/...`
  - `.claude/skills/harness/tests/__pycache__/test_harness_cli.cpython-314-pytest-9.0.3.pyc` 等
- **证据**：`regression-logs/07-artifact-structure/03-final-tree.log`
- **优先级**：**P1**

#### P1-06 `artifacts/{branch}/` 实际结构与 Scope 3.1.2 文档不一致

- **重现步骤**：按 Scope 3.1.2 期望找 `artifacts/main/changes/`、`artifacts/main/bugfixes/`、`artifacts/main/archive/`。
- **期望行为**：Scope 文档示意的平行结构。
- **实际行为**：
  - `changes/` 不在 `artifacts/main/` 下，而是嵌套在 `artifacts/main/requirements/req-XX-.../changes/`。
  - `bugfixes/` 在 `artifacts/main/bugfixes/` 存在（OK）。
  - `archive/` 根本未生成（见 P0-04 archive 不可用）。
  - 源仓 `/Users/jiazhiwei/IdeaProjects/harness-workflow/artifacts/` 还有与 `main/` 同层的 `requirements/`、`bugfixes/`（未被 req-27 重构覆盖），表明 req-27 本身落实不完整。
- **证据**：`regression-logs/07-artifact-structure/01-artifact-tree.log`
- **优先级**：**P1**（需要对齐文档或代码其中之一）

### P2（打磨级）

#### P2-01 `regression --cancel` 仍给出完成类提示

- **重现步骤**：`harness regression "test issue"` → `harness regression --cancel`。
- **期望行为**：简单确认取消即可。
- **实际行为**：额外输出 `Created regression experience: .workflow/context/experience/regression/test-issue.md` 与 `Consider summarizing lessons...` 建议。一般"取消"不应同时沉淀经验。
- **证据**：`regression-logs/05-auxiliary/08-regression-cancel.log`
- **优先级**：**P2**

#### P2-02 `harness update --scan` 对于未识别项目无更具体的指导

- **实际行为**：输出"未检测到已知技术栈"等通用建议，未对当前测试床做针对性适配。
- **证据**：`regression-logs/01-install-update/06-update-scan.log`
- **优先级**：**P2**

#### P2-03 `harness feedback` 产出文件写入 repo 根（可能意外入 git）

- **实际行为**：`Feedback exported to /private/tmp/.../harness-feedback.json` 置于 repo 根。若用户未把它加入 .gitignore 会被误提交。
- **证据**：`regression-logs/05-auxiliary/06-feedback.log`
- **优先级**：**P2**

## P0 可修复性评估

P0-01 ~ P0-06 全部可在本 req-25 周期内修复：

1. **P0-01**：修改 `install_command` 在未发现 `.workflow` 时先内联调用 `init_docs`，然后继续 skill install。
2. **P0-02**：清洗 `src/harness_workflow/assets/scaffold_v2/.workflow/state/runtime.yaml` 为初始值；从 scaffold 中剔除 `state/sessions/req-XX/`、`flow/archive/`、`flow/suggestions/archive/`（或仅保留空目录占位）、`archive/` 下的他仓历史。
3. **P0-03 / P0-04 / P0-05**：统一把 `.workflow/flow/requirements` 读取点改为 `artifacts/{branch}/requirements`（或新引入的 helper `resolve_requirement_root(root) -> Path`）。至少需要修改 `workflow_helpers.py` 的 9 处引用。
4. **P0-06**：检查 `install --agent kimi` 的打包路径，补齐 `references/`、`scripts/`、`assets/`、`tests/` 复制逻辑，或让四 agent 共用一个通用复制函数。

**阻塞因素**：无。所有 P0 根因明确，均在 `src/harness_workflow/` 内可改。

## P1 / P2 延期说明

本次按 req-25 Acceptance 8 仅做"记录 + 估期"：

| ID | 延期原因 | 建议负责人 | 预计闭环窗口 |
|---|---|---|---|
| P1-01 | 需先澄清 `enter` 语义设计（是否应该锁定 current_requirement） | 架构师角色 | req-28 或 req-29 |
| P1-02 | 与 `requirement` 命令 slugify 统一 | executing | P0 修完后一并改 |
| P1-03 | 需先定义 "未知 tool_id 是否允许"的策略 | 架构师 | req-28 |
| P1-04 | install 幂等性整体需要设计 | architecture | 下一个 minor 版本 |
| P1-05 | 打包流程清理（增加 MANIFEST 过滤） | release 流程负责人 | 下一次发布 |
| P1-06 | req-27 重构收口未完成，需要独立 req | architecture | req-27 后续迭代 |
| P2-01 | 语义调整，影响面小 | executing | 任意空闲窗口 |
| P2-02 | 与 project-scan 能力绑定 | architecture | 技术栈扩展时 |
| P2-03 | 产物落盘位置策略 | architecture | 任意窗口 |

## 回归测试床保留

测试床 `/tmp/harness-regression-20260419-104820/` 保留，以便 P0 修复后在**等价新建空仓**（例如 `/tmp/harness-regression-<ts2>-postfix/`）上重跑 3.1.1 命令链路并对比结果。

## 结论

- 总体结论：**本次回归暴露 6 个 P0 阻断性问题**，新用户在"git clone harness-workflow → 开 install → requirement → change → archive" 的主路径上**无法完成整条闭环**（`install` 需要先调 `init`；`validate` / `archive` / `rename` 全部因路径硬编码到废弃的 `.workflow/flow/requirements` 而失败）。
- **需求主目标"新用户首次使用零断裂"不达标**，建议本 req 继续推进到 regression / 下一轮 change，对 P0 统一闭环后再进入 acceptance。
- 所有原始日志保存在 `regression-logs/` 七个子目录内，命令全文、执行时间、工作目录、stdout+stderr、退出码字段齐全。
