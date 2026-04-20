# Acceptance Stage Experience

> Placeholder experience file. Fill in based on actual project lessons.

## Key Constraints

<!-- Record must-follow constraints here -->

## Best Practices

<!-- Record recommended approaches here -->

## Common Mistakes

<!-- Record common errors here -->

## 经验一：harness validate --human-docs 的 Summary 口径以工具输出为准，不按 briefing 记忆硬编码

### 场景

req-29 briefing 预期"validate --human-docs 最终 18/18"，但工具实际输出 14/14（5 变更简报 + 5 实施说明 + 4 个 req 级对人文档）。

### 经验内容

- acceptance 与 done 阶段跑 `harness validate --human-docs --requirement <req-id>` 后，应**以工具实际输出的 Summary 为准**，不能按 briefing 或记忆里的期望数字硬断言。
- 若 briefing 预期数与实际输出不符，需在验收摘要.md / done-report.md 中如实记录实际数并说明差异原因（通常是 briefing 对条目数的估算不准，而不是落盘缺失）。
- 正确的硬门禁语义是"Summary 行必须包含 'All human docs landed.'"而不是"数字必须等于 N"。

### 反例

- 根据 briefing 的 18/18 预期死磕工具，误判 validate 失败。
- 在 acceptance/done 报告里写错期望数，导致后续审阅者 confused。

### 来源

req-29 — ff --auto + archive 路径清洗批量合集

---

## 经验二：独立复跑遇到 failure，必须 git stash 回到 HEAD baseline 认证 pre-existing

### 场景

acceptance 阶段独立复跑全量 `pytest`，executing 简报称"唯一 failure 是 pre-existing，零新增回归"。如果只信简报直接判 pass，有可能把新增 regression 漏网——executing 的自检未必独立。

### 经验内容

1. **独立认证 = git stash + 重跑**：在当前 repo 里 `git stash -u`（或 `git stash --include-untracked`）把 executing 的代码改动暂存，回到 HEAD baseline；重跑同一条 failing 测试；若 HEAD baseline 下同样 FAIL → 确实 pre-existing，写进验收摘要。若 HEAD baseline 下 PASS → 新增 regression，拒绝本次 acceptance。
2. **pop 回来**：认证完毕立即 `git stash pop` 恢复 executing 的改动，不得遗忘在 stash 里。
3. **失败路径独立度检查**：除了 `git stash` 路径，还要核查"failure 到底是哪个 test 文件 / 哪个断言"，与本 bugfix/change 修改的范围是否存在间接依赖（比如 executing 改了 workflow_helpers，而 failing 测试恰好 `import` 该模块——理论上 pre-existing 但值得二次核查）。
4. **在验收摘要里留痕**：写清"已用 git stash 回到 HEAD baseline 复跑，确认 pre-existing，无新增回归"，而不是仅复制 executing 简报的结论。

### 反例

- 只读 executing 简报里的一句"pre-existing，零新增"就签字放行——违反"生产者 / 评估者分离"原则；本项目 bugfix-3 的 acceptance subagent 就是靠这条认证排除了 `test_smoke_req29` 的 FAIL 嫌疑（确认是 req-29 阶段的遗留）。
- 不 `git stash pop`，后续 commit 时少了 executing 的改动——导致 done 阶段或归档时发现代码 diff 与 simulations 对不上。

### 来源

bugfix-3 — pipx 重装后新项目 install/update 生成数据不正确（acceptance 阶段独立复跑）
