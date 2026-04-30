---
id: chg-04
title: "_pad_list 真实扫描 + _pad_interactive questionary 引导 + 端到端 dogfood + slash command 同步"
parent: req-53（新增 harness 命令给项目加规范经验工具引导式）
created_at: 2026-04-29
status: pending
depends_on: chg-03
---

## 1. 范围（Scope）

把 chg-01 的 `_pad_list` / `_pad_interactive` stub 替换为真实实现 + 端到端 dogfood + slash command 同步：

- **`_pad_list` 真实扫描**：扫 `artifacts/project/{constraints,experience/*,tools}/` 6 份 index.md（复用 `_load_project_level_index` 5 类 + 单独读 tools/index.md），按 `kind / scope` 分组打印分组列表；按 path 字母序排序；空目录显示 `(无)`。
- **`_pad_interactive` questionary 三步引导**：
  - 步骤 1：`questionary.select` 选 kind（`rule` / `experience` / `tool`）
  - 步骤 2（仅 kind=rule/experience 时）：`questionary.select` 选 scope（按 PAD_KINDS[kind] 列表）
  - 步骤 3：`questionary.text` 输入 title（必填，空回车不通过）
  - 完成后调 `_pad_add(root, kind, scope, title)`（chg-02 + chg-03 真实实现）
  - 非交互式终端（`sys.stdin.isatty() == False`）→ 报错 + 退出（与 `prompt_platform_selection` 同款 isatty 守卫）
- **端到端 dogfood pytest**：`tmpdir + harness install + 多次 pad（rule + experience + tool）+ pad list + 验证 6 类落位 + 验证 install --check 无回归`。
- **slash command 同步**：新增 `.claude/commands/harness-pad.md`（复制 `harness-suggest.md` 模板改命令名 + argument-hint），同款 hard gate + execution rules。同时同步 `.codex/skills/harness/`、`.kimi/skills/harness/`、`.qoder/skills/harness/` 下的 commands 目录（与 `harness-suggest` 同款分发，由 `install_local_skills` 统一负责）。
- **WORKFLOW.md 不动**（OQ-Verdicts 决策：pad 是辅助命令，不进 Main Entry）；README 加一段说明。

## 2. 目标（Goal）

- G-01：`harness pad list` 输出三段（rule / experience / tool）+ 各段按 scope 分组（rule 5 段 / experience 5 段 / tool 单段）+ 空段显示 `(无)`。
- G-02：`harness pad`（无参数 TTY 模式）触发 questionary，三步答完后落地 + index 登记 + git stage 与 chg-02/03 完全一致。
- G-03：非 TTY 跑裸 `pad` → exit ≠ 0 + stderr 含 "interactive 模式需要交互式终端"。
- G-04：tmpdir 端到端 dogfood：install + 跑 5 条 pad（覆盖 rule × 2 不同 scope + experience × 2 不同 scope + tool × 1）→ 全部落位 / 全部 index 登记 / git diff --cached 含 5 条内容文件 + 6 条 index.md（如有变化）。
- G-05：`.claude/commands/harness-pad.md` 含 hard gate 模板 + argument-hint 形如 `<kind> [<scope>] <title>|list`。

## 3. 验收（AC，对齐 requirement.md）

- AC-06（list 子命令）：分组列表按 kind / scope 打印，覆盖 6 份 index.md。
- AC-08（interactive 模式）：三步答完后行为与位置参数一致（落位 + index + git stage）。
- AC-07（fresh repo dogfood）：tmpdir + install + 多 pad → 端到端验证。
- AC-10（PetMallPlatform 真实仓自验）部分：本 chg 通过 `tests/test_req53_pad_dogfood.py` 模拟该场景；真实仓验证由 user 在 acceptance 阶段手工验。

## 4. 依赖

- 前置：chg-03（_pad_add 已含真实落位 + 索引登记 + git stage + stderr 活证）
- 后置：req-53 完成，进 testing。

## 5. 范围红线

- 不动 WORKFLOW.md（OQ-Verdicts 已定）
- 不引入新 questionary 依赖（已是 harness-workflow 现有 dep）
- 不动 `install_local_skills` 主流程（仅 `.claude/commands/harness-pad.md` 静态文件 + 同款分发模板）
- README 增量段不超过 30 行
- 不动 PetMallPlatform / PetMallAdmin / uav 仓
