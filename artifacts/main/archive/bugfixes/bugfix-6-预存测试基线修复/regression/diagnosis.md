# Regression Diagnosis

## Issue

预存测试基线：`python3 -m unittest discover tests` 出现 3 failures + 3 errors（其余 44 pass / 36 skipped，共 86 条），均为 req-26 之前就已存在的历史遗留，非本次需求引入。本 bugfix 旨在定位每条失败的根因并给出统一修复路线。

## 测试基线（2026-04-19 实测）

| 类型 | 测试 | 失败要点 |
| --- | --- | --- |
| FAIL | `test_cli.test_install_writes_three_platform_hard_gate_entrypoints` | `CLAUDE.md` 中缺少英文串 `stop immediately`（模板已全面中文化为"立即停止"） |
| FAIL | `test_cli.test_installed_skill_uses_global_harness_commands` | `.codex/skills/harness/SKILL.md` 不再出现 `harness requirement` 字样（实际文案已改为"harness …"或 `harness active`） |
| FAIL | `test_cli.test_bugfix_creates_workspace_and_enters_regression` | 断言 `.workflow/flow/bugfixes/<dir>/bugfix.md` 存在；但 `create_bugfix` 早已把制品写到 `artifacts/{branch}/bugfixes/<dir>/`（req-26 路径同构改造） |
| ERROR | `test_cli.test_update_check_and_apply_refresh_qoder_skill_and_rule` | `install` 后 `.qoder/skills/harness/SKILL.md` 不存在即 `unlink` 失败；install 根据 `platforms-config.yaml#enabled` 选择性落盘，默认未启用 qoder |
| ERROR | `test_cli.test_update_check_and_apply_refresh_skills_and_missing_files` | 同上，`.claude/skills/harness/SKILL.md` 在默认 enabled 列表外，测试假设 install 无条件三平台并存 |
| ERROR | `test_cycle_detection` (整文件 loader 失败) | `from harness_workflow.core import ...` 导入失败：`harness_workflow.core` 模块根本不存在；实际实现在 `harness_workflow.tools.harness_cycle_detector`，测试文件未跟进重命名 |

## Root Cause Analysis

按共同根因归类，三条线：

### R1 — 模板漂移（CLAUDE.md / SKILL.md 文案迭代后测试未跟上）

- 涉及：FAIL#1、FAIL#2。
- 现状：`install` 命令在 `.codex/skills/harness/SKILL.md`、`CLAUDE.md` 等入口文件写的是当前业务文案（中文 Hard Gate、Harness workflow 薄包装、`harness active` 示例）；测试断言的"stop immediately"、"harness requirement"原文案在多轮模板迭代中已被替换。
- 结论：**测试漂移**。生产行为正确，断言内容过时。
- 影响面：仅测试；线上 install 流程、生成的入口文件 Hard Gate 语义完整（中文版），用户使用不受影响。

### R2 — 路径迁移漂移（bugfix 制品目录从 `.workflow/flow/` 搬到 `artifacts/{branch}/`）

- 涉及：FAIL#3。
- 现状：`workflow_helpers.create_bugfix` 已落到 `artifacts/{branch}/bugfixes/<dir>/`；测试仍断言旧路径 `.workflow/flow/bugfixes/...`。这是 req-26「路径同构」改造的历史债，与 req-27 迁移同源。
- 结论：**测试漂移**。
- 影响面：仅测试；生产 bugfix 创建行为正确，本仓库当前 bugfix-6 等目录即位于新路径 `artifacts/main/bugfixes/`，与代码一致。

### R3 — 模块缺失 / 平台默认开关漂移

- 涉及：ERROR#1、ERROR#2、ERROR#3。
- ERROR#3：`tests/test_cycle_detection.py` 顶部 `from harness_workflow.core import ...` 在 `src/harness_workflow/` 下找不到 `core` 包；等价功能位于 `harness_workflow.tools.harness_cycle_detector`（含 `CallChainNode`、`CycleDetector`、`detect_subagent_cycle` 等符号的可能实现点）。**测试漂移（模块路径没跟上重构）**。
- ERROR#1、ERROR#2：`install_local_skills` 按 `platforms-config.yaml#enabled` 选择性创建 `.codex` / `.claude` / `.qoder` 下的 `skills/harness/SKILL.md`；默认仅 codex 启用，故在新建临时仓里写入不存在的 `.qoder/skills/harness/SKILL.md` 时 `FileNotFoundError`。测试假设 install 后三平台无条件就绪。**测试漂移（需要显式 enable 或改测试准备步骤）**；也可以视作"默认平台开关口径变更"未同步到测试。
- 影响面：仅测试；update/cycle_detection 生产命令本身可用（update 另有 e2e 测试 `test_update_does_not_restore_legacy_runtime_entrypoint` 通过；cycle detector 通过 tools 子包调用）。

## 判定

6 条失败，0 条真 bug，6 条全部判为 **测试漂移**（含 1 条源码级别的模块引用漂移）。

| 编号 | 类型 | 判定 | 处理建议 |
| --- | --- | --- | --- |
| FAIL#1 | 模板文案 | 测试漂移 | 修改测试断言：把 `stop immediately` 改为匹配当前中/英双模板的关键短语（例如 "立即停止" 与 "stop immediately" 任一命中即通过） |
| FAIL#2 | 模板文案 | 测试漂移 | 修改测试断言：改为断言 SKILL.md 中存在 `harness ` 命令族关键词（如 `.workflow/state/runtime.yaml` + `harness` 短语）或更新为实际出现字段 |
| FAIL#3 | 路径迁移 | 测试漂移 | 修改测试：断言 `artifacts/{branch}/bugfixes/<dir>/bugfix.md` 存在；同步其余 state_file、runtime 字段断言口径 |
| ERROR#1 | 平台开关 | 测试漂移 | 在测试 setUp 中启用 qoder / 显式写 platforms-config.yaml；或改断言只针对实际 enabled 平台 |
| ERROR#2 | 平台开关 | 测试漂移 | 同上，覆盖 cc 平台 |
| ERROR#3 | 模块缺失 | 测试漂移（源引用） | 改 import：`from harness_workflow.tools.harness_cycle_detector import ...`；若符号不完全匹配，补齐或 skip 整文件（看 bugfix-6 executing 决策） |

## Routing Direction

- [x] **Real issue**：测试基线确有 3 fail + 3 error，影响"红即真问题"的信号质量；需要在 bugfix-6 范围内统一修复。
- [ ] False positive
- 推进方向：`harness regression --confirm` → 进入 bugfix-6 的 planning/executing，按 R1/R2/R3 三类分组修测试断言与测试 import。
- 范围结论：**全部在 bugfix-6 范围内可吞**。不需要转 change / 新需求：所有改动限于 `tests/test_cli.py`、`tests/test_cycle_detection.py`，不触及生产代码。

## Required Inputs

- 无需人工输入；见同目录 `required-inputs.md`（所有项均为 no）。
