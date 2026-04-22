# Regression Diagnosis — bugfix-5

## Issue
`harness install --agent kimi` 安装后 `.kimi/skills/harness/` 目录残缺，缺少 `references / scripts / assets / tests / agents` 共 5 个子目录。触发 P0-06。

## 现象复现（空仓实测）
在空仓 `git init` 后分别执行 `harness install --agent <agent>`，观察 `.<agent>/skills/harness/` 结构：

| agent | 子目录/文件 |
|-------|-------------|
| kimi  | `SKILL.md`, `agent/` (claude.md / codex.md / kimi.md) |
| claude| `SKILL.md`, `agent/` |
| codex | `SKILL.md`, `agent/` |
| qoder | `SKILL.md`, `agent/` |

**初判（P0-06）修正**：缺失**不是 kimi 独有**，而是四个 agent 通过 `--agent` 方式安装后**全部缺失** 5 个子目录。之所以原先只在 kimi 上感到问题，是因为 codex/claude/qoder 在完整路径（`harness install` 不带 `--agent`）下还会走 `install_local_skills()`，从 `assets/skill/` 拷贝完整树；而 kimi 从不走那条路径（代码注释明确："kimi 不通过 install_local_skills 安装"）。

## 根因

项目里存在**两套 skill 模板源**：

1. `src/harness_workflow/assets/skill/`  — **完整模板**，含 `SKILL.md`, `agents/`, `assets/`, `references/`, `scripts/`, `tests/` 5 大子目录 + 子文件
2. `src/harness_workflow/skills/harness/` — **残缺入口模板**，只含 `SKILL.md` + `agent/{claude,codex,kimi}.md`（这里的 `agent/` 是 agent 特异化说明，不是完整模板的 `agents/`）

`install_local_skills()`（给 codex/claude/qoder 走完整 `harness install` 时用）使用 **完整模板** `SKILL_ROOT = assets/skill/`：

- `src/harness_workflow/workflow_helpers.py:34` — `SKILL_ROOT = PACKAGE_ROOT.joinpath("assets", "skill")`
- `src/harness_workflow/workflow_helpers.py:2139` — `_copy_tree(Path(str(SKILL_ROOT)), target)`

`install_agent()`（`harness install --agent <agent>` 走的路径）却使用 **残缺模板** `skills/harness/`：

- `src/harness_workflow/workflow_helpers.py:4356-4358` — `get_skill_template_root()` 返回 `Path(__file__).resolve().parent / "skills" / "harness"`
- `src/harness_workflow/workflow_helpers.py:4402` — `template_root = get_skill_template_root()` 随后作为复制源

两条路径**模板源不一致**导致：
- `harness install` 无 `--agent`（init + install_local_skills 完整流程）→ 对称完整
- `harness install --agent X`（只走 install_agent）→ 全部残缺

`install_agent()` 的循环扫描 `template_root.rglob("*")`（4426/4447 行），扫到什么拷什么；模板根本没有那 5 个子目录，所以一定拷不过去。无过滤规则误杀。

## 根因类型
**B) 同步代码漏拷**（但本质是"选错模板源"）。`install_agent()` 指向了残缺模板，而非完整模板。模板源本身在 `assets/skill/` 下**齐全**，不需要补模板。

## 精确行号（本次修复涉及）
- `src/harness_workflow/workflow_helpers.py:34` — `SKILL_ROOT` 常量（完整模板，继续使用）
- `src/harness_workflow/workflow_helpers.py:4356-4358` — `get_skill_template_root()`：错误指向残缺模板，**需改为指向 `SKILL_ROOT`**
- `src/harness_workflow/workflow_helpers.py:4372-4489` — `install_agent()`：主复制逻辑；行为保留，仅模板源切换；另需**叠加** agent-specific 说明文件

## 对比四个 agent 的差异点
| agent | 通过 `install_local_skills` 安装？ | 通过 `install_agent` 安装？ | 残缺根因 |
|-------|-----|-----|----|
| codex | 是（enabled=codex） | 可选（`--agent codex`） | install_agent 走残缺模板 |
| claude(cc) | 是（enabled=cc） | 可选（`--agent claude`） | 同上 |
| qoder | 是（enabled=qoder） | 可选（`--agent qoder`） | 同上 |
| kimi | **否**（注释：不通过该机制） | 唯一路径 | 同上且无兜底 |

这就是 kimi 看起来"独自残缺"的观感原因：其他 agent 有 `install_local_skills()` 作为兜底，kimi 没有。一旦走 `--agent` 路径，四者都会残缺。

## Routing Direction
- [x] Real issue → proceed to fix
- [ ] False positive → revert to previous stage

**路由**：实现问题 → executing（本 subagent 持续推进）。

## Required Inputs
- 无需人工输入。

## 修复方案
让 `install_agent()` 使用完整模板 `SKILL_ROOT = assets/skill/`，同时叠加 `skills/harness/agent/{agent}.md`（仅对应当前 agent 的文件）到目标 `agent/` 子目录以保留 agent 特异化说明。

**约束**：
- 不破坏 codex/claude/qoder 完整 `harness install` 的现有行为（`install_local_skills` 不动）
- 不修改 `runtime.yaml`，不推进 stage
- 两个模板目录同时保留：`assets/skill/` 为完整源，`skills/harness/agent/*.md` 为 agent 特异化
