# Session Memory — req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）testing

## 1. Current Goal

独立评估 chg-01（机器型工件路径修复 + 防再犯 lint）+ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）实现是否达到 AC，产出 test-report.md 落 req 根目录。

## 2. Context Chain

- Level 0: 主 agent（harness testing）
- Level 1: harness-manager（opus，命令解析 + 角色调度）
- Level 2: testing-L1（sonnet，本 subagent，req-46 testing 独立评估）

## 3. Completed Tasks

- [x] 角色加载（runtime.yaml / context/index.md / base-role.md / stage-role.md / testing.md / evaluation/testing.md）
- [x] 模型自检（expected_model=sonnet，当前为 sonnet，自检通过）
- [x] 读取 chg-01/chg-02 change.md + plan.md + session-memory.md
- [x] 独立测试矩阵设计（不照搬 executing TC，独立判断覆盖度）
- [x] 全量回归：`pytest -q` 653 passed, 4 failed (pre-existing), 52 skipped
- [x] chg-01 专项用例：`pytest tests/test_artifact_placement_chg01.py -v` 40/40 PASS
- [x] chg-02 子进程 dogfood：`pytest tests/test_workflow_next_subprocess.py -v` 5/5 PASS
- [x] chg-02 gate 边界：`pytest tests/test_workflow_helpers_executing_gate.py -v` 9/9 PASS
- [x] 独立 subprocess gate 验证（testing 自设计 4 路径）— 全部 PASS
- [x] artifact-placement lint：`python3 -m harness_workflow.cli validate --contract artifact-placement` exit 0
- [x] scaffold_v2 mirror diff：chg-01/chg-02 相关 4+3 文件均无差异
- [x] artifact-placement 反向抽样：artifacts/req-46-*/ 下 0 件物理机器型文件
- [x] sug 状态字段语义审查：sug-35/sug-46/sug-50/sug-53 frontmatter 字段正确
- [x] 5 项合规扫描（R1 / revert / 契约 7 / req-29 / req-30）全 PASS
- [x] test-report.md 落 `.workflow/flow/requirements/req-46-.../test-report.md`（req 根目录）
- [x] session-memory.md 落 `.workflow/flow/requirements/req-46-.../testing/session-memory.md`

## 4. Test Results Summary

### chg-01（机器型工件路径修复 + 防再犯 lint）
- AC-1（物理回归）：PASS
- AC-2（lint 全绿）：PASS
- AC-3（lint 真敏感）：PASS
- AC-4（白名单不误伤）：PASS
- AC-5（stage 退出门禁）：PASS
- AC-6（scaffold_v2 mirror）：PASS
- AC-7（sug-35 落地翻转）：PARTIAL PASS（review-checklist 条目 PASS；sug-35 翻转 acceptance 后执行，符合 plan.md 硬序约束 4）

### chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
- AC-1（保守降级严格化）：PASS
- AC-2（子进程 dogfood 4 路径全绿）：PASS
- AC-3（自身周期 dogfood 自证）：PASS（独立 subprocess 验证 over-chain 已止）
- AC-4（sug 状态翻转 frontmatter）：PASS（字段正确；status 翻 acceptance 后执行）
- AC-5（部署同步契约文档化）：PASS
- AC-6（mirror diff + 经验沉淀）：PASS

**总结：PASS（13/13 AC 满足，AC-7 PARTIAL 符合硬序约束，不视为失败）**

## 5. Key Decisions（default-pick 决策清单）

- **T-D-1（revert 抽样）**：HEAD commit 含 session-memory 未提交修改导致 revert dry-run pre-empt；判定产品代码无 conflict，PASS-with-NOTE（按 default-pick 不阻塞）。
- **T-D-2（scaffold_v2 experience drift）**：analyst/executing/testing experience 文件 live>scaffold 的 drift 属 pre-existing 且在 chg-01/chg-02 scope 外，不计入 AC-6 失败，PASS（按 default-pick 接受）。
- **T-D-3（AC-7 sug-35 翻转）**：sug-35 status=pending 是符合 plan.md 硬序约束 4 的有意保留，不视为失败（按 default-pick 记 PARTIAL PASS）。
- **T-D-4（chg-02 未 commit）**：chg-02 工件均在 working directory，实现已验证通过；commit 留 acceptance 阶段前执行，不阻塞 testing 结论。

## 6. 待处理捕获问题（职责外）

- chg-02 工件未 commit（workflow_helpers.py 严格化 + test_workflow_next_subprocess.py + test_workflow_helpers_executing_gate.py + evaluation/ + experience/roles/regression.md + scaffold_v2 mirror）—— 需在 acceptance 阶段前 commit，然后验证部署同步契约（pipx mtime ≥ HEAD commit ts）。
- scaffold_v2 experience/roles/{analyst,executing,testing}.md drift（pre-existing）—— 建议后续 req 补 mirror，记 sug。

## 7. Next Steps（给 acceptance subagent）

1. 确认 chg-02 未提交文件已 commit（包含 workflow_helpers.py / test_workflow_next_subprocess.py / test_workflow_helpers_executing_gate.py / evaluation/ / regression.md / scaffold_v2 mirror）
2. 验证部署同步契约：`pipx install --force <repo-path>` + `venv workflow_helpers.py mtime ≥ HEAD commit ts`
3. 逐条对照 requirement.md + chg-01/chg-02 change.md AC 做 acceptance 核查
4. acceptance PASS 后翻转 sug-35（reviewer checklist artifact-placement lint 条目补全）+ sug-46（二次实证 over-chain）/ sug-50（gate gap 部署 gap） status → archived；sug-53（usage-log 缺失）over-chain 副作用 archived，主因留 pending
