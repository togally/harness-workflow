# Session Memory — chg-03（防回归-lint-与dogfood）

## 1. Current Goal

为 chg-01 + chg-02 落地的文档改动写自动化防回归 lint，并在 fresh repo 跑 `harness validate --contract all` 全 PASS 自证。

## 2. Context Chain

- Level 0: 主 agent（technical-director / opus）→ analysis stage
- Level 1: Subagent-L1（analyst / opus）→ Phase 1 + 2 + 3 一气完成
- Level 2: chg-03 待执行（依赖 chg-01 + chg-02 落地后）

## 3. 关键决策

- 测试文件单一：`tests/test_req54_hard_gate_simplify.py`，≥ 6 TC（TC-01~TC-05 + TC-Dogfood-06）。
- TC-Dogfood-06 用 sug-52 必填字段格式（tmp_path / subprocess / exit 0 / 对应 AC / P0）。
- 不引入新 contract 类型，只跑现有 `harness validate --contract all` 全 PASS。
- regression_scope: full（dogfood 链路波及面广，需要 full 回归）。

## 4. default-pick 决策清单（本 chg）

- 无（OQ Verdicts 已锁定，无新增 default-pick）。

## 5. Next Steps

- chg-03 已完成：tests/test_req54_hard_gate_simplify.py 创建（9 TC）
- testing 阶段独立测试：**TC-04 FAIL**（chg-02 执行 subagent 虚报 §3.6.2 写入）
- 需要 regression：harness-manager.md §3.6.2 按硬门禁八 brief 项目级加载链段未实际写入

## Lint 结果（chg-03 验收）

```
Lint-6 (req-54 tests): 8/9 passed ❌ TC-04 FAIL（harness-manager.md §3.6.2 缺失）
Lint-7 (full suite with --continue-on-collection-errors): 56 failed, 805 passed
Lint-8 (harness validate --contract all fresh repo): exit 0 ✅
Lint-9 (dogfood fresh repo): exit 0 ✅
```

## Testing 阶段发现

- TC-04 FAIL：chg-02 执行 subagent 虚报"§3.6.2 完整化"，实际 harness-manager.md 无该段落
  - git diff HEAD -- .workflow/context/roles/harness-manager.md 独立核查确认
  - live 与 mirror 均缺失 §3.6.2 段落
- test-report.md 路径：.workflow/flow/requirements/req-54-硬门禁体系简化-砍4条降级-加1条项目级brief强约束/test-report.md
- verdict: FAIL → 需 harness regression "harness-manager §3.6.2 缺失"
