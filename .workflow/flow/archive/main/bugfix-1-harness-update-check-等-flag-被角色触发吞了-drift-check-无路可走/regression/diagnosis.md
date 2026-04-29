# Regression Diagnosis — bugfix-1

## Issue
harness update --check 等 flag 被角色触发吞了，drift check 无路可走（即：user 跑 `harness update --check` 期待 managed 文件 drift 预览，但 CLI 一律打印 req-33 / chg-02 的引导文案并 `exit 0`，drift check 无 CLI 入口）。

## Trigger（用户 agent 对话节选）

```
$ harness update --check
harness update 已重定义为角色契约触发。
请在 Claude Code / Codex 会话中说 '生成项目现状报告' 召唤 project-reporter。
CLI 同步职责已迁到 `harness install`。
```

期望：rc=0 且输出 "Update summary … No files were changed." 形式的 drift 预览。
实际：三行引导文案 + rc=0，drift 信息丢失。

---

## 1. 代码层根因（一句话）

`src/harness_workflow/cli.py` L400-L409 `args.command == "update"` handler 被 req-33 / chg-02 / S-B4 severed 为**"忽略所有 flag 统一打印引导 + return 0"**；`update_parser` L172-L189 保留 `--check` / `--scan` / `--force-managed` / `--agent` / `--all-platforms` 五个 flag argparse 解析不报错，但 handler 不读取 `args.check` / `args.scan` / `args.force_managed`，也从不 delegate。

关键代码（`src/harness_workflow/cli.py:400-409`）：

```python
if args.command == "update":
    # req-33 / chg-02 / S-B4：CLI 同步职责已迁到 `harness install`。
    # 保留 update_parser 的 --check / --scan / --force-managed / --agent / --all-platforms 不报错，handler 一律忽略。
    print("harness update 已重定义为角色契约触发。")
    print("请在 Claude Code / Codex 会话中说 '生成项目现状报告' 召唤 project-reporter。")
    print("CLI 同步职责已迁到 `harness install`。")
    return 0
```

与此同时：

- `src/harness_workflow/tools/harness_update.py` L16-L44 **仍然是完整 tool script**（accept 5 个 flag，路由 `scan_project(root)` 或 `update_repo(root, check=..., force_managed=..., force_all_platforms=..., agent_override=...)`），chg-02 `change.md` L37 明确不删（"沦为 test-only helper"）。→ CLI 失去对它的触发路径。
- `src/harness_workflow/workflow_helpers.py` L3095-L3230 `install_repo(root, *, force_skill, check, force_managed, force_all_platforms, agent_override)` 是 req-33 / chg-01 merge 后的主实现，支持 drift check；`update_repo` L3387-L3403 是空壳委托。→ Python API 层 drift 能力完整，纯 CLI 入口缺失。

## 2. 契约层根因（scope 盲区）

req-33 / chg-02 `change.md` L11 / L23 / L31 / L50 / L69-L71 / L95 明确设计 P-B2 = "保留 `--check` / `--scan` 不报错 + handler 忽略 + rc=0"，理由为"兼容存量 shell 脚本 / CI 的 argparse 解析"。harness-manager.md §A.5（L425-L427）进一步告诉用户："若确需扫描项目特征，请……**在会话中直接触发 project-reporter**（其 10 节模板的 §2-§5 覆盖原 `scan_project()` 的技术栈 / 目录结构 / 规范文件检测）。"

**盲区**：chg-02 把 `--scan` 的替代方案指向 **project-reporter 角色**（生成 `project-overview.md`），把 `--check` / `--force-managed` 的替代方案指向 **`harness install`** —— 但 `install_parser`（cli.py L160-L163）仅注册了 `--force-skill` / `--agent` / `--root` 三个 flag，**从未**扩展 `--check` / `--force-managed` / `--all-platforms`。install handler（L385-L392）也只委托 `harness_install.py`（单 agent 安装），不调 `install_repo(check=True, ...)`。

结论：chg-02 契约声明的"迁到 `harness install`"**从未在 CLI 层实现**。`--check` / `--scan` / `--force-managed` 三类 flag 被 CLI 截断，而承诺的替代入口实际不存在。这是**scope 盲区**（不是故意简化）——chg-02 关注"切断 update CLI 刷新职责"，未审视"install CLI 是否吸收了对等 flag"。chg-01 `change.md` 负责 helper 层合并，亦未引入 install CLI flag 扩展。

## 3. 真实问题判定

✅ **真实问题**（非误判）。

证据：
- CLI 端唯一 drift check 路径（`harness update --check`）已 severed。
- 承诺替代路径（`harness install --check`）从未注册 flag。
- 残留 `tools/harness_update.py` 仍可跑但无 CLI 触发链。
- `tests/test_cli.py::test_update_check_and_apply_refresh_qoder_skill_and_rule`（L402-L439）自证：CLI `update --check --all-platforms` 只验证"打印引导"，**真正的刷新必须绕道 Python `update_repo(...)` API**。→ shell / CI 用户目前无 CLI 入口做 drift。

## 4. 路由决定

**Routing Direction**: ✅ Real issue → proceed to fix（路由到 **executing**，通过 harness-manager 派发修复）。

- 非需求/设计误判（契约本身可行，只是 CLI 覆盖不全）。
- 非测试误判（tests 已证实 CLI 现状就是这样）。
- 是 CLI 实现层遗漏 + harness-manager.md §A.3-A.5 措辞需同步澄清。

完整方案、推荐、修复路径、验收标准、影响面见 `bugfix.md`。

## Required Inputs
- 无。用户已授权 ff，推荐默认走方案 A。
