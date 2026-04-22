# Requirement

## 1. Title

harness CLI 闭环修复 + 对人文档 SOP 收束（批量建议合集 7 条）

## 2. Goal

- **优先级 1（必做，硬阻塞）**：修复 harness CLI 在 bugfix / archive / suggest 三条链路上的闭环 bug，让 `harness bugfix → harness next → harness archive → harness suggest` 可以真正打通（档 1，sug-12/13/14/15）。
- **优先级 2（必做但非硬阻塞）**：补齐对人文档的"真实落盘验证"、下游仓库 `harness change` 模板刷新策略、以及首次完整的对人文档产出链示范（档 2，sug-09/10/11）。

## 3. Scope

### 3.1 Included

**档 1 — CLI 闭环 bug 修复（4 条，必做，硬阻塞）**

- **sug-12** 修复 `harness bugfix "<t>"` 不写 `operation_type` / `operation_target` 到 `runtime.yaml` 的问题；保证字段在 save/load 与 `harness next` / `harness status` 周期中持久化，让 regression 流程能正常推动。
- **sug-13** 恢复 `harness_workflow` 模块的 cycle-detection 6 个符号（`CallChainNode` / `CycleDetector` / `CycleDetectionResult` / `detect_subagent_cycle` / `report_cycle_detection` / `get_cycle_detector` / `reset_cycle_detector`）到生产侧，让 `tests/test_cycle_detection.py` 从 smoke 恢复为完整用例。
- **sug-14** 让 `harness archive` 支持 bugfix：`list_done_requirements` / `archive_requirement` 需扫描并支持 `bugfixes/` 目录；归档落到 `artifacts/{branch}/archive/bugfixes/<dir>`，并清理 `active_requirements`。
- **sug-15** 修复 `harness suggest --delete` / `--apply` 对无 frontmatter 的 sug 文件永远失败的 bug（补齐 filename fallback）；并在 done.md / stage-role.md 中硬门禁 done 阶段 subagent 写 sug 必带 frontmatter。

**档 2 — SOP / 文档补齐（3 条，必做但非硬阻塞）**

- **sug-09** 为对人文档"agent 运行时真实落盘"提供可跑的验证方式（CLI / smoke test / checklist 择一，或组合）。
- **sug-10** 输出"下游已安装仓库如何刷新 `harness change` 模板"的策略指南（`.workflow/constraints/` 或 `docs/` 下），若可行再在 `harness update` 上加针对性开关。
- **sug-11** 本 req-28 自身作为对人文档产出链的首次完整示范，6 份对人文档全部真实产出。

### 3.2 Excluded

- **不做** sug-08（bugfix-6 已消费未清理 sug 池）的回溯——已在现场 `rm` 解决。
- **不动** 本需求之外已归档的 req-26 / bugfix-6 产物。
- **不做** 下游仓库批量 `harness update` 的真实远程推送——sug-10 只负责产出策略文档和（可选的）CLI 开关。
- **不做** 对 bugfix-3/4/5/6 的主动归档 sweep（可作为 sug-14 的回填可选项，但不纳入硬验收）。

## 4. Acceptance Criteria

### 档 1（必做，硬阻塞）

- **AC-12（sug-12，必做）**
  - `harness bugfix "<title>"` 执行后，`.workflow/state/runtime.yaml` 中必出现 `operation_type: "bugfix"` + `operation_target: "<bugfix-id>"`。
  - 经任意一次 `harness next` 或 `harness status` 后字段仍保留，不被覆盖或丢失。
  - 原 AC-03（state yaml 同步）对 bugfix 同样生效：stage 随推进同步写入 bugfix 的 yaml。

- **AC-13（sug-13，必做）**
  - `harness_workflow` 模块对外导出 6 个 cycle-detection 符号（`CallChainNode` / `CycleDetector` / `CycleDetectionResult` / `detect_subagent_cycle` / `report_cycle_detection` / `get_cycle_detector` / `reset_cycle_detector`），基本语义正确。
  - `tests/test_cycle_detection.py` 从 smoke 恢复为完整用例（可从 git 历史 `5584656^` 或 diagnosis.md 取回），测试全部通过。

- **AC-14（sug-14，必做）**
  - `harness archive bugfix-N` 成功：产出落到 `artifacts/{branch}/archive/bugfixes/<dir>`，`active_requirements` 中对应条目被清理干净。
  - `list_done_requirements` / `archive_requirement` 支持 `bugfixes/` 目录，同时保持对 `requirements/` 的兼容。
  - **在本需求交付范围内，一次性 sweep 归档现存 active 的 bugfix-3 / bugfix-4 / bugfix-5 / bugfix-6**，执行后 `.workflow/state/runtime.yaml` 的 `active_requirements` 不再包含这 4 个 bugfix，归档产物落在 `artifacts/main/archive/bugfixes/` 下。此为硬 AC。

- **AC-15（sug-15，必做）**
  - `harness suggest --delete sug-XX` / `--apply sug-XX` 对无 frontmatter 的 sug 文件也能成功（以 filename 为 fallback 匹配 sug-id）。
  - done 阶段新产 sug 必带 frontmatter：在 `done.md` + `stage-role.md` 明确硬门禁，新增 sug 不含 frontmatter 时拒绝写入或报错退出。
  - **扩展覆盖 `create_suggestion` 编号 bug**：当前实现只扫 `.workflow/flow/suggestions/` 当前目录决定下一个编号，不考虑 `.workflow/flow/suggestions/archive/` 下已归档的历史 sug，会导致编号从已用过的值重新开始（例如池清空后下一条又叫 `sug-01`，与历史归档冲突）。修复后 `create_suggestion` 需跨当前目录与 archive 子目录计算最大编号并 +1，保证单调递增。

### 档 2（必做但非硬阻塞）

- **AC-09（sug-09，必做但非硬阻塞）**
  - 提供一个可跑的校验方式，断言 req / bugfix 周期中每个 stage 的对人文档都真实落盘到 `artifacts/{branch}/...`。
  - 形式任选其一或组合：CLI 命令（如 `harness validate --human-docs`）、独立 smoke test、acceptance 角色 SOP 内嵌 checklist。
  - 校验失败时能明确指出缺失的文件路径。

- **AC-10（对应 sug-10，下游模板刷新）**
  - 背景：`harness change` 模板由已安装的 `harness_workflow` Python 包动态读取（`render_template` 从包内 `TEMPLATE_ROOT` 读），不会 copy 到下游仓库。
  - 下游用户升级 Python 包（`pip install -U harness-workflow` 或等价）即自动使用最新模板；老的 change 落盘文件是一次性快照，保持不动。
  - 本 AC 交付：在 `README.md` 或 `docs/` 下补 1~3 行提示，明确"如需刷新 harness change / plan 模板，升级 `harness_workflow` Python 包即可，无需额外 harness CLI 子命令"。不改 CLI。
  - 优先级：**非硬阻塞**（5 分钟文档小改）。

- **AC-11（sug-11，必做但非硬阻塞）**
  - req-28 自身就是对人文档产出链的首次完整示范——在推进全过程中，以下 6 份对人文档全部真实产出：
    - `需求摘要.md`（req 级）
    - `变更简报.md`（change 级，每个 change 一份）
    - `实施说明.md`（change 级，每个 change 一份）
    - `测试结论.md`（req 级）
    - `验收摘要.md`（req 级）
    - `交付总结.md`（req 级）
  - 验证由 AC-09 的 checklist 反向覆盖（即 AC-09 的校验对 req-28 执行应全部通过）。

## 5. Split Rules

- 档 1 与档 2 建议拆分为不同 change：
  - 档 1 聚焦代码 / 测试层的 CLI 闭环修复，交付形态偏"bugfix 合集"。
  - 档 2 聚焦 SOP / 文档 / 验证脚本层，交付形态偏"规范与工具补齐"。
- 档 1 内部可再按"state 持久化（sug-12）"、"cycle-detection 符号恢复（sug-13）"、"archive 扩展 bugfix（sug-14）"、"suggest frontmatter fallback + 门禁（sug-15）"拆为 4 个 change，或按依赖关系合并为 2 个。
- 档 2 内部可按"落盘验证机制（sug-09）"、"下游刷新策略（sug-10）"、"本 req 自身作为示范（sug-11，主要是跟随推进而非独立 change）"拆分。
- 每个 change 独立可交付、可测试。
- 需求完成时填写 `completion.md` 并记录项目启动验证成功。

## 6. 依赖关系

- sug-12 / sug-14 / sug-15 **全部作为 req-28 下的 change 交付，不另开 bugfix-7**。
  技术原因：开独立 bugfix-7 会立刻踩 sug-12（`operation_type` 缺失 → `harness next` 从 regression 推不动），bugfix-7 的全链路本身就依赖 sug-12 已修好，形成鸡生蛋。
  反之在 req-28 下作为 change 修，走的是标准 requirement 流程（不经过 bugfix 的 regression stage），不会踩 sug-12 的坑。
- 档 1 的 sug-13 涉及生产代码符号恢复 + 测试恢复，与 sug-12/14/15 互相独立，可并行。
- 档 2 的 sug-09 在 AC-11 中被复用来做自我验证，建议 sug-09 优先于 sug-11 完成，或至少在 sug-11 验证阶段已可用。
- 档 2 的 sug-10 与档 1 / 其他档 2 无强依赖，可独立并行。

## 合并建议清单

- sug-09-ac06-agent-runtime-verification: # Suggestion: 补充 AC-06 对人文档"agent 运行时真实落盘"验证
- sug-10-downstream-repo-change-template-refresh: # Suggestion: 下游已安装仓库的 `harness change` 模板刷新策略
- sug-11-next-req-first-full-human-doc-demo: # Suggestion: 下一个需求作为对人文档产出链的首次完整示范
- sug-12: ## 现象
- sug-13: ## 现象
- sug-14: ## 现象
- sug-15: ## 现象
