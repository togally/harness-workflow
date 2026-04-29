---
id: bugfix-1
title: harness update --check 等 flag 被角色触发吞了，drift check 无路可走
created_at: 2026-04-23
---

# Bugfix: bugfix-1（harness update --check 等 flag 被角色触发吞了，drift check 无路可走）

## 1. 问题报告

用户（agent）在会话中跑 `harness update --check`，期望 CLI 显示 managed 文件 drift 预览（等价历史 `update_repo --check` 输出 "Update summary … No files were changed."）。实际：

```
$ harness update --check
harness update 已重定义为角色契约触发。
请在 Claude Code / Codex 会话中说 '生成项目现状报告' 召唤 project-reporter。
CLI 同步职责已迁到 `harness install`。
```

CLI 把 `--check` / `--scan` / `--force-managed` / `--all-platforms` / `--agent` **全部**吞了，drift check 在 CLI 层无入口。

## 2. 复现步骤

```bash
cd <repo-with-harness-installed>
# 预期：输出 drift 预览（Update summary + No files were changed）
# 实际：输出三行引导 + rc=0
python -m harness_workflow update --check
# 或
harness update --check
```

附加复现：

```bash
# 承诺替代路径"harness install"也无 --check / --force-managed flag（argparse 直接报错）
harness install --check                 # argparse: unrecognized arguments
harness install --force-managed         # argparse: unrecognized arguments
harness install --all-platforms         # argparse: unrecognized arguments
```

## 3. 根因

### 代码层
`src/harness_workflow/cli.py` L400-L409 `if args.command == "update":` handler 被 req-33（install 吸收 update 的 CLI 职责 + harness update 契约层重定义为触发 project-reporter）/ chg-02（harness update 角色契约层重定义为召唤 project-reporter） S-B4 severed 为"忽略所有 flag 统一打印引导 + return 0"；update_parser L172-L189 仍注册 5 个 flag 不报错，但 handler 不读 `args.check` / `args.scan` / `args.force_managed` / `args.all_platforms` / `args.agent`，也不 delegate。

同时：`install_parser`（L160-L163）**只注册** `--root` / `--force-skill` / `--agent`，**未**扩展 `--check` / `--force-managed` / `--scan` / `--all-platforms`。install handler（L385-L392）只调 `_run_tool_script("harness_install.py", ["--agent", agent], root)`，`harness_install.py` 又只接 `--agent`（single-agent install），不走 `install_repo(check=True, ...)` 链。

结果：Python API 层（`install_repo` L3095-L3230 支持 `check` / `force_managed` / `force_all_platforms` / `agent_override` / `force_skill`）完整；CLI 层**两个 subcommand 都没暴露 drift / scan / force-managed 入口**。

### 契约层
req-33 / chg-02 `change.md` L11 / L23 / L31 / L37-L38 / L50 / L95 明确选 P-B2（保留 flag 不报错，handler 忽略，兼容 CI argparse 解析），harness-manager.md §A.4（L421-L423）/ §A.5（L425-L427）告诉用户"请改用 `harness install`"或"直接在会话中触发 project-reporter"。**盲区**：chg-02 聚焦"切断 update CLI 刷新职责"，未审视"install CLI 是否吸收了对等 flag"；chg-01 聚焦 helper 层 `install_repo` / `update_repo` 合并，未审视 CLI parser 扩展。→ 承诺的"迁到 `harness install`"**CLI 端从未落地**。

## 4. 修复方案（候选）

### 方案 A（推荐·最小改动）：update CLI 按 flag 分叉 — 有 flag 透传 install_repo，裸命令才打印引导

- `cli.py` L400-L409 handler 改为：检测 `args.check` / `args.scan` / `args.force_managed` / `args.all_platforms` / `args.agent` 任意一个非默认值 → 调 `install_repo(root, force_skill=True, check=args.check, force_managed=args.force_managed, force_all_platforms=args.all_platforms, agent_override=args.agent)` 或 `scan_project(root)`（如 `--scan`）；全部默认（裸 `harness update`）才走 req-33 / chg-02 的打印引导 + return 0。
- harness-manager.md §A.3 首段增补一句"无 flag 时打印引导；任意刷新 flag 触发 install_repo 委托"；§A.4 / §A.5 改为"该 flag 透传到 `install_repo(check=True, ...)` / `scan_project(...)`，drift 预览 / 扫描行为不变"。
- 影响面最小：unit behavior 完全回归 bugfix-3 之前；现有 `test_update_check_and_apply_refresh_qoder_skill_and_rule` 的"打印引导"断言需放宽（`--check --all-platforms` 带 flag 走 install_repo 分支）。

### 方案 B（语义回归）：废除 req-33 / chg-02 的契约重定义，update CLI 回到旧 update_repo 行为；角色触发另起命令（如 `harness report`）

- 完全 revert cli.py L400-L409 为 req-33 / chg-02 之前的 update_repo 调用链；新增 `harness report` subcommand 触发 project-reporter 会话引导。
- 影响面大：需 revert chg-02 文档、改 harness-manager.md §A.3 / §3.5.1、改 skill descriptions、改 tests；req-33 全链路归档需追加勘误 commit。

### 方案 C（中间路径）：删除 update CLI subcommand，所有同步 flag 统一走 install；角色触发改为纯会话触发词，不占 CLI 命名空间

- `cli.py` L170-L189 `update_parser` 整块删除；`install_parser` L160-L163 扩展 `--check` / `--force-managed` / `--scan` / `--all-platforms`；install handler 改直调 `install_repo(...)`。
- harness-manager.md §A.3-A.5 整段删除；§3.5.1 保留会话触发词召唤 project-reporter。
- 影响面大：breaking 所有 `harness update *` shell 脚本 / CI；skill description 全面改写；但语义最干净。

## 5. 推荐方案 + 理由

**推荐方案 A**。E 原则（最小改动 / 最小风险）：方案 A 只改 cli.py 1 段 handler + harness-manager.md 3 段措辞，保留 chg-02 契约定义（裸 update 仍触发角色引导），同时恢复 CLI drift check 能力。方案 B / C 都要 revert chg-02 契约或引入 CLI breaking。

（50 字内：A 只改 handler 分叉，裸 update 保留角色引导，带 flag 透传 install_repo，零 breaking。）

## 6. 修复路径

### executing 阶段精确改点

1. **`src/harness_workflow/cli.py` L400-L409**（`if args.command == "update":` 整块 handler）：
   - 引入判断 `has_refresh_flag = args.check or args.scan or args.force_managed or args.all_platforms or args.agent`。
   - 若 `args.scan` → `from harness_workflow.workflow_helpers import scan_project; return scan_project(root)`。
   - 若 `has_refresh_flag and not args.scan` → `from harness_workflow.workflow_helpers import install_repo; return install_repo(root, force_skill=True, check=args.check, force_managed=args.force_managed, force_all_platforms=args.all_platforms, agent_override=args.agent)`。
   - 否则（裸 update）→ 保留 req-33 / chg-02 的三行打印 + `return 0`。

2. **`.workflow/context/roles/harness-manager.md` §A.3（L402-L419）/ §A.4（L421-L423）/ §A.5（L425-L427）**：
   - §A.3 首句补："**无 flag 时**打印引导 + exit 0；**任意刷新 flag（`--check` / `--scan` / `--force-managed` / `--all-platforms` / `--agent`）存在时**透传到 `install_repo(...)` / `scan_project(...)`（等价 req-33 / chg-01 合并后的 Python API）。"
   - §A.4 改写为："`--check` 触发 `install_repo(root, force_skill=True, check=True, ...)`，输出 'Update summary … No files were changed.' 的 drift 预览（原 `update_repo --check` 行为回归）。"
   - §A.5 改写为："`--scan` 触发 `scan_project(root)`（等价历史行为）；若需 10 节现状报告请在会话中说触发词召唤 project-reporter。"

3. **`tests/test_cli.py`**：
   - `test_update_check_and_apply_refresh_qoder_skill_and_rule`（L402-L439）的 `self.assertIn("harness update 已重定义为角色契约触发", check.stdout)` 需改为验证 `--check --all-platforms` 实际触发 drift 预览（不应再打印引导三行）；保留一个新的 `test_update_bare_prints_role_contract_guidance` 验证裸 `harness update` 仍打印引导。
   - 新增至少 2 个断言：(a) `harness update --check` rc=0 且 stdout 含 "Update summary"；(b) `harness update --scan` rc=0 且行为 = `scan_project`。

### R1 豁免范围

- `src/harness_workflow/cli.py` 的 `update_cmd` 内联 handler（L400-L409 → 扩展后约 L400-L430）。
- `.workflow/context/roles/harness-manager.md` §A.3 / §A.4 / §A.5 措辞。
- `tests/test_cli.py` 既有 `test_update_check_and_apply_refresh_qoder_skill_and_rule` 断言调整 + 新增 2 个 flag 路由 test。

### 不改动（与 chg-02 / chg-01 一致）

- 不改 `update_parser` / `install_parser` 定义（方案 A 不扩展 install flag；drift 路径仍走 update CLI）。
- 不改 `workflow_helpers.install_repo` / `update_repo` / `scan_project` 签名。
- 不删 `tools/harness_update.py`（保持 import 兼容）。
- 不改 `.claude/skills/harness/SKILL.md` 的 chg-02 补注小节（仅需微调描述一句）。

### scaffold_v2 mirror 同步（硬门禁五）

- req-34 / chg-04 引入跨 repo scaffold mirror 硬门禁：改 `harness-manager.md` 时必须同步 `scaffold_v2/.workflow/context/roles/harness-manager.md`；改 `tests/test_cli.py` / `cli.py` 时需评估是否有 mirror 副本。executing 阶段必做。

## 7. 影响面

### Breaking
- **不 breaking**，反而 **restore** req-33 之前的预期行为：`harness update --check` 再次输出 drift 预览，兼容 bugfix-3 引入的 `--agent` / `--all-platforms`。
- 裸 `harness update`（无 flag）仍保留 req-33 / chg-02 的三行引导 + rc=0 → chg-02 契约承诺完整兑现，不回撤。
- 会话触发词召唤 project-reporter 路径（§3.5.1）完全不受影响。

### 测试覆盖
- `tests/test_cli.py::test_update_check_and_apply_refresh_qoder_skill_and_rule` 的断言需调整（见 §6.3）。
- 新增：`test_update_bare_prints_guidance`（裸 update 打印引导）、`test_update_check_runs_drift_preview`（--check 走 install_repo）、`test_update_scan_runs_scan_project`（--scan 走 scan_project）。
- 无需改 `test_update_reports_missing_active_version`（已被 `@unittest.skip` 跳过，legacy version flow 遗留）。
- pytest 基线：chg-03 done 报告 288 passed 零回归，本 bugfix 预期新增 2-3 测试 + 调 1 测试断言，目标 ≥ 290 passed 零新增失败。

### 契约 7 链路
- 本 bugfix 首次引用父链：req-33（install 吸收 update 的 CLI 职责 + harness update 契约层重定义为触发 project-reporter）/ chg-02（harness update 角色契约层重定义为召唤 project-reporter） / chg-01（install 吸收 update_repo 的 CLI 职责：Python 合并 / 幂等化 / 测试断言同步）。已在本文件首段标注，executing 阶段 commit message 同样要求。

## 8. 验收标准

- **AC-1** `harness update --check` rc=0 且 stdout 行为 = 历史 `update_repo --check` drift 预览（含 "Update summary"、"No files were changed." 关键字）。
- **AC-2** `harness update --scan` rc=0 且行为 = `scan_project(root)`（项目适配报告 / 同历史）。
- **AC-3** `harness update --force-managed` rc=0 且行为 = `install_repo(force_skill=True, force_managed=True)`（覆写 local-modified managed 文件）。
- **AC-4** 裸 `harness update`（无任何刷新 flag）仍打印 req-33 / chg-02 引导三行 + rc=0。
- **AC-5** `.workflow/context/roles/harness-manager.md` §A.3 / §A.4 / §A.5 措辞同步到"无 flag 打印引导 / 有 flag 透传 install_repo"，且 scaffold_v2 mirror（若存在）同步。
- **AC-6** `tests/test_cli.py` 至少新增 2 条断言覆盖 `--check` / `--scan` flag 路由，且调整既有 `test_update_check_and_apply_refresh_qoder_skill_and_rule` 断言使之反映新行为。
- **AC-7** `pytest` 零新增失败（baseline ≥ 288 passed → fix 后 ≥ 290 passed 或等值 + 调整 1 条 assert）；`harness validate --contract all` 绿。
- **AC-8** scaffold_v2 mirror 同步（硬门禁五，req-34 / chg-04）— 若 scaffold_v2 存在本仓 cli.py / harness-manager.md 的 mirror，commit 必须并行更新。
