# req-25 Completion Report

## 需求闭环摘要

- 标题：全面回归测试 harness-workflow 在新项目中的端到端可用性
- 最终状态：**PASS**（6/6 P0 闭环）
- 交付日期：2026-04-19

## 交付项

| 类别 | 交付 | 说明 |
|---|---|---|
| 修复变更（chg-01） | req-27 路径迁移收尾：`resolve_requirement_root` helper + 9 处硬编码 + `archive_base` + `harness migrate` 命令 | 修复 P0-03 / P0-04 / P0-05 + P1-06（部分） |
| 修复变更（bugfix-3） | `install_command` 在空仓库检测到 `.workflow/` 缺失时自动内联调用 `init` | 修复 P0-01 |
| 修复变更（bugfix-4） | `src/harness_workflow/assets/scaffold_v2/` 清洗：`runtime.yaml` 初始化为空值；剔除 `state/sessions/`、`flow/archive/`、`flow/suggestions/archive/`、`.DS_Store`、`__pycache__/*.pyc`；总文件数 903 → 72 | 修复 P0-02 + P1-05 |
| 修复变更（bugfix-5） | `get_skill_template_root` 指向完整 SKILL_ROOT，四个 agent 的 `skills/harness/` 目录下全部包含 SKILL.md + agent/agents/assets/references/scripts/tests 子目录 | 修复 P0-06 |

## 最终回归验证

- 测试床：`/tmp/harness-regression-final-20260419-122147/`（空 git init 仓）
- 辅助 migrate 测试床：`/tmp/harness-migrate-test-1776572833/`
- 日志归档：`regression-logs-final/`（7 子目录，共 67 个 `.log` 文件）
- 命令执行统计：TOTAL=67, PASS=52, FAIL=15（失败项全部为"期望失败 / 提示 / 缺参"或已记录的衍生副作用，无真正产品缺陷回归）
- 6 P0 闭环：**6/6 PASS**
- 详细报告见 `final-report.md`

## 验收标准对齐

| 标准 | 状态 | 证据 |
|---|---|---|
| AC1 命令覆盖完整性 | PASS | 3.1.1 命令在最终回归中均被执行并有通过/存在问题标注 |
| AC2 产出结构一致性 | PASS（带 P1） | `artifacts/main/{requirements,changes(嵌套),bugfixes,archive,regressions}/` 均已落实；`archive/main/main/` 双层 branch 记入新 P1 |
| AC3 脚本可执行性 | PASS | 所有 CLI 入口无致命错误；`language` 缺参报 rc=2 属 UX 提示 |
| AC4 Agent skill 安装正确性 | PASS | 四 agent 结构完全对称，每个 89 个文件 |
| AC5 状态机一致性 | PASS（带 P1-new-02） | runtime.yaml 正确流转；state yaml 不随 next 同步属新 P1，已记录 |
| AC6 问题清单完整性 | PASS | 每条问题含重现步骤 / 期望 / 实际 / 优先级 |
| AC7 P0 闭环 | **PASS** | 6 P0 全部在 req-25 内修完并回归验证通过 |
| AC8 P1/P2 延期说明 | PASS | 所有 P1/P2 项（含 4 条新 P1）均在 `final-report.md` 注明延期原因和建议归属窗口 |
| AC9 允许非 P0 通过 | PASS | 符合 |

## 后续跟进项

下述问题延至后续 req / bugfix 周期处理（不阻断本 req 验收）：

| ID | 描述 | 建议归属 |
|---|---|---|
| P1-new-01 | `harness rename` 未维护 state yaml 与 id 前缀 | 新 bugfix |
| P1-new-02 | `harness next` 不更新 state yaml 的 stage/status | 新 bugfix 或 req-28 |
| P1-new-03 | `harness regression "<issue>"` 产出目录含空格、无 id 前缀 | 与 P1-02 合并的 slugify 统一 bugfix |
| P1-new-04 | 归档路径出现 `archive/main/main/` 双层 branch | 新 bugfix |
| P1-01/02/03/04 | 延续旧 P1 | 见原测试报告延期说明 |
| P2-01/02/03 | 延续旧 P2 | 见原测试报告延期说明 |

## 备注

- 测试床与日志归档全部保留，便于后续 bugfix 回归对照。
- 本次验收由独立 testing subagent 执行，未修改主仓 `.workflow/state/runtime.yaml`，未推进 stage，未自行修复新发现问题（仅记录）。
