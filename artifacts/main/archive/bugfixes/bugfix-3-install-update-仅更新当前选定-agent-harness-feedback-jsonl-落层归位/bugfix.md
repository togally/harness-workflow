---
id: bugfix-3
title: install/update 仅更新当前选定 agent + .harness/feedback.jsonl 落层归位
created_at: 2026-04-20
---

# Problem Description

## 问题 1 — install/update 跨 agent 全量刷新
- 现象：用户执行 `harness install --agent claude` 后，下一次 `harness install` / `harness update` 仍然刷新 `.codex/` / `.qoder/` / `.kimi/` 所有平台目录；用户预期只刷新当前选定的 `.claude/` 相关文件。
- 影响范围：所有 install/update 使用方；PetMallPlatform 实测 `.codex/skills/harness/`、`.qoder/skills/harness/`、`.kimi/skills/harness/` 全部齐全，无法按单 agent 聚焦。

## 问题 2 — `.harness/feedback.jsonl` 落位错误
- 现象：`FEEDBACK_DIR = Path(".harness")` 常量在六层架构成型前先行落地，导致 feedback.jsonl 游离于 `.workflow/` 之外；主仓已跟踪 182 行、PetMall 已跟踪 28 行真实审计数据。
- 影响范围：所有仓库根目录多出 `.harness/` 脏路径；与"一切运行时状态归四层 state"的架构约束冲突；下游 `harness feedback` CLI 直接从 `.harness/feedback.jsonl` 读取，路径错配需要同步迁移。

# Root Cause Analysis

## 问题 1 根因（引用 `regression/diagnosis.md` §1.4）
- `install_agent` 已按 agent 收敛，但作用域信号（"当前用哪一个 agent"）没有被持久化到任何状态字段。
- `update_repo`（`workflow_helpers.py:2869-2912`）与 `_managed_file_contents`（`workflow_helpers.py:2120-2139`）的写入范围分别由"硬编码 `refreshed .codex/...`"和"`COMMAND_DEFINITIONS × 4 agent 全量字典"决定，二者都不感知用户实际操作的 agent。
- `_project_skill_targets`（`workflow_helpers.py:1989-2002`）依赖 `platforms.yaml.enabled[]` 多选集合，本身就表达不了"单选激活 agent"。

## 问题 2 根因（引用 `regression/diagnosis.md` §2.6）
- `FEEDBACK_DIR = Path(".harness")` 常量（`workflow_helpers.py:136-137`）早于六层架构成型，从未被纳入"工作流数据 = `.workflow/`"的统一归位规则。
- `harness_export_feedback.py:20` 直接硬编码 `root / ".harness" / "feedback.jsonl"`，和常量耦合死。
- scaffold_v2 对人/对 agent 的文档（`harness-manager.md:537` / `harness-export-feedback.md:8`）继承旧路径。
- 5 个 `record_feedback_event` 调用点全部通过常量写入（workflow_helpers.py:2294-2307），只要改常量即可覆盖。

# Fix Scope

## 将改（白名单）
- `src/harness_workflow/workflow_helpers.py`
  - 常量：`FEEDBACK_DIR` / `FEEDBACK_LOG` 指向 `.workflow/state/feedback/feedback.jsonl`
  - 新增 helper：`read_active_agent(root)` / `write_active_agent(root, agent)`
  - `_project_skill_targets`：优先读 `active_agent`，缺省回退 `enabled[]`
  - `_managed_file_contents`：接收 `active_agent` 参数，只为该 agent 写 `.{agent}/commands/*` + `.{agent}/skills/*`
  - `install_agent`：末尾调用 `write_active_agent(root, agent)`
  - `update_repo`：读 `active_agent` 并传给 `install_local_skills` / `_sync_requirement_workflow_managed_files`；一次性迁移 `.harness/feedback.jsonl` → `.workflow/state/feedback/feedback.jsonl`；签名加 `force_all_platforms=False`；硬编码 `refreshed` 打印改为按实际写入路径动态输出；缺 `active_agent` 时一行 warning 走兼容模式
  - `install_local_skills`：接收 `active_agent`（可选），优先单 agent，回退 `_project_skill_targets` 旧行为
- `src/harness_workflow/tools/harness_update.py`
  - CLI 新增 `--agent X`（一次性覆盖）+ `--all-platforms`（escape hatch）
  - 将参数传入 `update_repo`
- `src/harness_workflow/tools/harness_export_feedback.py`
  - `log_path = root / ".workflow" / "state" / "feedback" / "feedback.jsonl"`
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md:537` 文案同步
- `src/harness_workflow/assets/scaffold_v2/.workflow/tools/catalog/harness-export-feedback.md:8` 文案同步
- `tests/test_active_agent_and_feedback_relocation.py`（新增，3 条红用例）

## 不改（边界）
- PetMallPlatform（用户仓库）— 仅供手动烟测临时副本
- `tests/test_workflow_helpers_update_idempotent.py`（已有红/绿）
- scaffold_v2 模板层（除上面两处文档引用）
- `.gitignore`（主仓 `.harness/feedback.jsonl` 迁移后留下空目录自动清理即可；不新增 `.harness/` 屏蔽规则，以免遮蔽未来同名脏路径排查）

# Fix Plan

1. **TDD 红色阶段**：新建 `tests/test_active_agent_and_feedback_relocation.py`，按场景写 3 条红用例：
   - `test_install_agent_persists_active_agent`：验证 install_agent 写入 `active_agent` 字段，且二次调用可覆盖。
   - `test_update_repo_only_refreshes_active_agent`：`platforms.yaml` 设 `active_agent=cc` + `enabled=[codex,qoder,cc,kimi]` 后 `update_repo` 只刷新 `.claude/`；开启 `force_all_platforms=True` 时四个平台全刷新。
   - `test_feedback_jsonl_writes_under_state_feedback`：覆盖 3a 新仓写新位置不建 `.harness/`、3b 旧仓 `update_repo` 迁移、3c `harness_export_feedback` 从新位置读。
   安全带：先运行 3 条用例确认 FAIL 在预期（字段缺失 / 文件位置错 / 跨 agent 刷新）。
2. **状态层 helper**：在 `workflow_helpers.py` 适当位置新增 `read_active_agent(root)` / `write_active_agent(root, agent)`，基于 `read_platforms_config` / yaml 直接读写 `platforms.yaml.active_agent` 字段。不影响现有 `enabled`/`disabled` 字段。
3. **install_agent 持久化**：在 `install_agent` 返回 `0` 之前追加 `write_active_agent(root, agent)`。二次调用覆盖旧值。
4. **update_repo 一次性数据迁移**：`update_repo` 开头加 `shutil.move` 老 `.harness/feedback.jsonl` 到 `.workflow/state/feedback/feedback.jsonl`（仅新位置不存在时）；迁移后若 `.harness/` 空目录则 `rmdir`；动作追加到 `actions` 列表。
5. **常量改造 + export CLI**：`FEEDBACK_DIR` / `FEEDBACK_LOG` 指向 `.workflow/state/feedback/`；`record_feedback_event` 无需改代码（走常量）；`harness_export_feedback.py:20` 路径同步。
6. **_project_skill_targets active_agent 化**：读 `active_agent` 时只返回对应 agent 路径；未设定时 warning + 回退 `enabled[]`（保留现有行为兼容旧仓）。
7. **_managed_file_contents active_agent 参数化**：接收 `active_agent`，按映射（`cc→.claude`、`codex→.codex`、`qoder→.qoder`、`kimi→.kimi`）只写当前 agent 的 commands/skills；`active_agent=None` 时回退旧的全量写入（兼容模式）。
8. **install_local_skills active_agent 化**：新增可选 `active_agent` 参数，优先走单 agent 目标；`update_repo` 按 `active_agent` 调用。
9. **update_repo 新签名 + CLI**：`update_repo(root, check=False, force_managed=False, force_all_platforms=False, agent_override=None)`；`harness_update.py` 新增 `--all-platforms` / `--agent X`；缺 `active_agent` 时打印 `active agent not set; refreshing enabled set (compat mode)`。硬编码 `refreshed` 打印改为遍历实际写入路径。
10. **scaffold_v2 文档同步**：`harness-manager.md:537` / `harness-export-feedback.md:8` 路径文案更新到 `.workflow/state/feedback/feedback.jsonl`。
11. **绿化验证**：跑 3 条新红用例应全 PASS；全量 pytest 应零新增回归（pre-existing `test_smoke_req29` failure 可容忍）；手动烟测 `/tmp/petmall-bugfix3-new-smoke/` 副本验证 install/update + 迁移效果。

# Validation Criteria

1. `PYTHONPATH=src python3 -m pytest tests/test_active_agent_and_feedback_relocation.py -v` → 3 passed（`test_install_agent_persists_active_agent` / `test_update_repo_only_refreshes_active_agent` / `test_feedback_jsonl_writes_under_state_feedback`）。
2. `PYTHONPATH=src python3 -m pytest -q --no-header` 全量 → 零新增回归（容忍 pre-existing `test_smoke_req29::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`）。
3. 手动烟测：`/tmp/petmall-bugfix3-new-smoke/` 副本上 `harness install --agent cc` 后 `.workflow/state/platforms.yaml` 出现 `active_agent: cc`，`.harness/feedback.jsonl` 已迁到 `.workflow/state/feedback/feedback.jsonl` 且原目录被清理；第二次 `harness update` 不触碰 `.codex/` / `.qoder/` / `.kimi/`（stat mtime 对比）。
4. `harness update --all-platforms` escape hatch 可恢复旧行为（全平台刷新），用于迁移期兜底。
5. `harness feedback` CLI（`harness_export_feedback.py`）从新路径正确读取历史事件；迁移后事件 `.workflow/state/feedback/feedback.jsonl` 累计条数 ≥ 迁移前 + 本次 update 产生的新事件数。
