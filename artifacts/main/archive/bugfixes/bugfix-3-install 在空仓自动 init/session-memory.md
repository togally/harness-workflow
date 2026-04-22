# Session Memory — bugfix-3

## 1. Current Goal

完成 bugfix-3（install 在空仓自动 init）的 regression + executing + testing 全链路：让空仓执行 `harness install` 不再被拒，自动 init 后完成 skill 安装，且不破坏已初始化仓库的状态。

## 2. Current Status

- [x] regression（diagnosis.md 完成，定位根因到 `workflow_helpers.py:4382`）
- [x] executing（修改 `install_agent()`，编辑 `workflow_helpers.py:4372-4400`，syntax 检查通过）
- [x] testing（5 个场景全部 PASS，test-evidence.md 完成）
- [x] bugfix.md 填完

## 3. Validated Approaches

- 调用链追踪：CLI → tool script → workflow_helpers 函数。`harness install` 走 `install_agent()`，不走 `install_repo()`。
- 对 editable pipx install 的改动立即生效：`/Users/jiazhiwei/.local/pipx/venvs/harness-workflow` 的 `direct_url.json` 标记为 `editable: true`，源码在 `/Users/jiazhiwei/IdeaProjects/harness-workflow`，编辑后无需 reinstall。
- 区分"新建"与"已存在"分支的最小侵入 fix：只替换 `install_agent()` 首行的 `ensure_harness_root(root)`，不触碰 `ensure_harness_root()` 自身。
- 验证状态不被破坏的可靠手段：md5 对比关键状态文件（`runtime.yaml`, `requirements/*.yaml`）前后。

## 4. Failed Paths

无。第一次修改即通过所有测试。

## 5. Candidate Lessons

```markdown
### 2026-04-19 install 入口不应假定 .workflow/ 已存在
- Symptom: `harness install --agent <x>` 在空仓 exit 1，错误提示 "Run `harness install` or `harness init` first" 自相矛盾。
- Cause: `install_agent()` 开头硬调用 `ensure_harness_root()`，该 guard 只应保护需要已初始化状态的命令。
- Fix: install 入口探测 `.workflow/` 缺失则自动 `init_repo()`，stdout 给出 "No .workflow/ found, running harness init first..." 提示；否则走原 guard。
- Generalization: "入口命令"（documented primary entrypoint）与"使用命令"应区分 guard 边界——入口命令允许/期望在未初始化状态下被调用，使用命令才需 guard。
```

```markdown
### 2026-04-19 编辑 pipx editable install 的仓库时无需 reinstall
- Scene: 本仓通过 `pipx install -e` 安装，`~/.local/bin/harness` 直接 import 源码包。
- Practice: 修改 `src/harness_workflow/**` 后立即用 `harness ...` 命令验证即可；无需 `pipx reinstall`。
- Verify: `pipx_venv/.../harness_workflow-*.dist-info/direct_url.json` 含 `"editable": true` → editable。
```

## 6. Derivative Findings (记录不修)

- **模板种子泄漏作者 runtime 状态**：`init_repo()` → `_sync_requirement_workflow_managed_files()` 将作者仓的 `.workflow/state/runtime.yaml`（内含 `current_requirement: req-25`、`active_requirements: [req-25]`）复制到新仓。新仓 `harness status` 看到非预期的 `req-25`。
  - 复现：`mkdir /tmp/x && cd /tmp/x && git init && harness init --write-claude && cat .workflow/state/runtime.yaml` 即见泄漏。
  - 影响：onboarding 误导；不阻塞 install/requirement 流程（req-01 仍可正确创建）。
  - 建议：在 template 层把 runtime.yaml 模板改为 "clean slate" 初值（`current_requirement: ""`、`active_requirements: []`），或 `init_repo()` 在写 runtime.yaml 时强制重置。
  - **未在 bugfix-3 范围内修复**，交由主 agent 决定是否开新 bugfix 或 change。

## 7. Next Steps

- 向主 agent 报告：bugfix-3 修复+验证完成，5/5 PASS；询问是否就"模板种子泄漏"开新 bugfix。
- 本 subagent 不推进 stage，不修改 runtime.yaml。

## 8. Open Questions

- 模板种子泄漏是否应归到 req-25 新的 P0 或单独 bugfix？留给主 agent 判定。
