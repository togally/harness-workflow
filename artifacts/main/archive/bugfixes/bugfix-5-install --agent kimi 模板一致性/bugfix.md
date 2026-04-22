---
id: bugfix-5
title: install --agent kimi 模板一致性
created_at: 2026-04-19
parent_requirement: req-25
related: P0-06
---

# Problem Description

- **现象**：`harness install --agent kimi` 安装后 `.kimi/skills/harness/` 只有 `SKILL.md` 和 `agent/`，缺失 `references / scripts / assets / tests / agents` 共 5 个子目录。
- **触发条件**：任何空仓或已初始化仓执行 `harness install --agent kimi`。
- **实际影响范围（诊断后修正）**：P0-06 初判此问题为 kimi 独有。实测**所有四个 agent**（kimi/claude/codex/qoder）通过 `--agent` 安装后都缺失相同 5 个子目录。kimi 看起来"独缺"的观感原因：codex/claude/qoder 在完整 `harness install` 流程中还会被 `install_local_skills()` 以 `assets/skill/` 为源兜底拷贝；而代码注释明确 "kimi 不通过 install_local_skills 安装，通过其他机制处理"，因此 kimi 没有兜底。
- **影响**：skill 目录残缺导致 `.kimi/skills/harness/` 下 references 文档、scripts 工具、tests 用例、模板等一律丢失；agent 在该仓内无法按完整 skill 规约工作。

# Root Cause Analysis

**根因类型：B) 同步代码漏拷（本质是"选错模板源"）**。

代码库中并存两套 skill 模板源：

1. `src/harness_workflow/assets/skill/` — 完整模板（6 个子目录，88 个文件）
2. `src/harness_workflow/skills/harness/` — 残缺入口模板（只有 `SKILL.md` + `agent/{claude,codex,kimi}.md`）

两个安装入口指向不同的源：

| 入口 | 模板源 | 代码行号 |
|------|-------|---------|
| `install_local_skills()`（codex/claude/qoder 走完整 `harness install`）| `SKILL_ROOT = assets/skill/` | `workflow_helpers.py:34`, `:2139` |
| `install_agent()`（所有 `--agent` 安装）| `skills/harness/` | `workflow_helpers.py:4356-4358`（旧）|

因此 `install_agent()` 扫描 `skills/harness/` 下的文件（只能扫到 SKILL.md + agent/\*.md）然后拷贝，5 个子目录永远不会出现在目标中。模板源自身齐全，不是模板缺文件；也非过滤误杀。

# Fix Scope

**涉及文件**：
- `src/harness_workflow/workflow_helpers.py` — 修改 `get_skill_template_root()`；新增 `get_agent_notes_root()`；重写 `install_agent()` 的模板扫描/拷贝逻辑
- `src/harness_workflow/skills/harness/agent/qoder.md` — 新建，补齐 qoder 特异化说明（原本缺失导致 qoder 目录结构与其他三个 agent 不对称）

**不在本次修改范围**：
- `install_local_skills()` / `install_repo()` / `_scaffold_v2_file_contents()` / 模板文件本身
- `runtime.yaml`、stage 状态、`.workflow/` 目录

# Fix Plan

1. `get_skill_template_root()` 返回值改为 `Path(str(SKILL_ROOT))`，与 `install_local_skills()` 保持同源。
2. 新增 `get_agent_notes_root()` 指向 `skills/harness/agent/`，存放 agent 特异化说明。
3. 重写 `install_agent()` 的文件扫描/拷贝循环：
   - 先从完整模板扫出所有源文件（过滤 `__pycache__` / `*.pyc` / `.DS_Store`）
   - 从 `skills/harness/agent/{agent}.md` 叠加当前 agent 的说明（overlay），映射到目标 `agent/{agent}.md`
   - change 检测时对模板原文先做 `{AGENT_NAME}` / `{SKILL_DIR}` 渲染再与 target 比较，保证幂等性
4. 补齐 `skills/harness/agent/qoder.md`。

# Validation Criteria

全部 pass：

- [x] 空仓 `harness install --agent kimi` 后 `.kimi/skills/harness/` 下存在 references / scripts / assets / tests / agents 共 5 个子目录
- [x] 同一空仓连续安装 claude / codex / kimi / qoder 四个 agent，四个 `.<agent>/skills/harness/` 目录结构完全对称（按 SHA-256 内容哈希，除 `agent/<agent>.md` 外其余 88 个文件完全一致）
- [x] 重复安装同一 agent 报 "No changes detected"（幂等）
- [x] `harness install`（无 `--agent`）路径不受破坏（走同一 `install_agent`）
- [x] `__pycache__` / `*.pyc` 不进入安装产物
- [x] 不修改 `.workflow/state/runtime.yaml`，不推进 stage

详细证据见 `test-evidence.md`。

# 修复后代码入口

```python
# workflow_helpers.py
SKILL_ROOT = PACKAGE_ROOT.joinpath("assets", "skill")   # L34（未变）

def get_skill_template_root() -> Path:                   # L4356（改写）
    """Returns full skill template at assets/skill/, same as install_local_skills."""
    return Path(str(SKILL_ROOT))

def get_agent_notes_root() -> Path:                      # 新增
    return Path(__file__).resolve().parent / "skills" / "harness" / "agent"

def install_agent(root, agent):                          # L4387（改写 scanning/copy 逻辑）
    # base: full template  +  overlay: skills/harness/agent/<agent>.md
    ...
```
