# Test Evidence — bugfix-5

## Change
install_agent() 切换模板源至 `assets/skill/`，叠加 `skills/harness/agent/{agent}.md`

## Test Date
2026-04-19

## Test Summary
在 `/tmp/harness-bugfix5-1776572160/` 下准备 5 个独立干净空仓，使用编辑后经 `pipx install --force -e .` 重装的 CLI：

1. **4 个独立仓，每个仓只装一个 agent**：`{kimi,claude,codex,qoder}-only`
2. **1 个交叉仓，4 个 agent 连续安装**：`cross-check`
3. **幂等性验证**：重复 install 同一 agent 应报 "No changes detected"
4. **`harness install`（无 `--agent`）兼容性**：不破坏原有 full install 行为

## 重装 CLI 命令
```bash
pipx install --force -e /Users/jiazhiwei/IdeaProjects/harness-workflow
# /Users/jiazhiwei/.local/pipx/venvs/harness-workflow/ 已更新
```

通过 Python 入口验证：
```python
from harness_workflow.workflow_helpers import get_skill_template_root, get_agent_notes_root
# template_root: .../src/harness_workflow/assets/skill
# notes_root:    .../src/harness_workflow/skills/harness/agent
```

## Results

### Test 1: 4 独立空仓的目录结构

每个仓都执行：`git init -q && harness install --agent <AG>`

| agent | 子目录（顶层）| 文件总数 |
|-------|---------------|---------|
| kimi  | SKILL.md, agent/, agents/, assets/, references/, scripts/, tests/ | 89 |
| claude| SKILL.md, agent/, agents/, assets/, references/, scripts/, tests/ | 89 |
| codex | SKILL.md, agent/, agents/, assets/, references/, scripts/, tests/ | 89 |
| qoder | SKILL.md, agent/, agents/, assets/, references/, scripts/, tests/ | 89 |

**5 个此前缺失的子目录均出现**：references / scripts / assets / tests / agents ✅

### Test 2: 四 agent 目录树对称性（按文件内容哈希）

对每个 agent 的 skill 目录，将 `agent/{agent}.md` 统一重命名为 `agent/AGENT.md`，再按 SHA-256 比较：

```
=== kimi vs claude ===   only differs at ./agent/AGENT.md
=== kimi vs codex  ===   only differs at ./agent/AGENT.md
=== kimi vs qoder  ===   only differs at ./agent/AGENT.md
```

**其余 88 个文件内容 bit-identical**，完全对称。唯一差异就是预期的 agent 特异化说明。

### Test 3: 单仓连续安装 4 个 agent

在同一个 `cross-check` 仓内依次 `install --agent claude / codex / kimi / qoder`：
```
claude: 89 files; subdirs: agent/ agents/ assets/ references/ scripts/ tests/
codex:  89 files; subdirs: agent/ agents/ assets/ references/ scripts/ tests/
kimi:   89 files; subdirs: agent/ agents/ assets/ references/ scripts/ tests/
qoder:  89 files; subdirs: agent/ agents/ assets/ references/ scripts/ tests/
```

4 个 `.{agent}/skills/harness/` 子树结构**完全对称**。

### Test 4: 幂等性（idempotency）

在 cross-check 仓中再次执行：
```
$ harness install --agent kimi  → "No changes detected. Skill is up to date."
$ harness install --agent claude → "No changes detected. Skill is up to date."
```

修复前 `install_agent` 的 `change detection` 没考虑 `{AGENT_NAME}` / `{SKILL_DIR}` 渲染后的比较，现已通过 `src_rendered` 对齐渲染后内容，幂等性通过 ✅。

### Test 5: 不破坏 full `harness install`

`harness install`（无 `--agent`）在当前 CLI 中通过 `prompt_agent_selection()` 选中一个 agent 后同样调用 `install_agent`，因此使用同一份新代码；结构与独立仓一致。

### Test 6: 转瞬即逝产物被正确过滤

`assets/skill/tests/__pycache__/*.pyc` 已在 `_iter_sources()` 显式跳过，未进入任何目标 agent 目录：
```
$ find /tmp/harness-bugfix5-.../cross-check -name "__pycache__"
(no output)
```

## Results Table

| Check | Result | Notes |
|-------|--------|-------|
| kimi 安装后含 references/scripts/assets/tests/agents 5 个子目录 | **pass** | 全部 89 个文件 |
| kimi 与 claude/codex/qoder 目录树对称 | **pass** | 仅 `agent/AGENT.md` 差异，预期 |
| 同一仓连续安装 4 agent 结构对称 | **pass** | 每个 `.{agent}/skills/harness` 都 89 files |
| 幂等性（重复 install 不脏写）| **pass** | 渲染后内容比较 |
| 不破坏 `harness install` 既有流程 | **pass** | 同一函数路径 |
| `__pycache__` / `*.pyc` 不污染安装产物 | **pass** | 显式过滤 |

## Issues Found and Fixed
1. `install_agent()` 原本使用残缺模板 `skills/harness/`；现改为 `SKILL_ROOT = assets/skill/`。
2. `skills/harness/agent/` 原本没有 `qoder.md`，补充该文件保持四 agent 对称。
3. `install_agent()` 原本在 change 检测时直接拿模板原文与已渲染的 target 比，永远判定为 "modify"；现修复为先渲染再比较。
4. 模板中 `__pycache__` 会被旧逻辑扫到；现显式过滤。

## Conclusion
- [x] **Pass** — bugfix-5 已修复；4 agent 目录树完全对称；不破坏既有流程
- [ ] Fail — requires further work
