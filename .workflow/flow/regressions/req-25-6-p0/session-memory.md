# Session Memory — req-25-6-p0 regression

## 1. Current Goal

- 独立核查 executing subagent 提交的 6 项 P0，判断真伪、定位根因、给出路由与分组建议
- 禁止修改业务代码、禁止改 runtime.yaml、禁止推进 stage

## 2. Current Status

- [x] 角色文件加载完毕（base-role → stage-role → regression → evaluation/regression）
- [x] 测试报告 `test-report.md` 已读完
- [x] 6 项 P0 的源码根因核查完毕
- [x] `analysis.md` 产出
- [x] `decision.md` 产出
- [x] `session-memory.md` 产出（本文件）

## 3. Validated Approaches

### 调用链
- Level 0: 主 agent → regression stage
- Level 1: regression subagent（本 agent）→ 独立诊断

### 关键发现摘要

**6 项结论：全部 confirm，0 项 reject**

| ID | 根因文件:行 | 修复路由 |
|---|---|---|
| P0-01 | `workflow_helpers.py:2137-2142 + 4173` | bugfix |
| P0-02 | `src/harness_workflow/assets/scaffold_v2/` 数据污染 | bugfix |
| P0-03 | `workflow_helpers.py:3897` | change（合并） |
| P0-04 | `workflow_helpers.py:3782, 3830` | change（合并） |
| P0-05 | `workflow_helpers.py:3530, 3562` | change（合并） |
| P0-06 | `workflow_helpers.py:33, 1962-1975, 4147-4149, 4184-4229` | bugfix |

**分组结论**：4 组 = 1 个 change（A 组，合并 P0-03/04/05）+ 3 个 bugfix（B/C/D 对应 P0-01/02/06）。

**共同祖先**：P0-03/04/05 共享 req-27 路径重构未收口的根因。`workflow_helpers.py` 中至少 9 处 `.workflow/flow/requirements` 硬编码，而 `create_requirement:3174` 已写新路径 `artifacts/{branch}/requirements` — 读写端不一致。

**衍生隐患**（随修复一并处理）：
1. `install_agent` 的 changes 打印与真实行为不一致（[delete]/[modify] 只报不做）→ 随 P0-06 修
2. scaffold_v2 内有 `flow/requirements/req-25-harness 完全由 harness-manager 角色托管/done-report.md` 含主仓自身进度 → 随 P0-02 清洗

## 4. Failed Paths

- 无（路径硬编码式 bug 核查路径笔直，不存在失败分支）

## 5. Candidate Lessons

```markdown
### 2026-04-19 路径重构必须读写成对迁移
- Symptom: req-27 之后多个命令在新仓完全不可用
- Cause: 重构 create_* 写入路径但未同步迁移 rename/archive/validate 的读取路径
- Fix: 任何路径重构在 PR 前应 grep 所有硬编码的旧路径，抽公共 helper 统一解析；添加 lint 规则禁止直接使用 `.workflow/flow/requirements`
```

```markdown
### 2026-04-19 scaffold 模板必须走 "清洗 + 冻结" 流程
- Symptom: 新仓 init 后继承老项目 10 个 sessions、4 个 archive 版本、7 个 suggestions 及 runtime.yaml 假状态
- Cause: scaffold_v2 是主仓 .workflow/ 历史快照的未清洗拷贝
- Fix: scaffold 打包时必须有显式白名单（只保留"模板级"文件），runtime.yaml 必须是初始空白态；加 CI 检查禁止 scaffold 里出现 req-*、sug-*、archive/
```

```markdown
### 2026-04-19 install/changes 声明与执行必须一致
- Symptom: install_agent 打印 [delete] 列表但 copy loop 并不执行 delete，导致 codex/claude/qoder 因残留文件"看起来正确"
- Cause: 在 4206-4213 扫描计算 changes，然后 4219-4229 仅调 shutil.copy，未处理 delete/modify 的真实动作
- Fix: install 流程应显式两步（dry-run diff → apply），或 changes 循环里严格执行每个动作，avoid "报告/动作" 分叉
```

## 6. Next Steps

给主 agent 的建议命令序列（由主 agent 决策是否执行）：

```
# 1. 合并 P0-03/04/05 为一个 change
harness change "完成 requirement 路径迁移到 artifacts/{branch}"

# 2. 开三个独立 bugfix
harness bugfix "install 在空仓自动 init"
harness bugfix "scaffold 清洗 harness-workflow 历史数据"
harness bugfix "install --agent 模板一致性"
```

执行顺序建议：change（A）→ bugfix（B）→ bugfix（C）→ bugfix（D）。
A 完成后 archive/validate/rename 同时复活，是最大 ROI。
C 会改 scaffold_v2，修完应重跑 req-25 测试床验证。

## 7. Open Questions

- A 组 change 是否要顺手重构 `archive_base` 目标目录（目前 `.workflow/flow/archive`，req-27 意图是 `artifacts/{branch}/archive`）？ → 留给架构师在 change 的 plan 阶段决定；诊断师倾向于"一起改"以避免 req-27 再留尾巴
- P1-06（artifacts 结构与 Scope 3.1.2 文档不一致）是否随 A 组 change 一并对齐文档？ → 诊断师建议由架构师在 A 的 plan 中评估，若工作量小则合入

## 8. 上下文消耗评估

- 读取文件：~15 个（源码 5、日志 4、role/context 文档 6）
- 工具调用：~30 次（Read/Grep/Bash/Edit）
- 预估上下文占比：30%-40%（well below 70% threshold）
- 无需 `/compact` 或 `/clear`

