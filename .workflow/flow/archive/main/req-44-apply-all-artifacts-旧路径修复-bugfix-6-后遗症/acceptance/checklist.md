# Acceptance Checklist — req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））

- 验收日期：2026-04-25
- 验收角色：acceptance subagent（Sonnet 4.6）

---

## §AC 映射

| AC | 描述 | 对应用例 | testing 结论 |
|----|------|---------|-------------|
| AC-01 | apply-all 后 bugfix-6 路径成功 + req_md 不存在不 unlink | TC-01 / TC-02 / TC-03 + EC-01 | ✅ PASS |
| AC-02 | apply 单 sug 取 sug.title + requirement.md 含 sug.content | TC-04 / TC-05 / TC-06 + EC-02 / EC-04 | ✅ PASS |
| AC-03 | rename 同步三处目录 + runtime current/locked title | TC-01..TC-05（chg-02）+ EC-03 | ✅ PASS |
| AC-04 | scaffold mirror no-op（仅改 src/ + tests/） | 合规扫描项 1 + executing 抽检 | ✅ PASS |
| AC-05 | e2e 用例 ≥ 2 per 类：apply 6 + rename 5 | 11 用例 + 4 反例 + 2 dogfood | ✅ PASS |

---

## §验收 checklist

| # | 检查项 | 依据 | 结果 |
|---|--------|------|------|
| 1 | `_append_sug_body_to_req_md` helper 已落 workflow_helpers.py line ~4300，按 `_use_flow_layout` 双路径 | 代码抽样 grep 命中 line 4300 | ✅ |
| 2 | `apply_suggestion` title 取 sug frontmatter；body 调 helper 写入 requirement.md | grep `apply_suggestion` + session-memory executing 段 | ✅ |
| 3 | `apply_all_suggestions` 废弃旧硬路径，FileNotFoundError → abort + stderr + sug 保留 | grep `apply_all_suggestions` line 4550；TC-03 PASS | ✅ |
| 4 | `rename_requirement` step 4 + step 5 追加 flow/ 目录探测 + runtime title 同步 | 代码抽样 line 5462–5476 | ✅ |
| 5 | 测试文件三份存在（test_req44_chg01.py / test_req44_chg02.py / test_req44_testing_extra.py） | ls 确认 | ✅ |
| 6 | 全量回归 591 passed，0 new failure，2 pre-existing | test-report.md §全量回归 | ✅ |
| 7 | 合规扫描 5/5（R1 越界 / revert / 契约 7 / req-29 / req-30） | test-report.md §D | ✅ |
| 8 | scaffold mirror AC-04 = no-op（仅改 src/ + tests/） | executing session-memory + test-report.md §合规 | ✅ |
| 9 | plan.md 两份六段齐，§测试用例设计 11 用例 AC 字段非空 | 读 plan.md 两份确认 | ✅ |
| 10 | 契约 7：首次引用 req-44 / chg-01 / chg-02 / sug-43..45 / bugfix-6 均带括号描述 | test-report.md §合规项 3（minor：change.md §3 模板字段裸 id，不阻断） | ✅（minor） |
| 11 | 不动 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 已落地契约本身（Scope OUT） | 合规扫描 R1 + git diff 命中文件范围 | ✅ |
| 12 | Dogfood 全链跑通（apply + rename 实证） | test-report.md §C | ✅ |

**checklist 小计：12/12 PASS（1 minor 不阻断）**

---

## §遗留

| 编号 | 类型 | 描述 | 阻断？ |
|------|------|------|--------|
| F-01 | followup sug | change.md §3 Requirement 字段 `- \`req-44\`` 裸 id（模板结构字段，非叙述性引用）；testing 已评估不阻断；建议下一 req 起统一在 change.md §3 补短描述或在 template 加注释 | 否 |
| F-02 | followup sug | R-3（runtime 未来扩 `*_requirement_title` 类字段需同步 rename_requirement 本处）；plan.md §回滚 已注明，done 阶段补 sug | 否 |

---

## §结论

**验收判定：PASS**

- 5 AC 全覆盖（AC-01 / AC-02 / AC-03 / AC-04 / AC-05）。
- 12 项 checklist 12/12 PASS，1 minor（change.md 裸 id，非叙述性结构字段，不阻断）。
- 全量回归 591 passed，0 new failure，2 pre-existing 与本 req 无关。
- 2 followup（F-01 change.md template 裸 id 改进 + F-02 runtime 字段扩展注意点），均不阻断。
- **推荐流转：acceptance → done**。
