# Session Memory — bugfix-5

## 1. Current Goal

- bugfix-5: 修复 `harness install --agent kimi` 模板残缺（P0-06）
- 全链路：regression（诊断）→ executing（修复）→ testing（验证）

## 2. Current Status

- [x] regression 诊断完成，根因类型 B（同步代码漏拷 / 选错模板源）
- [x] executing 完成代码修复：`get_skill_template_root()` 改指向 `SKILL_ROOT = assets/skill/`，重写 `install_agent()` 模板扫描/拷贝逻辑，新增 agent 特异化叠加
- [x] executing 补齐 `skills/harness/agent/qoder.md`
- [x] testing 5 仓实测：4 agent 独立仓 + 1 个交叉仓；全部 pass；目录树对称
- [x] 文档产出：`regression/diagnosis.md`、`test-evidence.md`、`bugfix.md`、本 `session-memory.md`

## 3. Validated Approaches

### 调用链（关键代码路径）

```
CLI: harness install --agent <agent>
  → cli.py:281  _run_tool_script("harness_install.py", ["--agent", agent])
    → tools/harness_install.py:23  install_agent(root, agent)
      → workflow_helpers.py:4387  install_agent()
        → get_skill_template_root() → assets/skill/   （修复后）
        → get_agent_notes_root()    → skills/harness/agent/
        → _iter_sources()：合并 base + agent overlay
        → rglob 扫描 + 渲染 + 写入 target_path
```

### 验证命令

```bash
# 重装 CLI 以生效本地修改
pipx install --force -e /Users/jiazhiwei/IdeaProjects/harness-workflow

# 四 agent 独立仓验证
for AG in kimi claude codex qoder; do
  D=/tmp/harness-bugfix5-XXXX/$AG-only
  mkdir -p $D && cd $D && git init -q
  harness install --agent $AG
done

# 按内容哈希 diff（归一化 agent/<agent>.md 为 agent/AGENT.md）
# 结果：仅 agent/AGENT.md 内容哈希不同；其余 88 个文件完全一致
```

### 关键 grep

- `SKILL_ROOT` 常量：`workflow_helpers.py:34`
- `install_local_skills` 完整模板复制：`workflow_helpers.py:2129-2141`
- `install_agent`：`workflow_helpers.py:4387-` （修复范围）

## 4. Failed Paths

- 最初假设："kimi 特有分支" —— 实测后推翻：四个 agent 通过 `--agent` 方式都会残缺，只是 codex/claude/qoder 还有 `install_local_skills()` 兜底
- 修正后的 P0-06 根因判定："install_agent 使用错误的模板根" 而非 "kimi 同步逻辑与其他 agent 不对齐"

## 5. Candidate Lessons

```markdown
### 2026-04-19 双模板源并存 → install_agent 选错源
- Symptom: `harness install --agent <any>` 后 skill 目录残缺 5 个子目录
- Cause: 项目存在 `assets/skill/`（完整）和 `skills/harness/`（残缺入口）两套模板源；`install_local_skills` 用完整源给 codex/claude/qoder 做兜底，`install_agent` 错用残缺源
- Fix:
  1. 让 `get_skill_template_root()` 与 `SKILL_ROOT` 同源（完整模板）
  2. 将 `skills/harness/agent/{agent}.md` 以 overlay 方式叠加到 target
  3. change 检测时先渲染模板再比较以保证幂等
- 经验：**多模板源并存必有漏洞**。模板源应该只有一个真相，agent 差异化以 overlay/变量形式实现。
- 经验：**对称性是最好的回归探测器**。诊断时直接对四个 agent 做交叉验证比盯着 kimi 分析更快定位。
```

```markdown
### 2026-04-19 pipx editable 安装后需 force reinstall 才能生效
- Symptom: 修改源码后 `harness install` 仍使用旧模板根
- Cause: pipx 默认 venv 未指向可编辑源，旧版本被缓存
- Fix: `pipx install --force -e <path>` 重装
- 经验：手工改代码 + CLI 测试组合，首步必须刷 pipx/pip 的 editable 状态
```

## 6. Next Steps

- [ ] 主 agent 可在可选的 PR 审查中考虑：是否统一两个模板源（移除 `skills/harness/SKILL.md` 的冗余定义，把 agent notes 直接迁入 `assets/skill/agents/`），但这已超出 bugfix-5 范围
- [ ] 如需再在其他 agent（如 gemini / cursor）上扩展，只需在 `get_agent_skill_path()` 和 `skills/harness/agent/` 各加一处

## 7. Open Questions

- 无（均在诊断/实测中解决）
