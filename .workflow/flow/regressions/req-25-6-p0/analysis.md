# Regression Analysis — req-25-6-p0

**诊断范围**：req-25 executing 阶段端到端测试报告中提交的 6 项 P0
**诊断日期**：2026-04-19
**诊断师**：regression subagent（独立核查，不带 executing 偏见）

---

## 1. Problem Assessment 汇总

| ID | 现象 | 真问题? | 根因文件 : 行 | 影响面 |
|---|---|---|---|---|
| P0-01 | 空仓 `harness install` 被拒，要求先 `init` | confirm | `src/harness_workflow/workflow_helpers.py:2137-2142`（`ensure_harness_root`） + `4173`（`install_agent` 入口即调 `ensure_harness_root`） | 任何"首次接触 harness"的新用户。`harness install` 在 CLAUDE.md / WORKFLOW.md / README 都是首选入口，但代码在 workspace 未建成前直接 fail。`--agent kimi/claude/codex/qoder` 四路径全部走同一入口，空仓均不可用 |
| P0-02 | scaffold 打包 harness-workflow 自身历史 | confirm | 数据根因：`src/harness_workflow/assets/scaffold_v2/` 物理目录含 73 个泄漏文件（req-01~req-25 历史归档、10 个旧 sessions、7 个旧 suggestions、archive v0.1.0/v0.2.0/legacy-cleanup 等）；行为根因：`_sync_requirement_workflow_managed_files` 经 `init_repo` 原样复制 scaffold 到目标仓 | 所有新仓 `harness init` 后初始状态继承旧数据，首次 `status` 即显示 req-25/done/ff=true 假信息。隐私 + 预期双重污染 |
| P0-03 | `harness validate` 报 "Requirement not found" | confirm | `src/harness_workflow/workflow_helpers.py:3897`：`validate_requirement` 在 `.workflow/flow/requirements` 查找；但 `create_requirement:3174` 写到 `artifacts/{branch}/requirements/` | Acceptance 闭环断裂，任何需求创建后立刻 validate 都报 not found |
| P0-04 | `harness archive` 报 "No done requirements / does not exist" | confirm | `src/harness_workflow/workflow_helpers.py:3782` `archive_requirement`、`3830` 残留清理、`3791` archive_base 均指向 `.workflow/flow/...` 废弃路径 | 归档命令完全不可用，需求永远无法闭环；archive 目标路径与 req-27 拟定的 `artifacts/{branch}/archive` 方向亦不一致 |
| P0-05 | `harness rename` 报 "Requirement does not exist" | confirm | `src/harness_workflow/workflow_helpers.py:3530` `rename_requirement`、`3562` `rename_change` 中解析 requirement 的路径 | 用户创建命名错误后无法修正，三种引用形式（id / title / 完整目录名）全部失败 |
| P0-06 | `harness install --agent kimi` 产出缺失关键子目录 | confirm | 两处分叉的 template root：①`workflow_helpers.py:1962-1975` `_project_skill_targets` 明确 `# kimi 不通过 install_local_skills 安装` 而遗漏"其他机制"；②`workflow_helpers.py:4147-4149` `get_skill_template_root` 返回 `skills/harness/`（仅 SKILL.md + agent/）不等于 `SKILL_ROOT = assets/skill/`（定义于 `workflow_helpers.py:33`，含 agents/assets/references/scripts/tests）；衍生缺陷：`install_agent:4184-4213` 的 [delete]/[modify] 只打印，copy loop `4219-4229` 并未真实删除 | 直接违反 req-25 Acceptance 4（四 agent 一致安装）。kimi SKILL.md 里引用 `references/harness-principles.md` 等会 404。codex/claude/qoder 看似正确实为"残留文件 + 无清理"的巧合 |

---

## 2. Evidence

### P0-01
- 日志：`regression-logs/01-install-update/01-install.log`（rc=1，"Harness workspace is missing"）
- 代码：`workflow_helpers.py:2137-2142` 在 `.workflow` 或 `.workflow/context` 缺失时 `raise SystemExit`；`workflow_helpers.py:4163-4173` `install_agent` 首行即调用；`cli.py:263-270` 所有 `install` 路径最终走 `install_agent`
- 结论：install 入口假设 workspace 已存在，文档里与 init 并列实则代码把 install 设为 init 下游

### P0-02
- 日志：`regression-logs/01-install-update/09-status.log`、`07-artifact-structure/03-final-tree.log`、`04-pollution.log`
- 文件树证据：`scaffold_v2/.workflow/state/sessions/req-07..req-11`、`scaffold_v2/.workflow/flow/archive/main/req-01..req-23`、`scaffold_v2/.workflow/flow/suggestions/archive/`（7 个 sug-*.md）、`scaffold_v2/.workflow/archive/legacy-cleanup|v0.1.0-self-optimization|v0.2.0-refactor|qoder`、`scaffold_v2/.workflow/flow/requirements/req-25-harness 完全由 harness-manager 角色托管/done-report.md`
- 结论：scaffold_v2 是主仓 `.workflow/` 历史快照的未清洗拷贝

### P0-03 / P0-04 / P0-05（共享根因）
- 日志：`02-session-control/03-validate.log`、`07-validate-existing.log`（P0-03）；`04-artifact-mgmt/05..09-archive-*.log`（P0-04）；`04-artifact-mgmt/04-rename*.log`（P0-05）
- 废弃路径硬编码清单（`workflow_helpers.py`）：
  - `3134` 建议打包后写入 requirement.md（潜在下游问题）
  - `3377` `create_change` 的 req_dir 解析分支
  - `3530`、`3562` rename_requirement / rename_change
  - `3782`、`3830` archive_requirement 主目录 + 残留清理
  - `3897` validate_requirement
  - `2052`、`2862` `_sync_requirement_workflow_managed_files` 路径锚点
- 对比正确路径：`3174` `create_requirement` 写 `artifacts/{branch}/requirements/`、`3341` `create_change` 另一分支、`3680` artifact 生成目录
- 结论：req-27 路径重构未收口，至少 9 处硬编码未迁移

### P0-06
- 日志：`06-skill-install/01..04-install-*.log` — codex/claude/qoder 首行 `[modify] SKILL.md` + 大量 [delete]；kimi 仅 `[modify] agent/*.md` 3 行
- 代码：`workflow_helpers.py:33-34` `SKILL_ROOT = assets/skill`（富模板）vs `4147-4149` `get_skill_template_root` 返回 `skills/harness`（瘦模板）；`1962-1975` `_project_skill_targets` 跳过 kimi；`4206-4213` changes 仅打印、`4219-4229` copy loop 不执行 delete/modify
- 结论：两层缺陷叠加——设计性跳过 kimi + install_agent 的 install 过程与 changes 声明不一致

---

## 3. Discussion Outcome

- 6 项全部 **confirm** 为真实问题，**0 项 reject**
- 衍生发现：
  - `install_agent` 的 [delete]/[modify] 声明与真实行为不符（P0-06 衍生，需随 P0-06 一并修）
  - scaffold_v2 内藏 `flow/requirements/req-25-harness 完全由 harness-manager 角色托管/` 含主仓进度快照（P0-02 衍生）
- **req-27**（artifacts 根目录重构）已创建但未完成 rename / archive / validate / create_change 读取端迁移 — 这是 P0-03/04/05 的共同祖先
- P0-03/04/05 三项应合并为单一 change："完成 req-27 遗留的 requirement 路径解析迁移"

---

## 4. Recommended Action

详见 `decision.md`。概要：

| 组 | P0 | 路由 | 建议入口 |
|---|---|---|---|
| A | P0-03 + P0-04 + P0-05 | 合并为 1 个 change（req-25 下新增），共同根因：req-27 路径迁移遗漏 | `harness change "完成 requirement 路径迁移到 artifacts/{branch}"` |
| B | P0-01 | 单点 bugfix | `harness bugfix "install 在空仓应自动 init"` |
| C | P0-02 | 单点 bugfix（含 scaffold 清洗 + 首次 runtime 状态校正） | `harness bugfix "scaffold_v2 清洗 harness-workflow 自身历史"` |
| D | P0-06 | 单点 bugfix（双问题：kimi 模板 + install_agent 一致性） | `harness bugfix "install --agent kimi 产出缺失 + install_agent delete 未执行"` |

**均可在 req-25 周期内闭环，无需新 requirement。无需人工输入。**

