# Session Memory — bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）

## 1. Current Goal

executing 阶段：实施 chg-01（init_repo force_managed 透传修复）+ chg-02（user-write-protected-zones 移除 skill/commands 误报）。

## 2. Current Status

执行完毕，全部 ✅。

## 3. Completed Steps

✅ chg-01（init_repo force_managed 透传修复）
- 修改文件：`src/harness_workflow/workflow_helpers.py`
  - `init_repo` 新增 `force_managed: bool = False` 参数
  - `install_repo` 内对 `init_repo` 的调用改为 `init_repo(..., force_managed=force_managed)`
- 修复点：`install_repo(force_managed=True)` → `init_repo(force_managed=True)` → `_sync_requirement_workflow_managed_files(force_managed=True)` 全链路打通
- 其他调用（`harness_init.py`、`install_agent` 内 L8071）保持默认 `force_managed=False` 不变（初始化场景语义正确）

✅ chg-02（user-write-protected-zones 移除 skill/commands 扫描列表）
- 修改文件：`src/harness_workflow/validate_contract.py`
  - `check_user_write_protected_zones` 的 `protected_zones` 只保留 `".workflow"` 一项
  - 删除 `.{claude,codex,kimi,qoder}/skills` 和 `.{claude,codex,kimi,qoder}/commands` 8 条路径

✅ bugfix.md / regression/diagnosis.md 补写（ff 模式跳过 regression 由 executing 补写）

✅ 新增回归测试 `tests/test_bugfix9_force_managed_and_user_write.py`（7 条用例）
- TC-A1 × 2（force_managed=True 覆盖 + force_managed=False 保护）
- TC-A2（grep 验证 install_repo 调用含 force_managed=force_managed）
- TC-B1 × 2（user project + skill 工具产出 → exit 0）
- TC-B2 × 2（user project + .workflow/ 野文件 → exit 1）

## 4. Internal Test Results

- 新增测试：7/7 PASS
- 全量 pytest：13 个 pre-existing fail（与修改无关，git stash pop 前后一致），0 新增 fail
- dogfood `harness install --check --force-managed`：stderr 含 `[install_repo] force_managed received: True`，无 `skipping user-modified (force_managed=False)` ✅
- dogfood `harness validate --contract user-write-protected-zones`：本仓 exit 0（dev mode 豁免）✅
- 模拟 user project + skill 工具产出：`harness validate --contract user-write-protected-zones` exit 0（不误报）✅
- `harness validate --contract artifact-placement`：exit 0 ✅
- `harness validate --human-docs`：exit 0（D-11=B 留痕，4 pending 正常，executing 阶段放行）✅

## 5. Changed Files

chg-01（init_repo force_managed 透传修复）：
- `src/harness_workflow/workflow_helpers.py`（init_repo 签名 + install_repo 调用点）

chg-02（user-write-protected-zones 移除 skill/commands 误报）：
- `src/harness_workflow/validate_contract.py`（protected_zones 缩减为 .workflow 单项）

新增测试：
- `tests/test_bugfix9_force_managed_and_user_write.py`

文档补写：
- `.workflow/flow/bugfixes/bugfix-9-force-managed-透传修复-user-write-门禁误报修复/bugfix.md`
- `.workflow/flow/bugfixes/bugfix-9-force-managed-透传修复-user-write-门禁误报修复/regression/diagnosis.md`

## 6. Open Questions / Default-pick Decisions

- 无 default-pick 决策（两个 chg 均为明确修法，无争议路径）
- chg-02 备选方案（把 skill 文件登记到 managed_state）降级为 sug 池，理由：复杂度高（改 install_local_skills + managed-files schema），简单方案已满足需求

## 7. Regression Candidates

无新经验（本次修复已有明确先例，force_managed 透传断链类见经验九）。
