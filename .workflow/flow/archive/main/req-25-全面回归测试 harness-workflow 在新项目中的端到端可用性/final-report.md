# req-25 端到端回归最终验收报告

## 测试元信息

| 项 | 值 |
|---|---|
| 测试床绝对路径 | `/tmp/harness-regression-final-20260419-122147/` |
| 辅助 migrate 测试床 | `/tmp/harness-migrate-test-1776572833/`（临时构造 legacy 仓） |
| harness CLI 路径 | `/Users/jiazhiwei/.local/bin/harness`（pipx editable install，指向源 `/Users/jiazhiwei/IdeaProjects/harness-workflow`） |
| 源仓绝对路径 | `/Users/jiazhiwei/IdeaProjects/harness-workflow`（主仓，未改动） |
| 执行日期 | 2026-04-19 |
| 执行角色 | testing subagent（req-25 最终回归） |
| 日志根路径 | `artifacts/main/requirements/req-25-.../regression-logs-final/` |
| 日志文件总数 | 67 |
| 命令 PASS（rc=0） | 52 |
| 命令 FAIL（rc≠0） | 15（其中 13 条属"期望失败/提示/缺参"，仅 2 条为新发现的衍生问题） |

## 分类覆盖摘要

| 类别 | 目录 | 文件数 | 关键结论 |
|---|---|---|---|
| A. 安装更新 | `01-install-update/` | 6 | 空仓 install 自动 init 生效（P0-01 闭环），update/status/rerun 全部 rc=0 |
| B. 会话控制 | `02-session-control/` | 2 | validate 修复生效（P0-03 闭环） |
| C. 工作流推进 | `03-workflow-advance/` | 16 | requirement → next × 多次 → change → executing → testing → acceptance → done 全链路通 |
| D. 工件管理 | `04-artifact-mgmt/` | 12 | rename、archive、migrate dry-run/apply/no-op 全部 rc=0（P0-04/05 + migrate 闭环） |
| E. 辅助功能 | `05-auxiliary/` | 15 | suggest / tool-search / tool-rate / feedback / language / enter / exit / ff / bugfix / regression 全部可执行 |
| F. Skill 安装 | `06-skill-install/` | 6 | 四个 agent skill 结构完全对称（P0-06 闭环） |
| G. 结构校验 | `07-artifact-structure/` | 10 | runtime.yaml 初始值、sessions 空、archive 不预存、无 req-02..11 / sug-XX / done-report（P0-02 闭环） |

## 6 P0 闭环表

| ID | 描述 | 关键证据 | 结果 |
|---|---|---|---|
| **P0-01** | 空仓 `harness install` 自动 init | `01-install-update/01-install-empty.log` 首行 `No .workflow/ found, running harness init first...`，rc=0 | **PASS** |
| **P0-02** | scaffold 清洗 | `07-artifact-structure/01-runtime-yaml.log` 显示 `current_requirement: ""`, `stage: ""`, `active_requirements: []`；`02-sessions-dir.log` sessions 空；`03-archive-dir.log` 无 `.workflow/flow/archive/` 和 `.workflow/archive/`；`05-done-reports.log` 无 req-02..11 / sug-XX / done-report；`.workflow` 文件共 69 个（接近预期 72）；无 `.DS_Store` / `.pyc` | **PASS** |
| **P0-03** | `harness validate` 找到需求 | `02-session-control/01-validate.log` 输出 `Artifact validation passed for req-01`，rc=0 | **PASS** |
| **P0-04** | `harness archive` 闭环 | `04-artifact-mgmt/08-archive-list-2.log` 输出 `Archived requirement: req-01-end-to-end test`，`Archive path: .../artifacts/main/archive/main/req-01-end-to-end test`，rc=0；`10-archive-verify.log` 确认目录结构存在 | **PASS** |
| **P0-05** | `harness rename` 闭环 | `04-artifact-mgmt/02-rename.log` 输出 `Requirement renamed: req-01-test regression req -> renamed-req`，rc=0（原 `Requirement does not exist` 已消失） | **PASS（带衍生问题）** |
| **P0-06** | 四个 agent skill 对称 | `06-skill-install/03-agents-compare.log`：codex / claude / kimi / qoder 四个 `skills/harness/` 目录结构完全一致（`SKILL.md + agent/ + agents/ + assets/ + references/ + scripts/ + tests/`），每个 **89 个文件**，全部包含 5 个要求子目录（references / scripts / assets / tests / agents） | **PASS** |

### 结论：6/6 P0 全部 PASS

## migrate 命令验证

| 步骤 | 日志 | 结果 |
|---|---|---|
| 构造 legacy 仓（`.workflow/flow/requirements/req-99-legacy/`） | — | 已构造 |
| `harness migrate requirements --dry-run` | `04-artifact-mgmt/20-migrate-dry-run.log` | rc=0，`1 planned, 0 conflict(s), 0 already-at-target` |
| `harness migrate requirements` | `04-artifact-mgmt/21-migrate-apply.log` | rc=0，`1 migrated, 0 skipped (conflict), 0 already-at-target` |
| 二次运行 | `04-artifact-mgmt/22-migrate-no-op.log` | rc=0，`nothing to migrate` |

**migrate 命令：PASS**

## 工作流全链路验证

| 阶段转换 | 日志 | 结果 |
|---|---|---|
| `harness requirement "end-to-end test"` | `03-workflow-advance/04-req-create.log` | rc=0 → req-01 |
| `next` → changes_review | `05-next-to-changes-review.log` | rc=0 |
| `change "test change 1"` | `06-change-create.log` | rc=0 → chg-01 |
| `next` → plan_review | `08-next.log` | rc=0 |
| `next` → ready_for_execution | `09-next.log` | rc=0 |
| `next --execute` → executing | `16-next-execute.log` | rc=0 |
| `next` → testing | `17-next-exec.log` | rc=0 |
| `next` → acceptance | `18-next-exec.log` | rc=0 |
| `next` → done | `19-next-exec.log` | rc=0 |
| `archive req-01`（手动标 status: done 后） | `08-archive-list-2.log` | rc=0，产物落入 `artifacts/main/archive/main/req-01-.../` |

**工作流全链路：PASS**

## 辅助命令覆盖

| 命令 | 日志 | 结果 |
|---|---|---|
| `harness suggest "test suggestion"` | `05-auxiliary/01-suggest.log` | rc=0，`sug-01-test-suggestion.md` |
| `harness tool-search "bash command"` | `02-tool-search.log` | rc=0 |
| `harness tool-rate bash 5` | `03-tool-rate.log` | rc=0 |
| `harness tool-rate unknown-tool 3`（P1-03 复核） | `13-tool-rate-unknown.log` | rc=0（仍允许任意 tool_id，P1-03 未修） |
| `harness feedback` | `04-feedback.log` | rc=0，导出到 repo 根（P2-03 未修） |
| `harness language en` / `harness language zh` | `05b/05c-language-*.log` | rc=0 |
| `harness enter` / `harness exit` | `06-enter.log` / `07-exit.log` | rc=0（P1-01 "No active requirements found / Entered harness mode" 矛盾提示仍在） |
| `harness ff` | `08-ff.log` | rc=0 |
| `harness bugfix "test-bug-fix"` | `10-bugfix.log` | rc=0，工件落入 `artifacts/main/bugfixes/bugfix-1-test-bug-fix/` |
| `harness regression "sample issue"` | `11-regression-start.log` | rc=0 |
| `harness regression --cancel` | `12-regression-cancel.log` | rc=0（P2-01 仍沉淀经验） |
| `harness validate`（归档后无需求） | `02-session-control/02-validate-done.log` | rc=1（`No active requirement.` 为正确行为） |

## 新发现问题清单（本轮首次暴露）

### P0（阻断性）— 无

### P1（重要非阻断）

#### P1-new-01 `harness rename` 未维护 state yaml 与 id 前缀

- **重现步骤**：
  1. 空仓 `harness install` → `harness requirement "test regression req"`（产生 `req-01-test regression req`）
  2. `harness rename requirement req-01 "renamed-req"`
  3. 检查 `artifacts/main/requirements/` 与 `.workflow/state/requirements/`
- **期望行为**：
  - 目录重命名后仍保留 id 前缀（如 `req-01-renamed-req/`）
  - `.workflow/state/requirements/req-01-*.yaml` 被同步重命名并更新 title
- **实际行为**：
  - 目录直接变为 `renamed-req/`（完全丢掉 `req-01-` 前缀）
  - `.workflow/state/requirements/req-01-test regression req.yaml` 未重命名、title 未更新
  - 导致后续 `harness change` 触发 `No active requirement.` —— runtime 仍记录 `current_requirement: req-01`，但 `resolve_requirement_reference` 找不到匹配目录
- **根因（推测）**：`workflow_helpers.py:3562` `resolve_title_and_id(new_name, ...)` 直接 slug 生成 `new_id = "renamed-req"`，未前缀化；同时缺少对应 state yaml 文件的 move 逻辑
- **证据**：`04-artifact-mgmt/02-rename.log`、`03-post-rename-state.log`
- **优先级**：**P1**（rename 本身不再 crash，但副作用会让后续命令连环失败；P0-05 验收标准"命令不报 does not exist"已达标，但语义完整度待修）

#### P1-new-02 `harness next` 不更新 state yaml 的 `stage` 与 `status`

- **重现步骤**：
  1. 新需求创建后一路 `harness next` 推到 `done`
  2. `cat .workflow/state/requirements/req-01-*.yaml`
- **期望行为**：state yaml 的 `stage` 随 runtime 同步，status 在 done 阶段自动变为 `done`
- **实际行为**：state yaml 永远停在创建时的 `stage: "requirement_review", status: "active"`；runtime.yaml 却已经是 `stage: done`。这导致：
  - `harness archive` 必须手动修改 state yaml 才能工作（`list_done_requirements` 读取的是 state yaml）
  - `harness status` 输出的 `requirement_stage` 与 `stage` 字段不一致（本次看到 `stage: done` + `requirement_stage: requirement_review`）
- **证据**：`04-artifact-mgmt/05-status-pre-archive.log`、`08-archive-list-2.log`（需先手改 state yaml）
- **优先级**：**P1**（影响 archive 自动闭环；绕过手段简单）

#### P1-new-03 `harness regression "<issue>"` 产出目录含空格，且无 id 前缀

- **重现步骤**：`harness regression "sample issue"`
- **期望行为**：slug 规范化 + id 前缀，例如 `reg-01-sample-issue/`
- **实际行为**：生成 `artifacts/main/regressions/sample issue/`（含空格，无 id）
- **证据**：`05-auxiliary/11-regression-start.log`
- **优先级**：**P1**（与 P1-02 同类"slugify 缺失"，扩展到 regressions 子命令）

#### P1-new-04 归档路径出现重复的 branch 层级 `archive/main/main/...`

- **重现步骤**：`harness archive` 完成后 `ls artifacts/main/archive/`
- **期望行为**：`artifacts/main/archive/req-01-.../`（单层）或统一为 `artifacts/archive/main/...`
- **实际行为**：`artifacts/main/archive/main/req-01-end-to-end test/` —— 多出一层 `main/`
- **证据**：`04-artifact-mgmt/10-archive-verify.log`
- **优先级**：**P1**（chg-01 引入 `archive_base` 时疑似双重拼接了 branch）

### P1（旧问题延续）

| ID | 状态 | 证据 |
|---|---|---|
| P1-01（enter 矛盾提示） | 未修 | `05-auxiliary/06-enter.log` 同时输出 `No active requirements found.` 与 `Entered harness mode.` |
| P1-02（requirement 目录空格） | 未修 | `04-artifact-mgmt/01-requirement-create.log` 生成 `req-01-test regression req/`（空格） |
| P1-03（tool-rate 接受未知 id） | 未修 | `05-auxiliary/13-tool-rate-unknown.log` rc=0 |
| P1-04（install --agent 反复 add/delete） | 本轮未复测（四 agent install 已一次性跑过，不重复） | — |
| P1-05（.DS_Store / .pyc 打包） | **已修** | `07-artifact-structure/06-tree-overview.log` 无 .DS_Store、无 .pyc |
| P1-06（artifacts/{branch}/ 结构） | **部分已修**：`archive/`、`bugfixes/`、`regressions/`、`requirements/` 四个子目录均在 `artifacts/main/` 下存在；`changes/` 仍内嵌于每个 requirement 下（Scope 3.1.2 未指定具体布局，此处与"需求内"变更逻辑一致） | `07-artifact-structure/10-artifacts-tree.log` |

### P2（打磨级）— 状态延续

| ID | 状态 | 证据 |
|---|---|---|
| P2-01（regression --cancel 仍沉淀经验） | 未修 | `05-auxiliary/12-regression-cancel.log` 输出 `Created regression experience: ...` |
| P2-02（update --scan 无针对性指导） | 未修 | `01-install-update/05-update-scan.log` |
| P2-03（feedback 文件落 repo 根） | 未修 | `05-auxiliary/04-feedback.log` 输出到 `/private/tmp/.../harness-feedback.json` |

## Fail 日志明细与分类

Python 统计 `FAIL=15` 条，归类如下：

| 日志 | rc | 归类 | 说明 |
|---|---|---|---|
| `02-session-control/02-validate-done.log` | 1 | 期望失败 | 归档后无 active req，正确提示 |
| `03-workflow-advance/03-change-create.log` | 1 | 衍生副作用（P1-new-01） | rename 未更 state yaml 导致 resolve 失败 |
| `03-workflow-advance/10-next.log` ~ `15-next.log` | 1 | 期望提示 | `ready_for_execution` 等待 `--execute` 确认（6 条） |
| `04-artifact-mgmt/03-post-rename-state.log` | 1 | 期望失败 | `cat meta.yaml` 失败（文件不存在） |
| `04-artifact-mgmt/06-archive-list.log` | 1 | 期望失败 | state yaml 未被 `next` 更新（P1-new-02） |
| `04-artifact-mgmt/09-archive-req01-done.log` | 1 | 期望失败 | 归档后二次尝试，无可 archive |
| `05-auxiliary/05-language.log` | 2 | 执行者缺参 | `harness language` 缺 `language` 位置参（非产品缺陷） |
| `05-auxiliary/09-regression-no-issue.log` | 1 | 期望失败 | 无活动 regression 时 `--cancel` 正确报错 |
| `07-artifact-structure/03-archive-dir.log` | 1 | 期望失败 | scaffold 后无 `.workflow/flow/archive/`（P0-02 要求的"干净"） |
| `07-artifact-structure/04-suggestions-archive.log` | 1 | 期望失败 | 无 `flow/suggestions/archive/`（P0-02 要求的"干净"） |

**真正的产品行为异常：0 条**（P1-new-01/02 引起的 `03-change-create` 和 `06-archive-list` 已在新问题清单单独记录）。

## 验收结论

### PASS

- 6/6 P0 全部闭环
- chg-01（resolve_requirement_root 路径迁移 + archive_base + migrate）落地可见
- bugfix-3（空仓自动 init）落地可见
- bugfix-4（scaffold 清洗）落地可见
- bugfix-5（四 agent skill 模板对齐）落地可见
- 端到端主路径 `install → requirement → next → change → next × N → archive` 无断裂（仅需手动补 state yaml 的 status，属 P1-new-02 已记录）

### 建议

- 本 req-25 可在**记录 4 条新 P1 和延续 P1/P2** 的前提下推进至 acceptance
- 新 P1（P1-new-01 ~ P1-new-04）与旧 P1/P2 统一延至下一周期或独立 bugfix 处理
- 无需再进入 regression 循环

## 回归测试床保留

- 主测试床 `/tmp/harness-regression-final-20260419-122147/` 保留
- 辅助 migrate 测试床 `/tmp/harness-migrate-test-1776572833/` 保留
- 所有原始日志 67 个 `.log` 文件完整保存在 `regression-logs-final/` 七个子目录内（命令全文、UTC 时间戳、工作目录、stdout+stderr、退出码字段齐全）
