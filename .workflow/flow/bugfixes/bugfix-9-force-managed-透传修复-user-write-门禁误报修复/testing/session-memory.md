# Session Memory — bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）/ testing

**角色**：测试工程师（testing / sonnet）
**日期**：2026-04-28

## 1. Current Goal

testing 阶段：独立验证 chg-01（init_repo force_managed 透传修复）+ chg-02（user-write-protected-zones 移除 skill/commands 误报）。

## 2. Current Status

测试完毕，全部 PASS。产出 test-evidence.md（testing 独立报告）+ testing/session-memory.md。

## 3. Completed Steps

✅ Step 0：自我介绍 — testing subagent（testing / sonnet），声明硬门禁（禁破坏性 git 命令）

✅ Step 1：TC 覆盖核查
- 对照 bugfix.md §Validation Criteria + regression/diagnosis.md §测试用例设计
- 4 TC（TC-A1 / TC-A2 / TC-B1 / TC-B2）对应实现均在 test_bugfix9_force_managed_and_user_write.py
- TC-B1 + TC-B2 各有 unit + subprocess 两个变体（共 7 用例）

✅ Step 2：执行测试
- pytest tests/test_bugfix9_force_managed_and_user_write.py -v：7/7 PASS
- pytest tests/（全量）：13 failed（pre-existing）+ 695 passed，0 新增 fail
- dogfood-a：harness install --check --force-managed，stderr 含 `force_managed received: True`，无 `force_managed=False` skip
- dogfood-b：harness validate --contract user-write-protected-zones（本仓 dev mode），exit 0 PASS
- dogfood-c：mock user project（tmpdir）+ .claude/skills/harness/SKILL.md，validate exit 0（不误报）
- dogfood-d：mock user project（同 tmpdir）+ .workflow/context/roles/my-custom.md（野文件），validate exit 1（正确拦截）

✅ Step 3：产出 test-evidence.md
- 路径：.workflow/flow/bugfixes/bugfix-9-force-managed-透传修复-user-write-门禁误报修复/test-evidence.md
- 含：TC 覆盖矩阵 + dogfood 4 项 + 全量回归 + 13 历史 fail 溯源 + 5 项合规扫描 + ##结论

✅ 退出条件验证
- harness validate --human-docs：exit 1（4 pending，D-11=B 留痕放行，testing 阶段正常）
- harness validate --contract artifact-placement：exit 0 PASS

## 4. Key Findings

- chg-01 修复确认有效：install_repo(force_managed=True) → init_repo(force_managed=True) → _sync_requirement_workflow_managed_files(force_managed=True) 全链路打通
- chg-02 修复确认有效：protected_zones 只保留 ".workflow"，skill/commands 工具产出不再误报
- 真野文件（.workflow/ 下用户自定义）仍被正确拦截，保护语义无损
- 13 历史 fail 全部与 bugfix-9 无关，pre-existing

## 5. Default-pick Decisions

- P-1（revert 抽样）：N/A（chg 在 working tree，无 commit sha，硬门禁禁止破坏性 git，留痕放行）

## 6. Hard Gate Compliance

- 无破坏性 git 命令执行（禁令：git revert / checkout / reset / clean / stash / rm / mv）✅
- 所有 dogfood 在 tmpdir 进行，未动主仓库 src/ ✅
- 产物落 .workflow/flow/bugfixes/bugfix-9-{slug}/ 正确路径 ✅
- 未修改任何代码 ✅
